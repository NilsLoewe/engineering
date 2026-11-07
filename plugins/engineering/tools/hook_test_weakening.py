#!/usr/bin/env python3
"""PreToolUse hook (rule hook-no-test-weakening): asks before an edit removes assertions or skips tests.

Reads the hook JSON on stdin. For Edit/MultiEdit/Write on a spec or test file it compares the old and
the new text. Fewer assertions or more skip markers -> permissionDecision "ask" with the reason, so a
human decides. Everything else passes silently. Never blocks on its own errors.
"""
import json, os, re, sys

TEST_FILE = re.compile(r"(^|/)(spec|test|tests|__tests__)/|(_spec\.rb|_test\.rb|\.(test|spec)\.[jt]sx?)$")
ASSERT = re.compile(r"\bexpect\s*[({]|\bassert\w*\s*[ (]|\.should\b|\bis_expected\b")
SKIP = re.compile(r"\b(xit|xdescribe|xcontext|xspecify|pending|skip)\b|\b(it|test|describe)\.(skip|todo)\b")


def count(text, rx):
    return sum(len(rx.findall(line)) for line in text.splitlines() if not line.lstrip().startswith(("#", "//")))


def pairs(tool, inp):
    if tool == "Edit":
        return [(inp.get("old_string", ""), inp.get("new_string", ""))]
    if tool == "MultiEdit":
        return [(e.get("old_string", ""), e.get("new_string", "")) for e in inp.get("edits", [])]
    if tool == "Write":
        try:
            old = open(inp.get("file_path", "")).read()
        except OSError:
            old = ""  # new file: nothing to weaken
        return [(old, inp.get("content", ""))]
    return []


def verdict(tool, inp):
    path = inp.get("file_path", "")
    if not TEST_FILE.search(path):
        return None
    old = "\n".join(o for o, _ in pairs(tool, inp))
    new = "\n".join(n for _, n in pairs(tool, inp))
    reasons = []
    a0, a1 = count(old, ASSERT), count(new, ASSERT)
    s0, s1 = count(old, SKIP), count(new, SKIP)
    if a1 < a0:
        reasons.append(f"removes {a0 - a1} assertion(s)")
    if s1 > s0:
        reasons.append(f"adds {s1 - s0} skip/pending marker(s)")
    if not reasons:
        return None
    return (f"{os.path.basename(path)}: this edit {' and '.join(reasons)}. Rule hook-no-test-weakening: "
            "fix the code instead of the test, or say why the assertion is wrong.")


def main():
    try:
        d = json.load(sys.stdin)
        why = verdict(d.get("tool_name", ""), d.get("tool_input", {}) or {})
    except Exception:
        return  # a broken hook must never stop work
    if why:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "ask", "permissionDecisionReason": why}}))


if __name__ == "__main__":
    main()
