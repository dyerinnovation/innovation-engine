## Docs

- Docs live in `docs/internal-docs/` (team and agents) and `docs/external-docs/` (users).
  Who reads it decides the side.
- Every doc task (new page, update, release notes, runbook, API docs, "the docs are
  stale") goes through the `update-help-docs` skill. Do not hand-write docs.
- Hosts, endpoints, database names and secret references live only in
  `docs/internal-docs/environments.md`. Secret values never go in any doc.
- After a code change, check `docs/internal-docs/doc-staleness.md` for docs the change
  may have made stale, and update them in the same change.
- Post-mortem records go in `docs/internal-docs/post-mortems/`; pasted evidence goes under
  `docs/internal-docs/` (feedback-triage).
