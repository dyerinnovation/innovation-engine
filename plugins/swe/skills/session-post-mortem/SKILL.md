---
name: session-post-mortem
description: Audit the current session for churn before a context compaction and propose fixes to the skills, rules, CLAUDE.md files and memory that caused it, approved item by item. Runs when the user announces a compaction ("do X and then I will compact", "let me compact and then Y", "about to compact", "I'll /compact after this", "before I compact"), or asks for a "post-mortem", "session post-mortem", "retro this session" or "what went wrong this session". Proposes only; applies nothing without per-item approval.
---

# Session post-mortem

Compaction is the moment a session's lessons are lost: the summary keeps the outcome,
not the friction. Lessons that stay in the conversation evaporate; lessons encoded in
the right instruction file compound. But every rule is context every future session
pays for, so the user is the gate on what gets encoded.

The `swe` plugin ships a `UserPromptSubmit` hook (`hooks/detect-compaction.sh`, registered
in the plugin's `hooks/hooks.json`) that injects a reminder to run this skill when a prompt
announces a compaction. It never blocks a prompt. The user can also invoke the skill
directly as `/swe:session-post-mortem`. `hooks/test-detect-compaction.sh` checks the
trigger phrases.

## 1. Do the requested work first

If the announcing message also asked for work ("push the branch, then I'll compact"),
finish that work completely before starting the post-mortem. The post-mortem covers it
too.

## 2. List the churn

Go over the whole session, not just the last stretch. Churn is effort that a better
instruction surface would have saved:

- work retried or redone (a failed command run again, an edit reverted, a lane re-run)
- wrong assumptions acted on (a path, a branch, an API shape, a tool's behavior)
- facts rediscovered that some file should have stated
- tool, hook or permission failures, and the workaround that got past them
- instructions the user had to give twice
- corrections from the user ("no, not that", "I said ...", "use X instead")
- files that contradicted each other, and which one turned out to be right

Each item gets one line of evidence: what happened and roughly when. Leave out work that
went fine, and do not re-review the diff; this is about process.

## 3. Find the surface that caused it

For each item, find the instruction that was missing, wrong, stale or too easy to miss.
Look in the surfaces that were in play this session:

- every CLAUDE.md loaded (user-level, workspace, project, subdirectory)
- user-level and project-level rules files (`.claude/rules/`)
- the skills used, including their scripts and reference files
- memory files (the auto-memory index and its entries)

Classify each item:

| Class | When |
|---|---|
| Rule | a standing behavior was missing or wrong |
| Skill or script | a repeated procedure should be written down, or a manual step scripted |
| Doc fix | a file states something false or stale, or two files disagree |
| Ticket | the fix is real work in a codebase, not an instruction change |
| Nothing | a genuine one-off; say so rather than forcing an artifact |

Prefer amending an existing file over adding one, and one sharp sentence over a
section. A contradiction is fixed by correcting the wrong file, not by adding a third.

Recurring churn escalates. If the same class of churn already has an approved fix (a
rule exists and was ignored, a memory entry covers it), the fix was too weak: propose
the next step up (rule to script, script to hook or check), flagged as a repeat.

## 4. Propose in one table

Present a single compact table, one row per item:

| # | Churn (one line of evidence) | Proposed change (file, size) | Recommend |
|---|---|---|---|
| 1 | Re-ran the deploy twice: wrong kube context | Amend `rules/deploy.md`: +1 line naming the context | Yes |
| 2 | Asked twice to skip italics | None; already in memory, followed after the reminder | Nothing |

State the size of every proposed change ("+3 lines to X", "new 20-line script",
"edit 1 line in Y"). Keep the recommend column honest: recommend against items whose
cost in context outweighs the churn they would save.

Then get a yes or no per item with AskUserQuestion (batch up to four items per
question). Do not treat silence or a general "looks good" as approval for items the
user did not see.

If the session had no churn, say "No churn this session" in one line. The check is the
deliverable; do not invent items to fill the table.

## 5. Apply only what was approved

Make exactly the approved changes, at the stated size. If an approved change turns out
larger than stated, stop and say so before writing it. Report each change as one line
with its file path. Unapproved items are dropped, not parked somewhere else.

Changes to files under version control follow that repo's usual flow (branch, commit);
do not push or merge unless the user asked for it in this session.

## 6. Hand back

End with one line telling the user it is safe to compact, for example:
"Post-mortem done (2 changes applied, 1 declined). Ready to compact."

## Guardrails

- Propose, never implement unapproved changes, including small ones.
- Process only: do not re-open decisions the user already made in the session.
- Never edit hook or permission settings as a post-mortem fix without approval of that
  exact change; those affect every session.
- Keep the whole post-mortem short. If it takes longer than the work it audits, cut it.
