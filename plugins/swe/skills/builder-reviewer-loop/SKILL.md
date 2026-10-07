---
name: builder-reviewer-loop
description: Run any non-trivial change as a builder agent plus an independent reviewer agent, with a visual check switched on whenever the change has a UI. The reviewer re-runs the checks itself and, for UI work, takes its own screenshots and compares them to the design. Triggers on "builder reviewer", "build and review", "review loop", "visual validation", "UI port", "check it matches the design", or planning a wave of changes where passing tests alone is not enough evidence.
---

# Builder and reviewer loop

A builder makes the change; a second agent, with a fresh context, decides whether it is
right. The builder has every reason to believe its own work; the reviewer's independence
is the whole value. For anything with a screen, passing tests is not proof, so the
reviewer also looks.

Pick each agent's model with `agent-model-routing`: the reviewer always gets the strongest
class; the builder gets mid-tier on a concrete edit list, strongest on a design-heavy brief.

## When to use

- Any change bigger than a one- or two-file fix, especially across several files or services.
- UI work: porting a design into code, new screens, anything where layout, color or type can drift.
- Work with written anti-patterns (a brand guide, a style guide, an architecture rule) that a
  code-only review could miss.

Skip it for tiny targeted fixes and for throwaway scripts.

## The loop

1. **Builder**: brief it with the goal, the inputs (plan, design, guides), numbered
   deliverables, what not to touch, and the checks to run (tests, lint, build). For UI work,
   add the routes or screens to screenshot at phone and desktop width.
2. **Reviewer**: a separate agent with the same plan and inputs, the builder's report, and
   the builder's judgment calls copied in verbatim. It re-runs the checks itself, reads the
   diff against the plan, and for UI work takes its **own** screenshots of the same screens
   and compares them side by side with the design. It never edits code.
3. **Verdict**: `pass`, `needs-changes` or `escalate`, with a one-line summary and issues by
   severity (blocking, warning, suggestion).
   - `pass`: done, move on.
   - `needs-changes`: a fix-up builder gets the blocking issues. At most two fix rounds.
   - `escalate`: a third failure, or a problem the builder cannot fix: hand it to the person.

Warnings and suggestions do not trigger a fix round; carry them into the next brief that
touches the same area.

## Visual check, when there is a UI

- Start the app once, in the background, and wait until it answers before anyone navigates.
- Screenshot every changed screen at phone width (about 390 px) and desktop width (about
  1440 px), in light and dark themes if the product has both.
- Save screenshots to files so the reviewer can find the builder's set and compare its own.
- Browser extension popups in screenshots are noise, not drift.

## Anti-patterns

- Skipping the reviewer because the builder "looked thorough".
- A reviewer that trusts the builder's screenshots instead of taking its own.
- Leaving a guide's anti-patterns out of either brief: put them in both, word for word.
- Letting a third silent fix round happen: count rounds, escalate on the third.
