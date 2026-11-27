#!/usr/bin/env python3
"""PR body check (rules 3+4): line budget, issue link, evidence, deploy line, no copied spec.

    pr_check.py [--max-lines 15] [--ui] [--template T.md] [body.md]   # stdin if no file
    gh pr view 12 --json body -q .body | pr_check.py
--template: the repo's PR template; every section it does not mark optional must be in the body.
Exit 0 = ok, 1 = findings printed.
"""
import argparse, re, sys

ISSUE_LINK = re.compile(r"github\.com/[\w.-]+/[\w.-]+/issues/\d+|monday\.com/boards/\d+/(pulses|items)/\d+"
                        r"|linear\.app/\S+/issue/|(?<![\w/])([\w.-]+/[\w.-]+)?#\d+\b")
SPEC_COPY = re.compile(r"\[engineering:spec\]|🤖 clarify · spec|^\s*[#*]*\s*(open questions|acceptance examples)\s*:", re.I | re.M)
EVIDENCE = re.compile(r"^\s*[#*]*\s*evidence\b", re.I | re.M)
# Deploy order was the most frequent PR-text point human reviewers still raised (SEON, 2026-11).
DEPLOY = re.compile(r"^\s*[#*-]*\s*deploy\b[^:\n]{0,20}:", re.I | re.M)
# A UI PR names the screens and states it walked through (skill ui-check); hook_browser enforces it at ready.
SCREENS = re.compile(r"^\s*[#*-]*\s*screens\s*:\s*\S", re.I | re.M)
# Headings, rules and table separators are the template's frame, not content: they do not count against the budget.
FRAME = re.compile(r"^\s*(#{1,6}\s|-{3,}\s*$|\|[\s:|-]*\|\s*$|<!--)")
HEADING = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$", re.M)
OPTIONAL = re.compile(r"\b(delete|remove)\b[^>]{0,60}\b(if|when)\b", re.I)


def template_sections(template):
    """Template headings the body must keep; a section whose comment says "delete/remove … if …" is optional."""
    parts = HEADING.split(template)[1:]
    return [h for h, text in zip(parts[::2], parts[1::2]) if not OPTIONAL.search(text)]


def check(body, max_lines=15, ui=False, template=None):
    lines = [l for l in body.splitlines() if l.strip() and not FRAME.match(l)]
    out = []
    if template:
        have = {h.lower() for h in HEADING.findall(body)}
        gone = [h for h in template_sections(template) if h.lower() not in have]
        if gone:
            out.append("repo PR template section(s) missing: " + ", ".join(gone))
    if len(lines) > max_lines:
        out.append(f"body has {len(lines)} non-empty lines, budget is {max_lines}")
    if not ISSUE_LINK.search(body):
        out.append("no issue link (GitHub issue, owner/repo#n, Monday item or Linear issue)")
    if not EVIDENCE.search(body):
        out.append("no 'Evidence' section (one line per acceptance example)")
    if not DEPLOY.search(body):
        out.append("no 'Deploy:' line (order of migrations, flags and other repos, or 'independent')")
    if ui and not SCREENS.search(body):
        out.append("UI change without a 'Screens:' line (skill ui-check; or 'Screens: n/a: <why>')")
    if SPEC_COPY.search(body):
        out.append("body repeats the spec; link the issue instead")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--max-lines", type=int, default=15)
    ap.add_argument("--ui", action="store_true", help="the diff changes files of the ux lens")
    ap.add_argument("--template", help="the repo's pull request template")
    a = ap.parse_args()
    body = open(a.file).read() if a.file else sys.stdin.read()
    out = check(body, a.max_lines, a.ui, open(a.template).read() if a.template else None)
    print("OK" if not out else "\n".join(f"- {x}" for x in out))
    sys.exit(1 if out else 0)


if __name__ == "__main__":
    main()
