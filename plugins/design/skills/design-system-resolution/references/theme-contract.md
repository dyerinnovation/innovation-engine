# Resolved-theme contract

The one shape `design-system-resolution` hands to every visual skill. A downstream skill
maps these names into its own template's token block and never reads the source files
again. Keep the contract small; add fields only, never rename or remove one.

## Shape

```json
{
  "system": "engine default theme",
  "source": "user-named | project | default",
  "colors": {
    "light": {
      "bg": "#f8fafc", "surface": "#ffffff", "sunken": "#f1f5f9",
      "rule": "#e2e8f0", "control": "#cbd5e1",
      "text": "#0f172a", "text_soft": "#334155", "text_muted": "#475569",
      "accent": "#1d4ed8", "accent_tint": "rgba(29,78,216,.10)",
      "success": "#15803d", "warning": "#854d0e", "danger": "#b91c1c"
    },
    "dark": {
      "bg": "#0b1120", "surface": "#151c2c", "sunken": "#10172a",
      "rule": "#263045", "control": "#3a465e",
      "text": "#f8fafc", "text_soft": "#e2e8f0", "text_muted": "#a3b0c2",
      "accent": "#93b4ff", "accent_tint": "rgba(147,180,255,.16)",
      "success": "#4ade80", "warning": "#facc15", "danger": "#f87171"
    },
    "fills": {
      "accent_fill": "#1d4ed8", "accent_fill_press": "#1e40af",
      "success_fill": "#15803d", "danger_fill": "#b91c1c", "on_fill": "#ffffff"
    },
    "data": []
  },
  "type": {
    "display": "ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", Roboto, Arial, sans-serif",
    "body": "ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", Roboto, Arial, sans-serif",
    "mono": "ui-monospace, \"SF Mono\", Menlo, Consolas, monospace"
  },
  "space": ["4px", "8px", "12px", "16px", "24px", "32px", "48px", "64px"],
  "radius": { "sm": "4px", "md": "8px", "lg": "12px", "pill": "999px" },
  "logo": null,
  "provenance": {
    "colors.light": "references/default-theme.css",
    "colors.dark": "references/default-theme.css",
    "type": "references/default-theme.css",
    "space": "references/default-theme.css",
    "radius": "references/default-theme.css",
    "logo": "none found"
  },
  "derived": [],
  "gaps": []
}
```

The values above are the engine default theme, so the example is also the fallback.

## Field rules

| Field | Rule |
|---|---|
| `system` | A short human name for the system used. This is the name said in the one-line notice. |
| `source` | Which rung of the order won: `user-named`, `project` or `default`. |
| `colors.light`, `colors.dark` | Every key present in both. Text keys (`text`, `text_soft`, `text_muted`, `accent`, `success`, `warning`, `danger`) reach 4.5:1 on `bg`, `surface` and `sunken` in the same theme. |
| `colors.fills` | Fills that carry white text. Each reaches 4.5:1 against `on_fill`. Deepen a fill until it passes; never lighten the text instead. |
| `colors.data` | Optional chart colors. Data only, never a second brand color. |
| `type.*` | Real faces first, then widely installed fallbacks in the same category, ending in a generic family. No CDN, no `@font-face`. |
| `space`, `radius` | A short scale. Downstream skills may round to their own scale. |
| `logo` | A relative path to the project's own logo file, or `null`. Never a redrawn or third-party mark. |
| `provenance` | One entry per field group: the file, page or skill it came from, or `default` when it was filled from the engine default theme. |
| `derived` | One entry per token whose value was computed rather than copied, for example `{"token": "colors.dark.accent", "value": "#3e80ff", "from": "#0b5fff (tokens.json color.brand)", "why": "lightened, same hue, 4.65:1 on dark surface"}`. Empty when every value was copied as is. |
| `gaps` | Field groups the source did not provide and that were filled from the default (for example `"colors.dark"`). Report these in the one-line notice. |

## Filling gaps

A project source rarely has everything. Take what it has, fill the rest from the engine
default theme, and list each filled group in `gaps`. Common cases:

- No dark theme: use dark values the source gives somewhere (a `.dark` class, a
  `prefers-color-scheme` block). Otherwise take the default dark grounds and text, and
  carry the project accent across with the rule in "Contrast fixes" below, so the brand
  still shows in dark mode. A separate dark-only file is not a dark theme for this source
  unless the project ties the two together (see "Ask or not" in the skill).
- Only one accent: use it for `accent` and as `accent_fill` if white text passes on it;
  otherwise darken it for `accent_fill` and record it in `derived`.
- No type stack: use the default stacks.

## Contrast fixes

When a source color fails its target, keep the hue and move only lightness, so the brand
stays recognizable and repeat runs land on the same value.

- Targets: 4.5:1 for every text key against `bg`, `surface` and `sunken` in its theme
  (the lowest of the three decides); 4.5:1 for every fill against `on_fill`.
- Direction: lighten on dark grounds, darken on light grounds and for fills.
- Method: convert to HSL, keep hue and saturation, step lightness by 1% until the target
  passes, and stop at the first passing value. Example: brand `#0b5fff` is 3.32:1 on the
  default dark surface; at the same hue it first passes at `#3e80ff` (4.65:1).
- Record each result in `derived` with the source value, the token, and the ratio, and
  point that group's `provenance` at the source file.
- Fall back to the default theme's token (for example dark `accent` `#93b4ff`) only when no
  shade of the hue passes before it washes out to near white or near black. Record the
  fallback in `gaps`.

## Text on its own tint

A tint is a see-through wash of a color, so it moves the background toward that color and
lowers the contrast of the same color's text. Check every text-on-tint pair (accent text on
`accent_tint`, status text on a status tint) against the tint composited over the ground it
sits on, at 4.5:1.

Worked example, brand `#0b5fff`, chip text on its own tint:

| Theme | Text | Tint over ground | Ratio | Fix | After |
|---|---|---|---|---|---|
| Light | `#0b5fff` | 10% over `#ffffff` = `#e7efff` | 4.44:1, fails | darken text 1% lightness to `#055bff` | 4.61:1 |
| Light | `#0b5fff` | thin tint to 8% = `#ebf2ff` | 4.56:1 | or keep text, thin the tint | 4.56:1 |
| Dark | `#3e80ff` | 16% over `#151c2c` = `#1c2c4e` | 3.77:1, fails | lighten text and tint together to `#5c94ff` | 4.52:1 |

Thinning the tint alone does not rescue the dark case here (even 4% stays at 4.44:1), so
move the text. Do not make the tint stronger: more opacity brings it closer to the text and
lowers the ratio. Record the result in `derived`, for example
`{"token": "colors.dark.accent_on_tint", "value": "#5c94ff", "from": "#3e80ff", "why": "lightened, same hue, 4.52:1 on its 16% tint over surface"}`.

## How a downstream skill uses it

1. Map the contract into the template's own token block (for example `--l-*` and `--d-*`
   names in a board template, or `--color-*` names in a report). Touch nothing else.
2. Recheck contrast if the template combines tokens in a new way, such as text on its own
   tint (see "Text on its own tint" above).
3. Use the accent where a reader sees it (headings, links, the primary action, status
   chips), not only in one decorative span, or the page will not look like the brand.
4. If `logo` is set, use that file in the page's lockup; otherwise use a plain text
   wordmark of the project name.
