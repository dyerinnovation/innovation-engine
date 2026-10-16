#!/usr/bin/env bash
# Render an exec deck to one PNG per slide so every slide can be looked at.
#
# Usage: render-check.sh <deck.html|deck.pptx> [out-dir]
#   .html  -> headless Chrome or Chromium prints to PDF (one slide per page)
#   .pptx  -> LibreOffice converts to PDF
#   then pdftoppm (poppler) writes out-dir/slide-1.png, slide-2.png, ...
# Set CHROME to the browser binary if it is not found automatically.
set -euo pipefail

src=${1:?usage: render-check.sh <deck.html|deck.pptx> [out-dir]}
out=${2:-render-check}
mkdir -p "$out"
base=$(basename "${src%.*}")
pdf="$out/$base.pdf"

case "$src" in
  *.html)
    chrome=${CHROME:-}
    if [ -z "$chrome" ]; then
      for c in google-chrome chromium chromium-browser \
               "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
               "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
        if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then chrome=$c; break; fi
      done
    fi
    [ -n "$chrome" ] || { echo "no Chrome or Chromium found; set CHROME" >&2; exit 1; }
    "$chrome" --headless --disable-gpu --no-pdf-header-footer \
      --print-to-pdf="$pdf" "file://$(cd "$(dirname "$src")" && pwd)/$(basename "$src")" 2>/dev/null
    ;;
  *.pptx)
    command -v soffice >/dev/null || { echo "LibreOffice (soffice) not found" >&2; exit 1; }
    soffice --headless --convert-to pdf --outdir "$out" "$src" >/dev/null
    ;;
  *) echo "expected .html or .pptx" >&2; exit 1 ;;
esac

command -v pdftoppm >/dev/null || { echo "pdftoppm (poppler) not found" >&2; exit 1; }
pdftoppm -png -r 80 "$pdf" "$out/slide"
ls "$out"/slide-*.png | wc -l | xargs echo "slides rendered:"
