#!/usr/bin/env python3
"""World overlay hook (SessionStart / SubagentStart): world rules and pointers, only in this world's repos.

One plugin can hold one world (overlay.json next to this file) or many (one folder per world,
e.g. kunden/<name>/overlay.json). Every world whose `repos` match `git remote get-url origin` is printed.

overlay.json: {"world", "repos": [regex on `git remote get-url origin`], "tracker": {...},
               "invariants": "invariants.md", "rules": "rules.md",
               "lenses": "generated/linsen/index.json" (optional),
               "context": {"context/x.md": "when to read it"}}
Paths in overlay.json are relative to the folder that holds it.
"""
import glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def world_text(cfg_path, origin):
    base = os.path.dirname(cfg_path)
    cfg = json.load(open(cfg_path))
    if not any(re.search(p, origin) for p in cfg.get("repos", [])):
        return None
    parts = [f"# World: {cfg['world']}"]
    for key, default in (("invariants", "invariants.md"), ("rules", "rules.md")):
        path = os.path.join(base, cfg.get(key, default))
        if os.path.exists(path):
            parts.append(open(path).read().strip())
    if cfg.get("tracker"):
        parts.append(f"Engineering tracker config: {cfg_path}")
    if cfg.get("lenses") and os.path.exists(os.path.join(base, cfg["lenses"])):
        parts.append(f"Engineering lenses: {os.path.join(base, cfg['lenses'])}")
    for path, when in (cfg.get("context") or {}).items():
        parts.append(f"World context, read {when}: {os.path.join(base, path)}")
    return "\n\n".join(parts)


def text_for(origin, root=ROOT):
    if not origin:
        return ""
    texts = []
    for cfg_path in sorted(glob.glob(os.path.join(root, "**", "overlay.json"), recursive=True)):
        try:
            t = world_text(cfg_path, origin)
        except Exception as e:  # one broken world must not hide the others, but it must be visible
            t = f"# World config broken: {cfg_path}: {e}"
        if t:
            texts.append(t)
    return "\n\n".join(texts)


def main():
    try:
        origin = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
        text = text_for(origin)
    except Exception:
        return  # a broken hook must never stop work
    if not text:
        return
    if sys.argv[1:2] == ["subagent"]:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": text}}))
    else:
        print(text)


if __name__ == "__main__":
    main()
