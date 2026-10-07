#!/usr/bin/env bash
# Export .drawio diagrams to SVG beside their source, pinned to a light canvas.
#
# Why not a bare `drawio --export`: draw.io stamps `color-scheme: light dark` on the
# exported <svg> root. In a dark-mode browser that flips only the canvas to dark while
# explicit fills stay light, so you get white text on white boxes. Pinning the export
# to light makes the diagram render the same for every reader.
#
# Usage:  export-drawio.sh                 # every .drawio in the current folder
#         export-drawio.sh a.drawio b.drawio
#
# Requires the draw.io desktop app's CLI on PATH as `drawio`.

set -euo pipefail

command -v drawio >/dev/null || { echo "drawio CLI not found; install the draw.io desktop app" >&2; exit 1; }

targets=("$@")
if [ ${#targets[@]} -eq 0 ]; then
  shopt -s nullglob
  targets=(*.drawio)
fi
[ ${#targets[@]} -eq 0 ] && { echo "no .drawio files found" >&2; exit 1; }

for src in "${targets[@]}"; do
  out="${src%.drawio}.svg"
  drawio --export --format svg --output "$out" "$src" >/dev/null 2>&1
  [ -s "$out" ] || { echo "FAILED (empty output; check disk space): $src" >&2; exit 1; }
  perl -pi -e 's/color-scheme:\s*light dark/color-scheme: light/' "$out"
  echo "$src -> $out"
done
