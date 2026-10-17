"""Tests for the reference server and client, at short timings.

Run from this folder:  python3 -m unittest -v test_reference
Needs Python 3.8+ and Node 18+ (the client cases are skipped without node).
Each case starts its own server on a free port with its own environment and stops it after.
"""

import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
NODE = shutil.which("node")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    def __init__(self, **env):
        self.port = free_port()
        full = dict(os.environ, PORT=str(self.port), PYTHONDONTWRITEBYTECODE="1", HEARTBEAT_S="0.5")
        for key in ("FAIL_TOOL", "IGNORE_CANCEL", "NO_PROGRESS"):
            full.pop(key, None)
        full.update({k: str(v) for k, v in env.items()})
        self.proc = subprocess.Popen([sys.executable, "-B", os.path.join(HERE, "sse_server.py")],
                                     env=full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.proc.stdout.readline()  # "listening on ..."

    @property
    def url(self):
        return "http://127.0.0.1:%d" % self.port

    def stop(self):
        self.proc.terminate()
        self.proc.wait(5)
        self.proc.stdout.close()


def post(port, path, body, timeout=10):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    conn.request("POST", path, json.dumps(body), {"Content-Type": "application/json"})
    return conn, conn.getresponse()


def read_stream(port, message="q", on_event=None, timeout=20):
    """Returns [(seconds_since_start, type, data)] until the stream closes."""
    t0 = time.monotonic()
    conn, res = post(port, "/chat/stream", {"message": message}, timeout)
    events, etype = [], None
    try:
        while True:
            line = res.readline()
            if not line:
                break
            line = line.decode().rstrip("\n")
            if line.startswith("event:"):
                etype = line[6:].strip()
            elif line.startswith("data:"):
                ev = (time.monotonic() - t0, etype, json.loads(line[5:]))
                events.append(ev)
                if on_event:
                    on_event(ev)
    finally:
        conn.close()
    return events


def types(events):
    return [e[1] for e in events]


def run_client(url, cancel_after=None, **env):
    full = dict(os.environ)
    full.update({k: str(v) for k, v in env.items()})
    args = [NODE, os.path.join(HERE, "client_state_machine.mjs"), url, "q"]
    if cancel_after is not None:
        args.append(str(cancel_after))
    t0 = time.monotonic()
    out = subprocess.run(args, env=full, capture_output=True, text=True, timeout=30).stdout
    return out, time.monotonic() - t0


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.stop()

    def start(self, **env):
        self.server = Server(**env)
        return self.server.port

    def assert_closed_properly(self, events, terminal):
        seq = types(events)
        self.assertEqual(seq[0], "ack")
        self.assertEqual(seq[-1], terminal)
        self.assertEqual(sum(t in ("done", "cancelled", "error") for t in seq), 1)
        starts = [e[2]["id"] for e in events if e[1] == "tool_start"]
        ends = [e[2]["id"] for e in events if e[1] == "tool_end"]
        self.assertEqual(sorted(starts), sorted(ends), "every tool_start needs exactly one tool_end")
        for sid in starts:
            at_start = next(i for i, e in enumerate(events) if e[1] == "tool_start" and e[2]["id"] == sid)
            at_end = next(i for i, e in enumerate(events) if e[1] == "tool_end" and e[2]["id"] == sid)
            self.assertLess(at_start, at_end)

    def test_normal_turn_streams_ack_progress_heartbeat_done(self):
        port = self.start(TOOL_SECONDS=2)
        events = read_stream(port)
        self.assert_closed_properly(events, "done")
        start = next(e for e in events if e[1] == "tool_start")
        self.assertIn("expected_s", start[2])
        self.assertIn("tool_progress", types(events))
        self.assertIn("heartbeat", types(events))
        self.assertLess(events[0][0], 0.3, "ack must come before any slow step")

    def test_failing_tool_still_closes_step(self):
        port = self.start(TOOL_SECONDS=2, FAIL_TOOL=1)
        events = read_stream(port)
        self.assert_closed_properly(events, "error")
        end = next(e for e in events if e[1] == "tool_end")
        self.assertFalse(end[2]["ok"])

    def _cancel_mid_tool(self, ignore):
        env = dict(TOOL_SECONDS=30, CANCEL_GRACE_S=1)
        if ignore:
            env["IGNORE_CANCEL"] = 1
        port = self.start(**env)
        sent = {}

        def on_event(ev):
            if ev[1] == "ack":
                sent["id"] = ev[2]["turn_id"]
            if ev[1] == "tool_start":
                def later():
                    time.sleep(1)
                    sent["at"] = time.monotonic()
                    c, r = post(port, "/chat/cancel", {"turn_id": sent["id"]})
                    sent["status"] = r.status
                    c.close()
                threading.Thread(target=later, daemon=True).start()

        t0 = time.monotonic()
        events = read_stream(port, on_event=on_event)
        closed = time.monotonic()
        self.assertEqual(sent.get("status"), 202)
        self.assert_closed_properly(events, "cancelled")
        end = next(e for e in events if e[1] == "tool_end")
        self.assertEqual(end[2]["summary"], "stopped")
        self.assertLess(closed - sent["at"], 1.0, "cancel must not wait on the tool")
        self.assertLess(closed - t0, 5)

    def test_cancel_cooperative_tool(self):
        self._cancel_mid_tool(ignore=False)

    def test_cancel_tool_that_ignores_cancel(self):
        self._cancel_mid_tool(ignore=True)

    def test_ceiling_with_tool_that_ignores_cancel(self):
        port = self.start(TOOL_SECONDS=30, TURN_CEILING_S=2, IGNORE_CANCEL=1)
        t0 = time.monotonic()
        events = read_stream(port)
        self.assert_closed_properly(events, "error")
        self.assertLess(time.monotonic() - t0, 4, "ceiling must not wait on the tool")
        self.assertLess(types(events).index("tool_end"), types(events).index("error"))

    def test_disconnect_stops_the_turn(self):
        port = self.start(TOOL_SECONDS=30)
        conn, res = post(port, "/chat/stream", {"message": "q"})
        turn_id = None
        while turn_id is None:
            line = res.readline().decode()
            if line.startswith("data:"):
                turn_id = json.loads(line[5:])["turn_id"]
        res.close()  # drop the stream mid-tool, as a closed tab would
        conn.close()
        time.sleep(2.5)  # next progress or heartbeat write sees the broken pipe
        c, r = post(port, "/chat/cancel", {"turn_id": turn_id})
        c.close()
        self.assertEqual(r.status, 404, "the turn should already be gone after the client left")

    def test_legacy_endpoint_is_marked_deprecated(self):
        port = self.start(TOOL_SECONDS=1)
        conn, res = post(port, "/chat", {"message": "q"})
        body = json.loads(res.read())
        conn.close()
        self.assertEqual(res.status, 200)
        self.assertIn("answer", body)
        self.assertEqual(res.getheader("Deprecation"), "true")


@unittest.skipUnless(NODE, "node not installed")
class ClientTests(unittest.TestCase):
    def setUp(self):
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.stop()

    def test_no_total_timeout_in_client(self):
        with open(os.path.join(HERE, "client_state_machine.mjs")) as f:
            src = f.read()
        self.assertNotIn("AbortSignal.timeout(", src)

    def test_still_working_respects_expected_step_length(self):
        # A normal step (2 s, advertised 3 s) under a 1 s floor: no "still working".
        self.server = Server(TOOL_SECONDS=2, EXPECTED_S=3, NO_PROGRESS=1)
        out, _ = run_client(self.server.url, STILL_WORKING_AFTER_MS=1000, LOST_AFTER_MS=4000)
        self.assertIn("final: done", out)
        self.assertNotIn("(still working)", out)

    def test_still_working_shows_when_step_overruns(self):
        self.server = Server(TOOL_SECONDS=4, EXPECTED_S=1, NO_PROGRESS=1)
        out, _ = run_client(self.server.url, STILL_WORKING_AFTER_MS=1000, LOST_AFTER_MS=4000)
        self.assertIn("(still working)", out)
        self.assertIn("final: done", out)

    def test_progress_events_reset_still_working(self):
        self.server = Server(TOOL_SECONDS=4, EXPECTED_S=1)  # progress every 1 s
        out, _ = run_client(self.server.url, STILL_WORKING_AFTER_MS=1500, LOST_AFTER_MS=4000)
        self.assertNotIn("(still working)", out)
        self.assertIn("final: done", out)

    def test_long_turn_outlives_silence_window(self):
        # Turn is ~3x the silence window; heartbeats and progress keep it alive.
        self.server = Server(TOOL_SECONDS=6)
        out, _ = run_client(self.server.url, STILL_WORKING_AFTER_MS=1000, LOST_AFTER_MS=2000)
        self.assertIn("final: done", out)

    def test_client_ceiling_with_tool_that_ignores_cancel(self):
        self.server = Server(TOOL_SECONDS=30, TURN_CEILING_S=2, IGNORE_CANCEL=1)
        out, took = run_client(self.server.url, STILL_WORKING_AFTER_MS=1000, LOST_AFTER_MS=4000)
        self.assertIn("final: error", out)
        self.assertIn("Searching your files...:failed", out.splitlines()[-2])
        self.assertLess(took, 5)

    def test_client_cancel_with_tool_that_ignores_cancel(self):
        self.server = Server(TOOL_SECONDS=30, IGNORE_CANCEL=1)
        out, took = run_client(self.server.url, cancel_after=1500, LOST_AFTER_MS=4000)
        self.assertIn("final: cancelled", out)
        self.assertIn("Searching your files...:stopped", out)
        self.assertLess(took, 4)


if __name__ == "__main__":
    unittest.main()
