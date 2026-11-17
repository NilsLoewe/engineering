#!/usr/bin/env python3
"""Self-test for hook.py: python3 test_hook.py"""
import json, os, tempfile

from hook import text_for


def world(root, folder, name, repos, invariants=None, rules=None):
    d = os.path.join(root, folder)
    os.makedirs(d, exist_ok=True)
    json.dump({"world": name, "repos": repos, "context": {"context/p.md": "always"}}, open(os.path.join(d, "overlay.json"), "w"))
    if invariants:
        open(os.path.join(d, "invariants.md"), "w").write(invariants)
    if rules:
        open(os.path.join(d, "rules.md"), "w").write(rules)


def test():
    with tempfile.TemporaryDirectory() as root:
        world(root, ".", "Single", ["github\\.com[:/]acme/"], "INV-1", "RULE-1")
        t = text_for("git@github.com:acme/app.git", root)
        assert t.startswith("# World: Single") and t.index("INV-1") < t.index("RULE-1")  # invariants first
        assert os.path.join(root, "context/p.md") in t  # context path resolves next to its overlay.json
        assert text_for("git@github.com:other/app.git", root) == ""
        assert text_for("", root) == ""

    with tempfile.TemporaryDirectory() as root:  # many worlds in one plugin, one folder each
        world(root, "kunden/acme", "Acme", ["acme/"], rules="ACME-RULE")
        world(root, "kunden/beta", "Beta", ["beta/"], rules="BETA-RULE")
        world(root, "kunden/_template", "Template", [])
        t = text_for("git@github.com:acme/shop.git", root)
        assert "# World: Acme" in t and "ACME-RULE" in t and "BETA-RULE" not in t and "Template" not in t
        assert os.path.join(root, "kunden/acme/context/p.md") in t
        open(os.path.join(root, "kunden/beta/overlay.json"), "w").write("{broken")
        t = text_for("git@github.com:acme/shop.git", root)
        assert "ACME-RULE" in t and "World config broken" in t  # a broken neighbour is reported, not fatal


if __name__ == "__main__":
    test()
    print("ok")
