# Azure DevOps Boards

## Read this first: the CLI's gaps

`az boards` (the `azure-devops` extension for the Azure CLI) covers show, create, update,
relations and flat WIQL queries. It cannot:

- read the process (Agile, Scrum, Basic, CMMI or a custom inherited one)
- list work item types or the states of a type
- list allowed state transitions or required fields
- add a comment as a standalone call (only `--discussion` on update, as HTML)
- link a pull request by number (it links work item IDs or raw artifact URLs)
- run tree or one-hop queries (`az boards query` is flat only)

For those, go straight to the REST API. Do not spend calls probing `az` for them.

## Interfaces, ranked

1. **Azure DevOps MCP server**, local, official (`@azure-devops/mcp`, Node 20 or newer).
   Microsoft also runs a remote server, but it needs Entra dynamic client registration that
   Claude Code does not support, so use the local one.
2. **REST API** at `https://dev.azure.com/<org>/<project>/_apis/...`, `api-version=7.1`.
3. **`az boards`** for quick show, create and update when the REST call is more typing.

## Auth with least scope

MCP:

```
claude mcp add --transport stdio azure-devops -- npx -y @azure-devops/mcp <org> -d core work work-items --authentication azcli
```

- `-d core work work-items` loads only the domains these recipes need (keep `core`).
- Auth modes: interactive browser sign-in (default), `azcli` (reuses `az login`), `env`
  (Azure Identity chain), `envvar` (reads `ADO_MCP_AUTH_TOKEN`), `pat` (reads
  `PERSONAL_ACCESS_TOKEN`, the base64 of `<any-name>:<pat>`). Prefer `azcli` or interactive.

Personal access token (PAT), when one is needed:

- Create it under User settings, Personal access tokens. Scope it to one organization,
  Custom defined, Work Items: Read and write (`vso.work_write`). Add Code: Read only if you
  must look up pull request IDs. Shortest expiry the user accepts.
- Keep it in `AZURE_DEVOPS_EXT_PAT`, which `az devops` reads directly, so no login command
  ever carries it. For REST, `curl -u ":$AZURE_DEVOPS_EXT_PAT"` (empty user name).
- With no PAT at all: `az login`, then pass an Entra token as Bearer:
  `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv`
  piped into a variable, never printed.

Defaults: `az devops configure --defaults organization=https://dev.azure.com/<org> project=<project>`.

Cheap read to prove the connector works: list projects (`core_list_projects`).

## Read the process first (REST)

```bash
O="https://dev.azure.com/<org>"; P="$O/<project>"; A="api-version=7.1"
curl -s -u ":$AZURE_DEVOPS_EXT_PAT" "$O/_apis/projects/<project>/properties?api-version=7.1-preview.1"  # System.ProcessTemplateType
curl -s -u ":$AZURE_DEVOPS_EXT_PAT" "$P/_apis/wit/workitemtypes?$A"                        # types in use
curl -s -u ":$AZURE_DEVOPS_EXT_PAT" "$P/_apis/wit/workitemtypes/Bug/states?$A"             # states with category
```

States carry a category (`Proposed`, `InProgress`, `Resolved`, `Completed`, `Removed`).
Reason about the category; names differ by process. Stock names, for orientation only:

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
| What am I assigned | `wit_work_item` (`my`) | `az boards query --wiql "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.StateCategory] NOT IN ('Completed','Removed') ORDER BY [System.ChangedDate] DESC"` |
| Show an item | `wit_work_item` (`get`) | `az boards work-item show --id <id>` |
| Create | `wit_work_item_write` (`create`) | `az boards work-item create --type Bug --title "..." --description "..."` |
| Comment | `wit_work_item_comment_write` (`add`) | `POST $P/_apis/wit/workItems/<id>/comments?format=markdown&api-version=7.1-preview.4` with `{"text":"..."}` |
| Move state | `wit_work_item_write` (`update`) | `az boards work-item update --id <id> --state "Active"` |
| Link a pull request | `wit_work_item_link_write` (`link_to_pull_request`) | `PATCH $P/_apis/wit/workitems/<id>?$A`, body below |
| Search | `search_workitem` | `az boards query --wiql "... WHERE [System.Title] CONTAINS '...'"` |

Pull request link body (`Content-Type: application/json-patch+json`):

```json
[{"op":"add","path":"/relations/-","value":{
  "rel":"ArtifactLink",
  "url":"vstfs:///Git/PullRequestId/<project-id>%2F<repo-id>%2F<pr-id>",
  "attributes":{"name":"Pull Request"}}}]
```

Native linking is easier when it applies: in Azure Repos, link the work item in the pull
request or mention `#<id>`; for GitHub repos connected through the Azure Boards app, put
`AB#<id>` in the PR title or description.

## Traps

- All REST updates are JSON Patch arrays with `Content-Type: application/json-patch+json`;
  plain JSON fails.
- The comments API is still preview (`7.1-preview.4`); pin the version string exactly.
- `--discussion` takes HTML and shows as a history entry, not a threaded comment.
- `--assigned-to` needs a resolvable identity (display name can be ambiguous); prefer the
  sign-in name.
- Area and iteration paths use backslashes: quote them, and escape them in JSON.
- `az boards` guesses the organization from the git remote when `--detect` is on; set
  defaults so it does not guess wrong in a repo with several remotes.
- The extension installs itself on first use and can prompt; run one `az boards` command
  interactively on a new machine before scripting it.
- Some state moves are blocked by rules on the process (required fields on Resolved, for
  example). Read the error, set the field, retry.
- The MCP server's tool names were consolidated into action-style tools; list the tools at
  runtime rather than hard-coding older names.

## Verification status

Verified against current docs: `az boards` command list and the flags used above (`query`
is flat only, `work-item create/show/update`, `relation add` takes `--target-id` or
`--target-url`), MCP package, Claude Code add command, auth modes and env var names,
domains flag, tool names in the toolset doc, remote server not supported for Claude Code,
states endpoint and categories, comments endpoint and its preview version. Not verified
this pass: the `projects/properties` preview version, `System.StateCategory` in WIQL (fall
back to listing state names if rejected), and the PR artifact URL format (from long-standing
community usage; check one existing link with `az boards work-item relation show`).
