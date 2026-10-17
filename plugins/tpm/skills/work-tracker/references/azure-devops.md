# Azure DevOps Boards

## Read this first: the CLI's gaps

`az boards` (the `azure-devops` extension for the Azure CLI) covers show, create, update,
delete, relations between work items, area and iteration paths, and flat WIQL queries.
`az boards work-item update --discussion "<text>"` adds a comment (the az docs: "Comment to
add to a discussion in a work item"), so a move plus a comment is one call:
`--state "Active" --discussion "picking this up"`. It has no command to:

- read the process (Agile, Scrum, Basic, CMMI or a custom inherited one)
- list work item types or the states of a type
- list allowed state transitions or required fields
- read, edit or delete comments, or choose a comment's format (`--discussion` returns the
  work item, not a comment id)
- link a pull request from the work item side (`relation add` targets work items only;
  for Azure Repos use `az repos pr work-item add` from the PR side)
- run tree or one-hop queries (`az boards query` supports flat queries only)

For those, go to the REST API or the MCP server. Do not spend calls probing `az`
for them.

## Interfaces, ranked

1. **Azure DevOps MCP server**, official, two forms:
   - Local (`@azure-devops/mcp`, Node 20 or newer, stdio). Works with Claude Code with no
     tenant setup, so start here.
   - Remote, hosted at `https://mcp.dev.azure.com/<org>` (streamable HTTP). Microsoft
     recommends it, but Claude Code needs a custom Microsoft Entra app registration to sign
     in (an admin may need to grant consent). The org must be backed by Entra ID.
2. **REST API** at `https://dev.azure.com/<org>/<project>/_apis/...`, `api-version=7.1`.
3. **`az boards`** for quick show, create and update when the REST call is more typing.

## Auth with least scope

Local MCP:

```
claude mcp add --transport stdio azure-devops -- npx -y @azure-devops/mcp <org> -d core work work-items search --authentication azcli
```

- `-d core work work-items search` loads only the domains these recipes need (always keep
  `core`; `search` carries `search_workitem`). With no `-d`, every domain loads.
- Auth modes (`--authentication` or `-a`): `interactive` (default, browser sign-in),
  `azcli` (reuses `az login`), `env` (Azure Identity chain), `envvar` (reads a bearer token
  from `ADO_MCP_AUTH_TOKEN`), `pat` (reads `PERSONAL_ACCESS_TOKEN`, the base64 of
  `<any-name>:<pat>`). Prefer `azcli` or interactive. Interactive needs a browser, so use
  `azcli` over SSH or in a container.

Remote MCP, after the Entra app registration (redirect URI
`http://localhost:3118/callback`):

```
claude mcp add --transport http ado https://mcp.dev.azure.com/<org> --client-id <client-id> --callback-port 3118
```

Limit it with headers: `X-MCP-Toolsets: wit` (work items plus `search_workitem`) and
`X-MCP-Readonly: true` for a read-only session.

Personal access token (PAT), when one is needed:

- Create it under User settings, Personal access tokens. Select one organization (global
  PATs stop working on 2026-12-01), only the scopes needed: Work Items Read and write
  (`vso.work_write`). Add Code Read (`vso.code`) only if you must read pull requests.
  Shortest expiry the user accepts.
- Keep it in `AZURE_DEVOPS_EXT_PAT`, which `az devops` reads directly when you have not
  signed in another way, so no login command ever carries it. For REST, use the PAT
  variant of the `ado` helper below (Basic auth, empty user name).
- With no PAT at all (preferred): `az login --allow-no-subscriptions`. The flag lets you
  sign in to a tenant where you have no Azure subscription, which is common for people who
  only use Azure DevOps; without it, `az login` can stop with a no-subscriptions error.
  Then pass a Microsoft Entra token as Bearer:
  `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv`
  captured into a variable, never printed. The token lasts about an hour.

Defaults: set by the `az devops configure` line in the block below.

Cheap read to prove the connector works: list projects (`core_list_projects`).

## Read the process first (REST)

Capture every runtime value into a variable and URL-encode anything that goes into a URL
path. Type names have spaces ("User Story", "Product Backlog Item"), so a hand-typed type
in a URL breaks, and a placeholder left between steps is a step that cannot run. The only
hand-filled values are the org, the project and the item id. Needs `jq`.

