#!/usr/bin/env python3
"""PreToolUse hook for browser work and UI pull requests. Denies three things:

1. Bash that starts the user's Google Chrome headless or with a debugging port. macOS sends every link
   to the running Chrome app; a hidden second instance swallows the user's clicks. Chrome Beta is fine.
2. chrome-devtools navigate_page/new_page to a host the current world lists in overlay.json
   `"browser": {"never": [<regex on the host>]}` or in the repo's `.engineering.json`.
3. A UI pull request leaving draft (`gh pr ready`, or `gh pr create` without --draft) when its body has
   no `Screens:` line. UI files are the globs of the core lens `ux`.

Errors of the hook itself go to stderr and never block work.
"""
import fnmatch, glob, json, os, re, shlex, subprocess, sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pr_check import SCREENS  # one definition of the Screens line for skill, check and hook

CHROME = re.compile(r"Google Chrome(?! Beta)(\.app|[\"'\s]|$)")
HEADLESS = re.compile(r"--headless|--remote-debugging-(port|pipe)")
PR_CMD = re.compile(r"\bgh\s+pr\s+(ready|create)\b([^;&|]*)")


def chrome_start(cmd):
    if CHROME.search(cmd) and HEADLESS.search(cmd):
        return ("Do not start Google Chrome headless or with a debugging port: macOS routes the user's links "
                "into it. Use the chrome-devtools MCP (Chrome Beta) or Playwright's own Chromium.")
    return None


def blocked_host(url, patterns):
    host = urlparse(url or "").hostname or ""
    for p in patterns:
        if host and re.search(p, host):
            return f"{host} is listed under browser.never for this world (production). Use local or staging."
    return None


def ux_globs(index=os.path.join(HERE, "..", "generated", "linsen", "index.json")):
    lenses = json.load(open(index))["linsen"]
    return next(l["pfade"] for l in lenses if l["name"] == "ux")


def ui_files(files, globs):
    return [f for f in files if any(fnmatch.fnmatch(f, g) for g in globs)]


def pr_gate(files, body, globs):
    ui = ui_files(files, globs)
    if not ui or SCREENS.search(body or ""):
        return None
    return (f"This PR changes UI files ({', '.join(ui[:3])}{' …' if len(ui) > 3 else ''}) and its body has no "
            "'Screens:' line. Run skill engineering:ui-check (mode change) and add the line, or write "
            "'Screens: n/a: <why nothing visible changed>'. Draft PRs need no Screens line.")


def parse_pr(cmd):
    """('ready'|'create', argv) for a gh pr command that would leave draft, else None."""
    m = PR_CMD.search(cmd)
    if not m:
        return None
    argv = shlex.split(m.group(2))
    if m.group(1) == "ready" and "--undo" in argv:
        return None
    if m.group(1) == "create" and ({"--draft", "-d"} & set(argv)):
        return None
    return m.group(1), argv


def opt(argv, *names):
    for i, a in enumerate(argv):
        for n in names:
            if a == n and i + 1 < len(argv):
                return argv[i + 1]
            if a.startswith(n + "="):
                return a.split("=", 1)[1]
    return None


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout


def pr_facts(kind, argv, cwd):
    """(changed files, body) of the PR the command acts on."""
    repo = opt(argv, "-R", "--repo")
    if kind == "ready":
        ref = next((a for a in argv if not a.startswith("-") and a != repo), None)
        d = json.loads(run(["gh", "pr", "view", *([ref] if ref else []), *(["-R", repo] if repo else []),
                            "--json", "files,body"], cwd))
        return [f["path"] for f in d.get("files", [])], d.get("body", "")
    base = opt(argv, "-B", "--base")
    base = f"origin/{base}" if base else "origin/HEAD"
    files = run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd).split()
    path = opt(argv, "-F", "--body-file")
    body = open(os.path.join(cwd, path)).read() if path and path != "-" else opt(argv, "-b", "--body") or ""
    return files, body


def world_never(cwd):
    """browser.never of every installed overlay whose repos match this repo, plus .engineering.json."""
    origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    pats = []
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    local = os.path.join(top, ".engineering.json") if top else ""
    if local and os.path.exists(local):
        pats += json.load(open(local)).get("browser", {}).get("never", [])
    if not origin:
        return pats
    conf = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    installed = json.load(open(os.path.join(conf, "plugins", "installed_plugins.json"))).get("plugins", {})
    for entries in installed.values():
        for e in entries:
            for cfg in glob.glob(os.path.join(e.get("installPath", ""), "**", "overlay.json"), recursive=True):
                c = json.load(open(cfg))
                if any(re.search(p, origin) for p in c.get("repos", [])):
                    pats += c.get("browser", {}).get("never", [])
    return pats


def verdict(tool, inp, cwd):
    if tool == "Bash":
        cmd = inp.get("command", "")
        why = chrome_start(cmd)
        if why:
            return why
        pr = parse_pr(cmd)
        if pr:
            return pr_gate(*pr_facts(*pr, cwd), ux_globs())
        return None
    if tool.startswith("mcp__chrome-devtools__") and inp.get("url"):
        return blocked_host(inp["url"], world_never(cwd))
    return None


def main():
    try:
        d = json.load(sys.stdin)
        why = verdict(d.get("tool_name", ""), d.get("tool_input", {}) or {}, d.get("cwd") or os.getcwd())
    except Exception as e:
        print(f"hook_browser: {e}", file=sys.stderr)  # a broken hook must never stop work, but it shows
        return
    if why:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny", "permissionDecisionReason": why}}))


if __name__ == "__main__":
    main()
