# Layout, frontmatter and setup commands

## The tree

```
docs/
  README.md                  # one screen: the who-reads-it rule and where things go
  internal-docs/             # team and agents
    environments.md          # the one environment inventory
    doc-staleness.md         # path glob -> docs to re-check
    runbooks/                # how to deploy, restore, rotate, recover
    decisions/               # dated decision records
    architecture/            # diagrams and system notes
    post-mortems/            # session and incident records
    logs/ messages/ meeting-notes/ feedback/ emails/ errors/   # feedback-triage evidence
  external-docs/             # people who use the app
    help/                    # task pages: how do I ...
    guides/                  # longer walkthroughs
    release-notes/           # one file per release
    api/                     # endpoint and SDK reference
```

Evidence folders are created on first use by feedback-triage; do not pre-create empty ones.

## Which side

Ask one question: who reads it?

- A user, a customer admin, or an outside developer calling the API: external.
- Anyone who runs, builds or supports the app, human or agent: internal.
- Both: split it. Example: "reset your password" is external; "what the reset job does
  and how to replay it" is an internal runbook.

## Per-doc frontmatter

Every doc on both sides starts with:

```yaml
---
title: Reset your password
audience: external        # external | internal
sources:                  # files this doc is true about; the writer reads all of them
  - src/auth/reset.ts
  - src/auth/routes.ts
  - config/email-templates/reset.html
environments: [production] # optional; names rows in internal-docs/environments.md
last-verified: 2026-01-15 @ a1b2c3d   # date and short commit of the sources read
owner: update-help-docs   # the skill that maintains it
---
```

Rules:

- `sources` lists files or globs in the repo, never URLs to a wiki.
- A doc with no `sources` is a draft and says so in its title line.
- `last-verified` changes only when the writer re-read every source at that commit.

## Setup command sequence

Run from the repo root. Each step is safe to re-run; nothing is overwritten.

```bash
# 1. Folders
mkdir -p docs/internal-docs/{runbooks,decisions,architecture,post-mortems}
mkdir -p docs/external-docs/{help,guides,release-notes,api}

# 2. Seed files from the skill templates (skip any that already exist)
SKILL="${CLAUDE_PLUGIN_ROOT}/skills/app-docs"
cp -n "$SKILL/templates/environments.md"   docs/internal-docs/environments.md
cp -n "$SKILL/templates/doc-staleness.md"  docs/internal-docs/doc-staleness.md
mkdir -p .claude/skills/update-help-docs
cp -n "$SKILL/templates/update-help-docs.SKILL.md" .claude/skills/update-help-docs/SKILL.md

# 3. docs/README.md: write the one-screen who-reads-it rule (by hand or by the skill)

# 4. CLAUDE.md: append templates/claude-md-snippet.md after showing the diff

# 5. Confirm the tree
find docs -maxdepth 2 -type d | sort
```

Then fill the placeholders in the copied files by reading the code, not from memory.
