# Migrating a messy docs/ folder

Goal: reach the two-sided tree without losing a file and without moving anything the owner
has not seen. Copy first, propose moves, act only on approval.

## Steps

1. **Inventory.** List every file under `docs/` (and stray doc files at the repo root, such
   as `RUNBOOK.md` or `DEPLOY.md`). Skip dependency and build folders.

   ```bash
   find docs . -maxdepth 1 -name '*.md' -print 2>/dev/null
   find docs -type f \( -name '*.md' -o -name '*.html' -o -name '*.txt' \) | sort
   ```

2. **Classify each file** with the who-reads-it rule: internal, external, split, or stale.
   Note its likely sources (the code it describes) by searching for the names it mentions.

3. **Propose in one table**, and stop for approval:

   | # | Current path | Reader | Proposed path | Sources found | Action |
   |---|---|---|---|---|---|
   | 1 | `docs/deploy.md` | team | `docs/internal-docs/runbooks/deploy.md` | `deploy/`, `.ci.yml` | copy |
   | 2 | `docs/faq.md` | users + team | split: `external-docs/help/faq.md` + `internal-docs/runbooks/support.md` | `src/billing/` | split |
   | 3 | `docs/old-api.md` | users | none | no matching code | flag stale |

   Actions are only: copy, split, flag stale, leave. Never "delete".

4. **Apply approved rows by copying.** Use `cp` (or `git mv` only when the owner approved a
   move for that row). Add the frontmatter to each copy, with `sources` from step 2 and
   `last-verified` left empty until the writer re-reads them.

5. **Leave a pointer in each original** that was copied, as its first line:
   `Moved to docs/internal-docs/runbooks/deploy.md. This copy is kept until the owner removes it.`

6. **Fix links** inside the new tree. Report links that pointed at files with no new home.

7. **Hand back a removal list**: originals that now have a pointer. The owner removes them
   when ready; the skill never does.

## Things that often turn up

- Secrets pasted into old docs. Do not copy the value; point to the secret's row in
  `environments.md` (an alias on the existing row if code already names it, a new row
  only for a distinct secret) and tell the owner the original still holds it.
- Hosts and endpoints scattered across many files. Move them into `environments.md` once
  and replace each mention with a pointer to the row.
- Post-mortems under `docs/post-mortems/`. Copy them into `docs/internal-docs/post-mortems/`
  and point the session-post-mortem skill at the new folder.
