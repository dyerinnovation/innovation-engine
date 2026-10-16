---
name: brand-design-system
description: Extract any brand (a client's, a partner's, or your own product's) into a self-contained design-token set, a brand guide and a specimen page that any HTML document, app theme or slide can inherit. Produces tokens.css, a brand guide with anti-patterns, and preview.html, with every color and typeface cited to a source. Triggers on "extract a design system", "brand tokens for <brand>", "make a <brand> design system", "match <brand>'s look", "theme this like <brand>", or "document our brand".
---

# Brand design system

A repeatable procedure: point it at a brand, get back a faithful, self-contained styling
reference. The goal is to evoke the brand through palette, type, layout and voice, never
by reproducing a trademarked logo.

## When run as an agent

If you were handed one brand to extract, do the research and write all three files
yourself. Any review of the result is the caller's job.

## Output contract (exactly three files per brand)

Write to `design-systems/<slug>/` (or a folder the user names), where `<slug>` is
lowercase kebab-case. Start from the skeletons in `template/`.

| File | Must contain |
|---|---|
| `tokens.css` | One `:root { }` block of CSS custom properties: the palette (backgrounds, ink, accent, optional data accents), type stacks (real brand faces first, then free, widely installed fallbacks; no CDN), a type scale, a spacing scale, radii, and semantic aliases (`--color-bg`, `--color-surface`, `--color-rule`, `--color-text`, `--color-text-muted`, `--color-accent`, `--font-display`, `--font-body`). A header comment cites the sources and the check date. |
| `SKILL.md` | The brand guide, from `template/brand-guide-template.md`: frontmatter with name, description and triggers, then 1. Color tokens (hex, rgb, when to use, an accent rationing rule), 2. Type system, 3. Layout and spacing, 4. Voice and tone, 5. Brand anti-patterns (a numbered list a reviewer can apply word for word), 6. Logo and wordmark usage (evoke, never reproduce), 7. How to apply, and Sources (cited URLs and date, with anything approximated flagged). |
| `preview.html` | A self-contained specimen: color swatches with hex labels, the type scale in the brand stacks, and a sample card with a heading, body text, a chip, a link and a primary button, all styled with `var(--...)` tokens. |

Copy the folder to `.claude/skills/<slug>-design-system/` to use the guide as a skill.

## The project's own brand skill

Output from this skill is what `design-system-resolution` looks for as "the project's own
brand skill" (rung 2 of its order), in `design-systems/<slug>/` or
`.claude/skills/<slug>-design-system/`. To make that hand-off clean:

- Keep the semantic aliases in `tokens.css` exactly as named in the template; resolution
  maps them straight into its theme contract (`--color-accent-strong` becomes the fill for
  white text).
- Add a dark block (`@media (prefers-color-scheme: dark)` with the same alias names) when
  the brand has dark values. Without one, resolution fills dark from the engine default
  theme and says so.
- Name the logo file path in section 6 of the guide when it is your own mark, so
  resolution can pass it on. Leave it out for any brand you do not own.
- If a project holds several brands, keep the `design-systems/README.md` index current and
  mark the default one, so resolution does not have to ask.

## Procedure

1. **Research the public brand, official sources first.**
   - The brand's own brand, press-kit, newsroom or design-system pages (authoritative hex
     values and typefaces).
   - The live computed CSS of the brand's main site as a cross-check of the real palette
     and font stacks (`getComputedStyle` on body, headings, links and buttons in a browser,
     or the site's CSS files).
   - Reputable secondary sources (type foundry "in use" pages, agency case studies) for
     typeface identification.
   - For your own product, the codebase theme or tokens file is the primary source.
2. **Extract the palette.** Capture the true backgrounds, the primary text color, and the
   one or two accents, each with hex, rgb and a "when to use" note. Note whether the brand
   grounds on pure white or black or on a tint. Ration accents: most brands have one hero
   color; secondary hues are for data only.
3. **Extract the type system.** Identify the real display and body faces. The files stay
   self-contained (no CDN, no `@font-face`), so each stack lists the real face first, then
   free, widely installed fallbacks in the same category (geometric sans, humanist sans,
   transitional serif, slab). Never introduce an unrelated web font as the brand face.
4. **Capture layout, voice and anti-patterns.** What makes a page read on-brand or off?
   Write the anti-patterns as blocking rules ("Never use pure white if the brand grounds
   on off-white", "Never recolor the accent", "Never reproduce the logo", "Never load CDN
   fonts").
5. **Logo.** Document the usage rules, but evoke the brand through palette, type and tone.
   Never reproduce or redraw a trademarked logo. For your own brand, reference your own
   logo files rather than redrawing them.
6. **Cite and date every source**, and flag anything approximated or inferred (a guessed
   hex, an uncertain typeface). Verified hex values are authoritative.

## Quality bar

- **Self-contained:** no CDN, no `@font-face`, no remote assets.
- **Contrast:** primary text on the primary background passes WCAG AA. Note any accent on
  background pairing that fails for small text and give a darker variant. White text on an
  accent fill must reach 4.5:1; deepen the fill until it does.
- **Accent discipline:** state how much of a page may use the accent; never body text.
- **Faithful:** every hex and typeface is sourced or flagged as approximated. No invented
  brand colors.
- **Evoke, never infringe:** no logo reproduction in any output.

## Verify before done

Open `preview.html` in a browser at desktop and phone width: the swatches match the
sourced hex values, the type scale renders in the intended stacks, and the sample card
reads on-brand. For brand-critical work, have an independent reviewer take its own
screenshots and check them against the anti-pattern list (see `swe:builder-reviewer-loop`).

## Index

If the folder holds several brands, keep a `design-systems/README.md` with one row per
brand: slug, a one-line description, and the check date.
