---
title: Environment inventory
audience: internal
sources:
  - {{deploy config path, for example deploy/ or a chart folder}}
  - {{CI config path}}
  - {{example env file, for example .env.example}}
last-verified: {{YYYY-MM-DD @ short commit}}
owner: update-help-docs
---

# Environment inventory

The one place hosts, endpoints and resource names live. Every other doc points here
instead of repeating them. Secret values never appear in this file; only where to find
them.

## Environments

| Name | Purpose | App URL | API base | Deployed by |
|---|---|---|---|---|
| local | developer machines | `http://localhost:{{port}}` | `http://localhost:{{port}}/api` | `{{command}}` |
| staging | pre-release checks | `{{url}}` | `{{url}}` | `{{pipeline or job}}` |
| production | users | `{{url}}` | `{{url}}` | `{{pipeline or job}}` |

## Hosts and services

| Environment | Service | Host or cluster | Port | Source of truth |
|---|---|---|---|---|
| staging | {{service}} | {{host}} | {{port}} | `{{file path}}` |

## Data stores

| Environment | Kind | Name (database, bucket, queue) | Source of truth |
|---|---|---|---|
| staging | {{postgres, object store, queue}} | {{name}} | `{{file path}}` |

## Secret references

One row per secret. The name in code or config (the env var, the secret manager key) is
the row; every other name for the same secret goes in `Aliases`. A legacy doc that says
"the DB password is in the vault" next to a `DATABASE_URL` secret adds an alias to that
row, marked `(from legacy doc docs/x.md, unverified)`, not a new row. Add a row only when
code or config shows a distinct secret. Unsure whether two names are one secret: keep one
row, alias the other, and ask in the report.

| Environment | Secret name | Aliases | Stored in | Used by | Rotated by |
|---|---|---|---|---|---|
| production | {{SECRET_NAME}} | {{other names, or none}} | {{secret manager and path, or CI secret name}} | {{service}} | `internal-docs/runbooks/{{runbook}}.md` |

Never a value, a partial value, or a hint at one.
