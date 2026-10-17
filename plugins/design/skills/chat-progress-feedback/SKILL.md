---
name: chat-progress-feedback
description: Design and build progress feedback for an AI chat or agent interface so the person is never left staring at silence. Covers the instant acknowledgement, showing thinking and each tool call as it starts, streaming the answer, a small visible state machine where every state ends, heartbeats and silence-based timeouts, "still working" and "connection lost" messages, cancel, and a Server-Sent Events reference with tests. Use when asked to "add streaming to the chat", "show tool calls in the UI", "the chat looks frozen", "the spinner never stops", "requests time out on long agent runs", "add a heartbeat", "show progress while the agent works", "add a stop button", or "make long AI turns feel responsive".
---

# Chat progress feedback

A model turn can take two seconds or five minutes. The person cannot tell a slow answer
from a dead one unless the interface tells them. The rule: never leave the person staring
at silence, and never let a spinner outlive the work behind it.

## When to use

- Building or reviewing a chat, copilot, or agent interface that calls tools or runs long.
- Debugging "it froze", "it spins forever", or "long requests time out".
- Moving a request/response chat endpoint to streaming.

## The five rules

1. **Acknowledge within a beat.** The first visible change (the message lands, a
   thinking indicator appears) happens before any slow step, even before the network call.
2. **Show the work as it happens.** Thinking, then each tool call by name as it starts
   ("Searching your files..."), then the answer streaming in word by word.
3. **Every state that starts must visibly end.** Each tool step closes as done, failed
   or stopped, even when the turn fails. Nothing spins forever.
4. **Timeouts measure silence, not total time, on every hop.** A turn may run for minutes
   as long as events keep arriving. This applies end to end: even when the task is framed
   as a proxy or server fix, find and replace every client-side total cap on the path
   (a `setTimeout` that aborts the fetch, `AbortSignal.timeout`, an HTTP library `timeout`).
   One leftover cap fails the turn no matter how well the server streams.
5. **Stop is always there.** Interrupt and cancel are available for the whole turn.

## The state machine

| State | Shows | Ends when |
|---|---|---|
| thinking | "Thinking..." indicator | first tool starts or text arrives |
| tool | the tool's label, a running step in the step list | its tool-end event closes the step |
| writing | the answer streaming in | done event |
| done | the answer; all steps closed | terminal |
| error | a plain sentence plus Try Again | terminal |
| lost | "Connection lost" plus Try Again | terminal |
| cancelled | "Stopped", partial text kept | terminal |

On any terminal state, close every step still marked running. Keep it a small explicit
machine in one place, not flags spread across components.

## Timing (starting defaults to tune, not standards)

