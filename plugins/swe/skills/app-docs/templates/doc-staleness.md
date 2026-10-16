---
title: Doc staleness table
audience: internal
sources:
  - docs/**
last-verified: {{YYYY-MM-DD @ short commit}}
owner: update-help-docs
---

# Doc staleness table

After a change, match the changed paths against the globs below and re-check the listed
docs. Doc paths are relative to `docs/`; globs are relative to the repo root.

| Path glob | Docs to check | Why |
|---|---|---|
| `{{src/feature/**}}` | `{{external-docs/help/feature.md}}` | {{what the doc describes}} |
| `{{deploy/**}}` | `internal-docs/environments.md` | hosts, ports, resource names |
