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
| `mcp-tool-design` | Designs MCP tools agents pick correctly: names, descriptions, honest annotations, scopes and safety. |
| `test-strategy` | Picks the test layers for a change, including evals for model output, and what must pass before merge. |
| `ui-test-walk` | Walks a UI change step by step at phone and desktop width, with screenshots and a severity-rated report. |
| `app-docs` | Sets up self-maintaining docs: internal-docs for the team, external-docs for users, every fact tied to its source, with a staleness table. |

The `swe` plugin also ships a `UserPromptSubmit` hook that reminds Claude to run
`session-post-mortem` when you announce a compaction ("then I'll compact"). It only adds
context; it never blocks a prompt.

## tpm: technical project manager

| Skill | What it does |
|---|---|
| `sprint-board` | Builds and keeps current a live Agile board page backed by a shared database. |
| `feedback-triage` | Files every paste (logs, messages, notes, feedback) verbatim into a typed, dated folder, via a background agent. |
| `human-actions` | Keeps one tracked list of the steps only a person can do, with evidence on completion. |
| `prd-writing` | Writes requirements docs grounded in the code, with decisions in place and tagged acceptance criteria, plus a linter. |
| `release-ladder` | Runs one tracker project per release with gate reviews, in GitHub, Linear or Jira. |
| `architecture-diagrams` | Keeps current and target architecture diagrams side by side, readable and exported. |
| `work-tracker` | Works your ticket system from Claude Code (GitHub Issues, Jira, Azure DevOps and more), with one best-practice file per platform. |
| `working-notes-page` | Turns a live chat or meeting transcript into an HTML notes page: decisions, actions with owners, open questions, each linked to its source. |

The `tpm` plugin also ships the `feedback-triage` filer agent.

## design

| Skill | What it does |
|---|---|
| `brand-design-system` | Turns any brand into self-contained tokens, a brand guide with anti-patterns, and a specimen page. |
| `design-system-resolution` | Step 0 of every visual skill: picks the design system to use (yours, the project's, or the engine default) and says which. |
| `exec-deck` | Builds executive slides as HTML first, then converts them to editable PowerPoint, checked slide by slide as images. |
| `chat-progress-feedback` | Design rules for chat and agent interfaces that never leave people staring at silence: visible steps, heartbeats, cancel. |
| `shared-ai-canvas` | Point at the exact text you mean, ask the AI, and get a tracked suggestion on just that part, never a silent rewrite. |

## Requirements

- Claude Code with plugin support.
- The session-post-mortem hook needs `bash`; `jq` is used when present, with a fallback
  when it is not.
- `sprint-board` publishes a Claude artifact with a shared database, so it needs a
  Claude account with artifacts available. The database-backed page option of
  `human-actions` needs Claude artifacts too.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Contact

Questions and security reports: opensource-innovation@dyer-capital.com. For bugs and ideas, open a GitHub issue.

## License

MIT. Copyright (c) 2026 Dyer Innovation Station L.L.C.
