"""Reference: text anchors that survive edits, and refuse rather than guess.

An anchor is the exact quote the person selected plus a little text before and after it.
Character offsets are stored only as hints and never decide where a change lands.

Resolution order (stop at the first step that yields exactly one place):
  1. exact match of the quote
  2. among exact matches, the one whose before/after text matches
  3. the recorded occurrence index, only if the occurrence count is unchanged
  4. a whitespace- and punctuation-tolerant match (with the same context tie-break)
Anything else is refused: not found, ambiguous, or spanning a non-text block.

Adapters flatten each medium (article, slides, script, timeline) into one string and put
OBJECT_REPLACEMENT (U+FFFC) where a non-text block sits, so a match across it is refused.
Python 3.8+, standard library only.
"""

import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Tuple

OBJECT_REPLACEMENT = "￼"
CONTEXT_CHARS = 32


@dataclass(frozen=True)
class Anchor:
    quote: str
    prefix: str = ""
    suffix: str = ""
    occurrence: Optional[int] = None    # index among exact matches when selected
    occurrences: Optional[int] = None   # how many exact matches existed then
    hint_start: Optional[int] = None    # offset hint only; never used to choose


@dataclass(frozen=True)
class Resolution:
    ok: bool
    start: int = -1
    end: int = -1
    method: str = ""     # exact | context | occurrence | tolerant
    reason: str = ""     # empty_quote | not_found | ambiguous | spans_non_text_block


def make_anchor(doc: str, start: int, end: int, context: int = CONTEXT_CHARS) -> Anchor:
    """Capture an anchor from a selection made on the current document."""
    quote = doc[start:end]
    hits = _find_all(doc, quote) if quote else []
    return Anchor(
        quote=quote,
        prefix=doc[max(0, start - context):start],
        suffix=doc[end:end + context],
        occurrence=hits.index(start) if start in hits else None,
        occurrences=len(hits) if hits else None,
        hint_start=start,
    )


def resolve(doc: str, anchor: Anchor) -> Resolution:
    if not anchor.quote or not anchor.quote.strip():
        return _refuse("empty_quote")
    if OBJECT_REPLACEMENT in anchor.quote:
        return _refuse("spans_non_text_block")

    exact = _find_all(doc, anchor.quote)
    n = len(anchor.quote)
    if len(exact) == 1:
        return _place(doc, exact[0], exact[0] + n, "exact")
    if len(exact) > 1:
        spans = [(s, s + n) for s in exact]
        by_context = _context_filter(doc, spans, anchor)
        if len(by_context) == 1:
            return _place(doc, by_context[0][0], by_context[0][1], "context")
        if (anchor.occurrence is not None and anchor.occurrences == len(exact)
                and 0 <= anchor.occurrence < len(exact)):
            s = exact[anchor.occurrence]
            return _place(doc, s, s + n, "occurrence")
        return _refuse("ambiguous")

    # 4. tolerant match: ignore whitespace runs and punctuation.
    norm_doc, index_map = _normalize_with_map(doc)
    norm_quote, _ = _normalize_with_map(anchor.quote)
    norm_quote = norm_quote.strip()
    if not norm_quote:
        return _refuse("not_found")
    spans = []
    for ns in _find_all(norm_doc, norm_quote):
        ne = ns + len(norm_quote) - 1
        spans.append((index_map[ns], index_map[ne] + 1))
    if not spans:
        return _refuse("not_found")
    if len(spans) == 1:
        return _place(doc, spans[0][0], spans[0][1], "tolerant")
    by_context = _context_filter(doc, spans, anchor)
    if len(by_context) == 1:
        return _place(doc, by_context[0][0], by_context[0][1], "tolerant")
    return _refuse("ambiguous")


def apply_suggestion(doc: str, anchor: Anchor, replacement: str) -> Tuple[Optional[str], Resolution]:
    """Re-resolve the anchor on the document as it is NOW, then replace only that span."""
    where = resolve(doc, anchor)
    if not where.ok:
        return None, where
    return doc[:where.start] + replacement + doc[where.end:], where


def change_is_confined(before: str, after: str, start: int, end: int) -> bool:
    """True when `after` differs from `before` only inside before[start:end].

    Use it when a model returns a whole rewritten document instead of a replacement:
    reject the patch if anything outside the selection moved.
    """
    head, tail = before[:start], before[end:]
    return (after.startswith(head) and after.endswith(tail)
            and len(after) >= len(head) + len(tail))


# helpers ---------------------------------------------------------------------------------

def _refuse(reason: str) -> Resolution:
    return Resolution(ok=False, reason=reason)


def _place(doc: str, start: int, end: int, method: str) -> Resolution:
    if OBJECT_REPLACEMENT in doc[start:end]:
        return _refuse("spans_non_text_block")
    return Resolution(ok=True, start=start, end=end, method=method)


def _find_all(haystack: str, needle: str) -> List[int]:
    hits, i = [], haystack.find(needle)
    while i != -1:
        hits.append(i)
        i = haystack.find(needle, i + 1)
    return hits


def _context_filter(doc: str, spans, anchor: Anchor):
    """Keep spans whose surrounding text matches the stored before/after text."""
    if not anchor.prefix and not anchor.suffix:
        return []
    want_pre = _normalize_with_map(anchor.prefix)[0].strip()
    want_suf = _normalize_with_map(anchor.suffix)[0].strip()
    keep = []
    for s, e in spans:
        pre = _normalize_with_map(doc[max(0, s - len(anchor.prefix) - 8):s])[0].strip()
        suf = _normalize_with_map(doc[e:e + len(anchor.suffix) + 8])[0].strip()
        if pre.endswith(want_pre) and suf.startswith(want_suf):
            keep.append((s, e))
    return keep


def _is_punct(ch: str) -> bool:
    return unicodedata.category(ch).startswith("P")


def _normalize_with_map(text: str):
    """Drop punctuation, collapse whitespace runs to one space; map back to source indexes."""
    out, index_map = [], []
    prev_space = False
    for i, ch in enumerate(text):
        if _is_punct(ch):
            continue
        if ch.isspace():
            if prev_space:
                continue
            out.append(" ")
            index_map.append(i)
            prev_space = True
            continue
        out.append(ch)
        index_map.append(i)
        prev_space = False
    return "".join(out), index_map
