# Demo: feedback-triage

Everything here is invented: Northwind Notes (a fictional notes app), its teammates, and
its systems. No real companies, people, or accounts.

Scenario: it is 2026-10-02 and the user, working on Northwind Notes, pastes four things in
a row. For each paste the main session answers immediately and dispatches the filer in the
background. `pastes/` is what the user pasted; `filed/` is exactly what the filer writes
under the evidence root `docs/internal-docs/`.

| Paste | Filed as |
|---|---|
| [`pastes/01-ci-failure.txt`](pastes/01-ci-failure.txt) | [`filed/logs/10-2-26/ci-build-failure.md`](filed/logs/10-2-26/ci-build-failure.md) |
| [`pastes/02-sam-message.txt`](pastes/02-sam-message.txt) | [`filed/messages/10-2-26/sam-sync-conflict-report.md`](filed/messages/10-2-26/sam-sync-conflict-report.md) |
| [`pastes/03-product-sync-notes.txt`](pastes/03-product-sync-notes.txt) | [`filed/meeting-notes/10-2-26/product-sync.md`](filed/meeting-notes/10-2-26/product-sync.md) |
| [`pastes/04-user-feedback-email.txt`](pastes/04-user-feedback-email.txt) | [`filed/feedback/10-2-26/offline-search-feedback.md`](filed/feedback/10-2-26/offline-search-feedback.md) |

Note the date folder `10-2-26` (no leading zeros), the subject-named files, and the
back-links in each `## Related`. The email in paste 04 had an API key in its signature
block; the filer redacted it.
