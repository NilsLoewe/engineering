#!/usr/bin/env python3
"""Offline self-test for feedback_collect.py: gh and the tracker are faked."""
import json, os, sys, unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import feedback_collect as fc  # noqa: E402

PR = {"html_url": "https://github.com/o/r/pull/9", "title": "Parse mails", "state": "open", "user": {"login": "ada"},
      "created_at": "2026-10-12T20:00:00Z", "head": {"ref": "feat"}, "base": {"ref": "release"},
      "body": "Task: https://example.monday.com/boards/100/pulses/200300500 (mail)"}


def c(id, login, at, body, reply=None, path="a.rb"):
    return {"id": id, "in_reply_to_id": reply, "user": {"login": login}, "created_at": at, "body": body,
            "html_url": f"https://github.com/o/r/pull/9#discussion_r{id}", "path": path, "line": 3}


PAGES = {
    "repos/o/r/pulls/9/comments": [[c(1, "alex", "2026-10-14T10:00:00Z", "bug: sender"),
                                    c(3, "ada", "2026-10-14T12:00:00Z", "Fixed in abc1234: sender from <...>", reply=1)],
                                   [c(2, "ada", "2026-10-13T09:00:00Z", "🤖 **review-agent** · minor"),
                                    c(4, "Copilot", "2026-10-15T09:00:00Z", "CR in header")]],
    "repos/o/r/pulls/9/reviews": [[{"user": {"login": "alex"}, "state": "CHANGES_REQUESTED", "body": "main point",
                                    "submitted_at": "2026-10-14T10:01:00Z", "html_url": "u"},
                                   {"user": {"login": "alex"}, "state": "COMMENTED", "body": "", "submitted_at": "x", "html_url": "u"}]],
    "repos/o/r/issues/9/comments": [[{"user": {"login": "linear[bot]"}, "created_at": "2026-10-12T21:00:00Z",
                                      "body": "linked", "html_url": "u"}]],
}

TICKET = {"url": "https://example.monday.com/boards/100/pulses/200300500", "title": "Mail channel",
          "state": None, "raw_state": {"status": "QA / Test"}, "body": "go-live",
          "comments": [{"author": "Bob", "created_at": "2026-10-07T07:17:41.000Z", "body": "before the PR"},
                       {"author": "Bob", "created_at": "2026-11-06T15:36:55.000Z", "body": "which mailbox?", "reply_to": "5"}]}


def sh(cmd, stdin=None):
    path = cmd[2]
    return json.dumps(PAGES[path] if "--slurp" in cmd else PR)


class Collect(unittest.TestCase):
    def setUp(self):
        self.read = []
        p = mock.patch.object(fc.tracker, "sh", sh)
        p.start()
        self.addCleanup(p.stop)

    def run_collect(self, *args):
        return fc.collect(*args, read=lambda ref, cfg: self.read.append(ref) or TICKET)

    def test_threads_grouped_and_kinds(self):
        out = self.run_collect("o/r#9")
        self.assertEqual([t["id"] for t in out["threads"]], [2, 1, 4])  # oldest first
        human = out["threads"][1]
        self.assertEqual((human["kind"], human["open"], human["replies"][0]["body"][:8]), ("human", False, "Fixed in"))
        self.assertEqual([t["kind"] for t in out["threads"]], ["agent", "human", "bot"])
        self.assertTrue(out["threads"][2]["open"])  # nobody answered Copilot

    def test_reviews_without_body_dropped(self):
        out = self.run_collect("https://github.com/o/r/pull/9")
        self.assertEqual([r["body"] for r in out["reviews"]], ["main point"])
        self.assertEqual(out["pr_comments"][0]["kind"], "bot")

    def test_ticket_from_pr_body_and_since_pr(self):
        out = self.run_collect("o/r#9")
        self.assertEqual(self.read, ["https://example.monday.com/boards/100/pulses/200300500"])
        self.assertEqual([x["body"] for x in out["ticket"]["comments"]], ["which mailbox?"])

    def test_explicit_ticket_wins(self):
        self.run_collect("o/r#9", "200300500")
        self.assertEqual(self.read, ["200300500"])

    def test_bad_ref(self):
        with self.assertRaises(SystemExit):
            self.run_collect("9")


if __name__ == "__main__":
    unittest.main()
