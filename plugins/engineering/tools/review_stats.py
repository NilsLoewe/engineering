#!/usr/bin/env python3
"""Precision of agent review findings per rule: which findings led to a change, which were dismissed.

    review_stats.py <owner/repo> [--since 2026-11-01] [--marker "🤖 review"] [--json]

Reads the inline threads of PRs updated since the date (gh GraphQL). A thread is an agent finding when its
first comment starts with a marker (default: the core marker and SEON's review agent). Outcome per thread:
the answer's tag (skill feedback: "fixed in <sha>:", "not a defect:", "not this ticket:", "deliberate:"),
else "changed" when GitHub marks the thread outdated (the code moved under it), "resolved", or "open".
Precision = (fixed + changed) / decided. Minor findings folded into review bodies have no thread and are
not counted. A rule with low precision is a candidate for removal from the catalog.
Limit: on a PR an agent wrote, the agent also answers the findings and fixes nearly all of them, so "fixed"
there measures compliance, not value. Precision says most where a human decides.
"""
import argparse, json, re, subprocess, sys
from collections import Counter, defaultdict

MARKERS = ["🤖 review", "🤖 **review-agent**"]
TAGS = [("fixed", re.compile(r"^\W*fixed in\b", re.I)), ("not-a-defect", re.compile(r"^\W*not a defect\b", re.I)),
        ("not-this-ticket", re.compile(r"^\W*not this ticket\b", re.I)), ("deliberate", re.compile(r"^\W*deliberate\b", re.I))]
SEV = re.compile(r"\b(blocker|major|minor|nit)\b")
RULE = re.compile(r"`([a-z][\w-]*-[\w-]+)`")  # rule ids contain a dash: kern-validate-input, fe-every-…
CAT = re.compile(r"`(?:blocker|major|minor|nit)` · ([\w-]+)")
GOOD = {"fixed", "changed"}
DECIDED = {"fixed", "changed", "not-a-defect", "not-this-ticket", "deliberate"}

QUERY = """query($q:String!,$after:String){search(query:$q,type:ISSUE,first:25,after:$after){
  pageInfo{hasNextPage endCursor}
  nodes{... on PullRequest{number reviewThreads(first:100){nodes{isResolved isOutdated
    comments(first:20){nodes{body}}}}}}}}"""


def finding(body, markers=MARKERS):
    """(severity, rule) of an agent finding's first comment, or None for any other comment."""
    if not any(body.startswith(m) for m in markers):
        return None
    head = body.split("\n")[0]  # the head line only: titles carry code in backticks too
    sev = SEV.search(head)
    rule = RULE.search(head) or CAT.search(head)
    return (sev.group(1) if sev else "?", rule.group(1) if rule else "-")


# Answers written before the tags existed: the same words anywhere in the reply.
LOOSE = [("not-a-defect", re.compile(r"\b(not a (defect|bug|problem)|intentional|by design|works as intended|won'?t fix|false positive)\b", re.I)),
         ("not-this-ticket", re.compile(r"\b(out of scope|not this ticket|follow-?up ticket|separate ticket)\b", re.I)),
         ("fixed", re.compile(r"\b(fixed|addressed|done) in [0-9a-f]{7,}\b", re.I))]


def outcome(thread):
    replies = [c["body"] or "" for c in thread["comments"]["nodes"][1:]]
    for rules in (TAGS, LOOSE):
        for r in replies:
            for tag, rx in rules:
                if rx.search(r):
                    return tag
    if thread["isOutdated"]:
        return "changed"
    return "resolved" if thread["isResolved"] else "open"


def collect(repo, since, markers):
    rows, after = [], None
    while True:
        out = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"q=repo:{repo} is:pr updated:>={since}",
                              *(["-f", f"after={after}"] if after else [])], capture_output=True, text=True)
        if out.returncode:
            sys.exit(f"review_stats: {out.stderr.strip()}")
        s = json.loads(out.stdout)["data"]["search"]
        for pr in s["nodes"]:
            for t in (pr.get("reviewThreads") or {}).get("nodes", []):
                f = t["comments"]["nodes"] and finding(t["comments"]["nodes"][0]["body"] or "", markers)
                if f:
                    rows.append({"pr": pr["number"], "severity": f[0], "rule": f[1], "outcome": outcome(t)})
        if not s["pageInfo"]["hasNextPage"]:
            return rows
        after = s["pageInfo"]["endCursor"]


def table(rows):
    by = defaultdict(Counter)
    for r in rows:
        by[r["rule"]][r["outcome"]] += 1
    out = []
    for rule, c in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
        decided = sum(v for k, v in c.items() if k in DECIDED)
        good = sum(v for k, v in c.items() if k in GOOD)
        out.append({"rule": rule, "findings": sum(c.values()), "decided": decided,
                    "precision": round(good / decided, 2) if decided else None, **dict(c)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--since", default="2026-11-01")
    ap.add_argument("--marker", action="append")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    t = table(collect(a.repo, a.since, a.marker or MARKERS))
    if a.json:
        return print(json.dumps(t, indent=1))
    print(f"{'rule':<40} {'n':>4} {'decided':>7} {'precision':>9}  outcomes")
    for r in t:
        rest = ", ".join(f"{k} {v}" for k, v in r.items() if k not in ("rule", "findings", "decided", "precision"))
        p = "–" if r["precision"] is None else f"{r['precision']:.0%}"
        print(f"{r['rule']:<40} {r['findings']:>4} {r['decided']:>7} {p:>9}  {rest}")


if __name__ == "__main__":
    main()
