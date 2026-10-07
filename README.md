# Innovation Engine

The Claude Code skills we build with every day, open source. Three plugins in one
marketplace: one for software engineering, one for running the work, one for design.

More guides and walkthroughs: https://innovation.dyer-capital.com/skills/

## Install

In Claude Code:

```
/plugin marketplace add dyerinnovation/innovation-engine
/plugin install swe@innovationengine
/plugin install tpm@innovationengine
/plugin install design@innovationengine
```

Install only the plugins you want. Skills are namespaced by plugin, so they show up as
`/swe:agent-model-routing`, `/tpm:sprint-board` and so on, and Claude also picks them up
from their descriptions when the moment fits.

## swe: software engineer

| Skill | What it does |
|---|---|
| `agent-model-routing` | Picks a model class (strongest, mid-tier, small) for every agent you spawn, by role and brief shape. |
| `builder-reviewer-loop` | Runs a change as a builder plus an independent reviewer, with its own screenshots for UI work. |
| `worktree-rectify` | Finds uncommitted, unpushed, stashed or orphaned work across your repos and recovers it. |
| `session-post-mortem` | Before a compaction, lists the session's churn and proposes instruction fixes, approved one by one. |

The `swe` plugin also ships a `UserPromptSubmit` hook that reminds Claude to run
`session-post-mortem` when you announce a compaction ("then I'll compact"). It only adds
context; it never blocks a prompt.

## tpm: technical project manager

| Skill | What it does |
|---|---|
| `sprint-board` | Builds and keeps current a live Agile board page backed by a shared database. |
| `feedback-triage` | Files every paste (logs, messages, notes, feedback) verbatim into a typed, dated folder, via a background agent. |
| `human-actions` | Keeps one tracked list of the steps only a person can do, with evidence on completion. |

The `tpm` plugin also ships the `feedback-triage` filer agent.

## design

| Skill | What it does |
|---|---|
| `brand-design-system` | Turns any brand into self-contained tokens, a brand guide with anti-patterns, and a specimen page. |

## Requirements

- Claude Code with plugin support.
- The session-post-mortem hook needs `bash`; `jq` is used when present, with a fallback
  when it is not.
- `sprint-board` publishes a Claude artifact with a shared database, so it needs a
  Claude account with artifacts available.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. Copyright (c) 2026 Dyer Innovation Station L.L.C.
