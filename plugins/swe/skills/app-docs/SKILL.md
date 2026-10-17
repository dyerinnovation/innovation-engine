---
name: app-docs
description: Self-maintaining app docs. Sets up docs/internal-docs/ (team and agents) and docs/external-docs/ (users), makes every doc name its source-of-truth files, keeps one environment inventory, generates a per-project update-help-docs skill, installs a CLAUDE.md rule that routes doc work through the skills, and keeps a staleness table that maps code changes to the docs they break. Use when asked to "set up docs", "update the docs", "help docs", "the docs are stale", "docs are out of date", "write release notes", "write a runbook", "document the environments", "API docs", "user guide", or to clean up a messy docs/ folder.
---

# App docs

Docs drift because people write them from memory and nobody knows which code change made
them wrong. This skill fixes both: every doc names the files it is true about, a skill
(not a person) writes it from those files, and a table says which changes make which docs
stale.

## The one rule: who reads it

| Reader | Side | Holds |
|---|---|---|
| The team and its agents | `docs/internal-docs/` | runbooks, decisions, evidence, post-mortems, environment inventory, architecture |
| The people who use the app | `docs/external-docs/` | help pages, guides, release notes, API docs |

If a doc has both readers, split it: the user part goes external, the operator part goes
internal, and the external one never links into internal. Full tree: `references/layout.md`.

## Four pieces that keep docs true

1. **Sources in every doc.** Frontmatter names `audience`, `sources` (code paths, config,
   schema) and `last-verified`, which is exactly `YYYY-MM-DD @ <short-sha>` (HEAD when the
   sources were read), or `@ <short-sha>+dirty` if any source had uncommitted changes.
   Nothing else goes in that field, so a script can parse it; notes go in the report.
   Format and check: `references/layout.md`. The writer reads every source before
   writing and refuses to state a fact it cannot point to. Missing fact: write
   `TODO(source needed): <what>` and list it in the report. Never guess.
   Examples count as facts: a header, a content type, a status code or a sample value
   in a request tells the reader the code accepts it. Take each one from the code, a
   schema or a test fixture; otherwise use a placeholder such as `<amount>` plus a TODO.
   Legacy prose docs are leads, not sources: confirm what they say in code or config.
   If you cannot, keep the fact marked `(from legacy doc docs/x.md, unverified)` and
   list it in the report; never put a legacy doc in `sources` as if it were proof.
2. **One environment inventory.** `docs/internal-docs/environments.md` holds hosts,
   endpoints, database names, queues, buckets and secret references (the name of the
   secret and where it lives, never the value). Every other doc reads from it instead of
   repeating a host. One row per secret: when a legacy doc names a secret that code or
   config already shows (for example "the DB password" next to a `DATABASE_URL` secret),
   add the legacy name to that row's `Aliases` cell, marked unverified, and ask in the
   report; a second row would count one secret twice and split its rotation story.
   Template: `templates/environments.md`.
3. **A staleness table.** `docs/internal-docs/doc-staleness.md` maps path globs to the docs
   to re-check. Run it after each change and in CI. See `references/staleness.md`.
4. **A routing rule plus a per-project skill.** A short CLAUDE.md snippet sends every doc
   task to `update-help-docs`, a skill generated for this project that knows both sides of
   the tree. Templates: `templates/claude-md-snippet.md`, `templates/update-help-docs.SKILL.md`.

## Set up a project

1. Check for an existing `docs/` folder. If it has content, follow
   `references/migration.md` first. Never delete or move a file without approval.
2. Create the tree and seed files with the command sequence in `references/layout.md`.
3. Fill `environments.md` by reading deploy config, compose or chart files, CI config and
   `.env.example`. Secret values never go in; only their reference.
4. Fill `doc-staleness.md` with one row per doc: the globs of its `sources`. Code that
   changes what users see (routes, UI, public config) also maps to the release notes.
5. Generate `.claude/skills/update-help-docs/SKILL.md` from the template: replace each
   `{{placeholder}}`, list the real doc sets, and keep the hard rules unchanged.
6. Append the CLAUDE.md snippet to the project's CLAUDE.md (show the diff, get approval).
7. Run the staleness check once by hand and report the result.

## Update docs

- **Tree exists**: hand the task to `update-help-docs` (or follow its steps if it was
  never generated).
- **Never set up** (no `docs/internal-docs/` or `docs/external-docs/`): do the minimum
  the request needs and stop. Write only the requested docs, on the right side of the
  new tree, with full frontmatter. Do not create the inventory, the staleness table,
  the per-project skill or the CLAUDE.md rule, and do not move legacy files. End the
  report with a setup proposal (the steps below plus the migration table). Half a setup
  done silently looks finished and is not, so leave it whole or untouched.
- **Release notes**: follow the convention already in the repo. Never guess a version
  number. Unreleased changes go here:

  | Convention | Where Unreleased goes | At release |
  |---|---|---|
  | one changelog file | an `## Unreleased` heading at the top of that file | rename the heading to the version |
  | one file per version (`release-notes-0.3.md`) | one file named like its siblings with `unreleased` for the version (`release-notes-unreleased.md`), in the same folder | rename the file (and its title) to the version |
  | none yet | `## Unreleased` at the top of `external-docs/release-notes/CHANGELOG.md` | rename the heading |

  There is only ever one Unreleased place, so the next writer appends instead of
  starting another file.

## Fits with other skills

- `tpm:feedback-triage` already defaults its evidence root to `docs/internal-docs/`; logs,
  messages, meeting notes and decisions land there with no change.
- `swe:session-post-mortem` currently writes its records to `docs/post-mortems/`. In a
  project that uses app-docs, point it at `docs/internal-docs/post-mortems/` (say so in the
  project's CLAUDE.md snippet; the snippet template already does).
- `tpm:prd-writing` PRDs and release plans are internal; their shipped result becomes an
  external release note written by `update-help-docs`.

## Hard rules

- Never invent a fact. No source, no sentence.
- Never write a secret value, token, password or real customer data into any doc.
- External docs never link into internal docs and never name internal hosts.
- Copy, never delete. Moves and removals are proposed in a table and wait for approval.
- Update `last-verified` only after re-reading every source, never as a bulk bump.
