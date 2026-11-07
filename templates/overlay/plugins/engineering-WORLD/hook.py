#!/usr/bin/env python3
"""World overlay hook (SessionStart / SubagentStart): world rules and pointers, only in this world's repos.

overlay.json: {"world", "repos": [regex on `git remote get-url origin`], "tracker": {...},
               "rules": "rules.md", "lenses": "generated/linsen/index.json" (optional),
               "context": {"context/x.md": "when to read it"}}
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    try:
        cfg = json.load(open(os.path.join(ROOT, "overlay.json")))
        origin = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
        if not origin or not any(re.search(p, origin) for p in cfg.get("repos", [])):
            return
        parts = [f"# World: {cfg['world']}"]
        rules = os.path.join(ROOT, cfg.get("rules", "rules.md"))
        if os.path.exists(rules):
            parts.append(open(rules).read().strip())
        if cfg.get("tracker"):
            parts.append(f"Engineering tracker config: {os.path.join(ROOT, 'overlay.json')}")
        if cfg.get("lenses") and os.path.exists(os.path.join(ROOT, cfg["lenses"])):
            parts.append(f"Engineering lenses: {os.path.join(ROOT, cfg['lenses'])}")
        for path, when in (cfg.get("context") or {}).items():
            parts.append(f"World context, read {when}: {os.path.join(ROOT, path)}")
        text = "\n\n".join(parts)
    except Exception:
        return  # a broken hook must never stop work
    if sys.argv[1:2] == ["subagent"]:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": text}}))
    else:
        print(text)


if __name__ == "__main__":
    main()
