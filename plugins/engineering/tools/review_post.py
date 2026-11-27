#!/usr/bin/env python3
"""Posts one GitHub review from a findings file; findings that GitHub cannot anchor go into the body.

    review_post.py <owner/repo> <pr> <findings.json> [--dry-run]

findings.json: [{"path", "line", "severity": "blocker|major|minor", "rule", "text"}]
           or {"findings": [...], "brief": {"check": ["..."], "skip": ["..."]}}
brief.check: what only the human reviewer can judge on this PR, with a pointer; brief.skip: what the
reviewers verified with evidence. It ends the review body under "For the human reviewer".
The review is always event COMMENT: the agent reports, a human decides.
Only blocker and major become inline threads; at most 5 minor go folded into the body. Each inline thread
mails every watcher, and in SEON the agent's findings per UI PR rose from 10 to 18 without fewer change
requests (retro 2026-11). One review per head: a second post on the same commit is refused (--force posts).
"""
import json, re, subprocess, sys

MARK = "🤖 review"
ORDER = {"blocker": 0, "major": 1, "minor": 2}
INLINE = {"blocker", "major"}
MAX_MINOR = 5


def sh(cmd, stdin=None):
    r = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"review_post: {' '.join(cmd[:4])} failed: {r.stderr.strip()}")
    return r.stdout


def right_lines(diff):
    """{path: set of new-file line numbers that appear in the diff} - the only lines GitHub accepts."""
    out, path, n = {}, None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            continue
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if m:
            n = int(m.group(1))
            continue
        if path is None or line.startswith(("--- ", "diff ", "index ")):
            continue
        if line.startswith("+") or line.startswith(" "):
            out.setdefault(path, set()).add(n)
            n += 1
    return out


def brief_text(brief):
    if not brief or not (brief.get("check") or brief.get("skip")):
        return ""
    out = "\n\n### For the human reviewer"
    if brief.get("check"):
        out += "\n\nCheck yourself:\n" + "\n".join(f"- {x}" for x in brief["check"])
    if brief.get("skip"):
        out += "\n\nVerified by the reviewers, skip unless you doubt it:\n" + "\n".join(f"- {x}" for x in brief["skip"])
    return out


def payload(findings, diff, head, brief=None):
    lines = right_lines(diff)
    fs = sorted(findings, key=lambda f: (ORDER.get(f.get("severity"), 3), f.get("path", ""), f.get("line", 0)))
    fs = [f for f in fs if f.get("severity") in INLINE] + [f for f in fs if f.get("severity") == "minor"][:MAX_MINOR]
    inline, loose, minor = [], [], []
    for f in fs:
        text = f"**{f['severity']}** · `{f.get('rule', '-')}`\n\n{f['text']}"
        line = f"- `{f.get('path', '?')}:{f.get('line', '?')}` {text.replace(chr(10), ' ')}"
        if f.get("severity") not in INLINE:
            minor.append(line)
        elif f.get("line") in lines.get(f.get("path"), set()):
            inline.append({"path": f["path"], "line": f["line"], "side": "RIGHT", "body": text})
        else:
            loose.append(line)
    counts = {s: sum(1 for f in fs if f.get("severity") == s) for s in ORDER}
    body = f"{MARK} · head `{head[:7]}` · " + ", ".join(f"{v} {k}" for k, v in counts.items())
    if loose:
        body += "\n\nNot anchorable on the diff:\n" + "\n".join(loose)
    if minor:
        body += (f"\n\n<details><summary>{len(minor)} minor (not blocking; fix or say why not in one PR comment)"
                 "</summary>\n\n" + "\n".join(minor) + "\n\n</details>")
    if not fs:
        body += "\n\nNo findings."
    body += brief_text(brief)
    return {"commit_id": head, "event": "COMMENT", "body": body, "comments": inline}


def posted_on(reviews, head):
    return any((r.get("body") or "").startswith(MARK) and r.get("commit_id") == head for r in reviews)


def main():
    args = [a for a in sys.argv[1:] if a not in ("--dry-run", "--force")]
    repo, pr, path = args
    data = json.load(open(path))
    findings, brief = (data, None) if isinstance(data, list) else (data["findings"], data.get("brief"))
    head = json.loads(sh(["gh", "pr", "view", pr, "-R", repo, "--json", "headRefOid"]))["headRefOid"]
    if "--force" not in sys.argv and "--dry-run" not in sys.argv and posted_on(
            json.loads(sh(["gh", "api", f"repos/{repo}/pulls/{pr}/reviews", "--paginate"])), head):
        sys.exit(f"review_post: an agent review on head {head[:7]} exists already; push first or pass --force")
    diff = sh(["gh", "pr", "diff", pr, "-R", repo])
    p = payload(findings, diff, head, brief)
    if "--dry-run" in sys.argv:
        print(json.dumps(p, indent=1, ensure_ascii=False))
        return
    sh(["gh", "api", f"repos/{repo}/pulls/{pr}/reviews", "--input", "-"], json.dumps(p))
    print(json.dumps({"ok": True, "inline": len(p["comments"]), "in_body": len(findings) - len(p["comments"])}))


if __name__ == "__main__":
    main()
