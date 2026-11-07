#!/usr/bin/env python3
"""Offline self-test for tracker.py: gh and the Monday API are faked."""
import io, json, os, sys, tempfile, unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
os.environ["TRACKER_MARKER"] = ""  # Kennzeichnung in den übrigen Tests aus
import tracker  # noqa: E402

MCFG = {"monday": {"states": {"idea": {"status": "To Do"}, "clarifying": {"status": "Refinement"},
                              "ready": {"status": "Ready"}, "in-progress": {"status": "In Progress"},
                              "review": {"status": "Code Review"}, "done": {"status": "Done"}},
                   "also": {"ready": {"status_1__1": "Refined"}}}}

GH_ISSUE = {"title": "Export CSV", "body": "Need export", "state": "OPEN", "url": "https://github.com/o/r/issues/7",
            "labels": [{"name": "status:clarifying"}, {"name": "bug"}],
            "comments": [{"author": {"login": "ada"}, "createdAt": "2026-11-06T10:00:00Z", "body": "Linked: https://x/pr/1"}]}

MONDAY_ITEM = {"items": [{"id": "200300400", "name": "Export intervention times",
                          "created_at": "2026-09-01T10:00:00Z", "url": "https://example.monday.com/boards/100/pulses/200300400",
                          "board": {"id": "100"},
                          "column_values": [{"id": "status", "text": "To Do"}, {"id": "status_1__1", "text": "Refined"}],
                          "updates": [
                              {"id": "2", "created_at": "2026-09-02T10:00:00Z", "text_body": "How many types?",
                               "creator": {"name": "Dev"}, "replies": [{"created_at": "2026-09-02T11:00:00Z",
                                                                         "text_body": "Several", "creator": {"name": "PO"}}]},
                              {"id": "1", "created_at": "2026-09-01T10:30:00Z", "text_body": "tbd how we configure",
                               "creator": {"name": "PO"}, "replies": []}]}]}


class Refs(unittest.TestCase):
    def test_parse(self):
        P = tracker.parse_ref
        self.assertEqual(P("https://github.com/o/r/issues/7"), ("github", ("o/r", "7")))
        self.assertEqual(P("o/r#7"), ("github", ("o/r", "7")))
        self.assertEqual(P("#7"), ("github", (None, "7")))
        self.assertEqual(P("https://example.monday.com/boards/100/pulses/200300400"), ("monday", "200300400"))
        self.assertEqual(P("200300400"), ("monday", "200300400"))
        with self.assertRaises(SystemExit):
            P("7")  # ambiguous: GitHub numbers need '#'


