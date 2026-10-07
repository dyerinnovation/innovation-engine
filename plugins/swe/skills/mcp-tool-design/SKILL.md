---
name: mcp-tool-design
description: Design, add or review a tool on a Model Context Protocol (MCP) server so a model picks it correctly and a host or directory review accepts it. Covers naming, the description a model reads, input and output schemas, honest behavior annotations (readOnlyHint, destructiveHint, idempotentHint, openWorldHint), scopes and auth, input sanitization, errors, audit, tests and docs. Use when asked to "add an MCP tool", "new MCP tool", "expose this feature over MCP", "write tool descriptions", "set tool annotations", "review our MCP server", "why does the model call the wrong tool", or before submitting an MCP server or app to a directory such as ChatGPT or Claude.
---

# MCP Tool Design

An MCP tool has two readers: the model that decides whether to call it, and the host or
reviewer that decides whether to trust it. Most tool bugs are not code bugs. They are a
description that sends the model to the wrong tool, a schema that accepts nonsense, or an
annotation that claims a tool is safe when it is not. Design for both readers on purpose.

## When to use

- Adding a tool to an MCP server, or exposing an existing feature through one.
- Reviewing a server before a directory submission or a security review.
- Debugging a model that calls the wrong tool, calls a tool twice, or never calls it.

## Step 1: Decide the tool's shape before writing code

Write these down in one line each. If any line is hard to write, the tool is not ready.

1. **Job**: one verb and one object ("list open tasks", "delete one task"). One tool, one job.
   A tool that takes a `mode` argument switching between read and write is two tools.
2. **Effect class**: reads only, writes and can be undone, writes and cannot be undone,
   starts background work, or reaches outside parties (email, public web, third-party APIs).
3. **Who it acts as**: the signed-in user, a service identity, or the agent itself. Say it
   in the description when it is not obvious.
4. **Scope**: the permission a caller must hold to run it.
5. **Retry behavior**: what happens if the same call arrives twice.

## Step 2: Name and describe it for the model

- **Name**: `verb_object` in snake case, scoped with a short server prefix when the host
  shows many servers side by side (`acme_list_tasks`, `acme_delete_task`). Stable once shipped:
  renaming breaks every prompt and skill that mentions it.
- **Title**: a short human label for the host UI ("Delete a task").
- **Description**, in this order:
  1. What it does, in one sentence.
  2. When to use it, and when to use a sibling tool instead ("Call list_tasks first").
  3. What it returns, in one sentence.
  4. Any cost, approval, or irreversibility the model should weigh ("Permanently deletes").
- Keep it under about 80 words. Long descriptions crowd the context of every turn.
- Never put instructions to ignore other tools, or marketing copy, in a description.
  Reviewers treat that as manipulation.

## Step 3: Schemas

- **Input schema**: typed, required fields marked, enums for closed sets, length limits on
  every string, ranges on every number. Describe each field in a few words.
- Prefer ids over free text for anything that selects a record.
- **Output schema**: declare it when the host supports structured results. Return
  structured content plus a short text summary the model can quote.
- Return only what the request needs. No tokens, internal ids that are not used by a
  follow-up call, or personal data the user did not ask for.

## Step 4: Annotations, set honestly on every tool

Hosts use behavior hints to decide on confirmation prompts, and directory reviews compare
them against what the tool really does. A mismatch is one of the most common rejection
reasons. When a hint is missing, the MCP spec defaults assume the worst for two of them,
so leaving them off makes a harmless tool look dangerous.

| Hint | Spec default | Set to true when |
|---|---|---|
| `readOnlyHint` | false | It only fetches, lists or looks up, and changes nothing anywhere. |
| `destructiveHint` | true | It can cause an outcome you cannot undo: delete, overwrite, send a message, revoke access, spend money. |
| `idempotentHint` | false | Calling again with the same arguments has no further effect. |
| `openWorldHint` | true | It reaches the public internet or open-ended outside parties. False for a bounded private account. |

Rules that catch most mistakes:

- Set `readOnlyHint`, `destructiveHint` and `openWorldHint` to an explicit true or false on
  every tool, even when the value matches the default. Some directories reject a server
  with any missing.
- Starting a job, queueing work or creating a draft is a write. `readOnlyHint: false`, even
  when nothing visible changes yet.
- Sending anything to a person or address the user typed is destructive (it cannot be
  unsent) and open world.
- Deleting by id is usually destructive and idempotent.
- Write one sentence per tool that justifies each hint. If you cannot, the tool's job is
  not clear yet. Some reviews ask for these justifications.

Example of four tools with different hints (TypeScript SDK shape; Python is the same idea):

```ts
server.registerTool('list_tasks', {
  title: 'List tasks',
  description: "List the signed-in user's open tasks. Use when the user asks what is on their list.",
  annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
}, listTasks);

server.registerTool('create_task', {
  title: 'Create a task',
  description: "Add one task to the signed-in user's list. Returns the new task id.",
  inputSchema: z.object({ title: z.string().min(1).max(200) }),
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false },
}, createTask);

server.registerTool('delete_task', {
  title: 'Delete a task',
  description: 'Permanently delete one task. Cannot be undone.',
  inputSchema: z.object({ taskId: z.string() }),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: true, openWorldHint: false },
}, deleteTask);

server.registerTool('email_task', {
  title: 'Email a task',
  description: 'Send one task to an email address the user gives. Cannot be unsent.',
  inputSchema: z.object({ taskId: z.string(), to: z.email() }),
  annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true },
}, emailTask);
```

## Step 5: The security pipeline every call passes

Run these in the same order for every tool, in shared code, not inside each handler:

1. **Authenticate** the caller from the request itself. On a remote server, validate the
   bearer token's issuer, audience (your server's URL) and expiry on every request. A token
   minted for another resource gets 401.
2. **Authorize by scope**. Keep one table mapping tool name to required scope. A tool that
   is missing from the table is denied by default, so a new tool cannot ship unguarded.
   A valid token without the scope gets 403.
3. **Sanitize input**: validate formats (ids, enums), clamp numbers, cap string lengths,
   strip control characters, and strip markup from free text that will be shown to people
   or other models.
4. **Rate limit** per caller and per tool.
5. **Guard side effects against replay**: if the host can redeliver a call, record a call
   id before a side-effecting tool runs and refuse a duplicate. Release the id when the
   call fails before running, so a legitimate retry is not refused.
6. **Audit**: one structured log record per call with tool, caller, success, and error.

Remember that tool output becomes model input. Treat text you return from users or the web
as untrusted data, and label it as such rather than passing it through as instructions.

## Step 6: Errors

- Return a tool error result (`isError: true`) with a plain sentence the model can act on:
  what was wrong and what to try ("No task with that id. Call list_tasks to get ids.").
- Distinguish "you lack permission" (with the scope name) from "not found" from "try later".
- Never return stack traces, SQL, or secrets.

## Step 7: Tests and docs, in the same change

- Unit tests per tool: happy path, a missing or bad id, an empty result, a scope denial,
  and oversized input.
- A construction smoke test: build the real server object and list its tools in CI.
  Mocked unit tests do not catch a server that fails to start or a lazy import that breaks
  at call time.
- An annotation test that asserts every registered tool sets all three required hints
  and appears in the scope table.
- Try it in a real client (an MCP inspector, then the target host in developer mode):
  one read tool and one write tool. After changing names, descriptions, schemas or
  annotations, refresh the connection and start a new conversation; hosts cache tool lists.
- Update the tool reference doc (name, description, parameters, example), and any skill or
  plugin that teaches an agent to use the tool.

## Review checklist

- [ ] One job per tool; no mode flag that switches between read and write.
- [ ] Description says what, when, returns, and any irreversibility, in under about 80 words.
- [ ] Every input field typed, bounded and described.
- [ ] All three required hints set explicitly; each one justified in a sentence.
- [ ] Tool listed in the scope table; unmapped tools denied by default.
- [ ] Errors are actionable sentences; nothing internal leaks.
- [ ] Tests, construction smoke, annotation test and docs updated in the same change.