| Signal | Default | Rule |
|---|---|---|
| Server heartbeat | every 10 to 15 s | Any event (progress or heartbeat) proves the connection is alive. |
| Heartbeat liveness | while the worker runs | Tie the heartbeat to the worker itself; stop it when the worker dies, so a dead job never looks alive. |
| "Still working" | max(8 s, the step's expected length) with no progress | Relative to the step, so a tool that normally takes 20 s does not show it on every turn. The server sends `expected_s` in `tool_start`; `tool_progress` events reset the timer, heartbeats do not. |
| Connection lost | about 45 s with no event at all | Not even a heartbeat: show a clear message plus Try Again. Every event resets this timer. |
| Turn ceiling | per product, minutes | Server-side backstop: stop the work and send an error event. |
| Cancel grace | 1 to 2 s | After cancel or ceiling, wait this long for the work to stop, then close open steps and end the turn anyway. |

Check every hop between server and browser (load balancer, reverse proxy, CDN, serverless
gateway). Each idle timeout must be longer than the heartbeat interval, or the connection
is cut mid-turn while the work is fine.

## Reference implementation: Server-Sent Events

- Add a **streaming twin** of the chat endpoint (`POST /chat/stream` next to `POST /chat`),
  same request body, answering with `text/event-stream`.
- Events are (type, data) pairs: `ack`, `thinking`, `tool_start`, `tool_end`, `text`,
  `heartbeat`, and one terminal event: `done`, `cancelled` or `error`.
- Send `ack` first, before any slow step.
- **Flush after every event**, above all right after `tool_start`, so the label shows while
  the tool runs, not after it.
- **Always send `tool_end`** for every `tool_start`, exactly once. A finally block in the
  tool is not enough: a tool that ignores the cancel flag never reaches it. Run the tool so
  the caller waits on the tool or the cancel flag, whichever comes first, and let the turn
  runner close any step still open before the terminal event. Drop events that arrive
  after the terminal one. Then kill or abandon the stuck work (its subprocess, its socket).
- Turn off proxy buffering and compression on the stream: `Cache-Control: no-cache,
  no-transform`, `X-Accel-Buffering: no`, and no gzip middleware on that route.
- Clients that disconnect cancel the work on the server.
- Use `fetch` with a stream reader on the client (the browser `EventSource` only does GET).
- **The old blocking endpoint**: move callers to the stream. If some caller cannot move
  yet, keep the old endpoint only as a thin wrapper over the same turn runner (same
  ceiling, same cancel), mark it deprecated (`Deprecation` header), and write down that it
  is still silent until the end, so every hop's timeout still applies to it. Keep its old
  response shape on every path, errors included, so old callers never render a missing
  field. Delete it when the last caller moves.

Other transports (WebSockets, hosted agent event streams, long polling) map onto the same
states and the same two client timers. Only the framing changes.

Files in `references/`:

| File | What it is |
|---|---|
| `sse_server.py` | Standard-library Python sketch: streaming endpoint, cancel, worker-tied heartbeat, turn ceiling, step closing that does not wait on a stuck tool, deprecated legacy wrapper. |
| `client_state_machine.mjs` | Framework-neutral client: states, both timers (step-relative "still working"), step closing, cancel, no total timeout. Doubles as a command-line test client. |
| `test_reference.py` | Automated cases below at short timings (`python3 -m unittest -v test_reference`). |

**Deliverables are self-contained.** The person has your output, not this skill. Adapt the
reference code into their own files (fix their `client.js`, do not describe it) and never
point them at a path inside this skill.

## Tests to run

Run `test_reference.py` (short timings, both sides) after changing the sketches. For a real
stack, run the same cases by hand, then once at real defaults through the real proxy.
Sketch switches: `HEARTBEAT_S`, `TOOL_SECONDS`, `EXPECTED_S`, `TURN_CEILING_S`,
`FAIL_TOOL=1`, `IGNORE_CANCEL=1`, `NO_PROGRESS=1`; client `LOST_AFTER_MS`,
`STILL_WORKING_AFTER_MS`.

1. **Long turn stays alive.** A turn several times longer than the silence window finishes
   as done; no connection-lost message. Also search the client for any total cap.
2. **"Still working" tracks the step.** A step that ends within its expected length never
   shows it; one that overruns without progress does; progress events keep it hidden.
3. **Dead worker surfaces fast.** Freeze the worker mid-tool (`kill -STOP` works for the
   sketch). The client shows "Connection lost" plus Try Again within the silence window,
   and the running step closes as stopped.
4. **Cancel mid-tool, including a tool that ignores cancel.** The UI shows Stopped at once.
   The server sends `tool_end` then `cancelled` within the grace period, without waiting for
   the tool. A client disconnect also ends the turn on the server.
5. **Ceiling with a tool that ignores cancel.** The step closes as failed, then the error
   event arrives at about the ceiling, not when the tool finally returns.
6. **Every step ends.** Force a tool to throw. The step shows failed, the turn shows an
   error with Try Again, and no spinner remains.
7. **Proxy check.** Repeat test 1 through the production path. It fails if any hop's idle
   timeout is shorter than the heartbeat or if a proxy buffers the stream.

## Review checklist

- [ ] First visible change happens before any slow step.
- [ ] Each tool call shows by name as it starts; the answer streams.
- [ ] Every started state ends, on success, error, cancel and lost.
- [ ] Heartbeat runs only while the worker is alive; a ceiling exists per turn.
- [ ] Client silence timer reset by every event; progress timer only by progress, and
      relative to the step's expected length.
- [ ] No client-side total timeout remains anywhere on the path.
- [ ] Cancel and ceiling close open steps without waiting on a stuck tool.
- [ ] Any legacy blocking endpoint is a deprecated wrapper or gone.
- [ ] Proxy idle timeouts are longer than the heartbeat; buffering is off.
- [ ] Stop works mid-tool and stops server work.
- [ ] Fixes live in the person's own files, with no pointers into this skill.

Pairs with `shared-ai-canvas`: a request pinned to a selection shows this progress until
its suggestion lands.
