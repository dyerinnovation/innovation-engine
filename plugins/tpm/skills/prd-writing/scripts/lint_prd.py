#!/usr/bin/env python3
"""Lint a PRD written from references/prd-template.md.

Checks:
  - Status, Release and Code read at header lines are filled in.
  - Every requirement row has a Where cell with a path:line reference.
  - Every requirement claim stays within a word budget (default 30 words).
  - Every open decision has a suggested default.
  - Every acceptance criterion has exactly one valid tag (ci, rubric:<id>, human),
    and ci or rubric criteria name what covers them.
  - No template placeholders like <name> are left in tables or headers.

Usage: python3 lint_prd.py path/to/prd.md [--claim-words 30]
Exit code 0 when clean, 1 when any error is found. Warnings do not fail.
"""

import argparse
import re
import sys

PATH_LINE = re.compile(r"[\w./-]+\.\w+:\d+")
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>|]*>")
TAG = re.compile(r"^(ci|human|rubric:[\w.-]+)$")


def sections(text):
    """Map each H2 heading to the lines under it."""
    out, current = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return out


def table_rows(lines):
    """Return table rows as lists of cells, skipping the header and divider."""
    rows = [l for l in lines if l.strip().startswith("|")]
    parsed = []
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if i == 0 or all(set(c) <= set("-: ") for c in cells):
            continue
        parsed.append(cells)
    return parsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prd")
    ap.add_argument("--claim-words", type=int, default=30)
    args = ap.parse_args()

    text = open(args.prd, encoding="utf-8").read()
    secs = sections(text)
    errors, warnings = [], []

    for field in ("Status", "Release", "Code read at"):
        m = re.search(r"\*\*" + field + r":\*\*\s*(.*)", text)
        if not m or not m.group(1).strip() or PLACEHOLDER.search(m.group(1)):
            errors.append(f"header: {field} is missing or still a placeholder")

    for cells in table_rows(secs.get("requirements", [])):
        if len(cells) < 3:
            errors.append(f"requirements: malformed row {cells}")
            continue
        rid, claim, where = cells[0], cells[1], cells[2]
        if not PATH_LINE.search(where):
            errors.append(f"{rid}: Where needs a path:line reference")
        if len(claim.split()) > args.claim_words:
            warnings.append(f"{rid}: claim is {len(claim.split())} words (budget {args.claim_words})")

    for cells in table_rows(secs.get("decisions", [])):
        if len(cells) < 6:
            errors.append(f"decisions: malformed row {cells}")
            continue
        did, default, status = cells[0], cells[3], cells[5].lower()
        if "open" in status and not default:
            errors.append(f"{did}: open decision has no suggested default")

    for cells in table_rows(secs.get("acceptance criteria", [])):
        if len(cells) < 4:
            errors.append(f"acceptance criteria: malformed row {cells}")
            continue
        aid, tag, covered = cells[0], cells[2].strip("`"), cells[3]
        if not TAG.match(tag):
            errors.append(f"{aid}: tag must be exactly one of ci, rubric:<id>, human (got '{tag}')")
        elif tag != "human" and not covered:
            errors.append(f"{aid}: a {tag} criterion must name what covers it")

    for name, lines in secs.items():
        for line in lines:
            if line.strip().startswith("|") and PLACEHOLDER.search(line):
                warnings.append(f"{name}: placeholder left in table: {line.strip()[:80]}")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
