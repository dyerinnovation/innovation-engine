# GitHub Issues and Projects

## Interfaces, ranked

1. **`gh` CLI** (best for issues). Official, stable flags, JSON output, already signed in on
   most developer machines.
2. **GitHub MCP server**, official, remote at `https://api.githubcopilot.com/mcp/`. Worth
   it when `gh` is not installed or the session has no shell.
3. **REST and GraphQL API**, through `gh api` so auth is handled for you. Needed for issue
   types, sub-issues and some Projects fields.

## Auth with least scope

`gh` (preferred): `gh auth login` and choose the browser. It stores the token in the OS
credential store. Projects need one extra scope: `gh auth refresh -s project` (or
`-s read:project` for read only).

Token sign-in, when browser sign-in is not possible: set `GH_TOKEN` in the environment
(the route `gh` recommends for fine-grained tokens), or for a classic token
`gh auth login --with-token < <token-file-outside-repo>`. Prefer a fine-grained token
limited to the repos in question with Issues: Read and write, Pull requests: Read,
Metadata: Read. Fine-grained tokens cannot reach Projects owned by a user account; for
those, a classic token needs `project` (or `read:project`).

MCP:

```
claude mcp add-json github '{"type":"http","url":"https://api.githubcopilot.com/mcp/","headers":{"Authorization":"Bearer ${GITHUB_PAT}"}}'
```

The single quotes keep `${GITHUB_PAT}` literal in the config; Claude Code expands it from
the environment at connect time, so the token never lands in the file. Keep `GITHUB_PAT`
in the environment.

Limit the remote server to what the recipes need:

- Read-only: add `/readonly` to the URL (`https://api.githubcopilot.com/mcp/readonly`), or
  send the header `X-MCP-Readonly: true`.
- Toolsets: use a toolset URL such as `https://api.githubcopilot.com/mcp/x/issues` (and
  `/x/issues/readonly`), or send `X-MCP-Toolsets: issues,pull_requests,projects`.
- The local server takes `--toolsets issues,pull_requests` (env `GITHUB_TOOLSETS`) and
  `--read-only` (env `GITHUB_READ_ONLY=1`).

Cheap read to prove it works: `gh auth status`, or the MCP `get_me` tool.

## Read the process first

GitHub has only two states, open and closed (closed as completed, not planned or
duplicate). The real process usually lives in labels, issue templates, issue types and a
Project board.

```bash
gh label list --limit 100
ls .github/ISSUE_TEMPLATE/ 2>/dev/null
gh project list --owner <owner>
gh project field-list <number> --owner <owner> --format json   # Status field and its options
gh api orgs/<org>/issue-types                                    # issue types, if the org uses them
```

Note: the labels that mean state or priority, the template names, the Project and its
Status options (that is the board column), issue types if the org uses them, and the
closing keyword convention in pull requests.

## Recipes

| Recipe | Command |
|---|---|
| What am I assigned | `gh issue list --assignee @me --state open --json number,title,labels,updatedAt` (across repos: `gh search issues --assignee @me --state open`) |
| Show an item | `gh issue view <n> --comments` |
| Create | `gh issue create --title "..." --body-file <file> --label bug` (add `-T "<name>"` when the repo has templates) |
| Comment | `gh issue comment <n> --body-file <file>` |
| Move state | Open or closed: `gh issue close <n> --reason "not planned"`, `gh issue reopen <n>`. Board column: `gh project item-edit --id <item-id> --project-id <project-id> --field-id <status-field-id> --single-select-option-id <option-id>` |
| Link a pull request | Put `Fixes #<n>` (or `Closes`, `Resolves`) in the PR description; it links now and closes the issue on merge into the default branch. `gh issue develop <n> --checkout` creates a linked branch |
| Search | `gh issue list --search "is:open label:bug in:title <words>"` or `gh search issues "<words>" --repo <owner>/<repo>` |

Body text goes through `--body-file` (or `-F -` from standard input) so quotes and
backticks survive.

## Traps

- Closing keywords only close the issue when the PR merges into the default branch, and only
  if they are in the PR description or a commit message, not a PR comment. Keywords in a PR
  that targets another branch are ignored.
- Moving a board column is a Project field edit, not an issue edit. It needs four IDs: the
  item ID, the project ID, the Status field ID and the option ID. Get them from
  `gh project item-list` and `gh project field-list` with `--format json`.
- `gh project` commands fail until the token has the `project` scope.
- `gh issue create` has no flag for issue types or sub-issues. Use the API:
  `gh api orgs/<org>/issue-types` to list types (classic tokens need `read:org`), and
  `gh api repos/<owner>/<repo>/issues/<n>/sub_issues` to list or (with `POST` and
  `sub_issue_id`) add sub-issues.
- `gh` picks the repo from the current directory's remotes. With forks, pass `-R <owner>/<repo>`.
- Search uses GitHub search syntax and has its own custom rate limit, stricter than the core API.

Checked against official docs on 2026-10-17.
