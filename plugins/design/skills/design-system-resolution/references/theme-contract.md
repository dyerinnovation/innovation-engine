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
| `gaps` | Field groups the source did not provide and that were filled from the default (for example `"colors.dark"`). Report these in the one-line notice. |

## Filling gaps

A project source rarely has everything. Take what it has, fill the rest from the engine
default theme, and list each filled group in `gaps`. Common cases:

- No dark theme: derive one only if the source gives clear dark values somewhere (a
  `.dark` class, a `prefers-color-scheme` block); otherwise use the default dark values
  and keep the project accent only if it passes contrast on the dark grounds.
- Only one accent: use it for `accent` and as `accent_fill` if white text passes on it;
  otherwise darken it for `accent_fill` and note the change.
- No type stack: use the default stacks.

## How a downstream skill uses it

1. Map the contract into the template's own token block (for example `--l-*` and `--d-*`
   names in a board template, or `--color-*` names in a report). Touch nothing else.
2. Recheck contrast if the template combines tokens in a new way (text on a tint).
3. If `logo` is set, use that file in the page's lockup; otherwise use a plain text
   wordmark of the project name.
