---
name: shared-ai-canvas
description: Design and build a shared canvas where a person and an AI work on the same visible document, the person points at exactly what they mean, and the AI changes only that. Covers select-then-ask (Edit With AI, comments), requests that carry their anchor, text anchors that survive edits, a resolution order that refuses rather than guesses, re-checking at apply time, tracked suggestions with accept, reject and Revert, anchored comment threads, and adapters for articles, slides, scripts and timelines. Use when asked to "add Edit With AI", "let users select text and ask the AI", "AI inline edits", "AI suggestions like track changes", "anchor comments to text", "the AI edited the wrong paragraph", "AI rewrote the whole document", "co-editing with an assistant", or "point at a slide and ask for a change".
---

# Shared AI canvas

The person and the AI work on the same visible document. The person points at exactly
what they mean, the request travels with that pointer, and the AI changes only what was
pointed at. Chat alone cannot do this: "make the second point shorter" is a guess about
which point, and a whole-document rewrite hides what changed.

## When to use

- Adding AI editing to a writing, slide, script or timeline tool.
- Fixing an assistant that edits the wrong place or rewrites more than it was asked to.
- Designing comments and review on a document an AI also edits.

## The rules

1. **Point, then ask.** Select text or a block, then press Edit With AI or add a comment.
   The chat opens with the selection pinned to the request, visibly.
2. **A request is the instruction plus its anchor**, never the instruction alone.
3. **Anchors are text, not positions.** Store the exact quote plus a little text before
   and after it (about 32 characters each), and how many copies of the quote existed.
   Character offsets are hints only.
4. **Resolve with context, in a fixed order.** Candidates are the exact matches of the
   quote, or, if there are none, matches that ignore whitespace and punctuation. Then:
   1. the recorded before and after text must agree, even when only one candidate is
      left, because a lone match can be the other copy of a quote that had duplicates
      (or a copy pasted later)
   2. if no candidate fits, a quote that was unique when selected may still land when
      one side fits (a neighbouring edit should not orphan it); a quote that had copies
      is refused
   3. the recorded occurrence (the second "ok") counts only when no context was stored
      and the number of copies is unchanged

   Exact matches are tried before tolerant ones, so a known false refusal is by design:
   if the quote had a twin and the person's own copy was re-spaced or re-punctuated, the
   untouched twin is the only exact match, its context does not fit, and the request is
   refused (`context_mismatch`) instead of finding the re-spaced copy. That is the safe
   side; the UI says "This text changed since you selected it. Select it again." and
   keeps the instruction so the person only reselects.
5. **Refuse rather than guess.** Not found, ambiguous, context no longer fits, or
   spanning a non-text block: tell the person and ask them to reselect. A patch never
   lands outside what was selected.
6. **Re-check the anchor when the change is applied.** The document may have moved on
   while the model worked; resolve again on the current version, refuse if it fails.
7. **Answer on the canvas as a tracked suggestion** on that anchor. The person accepts or
   rejects it; Revert stays available after accept. The AI never silently rewrites.
8. **Comment threads stay attached to their anchor**, with replies, mentions and resolve.
   A thread whose anchor is gone shows as detached, never moved to a new guess.

## The flow

| Step | Person sees | System does |
|---|---|---|
| Select | a highlight and an Edit With AI button | captures the anchor from the selection |
| Ask | chat opens with the quote pinned above the input | sends instruction plus anchor plus document version |
| Wait | the pinned request shows live progress and a Stop button, then a slow state and a timed-out state with Retry (the `chat-progress-feedback` skill) | model returns a replacement for the quote, not a document; Stop cancels it and leaves the document untouched |
| Review | a tracked suggestion on the highlighted span | re-resolves the anchor; refuses with a reselect prompt if it fails |
| Decide | Accept, Reject, then Revert after accept | applies one undoable change; records its id for Revert |

Ask the model for a replacement of the quote only. If a model or tool returns a whole
document anyway, diff it against the original and reject the patch unless every change
falls inside the resolved span (`change_is_confined` in the reference).

## Across media

The resolver only sees text. Each medium gets a small adapter that flattens it to one
string, marks non-text blocks with the U+FFFC character so a match across them is
refused, and maps a resolved range back to the medium's own selection.

| Medium | Anchor is |
|---|---|
| Article | a quote across paragraphs, never across an embed |
| Slides | a quote inside one text box on one slide |
| Script | a quote in one line or a run of lines in one scene |
| Timeline | one block (clip, caption, cue) or a quote in its caption |

## References

| File | What it is |
|---|---|
| `references/anchor_resolution.py` | `make_anchor`, `resolve` (the order above plus refusals), `apply_suggestion` (re-checks at apply), `change_is_confined`. Standard-library Python. |
| `references/test_anchor_resolution.py` | Unit tests: each resolution step, each refusal, a deleted or added duplicate (exact and tolerant), the by-design refusal of a re-spaced twin, apply after the document moved, and confinement. Run `python3 -m unittest test_anchor_resolution` in that folder. |
| `references/adapters-and-records.md` | The adapter contract per medium, and the request, suggestion and comment-thread record shapes. |

## Review checklist

- [ ] Every AI edit request carries an anchor; none is instruction-only.
- [ ] Anchors store quote plus before and after text; offsets never decide.
- [ ] Recorded context must fit even for a single match; a deleted duplicate is refused,
      never moved onto the surviving copy.
- [ ] Ambiguous, missing and cross-block anchors are refused with a reselect prompt.
- [ ] The anchor is resolved again at apply time on the current document.
- [ ] Changes arrive as suggestions with Accept, Reject and Revert; no silent rewrites.
- [ ] A patch that touches anything outside the selection is rejected.
- [ ] Threads keep their anchor, support replies, mentions and resolve, and show detached
      when the anchor is gone.
- [ ] The pinned request shows progress until its suggestion lands, with a Stop button,
      a slow state and a timed-out state that offers Retry (`chat-progress-feedback`).
- [ ] Builders expect the by-design false refusal: a re-spaced copy of a duplicated quote
      is refused with the reselect message, never matched to its twin.
