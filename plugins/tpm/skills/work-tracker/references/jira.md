# Jira Cloud

## Interfaces, ranked

1. **Atlassian Rovo MCP server** (best). HTTP at `https://mcp.atlassian.com/v2/mcp`, the
   recommended endpoint. Covers Jira, Confluence and more. OAuth 2.1 sign-in; API token
   sign-in only after an organization admin turns it on (Atlassian Administration, Rovo,
   Rovo MCP server, Authentication).
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
you need. The v1 endpoints still work; the v1 SSE endpoint is retired.

CLI: `acli jira auth login --web` signs in through the browser. For token sign-in, pass
`--token` with no value and the token is read from standard input, so it never appears in
the command line:

```
acli jira auth login --site "<site>.atlassian.net" --email "<account-email>" --token < <token-file-outside-repo>
```

API token for REST:

- Create it at the Atlassian account API token page. Prefer "Create API token with scopes",
  pick the Jira app, the shortest expiry the user accepts (1 to 365 days), and only the
  classic scopes `read:jira-work` and `write:jira-work` (add `read:jira-user` to look up
  people). Scopes cannot be changed later; make a new token instead.
- A token with scopes does not work on the site URL. Call it through the gateway,
  `https://api.atlassian.com/ex/jira/<cloud-id>/rest/api/3/...`, with the same basic auth
  (email plus token). Get the cloud id from `https://<site>.atlassian.net/_edge/tenant_info`.
- A token without scopes works on the site URL with basic auth but carries the full power
  of your account. Use it only for a tool that does not support scoped tokens.
- Keep it in an environment variable such as `JIRA_API_TOKEN`; pass it with
  `-u "$JIRA_EMAIL:$JIRA_API_TOKEN"` so it never lands in the transcript.

Cheap read to prove the connector works: MCP `getAccessibleAtlassianResources` or
`listJiraProjects`; over REST, `GET /myself`.

## Read the process first

Jira workflows differ per project and per issue type, and moves are transitions with IDs,
not free state edits. `B` is the site URL for a token without scopes, or the gateway URL
for a token with scopes.

```bash
B="https://<site>.atlassian.net/rest/api/3"   # or https://api.atlassian.com/ex/jira/<cloud-id>/rest/api/3
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$B/project/<KEY>/statuses"           # statuses per issue type
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$B/issue/createmeta/<KEY>/issuetypes" # types for create
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$B/issue/<KEY-1>/transitions"         # moves allowed from here
```

Note: statuses per type, which status category means done, required fields per type,
whether the project is team-managed or company-managed, and components or labels in use.

## Recipes

MCP tool names below are from the server's supported tools list on the check date. The
server shows a few primary tools and discovers the rest on demand; list the tools at
runtime before relying on a name.

| Recipe | MCP | acli | REST v3 |
|---|---|---|---|
| What am I assigned | `searchJiraIssuesUsingJql` | `acli jira workitem search --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC" --json` | `POST /search/jql` with the same JQL and a `fields` list |
| Show an item | `getJiraIssue` | `acli jira workitem view KEY-1 --fields "*navigable"` | `GET /issue/KEY-1?fields=summary,status,assignee,description,comment` |
| Create | `createJiraIssue` | `acli jira workitem create --project KEY --type Task --summary "..." --description "..."` | `POST /issue` with `fields.project.key`, `fields.issuetype.name`, `fields.summary` |
| Comment | `addOrEditJiraIssueComment` | `acli jira workitem comment create --key KEY-1 --body "..."` | `POST /issue/KEY-1/comment` with an ADF `body` |
| Move state | `listJiraIssueTransitions`, then `transitionJiraIssue` | `acli jira workitem transition --key KEY-1 --status "In Progress"` | `GET /issue/KEY-1/transitions`, then `POST` the same path with `{"transition":{"id":"<id>"}}` |
| Link a pull request | `createJiraIssueRemoteIssueLink` | Native: put `KEY-1` in the branch name, commit message or PR title | `POST /issue/KEY-1/remotelink` with `{"object":{"url":"<pr-url>","title":"PR <n>"}}` |
| Search | `searchJiraIssuesUsingJql` | `acli jira workitem search --jql "project = KEY AND text ~ \"...\"" --limit 20` | `POST /search/jql` |

## Traps

- The old `/rest/api/3/search` endpoint is being removed. Use `/rest/api/3/search/jql`. It
  pages with `nextPageToken` and `isLast`, returns no total. Set `maxResults` and cap the
  number of pages you fetch. For a count, use `POST /search/approximate-count`.
- REST v3 bodies for descriptions and comments are Atlassian Document Format (ADF) JSON, not
  plain text or wiki markup. `acli` accepts plain text (or ADF) for `--body` and
  `--description`.
- Transitions are by ID and depend on the current status. A status that exists in the
  project may not be reachable from here; read `/transitions` first.
- Assignees are `accountId` values, not usernames or emails. Look them up with
  `GET /user/search?query=...` (or MCP `lookupJiraAccountId`), or use `@me` with
  `acli jira workitem create --assignee`.
- Team-managed and company-managed projects configure issue types and fields separately.
  Read `createmeta` for the exact project before a create.
- `acli` calls items "work items"; the REST API still says "issue". Same thing.
- Keys are case sensitive in development links: `KEY-1`, not `key-1`.
- Native PR links (the development panel) need the GitHub or other source integration
  installed on the site. Without it, use a remote link.

Checked against official docs on 2026-10-17.
