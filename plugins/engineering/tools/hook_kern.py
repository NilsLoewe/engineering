#!/usr/bin/env python3
"""Gives the core rules to every session and every subagent (SessionStart / SubagentStart hook).

SessionStart: plain text on stdout, only inside a git work tree.
SubagentStart (arg "subagent"): JSON additionalContext, because subagents do not get SessionStart output.
"""
import json, os, subprocess, sys

KERN = os.path.join(os.path.dirname(__file__), "..", "generated", "kern.md")


def main():
    try:
        if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode:
            return
        text = open(KERN).read()
    except Exception:
        return  # a broken hook must never stop work
    if sys.argv[1:2] == ["subagent"]:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": text}}))
    else:
        print(text)


if __name__ == "__main__":
    main()
