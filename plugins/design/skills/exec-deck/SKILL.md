---
name: exec-deck
description: Build an executive slide deck as branded 16:9 HTML first, then convert it to an editable native PowerPoint (.pptx), with every slide rendered to an image and checked before it ships. Bottom line up front, one idea per slide, big numbers over prose, sourced numbers. Triggers on "make an exec deck", "build a deck for leadership", "board deck", "steering committee slides", "executive presentation", "pitch slides", "decision deck", "turn this into slides", "make it a PowerPoint", "export the deck to pptx", or "rebrand this deck".
---

# Exec deck

Write the deck as one HTML file (one `<section class="slide">` per slide), check it by
looking at every slide, then build an editable .pptx from the same file. The HTML is the
source of truth; the .pptx is generated, never hand-edited first.

Files in this skill:

| File | Use |
|---|---|
| `references/deck-template.html` | Start here. Theme tokens in one `:root` block, six layouts, the authoring contract in a comment |
| `scripts/build_pptx.py` | HTML (or JSON) to editable .pptx with native bullets. Needs only `python-pptx` |
| `scripts/test_build_pptx.py` | Tests for the builder (bullets, cap, trade-off lines, font matching, big-number layout, `--strict`) |
| `scripts/render-check.sh` | HTML or .pptx to one PNG per slide (headless Chrome or LibreOffice, then `pdftoppm`) |

## Step 0: Resolve the design system
If the design plugin is installed, run `design-system-resolution`. Otherwise: use the system the user names; else the project's own (a tokens or theme file, a design-system page, a brand skill); else the neutral default theme in this skill's template. Say in one line which one you used, and ask only when two or more are found.

Apply it by replacing only the template's `:root` block. Map the system onto the same
names (`--color-bg`, `--color-text`, `--color-accent`, `--color-accent-strong`,
`--color-on-accent`, `--font-display`, `--font-body` and the rest). Use hex values so the
pptx builder can read them. One palette and type block per client or product; swapping
brands means swapping that block, nothing else.

## Exec style rules (apply to every slide)

1. Bottom line up front: slide 2 states the answer or the ask, not the agenda.
2. One idea per slide; the title is that idea as a full sentence, not a topic label.
3. Big numbers and visuals over prose. No paragraphs.
4. At most 3 bullets per slide, counting every card on it, one line each. One stated
   exception: an options slide with up to 3 options gives each option one "for" and
   one "against" line (6 at most), because a decision without its costs is not a
   decision. With 4 options, one line each. The builder drops extras and warns, so fix
   the HTML instead of relying on it.
5. Every number names its source in the slide footer (`data-field="source"`).
6. The last slide is the decision: what you need, by when, and what happens either way.
7. Accent color is rationed: one highlight per slide (the pick, the key number, the ask).

## Layouts

| `data-layout` | Use for | Fields |
|---|---|---|
| `title` | Cover | kicker, title, subtitle, meta |
| `bottom-line` | The answer in one sentence plus proof | kicker, title, point x3, source |
| `big-number` | One metric that carries the argument | kicker, title, number, label, context, source |
| `comparison` | 2 to 4 options side by side (columns size themselves) | title; each `data-group`: head, `for` + `against` (or one point); `data-pick` on the winner |
| `timeline` | Plan or milestones (3 to 5 steps) | title; each `data-group`: when, what; `data-pick` on the key step |
| `decision` | The ask | title, ask, point x2, source |

Add `<aside class="notes" data-field="notes">` for speaker notes; they become pptx notes.

## Procedure

1. **Outline first.** List slides as one sentence each, in order. Check the story reads
   from titles alone. Pick a layout per slide.
2. **Theme.** Do Step 0, then copy the template next to the deck's working folder and set
   the `:root` block.
3. **Build the slides.** For 6 or more slides, give each subagent one slide (or a small
   group): the outline, the theme block, the layout, its facts and sources, and the
   authoring contract. Each returns only its `<section>` markup. A mid-tier model class is
   enough for a slide; the main session assembles them.
4. **Verify the whole set together** in the main session: titles tell the story, one
   accent per slide, consistent kicker wording, numbering, and sources on every number.
5. **Render and look.** `bash scripts/render-check.sh deck.html check/html`, then open
   every PNG. Fix overflow, cut-off text (an ellipsis means a bullet is too long),
   crowding and contrast before converting.
6. **Convert.** `python3 scripts/build_pptx.py deck.html -o versions/<name>-v1.pptx --strict`.
   `--strict` fails on any layout warning (bullet cap, a line that will wrap, a missing
   font), so shorten the text in the HTML and rebuild until it passes. The builder uses
   the first installed face in each CSS font stack, matched by exact family name from
   the font file (so "Arial" never picks up "Arial Hebrew"); if it warns the font is
   missing, pass `--font "<installed font>"`, because a substituted face changes every width.
7. **Render the pptx and look again.** `bash scripts/render-check.sh versions/<name>-v1.pptx check/pptx`.
   Compare against the HTML renders slide by slide.
8. **The render check is a gate, not a report.** Any defect you can see in a PNG
   (overlap, a wrapped bullet or head, text running off a box, a label touching its
   number) gets fixed and re-rendered before the deck is done. Do not ship it under
   "known differences"; the reader sees the slide, not your notes.
9. **Version.** Keep every exported file in a `versions/` folder next to the deck, named
   `<name>-v<N>.pptx` (and `.pdf` if shared), and copy the latest one next to the HTML as
   `<name>.pptx` so anyone opening the folder finds it. Never overwrite a version
   someone has seen.

## Setup notes

- `python-pptx`: run with `uv run --with python-pptx python scripts/build_pptx.py ...`, or
  install in a throwaway virtual environment and remove it after. Tests:
  `uv run --with python-pptx --with pytest pytest -q -p no:cacheprovider scripts/test_build_pptx.py`.
- Render tools: Chrome or Chromium for HTML (set `CHROME` if not found), LibreOffice
  (`soffice`) for .pptx, and `pdftoppm` from poppler for both.
- The pptx is a faithful layout match, not a pixel copy: text boxes, shapes and fills are
  native and editable. Charts or images in the HTML need to be added as images or native
  charts by hand; the builder covers the six text layouts.

## Done means

- Every slide rendered to PNG and looked at, in both HTML and pptx form, with no
  visible defect left open.
- `build_pptx.py --strict` passes.
- No slide breaks a style rule above; every number has a source.
- The .pptx opens and edits cleanly (lists are real PowerPoint bullets); the file sits in
  `versions/` with a version number and a latest copy beside the HTML.
- One line to the user: which design system was used, slide count, and the file path.
