# Sam sync conflict report (2026-10-02)

Chat message from Sam (teammate) about lost offline edits in the beta.

## Raw

```
Sam: hey, two testers on the beta say edits made on their phone vanish after they open the laptop app. Both had been offline for a few hours. I can repro it once with airplane mode on. Not sure if it is related to the merge change from Tuesday. Can you look before Friday's build?
```

## Triage

- Meaning: possible data loss on reconnect after offline edits; matches the failing tie-break merge test.
- Owner of the next step: the user investigates; Sam collects device logs from both testers.
- Open: reproducibility (Sam saw it once), and whether Tuesday's merge change caused it. Deadline: Friday's build.

## Related

- [CI build failure](../../logs/10-2-26/ci-build-failure.md)
- [Product sync](../../meeting-notes/10-2-26/product-sync.md)
