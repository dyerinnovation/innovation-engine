# Working notes: data schema and merge rule

The page holds all of its content in one JSON block:
`<script type="application/json" id="notes-data">`. The skill rewrites only that block.
Fields may be added; never rename or remove one.

## Top level

| Field | Type | Notes |
|---|---|---|
| `schema` | number | `1` |
| `meta` | object | See below |
| `notes` | array | Every note ever filed, superseded ones included |
| `transcript` | array | Every transcript line ever filed, in order |
| `log` | array | `{t, rev, msg}`, one line per revision (keep about 40). `t` is that revision's own UTC ISO time; the page shows it as HH:MM UTC |

## `meta`

| Field | Notes |
|---|---|
| `id` | Slug for the conversation; also the export file name and the browser storage key |
| `title`, `subtitle` | Plain words |
| `source.kind` | `chat`, `transcript` or `stream` |
| `source.evidence` | Relative link to the verbatim transcript file in the evidence folder |
| `started`, `updated` | ISO times; `updated` is the time of the latest revision |
| `tz` | Optional. The meeting's local zone (for example `UTC-7`), used only to resolve spoken dates like "Friday" |
| `revision` | Whole number, plus one on every write. Notes with `rev` equal to it show a New badge |
| `cursor` | Id of the last transcript line already processed |

## A note

| Field | Notes |
|---|---|
| `id` | Stable forever; see Note ids below. Agent notes: kind letter plus the first source line (`f-t0007`). Person notes: `p-` plus a time code. Never reuse or renumber |
| `kind` | `decision`, `action`, `question` or `fact` |
| `text` | One idea, plain words, one or two sentences |
| `owner` | Required on actions. If nobody was named, write `unassigned` and also file a question asking who owns it |
| `due` | Optional. An ISO date (`2030-03-08`) and nothing else, set only when the transcript gives a date you can resolve against the meeting date (a weekday, "tomorrow", a calendar date) |
| `due_text` | Optional. The deadline in the speaker's words, lower case, when it is not a single date ("before the freeze", "end of month"). Kept next to `due` when both apply |
| `status` | `open`, `done` (actions), `answered` (questions), `superseded`. `done` and `answered` need a transcript line (or a person) that says so; see Evidence below |
| `answer` | Optional, for answered questions: what was said, not a guess. Add the answering line to `src` |
| `src` | Transcript line ids the note came from (`t-0004`). Empty only for person notes |
| `supersedes`, `superseded_by` | Ids linking a replaced note and its replacement |
| `origin` | `agent` or `person` |
| `via` | Person notes only: `capture` (typed in the page), `chat` (dictated to the agent in chat) or `file` (edited by hand) |
| `person_status` | Set by an export when a person marked an action done or reopened it in the browser |
| `rev` | Revision in which the note was added or last changed |
| `created`, `updated` | ISO times of the revision that filed and last changed the note (person notes: the capture time) |

## Note ids

An agent note's id is its kind letter (`d`, `a`, `q`, `f`) plus the lowest transcript
line id in its `src` when it is first filed: a fact from `t-0007` is `f-t0007`, a
decision from `t-0004` and `t-0005` is `d-t0004`. If that id is taken by another note of
the same kind, add `-2`, `-3` in line order. Transcript ids are fixed by the splitting
rule, so the same transcript gives the same note ids on every run and in every merge,
whatever order the notes were filed in; a counter would not. The id never changes later,
even when more lines join `src`. A replacement note (supersedes) gets its own id from its
own first line.

## Times

Every stored time (`started`, `updated`, `created`, log `t`) is a UTC ISO string ending in
`Z`. One convention means the log, the notes and the meta never disagree about when
something happened, whatever machine wrote them. Only `at` on a transcript line keeps the
source's own clock or offset, verbatim.

Each revision gets its own time: the moment that write happens. `meta.updated`, the log
line for that revision, and `created` or `updated` on every note it filed or changed all
carry that one time, and it is later than the previous revision's. Never stamp two
revisions with the same time, even when several chunks are processed in one sitting; and
a person note keeps its capture time, so it can sit between two revisions, never after
the one that merged it.

## A transcript line

`{id, speaker, at, text}`. Ids are `t-` plus four digits, in order, never reused. `at` is
the time offset or clock time if the source has one (repeat it on every line split from
the same turn). `text` is verbatim.

Splitting rule, the same on every run: one line per sentence. A sentence ends at `.`, `?`
or `!` followed by a space or the end of the turn; a turn with no such mark is one line.
Do not merge short sentences or split inside one. A fixed rule means the same transcript
always gets the same ids, so source chips stay exact across updates and reruns.

## Evidence

Status and fields change only on evidence. A question becomes `answered` when a line
answers it; an action becomes `done` when a line says it is done (or a person marks it).
An owner, a due date or an answer is filled in only from a line that states it. A
question like "Who owns X?" stays `open` until someone is named as owner; at that point
set the action's `owner` from the same line and answer the question with it. If you only
infer something, leave the field empty and, if it matters, file a question.

## Merge rule (every update)

1. Read the current file first. If it changed since you last wrote it, someone edited it:
   work from what is there now.
2. Append new transcript lines after `cursor`. Never edit or drop an existing line.
3. For each new idea, look for an existing note about the same thing, of any kind
   (see Dedupe below), before adding one.
   - Same idea, nothing new: add the line id to its `src`. Done.
   - Same idea, more detail (an owner, a due date, an answer): update that note in place
     and bump its `rev`, if it is an agent note.
   - The idea changed (a decision reversed, a date moved): add a new note with
     `supersedes`, and set the old note to `status: superseded` with `superseded_by`.
   - New idea: add a note whose id comes from its first source line (Note ids above).
4. Never delete a note. A note filed by mistake is set to `superseded` with no
   replacement and a log line saying why.
5. Person notes win. A note with `origin: person` (typed in the capture bar, or edited by
   hand in the file) is never rewritten, superseded or removed by the agent. If the
   conversation contradicts it, file the new note and say so in the log; the person
   decides.
6. Exports coming back: when a person hands over an exported JSON, add every note whose
   id is missing, keep its id, and apply each `person_status`. Then drop nothing.
7. Notes the person dictates in chat ("add a note: ..."): file as a person note, not an
   agent note. Id `p-` plus a time code, `origin: person`, `via: chat`, `src: []` (the
   chat is not the transcript), owner only if the person named one, `rev` set to the new
   revision. Write the text as given. Log it: "Added p-... for the person (chat)." From
   then on it falls under step 5.
8. Add one to `meta.revision`, take a fresh UTC time for this revision (Times above),
   set `meta.updated` to it, move `cursor`, and append one `log` line `{t, rev, msg}`
   that counts what was filed.

## Dedupe (one idea, one note)

Run this over the new notes before writing:

- A problem that leads straight to a fix ("webhooks fail, I'll patch it Friday") is one
  action. The problem goes in the action text. File a separate fact only for a number,
  limit or name that stays true after the action is done.
- "Ask X" or "check with X" is either a question or an action, never both. If someone took
  it, it is an action. If nobody did, it is one open question whose text names who must be
  asked ("Show tax in the picker? Finance must confirm").
- The same question raised twice, or worded two ways, is one question with both lines in
  `src`.
- The one allowed pair: an action with owner `unassigned` plus its "Who owns X?" question.
- Two notes whose `src` lists are the same line ids are a warning sign; keep one unless
  the line truly holds two ideas (a decision and a separate action).
