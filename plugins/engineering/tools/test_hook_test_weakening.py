#!/usr/bin/env python3
"""Self-test for hook_test_weakening.py."""
import os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(__file__))
from hook_test_weakening import verdict  # noqa: E402


class Weakening(unittest.TestCase):
    def test_removed_expectation_asks(self):
        v = verdict("Edit", {"file_path": "spec/models/alarm_spec.rb",
                             "old_string": "expect(a).to eq 1\nexpect(b).to eq 2", "new_string": "expect(a).to eq 1"})
        self.assertIn("removes 1 assertion", v)

    def test_added_skip_asks(self):
        v = verdict("Edit", {"file_path": "src/apps/alarm.test.tsx", "old_string": "it('x', () => {",
                             "new_string": "it.skip('x', () => {"})
        self.assertIn("skip", v)

    def test_more_assertions_pass(self):
        self.assertIsNone(verdict("Edit", {"file_path": "spec/a_spec.rb", "old_string": "expect(a).to eq 1",
                                           "new_string": "expect(a).to eq 1\nexpect(b).to eq 2"}))

    def test_non_test_file_pass(self):
        self.assertIsNone(verdict("Edit", {"file_path": "app/models/alarm.rb", "old_string": "expect(", "new_string": ""}))

    def test_write_compares_with_disk(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "spec", "x_spec.rb"); os.makedirs(os.path.dirname(p))
            open(p, "w").write("expect(a).to be true\nexpect(b).to be true\n")
            self.assertIn("removes", verdict("Write", {"file_path": p, "content": "expect(a).to be true\n"}))
            self.assertIsNone(verdict("Write", {"file_path": os.path.join(d, "spec", "new_spec.rb"), "content": "x"}))

    def test_commented_lines_ignored(self):
        self.assertIsNone(verdict("Edit", {"file_path": "spec/a_spec.rb", "old_string": "# expect(a)\nexpect(b)",
                                           "new_string": "expect(b)"}))


if __name__ == "__main__":
    unittest.main()
