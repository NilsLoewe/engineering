#!/usr/bin/env python3
"""Collect review and QA feedback for one PR and its ticket as JSON (read only).

    feedback_collect.py <pr-ref> [<ticket-ref>]
    pr-ref: owner/repo#N or a PR URL. ticket-ref: anything tracker.py reads; default: the first
    Monday or GitHub issue link in the PR body. Monday needs the token (run where tracker.py runs).

Output: pr, threads (inline review threads, oldest first), reviews (with a body), pr_comments,
ticket (with only the comments written since the PR was opened). Every comment carries `kind`:
human, agent (body starts with 🤖, posted under a human account) or bot. A thread is `open`
when its last comment is not from the PR author.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import tracker  # noqa: E402

TICKET_LINK = re.compile(r"https://\S*monday\.com/boards/\d+/(?:pulses|items)/\d+|https://github\.com/[\w.-]+/[\w.-]+/issues/\d+")


def kind(login, body):
    if login.endswith("[bot]") or login == "Copilot":
        return "bot"
    return "agent" if body.lstrip().startswith("🤖") else "human"


def api(path):
    """All pages of a GitHub list endpoint."""
    return [x for page in json.loads(tracker.sh(["gh", "api", path, "--paginate", "--slurp"])) for x in page]


def note(c, login_key="user"):
    login, body = c[login_key]["login"], c.get("body") or ""
    return {"author": login, "kind": kind(login, body), "created_at": c.get("created_at") or c.get("submitted_at"),
            "body": body}


def collect(pr_ref, ticket_ref=None, read=tracker.read):
    m = re.search(r"([\w.-]+/[\w.-]+)(?:#|/pull/)(\d+)", pr_ref)
    if not m:
        tracker.die(f"unknown PR reference: {pr_ref}")
    repo, n = m.groups()
    base = f"repos/{repo}"
    pr = json.loads(tracker.sh(["gh", "api", f"{base}/pulls/{n}"]))
    author = pr["user"]["login"]

    by_root = {}
    for c in sorted(api(f"{base}/pulls/{n}/comments"), key=lambda c: c["created_at"]):
        by_root.setdefault(c.get("in_reply_to_id") or c["id"], []).append(c)
    threads = []
    for root, cs in by_root.items():
        first = cs[0]
        threads.append({"id": root, "url": first["html_url"], "path": first["path"],
                        "line": first.get("line") or first.get("original_line"), **note(first),
                        "open": cs[-1]["user"]["login"] != author, "replies": [note(c) for c in cs[1:]]})
    threads.sort(key=lambda t: t["created_at"])

    reviews = [{**note(r), "state": r["state"], "url": r["html_url"]} for r in api(f"{base}/pulls/{n}/reviews") if r.get("body")]
    pr_comments = [{**note(c), "url": c["html_url"]} for c in api(f"{base}/issues/{n}/comments")]

    ticket_ref = ticket_ref or next(iter(TICKET_LINK.findall(pr.get("body") or "")), None)
    ticket = None
    if ticket_ref:
        t = read(ticket_ref, tracker.load_config())
        since = tracker.ts(pr["created_at"])
        ticket = {"ref": ticket_ref, "url": t["url"], "title": t["title"], "state": t["state"], "raw_state": t["raw_state"],
                  "body": t["body"], "comments": [c for c in t["comments"] if tracker.ts(c["created_at"]) >= since]}
    return {"pr": {"url": pr["html_url"], "title": pr["title"], "state": pr["state"], "author": author,
                   "created_at": pr["created_at"], "head": pr["head"]["ref"], "base": pr["base"]["ref"]},
            "threads": threads, "reviews": reviews, "pr_comments": pr_comments, "ticket": ticket}


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if not a or a[0] in ("-h", "--help") or len(a) > 2:
        sys.exit(__doc__)
    print(json.dumps(collect(*a), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
