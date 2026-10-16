# Linear

## Interfaces, ranked

1. **Official remote MCP server** (best). Streamable HTTP at `https://mcp.linear.app/mcp`;
   a read-only variant is at `https://mcp.linear.app/mcp/readonly`. The old SSE endpoint
   `https://mcp.linear.app/sse` is deprecated.
2. **GraphQL API** at `https://api.linear.app/graphql`, for anything the connector lacks.
3. **CLI**: Linear ships no official CLI. Community CLIs exist; do not depend on one.

## Auth with least scope

MCP, interactive (preferred):

```
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

Then run `/mcp` inside Claude Code and finish the OAuth sign-in in the browser. For a
read-only session, use the `/mcp/readonly` URL instead.

API key, for the GraphQL API or a headless MCP session:

- Create it in Linear under Settings, Security and access, Personal API keys.
- Restrict it: choose Read plus Write (or Read only), not Admin, and limit it to the teams
  you work in. A key limited to some teams fails with FORBIDDEN on other teams.
- Keep it in an environment variable such as `LINEAR_API_KEY`, set in the shell profile or
  read from the keychain. Never in the repo.
- Header format matters: a personal key goes in raw, `Authorization: <key>`, with no
  `Bearer`. An OAuth access token uses `Authorization: Bearer <token>`. The MCP server
  accepts either as a Bearer header.

Cheap read to prove the connector works: list teams, or `viewer { id name }` over GraphQL.

## Read the process first

Each team has its own workflow states, grouped by a fixed `type`: `triage`, `backlog`,
`unstarted`, `started`, `completed`, `canceled`. Names are per team; the type is what to
reason about.

- MCP: list teams, then list issue statuses for the team, then list issue labels.
- GraphQL:

```graphql
query {
  teams { nodes { id key name
    states { nodes { id name type position } }
    labels { nodes { id name } } } }
}
```

Note per team: state names in order, which are `completed` and `canceled`, whether Triage
is on, label groups in use, and whether cycles and projects are used.

## Recipes

| Recipe | MCP (tool names as listed by the server) | GraphQL |
|---|---|---|
| What am I assigned | `list_issues` with assignee "me" and open states | `viewer { assignedIssues(filter: {state: {type: {nin: ["completed","canceled"]}}}) { nodes { identifier title state { name } } } }` |
| Show an item | `get_issue` with the key, `list_comments` | `issue(id: "ENG-7") { title description state { name } assignee { name } comments { nodes { body } } }` |
| Create | `save_issue` with team, title, description | `issueCreate(input: {teamId: "<team-uuid>", title: "...", description: "..."}) { success issue { identifier } }` |
| Comment | `save_comment` with the issue and body | `commentCreate(input: {issueId: "<issue-id>", body: "..."}) { success }` |
| Move state | `save_issue` with the issue and the new state | `issueUpdate(id: "ENG-7", input: {stateId: "<state-uuid>"}) { success }` |
| Link a pull request | Native: put the key in the branch name or PR title | `attachmentLinkURL(issueId: "<issue-id>", url: "<pr-url>") { success }` |
| Search | `list_issues` with a query and filters | `searchIssues(term: "...") { nodes { identifier title } }` |

GraphQL call shape, token from the environment and never echoed:

```bash
curl -s https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" -H "Content-Type: application/json" \
  -d '{"query":"{ viewer { id name } }"}'
```

## Traps

- `issueUpdate` and `issue(id:)` accept the short key (`ENG-7`) or the UUID; most create
  inputs (`teamId`, `stateId`, `labelIds`) need UUIDs. Look them up first.
- Creating without `stateId` lands in the team's first backlog state, or Triage when Triage
  is enabled. Set the state if the team expects something else.
- The GraphQL API can return HTTP 200 with an `errors` array. Always check it.
- Pull request links: with the GitHub or GitLab integration on, a branch named with the key
  or a PR body with "Fixes ENG-7" links the PR and can move the issue on merge. Check
  the team's settings before also moving it by hand, or it moves twice.
- Do not poll every issue; filter in the query and order by `updatedAt`. Rate limits apply.
- Tool names on the MCP server change between releases. List the tools rather than
  hard-coding names.

## Verification status

Verified against current docs: MCP URLs, transports, add command, auth header formats,
API key restrictions, GraphQL endpoint, `viewer`, `issue`, `issueCreate`, `issueUpdate`,
default state on create. Not verified against docs this pass: `searchIssues`,
`attachmentLinkURL` and `commentCreate` argument names (check the schema explorer before use).
