# Linear

## Interfaces, ranked

1. **Official remote MCP server** (best). Streamable HTTP at `https://mcp.linear.app/mcp`;
   a read-only variant is at `https://mcp.linear.app/mcp/readonly`. The old SSE endpoint
   `https://mcp.linear.app/sse` is deprecated.
2. **GraphQL API** at `https://api.linear.app/graphql`, for anything the connector lacks.
3. **CLI**: not used here. Work through the MCP server or the GraphQL API.

## Auth with least scope

MCP, interactive (preferred):

```
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

Then run `/mcp` inside Claude Code and finish the OAuth sign-in in the browser. For a
read-only session, use the `/mcp/readonly` URL instead, or grant only the `read` scope.

API key, for the GraphQL API or a headless MCP session:

- Create it in Linear under Settings, Account, Security and access, Personal API keys.
- Restrict it: choose Read plus Write (or Read only), not Admin, and limit it to the teams
  you work in.
- Keep it in an environment variable such as `LINEAR_API_KEY`, set in the shell profile or
  read from the keychain. Never in the repo.
- Header format matters: a personal key goes in raw, `Authorization: <key>`, with no
  `Bearer`. An OAuth access token uses `Authorization: Bearer <token>`. The MCP server
  accepts either as `Authorization: Bearer <token>`.

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

MCP tool names below are the ones the server listed on the check date. List the tools at
runtime before relying on them.

| Recipe | MCP | GraphQL |
|---|---|---|
| What am I assigned | `list_issues` with assignee "me" and open states | `viewer { assignedIssues(filter: {state: {type: {nin: ["completed","canceled"]}}}) { nodes { identifier title state { name } } } }` |
| Show an item | `get_issue` with the key, `list_comments` | `issue(id: "ENG-7") { title description state { name } assignee { name } comments { nodes { body } } }` |
| Create | `save_issue` with team, title, description | `issueCreate(input: {teamId: "<team-uuid>", title: "...", description: "..."}) { success issue { identifier } }` |
| Comment | `save_comment` with the issue and body | `commentCreate(input: {issueId: $key, body: "..."}) { success comment { id } }` |
| Move state | `save_issue` with the issue and the new state | `issueUpdate(id: "ENG-7", input: {stateId: "<state-uuid>"}) { success }` |
| Link a pull request | Native: put the key in the branch name or PR title | `attachmentLinkURL(issueId: $key, url: $prUrl, title: "PR <n>") { success attachment { id url } }` |
| Search | `list_issues` with a query and filters | `searchIssues(term: "...", first: 20) { nodes { identifier title } }` |

GraphQL call shape. The key goes in on standard input so it never shows in the process
list, and `jq -n` builds the body so quotes in values cannot break the JSON:

```bash
lin() {  # usage: lin '<graphql>' '<variables json>'
  printf 'Authorization: %s\n' "$LINEAR_API_KEY" \
    | curl -s https://api.linear.app/graphql -H @- -H "Content-Type: application/json" \
        -d "$(jq -n --arg q "$1" --argjson v "${2:-null}" '{query:$q, variables:($v // {})}')"
}
need() { for v; do eval "[ -n \"\${$v}\" ]" || { echo "stop: $v is empty; read the errors array" >&2; return 1; }; done; }
lin '{ viewer { id name } }'
```

Read one team's states, in order, printing only the states. Parenthesize: in jq the
comma binds looser than `|=`, so `.errors, .x |= f` prints the whole response.

```bash
R=$(lin 'query($k:String!){ teams(filter:{key:{eq:$k}}){ nodes { id states { nodes { id name type position } } } } }' \
  "$(jq -n --arg k "ENG" '{k:$k}')")
echo "$R" | jq -c '.errors // empty'
STATES=$(echo "$R" | jq -r '.data.teams.nodes[0].states.nodes // [] | sort_by(.position)[] | "\(.name)\t\(.type)\t\(.id)"')
need STATES && echo "$STATES"
```

Comment and link, end to end. Capture each value into a variable instead of leaving a
placeholder between steps, and verify each write by the id it returned, not by list order:

```bash
KEY="ENG-7"; PR_URL="https://github.com/<owner>/<repo>/pull/<n>"   # the values the user gave
ISSUE=$(lin 'query($k:String!){ issue(id:$k){ id } }' "$(jq -n --arg k "$KEY" '{k:$k}')" \
  | jq -r '.data.issue.id // empty')   # proves the key exists; the UUID also works below
need ISSUE &&
CID=$(lin 'mutation($i:String!,$b:String!){ commentCreate(input:{issueId:$i, body:$b}){ success comment { id } } }' \
  "$(jq -n --arg i "$ISSUE" --arg b "repro steps added" '{i:$i,b:$b}')" | jq -r '.data.commentCreate.comment.id // empty') &&
need CID &&
AID=$(lin 'mutation($i:String!,$u:String!){ attachmentLinkURL(issueId:$i, url:$u){ success attachment { id } } }' \
  "$(jq -n --arg i "$ISSUE" --arg u "$PR_URL" '{i:$i,u:$u}')" | jq -r '.data.attachmentLinkURL.attachment.id // empty') &&
need AID &&
lin 'query($c:String!){ comment(id:$c){ body issue { identifier } } }' "$(jq -n --arg c "$CID" '{c:$c}')"
```

The `&&` chain stops at the first empty value, so no mutation runs against a missing
issue. When it stops, rerun that call without the trailing `jq` and read the `errors`
array.

## Traps

- The short key (`ENG-7`) or the UUID both work for `issue(id:)` and `issueUpdate(id:)`
  (developer guide) and for the `issueId` of `commentCreate`, `attachmentLinkURL` and
  `attachmentCreate` (the published schema: "Can be a UUID or issue identifier"). The
  developer guide's attachment examples show only UUIDs, so if a mutation rejects the key,
  pass `ISSUE` from the block above. `teamId`, `stateId` and `labelIds` need UUIDs; look
  them up first.
- Creating without `stateId` lands in the team's first Backlog-category state, or in Triage
  when Triage is on. Set the state if the team expects something else.
- The GraphQL API can return HTTP 200 with an `errors` array (partial success). Always
  check it. Rate-limit errors come back as HTTP 400 with the reason in `errors`.
- `searchIssues` is rate limited to 30 requests per minute. Prefer `issues(filter: ...)`
  or `assignedIssues(filter: ...)` when you know the fields to filter on.
- Pull request links: with the GitHub integration on, a branch or PR title with the key
  links the PR, and a closing word in the PR title or description ("Fixes ENG-7") also
  moves the issue on merge. By default a linked issue moves to In Progress when the PR
  opens and to Done on merge. Check the team's settings before also moving it by hand.
- Do not poll every issue; filter in the query and order by `updatedAt`. Rate limits apply,
  and polling is discouraged.
- Tool names on the MCP server change between releases. List the tools rather than
  hard-coding names.

Checked against official docs on 2026-10-17 (GraphQL getting started, attachments, and the published GraphQL schema in Linear's SDK repository).
