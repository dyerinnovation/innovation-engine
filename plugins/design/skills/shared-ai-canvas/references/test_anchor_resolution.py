"""Unit tests for anchor_resolution.py. Run: python3 -m unittest test_anchor_resolution"""

import unittest

from anchor_resolution import (
    OBJECT_REPLACEMENT, Anchor, apply_suggestion, change_is_confined, make_anchor, resolve,
)

DOC = (
    "The launch went well. Sign-ups doubled in a week.\n\n"
    "Next we fix onboarding. The launch went well, but support was slow."
)


class ResolveOrder(unittest.TestCase):
    def test_unique_exact_match(self):
        a = Anchor(quote="Sign-ups doubled")
        r = resolve(DOC, a)
        self.assertTrue(r.ok)
        self.assertEqual(r.method, "exact")
        self.assertEqual(DOC[r.start:r.end], "Sign-ups doubled")

    def test_duplicate_resolved_by_context(self):
        second = DOC.rindex("The launch went well")
        a = make_anchor(DOC, second, second + len("The launch went well"))
        r = resolve(DOC, a)
        self.assertTrue(r.ok)
        self.assertEqual(r.method, "context")
        self.assertEqual(r.start, second)

    def test_duplicate_resolved_by_occurrence_when_count_unchanged(self):
        doc = "ok. ok. ok."
        a = Anchor(quote="ok", occurrence=1, occurrences=3)
        r = resolve(doc, a)
        self.assertTrue(r.ok)
        self.assertEqual(r.method, "occurrence")
        self.assertEqual(r.start, 4)

    def test_occurrence_ignored_when_count_changed(self):
        doc = "ok. ok. ok. ok."
        a = Anchor(quote="ok", occurrence=1, occurrences=3)
        self.assertEqual(resolve(doc, a).reason, "ambiguous")

    def test_offset_hint_never_decides(self):
        doc = "ok. ok."
        a = Anchor(quote="ok", hint_start=4)
        self.assertEqual(resolve(doc, a).reason, "ambiguous")

    def test_tolerant_whitespace_and_punctuation(self):
        doc = "We said “ship it”   on\nFriday, and we did."
        a = Anchor(quote='We said "ship it" on Friday')
        r = resolve(doc, a)
        self.assertTrue(r.ok)
        self.assertEqual(r.method, "tolerant")
        self.assertEqual(doc[r.start:r.end], "We said “ship it”   on\nFriday")


class Refusals(unittest.TestCase):
    def test_not_found(self):
        self.assertEqual(resolve(DOC, Anchor(quote="pricing page")).reason, "not_found")

    def test_ambiguous_without_context(self):
        self.assertEqual(resolve(DOC, Anchor(quote="The launch went well")).reason, "ambiguous")

    def test_empty_quote(self):
        self.assertEqual(resolve(DOC, Anchor(quote="   ")).reason, "empty_quote")

    def test_spans_non_text_block(self):
        doc = "Intro text." + OBJECT_REPLACEMENT + "Caption text."
        self.assertEqual(resolve(doc, Anchor(quote="text." + OBJECT_REPLACEMENT + "Caption")).reason,
                         "spans_non_text_block")
        # tolerant matching must not jump across the block either
        self.assertEqual(resolve(doc, Anchor(quote="Intro text Caption")).reason, "not_found")


class ApplyRechecks(unittest.TestCase):
    def test_apply_after_document_moved(self):
        start = DOC.index("Sign-ups doubled")
        a = make_anchor(DOC, start, start + len("Sign-ups doubled"))
        moved = "New first line.\n" + DOC
        new_doc, r = apply_suggestion(moved, a, "Sign-ups tripled")
        self.assertTrue(r.ok)
        self.assertIn("Sign-ups tripled in a week", new_doc)
        self.assertTrue(new_doc.startswith("New first line."))

    def test_apply_refuses_when_quote_was_deleted(self):
        start = DOC.index("Sign-ups doubled")
        a = make_anchor(DOC, start, start + len("Sign-ups doubled"))
        edited = DOC.replace("Sign-ups doubled in a week.", "")
        new_doc, r = apply_suggestion(edited, a, "Sign-ups tripled")
        self.assertIsNone(new_doc)
        self.assertEqual(r.reason, "not_found")

    def test_change_confined_to_selection(self):
        before = "alpha beta gamma"
        s, e = 6, 10  # "beta"
        self.assertTrue(change_is_confined(before, "alpha BETA! gamma", s, e))
        self.assertFalse(change_is_confined(before, "Alpha BETA gamma", s, e))
        self.assertFalse(change_is_confined(before, "alpha BETA gamma.", s, e))


if __name__ == "__main__":
    unittest.main()
