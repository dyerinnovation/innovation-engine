---
name: release-ladder
description: Plan and run releases as a ladder of numbered rungs, each one proven milestone, tracked in any issue tracker (GitHub, Linear, Jira) with one project per release, a gate ticket, park and hard-cut labels, an optional narrative mirror that is never a second tracker, and a release hub whose statuses need evidence. Also audits the ladder against reality (tags, deployed versions, live data) and covers cutting and rolling back a release. Use when asked to "plan releases", "set up the release ladder", "what is shipped", "is the ladder right", "update the release hub", "cut a release", "tag a release candidate", "what release does this belong to", "release review", or when organizing a backlog into releases.
---

# Release Ladder

A release ladder answers three questions at a glance: what is each release, what is
actually running, and what is next. It rots quietly. A release passes its acceptance walk
and stays marked "in flight" for days; a rendered copy disagrees with its source. This skill
sets the ladder up so the truth lives in one place, and audits it on purpose.

## Versioning

- Each release (a rung) is one proven milestone with one item in it: one feature, one
  agent, one integration. Two items means two rungs.
- Before general availability, use a visible pre-release prefix, for example `rc-0.X.0`,
  so nobody mistakes a candidate for a GA build in logs or deploy names.
- `rc-0.X.0`: a rung's gate passed.
- `rc-0.X.Y` (Y of 1 or more): a refinement of rung X's item only: fixes, or a model or
  dependency upgrade behind the same feature. Never a bundle of new capabilities.
- `v1.0.0` and later: standard semantic versioning after general availability.
- Version numbers are identity, not priority. Never renumber a decided rung to change its
  order. Add a point release instead, and express order in a focus column.
- Frozen history stays frozen. A retired numbering series is kept, never deleted.

## Tracker layout (works in GitHub, Linear or Jira)

| Concept | GitHub | Linear | Jira |
|---|---|---|---|
| One container per release | Milestone or Project | Project | Fix version or Epic |
| The gate | Issue labeled `release-review` | Issue labeled `release-review` | Issue labeled `release-review` |
| No release home yet | Label `park` | Label `park` | Label `park` |
| Cancelled by a product decision | Label `hard-cut`, closed | Label `hard-cut`, cancelled | Label `hard-cut`, won't do |

Rules:

- Every open work item belongs to exactly one release container, or carries `park`.
- Each release has exactly one gate ticket. It closes when the release review passes, and
  it links the walk record and the tag.
- `hard-cut` items keep a one-line reason and the decision that cut them.
- Retire old labels (for example a one-off "demo blocker") rather than reusing them. Keep
  them read-only for history and never apply them to new items.

## The narrative mirror (optional)

A wiki or docs page per release can tell the story: what it is for, the PRD, the review,
the tag. It links to the tracker container and never holds its own task list or statuses.
If people start tracking work there, it has become a second tracker; move the items back.

## The release hub

One page, kept in the repo, that indexes the ladder:

| Release | Focus | Item | Status | Live evidence | PRD | Notes |
|---|---|---|---|---|---|---|
| rc-0.7.0 | Now | Saved searches | In flight | dev at `abc1234`; untagged | link | |

- **Focus**: Now, Next, Later, or done. This is where order lives.
- **Status**: Planned, In flight, Shipped.
- **Live evidence**: what proves the status: a tag, a queried deploy version, a record in
  the live system, a walk record.
- Keep a **Known gaps** section under the table for anything you cannot fix right now:
  untagged rungs, missing PRDs, links that break on a clean clone.

The master PRD owns the ladder and the decision ledger; the hub is an index over it. If both
carry a status column, checking they agree is part of every audit.

## Evidence standard

A release is Shipped only with evidence you can point at, never because someone remembers
it shipped. Record the evidence in the Live evidence cell or a decision ledger entry.

Update the hub in the same change that causes a status change: a rung moves state, is added
or split, gets a PRD, a ledger entry lands, the deployed version changes, or focus changes.

## Audit procedure

Run it when picking up release work, when a rung finishes, and before a release review.

1. **Read the claims**: the ladder in the master PRD, the hub table and focus, the known
   gaps, and the actual PRD folder (the folder is the truth for which PRDs exist).
2. **Check reality, do not recall it**: list tags (`git tag -l 'rc-*' | sort -V`), query
   what is deployed per service and environment, check rendered docs are in step with their
   source, and for rungs proven by data, query the live system read-only.
3. **Report every disagreement**:

| Symptom | Usually means |
|---|---|
| Shipped, no tag | Real work, missing release hygiene. Record it; tagging is a separate decision. |
| In flight, evidence says done | The record lagged. Update with a ledger entry naming the evidence. |
| Shipped, no evidence found | The dangerous one. Do not assume. Report that it could not be confirmed. |
| PRD link with no file | Fix the link. |
| Focus names a finished rung | Rewrite focus. |

4. **Update**: fix both ladders, mark Shipped only with evidence, move what you cannot fix
   into Known gaps. Never delete a gap because it is inconvenient; it leaves when fixed.
5. **Do not cut tags during an audit**. Report missing ones and let a person choose the
   commit.

## Cutting a release

Pre-flight:

- [ ] The gate ticket's release review passed (every `human` criterion walked).
- [ ] CI is green on the exact commit to tag, including `ci` and `rubric` criteria.
- [ ] The candidate has soaked in the pre-production environment, or a shorter soak is
      explicitly accepted.
- [ ] Migrations are forward compatible, or a rollback is tested.
- [ ] Error rates and alerts in pre-production are quiet.
- [ ] Clients handle both old and new API shapes if a breaking change shipped.

Then tag the main branch, never a feature branch, with an annotated tag:

```bash
git checkout main && git pull
git tag -a rc-0.7.0 -m "rc-0.7.0: saved searches"
git push origin rc-0.7.0
```

Tags are immutable. If a candidate fails after tagging (a flaky test, a bad deploy), fix it
and cut `rc-0.7.1` or a suffixed candidate; never delete and recreate a pushed tag.

Rollback is a traffic shift to the previous version or a new patch tag pointing at a known
good commit. Write the rollback trigger down before the cut, not during the incident.

After the cut: close the gate ticket with the tag and walk record, update the hub's status
and evidence, and update the narrative mirror if you keep one.