```bash
ORG="<org>"; PROJECT="<project>"; ID=4821
enc() { jq -rn --arg v "$1" '$v|@uri'; }                 # URL-encode one value
O="https://dev.azure.com/$ORG"; P="$O/$(enc "$PROJECT")"; A="api-version=7.1"
az devops configure --defaults organization="$O" project="$PROJECT"
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)
ado() { printf 'Authorization: Bearer %s\n' "$TOKEN" | curl -sf -H @- "$@"; }  # token via stdin, never argv
need() { for v; do eval "[ -n \"\${$v}\" ]" || { echo "stop: $v is empty; check the call that set it" >&2; return 1; }; done; }
need TOKEN   # stops here if az login has lapsed

TYPE=$(az boards work-item show --id "$ID" --query 'fields."System.WorkItemType"' -o tsv)
ado "$P/_apis/wit/workitemtypes?$A" | jq -r '.value[].name'                       # types in use
need TYPE && ado "$P/_apis/wit/workitemtypes/$(enc "$TYPE")/states?$A" \
  | jq -r '.value[] | "\(.name)\t\(.category)"'                                   # states with category
PID=$(ado "$O/_apis/projects/$(enc "$PROJECT")?$A" | jq -r '.id // empty')
need PID && ado "$O/_apis/projects/$PID/properties?keys=System.Process%20Template&api-version=7.1-preview.1"  # process name
```

With a PAT instead of `az login`, swap the helper for
`ado() { printf 'Authorization: Basic %s\n' "$(printf ':%s' "$AZURE_DEVOPS_EXT_PAT" | base64 | tr -d '\n')" | curl -sf -H @- "$@"; }`.
The `tr` matters: GNU `base64` (Linux) wraps its output at 76 characters, which splits
the header for a long PAT; macOS `base64` does not wrap. With `tr` it works on both.

The properties call needs the project ID (a GUID), not the name, which is why `PID` is
read first.

States carry a category (`Proposed`, `InProgress`, `Resolved`, `Completed`, `Removed`).
Reason about the category; names differ by process. Stock names for the main backlog type,
for orientation only:

| Process | States |
|---|---|
| Basic | To Do, Doing, Done |
| Agile | New, Active, Resolved, Closed, Removed |
| Scrum | New, Approved, Committed, Done, Removed |
| CMMI | Proposed, Active, Resolved, Closed |

Note also area and iteration paths the team uses (`az boards area project list`,
`az boards iteration team list --team <team>`).

## Recipes

| Recipe | MCP tool (action) | az or REST |
|---|---|---|
| What am I assigned | `wit_work_item` (`my`) | `az boards query --wiql "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] NOT IN ($DONE) ORDER BY [System.ChangedDate] DESC"`, with `$DONE` built below |
| Show an item | `wit_work_item` (`get`) | `az boards work-item show --id "$ID"` |
| Create | `wit_work_item_write` (`create`) | `az boards work-item create --type Bug --title "..." --description "..."` |
| Comment | `wit_work_item_comment_write` (`add`) | `az boards work-item update --id "$ID" --discussion "..."`; REST (below) when you need the comment id or markdown |
| Move state | `wit_work_item_write` (`update`) | `az boards work-item update --id "$ID" --state "$STATE"`, adding `--discussion "..."` to comment in the same call |
| Link a pull request | `wit_work_item_link_write` (`link_to_pull_request`) | Azure Repos: `az repos pr work-item add --id "$PR" --work-items "$ID"`, or `PATCH $P/_apis/wit/workitems/$ID?$A` with the body below |
| Search | `search_workitem` | `az boards query --wiql "... WHERE [System.Title] CONTAINS '...'"` |

`$DONE` is every Completed or Removed state name across the project's types, quoted for
WIQL (WIQL cannot filter on category):

```bash
DONE=$(ado "$P/_apis/wit/workitemtypes?$A" | jq -r '.value[].name' | while read -r t; do
  ado "$P/_apis/wit/workitemtypes/$(enc "$t")/states?$A" \
    | jq -r '.value[] | select(.category == "Completed" or .category == "Removed") | .name'
done | sort -u | sed "s/.*/'&'/" | paste -sd, -)
need DONE && az boards query --wiql "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] NOT IN ($DONE) ORDER BY [System.ChangedDate] DESC" -o table
```

