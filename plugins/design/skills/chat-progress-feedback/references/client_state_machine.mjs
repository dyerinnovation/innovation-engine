// Reference sketch: the client side of a streaming chat turn.
//
// Framework-neutral: no UI library. The machine owns the states and the two timers; your UI
// subscribes with onChange(view) and renders whatever it gets. Works in a browser or in a
// recent Node (global fetch and ReadableStream).
//
// States: idle -> thinking -> tool -> writing -> done | error | lost | cancelled
// Rules this sketch enforces:
//   - Acknowledge at once: state becomes "thinking" before the request is even sent.
//   - Every tool step that starts is closed, even if the stream ends badly.
//   - Silence timer (lostAfterMs): reset by EVERY event, heartbeats included.
//   - Progress timer (stillWorkingAfterMs): reset only by visible progress, not heartbeats.
//   - Cancel is always available while the turn runs.
//
// Run directly for a quick check against the reference server:
//   node client_state_machine.mjs http://127.0.0.1:8787 "your question" [cancelAfterMs]

export const DEFAULTS = {
  stillWorkingAfterMs: 8000, // starting default, tune per product
  lostAfterMs: 45000,        // must be well above the server heartbeat interval
};

const TERMINAL = new Set(['done', 'error', 'lost', 'cancelled']);

export function createTurn({ baseUrl, onChange, options = {} }) {
  const opts = { ...DEFAULTS, ...options };
  const abort = new AbortController();
  const view = {
    state: 'idle',       // see the list above
    stillWorking: false, // true after the progress timer fires
    step: '',            // the line shown under the spinner
    steps: [],           // [{id, label, status: 'running' | 'ok' | 'failed' | 'stopped'}]
    text: '',
    error: null,         // {message, retryable}
    turnId: null,
  };
  let silenceTimer = null;
  let progressTimer = null;

  const emit = () => onChange && onChange({ ...view, steps: view.steps.map((s) => ({ ...s })) });

  function armSilence() {
    clearTimeout(silenceTimer);
    silenceTimer = setTimeout(() => finish('lost', {
      message: 'Connection lost. Your request may not have finished.',
      retryable: true,
    }), opts.lostAfterMs);
  }

  function armProgress() {
    clearTimeout(progressTimer);
    if (view.stillWorking) { view.stillWorking = false; }
    progressTimer = setTimeout(() => { view.stillWorking = true; emit(); }, opts.stillWorkingAfterMs);
  }

  function set(state, step) {
    view.state = state;
    if (step !== undefined) view.step = step;
  }

  function finish(state, error) {
    if (TERMINAL.has(view.state)) return;
    clearTimeout(silenceTimer);
    clearTimeout(progressTimer);
    // Every started step visibly ends, so nothing spins forever.
    for (const s of view.steps) if (s.status === 'running') s.status = state === 'done' ? 'ok' : 'stopped';
    view.stillWorking = false;
    view.error = error || null;
    set(state, state === 'done' ? '' : view.step);
    if (state !== 'done') abort.abort();
    emit();
  }

  function handle(type, data) {
    armSilence(); // any event at all proves the connection is alive
    if (type === 'heartbeat') {
      if (data.step) view.step = data.step; // keeps the "still working" line current
      emit();
      return;
    }
    armProgress(); // a real progress event
    switch (type) {
      case 'ack': view.turnId = data.turn_id; break;
      case 'thinking': set('thinking', 'Thinking...'); break;
      case 'tool_start':
        view.steps.push({ id: data.id, label: data.label || data.name, status: 'running' });
        set('tool', data.label || data.name);
        break;
      case 'tool_end': {
        const s = view.steps.find((x) => x.id === data.id);
        if (s) s.status = data.ok ? 'ok' : 'failed';
        break;
      }
      case 'text': view.text += data.delta; set('writing', 'Writing...'); break;
      case 'done': if (data.answer && !view.text) view.text = data.answer; return finish('done');
      case 'cancelled': return finish('cancelled');
      case 'error': return finish('error', data);
      default: break; // ignore unknown types so the server can add events safely
    }
    emit();
  }

  async function start(message) {
    set('thinking', 'Thinking...'); // acknowledge within a beat, before any network wait
    emit();
    armSilence();
    armProgress();
    try {
      const res = await fetch(`${baseUrl}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({ message }),
        signal: abort.signal,
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let cut;
        while ((cut = buffer.indexOf('\n\n')) >= 0) {
          const frame = buffer.slice(0, cut);
          buffer = buffer.slice(cut + 2);
          let type = 'message';
          let data = '';
          for (const line of frame.split('\n')) {
            if (line.startsWith('event:')) type = line.slice(6).trim();
            else if (line.startsWith('data:')) data += line.slice(5).trim();
          }
          try { handle(type, data ? JSON.parse(data) : {}); } catch { /* skip a bad frame */ }
        }
      }
      // The stream closed without a terminal event: say so, never leave a spinner.
      finish('lost', { message: 'Connection lost. Your request may not have finished.', retryable: true });
    } catch (err) {
      if (view.state === 'cancelled' || TERMINAL.has(view.state)) return;
      finish('lost', { message: 'Could not reach the server.', retryable: true });
    }
  }

  async function cancel() {
    if (TERMINAL.has(view.state) || view.state === 'idle') return;
    const id = view.turnId;
    finish('cancelled'); // the UI stops at once; the server is told in the background
    if (id) {
      try {
        await fetch(`${baseUrl}/chat/cancel`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ turn_id: id }),
        });
      } catch { /* closing the stream also stops the server side */ }
    }
  }

  return { start, cancel, view: () => ({ ...view }) };
}

// Minimal CLI for the tests in the skill.
if (import.meta.url === `file://${process.argv[1]}`) {
  const [baseUrl = 'http://127.0.0.1:8787', message = 'hello', cancelAfter] = process.argv.slice(2);
  const t0 = Date.now();
  const options = {};
  if (process.env.LOST_AFTER_MS) options.lostAfterMs = Number(process.env.LOST_AFTER_MS);
  if (process.env.STILL_WORKING_AFTER_MS) options.stillWorkingAfterMs = Number(process.env.STILL_WORKING_AFTER_MS);
  let last = '';
  const turn = createTurn({
    baseUrl,
    options,
    onChange: (v) => {
      const line = `${v.state}${v.stillWorking ? ' (still working)' : ''} | ${v.step} | ` +
        v.steps.map((s) => `${s.label}:${s.status}`).join(', ') + (v.error ? ` | ${v.error.message}` : '');
      if (line !== last) console.log(`${((Date.now() - t0) / 1000).toFixed(1)}s ${line}`);
      last = line;
    },
  });
  if (cancelAfter) setTimeout(() => turn.cancel(), Number(cancelAfter));
  await turn.start(message);
  console.log(`final: ${turn.view().state} text="${turn.view().text}"`);
}
