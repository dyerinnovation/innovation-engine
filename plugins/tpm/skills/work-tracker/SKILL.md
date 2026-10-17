---
name: work-tracker
description: Work a team's ticket system from Claude Code (Linear, Jira, Azure DevOps Boards, GitHub Issues). Onboard once (install, least-scope token kept outside the repo, defaults), read the project's process (states, item types, conventions) before writing anything, then run the common recipes. Picks one per-platform reference with the right interface, exact commands and known traps. Triggers on "what am I assigned", "what's on my plate", "show me the ticket", "open the issue", "create a ticket", "file a bug", "comment on the ticket", "move the ticket", "move it to In Review", "close the issue", "update the work item", "link the PR to the ticket", "search the backlog", "find the ticket for", or "/work-tracker".
---

# Work tracker

One method for any ticket system. The method lives here; the exact commands for each
platform live in `references/`. Read only the reference for the platform in front of you.

## 1. Pick the platform

Decide from the project, in this order, and stop at the first hit:

1. The user named it ("our Jira", "the board in Azure DevOps").
2. The project says so: a "Work tracker" line in `CLAUDE.md` or the README, a tracker URL
   in the docs or the pull request template, or ticket keys in recent commit messages and
   branch names (`<KEY>-<n>` points at Linear or Jira, `AB#123` at Azure DevOps, `#123` at
   GitHub).
3. The git remote: `git remote get-url origin`. `dev.azure.com` or `visualstudio.com`
   means Azure DevOps; `github.com` means GitHub Issues unless step 2 said otherwise.
4. Ask, in one line.

| Platform | Reference |
|---|---|
| Linear | `references/linear.md` |
| Jira Cloud | `references/jira.md` |
| Azure DevOps Boards | `references/azure-devops.md` |
| GitHub Issues and Projects | `references/github-issues.md` |

## 2. Pick the interface

Use the best one that works, in this order:

1. **MCP connector**, when one is installed and answers. Before you call it broken, call
   one cheap read tool (list teams, list projects, who am I). An "authentication required"
   notice alone is not proof; a failed call is.
2. **Official CLI**, when the connector is missing or lacks the operation.
3. **REST or GraphQL API**, for anything the first two cannot do. The references name these
   gaps up front so you do not discover them by trial.

Mixing is fine: read the process over the API, then do daily work through the connector.

## 3. Onboard once per machine

- Install the connector or CLI from the reference.
- Prefer browser sign-in (OAuth). When a token is needed, create it with the least scope
  the recipes need (read and write work items, nothing else) and the shortest expiry the
  user accepts.
- Store the token outside the repo: the OS keychain, the CLI's own credential store, or an
  environment variable set in the shell profile. Never in a tracked file, never in an MCP
  config that is committed.
- Set defaults (organization, project, team) so commands stay short. Record the non-secret
  defaults in the project's `CLAUDE.md` under a "Work tracker" heading.

## 4. Read the process before writing

Before the first create, move or close in a project, read and note:

- **States** per item type, in order, and which ones count as done.
- **Item types** in use (Bug, Story, Task, Epic, Feature) and which fields each requires.
- **Transitions**: some platforms only allow certain moves from a given state.
- **Conventions**: labels, title style, templates, how a pull request links to an item,
  who may close.

Write a short summary under the "Work tracker" heading in `CLAUDE.md` so the next session
skips this step. Never guess a state name; read it.

## 5. Recipes

Each reference maps these to exact commands.

| Recipe | What it does |
|---|---|
| What am I assigned | Open items assigned to me, newest activity first |
| Show an item | Title, state, assignee, description, recent comments, links |
| Create | Title, type, description, labels; assign only if asked |
| Comment | Add a comment; keep it short and factual |
| Move state | Read the allowed states or transitions, then move |
| Link a pull request | Prefer the platform's native link (keyword in the PR, branch name); fall back to an explicit link |
| Search | By text, label, state or assignee in the platform's query language |

When you write commands or a plan:

- **Derive, do not placeholder.** Capture runtime values (item type, ids, UUIDs, state
  names) into shell variables from a read call, and URL-encode any that go into a URL path;
  type names like "User Story" contain spaces. Only the org, project, token and the values
  the user gave should be filled by hand.
- **Stop on an empty derived value.** A failed token, a typo or a missing item makes a
  read return nothing, and the next command then runs with a hole in it (a WIQL
  `NOT IN ()`, a URL with no type, a mutation with no issue id) and fails far from the
  cause or does the wrong thing. After each derived value, check it is non-empty; if it
  is empty, stop and report which value and which call, instead of passing it on. The
  references define a `need` helper for this.
- **Take the simplest path that does the whole job.** If the CLI can move and comment in
  one call, use it; keep the API for what the CLI cannot do (reading the process, states,
  transitions).
- **Verify a write by the id it returned**, or by exact text with an explicit sort order,
  never by assuming the newest entry is first.

Write actions (create, comment, move, link, close) change shared state that other people
watch. Confirm the target item and the exact change with the user before the first write in
a session, unless they already asked for that exact change.

## Token rules

- Never commit a token, and never write one into a file inside the repo.
- Never echo a token or print it to the transcript. Pass it by environment variable or
  standard input, not as a command argument.
- Redact tokens in any output you paste or save: replace the value with `<redacted>`.
- If a token was exposed, tell the user and ask them to revoke and reissue it.

## Copy rules

Plain words, no italics, no em dashes, no emoji. Ticket text follows the project's own
conventions from step 4.
