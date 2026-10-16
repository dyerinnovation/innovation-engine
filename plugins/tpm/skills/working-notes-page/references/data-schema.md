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
| `log` | array | `{t, msg}`, one line per update (keep about 40) |

## `meta`

| Field | Notes |
|---|---|
| `id` | Slug for the conversation; also the export file name and the browser storage key |
| `title`, `subtitle` | Plain words |
| `source.kind` | `chat`, `transcript` or `stream` |
| `source.evidence` | Relative link to the verbatim transcript file in the evidence folder |
| `started`, `updated` | ISO times; `updated` changes on every write |
| `revision` | Whole number, plus one on every write. Notes with `rev` equal to it show a New badge |
| `cursor` | Id of the last transcript line already processed |

## A note

| Field | Notes |
|---|---|
| `id` | Stable forever. Agent notes: kind prefix plus a counter (`d-001`, `a-001`, `q-001`, `f-001`). Person notes from the capture bar: `p-` plus a time code. Never reuse or renumber |
| `kind` | `decision`, `action`, `question` or `fact` |
| `text` | One idea, plain words, one or two sentences |
| `owner` | Required on actions. If nobody was named, write `unassigned` and also file a question asking who owns it |
| `due` | Optional date for actions |
| `status` | `open`, `done` (actions), `answered` (questions), `superseded` |
| `answer` | Optional, for answered questions; add the answering line to `src` |
| `src` | Transcript line ids the note came from (`t-0004`). Empty only for person notes |
| `supersedes`, `superseded_by` | Ids linking a replaced note and its replacement |
| `origin` | `agent` or `person` |
| `person_status` | Set by an export when a person marked an action done or reopened it in the browser |
| `rev` | Revision in which the note was added or last changed |
| `created`, `updated` | ISO times |

## A transcript line

`{id, speaker, at, text}`. Ids are `t-` plus four digits, in order, never reused. `at` is
the time offset or clock time if the source has one. `text` is verbatim; split long turns
into lines at sentence breaks so a note can point at the exact line.

## Merge rule (every update)

1. Read the current file first. If it changed since you last wrote it, someone edited it:
   work from what is there now.
2. Append new transcript lines after `cursor`. Never edit or drop an existing line.
3. For each new idea, look for an existing note of the same kind about the same thing.
   - Same idea, nothing new: add the line id to its `src`. Done.
   - Same idea, more detail (an owner, a due date, an answer): update that note in place
     and bump its `rev`, if it is an agent note.
   - The idea changed (a decision reversed, a date moved): add a new note with
     `supersedes`, and set the old note to `status: superseded` with `superseded_by`.
   - New idea: add a note with the next id for its kind.
4. Never delete a note. A note filed by mistake is set to `superseded` with no
   replacement and a log line saying why.
5. Person notes win. A note with `origin: person` (typed in the capture bar, or edited by
   hand in the file) is never rewritten, superseded or removed by the agent. If the
   conversation contradicts it, file the new note and say so in the log; the person
   decides.
6. Exports coming back: when a person hands over an exported JSON, add every note whose
   id is missing, keep its id, and apply each `person_status`. Then drop nothing.
7. Set `meta.updated`, add one to `meta.revision`, move `cursor`, and append one `log`
   line that counts what was filed.
