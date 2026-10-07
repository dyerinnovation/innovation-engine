# <Release Item>: PRD

- **Owner:** <name or role>
- **Status:** draft
- **Release:** <version on the ladder, e.g. 0.7.0>
- **Updated:** <YYYY-MM-DD>
- **Code read at:** <repo> <short sha>; <repo> <short sha>
- **Parent docs:** <vision doc>, <master PRD and decision ledger>
- **Source:** <spike or research doc this synthesizes, or "none">
- **Credential path and acting identity:** <only for releases that touch an outside platform: how the credential is obtained (stored token or minted per call) and whose identity the platform sees>

> <One sentence: what this release does for the user.>

## The Flow

<One diagram: a flow for simple features, a state diagram for anything with a lifecycle.
For a lifecycle, list one screen or mockup per state under the diagram.>

| State | Screen | Entered when | Leaves when |
|---|---|---|---|
| | | | |

## At a Glance

- **What changes:** <one line>
- **What the user does:** <one line>
- **How we judge it:** <one line>

## Code Read

What exists today, read before any requirement was written.

| Kind | Item | Where |
|---|---|---|
| Entrypoint | | `path/to/file.ext:123` |
| Record | | `path/to/model.ext:45` |
| Screen | | `path/to/Screen.tsx:10` |
| Doc drift | <a doc that disagrees with the code> | `path/to/doc.md:7` |

## Decisions

Decided and open in one table. Every open row has a suggested default.

| # | Decision | Options | Suggested default | Affects | Status |
|---|---|---|---|---|---|
| D1 | | A; B | A, because <reason> | R2, AC3 | Open |

## Problem and Why Now

- <1 to 3 bullets>

## Goals

- <3 to 5 outcomes, not features>

## Non-Goals

- <what this release does not build>

## User Stories

- As a <role>, I want <X> so that <Y>.

## Requirements

| # | Requirement | Where | Bucket |
|---|---|---|---|
| R1 | <one short claim> | `path/to/file.ext:123` | isolated-code |

## Edge Cases

Enumerate these before the acceptance criteria. Each one becomes a criterion.

| Case | Handling |
|---|---|
| | |

## Acceptance Criteria

One row, one verifiable check. EARS form. Tag each with exactly one of `ci`, `rubric:<criterion-id>`, `human`.

| # | Criterion | Tag | Covered by |
|---|---|---|---|
| AC1 | When <event>, the system shall <behavior>. | ci | `tests/path::test_name` |
| AC2 | While <state>, the system shall <behavior>. | rubric:<criterion-id> | prompt `<file>`; rubric `<file>` |
| AC3 | If <error>, then the system shall <handling>. | human | release walk |

## Success Metric

- <the one number that says it worked after ship>

## Risks and Dependencies

| Risk or dependency | Level | Guard |
|---|---|---|
| | | |

## Waves

| Wave | Scope | Proves done | Size |
|---|---|---|---|
| 1 | | | |

## Tickets

- [ ] R1: <ticket link once filed>
