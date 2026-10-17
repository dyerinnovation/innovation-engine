"""Reference sketch: a streaming chat endpoint over Server-Sent Events.

Framework-neutral on purpose (Python standard library only). Port the shape, not the code:
the same events and rules apply to any web framework, WebSockets, or a hosted agent's event
stream. Copy what you need into your own server; do not import this file from a product.

Endpoints
  POST /chat/stream   the streaming endpoint: answers with text/event-stream
  POST /chat/cancel   body {"turn_id": "..."}: stops a running turn
  POST /chat          legacy blocking endpoint, kept only as a thin wrapper over the same
                      turn runner for callers that cannot stream yet. It still sends nothing
                      until the turn ends, so every hop's timeout still applies to it. Move
                      callers to /chat/stream, then delete it.

Events, as (type, data) pairs, one JSON object per data line:
  ack            {"turn_id"}                 first byte, sent before any slow step
  thinking       {}                          the model is planning
  tool_start     {"id", "name", "label", "expected_s"}
                                             a tool call began; expected_s is how long a normal
                                             run takes, so the client can time "still working"
                                             against it instead of a fixed number
  tool_progress  {"id", "note"}              the running tool moved forward
  tool_end       {"id", "ok", "summary"}     sent exactly once for every tool_start, even on
                                             failure, cancel, or ceiling
  text           {"delta"}                   answer text, streamed as it is written
  heartbeat      {"step"}                    keep-alive while work is really running
  done           {"answer"}                  terminal: success
  cancelled      {}                          terminal: the person stopped it
  error          {"message", "retryable"}    terminal: failure or ceiling reached

Run:  python3 sse_server.py            (port 8787)
Tune: HEARTBEAT_S, TURN_CEILING_S, CANCEL_GRACE_S, TOOL_SECONDS, EXPECTED_S, PORT.
Demo switches:
  NO_PROGRESS=1    the tool sends no tool_progress (to see "still working" past expected_s)
  FAIL_TOOL=1      the tool throws halfway (every step must still end)
  IGNORE_CANCEL=1  the tool never checks the cancel flag (cancel and ceiling must still
                   close the step and the turn without waiting for it)
"""

import json
import os
import queue
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HEARTBEAT_S = float(os.environ.get("HEARTBEAT_S", "12"))         # every 10 to 15 s
TURN_CEILING_S = float(os.environ.get("TURN_CEILING_S", "600"))   # server-side backstop
CANCEL_GRACE_S = float(os.environ.get("CANCEL_GRACE_S", "2"))     # wait this long for work to stop
TOOL_SECONDS = float(os.environ.get("TOOL_SECONDS", "3"))        # demo tool duration
EXPECTED_S = float(os.environ.get("EXPECTED_S", str(TOOL_SECONDS + 1)))  # what tool_start advertises
PORT = int(os.environ.get("PORT", "8787"))

TERMINAL = {"done", "cancelled", "error"}
TURNS = {}  # turn_id -> threading.Event (cancel flag)


class Cancelled(Exception):
    pass


class Turn:
    """One turn's shared state. Owns the open-step list so any thread can close steps.

    Why: a tool that ignores cancel can block its thread forever. If only that thread could
    send tool_end, a cancel or ceiling would leave the step spinning. Here the turn runner can
    close every open step itself, and late events from abandoned threads are dropped.
    """

    def __init__(self, emit, cancel):
        self._emit = emit
        self.cancel = cancel
        self.lock = threading.Lock()
        self.open_steps = {}  # tool id -> label
        self.finished = False
        self.step = "Starting"

    def emit(self, event_type, data):
        with self.lock:
            if self.finished:
                return  # the turn already ended: drop late events from stuck threads
            if event_type in TERMINAL:
                self.finished = True
            self._emit(event_type, data)

    def open_step(self, tool_id, name, label, expected_s):
        with self.lock:
            self.open_steps[tool_id] = label
        self.step = label
        self.emit("tool_start", {"id": tool_id, "name": name, "label": label, "expected_s": expected_s})

    def close_step(self, tool_id, ok, summary):
        """Idempotent: the first close wins, later ones are no-ops."""
        with self.lock:
            if self.open_steps.pop(tool_id, None) is None:
                return
        self.emit("tool_end", {"id": tool_id, "ok": ok, "summary": summary})

    def close_all(self, summary):
        with self.lock:
            ids = list(self.open_steps)
        for tool_id in ids:
            self.close_step(tool_id, False, summary)


def run_tool(turn, tool_id, name, label, expected_s, fn):
    """Runs one tool so cancel works even when the tool itself ignores it.

    The tool runs in its own thread; this caller waits on whichever comes first, the tool or
    the cancel flag. On cancel it closes the step and returns at once. The stuck thread is
    left behind (daemon); in real code also kill its subprocess or close its connection.
    """
    turn.open_step(tool_id, name, label, expected_s)
    box = {}
    done = threading.Event()

    def progress(note):
        if not turn.cancel.is_set():
            turn.emit("tool_progress", {"id": tool_id, "note": note})

    def target():
        try:
            box["result"] = fn(turn.cancel, progress)
        except Cancelled:
            box["cancelled"] = True
        except Exception as exc:  # report, never hang
            box["error"] = exc
        finally:
            done.set()

    threading.Thread(target=target, daemon=True).start()
    while not done.wait(0.1):
        if turn.cancel.is_set():
            turn.close_step(tool_id, False, "stopped")
            raise Cancelled()
    if box.get("cancelled") or turn.cancel.is_set():
        turn.close_step(tool_id, False, "stopped")
        raise Cancelled()
    if "error" in box:
        turn.close_step(tool_id, False, "failed")
        raise box["error"]
    turn.close_step(tool_id, True, box["result"])
    return box["result"]


