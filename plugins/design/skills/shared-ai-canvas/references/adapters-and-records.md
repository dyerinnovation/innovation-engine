# Media adapters and record shapes

## Adapter contract

Each medium gets one small adapter. The resolver only ever sees text, so the adapter's job
is to turn the medium into text and back.

| Method | Does |
|---|---|
| `flatten(doc) -> (text, segments)` | One string for the whole canvas, with U+FFFC where a non-text block sits, plus a segment list mapping text ranges to block ids. |
| `scope(anchor) -> block id or none` | The block the anchor must stay inside, if the medium has hard boundaries. |
| `to_native(start, end) -> native range` | Turns a resolved text range into the medium's own selection (node path, cell, cue). |
| `apply(doc, native range, replacement)` | Writes the accepted suggestion as a normal, undoable edit. |

| Medium | Anchor is | Non-text blocks (U+FFFC) | Boundary rule |
|---|---|---|---|
| Article text | a quote inside paragraphs, headings, list items | images, embeds, code you will not let the model edit | may span paragraphs, never an embed |
| Slides | a quote inside one text box on one slide | images, charts, shapes without text | never crosses a text box or a slide |
| Script lines | a quote inside one line or a run of consecutive lines | stage directions or cues kept read-only | stays inside one scene |
| Timeline blocks | a whole block (a clip, caption or cue) or a quote in its caption text | media itself (video, audio) | one block; timing changes are a separate, explicit request |

For a whole-block anchor (a clip, a chart), the quote is the block's stable text form
(its caption or title) plus its block id; the same refuse rule applies when the block is
gone or duplicated.

## Records

Request (what travels to the model):

```json
{
  "instruction": "Make this shorter",
  "anchor": {
    "quote": "Sign-ups doubled in a week.",
    "prefix": "The launch went well. ",
    "suffix": "\n\nNext we fix onboarding.",
    "occurrence": 0, "occurrences": 1, "hint_start": 22,
    "block_id": "p-1"
  },
  "doc_version": 41
}
```

Suggestion (what comes back and sits on the canvas):

```json
{
  "id": "s-9", "anchor": { "...": "same as the request" },
  "replacement": "Sign-ups doubled.",
  "status": "pending",
  "author": "assistant", "created_at": "2026-01-01T12:00:00Z",
  "applied_change_id": null
}
```

Status moves `pending -> accepted | rejected | stale`. Accept re-resolves the anchor, then
applies; a failed re-resolve marks the suggestion `stale` and asks for a reselect. An
accepted suggestion keeps `applied_change_id` so Revert can undo exactly that change.

Comment thread:

```json
{
  "id": "c-3", "anchor": { "...": "an anchor" },
  "status": "open",
  "messages": [
    { "author": "person", "body": "@reviewer is this number right?", "mentions": ["reviewer"] },
    { "author": "assistant", "body": "The source says 2.1x; see the suggestion." }
  ]
}
```

Threads resolve and reopen; a thread whose anchor no longer resolves is shown as detached
in the thread list, never silently moved to a new spot.
