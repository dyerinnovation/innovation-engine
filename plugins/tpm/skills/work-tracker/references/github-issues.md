# GitHub Issues and Projects

## Interfaces, ranked

1. **`gh` CLI** (best for issues). Official, stable flags, JSON output, already signed in on
   most developer machines.
2. **GitHub MCP server**, official, remote at `https://api.githubcopilot.com/mcp`. Worth it
   when `gh` is not installed or the session has no shell.
3. **REST and GraphQL API**, through `gh api` so auth is handled for you. Needed for issue
   types, sub-issues and some Projects fields.

## Auth with least scope

`gh` (preferred): `gh auth login` and choose the browser. It stores the token in the OS
keychain. Projects need one extra scope: `gh auth refresh -s project` (or `-s read:project`
for read only).

Token sign-in, when browser sign-in is not possible: `gh auth login --with-token < <token-file-outside-repo>`,
or set `GH_TOKEN` in the environment. Prefer a fine-grained token limited to the repos in
question with Issues: Read and write, Pull requests: Read, Metadata: Read. Note that
fine-grained tokens cannot reach user-owned Projects; a classic token needs `repo` and
`project`.

MCP:

```
claude mcp add-json github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer ${GITHUB_PAT}"}}'
```

Keep `GITHUB_PAT` in the environment; never paste the literal token into a config file that
is tracked. The server can be limited to the issues toolset and to read-only; check the
server's docs for the current header or URL form.

Cheap read to prove it works: `gh auth status`, or the MCP "get me" tool.

## Read the process first

GitHub has only two states, open and closed (closed as completed or not planned). The real
process usually lives in labels, issue templates, issue types and a Project board.

```bash
gh label list --limit 100
ls .github/ISSUE_TEMPLATE/ 2>/dev/null
gh project list --owner <owner>
gh project field-list <number> --owner <owner> --format json   # Status field and its options
gh api graphql -f query='{ organization(login:"<org>") { issueTypes(first:20) { nodes { id name } } } }'
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
| Link a pull request | Put `Fixes #<n>` (or `Closes`, `Resolves`) in the PR body; it links now and closes on merge to the default branch. `gh issue develop <n> --checkout` creates a linked branch |
| Search | `gh issue list --search "is:open label:bug in:title <words>"` or `gh search issues "<words>" --repo <owner>/<repo>` |

Body text goes through `--body-file` (or `-F -` from standard input) so quotes and
backticks survive.

## Traps

- Closing keywords only close the issue when the PR merges into the default branch, and only
  if they are in the PR body or a commit message, not a PR comment.
- Moving a board column is a Project field edit, not an issue edit. It needs four IDs: the
  item ID, the project ID, the Status field ID and the option ID. Get them from
  `gh project item-list` and `gh project field-list` with `--format json`.
- `gh project` commands fail until the token has the `project` scope.
- Issue types and sub-issues are org-level features and are not exposed by every `gh`
  version's `issue create`; use `gh api graphql` for them.
- `gh` picks the repo from the current directory's remotes. With forks, pass `-R <owner>/<repo>`.
- Search uses GitHub search syntax and is rate limited separately from the core API.

## Verification status

Verified against the installed `gh` help: `issue list` flags, `issue create`, `issue edit`,
`issue develop`, `search issues`, `project item-edit` flags, `auth login --with-token` and the `project`
scope note. Verified against the MCP server's install guide: remote URL and the `add-json`
form. Not verified this pass: the `issueTypes` GraphQL field, the MCP read-only and toolset
switches, and fine-grained token reach into Projects.
