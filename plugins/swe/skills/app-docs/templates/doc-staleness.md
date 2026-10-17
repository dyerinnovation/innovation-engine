---
title: Doc staleness table
audience: internal
sources: []   # this table is kept current by the writer adding a row with each new doc
last-verified: {{YYYY-MM-DD @ short commit}}
owner: update-help-docs
---

# Doc staleness table

After a change, match the changed paths against the globs below and re-check the listed
docs. Doc paths are relative to `docs/`; globs are relative to the repo root.

| Path glob | Docs to check | Why |
|---|---|---|
| `{{src/feature/**}}` | `{{external-docs/help/feature.md}}`, `{{the Unreleased place: changelog file, or release-notes-unreleased.md}}` | {{what the doc describes}}; user-visible change |
| `{{src/routes/**}}` | `{{external-docs/api/**}}`, `{{the Unreleased place}}` | endpoint reference; user-visible change |
| `{{deploy/**}}` | `internal-docs/environments.md` | hosts, ports, resource names |

Globs point at code and config, never at `docs/**`: a row that fires on every doc edit
is noise, and people learn to ignore the check.
