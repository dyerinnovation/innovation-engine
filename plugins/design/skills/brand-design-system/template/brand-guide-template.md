---
name: <slug>-design-system
description: Brand-faithful styling reference for <Brand>. Use when building any page, document, deck or app theme that should carry <Brand>'s look and feel. Encodes the verified palette, the <accent> accent, the <display> and <body> type system with free self-contained fallbacks, layout and voice rules, and an explicit anti-pattern list. Triggers on "<Brand> brand", "<Brand> design system", "<Brand> colors", "style this like <Brand>".
---

# <Brand> Design System

A reference for producing material that looks and reads like <Brand> made it:
**<three to six word brand essence, for example "warm minimalism, one coral accent">**.
Not <what it must not read as>.

Values checked against <primary source> (<YYYY-MM-DD>) and cross-checked with
<secondary source>. Sources are at the bottom; anything approximated is flagged.

## 1. Color tokens

<Tables for backgrounds, ink and accent: | Token | Hex | rgb | When to use |>
<Accent rationing rule: how much of a page may use the accent; body text is always ink.>

## 2. Type system

<Real display and body faces (with foundry). The free fallback stacks from tokens.css and
why (the real face first means anyone who has it sees it). Pairing rules: headings in the
display face, body in the body face, eyebrows in the display face, uppercase.>

## 3. Layout and spacing

<Density (airy or dense), grid or editorial, rules or cards, corner radius character,
alignment, line length: whatever defines this brand's page.>

## 4. Voice and tone

<How this brand writes. Do and do not. Concrete guidance for headlines, body copy and
buttons.>

## 5. Brand anti-patterns: never do this

<A numbered, blocking list a reviewer can apply word for word. Always include:
 - the wrong-background tell (pure white or black when the brand grounds on a tint)
 - accent misuse (recolored, oversaturated, used for body text)
 - unapproved typefaces
 - never load CDN fonts or assets (files stay self-contained)
 - never reproduce or redraw the logo
 - any brand-specific tell.>

## 6. Logo and wordmark usage

<Describe the identity, clear space and misuse rules. Evoke the brand through palette,
type and tone; do not reproduce the trademarked mark.>

## 7. How to apply

1. Inline the tokens.css `:root` block into the document.
2. Set the canvas (background, text color, body font).
3. Set headings in the display face.
4. Place the accent deliberately, within the rationing rule.
5. Write copy in the voice from section 4.
6. Check the result against section 5.
7. Compare visually with preview.html.

## Sources (checked <YYYY-MM-DD>)

- <Official brand or design-system page: URL>
- <Live computed CSS of the brand's site: how it was captured>
- <Type foundry or identity case study: URL>

### Approximated or not independently verifiable

- <Anything inferred: name-to-hex guesses, uncertain typefaces. Verified hex values are
  authoritative; approximations are best effort.>
