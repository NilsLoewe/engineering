#!/usr/bin/env python3
"""Self-test for review_post.py (no network)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
from review_post import payload, right_lines  # noqa: E402

DIFF = """diff --git a/app/a.rb b/app/a.rb
index 1..2 100644
--- a/app/a.rb
+++ b/app/a.rb
@@ -10,3 +10,4 @@ class A
 keep
-old
+new
+added
 tail
"""


class Post(unittest.TestCase):
    def test_right_lines(self):
        self.assertEqual(right_lines(DIFF), {"app/a.rb": {10, 11, 12, 13}})

    def test_anchor_or_body(self):
        f = [{"path": "app/a.rb", "line": 11, "severity": "minor", "rule": "r1", "text": "x"},
             {"path": "app/a.rb", "line": 99, "severity": "blocker", "rule": "r2", "text": "y"}]
        p = payload(f, DIFF, "abcdef123")
        self.assertEqual(p["event"], "COMMENT")
        self.assertEqual([c["line"] for c in p["comments"]], [11])
        self.assertIn("app/a.rb:99", p["body"])
        self.assertTrue(p["body"].startswith("🤖 review · head `abcdef1` · 1 blocker, 0 major, 1 minor"))

    def test_no_findings(self):
        self.assertIn("No findings.", payload([], DIFF, "abc")["body"])


if __name__ == "__main__":
    unittest.main()
