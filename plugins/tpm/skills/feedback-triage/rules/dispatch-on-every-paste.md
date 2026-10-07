# Dispatch the filer on every paste

Always loaded. Copy into the project's `.claude/rules/` and set the evidence root below.

Evidence root: `docs/internal-docs/` (replace with the project's root).

## Rule

Whenever the user pastes anything (command output, logs, a chat message or thread, meeting
notes, an email, review feedback, a document), in the same turn:

1. Decide what it means: meaning, who owns the next step, what is still open. That is the
   triage brief.
2. Dispatch the `feedback-triage` agent in the background, on a small, fast model named in
   the spawn, with the paste verbatim, type, subject slug, today's date, the brief, the
   evidence root, and related paths.
3. Answer the user immediately. Do not wait for the filer.

Short pastes count when they carry evidence (a log line, an error, a decision). Text that is
only an instruction to you is not a paste to file. Do not file by hand.

## Fallback

If the `feedback-triage` agent is not installed, dispatch a general-purpose agent on a
small, fast model and put the full body of the `feedback-triage` agent file (its filing
rules and hard rules) at the top of the brief.

## Verify before reporting

When the filer returns paths, check them before telling the user anything is saved:

- the file exists, and
- `grep -n '^## Raw' <path>` and `grep -n '^## Triage' <path>` both match.

Report the path only after both pass. If either fails, say so and re-dispatch once.
The filer never commits; the main session decides whether and when to commit evidence.
