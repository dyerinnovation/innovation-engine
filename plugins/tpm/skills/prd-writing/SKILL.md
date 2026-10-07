---
name: prd-writing
description: Write a per-release product requirements document (PRD) that is grounded in the code, scannable in one screen, and ready to build and test against. Reads the code first, stamps each requirement with file:line and the commit, puts each decision next to the requirement it changes with a suggested default, draws a state diagram with a screen per state for lifecycle features, writes EARS acceptance criteria tagged ci, rubric or human, and runs a small lint. Use when asked to "write a PRD", "new PRD", "scaffold a PRD", "spec this release", "requirements for", "turn this spike into a PRD", "acceptance criteria for", or before any feature goes to build lanes.
---

# PRD Writing

A PRD is the contract between the person who says yes and the people or agents who build.
It fails in three common ways: it describes a system that no longer matches the code, it
leaves open questions without a recommended answer so building stalls, and its acceptance
criteria cannot be checked. This method closes all three.

One release equals one item. If the work needs two PRDs, it is two releases.

## Inputs

- The release it belongs to (a rung on the release ladder; see the release-ladder skill).
- A short slug, 2 to 4 words.
- Any spike, research doc or request it synthesizes.
- The vision doc and master PRD or decision ledger, so the new PRD does not contradict a
  standing decision or non-goal.

## Step 1: Read the code first

Before writing a single requirement, read the code the feature touches and fill the Code
Read table: entrypoints (routes, tools, jobs), records (models, tables), and screens, each
with `path:line`. Record the commit short sha for every repo you read.

This step routinely changes the plan. A feature described as "a small change on one side"
may turn out to need a route that was removed, a branch that never existed, and a screen
nobody built. Docs that disagree with the code go in the table as doc drift.

## Step 2: Scaffold from the template

Copy `references/prd-template.md` to your PRD folder as `<release>-<slug>-prd.md`. Fill the
header first: owner, status `draft`, release, date, code read at, parent docs, source. For any
release that connects to an outside platform, fill the credential path and acting identity
line: how the credential is obtained, and whose identity the platform sees. Two credential
shapes disagreeing about who acts is a real class of bug this line catches.

## Step 3: Lead with the pitch, fold the detail

The top of the PRD is read by the decider in about one screen:

- one sentence thesis
- one diagram
- three "at a glance" bullets
- the decisions table

Everything else (requirements, edge cases, criteria, risks, waves, tickets) is reference
for builders. In a rendered version, put it in collapsible sections. Every section is a
heading plus bullets, a table or a diagram; paragraphs at most two sentences.

## Step 4: Diagram

- Simple feature: one flow diagram.
- Anything with a lifecycle (requests, invites, jobs, approvals, drafts): a state diagram
  plus a table listing one screen or mockup for each state, what enters it and what leaves
  it. Missing screens show up here, not in review.

## Step 5: Decisions with defaults, in place

Replace a bare open-questions list with the Decisions table. Each open decision lists the
options, a suggested default with a one-line reason, and which requirements or criteria it
changes. The decider can then answer by accepting defaults, and building is never blocked
on an unanswered question. Flag any default that stays untouched at approval so it is a
conscious choice.

## Step 6: Requirements

One row per requirement: a short claim (about 30 words or fewer), a Where cell with the
`path:line` it changes or extends, and a work bucket that tells the planner how it can be
parallelized (research spike, isolated code, overlap risk, shippable feature, infra
bootstrap). Requirement granularity is the sprint plan; get it right here.

## Step 7: Edge cases, then acceptance criteria

List edge cases first: empty, duplicate, expired, unauthorized, offline, concurrent, very
large. Each becomes its own criterion.

Write criteria in EARS form, one verifiable check per row:

- When <event>, the system shall <behavior>.
- While <state>, the system shall <behavior>.
- If <error>, then the system shall <handling>.

Tag each with exactly one of:

| Tag | Meaning | Covered by |
|---|---|---|
| `ci` | An automated test or scripted probe proves it | the test path and name |
| `rubric:<id>` | A blocking criterion in an evaluation rubric proves it (LLM output) | the prompt and rubric locations |
| `human` | A person must see it in a release walk | the walk |

For LLM behavior, a rule is covered only when it is in both the prompt and a blocking
rubric criterion. If you cannot name what covers a `ci` criterion, it is not covered.

## Step 8: The rest

Success metric (the one number that says it worked after ship, distinct from the
criteria), risks with a guard each, waves with what proves each done, and tickets generated
from requirements, each linking back to the PRD.

## Step 9: Lint

```bash
python3 scripts/lint_prd.py <your-prd>.md
```

It fails on: a requirement without `path:line`, an open decision without a default, a
criterion without exactly one valid tag, a `ci` or `rubric` criterion without its covering
test, and header fields left blank. It warns on long claims and leftover placeholders. A
clean lint is necessary, not sufficient; still look at the rendered page at phone and
desktop width.

## Step 10: Stop at the gate

Hand the draft to the decider. Do not create tickets or start builders until the status is
`approved`. After approval:

- Add the release to the master ladder if it is new (release-ladder skill).
- Render the PRD if your project keeps a human reading copy beside the markdown, and keep
  the render in step with its source.
- For shippable-feature lanes, the builder may start with a build plan that cites the PRD's
  requirement ids, and the reviewer checks the `path:line` targets still hold.

## Copy rules

Title case headings, sentence case prose, plain words, short sentences, no em dashes.
