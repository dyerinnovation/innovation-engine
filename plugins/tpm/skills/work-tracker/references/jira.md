# Jira Cloud

## Interfaces, ranked

1. **Atlassian remote MCP server** (best). HTTP at `https://mcp.atlassian.com/v2/mcp`.
   Covers Jira, Confluence and more. OAuth 2.1 sign-in; API token sign-in only if the site
   admin allows it.
2. **Atlassian CLI** (`acli`), official. Good for search, view, create, comment and
   transition by status name.
3. **REST API v3** at `https://<site>.atlassian.net/rest/api/3/`, for reading the process,
   remote links and anything else.

## Auth with least scope

MCP (preferred):

```
claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
```

Then run `/mcp` in Claude Code and finish the OAuth sign-in. Consent only to the products
you need.

CLI: `acli jira auth login --web` signs in through the browser. For token sign-in, the
token is read from standard input, so it never appears in the command line:

```
acli jira auth login --site "<site>.atlassian.net" --email "<account-email>" --token < <token-file-outside-repo>
```

API token for REST:

- Create it at the Atlassian account security page. Prefer a token with scopes, and pick
  only `read:jira-work` and `write:jira-work` (add `read:jira-user` to look up people).
- A token with scopes is called through the gateway,
  `https://api.atlassian.com/ex/jira/<cloud-id>/rest/api/3/...`, not the site URL. Get the
  cloud id from `https://<site>.atlassian.net/_edge/tenant_info`.
- A classic token (no scopes) works on the site URL with basic auth but carries the full
  power of your account. Use it only if scoped tokens are blocked.
- Keep it in an environment variable such as `JIRA_API_TOKEN`; pass it with
  `-u "$JIRA_EMAIL:$JIRA_API_TOKEN"` so it never lands in the transcript.

Cheap read to prove the connector works: list accessible resources or visible projects.

## Read the process first

Jira workflows differ per project and per issue type, and moves are transitions with IDs,
not free state edits.

```bash
B="https://<site>.atlassian.net/rest/api/3"
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$B/project/<KEY>/statuses"           # statuses per issue type
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$B/issue/createmeta/<KEY>/issuetypes" # types and required fields
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$B/issue/<KEY-1>/transitions"         # moves allowed from here
```

Note: statuses per type, which status category means done, required fields per type,
whether the project is team-managed or company-managed, and components or labels in use.

## Recipes

| Recipe | acli | REST v3 |
|---|---|---|
| What am I assigned | `acli jira workitem search --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC" --json` | `POST /search/jql` with the same JQL and a `fields` list |
| Show an item | `acli jira workitem view KEY-1 --fields "*navigable"` | `GET /issue/KEY-1?fields=summary,status,assignee,description,comment` |
| Create | `acli jira workitem create --project KEY --type Task --summary "..." --description "..."` | `POST /issue` with `fields.project.key`, `issuetype.name`, `summary` |
| Comment | `acli jira workitem comment create --key KEY-1 --body "..."` | `POST /issue/KEY-1/comment` with an ADF body |
| Move state | `acli jira workitem transition --key KEY-1 --status "In Progress"` | `GET /issue/KEY-1/transitions`, then `POST` the same path with `{"transition":{"id":"<id>"}}` |
| Link a pull request | Native: put `KEY-1` in the branch name, commit or PR title | `POST /issue/KEY-1/remotelink` with `{"object":{"url":"<pr-url>","title":"PR <n>"}}` |
| Search | `acli jira workitem search --jql "project = KEY AND text ~ \"...\"" --limit 20` | `POST /search/jql` |

With the MCP connector, the same recipes map to its tools (search by JQL, get issue, create
issue, add comment, get transitions, transition issue). List the tools at runtime; names
changed between v1 and v2 of the server.

## Traps

- The old `/rest/api/3/search` endpoint was removed. Use `/rest/api/3/search/jql`. It pages
  with `nextPageToken`, returns no total, and some users report tokens that loop; cap pages.
- REST v3 bodies for descriptions and comments are Atlassian Document Format (ADF) JSON, not
  plain text or wiki markup. `acli` accepts plain text and converts it.
- Transitions are by ID and depend on the current status. A status that exists in the
  project may not be reachable from here; read `/transitions` first.
- Assignees are `accountId` values, not usernames or emails. Look them up with
  `GET /user/search?query=...`, or use `@me` in `acli`.
- Team-managed and company-managed projects expose different fields and issue type IDs.
- `acli` calls items "work items"; the REST API still says "issue". Same thing.
- Native PR links (the development panel) need the GitHub or other source integration
  installed on the site. Without it, use a remote link.

## Verification status

Verified against current docs: MCP URL, transport, add command, `acli jira auth login` flags,
`acli jira workitem search`, `view`, `create`, `comment create`, `transition` flags, removal
of the old search endpoint and `nextPageToken` paging. Not verified this pass: the exact
v2 MCP tool names, scoped-token gateway behavior with basic auth (community reports
disagree; try Bearer if basic fails), `_edge/tenant_info`, and the `statuses`,
`createmeta` and `remotelink` request shapes (check the REST reference before use).