def demo_search(cancel, progress):
    """Stand-in for a slow tool. Reports progress each second; checks cancel unless told not to."""
    ignore_cancel = bool(os.environ.get("IGNORE_CANCEL"))
    deadline = time.monotonic() + TOOL_SECONDS
    halfway = time.monotonic() + TOOL_SECONDS / 2
    scanned = 0
    while time.monotonic() < deadline:
        pause = min(1.0, max(0.0, deadline - time.monotonic()))
        if ignore_cancel:
            time.sleep(pause)
        elif cancel.wait(pause):
            raise Cancelled()
        scanned += 1
        if not os.environ.get("NO_PROGRESS"):
            progress("%d folders scanned" % scanned)
        if os.environ.get("FAIL_TOOL") and time.monotonic() >= halfway:
            raise RuntimeError("the search tool failed")
    return "3 matches"


def demo_worker(message, turn):
    """Stand-in for the real agent loop."""

    def check():
        if turn.cancel.is_set():
            raise Cancelled()

    turn.step = "Thinking..."
    turn.emit("thinking", {})
    time.sleep(0.5)
    check()

    run_tool(turn, "t1", "search_files", "Searching your files...", EXPECTED_S, demo_search)

    turn.step = "Writing..."
    answer = ""
    for word in ("Here", " is", " what", " I", " found", " about: ", message):
        check()
        turn.emit("text", {"delta": word})
        answer += word
        time.sleep(0.1)
    return answer


def run_turn(message, emit, cancel):
    """Runs the worker in its own thread, heartbeats only while it is alive, and always ends
    the turn with exactly one terminal event, even if the worker never returns."""
    turn = Turn(emit, cancel)
    state = {"result": None, "error": None}

    def target():
        try:
            state["result"] = demo_worker(message, turn)
        except Cancelled:
            state["error"] = "cancelled"
        except Exception as exc:  # report, never hang
            state["error"] = str(exc) or exc.__class__.__name__

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    started = last_beat = time.monotonic()
    stop_reason = None  # "cancel" or "ceiling"
    stop_at = None
    while worker.is_alive():
        worker.join(0.1)
        now = time.monotonic()
        if stop_reason is None and cancel.is_set():
            stop_reason, stop_at = "cancel", now
        if stop_reason is None and now - started > TURN_CEILING_S:
            stop_reason, stop_at = "ceiling", now
            cancel.set()
        if stop_reason and now - stop_at > CANCEL_GRACE_S:
            break  # the work did not stop in time: close the turn without it
        if not stop_reason and worker.is_alive() and now - last_beat >= HEARTBEAT_S:
            # Liveness is tied to the worker thread: a dead worker stops the heartbeat.
            turn.emit("heartbeat", {"step": turn.step})
            last_beat = now

    # Close any step the worker left open (stuck tool, crash) before the terminal event.
    turn.close_all("stopped" if stop_reason else "did not finish")
    if stop_reason == "ceiling":
        turn.emit("error", {"message": "This took too long and was stopped.", "retryable": True})
    elif stop_reason == "cancel" or state["error"] == "cancelled":
        turn.emit("cancelled", {})
    elif state["error"]:
        print("turn failed:", state["error"], flush=True)  # details go to logs, not the person
        turn.emit("error", {"message": "Something went wrong while working on this.", "retryable": True})
    elif state["result"] is None:
        turn.emit("error", {"message": "The worker stopped without an answer.", "retryable": True})
    else:
        turn.emit("done", {"answer": state["result"]})


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except ValueError:
            return {}

    def _json(self, code, payload, headers=()):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path == "/chat/cancel":
            flag = TURNS.get(self._body().get("turn_id", ""))
            if flag:
                flag.set()
            return self._json(202 if flag else 404, {"cancelled": bool(flag)})
        if self.path == "/chat":
            # Legacy: same runner and ceiling, but silent until the end. Kept for old callers only.
            events = []
            run_turn(self._body().get("message", ""), lambda t, d: events.append((t, d)), threading.Event())
            last = events[-1] if events else ("error", {})
            return self._json(200 if last[0] == "done" else 500, last[1],
                              headers=[("Deprecation", "true"), ("Link", '</chat/stream>; rel="successor-version"')])
        if self.path == "/chat/stream":
            return self._stream(self._body().get("message", ""))
        self._json(404, {"error": "not found"})

    def _stream(self, message):
        turn_id = uuid.uuid4().hex
        cancel = threading.Event()
        TURNS[turn_id] = cancel
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Accel-Buffering", "no")  # tells nginx-style proxies not to buffer
        self.send_header("Connection", "close")
        self.end_headers()

        out = queue.Queue()

        def send(event_type, data):
            frame = "event: %s\ndata: %s\n\n" % (event_type, json.dumps(data))
            self.wfile.write(frame.encode())
            self.wfile.flush()  # flush every event, above all right after tool_start

        try:
            send("ack", {"turn_id": turn_id})  # before the worker even starts
            threading.Thread(target=run_turn, args=(message, lambda t, d: out.put((t, d)), cancel),
                             daemon=True).start()
            while True:
                event_type, data = out.get()
                send(event_type, data)
                if event_type in TERMINAL:
                    break
        except (BrokenPipeError, ConnectionResetError):
            cancel.set()  # the client left: stop the work, do not keep paying for it
        finally:
            TURNS.pop(turn_id, None)
            self.close_connection = True

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("listening on http://127.0.0.1:%d" % PORT, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
