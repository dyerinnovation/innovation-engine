---
name: test-strategy
description: Decide which tests a change needs and what must pass before merge. Picks layers per change (unit, integration, end to end, evals for LLM output, a human walk), maps acceptance criteria to the test that proves each one, sets the pre-merge and post-merge gates, and handles flaky tests without hiding real bugs. Use when asked "how should we test this", "what tests do we need", "test plan", "test strategy", "is this covered", "what do I run before merging", "this test is flaky", "set up evals", "grade LLM output", or when a PRD's acceptance criteria need a covering test.
---

# Test Strategy

The goal is not coverage for its own sake. It is that every promise a change makes has
one named thing that would fail if the promise broke, and that the cheap checks run first.
Use this before writing code for a change, and again before merge.

## Step 1: Classify the change

Read the diff or the plan, then name every class that applies:

| Change | Typical risk |
|---|---|
| Pure logic (parsing, pricing, state rules) | Wrong answer on an edge case |
| Data layer (schema, migration, query) | Bad migration, slow or wrong query, lost data |
| API or tool contract (route, MCP tool, event shape) | Producer and consumer disagree on the wire |
| UI (screen, component, copy) | Layout, state or theme drift a build cannot see |
| Integration with an outside service | Auth, timeouts, rate limits, changed responses |
| LLM-backed behavior (prompt, agent, grader) | Quality drift that no assertion catches |
| Infra or deploy (config, chart, pipeline) | Starts in CI, fails at runtime |

## Step 2: Pick the layers

Choose the cheapest layer that can actually catch each risk. Add a layer only when the one
below cannot see the failure.

| Layer | Use it for | Notes |
|---|---|---|
| Unit | Logic, validation, error branches | Fast, no network. Most tests live here. |
| Integration | Data layer, API contracts, the real database or queue | Use throwaway records and clean up in a finally block. |
| Construction smoke | Any new service, server or worker | Build the real app object in CI. Mocked units do not catch a crash at startup or a broken lazy import. |
| Contract | One side produces a shape another side consumes | Assert the serialized response end to end (route, schema, client type), not each side alone. |
| End to end | A few critical user paths | Keep the set small; these are the slowest and flakiest. |
| Eval | LLM output quality | See Step 4. |
| Human walk | Visual polish, judgment calls, anything a person must see | Use the ui-test-walk skill. |

Rules of thumb:

- Every bug fix starts with a test that fails before the fix and passes after.
- Every new error branch gets a test that drives it.
- Migrations get a forward test and a rollback or a written "forward only" note.
- If a UI change ships, a typecheck and build passing is not evidence it looks right.

## Step 3: Map acceptance criteria to tests

Each acceptance criterion gets exactly one tag:

- `ci`: an automated test or scripted probe proves it. Name the test (`path::test_name`).
- `rubric`: a blocking criterion in an evaluation rubric proves it. Name the criterion.
- `human`: it needs a person in a walk. Phrase it as something a person can see.

If you cannot name the covering test, the criterion is not covered. Tag it `human` or write
the test; never mark it automated on faith.

## Step 4: Evals for LLM output

LLM behavior needs graded runs, not exact-match asserts.

- **Rule in both halves.** A quality rule is landed only when it is in the prompt (so the
  model does it right the first time) and in a blocking rubric criterion (so the grader
  catches a miss). Prompt only is unenforced; rubric only burns revision cycles.
- **The grader must see what it grades.** If a criterion is about every frame, every step
  or every citation, the grader's input has to include all of them.
- **Ground on real material.** Run evals against real, human-made reference inputs and
  compare against human-made ground truth where you have it, not only against synthetic
  prompts.
- **Use fresh inputs.** For tasks that research or summarize, pick topics newer than the
  model's training data, or the run proves recall rather than the pipeline. Do not reuse a
  topic across eval runs.
- **Keep runs small.** Short inputs bound cost while you test plumbing. Scale up only to
  judge quality.
- **Prefer one review pass.** Repeated self-review loops often add defects (a fixer that
  invents a fact, a rewrite that lengthens sentences). Measure before adding passes.
- **Compare to a baseline.** Record finding counts, cost and wall time per run so a prompt
  change can be judged against the last one.
- **Write a short report per run**: what was tested, results per scenario, bugs found (write
  "none found" explicitly when clean), open decisions, next action. Summarize; do not paste
  raw logs.

Choose the grader model by class: the strongest model for subtle judgment, a mid-tier model
for routine rubric checks, a small model only for format checks.

## Step 5: Gates

**Before merge** (every change):

1. Lint and typecheck.
2. Unit tests for the touched packages.
3. Integration and contract tests for touched boundaries.
4. Construction smoke for any touched service.
5. Evals for changed prompts, agents or graders, at small size.
6. For UI changes, a screenshot check at phone and desktop width (ui-test-walk).

**After merge** (CI or a scheduled job):

- The full suite, end to end tests, tests that need shared live infrastructure, and full
  size evals.
- Verify the deploy actually rolled out: the running version matches the merged commit.

**Before a release**: every `human` criterion walked, every `ci` and `rubric` criterion
green on the release commit.

## Step 6: Flaky tests

A flaky test is a test whose result changes with no code change. Treat it as a bug in the
test or the system, never as weather.

1. **Check it is really flaky.** If it fails the same way every time, it is a systematic
   failure, not a flake. Find the mechanism.
2. **Find the mechanism before the mitigation.** If the fix is a retry, a longer timeout or
   a fallback, write one sentence naming what it compensates for. If you cannot, you have
   not found the bug. Common causes: shared state between tests, ordering, real clocks,
   unawaited async work, network calls, and test data left behind by an earlier run.
3. **Quarantine with a ticket, not a skip.** Move it to a quarantined set that still runs
   and reports, open a tracked issue naming the suspected cause, and set a date to fix or
   delete it.
4. **Never retry to green silently.** An automatic rerun that hides a failure turns a real
   race into a release surprise. If CI retries, it must report that it did.
5. **A release candidate that fails on a flaky test is not shipped.** Fix or quarantine,
   then cut a new candidate.

## Test data hygiene

- Integration tests create their own records and remove them in a finally block.
- Never point bulk deletes or test runs at production. Make the tooling refuse it.
- A human walk starts from a known slate: clear leftovers that are not part of the
  scenario, then seed exactly what the scenario needs and say what was seeded.

## Output

When asked for a test plan, return a short table: risk, layer, test name or file, gate
(pre-merge, post-merge, release), and tag (`ci`, `rubric`, `human`). Flag any criterion with
no covering test.