class GitHub(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def sh(cmd, stdin=None):
            self.calls.append((cmd, stdin))
            if cmd[:3] == ["gh", "label", "list"]:
                return json.dumps([{"name": "status:clarifying"}, {"name": "status:ready"}])
            return json.dumps(GH_ISSUE) if cmd[:3] == ["gh", "issue", "view"] else ""
        p = mock.patch.object(tracker, "sh", sh)
        p.start()
        self.addCleanup(p.stop)

    def test_read_maps_label_to_state(self):
        r = tracker.read("o/r#7", {})
        self.assertEqual((r["state"], r["raw_state"], r["comments"][0]["author"]), ("clarifying", ["status:clarifying"], "ada"))

    def test_config_overrides_label(self):
        r = tracker.read("o/r#7", {"github": {"states": {"clarifying": "bug"}}})
        self.assertEqual(r["state"], "clarifying")

    def test_set_state_swaps_status_labels(self):
        tracker.set_state("o/r#7", "ready", {}, dry=False)
        edit = self.calls[-1][0]
        self.assertIn("status:ready", edit)
        self.assertEqual(edit[edit.index("--remove-label") + 1], "status:clarifying")
        self.assertNotIn("bug", edit)

    def test_label_created_only_if_missing(self):
        self.assertEqual(len(tracker.set_state("o/r#7", "ready", {}, dry=True)["cmds"]), 1)
        plan = tracker.set_state("o/r#7", "review", {}, dry=True)["cmds"]
        self.assertEqual(plan[0][:4], ["gh", "label", "create", "status:review"])
        self.assertNotIn("--force", plan[0])

    def test_dry_run_writes_nothing(self):
        out = tracker.comment("o/r#7", "hello", dry=True)
        plan = tracker.set_state("o/r#7", "ready", {}, dry=True)
        self.assertTrue(out["dry_run"])
        self.assertIn("status:clarifying", plan["cmds"][-1])  # dry-run still reads, so the plan is exact
        self.assertTrue(all(c[0][1] in ("issue", "label") and c[0][2] in ("view", "list") for c in self.calls))

    def test_env_forces_dry_run(self):
        with mock.patch.dict(os.environ, {"TRACKER_DRY_RUN": "1"}), redirect_stdout(io.StringIO()) as o:
            tracker.main(["comment", "o/r#7", "--body", "x"])
        self.assertTrue(json.loads(o.getvalue())["dry_run"])
        self.assertEqual(self.calls, [])

    def test_keyed_comment_patches_existing(self):
        def sh(cmd, stdin=None):
            self.calls.append((cmd, stdin))
            if cmd[:2] == ["gh", "api"] and cmd[2].endswith("/comments"):
                return json.dumps([{"id": 5, "body": "🤖 clarify · spec · x"}])
            return ""
        with mock.patch.object(tracker, "sh", sh):
            out = tracker.comment("o/r#7", "new", dry=True, key="spec")
        self.assertEqual(out["cmd"][:4], ["gh", "api", "-X", "PATCH"])
        self.assertIn("repos/o/r/issues/comments/5", out["cmd"])

    def test_assign_replaces_assignees(self):
        def sh(cmd, stdin=None):
            self.calls.append((cmd, stdin))
            return json.dumps({"assignees": [{"login": "ada"}]}) if cmd[:3] == ["gh", "issue", "view"] else ""
        with mock.patch.object(tracker, "sh", sh):
            out = tracker.assign("o/r#7", "bob", {}, dry=True)
        self.assertEqual(out["cmd"][-4:], ["--add-assignee", "bob", "--remove-assignee", "ada"])

    def test_link_is_idempotent(self):
        self.assertEqual(tracker.link("o/r#7", "https://x/pr/1", {}, dry=False)["skipped"], "already linked")
        tracker.link("o/r#7", "https://x/pr/2", {}, dry=False)
        self.assertEqual(self.calls[-1][1], "Linked: https://x/pr/2")


class Monday(unittest.TestCase):
    def setUp(self):
        self.queries = []

        def gql(q, v=None):
            self.queries.append((q, v))
            if q.lstrip().startswith("mutation"):
                return {"create_update": {"id": "99"}, "change_multiple_column_values": {"id": "1"}}
            return MONDAY_ITEM
        p = mock.patch.object(tracker, "gql", gql)
        p.start()
        self.addCleanup(p.stop)

    def test_read_first_update_is_description(self):
        r = tracker.read("200300400", MCFG)
        self.assertEqual(r["body"], "tbd how we configure")
        self.assertEqual([c["body"] for c in r["comments"]], ["How many types?", "Several"])
        self.assertEqual(r["state"], "idea")  # status To Do; the old Refinement column is not read

    def test_state_read_from_status_only(self):
        item = json.loads(json.dumps(MONDAY_ITEM))
        with mock.patch.object(tracker, "gql", lambda q, v=None: item):
            for label, state in [("To Do", "idea"), ("Refinement", "clarifying"),
                                 ("Ready", "ready"), ("QA / Test", None)]:
                item["items"][0]["column_values"][0]["text"] = label
                self.assertEqual(tracker.read("200300400", MCFG)["state"], state, label)

    def test_ready_also_sets_old_refinement_column(self):
        tracker.set_state("200300400", "ready", MCFG, dry=False)
        self.assertEqual(json.loads(self.queries[-1][1]["v"]),
                         {"status": {"label": "Ready"}, "status_1__1": {"label": "Refined"}})

    def test_config_after_the_operation(self):
        with tempfile.TemporaryDirectory() as d:
            ov = os.path.join(d, "o.json"); open(ov, "w").write(json.dumps({"tracker": MCFG}))
            out = io.StringIO()
            with mock.patch.object(tracker, "read", lambda ref, cfg: {"states": sorted(cfg["monday"]["states"])}), redirect_stdout(out):
                tracker.main(["read", "200300400", "--config", ov])
        self.assertIn("ready", out.getvalue())

    def test_monday_without_config_fails(self):
        with self.assertRaises(SystemExit):
            tracker.read("200300400", {})

    def test_config_from_overlay_file_and_repo_file(self):
        with tempfile.TemporaryDirectory() as d:
            ov = os.path.join(d, "overlay.json"); open(ov, "w").write(json.dumps({"tracker": MCFG}))
            open(os.path.join(d, ".engineering.json"), "w").write(json.dumps({"tracker": {"monday": {"states": {"ready": {"status": "Go"}}}}}))
            cfg = tracker.load_config(start=d, explicit=ov)
        self.assertEqual(cfg["monday"]["states"]["ready"], {"status": "Go"})
        self.assertEqual(cfg["monday"]["states"]["idea"], {"status": "To Do"})

    def test_assign_by_name_or_email(self):
        users = {"users": [{"id": "1", "name": "Ada Admin", "email": "ada@x", "enabled": True},
                           {"id": "2", "name": "Bob Admin", "email": "bob@x", "enabled": True}]}
        def gql(q, v=None):
            self.queries.append((q, v))
            return users if "users" in q else {"items": [{"board": {"id": "100"}}]}
        with mock.patch.object(tracker, "gql", gql):
            out = tracker.assign("200300400", "bob@x", MCFG, dry=True)
            self.assertEqual(json.loads(out["variables"]["v"]), {"personsAndTeams": [{"id": 2, "kind": "person"}]})
            self.assertEqual(out["variables"]["c"], "person")
            with self.assertRaises(SystemExit):
                tracker.assign("200300400", "admin", MCFG, dry=True)  # matches both names

    def test_set_state_mutation(self):
        tracker.set_state("200300400", "in-progress", MCFG, dry=False)
        q, v = self.queries[-1]
        self.assertIn("change_multiple_column_values", q)
        self.assertEqual(json.loads(v["v"]), {"status": {"label": "In Progress"}})
        self.assertEqual(v["b"], "100")

    def test_comment_html_and_dry_run(self):
        out = tracker.comment("200300400", "a<b\nc", dry=True)
        self.assertEqual(out["variables"]["b"], "<p>a&lt;b</p><p>c</p>")
        self.assertEqual(self.queries, [])

    def test_html_lists_and_bold(self):
        h = tracker.to_html("**Goal:** x\n1. a `b`\n2. c\n\n- d\ntail")
        self.assertEqual(h, "<p><b>Goal:</b> x</p><p>1. a <i>b</i></p><p>2. c</p><ul><li>d</li></ul><p>tail</p>")

    def test_keyed_comment_edits_existing(self):
        item = {"items": [{"updates": [{"id": "7", "text_body": "🤖 clarify · spec · 06.11.2026 17:00\n\nold"}]}]}
        with mock.patch.object(tracker, "gql", lambda q, v=None: self.queries.append((q, v)) or
                               (item if q.startswith("query") else {"edit_update": {"id": "7"}})):
            out = tracker.comment("200300400", "new", dry=False, key="spec")
            self.assertEqual(out, {"ok": True, "update_id": "7", "edited": True})
            self.assertIn("edit_update", self.queries[-1][0])
            self.assertTrue(self.queries[-1][1]["b"].startswith("<p>🤖 clarify · spec · "))
            out = tracker.comment("200300400", "q", dry=True, key="questions")
            self.assertIn("create_update", out["mutation"])

    def test_token_from_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as t:
            t.write("OTHER=1\nexport monday_token='abc'\n")
        f = t.name
        self.addCleanup(os.remove, f)
        with mock.patch.dict(os.environ, {"MONDAY_TOKEN": "", "MONDAY_TOKEN_FILE": f}):
            self.assertEqual(tracker.monday_token(), "abc")



class Marker(unittest.TestCase):
    def test_marker_prefixed_once(self):
        seen = []
        with mock.patch.object(tracker, "MARKER", "🤖 m"), \
             mock.patch.object(tracker, "monday_comment", lambda i, b, d, h=None: seen.append(b) or {}):
            tracker.comment("200300401", "body", True)
            tracker.comment("200300401", "🤖 m\n\nbody", True)
        self.assertEqual(seen, ["🤖 m\n\nbody", "🤖 m\n\nbody"])

if __name__ == "__main__":
    unittest.main()
