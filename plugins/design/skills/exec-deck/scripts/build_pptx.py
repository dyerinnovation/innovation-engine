#!/usr/bin/env python3
"""Build an editable 16:9 .pptx from an exec deck (HTML or JSON).

Usage:
  python3 build_pptx.py deck.html -o versions/deck-v1.pptx
  python3 build_pptx.py deck.json -o versions/deck-v1.pptx
  python3 build_pptx.py deck.html --dump deck.json   # write the parsed JSON only

Input HTML follows the authoring contract in references/deck-template.html:
one <section class="slide" data-layout="..."> per slide, text marked with
data-field, repeated items wrapped in data-group (data-pick = recommended).
Theme colors and fonts come from the first :root block (hex values only).

JSON shape: {"theme": {"color-bg": "#fff", ...},
             "slides": [{"layout": "big-number", "fields": {"title": ["..."]},
                         "groups": [{"pick": false, "fields": {...}}]}]}

Only dependency: python-pptx. Every text box stays native and editable.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser

VOID = {"br", "img", "hr", "meta", "link", "input", "source", "wbr"}
DEFAULT_THEME = {
    "color-bg": "#ffffff", "color-surface": "#f3f4f6", "color-rule": "#d9dce1",
    "color-text": "#16181d", "color-text-soft": "#3d424b", "color-text-muted": "#6b717c",
    "color-accent": "#2856c9", "color-accent-strong": "#1d3f96", "color-on-accent": "#ffffff",
    "font-display": "Arial", "font-body": "Arial",
}


class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.slides, self.stack, self.css = [], [], []
        self.slide = self.group = None
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "style":
            self.in_style = True
        if tag in VOID:
            if tag == "br":
                self._text(" ")
            return
        frame = {"tag": tag, "slide": False, "group": False, "field": None, "buf": []}
        if tag == "section" and "slide" in (a.get("class") or "").split():
            self.slide = {"layout": a.get("data-layout", "bottom-line"), "fields": {}, "groups": []}
            frame["slide"] = True
        elif self.slide is not None and "data-group" in a:
            self.group = {"pick": "data-pick" in a, "fields": {}}
            self.slide["groups"].append(self.group)
            frame["group"] = True
        if self.slide is not None and a.get("data-field"):
            frame["field"] = a["data-field"]
        self.stack.append(frame)

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag in VOID:
            return
        while self.stack:
            frame = self.stack.pop()
            if frame["field"]:
                text = re.sub(r"\s+", " ", "".join(frame["buf"])).strip()
                target = self.group if self.group is not None else self.slide
                if text and target is not None:
                    target["fields"].setdefault(frame["field"], []).append(text)
            if frame["group"]:
                self.group = None
            if frame["slide"]:
                self.slides.append(self.slide)
                self.slide = None
            if frame["tag"] == tag:
                break

    def handle_data(self, data):
        if self.in_style:
            self.css.append(data)
        else:
            self._text(data)

    def _text(self, data):
        for frame in self.stack:
            if frame["field"]:
                frame["buf"].append(data)


def parse_html(src):
    p = DeckParser()
    p.feed(src)
    theme = dict(DEFAULT_THEME)
    m = re.search(r":root\s*{([^}]*)}", "".join(p.css))
    if m:
        for name, val in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", m.group(1)):
            val = val.strip()
            if name.startswith("font-"):
                theme[name] = val.split(",")[0].strip().strip("\"'")
            elif re.fullmatch(r"#[0-9a-fA-F]{6}", val):
                theme[name] = val
    return {"theme": theme, "slides": p.slides}


# ----------------------------------------------------------------------------- pptx
def build(deck, out):
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.util import Inches, Pt
    except ImportError:
        sys.exit("python-pptx is not installed: pip install python-pptx")

    t = dict(DEFAULT_THEME, **deck.get("theme", {}))
    rgb = lambda k: RGBColor.from_string(t[k].lstrip("#").upper())
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    L, W = 0.8, 13.333 - 1.6  # left margin and content width, inches

    def box(s, x, y, w, h, text, size, color="color-text", bold=False, font="font-body"):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        lines = text if isinstance(text, list) else [text]
        for i, line in enumerate(lines):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.space_after = Pt(size * 0.6)
            r = para.add_run()
            r.text = line
            r.font.size, r.font.bold, r.font.name = Pt(size), bold, t[font]
            r.font.color.rgb = rgb(color)
        return tb

    def rect(s, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
        sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = rgb(fill)
        sh.line.fill.background()
        sh.shadow.inherit = False
        style = sh._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
        if style is not None:  # drop theme effects (shadows) some viewers still apply
            sh._element.remove(style)
        return sh

    def first(d, k, default=""):
        return (d.get(k) or [default])[0]

    def bullets(d):
        return ["•  " + p for p in d.get("point", [])[:3]]

    for n, sd in enumerate(deck["slides"], 1):
        s = prs.slides.add_slide(blank)
        f, groups, lay = sd.get("fields", {}), sd.get("groups", []), sd.get("layout")
        bg = "color-accent-strong" if lay == "title" else "color-bg"
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = rgb(bg)
        ink = "color-on-accent" if lay == "title" else "color-text"

        if lay == "title":
            box(s, L, 2.0, W, 0.4, first(f, "kicker").upper(), 13, ink, True)
            box(s, L, 2.5, W * 0.8, 2.0, first(f, "title"), 48, ink, True, "font-display")
            box(s, L, 4.6, W * 0.8, 0.8, first(f, "subtitle"), 20, ink)
            box(s, L, 5.6, W, 0.4, first(f, "meta"), 13, ink)
        else:
            box(s, L, 0.55, W, 0.4, first(f, "kicker").upper(), 12, "color-accent", True)
            title_size = 34 if lay == "bottom-line" else 30
            box(s, L, 0.95, W * 0.85, 1.3, first(f, "title"), title_size, "color-text", True, "font-display")

        if lay == "bottom-line":
            rect(s, L, 2.6, 0.08, 2.6, "color-accent")
            box(s, L + 0.35, 2.7, W - 0.5, 2.6, bullets(f), 22, "color-text-soft")
        elif lay == "big-number":
            box(s, L, 2.3, 6.2, 2.6, first(f, "number"), 150, "color-accent", True, "font-display")
            lx = L + 0.4 + 1.25 * len(first(f, "number"))
            box(s, lx, 3.6, W - (lx - L), 1.2, first(f, "label"), 26, "color-text", True)
            box(s, L, 5.1, W, 0.8, first(f, "context"), 20, "color-text-soft")
        elif lay == "comparison":
            gw = (W - 0.4 * (len(groups) - 1)) / max(len(groups), 1)
            for i, g in enumerate(groups):
                x = L + i * (gw + 0.4)
                rect(s, x, 2.4, gw, 3.7, "color-surface")
                rect(s, x, 2.4, gw, 0.07, "color-accent" if g.get("pick") else "color-rule")
                y = 2.65
                if g.get("pick"):
                    pill = rect(s, x + 0.3, y, 1.7, 0.35, "color-accent-strong", MSO_SHAPE.ROUNDED_RECTANGLE)
                    pill.text_frame.text = "RECOMMENDED"
                    run = pill.text_frame.paragraphs[0].runs[0]
                    run.font.size, run.font.bold, run.font.name = Pt(10), True, t["font-body"]
                    run.font.color.rgb = rgb("color-on-accent")
                    y += 0.5
                box(s, x + 0.3, y, gw - 0.6, 0.6, first(g["fields"], "head"), 22, "color-text", True, "font-display")
                box(s, x + 0.3, y + 0.8, gw - 0.6, 2.2, bullets(g["fields"]), 18, "color-text-soft")
        elif lay == "timeline":
            rect(s, L, 3.05, W, 0.04, "color-rule")
            gw = W / max(len(groups), 1)
            for i, g in enumerate(groups):
                x = L + i * gw
                dot = rect(s, x, 2.88, 0.38, 0.38, "color-accent" if g.get("pick") else "color-bg", MSO_SHAPE.OVAL)
                dot.line.color.rgb = rgb("color-accent")
                dot.line.width = Pt(3)
                box(s, x, 3.5, gw - 0.2, 0.4, first(g["fields"], "when").upper(), 14, "color-accent", True)
                box(s, x, 3.95, gw - 0.2, 1.4, first(g["fields"], "what"), 19, "color-text", True)
        elif lay == "decision":
            ask = rect(s, L, 2.5, W, 1.0, "color-accent-strong", MSO_SHAPE.ROUNDED_RECTANGLE)
            ask.adjustments[0] = 0.12
            tf = ask.text_frame
            tf.word_wrap = True
            tf.text = first(f, "ask")
            run = tf.paragraphs[0].runs[0]
            run.font.size, run.font.bold, run.font.name = Pt(24), True, t["font-display"]
            run.font.color.rgb = rgb("color-on-accent")
            box(s, L, 3.9, W, 2.0, bullets(f), 20, "color-text-soft")

        if lay != "title":
            rect(s, L, 6.7, W, 0.01, "color-rule")
            box(s, L, 6.75, W - 1.0, 0.4, first(f, "source"), 10, "color-text-muted")
            box(s, L + W - 0.6, 6.75, 0.6, 0.4, str(n), 10, "color-text-muted")
        if f.get("notes"):
            s.notes_slide.notes_text_frame.text = " ".join(f["notes"])

    prs.save(out)
    print(f"wrote {out}: {len(deck['slides'])} slides")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", help="deck .html or .json")
    ap.add_argument("-o", "--out", help="output .pptx path (put it in versions/)")
    ap.add_argument("--font", help="font for every text box (one installed where the deck is opened)")
    ap.add_argument("--dump", help="write the parsed deck JSON to this path")
    args = ap.parse_args()
    with open(args.src, encoding="utf-8") as fh:
        raw = fh.read()
    deck = json.loads(raw) if args.src.endswith(".json") else parse_html(raw)
    if not deck.get("slides"):
        sys.exit("no slides found: check the section.slide markup")
    for i, sd in enumerate(deck["slides"], 1):
        for d in [sd.get("fields", {})] + [g["fields"] for g in sd.get("groups", [])]:
            if len(d.get("point", [])) > 3:
                print(f"warning: slide {i} has more than 3 points; extras dropped", file=sys.stderr)
    if args.font:
        deck.setdefault("theme", {}).update({"font-display": args.font, "font-body": args.font})
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as fh:
            json.dump(deck, fh, indent=2)
        print(f"wrote {args.dump}")
    if args.out:
        build(deck, args.out)
    if not (args.out or args.dump):
        ap.error("give -o and/or --dump")


if __name__ == "__main__":
    main()
