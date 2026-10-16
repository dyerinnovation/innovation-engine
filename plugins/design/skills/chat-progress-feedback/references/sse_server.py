"""Reference sketch: a streaming chat endpoint over Server-Sent Events.

Framework-neutral on purpose (Python standard library only). Port the shape, not the code:
the same events and rules apply to any web framework, WebSockets, or a hosted agent's event
stream.

Endpoints
  POST /chat          the ordinary request/response endpoint (returns the final answer)
  POST /chat/stream   its streaming twin: same body, answers with text/event-stream
  POST /chat/cancel   body {"turn_id": "..."}: stops a running turn

Events, as (type, data) pairs, one JSON object per data line:
  ack         {"turn_id"}                    first byte, sent before any slow step
  thinking    {}                             the model is planning
  tool_start  {"id", "name", "label"}        a tool call began ("Searching your files...")
  tool_end    {"id", "ok", "summary"}        ALWAYS sent for every tool_start, even on failure
  text        {"delta"}                      answer text, streamed as it is written
  heartbeat   {"step"}                       keep-alive while work is really running
  done        {"answer"}                     terminal: success
  cancelled   {}                             terminal: the person stopped it
  error       {"message", "retryable"}       terminal: failure or ceiling reached

Run:  python3 sse_server.py            (port 8787)
Tune: HEARTBEAT_S, TURN_CEILING_S, TOOL_SECONDS, PORT environment variables.
FAIL_TOOL=1 makes the demo tool throw (to test that every step still ends).
"""

import json
import os
import queue
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HEARTBEAT_S = float(os.environ.get("HEARTBEAT_S", "12"))        # every 10 to 15 s
TURN_CEILING_S = float(os.environ.get("TURN_CEILING_S", "600"))  # server-side backstop
TOOL_SECONDS = float(os.environ.get("TOOL_SECONDS", "3"))       # demo tool duration
PORT = int(os.environ.get("PORT", "8787"))

TERMINAL = {"done", "cancelled", "error"}
TURNS = {}  # turn_id -> threading.Event (cancel flag)


class Cancelled(Exception):
    pass


def demo_worker(message, emit, cancel, state):
    """Stand-in for the real agent loop. Emits progress; checks cancel between steps."""

    def step(label):
        state["step"] = label
        if cancel.is_set():
            raise Cancelled()

    step("Thinking...")
    emit("thinking", {})
    time.sleep(0.5)

    tool_id = "t1"
    step("Searching your files...")
    emit("tool_start", {"id": tool_id, "name": "search_files", "label": "Searching your files..."})
    ok, summary = False, "did not finish"
    try:
        # A long tool must be interruptible: wait on the cancel flag instead of sleeping.
        if cancel.wait(TOOL_SECONDS):
            raise Cancelled()
        if os.environ.get("FAIL_TOOL"):
            raise RuntimeError("the search tool failed")
        ok, summary = True, "3 matches"
    finally:
        emit("tool_end", {"id": tool_id, "ok": ok, "summary": summary})  # never skipped

    step("Writing...")
    answer = ""
    for word in ("Here", " is", " what", " I", " found", " about: ", message):
        step("Writing...")
        emit("text", {"delta": word})
        answer += word
        time.sleep(0.1)
    return answer


def run_turn(message, emit, cancel):
    """Runs the worker in its own thread; heartbeats only while that thread is alive."""
    state = {"step": "Starting", "result": None, "error": None}

    def target():
        try:
            state["result"] = demo_worker(message, emit, cancel, state)
        except Cancelled:
            state["error"] = "cancelled"
        except Exception as exc:  # report, never hang
            state["error"] = str(exc) or exc.__class__.__name__

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    started = time.monotonic()
    while worker.is_alive():
        worker.join(HEARTBEAT_S)
        if not worker.is_alive():
            break
        if time.monotonic() - started > TURN_CEILING_S:
            cancel.set()
            emit("error", {"message": "This took too long and was stopped.", "retryable": True})
            return
        # Liveness is tied to the worker thread: a dead worker stops the heartbeat.
        emit("heartbeat", {"step": state["step"]})

    if state["error"] == "cancelled":
        emit("cancelled", {})
    elif state["error"]:
        print("turn failed:", state["error"], flush=True)  # details go to logs, not the person
        emit("error", {"message": "Something went wrong while working on this.", "retryable": True})
    elif state["result"] is None:
        emit("error", {"message": "The worker stopped without an answer.", "retryable": True})
    else:
        emit("done", {"answer": state["result"]})


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except ValueError:
            return {}

    def _json(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path == "/chat/cancel":
            flag = TURNS.get(self._body().get("turn_id", ""))
            if flag:
                flag.set()
            return self._json(202 if flag else 404, {"cancelled": bool(flag)})
        if self.path == "/chat":
            events = []
            run_turn(self._body().get("message", ""), lambda t, d: events.append((t, d)), threading.Event())
            last = events[-1] if events else ("error", {})
            return self._json(200 if last[0] == "done" else 500, last[1])
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
        threading.Thread(target=run_turn, args=(message, lambda t, d: out.put((t, d)), cancel), daemon=True).start()

        def send(event_type, data):
            frame = "event: %s\ndata: %s\n\n" % (event_type, json.dumps(data))
            self.wfile.write(frame.encode())
            self.wfile.flush()  # flush every event, above all right after tool_start

        try:
            send("ack", {"turn_id": turn_id})
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
