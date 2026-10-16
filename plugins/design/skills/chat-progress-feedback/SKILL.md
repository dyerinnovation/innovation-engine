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
4. **Timeouts measure silence, not total time.** A turn may run for minutes as long as
   events keep arriving. A turn that goes quiet is the problem.
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
| "Still working" | about 8 s with no visible progress | Show "still working" with the current step. Heartbeats do not reset this timer; progress events do. |
| Connection lost | about 45 s with no event at all | Not even a heartbeat: show a clear message plus Try Again. Every event resets this timer. |
| Turn ceiling | per product, minutes | Server-side backstop: stop the work and send an error event. |

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
- **Always send `tool_end`** for every `tool_start` (use a finally block).
- Turn off proxy buffering and compression on the stream: `Cache-Control: no-cache,
  no-transform`, `X-Accel-Buffering: no`, and no gzip middleware on that route.
- Clients that disconnect cancel the work on the server.
- Use `fetch` with a stream reader on the client (the browser `EventSource` only does GET).

Other transports (WebSockets, hosted agent event streams, long polling) map onto the same
states and the same two client timers. Only the framing changes.

Files in `references/`:

| File | What it is |
|---|---|
| `sse_server.py` | Standard-library Python sketch: streaming twin, cancel endpoint, worker-tied heartbeat, turn ceiling, flush and always-close rules. |
| `client_state_machine.mjs` | Framework-neutral client: states, both timers, step closing, cancel. Doubles as a command-line test client. |

## Tests to run

Run the reference server and client with short timings first
(`HEARTBEAT_S=1 TOOL_SECONDS=7`, client `LOST_AFTER_MS=4000 STILL_WORKING_AFTER_MS=2000`),
then once at real defaults against your own stack, through the real proxy.

1. **Long turn stays alive.** A turn of 3 minutes or more (a slow tool, or `TOOL_SECONDS=200`)
   finishes as done. "Still working" appears during the long step; no connection-lost
   message appears.
2. **Dead worker surfaces fast.** Freeze or kill the worker mid-tool (`kill -STOP` on the
   server process works for the sketch). The client shows "Connection lost" plus Try Again
   within the silence window, and the running step closes as stopped.
3. **Cancel mid-tool.** Press Stop while a tool runs. The UI shows Stopped at once, the
   step closes, the server sends `tool_end` and stops the work (check its logs or a counter).
4. **Every step ends.** Force a tool to throw (`FAIL_TOOL=1` in the sketch). The step shows failed, the turn shows an
   error with Try Again, and no spinner remains.
5. **Proxy check.** Repeat test 1 through the production path. It fails if any hop's idle
   timeout is shorter than the heartbeat or if a proxy buffers the stream.

## Review checklist

- [ ] First visible change happens before any slow step.
- [ ] Each tool call shows by name as it starts; the answer streams.
- [ ] Every started state ends, on success, error, cancel and lost.
- [ ] Heartbeat runs only while the worker is alive; a ceiling exists per turn.
- [ ] Client silence timer reset by every event; progress timer only by progress.
- [ ] Proxy idle timeouts are longer than the heartbeat; buffering is off.
- [ ] Stop works mid-tool and stops server work.

Pairs with `shared-ai-canvas`: a request pinned to a selection shows this progress until
its suggestion lands.
