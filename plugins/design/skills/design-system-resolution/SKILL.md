---
name: design-system-resolution
description: Step 0 of every visual skill. Decide which design system a page, board, deck, diagram or report should use, then hand back one small resolved-theme contract (light and dark color tokens, type stacks, spacing and radius, logo, and where each came from). Order is the system the user names, then the project's own tokens, theme file, design-system page or brand skill, then the neutral engine default theme. Triggers on "which design system", "use our brand", "theme this", "match our styles", "use our colors", "make it look like our app", "what theme should this use", or at the start of any skill that produces a visual page.
---

# Design system resolution

Every visual skill starts here, so styling is decided once, the same way, and in one
place. The output is a resolved-theme contract (`references/theme-contract.md`) that the
calling skill maps into its own template.

## The order

Stop at the first rung that gives an answer.

1. **The system the user names.** "Use our brand", "match the docs site", "theme it like
   the app", a path, a page link or a brand skill by name. Use exactly that.
2. **The project's own system.** Search the working project for:
   - tokens or theme files: `tokens.json`, `tokens.css`, `theme.css`, `theme.ts`,
     `design-tokens.*`, a `theme` block in a Tailwind config, a `:root` block of CSS custom
     properties in the main stylesheet
   - a design-system page or published artifact the project links to
   - a brand skill made with `brand-design-system` (a `design-systems/<slug>/` folder or
     a `.claude/skills/<slug>-design-system/` skill)
   - a logo file the project owns (`logo.svg`, `assets/brand/`), recorded as `logo`
3. **The engine default theme.** `references/default-theme.css`: neutral, accessible,
   light and dark, brand-neutral.

## Ask or not

- **One clear answer: do not ask.** Say in one line which system you used, for example
  "Theme: project tokens from `web/src/theme.css` (dark filled from the default)."
- **Two or more candidates on the same rung: ask once**, listing each with its path, and
  recommend the one closest to the thing being made (the app's own theme for an app page).
- **Another company's brand that is not on file: ask once** whether to extract it with
  `brand-design-system` first or to use the default theme for now. Never guess a
  third-party palette from memory.
- **Nothing found: use the default** and say so in the same one line.

## Procedure

1. Check the request and recent messages for a named system (rung 1).
2. If none, search the project (rung 2). Prune heavy folders (`node_modules`, `.venv`,
   build output) from the search.
3. Read the winning source and fill the contract: colors for light and dark, fills that
   carry white text, type stacks with fallbacks, spacing, radius, logo, provenance.
4. Fill every missing group from the default theme and list it in `gaps`.
5. Check contrast: text tokens at 4.5:1 on every ground in their theme, white text only
   on fills that reach 4.5:1. If a source token fails, darken or lighten it, keep the
   hue, and note the change in provenance.
6. Return the contract and the one-line notice to the calling skill.

## Rules

- Never reproduce or redraw a logo you do not own. `logo` is the project's own file or
  `null`.
- No CDN fonts and no `@font-face` in the contract; stacks only.
- Resolve once per artifact. A later update to the same page reuses the same system unless
  the user asks for a change.
- Do not edit the project's source files; the contract is read-only output.

## Inline fallback for other plugins

Skills in other plugins must not hard-depend on this one. Each carries a short Step 0:

```
## Step 0: Resolve the design system
If the design plugin is installed, run `design-system-resolution`. Otherwise: use the
system the user names; else the project's own (a tokens or theme file, a design-system
page, a brand skill); else the neutral default theme in this skill's template. Say in one
line which one you used, and ask only when two or more are found.
```

A skill with no template of its own ends the fallback with "else plain neutral styling".

## Where this lives

This skill sits in the design plugin because it is about styling. If three or more
cross-cutting skills like it pile up across plugins, revisit a shared utilities plugin.
