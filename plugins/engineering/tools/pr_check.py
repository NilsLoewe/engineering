#!/usr/bin/env python3
"""PR body check (rules 3+4): line budget, issue link, no copied spec.

    pr_check.py [--max-lines 15] [body.md]        # stdin if no file
    gh pr view 12 --json body -q .body | pr_check.py
Exit 0 = ok, 1 = findings printed.
"""
import argparse, re, sys

ISSUE_LINK = re.compile(r"github\.com/[\w.-]+/[\w.-]+/issues/\d+|monday\.com/boards/\d+/(pulses|items)/\d+"
                        r"|linear\.app/\S+/issue/|(?<![\w/])([\w.-]+/[\w.-]+)?#\d+\b")
SPEC_COPY = re.compile(r"\[engineering:spec\]|🤖 clarify · spec|^\s*[#*]*\s*(open questions|acceptance examples)\s*:", re.I | re.M)
EVIDENCE = re.compile(r"^\s*[#*]*\s*evidence\b", re.I | re.M)


def check(body, max_lines=15):
    lines = [l for l in body.splitlines() if l.strip() and not l.strip().startswith("<!--")]
    out = []
    if len(lines) > max_lines:
        out.append(f"body has {len(lines)} non-empty lines, budget is {max_lines}")
    if not ISSUE_LINK.search(body):
        out.append("no issue link (GitHub issue, owner/repo#n, Monday item or Linear issue)")
    if not EVIDENCE.search(body):
        out.append("no 'Evidence' section (one line per acceptance example)")
    if SPEC_COPY.search(body):
        out.append("body repeats the spec; link the issue instead")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--max-lines", type=int, default=15)
    a = ap.parse_args()
    body = open(a.file).read() if a.file else sys.stdin.read()
    out = check(body, a.max_lines)
    print("OK" if not out else "\n".join(f"- {x}" for x in out))
    sys.exit(1 if out else 0)


if __name__ == "__main__":
    main()
