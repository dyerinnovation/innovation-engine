---
name: working-notes-page
description: Turn an ongoing conversation (this chat, a pasted meeting transcript, or a transcript file that keeps growing) into a detailed, self-contained HTML working-notes page that files every new piece into the right section on its own (decisions, actions with owners, open questions, key facts) with a link back to the transcript line it came from, and keeps updating as the conversation goes on. Triggers on "take notes", "keep notes on this", "live notes", "meeting notes", "working notes", "notes page", "turn this transcript into notes", "file this into the notes", "keep the notes updated", "capture decisions and action items", "who owns what", or any meeting transcript pasted while a notes page is open.
---

# Working notes page

The goal: anything said in the chat or a transcript lands in the right place on one page,
automatically, with a source link, and nothing a person captured is ever lost. The page is
one HTML file; all content lives in one JSON block inside it that this skill rewrites.

Template: `references/working-notes-template.html`. Schema and merge rule:
`references/data-schema.md`.

## Step 0: Resolve the design system
If the design plugin is installed, run `design-system-resolution`. Otherwise: use the system the user names; else the project's own (a tokens or theme file, a design-system page, a brand skill); else the neutral default theme in this skill's template. Say in one line which one you used, and ask only when two or more are found.

Map the chosen tokens into the THEME TOKENS `:root` block only (light `--l-*`, dark `--d-*`,
brand fill, one dot color per note kind, fonts). Check 4.5:1 text contrast in both themes.

## When to use

- A meeting transcript is pasted or streamed, in one go or in chunks.
- The chat itself is a working session and the person wants notes kept as it goes.
- Not for a one-off summary nobody will update (write a short doc), and not for tracking
  lanes of agent work (use `tpm:sprint-board`).

## Start a page

1. Copy the template to the notes folder (default `<evidence root>/working-notes/<slug>.html`).
2. Clear the sample data. Set `meta`: `id`, `title`, `subtitle`, `source.kind`
   (`chat`, `transcript` or `stream`), `started`, `revision: 0`.
3. Save the raw transcript verbatim to the evidence folder (below) and set
   `meta.source.evidence` to a relative link to that file.
4. Run the update loop on everything so far. Tell the person the page path.

## Update loop (every new chunk)

A chunk is each new turn in live chat mode, each paste, or each new set of lines in a
growing transcript file (read from `meta.cursor`).

1. Save the chunk verbatim to the evidence folder first.
2. Split it into transcript lines (`t-0001` onward), one per sentence, and append them.
   Use the exact splitting rule in the schema so reruns give the same ids.
3. Classify every idea in the chunk and file it:

| Kind | File it when someone | Example |
|---|---|---|
| Decision | agrees on a choice or a direction | "Then we go with titles only" |
| Action | says someone will do something | "I'll draft it by Monday" |
| Question | raises something nobody settled | "Do archived notes show up?" |
| Fact | states a number, date, limit or name as true | "The freeze is on the 13th" |

   Small talk and filler stay in the transcript only. A question answered later is set to
   `answered` with the answer and its line added to `src`.
4. Dedupe the new notes against each other and the page (schema, Dedupe): one idea gets
   one note of one kind, with all its lines in `src`.
5. Merge by the rule in `references/data-schema.md`: never delete, mark superseded,
   person notes win. A new agent note's id is its kind letter plus its first source line
   (`f-t0007`), so ids match across runs and merges, unlike a counter that depends on
   filing order.
6. Bump `revision`, give this revision its own fresh UTC time (on `meta.updated`, the log
   line and the notes it touched; never shared with another revision), move `cursor`, and
   rewrite only the JSON block.
7. Reply in one line: what was filed ("2 actions, 1 decision; f-t0002 superseded").

Classify with the strongest or mid-tier model class in the main session; never hand
meaning to a small model.

## Note rules

- One idea, one note. Split "we chose X and the designer will do Y" into a decision and an
  action, but never file one idea twice: a problem with a fix is just the action, and
  "check with X" is a question or an action, not both. Duplicates make counts and the
  open list lie.
- Plain words, the speaker's meaning, no filler. One or two sentences.
- An owner on every action. If none was named: owner `unassigned`, plus a question
  "Who owns X?".
- A source link on every agent note: the transcript line ids it came from.
- Never invent. An owner, a date, an answer, `done` or `answered` needs a line that says
  so. "Who owns X?" stays open until someone is named; an unowned action stays
  `unassigned`, even if it seems finished. A wrong "done" is worse than an open item.
- Due dates: `due` is an ISO date only when the line gives a resolvable date ("Friday"
  against the meeting date); otherwise put the words in `due_text`. All stored times are UTC.
- No secrets: redact keys, passwords and tokens to `<redacted>` in notes and transcript.

## A note the person dictates in chat

When the person says "add a note: ..." in chat, stand in for the capture bar: file it as a
person note (`p-` id, `origin: person`, `via: chat`, no `src`), log it, and treat it as
theirs from then on, so later merges never rewrite it. Details: schema merge step 7.

## Pairs with feedback-triage

The raw transcript is evidence. If `tpm:feedback-triage` is set up, dispatch its filer in
the background with each chunk (type: meeting notes, or messages for a chat) and use the
path it returns as `meta.source.evidence`. Otherwise write it yourself to
`<evidence root>/meeting-notes/<M-D-YY>/<subject>.md` (chats go under `messages/`),
appending each chunk under `## Raw`. The page links that file; each note links its lines.

## What the page does (already in the template)

- Four sections with counts, kind filter chips and search; a New badge on this revision.
- Each note shows its id, owner, due date, status and source line chips; tap a chip to
  jump to the highlighted line, or Show Excerpt to read it inline.
- Capture bar for manual notes (an action needs an owner). They are kept in this browser
  until merged, marked "Added here, not merged". Actions can be marked done.
- Export Markdown, Export JSON and Copy Markdown, all offline. To merge browser notes,
  the person exports JSON and hands it back; the skill folds it in (merge rule step 6).
- Superseded notes, the full transcript and the update log sit in collapsed panels.
- Light and dark from one token block; one column at phone width.

## Verify before saying it is updated

- The JSON block parses, and every `src` id exists in `transcript`.
- No note was removed and no person note changed (compare ids and texts with the read).
- No two live notes say the same thing; no `due` that is not an ISO date; no `answered`
  or `done` without a source line or a person behind it.
- Agent note ids follow the first-source-line rule; each revision's time is unique and
  later than the one before.
- Open the page once at desktop and phone width: sections render and a source chip jumps.
  Use a headless browser and send every file it writes (screenshots, snapshots, console
  logs) into the output folder, for example `<notes folder>/preview/`, or into a temp
  dir you delete afterwards. Never the repo root or a browser tool's default folder:
  stray preview files end up committed or mistaken for evidence.
