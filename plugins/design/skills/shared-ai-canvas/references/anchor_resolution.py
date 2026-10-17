"""Reference: text anchors that survive edits, and refuse rather than guess.

An anchor is the exact quote the person selected plus a little text before and after it.
Character offsets are stored only as hints and never decide where a change lands.

Candidates are the exact matches of the quote, or, when there are none, the matches that
ignore whitespace runs and punctuation. The same rule then picks among them:
  - When before/after text was recorded, it must agree, even for a single candidate.
    The quote alone is not proof: if it had copies when selected, or a copy was pasted
    later, a lone match can be the wrong copy.
      * one candidate whose before and after text both fit wins;
      * if none fit, a single candidate may stand on one fitting side only when the quote
        was unique at selection (a neighbouring edit should not orphan it);
      * otherwise refuse with context_mismatch.
  - With no recorded context, a single candidate wins only if the quote was not a
    duplicate when selected; among several, the recorded occurrence index is used only
    if the count is unchanged.
Refusals: empty_quote, not_found, ambiguous, context_mismatch, spans_non_text_block.

Adapters flatten each medium (article, slides, script, timeline) into one string and put
OBJECT_REPLACEMENT (U+FFFC) where a non-text block sits, so a match across it is refused.
Python 3.8+, standard library only.
"""

import unicodedata
from bisect import bisect_left
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
    reason: str = ""     # empty_quote | not_found | ambiguous | context_mismatch
                         # | spans_non_text_block


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

    norm_doc, index_map = _normalize_with_map(doc)
    n = len(anchor.quote)
    exact = _find_all(doc, anchor.quote)
    if exact:
        return _choose(doc, norm_doc, index_map, [(s, s + n) for s in exact], anchor, "exact")

    # No exact copy: tolerant match that ignores whitespace runs and punctuation.
    norm_quote = _normalize_with_map(anchor.quote)[0].strip()
    if not norm_quote:
        return _refuse("not_found")
    spans = []
    for ns in _find_all(norm_doc, norm_quote):
        ne = ns + len(norm_quote) - 1
        spans.append((index_map[ns], index_map[ne] + 1))
    if not spans:
        return _refuse("not_found")
    return _choose(doc, norm_doc, index_map, spans, anchor, "tolerant")


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


def _choose(doc, norm_doc, index_map, spans, anchor: Anchor, method: str) -> Resolution:
    """Pick exactly one candidate span using the recorded context, or refuse."""
    was_duplicate = (anchor.occurrences or 0) > 1
    want_pre = _normalize_with_map(anchor.prefix)[0].strip()
    want_suf = _normalize_with_map(anchor.suffix)[0].strip()

    if want_pre or want_suf:
        fits = [_context_fit(norm_doc, index_map, s, e, want_pre, want_suf) for s, e in spans]
        both = [sp for sp, (pre_ok, suf_ok) in zip(spans, fits) if pre_ok and suf_ok]
        if len(both) == 1:
            label = "context" if method == "exact" and len(spans) > 1 else method
            return _place(doc, both[0][0], both[0][1], label)
        if len(both) > 1:
            return _refuse("ambiguous")
        # Nothing fits on both sides. Only a quote that was unique when selected, and is
        # still the only candidate, may survive an edit to one neighbouring side.
        if len(spans) == 1 and not was_duplicate:
            pre_ok, suf_ok = fits[0]
            if (want_pre and pre_ok) or (want_suf and suf_ok):
                return _place(doc, spans[0][0], spans[0][1], method)
        return _refuse("context_mismatch")

    # No context recorded: the quote and the occurrence count are all there is.
    if len(spans) == 1 and not was_duplicate:
        return _place(doc, spans[0][0], spans[0][1], method)
    if (method == "exact" and anchor.occurrence is not None
            and anchor.occurrences == len(spans) and 0 <= anchor.occurrence < len(spans)):
        s, e = spans[anchor.occurrence]
        return _place(doc, s, e, "occurrence")
    return _refuse("ambiguous")


def _context_fit(norm_doc, index_map, start, end, want_pre, want_suf):
    """(prefix agrees, suffix agrees) for a raw span, compared in normalized text.

    An empty recorded side always agrees. Comparing in normalized text means a changed
    space or quote mark next to the selection does not count as different context.
    """
    ns = bisect_left(index_map, start)   # first normalized char at or after start
    ne = bisect_left(index_map, end)     # first normalized char at or after end
    pre_ok = norm_doc[:ns].rstrip().endswith(want_pre)
    suf_ok = norm_doc[ne:].lstrip().startswith(want_suf)
    return pre_ok, suf_ok


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
