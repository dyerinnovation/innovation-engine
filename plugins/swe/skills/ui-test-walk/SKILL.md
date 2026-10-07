---
name: ui-test-walk
description: Walk a UI change in a real browser, by a person or an agent, and produce a findings report. Writes click-through steps with expected results, runs them at phone width (390 px) and desktop width (1440 px) in light and dark themes, captures screenshots, checks acceptance criteria, and reports findings by severity. Use when asked for a "UI walk", "UAT", "acceptance walk", "release walk", "walk this change", "visual check", "screenshot check", "check it on mobile", "check dark mode", "critic visual pass", or before merging or releasing any user-visible change.
---

# UI Test Walk

A build that compiles says nothing about whether a screen looks right, reads right on a
phone, or survives dark mode. A walk is the check that does: someone opens the real app in a
real browser and follows written steps, comparing what they see to what the steps say they
should see.

## Who walks

- **Agent walk**: a browser-driving agent follows the steps and screenshots each check. Use
  it on every UI change before merge.
- **Person walk**: a person follows the same steps for judgment calls (feel, copy, polish)
  and for release gates.
- **Independence**: the walker should not be the builder. A builder sees what they meant to
  build. If an agent built the change, a separate agent with its own context walks it and
  takes its own screenshots rather than reusing the builder's. Use the strongest model class
  for this critic role; visual drift is easy to miss.

## Step 1: Write the steps

Each step is a reproduction step someone could follow cold, with three parts:

1. **Start**: where you are (the URL or screen, signed in as which test user, with what data).
2. **Action**: one click, one keystroke sequence, or one navigation.
3. **Expected**: what you should observe, concrete enough to be wrong (a label, a count, a
   toast, a state change), not "it works".

Rules:

- One action or one check per step. No run-on steps joined by arrows or semicolons.
- Write in user language ("click Save"), not code language ("the handler fires").
- Every step stands alone. It travels with any issue filed from it, so never write "see the
  ticket for steps".
- Cover the empty state, the loading state, an error state and a long-content state, not
  only the happy path.
- For a feature both a person and an agent touch, prove each side sees the other's writes.
- Keep steps in sync with the code. A change that renames a label, route or flow updates the
  steps in the same change. A stale step produces a fail that is a doc bug, not a regression.

## Step 2: Prepare the environment

- Use the deploy that matches the commit under test and write that commit in the report.
- Start from a known slate: remove leftover records that are not part of the scenario, then
  seed exactly what the walk needs and list what was seeded.
- Use dedicated test accounts. Never walk on production data.
- If you start a local server for the walk, stop it when the walk ends.

## Step 3: Walk the matrix

Run every step in each cell the change could affect:

| | Light | Dark |
|---|---|---|
| Phone, 390 px wide | required | required |
| Desktop, 1440 px wide | required | required |

At each cell check:

- No horizontal scroll at 390 px; tap targets usable; text not clipped or overlapping.
- Contrast holds in both themes; no white text on white, no invisible borders or icons.
- Images, diagrams and embedded content adapt or stay legible in dark mode.
- Keyboard focus is visible and the tab order is sensible on desktop.
- The browser console is free of new errors.

Screenshot each check that has a visual expectation, named
`<step-id>-<width>-<theme>.png`. Browser extension popups and password managers in a
screenshot are noise, not findings.

## Step 4: Record results

For each step: pass, fail, or not run, plus a note on a fail saying what you saw instead.
For each acceptance criterion in the plan or PRD:

- `human` criteria are checked by the walker.
- `ci` and `rubric` criteria are shown with the name of the test or rubric item that covers
  them, and are not the walker's job.

If the walk is recorded in a tool (a board, a form, a tracker), confirm the results actually
reached it before closing the walk. A walk that looks finished on screen but never saved is
indistinguishable from no walk.

## Step 5: Findings report

Write one finding per problem:

| Field | Content |
|---|---|
| Title | What is wrong, in a few words |
| Severity | See below |
| Where | Screen, width, theme |
| Steps | The failing step, copied in full |
| Expected | From the step |
| Actual | What happened |
| Evidence | Screenshot file names, console errors |

Severity is what the failure costs a user, not the order to fix things in:

| Severity | Meaning |
|---|---|
| Blocker | The path cannot be completed, data is lost or exposed, or a gate fails |
| High | The path completes but is wrong or misleading for many users |
| Medium | A visible defect with a workaround, or a single cell of the matrix broken |
| Low | Polish: spacing, copy, minor alignment |

Report header: change under test, commit, environment, test users, date, counts of pass,
fail and not run, and the verdict:

- **Pass**: no blocker or high findings.
- **Needs changes**: one or more blocker or high findings. Hand the findings to a fix round
  with the failing steps attached. Cap fix rounds at two, then escalate to a person.
- **Escalate**: the fix needs a product decision.

File medium and above as tracked issues with the full steps. Medium and low findings do not
block a merge on their own; carry them into the next change that touches the same screen.

## Carry forward

The next walk includes every step from the last walk that failed or was never run, marked
with why it is back ("failed last walk, since fixed, re-verify"). Group carried steps by
screen, not in a separate bucket. Delete steps for behavior that no longer exists rather
than leaving them to fail.
