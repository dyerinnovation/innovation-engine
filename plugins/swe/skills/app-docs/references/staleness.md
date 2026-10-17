# The staleness table

`docs/internal-docs/doc-staleness.md` answers one question after every change: which docs
might now be wrong? It is a plain markdown table so people and agents can read it, and
simple enough for a script to parse.

## Format

| Path glob | Docs to check | Why |
|---|---|---|
| `src/auth/**` | `external-docs/help/sign-in.md`, `internal-docs/runbooks/auth-keys.md`, `external-docs/release-notes/CHANGELOG.md` | sign-in flow and key rotation; user-visible change |
| `src/routes/**`, `api/openapi.yaml` | `external-docs/api/**`, `external-docs/release-notes/CHANGELOG.md` | endpoint reference; user-visible change |
| `deploy/**`, `.ci.yml` | `internal-docs/environments.md`, `internal-docs/runbooks/deploy.md` | hosts and deploy steps |
| `db/migrations/**` | `internal-docs/environments.md`, `external-docs/release-notes/CHANGELOG.md` | schema and user-visible changes |

Rules:

- Doc paths are relative to `docs/`. Globs are relative to the repo root.
- Every doc's `sources` frontmatter must be covered by at least one row. The setup step
  builds the first version straight from the `sources` lists.
- A row with no matching files is itself stale; the check reports it.
- Any glob for code users can see (routes, UI, public config, migrations that change
  behavior) also lists the release notes, where its `Unreleased` entry belongs. The
  release notes path is whatever the repo already uses: the changelog file, or for
  one-file-per-version repos the single `release-notes-unreleased.md` (or the sibling
  name pattern the repo uses), never a glob over every version file.
- Globs point at code and config, never at `docs/**`. The table itself has no `sources`
  row: it changes when a doc is added, and the writer adds that row in the same step.
  A row that fires on every doc edit trains people to ignore the check.
- A legacy doc is never a glob here; once its facts are verified, the row points at the
  code or config that proved them.

## Running it after a change

1. Get the changed files: `git diff --name-only <base>...HEAD`.
2. Match each against the globs; collect the docs to check.
3. For each doc, `update-help-docs` re-reads its sources and either updates the doc or
   confirms it is still true and bumps `last-verified`.
4. Report: docs updated, docs confirmed, docs that need a human (missing source, unclear
   behavior).

## Reading `last-verified`

Parse it with the pattern in `references/layout.md` and act on the result:

| Value | Check result |
|---|---|
| does not match the pattern | error: bad `last-verified`, name the doc (never skip it silently) |
| empty | unverified: list it for a first verification |
| `<date> @ <sha>+dirty` | unverified: verified against uncommitted work, re-check after commit |
| `<date> @ <sha>`, sha unknown to git (rebased away) | stale: re-check |
| `<date> @ <sha>` | stale if `git diff --name-only <sha> HEAD -- <sources>` lists anything, else current |

The diff against the recorded sha catches drift even when nobody ran the check on the
change that caused it.

## Running it in CI

A small script (in the project's own language) does steps 1 and 2 and fails or warns when
a changed path maps to a doc that the same change did not touch. Start in warn mode; switch
to fail once the table is trusted. The script never edits docs; it only lists them.

Also check in CI:

- every doc has `audience`, `sources` and a `last-verified` that matches the pattern
- every `sources` path still exists
- no file under `external-docs/` links into `internal-docs/` or names an internal host from
  `environments.md`
