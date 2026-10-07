# Contributing

Issues and pull requests are welcome.

- Keep each `SKILL.md` short, with a `name` and a description full of the phrases people
  actually say.
- Keep skills product-neutral: no company, product or personal names, no absolute home
  paths, no emails, no internal links.
- Name model classes (strongest, mid-tier, small), not specific models, unless as an
  example.
- Plain words, no em dashes, no italics.
- Before opening a pull request, run:

```
claude plugin validate .
scripts/scrub-gate.sh
gitleaks detect --source . --no-git --redact
bash plugins/swe/skills/session-post-mortem/hooks/test-detect-compaction.sh
```
