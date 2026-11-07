#!/usr/bin/env python3
"""Posts one GitHub review from a findings file; findings that GitHub cannot anchor go into the body.

    review_post.py <owner/repo> <pr> <findings.json> [--dry-run]

findings.json: [{"path", "line", "severity": "blocker|major|minor", "rule", "text"}]
The review is always event COMMENT: the agent reports, a human decides.
"""
import json, re, subprocess, sys

MARK = "🤖 review"
ORDER = {"blocker": 0, "major": 1, "minor": 2}


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


def payload(findings, diff, head):
    lines = right_lines(diff)
    fs = sorted(findings, key=lambda f: (ORDER.get(f.get("severity"), 3), f.get("path", ""), f.get("line", 0)))
    inline, loose = [], []
    for f in fs:
        text = f"**{f['severity']}** · `{f.get('rule', '-')}`\n\n{f['text']}"
        if f.get("line") in lines.get(f.get("path"), set()):
            inline.append({"path": f["path"], "line": f["line"], "side": "RIGHT", "body": text})
        else:
            loose.append(f"- `{f.get('path', '?')}:{f.get('line', '?')}` {text.replace(chr(10), ' ')}")
    counts = {s: sum(1 for f in fs if f.get("severity") == s) for s in ORDER}
    body = f"{MARK} · head `{head[:7]}` · " + ", ".join(f"{v} {k}" for k, v in counts.items())
    if loose:
        body += "\n\nNot anchorable on the diff:\n" + "\n".join(loose)
    if not fs:
        body += "\n\nNo findings."
    return {"commit_id": head, "event": "COMMENT", "body": body, "comments": inline}


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    repo, pr, path = args
    findings = json.load(open(path))
    head = json.loads(sh(["gh", "pr", "view", pr, "-R", repo, "--json", "headRefOid"]))["headRefOid"]
    diff = sh(["gh", "pr", "diff", pr, "-R", repo])
    p = payload(findings, diff, head)
    if "--dry-run" in sys.argv:
        print(json.dumps(p, indent=1, ensure_ascii=False))
        return
    sh(["gh", "api", f"repos/{repo}/pulls/{pr}/reviews", "--input", "-"], json.dumps(p))
    print(json.dumps({"ok": True, "inline": len(p["comments"]), "in_body": len(findings) - len(p["comments"])}))


if __name__ == "__main__":
    main()
