---
name: architecture-diagrams
description: Create, name, update and export architecture diagrams in draw.io or Mermaid, keeping a current-state diagram and a target-state diagram side by side during a migration, with the original kept as a suffixed reference, all in one folder. Covers per-environment diagrams, per-release flow diagrams, what every diagram must show, when a change must update a diagram, and exporting SVGs that stay legible in dark mode. Use when asked to "draw the architecture", "update the architecture diagram", "diagram this flow", "current vs target architecture", "migration diagram", "export the drawio", "mermaid diagram of", or when a change adds a service, boundary, data flow or environment.
---

# Architecture Diagrams

Diagrams are worth keeping only if they are true and findable. This convention keeps every
diagram in one folder, makes it obvious which picture is today and which is the plan, and
ties updates to the changes that make them stale.

## Pick the tool

| Use | When |
|---|---|
| Mermaid | Flows, sequences and state diagrams that live inside markdown docs and PRDs. Diffable, renders on most code hosts, no export step. |
| draw.io (`.drawio`) | Deployment and infrastructure views with boundaries, many nodes, or precise layout. Export an SVG beside each source. |

Do not maintain the same diagram in both. Pick one per diagram.

## One folder

All architecture diagrams live in one folder, for example `docs/architecture/`. Subfolders
are allowed for a family of related flows (`docs/architecture/onboarding-flows/`). Source
and export sit together: `prod.drawio` and `prod.svg`. Commit both.

## Naming

| Kind | Pattern | Example |
|---|---|---|
| Environment view | `<env>.drawio` | `dev.drawio`, `staging.drawio`, `prod.drawio` |
| Release or feature flow | `<release>-<slug>-<view>` | `rc-0.7.0-saved-search-write-path.drawio` |
| Pre-migration reference | `<name>-<old-approach>` | `prod-custom-relay.drawio` |
| Decision record diagram | `<adr-number>-<slug>` | `0009-reviewer-pipeline.drawio` |

Lowercase, hyphens, no dates in the name (git has the dates), no "final" or "v2".

## Current vs target during a migration

When you replace a significant piece (a messaging layer, a hosting platform, a media
server):

1. Copy each affected diagram to `<name>-<old-approach>` before editing. That copy is the
   frozen reference of how things worked before. Never edit it again.
2. The unsuffixed file becomes the target architecture. Edit it to show the new design.
3. Add a short migration notes file in the folder: one row per diagram with the
   environment, its status (needs update, updated, reference only), and exactly what to
   add or change in each.
4. When the migration ships, the unsuffixed diagram is simply "current". Keep the suffixed
   references as long as the old approach might be revived or explained; delete them in a
   deliberate change, not as cleanup.

If you keep the old implementation on a branch as a fallback, name the branch after the
same suffix so the diagram and the code point at each other.

## What every diagram shows

- One question per diagram: "how does a request reach the database in prod", not
  everything at once. Use levels: system context, then containers (services, stores,
  queues), then components inside one container only when needed.
- Boundaries drawn as boxes: environment, network, cloud account or project, trust zone.
  What sits outside a boundary matters as much as what sits inside.
- Every arrow labeled with what flows and how (protocol, port, sync or async), with a
  direction.
- External parties (third-party APIs, identity providers, clients) visually distinct from
  your own services.
- A title, the environment, and a legend if you use colors or line styles.
- Readable when the SVG is scaled to a phone width: few crossing lines, text no smaller than
  the body text of the doc that embeds it.

## When to update

In the same change as the code or infrastructure change, not as a follow-up, when you:

- add, remove or rename a service, store, queue or external dependency
- change how two components talk (protocol, sync to async, direct to brokered)
- add an environment or change what runs where
- move a trust boundary (new public endpoint, new credential path)

A reviewer who sees one of these in a diff without a diagram change should ask for it.

Release PRDs get their own flow diagram (`<release>-<slug>-<view>`), and the environment
views are updated when that release ships.

## Exporting draw.io

Use `scripts/export-drawio.sh` from the diagrams folder. It exports each `.drawio` to an SVG
beside it and pins the SVG to a light canvas. Without the pin, draw.io's export flips only
the background in a dark-mode browser and leaves light fills, which gives white text on
white boxes. If the embedding page supports dark mode, keep the diagram on a light card
rather than inverting it.

After exporting, open the SVG at desktop width and at 390 px wide and check labels are
readable.

## Mermaid tips

- Keep node ids short and labels in quotes: `api["API service"] -->|HTTPS| db[("Postgres")]`.
- Use `stateDiagram-v2` for lifecycles and pair it with a table of the screen for each state.
- Use `sequenceDiagram` for request flows that cross more than two services.
- Let the renderer pick colors so the diagram follows the page's light or dark theme.
