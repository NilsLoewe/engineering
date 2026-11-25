#!/usr/bin/env python3
"""Self-test for hook_browser.py: python3 test_hook_browser.py"""
import json, os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_browser as h  # noqa: E402

GLOBS = h.ux_globs()


class Chrome(unittest.TestCase):
    def test_user_chrome_headless_denied(self):
        for cmd in ['"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --remote-debugging-port=9333',
                    'open -a "Google Chrome" --args --remote-debugging-port=9222',
                    "open -a 'Google Chrome' --args --headless"]:
            self.assertIsNotNone(h.chrome_start(cmd), cmd)

    def test_beta_and_plain_open_allowed(self):
        for cmd in ['"/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta" --headless=new',
                    'open -a "Google Chrome" https://example.org', "npx playwright test --headed"]:
            self.assertIsNone(h.chrome_start(cmd), cmd)


class Hosts(unittest.TestCase):
    def test_never_host(self):
        self.assertIsNotNone(h.blocked_host("https://app.fump.io/contacts", [r"^app\.fump\.io$"]))
        self.assertIsNone(h.blocked_host("https://staging.fump.io/", [r"^app\.fump\.io$"]))
        self.assertIsNone(h.blocked_host("about:blank", [r"^app\.fump\.io$"]))

    def test_world_never_from_repo_config(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            json.dump({"browser": {"never": [r"^prod\.example$"]}}, open(os.path.join(d, ".engineering.json"), "w"))
            os.environ["CLAUDE_CONFIG_DIR"] = d  # no installed plugins, only the repo config
            self.assertEqual(h.world_never(d), [r"^prod\.example$"])
            out = h.verdict("mcp__chrome-devtools__new_page", {"url": "https://prod.example/x"}, d)
            self.assertIn("browser.never", out)


class PRGate(unittest.TestCase):
    def test_ui_pr_needs_screens(self):
        self.assertIn("Screens:", h.pr_gate(["app/views/contacts/index.html.erb"], "Closes #1", GLOBS))
        self.assertIsNone(h.pr_gate(["src/Page.tsx"], "Closes #1\nScreens: n/a: type only", GLOBS))
        self.assertIsNone(h.pr_gate(["app/models/contact.rb"], "Closes #1", GLOBS))

    def test_which_commands_leave_draft(self):
        self.assertEqual(h.parse_pr("cd x && gh pr ready 12 -R o/r")[0], "ready")
        self.assertIsNone(h.parse_pr("gh pr ready 12 --undo"))
        self.assertIsNone(h.parse_pr("gh pr create --draft --body-file b.md"))
        self.assertEqual(h.parse_pr("gh pr create --body-file b.md --title x")[0], "create")
        self.assertIsNone(h.parse_pr("gh pr view 12"))

    def test_create_reads_body_file_and_diff(self):
        with tempfile.TemporaryDirectory() as d:
            g = lambda *a: subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)
            g("init", "-q", "-b", "main"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
            g("commit", "-q", "--allow-empty", "-m", "base"); g("update-ref", "refs/remotes/origin/main", "HEAD")
            open(os.path.join(d, "Page.tsx"), "w").write("<A/>\n"); g("add", "."); g("commit", "-q", "-m", "ui")
            open(os.path.join(d, "b.md"), "w").write("Closes #1\n")
            files, body = h.pr_facts("create", ["--base", "main", "--body-file", "b.md"], d)
            self.assertEqual((files, body), (["Page.tsx"], "Closes #1\n"))
            self.assertIn("Screens:", h.verdict("Bash", {"command": "gh pr create --base main --body-file b.md"}, d))


if __name__ == "__main__":
    unittest.main()
