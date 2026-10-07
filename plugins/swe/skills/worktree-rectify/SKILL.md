---
name: worktree-rectify
description: Hunt for dangling work (uncommitted changes, unpushed commits, stashes, orphaned branches and worktrees) across every repo the current work has touched, then recover it before new agents start or before a session closes. Triggers on "/worktree-rectify", "rectify worktrees", "check for dangling work", "bookend check", "anything left uncommitted", or the start and end of any multi-session or multi-agent sprint.
---

# Worktree rectify

Bookend multi-agent work with a dangling-work audit. Run it at **session start** (recover
the last session's work before new agents spawn) and at **session end** (never close out
with uncommitted or unpushed changes).

## 1. Find the repos in scope

Take the list from the current workspace: the repos the session or plan has touched, the
working directory and its git submodules, and any worktrees those repos list
(`git worktree list`). If the scope is still unclear, ask: "Which repos should I check?"

## 2. Run the scan

The scan is read-only command work, not reasoning, so give it to one agent on the
**small or mid-tier** model class (see `agent-model-routing`), and name the model in the
spawn. In every repo in scope, it runs:

1. `git status --porcelain`: uncommitted working-tree changes
2. `git stash list`
3. `git log @{u}..HEAD --oneline`: unpushed commits on the current branch (note branches
   with no upstream)
4. `git branch -a` and `git log --all --oneline --source | head -50`: other branches with
   recent work
5. `git reflog --all | head -50` and `git fsck --lost-found --unreachable 2>&1 | head -30`
6. `git worktree list`, plus stray checkouts in the temp directory or next to the repo
7. In a long or resumed session, the transcript for "SHA pending", "deferred commit" or
   "will push later"
8. For each changed file, `git log --all -p -S "<identifying line>"` to see whether the same
   change already landed elsewhere (avoid double commits)

It writes findings to the audit report. Default path: `./worktree-audit-<YYYY-MM-DD>.md`
in the workspace root; use the project's own docs folder if it has a convention for
reports, or a path the user gives.

## 3. Triage each finding

- **Commit and push**: clearly part of current or finished work. Stage files by name
  (never `git add -A`), commit with the usual co-author trailer, push, and backfill the
  commit SHA on the matching item in your issue tracker.
- **Park**: real work that is not ready. `git stash push -m "wip:<item>"` plus a follow-up
  item in your issue tracker so it is not forgotten.
- **Discard**: only with the user's explicit yes. Never auto-discard.

## 4. Verify clean

Re-run `git status` and `git log @{u}..HEAD` in every repo. Confirm: clean working trees,
no unpushed commits unless deliberately parked, no unlabeled stashes, and no tracker items
still saying "SHA pending".

## 5. Report

Add a `## Resolution` section to the audit report: files recovered with commit SHAs, items
backfilled, anything parked with its stash label and follow-up item, and a final status of
"clean" or "open items: <list>". Tell the user in one line, for example "Rectify complete:
3 commits recovered, 2 items backfilled, 1 parked" or "Clean, nothing dangling".

## When to run

- Session start, before any implementation agent spawns.
- Session end, before compacting or marking a sprint done.
- After an agent crashes or stops unexpectedly mid-commit.
- Before a force-push or any destructive git operation.

## Anti-patterns

- `git add -A` or `git add .` in a rectify pass: files you do not expect may belong to
  another agent.
- Force-pushing during rectification.
- Discarding work without the user's explicit approval.
- Skipping a repo because it was "probably fine".
