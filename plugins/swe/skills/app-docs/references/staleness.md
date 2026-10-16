# The staleness table

`docs/internal-docs/doc-staleness.md` answers one question after every change: which docs
might now be wrong? It is a plain markdown table so people and agents can read it, and
simple enough for a script to parse.

## Format

| Path glob | Docs to check | Why |
|---|---|---|
| `src/auth/**` | `external-docs/help/sign-in.md`, `internal-docs/runbooks/auth-keys.md` | sign-in flow and key rotation |
| `api/openapi.yaml` | `external-docs/api/**` | endpoint reference |
| `deploy/**`, `.ci.yml` | `internal-docs/environments.md`, `internal-docs/runbooks/deploy.md` | hosts and deploy steps |
| `db/migrations/**` | `internal-docs/environments.md`, `external-docs/release-notes/next.md` | schema and user-visible changes |

Rules:

- Doc paths are relative to `docs/`. Globs are relative to the repo root.
- Every doc's `sources` frontmatter must be covered by at least one row. The setup step
  builds the first version straight from the `sources` lists.
- A row with no matching files is itself stale; the check reports it.

## Running it after a change

1. Get the changed files: `git diff --name-only <base>...HEAD`.
2. Match each against the globs; collect the docs to check.
3. For each doc, `update-help-docs` re-reads its sources and either updates the doc or
   confirms it is still true and bumps `last-verified`.
4. Report: docs updated, docs confirmed, docs that need a human (missing source, unclear
   behavior).

## Running it in CI

A small script (in the project's own language) does steps 1 and 2 and fails or warns when
a changed path maps to a doc that the same change did not touch. Start in warn mode; switch
to fail once the table is trusted. The script never edits docs; it only lists them.

Also check in CI:

- every doc has `audience`, `sources` and `last-verified`
- every `sources` path still exists
- no file under `external-docs/` links into `internal-docs/` or names an internal host from
  `environments.md`
