---
name: update-help-docs
description: Write and update {{project}} docs from the code, on both sides of the tree. Use for "update the docs", "help docs", "write a help page", "release notes", "write a runbook", "API docs", "the docs are stale", "document this feature", or after any change that the staleness table maps to a doc.
---

# Update help docs ({{project}})

Generated from the app-docs skill. Fill every `{{placeholder}}`, then delete this line.

## The tree

| Side | Path | Reader | Doc sets |
|---|---|---|---|
| internal | `docs/internal-docs/` | team and agents | runbooks, decisions, architecture, post-mortems, environments |
| external | `docs/external-docs/` | users | help, guides, release notes, API |

Project facts:

- Code roots: `{{src/}}`, `{{api/}}`
- API schema: `{{path to OpenAPI or schema file, or none}}`
- Release notes cover: `{{what counts as user-visible}}`
- External tone: {{plain, second person, task first}}; internal tone: {{terse, commands first}}

## Steps

1. Work out which docs are in scope: the ones named in the request, plus any the staleness
   table (`docs/internal-docs/doc-staleness.md`) maps the changed paths to.
2. For each doc, read its frontmatter `sources` and read every one of those files. For a new
   doc, find the sources first and write them into the frontmatter.
3. Read `docs/internal-docs/environments.md` for any host, endpoint or resource name. Never
   copy a value into an external doc unless it is a public URL listed there as public.
4. Write or update the doc. Each fact must trace to a source just read. If a fact is
   missing, write `TODO(source needed): <what>` instead of guessing. Examples are facts
   too: headers, content types, status codes and sample values come from the code, a
   schema or a test fixture, or become a placeholder plus a TODO. Old prose docs are
   leads only: verify them in code or config, or mark the fact
   `(from legacy doc <path>, unverified)` and report it.
5. Set `last-verified` to exactly `YYYY-MM-DD @ <short-sha>` (today, `git rev-parse
   --short HEAD`), only for docs whose sources were all re-read. If any source has
   uncommitted changes, write `@ <short-sha>+dirty`. No other text in that field; put
   notes in the report.
6. If a new doc or source was added, add or update its row in the staleness table.
7. Report: docs written, docs confirmed unchanged, TODOs left, and any doc whose sources no
   longer exist.

## Release notes

- Convention: `{{changelog file, or one file per release in a folder}}`. Keep it.
- Unreleased changes go in: `{{one changelog: the "## Unreleased" heading at the top of
  that file; one file per version: the single file named like its siblings with
  "unreleased" for the version, for example release-notes-unreleased.md}}`. Append to it;
  never start a second Unreleased place.
- At release: `{{rename the heading to the version | rename the file and its title to the
  version}}`. Never guess a version number.
- Source: merged changes since the last release tag, read from the commits and the code,
  not from ticket titles alone.
- Only user-visible changes. Group by: New, Improved, Fixed. Internal-only changes go in an
  internal decision or runbook if they matter, not in the release note.

## Hard rules

- No source, no sentence.
- Never write a secret value, token, password or real customer data.
- External docs never link into `docs/internal-docs/` and never name internal hosts.
- Never delete a doc; propose removals to the owner.
- Never bump `last-verified` without re-reading the sources.
