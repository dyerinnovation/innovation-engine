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
2. Split it into transcript lines (`t-0001` onward) and append them.
3. Classify every idea in the chunk and file it:

| Kind | File it when someone | Example |
|---|---|---|
| Decision | agrees on a choice or a direction | "Then we go with titles only" |
| Action | says someone will do something | "I'll draft it by Monday" |
| Question | raises something nobody settled | "Do archived notes show up?" |
| Fact | states a number, date, limit or name as true | "The freeze is on the 13th" |

   Small talk and filler stay in the transcript only. A question answered later is set to
   `answered` with the answer and its line added to `src`.
4. Merge by the rule in `references/data-schema.md`: stable ids, never delete, mark
   superseded, person notes win.
5. Bump `revision`, move `cursor`, add one log line, and rewrite only the JSON block.
6. Reply in one line: what was filed ("2 actions, 1 decision; f-002 superseded").

Classify with the strongest or mid-tier model class in the main session; never hand
meaning to a small model.

## Note rules

- One idea per note. Split "we chose X and the designer will do Y" into a decision and an action.
- Plain words, the speaker's meaning, no filler. One or two sentences.
- An owner on every action. If none was named: owner `unassigned`, plus a question
  "Who owns X?".
- A source link on every agent note: the transcript line ids it came from.
- Never invent an owner, a date or a decision the transcript does not hold.
- No secrets: redact keys, passwords and tokens to `<redacted>` in notes and transcript.

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
- Open the page once at desktop and phone width: sections render and a source chip jumps.