An empty `DONE` means a states call failed (often an expired token, since `curl -sf`
prints nothing on an HTTP error); without the guard the query becomes `NOT IN ()`, which
is a WIQL syntax error.

### Move plus comment, end to end

Pick the target state from the states read above rather than typing it, then move and
comment in one call. Check the state name exists for this type first; names differ by
process.

```bash
STATES=$(ado "$P/_apis/wit/workitemtypes/$(enc "$TYPE")/states?$A")
STATE="Active"   # what the user asked for; or derive: [.value[]|select(.category=="InProgress")][0].name
if ! need TYPE STATES; then :   # need already said which value is empty; stop here
elif echo "$STATES" | jq -e --arg s "$STATE" 'any(.value[]; .name == $s)' >/dev/null; then
  az boards work-item update --id "$ID" --state "$STATE" --discussion "picking this up" \
    --query 'fields."System.State"' -o tsv
else
  echo "No state '$STATE' on $TYPE; valid:"; echo "$STATES" | jq -r '.value[].name'
fi
```

Verify the comment by its id, not by its position in a list. `--discussion` returns no
comment id, so find it by exact text with an explicit order, then keep the id:

```bash
CID=$(ado "$P/_apis/wit/workItems/$ID/comments?order=desc&\$top=20&api-version=7.1-preview.4" \
  | jq -r --arg t "picking this up" '[.comments[] | select(.text == $t)][0].id // empty')
need CID   # empty: the comment did not land, or the text differs (HTML-wrapped, edited)
```

When you post over REST instead, the response is the comment itself, so capture its id
and read it back:

```bash
BODY=$(jq -n --arg t "picking this up" '{text:$t}')   # body as an argument: stdin carries the header
CID=$(ado -X POST -H "Content-Type: application/json" -d "$BODY" \
    "$P/_apis/wit/workItems/$ID/comments?format=markdown&api-version=7.1-preview.4" \
  | jq -r '.id // .commentId // empty')
need CID && ado "$P/_apis/wit/workItems/$ID/comments/$CID?api-version=7.1-preview.4" | jq -r '.text'
```

The schema names the field `id`; some doc samples show `commentId`, hence the fallback.

Azure Repos pull request link over REST. Read the PR's `artifactId` first and use it as
is: `GET $P/_apis/git/repositories/<repo>/pullrequests/<pr-id>?$A`. It has the form
`vstfs:///Git/PullRequestId/<project-id>%2F<repo-id>%2F<pr-id>`. Then send, with
`Content-Type: application/json-patch+json`:

```json
[{"op":"add","path":"/relations/-","value":{
  "rel":"ArtifactLink",
  "url":"<artifactId>",
  "attributes":{"name":"Pull Request"}}}]
```

Native linking is easier when it applies: in Azure Repos, type `#` in the PR description
to pick the work item, or add it in the PR's Work items area. For GitHub repos connected
through the Azure Boards app, put `AB#<id>` in the PR description or a commit message (not
the title, not a comment); `Fixes AB#<id>` also moves it to the first Resolved-category
state (or Completed) when the PR merges into the default branch.

## Traps

- All REST updates are JSON Patch arrays with `Content-Type: application/json-patch+json`;
  plain JSON fails.
- The comments API is still preview (`7.1-preview.4`), and on the add call `format`
  (`markdown` or `html`) is required; pin the version string exactly.
- The `ado` helper feeds the auth header on standard input, so never also pipe a request
  body into it; pass the body with `-d "$BODY"`.
- The list-comments call takes `order=asc` or `order=desc`. Never assume the newest
  comment is first or last; match by id or exact text.
- WIQL has no state-category field. Filter on state names you read from the states call.
- Area and iteration paths use backslashes: quote them, and escape them in JSON.
- `az boards` picks up the organization from git config when no default is set; set
  defaults so it does not guess wrong in a repo with several remotes.
- The extension installs itself the first time you run an `az boards` command; run one
  interactively on a new machine before scripting it.
- Some state moves are blocked by rules on the process (required fields on Resolved, for
  example). Read the error, set the field, retry.
- The MCP server's tools are consolidated action-style tools (for example `wit_work_item`
  with an `action`); list the tools at runtime rather than hard-coding older names.
- Personal Microsoft accounts are not supported by the MCP server; the org must be backed
  by Microsoft Entra ID.

Checked against official docs on 2026-10-17 (az boards work-item, az login, wit comments add, get and list).
