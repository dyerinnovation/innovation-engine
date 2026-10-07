---
name: human-actions
description: Keep one tracked list of the actions only a person can perform (browser or OAuth consent clicks, app installs, DNS changes, approvals, live test walks, recordings, purchases, credential handoffs, decisions). Add an item the moment work needs a person's hands, complete it with evidence, cancel it with a reason, never delete. The backend is generic (an issue label, a tracker label, or a database-backed page). Triggers on "human action", "add to my checklist", "what needs me", "action checklist", "blocked on the owner", "needs a person", or "/human-actions".
---

# Human actions

Some steps only a person can do. Each project keeps exactly one list of them, and that
list is the only place such a step lives. The method below is the same everywhere; where
the list lives and how to write to it goes in a profile copied from `profiles/_template.md`.

## Pick one backend per project

| Backend | How an item looks |
|---|---|
| GitHub issues | An issue with the label `human-action` |
| Your issue tracker | An issue with a `human-action` label, in the project's team or board |
| A database-backed page | A private page with a `db` collection `actions` and a checkbox per item |

Pick one before the first item, record it in the profile, and get the owner's yes on it.

## When to add an item

Add it the moment a task needs a person's hands, not at the end of the session:

- auth clicks: OAuth consent, app installs, signing in to a third-party console
- approvals: merge or release gates, a product decision, a spend
- recordings and live walks: voice, video, a test walk in a real browser or device
- purchases and account settings
- credential handoffs: a key or secret that a person must create or paste
- decisions only the owner can make

If an agent could do it with the tools it has, it is agent work, not a human action.

## Item format

- **Title**: short, Title Case, starts with a verb ("Approve DNS Record For The Docs Site").
- **tldr**: one sentence on what and why. Pages show it uncollapsed; a second sentence
  becomes a wall of text.
- **Steps**: a numbered list, one action per number, self-contained: exact URLs, exact
  button and menu names, exact values to paste (never secrets). No "see chat" references.
- **Done when**: a final line stating the observable result ("Done when: the record
  resolves and the health check is green").
- **One action per item.** A multi-part errand is several items.
- **Order**: gate blockers first, using the backend's ordering field.

## Lifecycle

1. **Add** (status todo or open).
2. **Done** with evidence: a comment or note saying what proved it ("Done: dig shows the
   CNAME"). Either side may mark it done; the owner's checkbox counts.
3. **Canceled with a reason** when it becomes obsolete. Say why, and mention it in chat.
4. **Never delete.** Done and canceled items are the audit trail.

## Session start

At the start of a working session, list the open items (profile: **List**). If an item
you are about to work around is still open, say so. If you can verify an item is already
done (the record resolves, the app is installed), mark it done with that evidence.

## Reporting rule

- Whenever you add, complete or cancel an item, tell the person in chat that the list
  changed and give the page or list link (profile: **Page**).
- Never leave a blocking step only in chat. A chat message is a pointer to the item,
  never the item.

## Copy rules

- No italics, no em dashes, no emoji, no exclamation points.
- Plain words; spell out acronyms on first use.
- No secrets in any field: name where the secret lives, never its value.

## No parallel lists

Each project has exactly one backend. Do not mirror items into JSON files, a second
tracker, task lists or a second page. A page is a view of the backend, never a second
copy. To change backend, migrate every item (open and closed) in one pass and retire the
old one in the same change.
