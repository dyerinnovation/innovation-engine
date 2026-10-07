---
name: sprint-board
description: Create and keep current a live, database-backed Agile board page (columns, workstream chips, card detail, step-by-step How To Test, headline, log, and Tested or Found a Problem buttons) themed from your project's design system. Use when asked for a "sprint board", "status board", "Jira-style board", "Agile board", "progress board", or to "keep the board updated", "move the card" or "update the board" during multi-agent work.
---

# Sprint board

A private Claude artifact that shows lane progress as an Agile board. The page is static
HTML; all content lives in the artifact's shared database, so Claude moves cards with
database writes (the `ArtifactData` tool) and never republishes the page to change content.

Template: `references/sprint-board-template.html`. It ships with a neutral palette and a
plain text wordmark. Edit only the THEME TOKENS `:root` block and the `BOARD` config object
at the top of the script.

## When to use

- A person wants to watch parallel lanes (builders, reviewers, merges, deploys, test walks)
  without reading the chat, especially for work that runs overnight.
- Any multi-lane round that runs longer than one sitting.
- Not for one-off reports (write a review doc) or for bug scratchpads (use the project's
  issues file).

## Data schema (add fields only; never rename or remove)

Collection `cards`, one document per work item (doc id = a short slug such as `auth-l2`):

| Field | Type | Notes |
|---|---|---|
| `title` | string | Short and plain: what the card is |
| `stream` | string | A key from `BOARD.streams` (default: frontend, backend, docs, infra, other) |
| `col` | string | backlog, building, review, merging, testing, done, you |
| `ref` | string | Issue, branch, SHA or doc name |
| `detail` | string | Plain sentences; `\n` for new lines; https links become clickable |
| `order` | number | Sort order within a column (low first) |
| `updated` | ISO string | Set on every change |
| `steps` | array | Optional `[{text, expect}]`: one plain action and what you should see. Shown as a collapsed, numbered How To Test section |
| `owner_note` | string | Written by the page's buttons: "tested ok" (also moves the card to done) or "found a problem (tell Claude what)" |

Doc `meta/status`: `headline` (one line; the page labels it Now, so do not prefix "Now:"),
`updated` ISO, `log` array of `{t, msg}` (keep about 40; the page shows newest first), and
optional `title` and `subtitle` that override the config.

Optional doc `meta/test_accounts`: `{title?, accounts:[{label, email, password?, url?}]}`.
Renders a Dev Only, Test Accounts block with copy buttons. Use it only for non-production
test logins the project deliberately shares, only when the person asked for it, and never
for real passwords, API keys or tokens. A board with this doc stays private. Leave the doc
out otherwise.

## Page behavior (already in the template)

- Seven columns on desktop, four at 1200 px, one column with column tabs under 720 px; no
  horizontal page scroll.
- Stream filter chips with counts; a done and ready-to-test progress bar.
- Headline, test accounts and log are collapsed by default with a one-line summary; each
  viewer's choice is remembered in localStorage (wrapped in try/catch).
- Tap a card title for detail; in the testing column, the Tested, Works and Found a Problem
  buttons appear. Cards with `steps` show a step badge and a How To Test toggle.
- Light and dark themes from one token block; `[hidden]` is forced to `display:none`.

## Create a new board

1. Copy the template to a scratch folder. Theme it (below) and set `BOARD`: key, wordmark,
   name, title, subtitle, columns and streams. Add one `--stream-<key>` token and one
   `.sdot.<key>` rule per stream.
2. Publish it as an artifact with an icon such as `board`, a one-sentence description and
   the database capability (`{"db":{}}`).
3. Seed it with one batch write (up to 50 writes): every card, then `meta/status`.
4. Check it once in a browser at 1440 px and 390 px, light and dark: data loads and a How
   To Test section expands.
5. Record the board URL and the schema in the project's notes or CLAUDE.md.

## Keep it current (every lane state change)

- Read before writing: list `cards` (or get one) and pin each write to the version you read.
  On a version conflict, re-read and redo; never overwrite the person's button writes.
- Move a card: update `{col, detail, updated}` (and `order` if needed). The detail says what
  changed and what the person checks next.
- Every move also appends one `log` line `{t:"HH:MM", msg}` and refreshes `headline` and
  `updated` on `meta/status`, in the same batch.
- A card entering `testing` must carry `steps`. Rules: exact URLs on the real environment,
  button and tab names exactly as the app shows them, one action per step, an `expect` for
  every step, never a password (say "sign in with your test account"), Title Case for UI
  names.
- Check `owner_note` fields at each check-in: "tested ok" means the card is done; a problem
  flag means ask what they saw, then open a fix lane and move the card back to building.
- Things only a person can do go in `you`, with the exact URL and click path in `detail`.
- Batch writes (at most 50 per call). Keep the total under a few hundred docs; prune old
  done cards when a sprint closes.

## Theme it from your design system

1. Read your design tokens: a design-system page, a `tokens.css` or `tokens.json`, or the
   codebase theme file. The `design:brand-design-system` skill can produce one.
2. Map them into the THEME TOKENS block only: neutrals (ground, raised, sunken, line,
   control, ink, body, muted, faint) for light (`--l-*`) and dark (`--d-*`); brand, brand
   fill for white text, pressed; warning and danger text and tints; one dot color per
   stream; fonts; radii; shadow. The mapping blocks after it never change.
3. Replace the text wordmark with your project's name. To use a logo, copy your own mark
   into the lockup; never redraw someone else's.
4. Check text contrast (4.5:1) in both themes, and that chip text stays neutral on tints.

## Rules

- Link everything: issues, docs, artifacts and environment URLs, as full https links in
  `detail` or `steps`.
- No secrets in cards, steps, headline or log. The only exception is the opt-in test
  accounts doc above.
- Never republish the page to change content; republish only for page changes, and read
  the live artifact first.
- Keep the board private.
