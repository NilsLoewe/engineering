#!/usr/bin/env python3
"""Self-test for review_stats.py (no network)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
from review_stats import finding, outcome, table  # noqa: E402


def thread(first, *replies, outdated=False, resolved=False):
    return {"isOutdated": outdated, "isResolved": resolved,
            "comments": {"nodes": [{"body": first}] + [{"body": r} for r in replies]}}


class Stats(unittest.TestCase):
    def test_parse_both_formats(self):
        self.assertEqual(finding("**major** · `kern-validate-input`\n\nx", ["**"]), ("major", "kern-validate-input"))
        self.assertEqual(finding("🤖 review · head `abc`"), ("?", "-"))
        seon = "🤖 **review-agent** · `minor` · team-rule · `fe-comment-volume`\n\n**Title**"
        self.assertEqual(finding(seon), ("minor", "fe-comment-volume"))
        old = "🤖 **review-agent** · `major` · correctness\n\n**Title**"
        self.assertEqual(finding(old), ("major", "correctness"))
        self.assertIsNone(finding("Looks good to me"))

    def test_outcome_tag_wins_over_outdated(self):
        self.assertEqual(outcome(thread("f", "Not a defect: the caller retries", outdated=True)), "not-a-defect")
        self.assertEqual(outcome(thread("f", "fixed in abc123: guard added")), "fixed")
        self.assertEqual(outcome(thread("f", "thanks", outdated=True)), "changed")
        self.assertEqual(outcome(thread("f")), "open")
        self.assertEqual(outcome(thread("f", "This is intentional, the job retries.", outdated=True)), "not-a-defect")

    def test_precision_ignores_open(self):
        rows = [{"rule": "r", "outcome": o} for o in ("fixed", "changed", "not-a-defect", "open")]
        t = table(rows)[0]
        self.assertEqual((t["findings"], t["decided"], t["precision"]), (4, 3, 0.67))


if __name__ == "__main__":
    unittest.main()
