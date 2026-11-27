#!/usr/bin/env python3
"""Self-test for review_post.py (no network)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
from review_post import payload, posted_on, right_lines  # noqa: E402

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
        f = [{"path": "app/a.rb", "line": 11, "severity": "major", "rule": "r1", "text": "x"},
             {"path": "app/a.rb", "line": 99, "severity": "blocker", "rule": "r2", "text": "y"}]
        p = payload(f, DIFF, "abcdef123")
        self.assertEqual(p["event"], "COMMENT")
        self.assertEqual([c["line"] for c in p["comments"]], [11])
        self.assertIn("app/a.rb:99", p["body"])
        self.assertTrue(p["body"].startswith("🤖 review · head `abcdef1` · 1 blocker, 1 major, 0 minor"))

    def test_minor_folded_into_body_and_capped(self):
        f = [{"path": "app/a.rb", "line": 11, "severity": "minor", "rule": f"m{i}", "text": "x"} for i in range(7)]
        p = payload(f, DIFF, "abc")
        self.assertEqual(p["comments"], [])  # no thread, no mail
        self.assertIn("<details><summary>5 minor", p["body"])
        self.assertNotIn("`m5`", p["body"])

    def test_one_review_per_head(self):
        rs = [{"body": "🤖 review · head `abc`", "commit_id": "abc"}, {"body": "LGTM", "commit_id": "def"}]
        self.assertTrue(posted_on(rs, "abc"))
        self.assertFalse(posted_on(rs, "def"))

    def test_brief_ends_the_body(self):
        brief = {"check": ["tenant: client_id comes from params"], "skip": ["digit count matches the IVR, ivr.rb:42"]}
        body = payload([], DIFF, "abc", brief)["body"]
        self.assertIn("### For the human reviewer\n\nCheck yourself:\n- tenant: client_id comes from params", body)
        self.assertIn("skip unless you doubt it:\n- digit count matches the IVR", body)
        self.assertNotIn("For the human reviewer", payload([], DIFF, "abc", {"check": [], "skip": []})["body"])

    def test_no_findings(self):
        self.assertIn("No findings.", payload([], DIFF, "abc")["body"])


if __name__ == "__main__":
    unittest.main()
