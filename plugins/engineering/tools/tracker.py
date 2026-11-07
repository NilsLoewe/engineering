#!/usr/bin/env python3
"""Tracker adapter: read / comment / set-state / link / assign / create.

Backends: github (via `gh`), monday (GraphQL). The backend follows from the
issue reference. Process states map to backend values through the config:
`--config FILE` or env ENGINEERING_CONFIG (a world overlay names its file),
then `.engineering.json` searched upward from cwd; the repo file wins.
GitHub works without config (labels status:<state>); Monday needs "monday.states".

    tracker.py read <ref>
    tracker.py comment <ref> [--key K] [--body TEXT | --body-file F]   (stdin if neither)
               --key: one living comment per key (e.g. spec, questions), edited in place
    tracker.py set-state <ref> <idea|clarifying|ready|in-progress|review|done>
    tracker.py link <ref> <url>
    tracker.py assign <ref> <person>        (Monday: name or e-mail; GitHub: login) replaces the assignee
    tracker.py create <owner/repo> --title T [--body-file F] [--state idea]   (GitHub issue)
    --dry-run (or env TRACKER_DRY_RUN=1) prints the write instead of doing it.
"""
import argparse, html, json, os, re, subprocess, sys, urllib.request
from datetime import datetime

STATES = ["idea", "clarifying", "ready", "in-progress", "review", "done"]

# GitHub default: one label per state. Monday has no default: boards differ, the config
# names the status column values per state ("monday.states") and optional extra columns
# written alongside ("monday.also").
DEFAULTS = {"github": {s: f"status:{s}" for s in STATES}, "monday": {}}
LINK_PREFIX = "Linked:"
MONDAY_API = "https://api.monday.com/v2"


def die(msg):
    sys.exit(f"tracker: {msg}")


def merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_config(start=None, explicit=None):
    cfg = {}
    for p in filter(None, [explicit or os.environ.get("ENGINEERING_CONFIG")]):
        cfg = merge(cfg, json.load(open(os.path.expanduser(p))).get("tracker", {}))
    d = os.path.abspath(start or os.getcwd())
    while True:
        p = os.path.join(d, ".engineering.json")
        if os.path.exists(p):
            return merge(cfg, json.load(open(p)).get("tracker", {}))
        if os.path.dirname(d) == d:
            return cfg
        d = os.path.dirname(d)


def state_map(backend, cfg):
    m = dict(DEFAULTS[backend])
    m.update((cfg.get(backend) or {}).get("states", {}))
    if backend == "monday" and not m:
        die("monday needs monday.states in the tracker config (world overlay or .engineering.json)")
    return m


def parse_ref(ref):
    """-> (backend, id). github id = (repo or None, number); monday id = item id."""
    m = re.search(r"monday\.com/boards/\d+/(?:pulses|items)/(\d+)", ref)
    if m:
        return "monday", m.group(1)
    m = re.search(r"github\.com/([\w.-]+/[\w.-]+)/(?:issues|pull)/(\d+)", ref)
    if m:
        return "github", (m.group(1), m.group(2))
    m = re.fullmatch(r"([\w.-]+/[\w.-]+)?#(\d+)", ref)
    if m:
        return "github", (m.group(1), m.group(2))
    if re.fullmatch(r"\d{6,}", ref):  # bare Monday item id; GitHub numbers need '#'
        return "monday", ref
    die(f"unknown issue reference: {ref}")


# ---------- github ----------

def sh(cmd, stdin=None):
    r = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
    if r.returncode:
        die(f"{' '.join(cmd)} failed: {r.stderr.strip()}")
    return r.stdout


def gh_repo_args(repo):
    return ["-R", repo] if repo else []


def gh_read(gid, cfg):
    repo, n = gid
    j = json.loads(sh(["gh", "issue", "view", n, *gh_repo_args(repo), "--json",
                       "title,body,labels,state,url,comments"]))
    labels = [l["name"] for l in j["labels"]]
    smap = state_map("github", cfg)
    state = next((s for s in STATES if smap[s] in labels), None)
    if state is None and j["state"] == "CLOSED":
        state = "done"
    return {"backend": "github", "url": j["url"], "title": j["title"], "body": j["body"] or "",
            "state": state, "raw_state": [l for l in labels if l.startswith("status:")],
            "comments": [{"author": (c.get("author") or {}).get("login"), "created_at": c["createdAt"],
                          "body": c["body"]} for c in j["comments"]]}


def gh_comment(gid, body, dry, head=None):
    repo, n = gid
    cid = None
    if head:
        repo = repo or json.loads(sh(["gh", "repo", "view", "--json", "nameWithOwner"]))["nameWithOwner"]
        for c in json.loads(sh(["gh", "api", f"repos/{repo}/issues/{n}/comments", "--paginate"])):
            if c["body"].strip().startswith(head):
                cid = c["id"]
    cmd = (["gh", "api", "-X", "PATCH", f"repos/{repo}/issues/comments/{cid}", "-F", "body=@-"] if cid else
           ["gh", "issue", "comment", n, *gh_repo_args(repo), "--body-file", "-"])
    if dry:
        return {"dry_run": True, "cmd": cmd, "body": body}
    sh(cmd, body)
    return {"ok": True, "edited": bool(cid)}


def gh_set_state(gid, state, cfg, dry):
    repo, n = gid
    smap = state_map("github", cfg)
    cur = gh_read(gid, cfg)["raw_state"]  # reads are safe in dry-run
    label = smap[state]
    have = {l["name"] for l in json.loads(sh(["gh", "label", "list", *gh_repo_args(repo), "--limit", "500",
                                                "--json", "name"]))}
    cmds = ([] if label in have else [["gh", "label", "create", label, *gh_repo_args(repo), "--color", "BFD4F2"]]) + [
            ["gh", "issue", "edit", n, *gh_repo_args(repo), "--add-label", label,
             *sum((["--remove-label", l] for l in cur if l != label), [])]]
    if dry:
        return {"dry_run": True, "cmds": cmds}
    for c in cmds:  # label create (if missing) then edit
        sh(c)
    return {"ok": True, "state": state}


# ---------- monday ----------

def monday_token():
    if os.environ.get("MONDAY_TOKEN"):
        return os.environ["MONDAY_TOKEN"]
    p = os.environ.get("MONDAY_TOKEN_FILE") or (".env" if os.path.exists(".env") else None)
    if p:
        with open(os.path.expanduser(p)) as f:
            for line in f:
                k, _, v = line.removeprefix("export ").partition("=")
                if k.strip().lower() == "monday_token":
                    return v.strip().strip("'\"")
    die("set MONDAY_TOKEN or MONDAY_TOKEN_FILE (env file with monday_token=...)")


def gql(query, variables=None):
    req = urllib.request.Request(MONDAY_API, json.dumps({"query": query, "variables": variables or {}}).encode(),
                                 {"Authorization": monday_token(), "Content-Type": "application/json",
                                  "API-Version": "2024-10"})
    r = json.load(urllib.request.urlopen(req, timeout=60))
    if r.get("errors"):
        die(f"monday: {r['errors']}")
    return r["data"]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def monday_read(item_id, cfg):
    d = gql("""query($id:[ID!]){items(ids:$id){id name created_at url board{id}
      column_values{id text}
      updates(limit:100){id created_at text_body creator{name} replies{created_at text_body creator{name}}}}}""",
            {"id": [item_id]})
    if not d["items"]:
        die(f"monday item {item_id} not found")
    it = d["items"][0]
    cols = {c["id"]: c["text"] for c in it["column_values"]}
    ups = sorted(it["updates"], key=lambda u: u["created_at"])
    # Monday has no description field in use on many boards: the first update counts as description if written within 2 h of creation.
    body = ""
    if ups and (ts(ups[0]["created_at"]) - ts(it["created_at"])).total_seconds() < 7200:
        body = ups[0]["text_body"] or ""
        first, ups = ups[0], ups[1:]
        ups = [{"id": None, "created_at": r["created_at"], "text_body": r["text_body"], "creator": r["creator"]}
               for r in first["replies"]] + ups
    comments = []
    for u in ups:
        comments.append({"id": u.get("id"), "author": (u.get("creator") or {}).get("name"),
                         "created_at": u["created_at"], "body": u["text_body"] or ""})
        for r in u.get("replies") or []:
            comments.append({"reply_to": u.get("id"), "author": (r.get("creator") or {}).get("name"),
                             "created_at": r["created_at"], "body": r["text_body"] or ""})
    comments.sort(key=lambda c: c["created_at"])
    smap = state_map("monday", cfg)
    # most specific mapping that matches wins (ready beats idea when Refinement=Refined)
    match = [s for s in STATES if all(cols.get(k) == v for k, v in smap[s].items())]
    state = max(match, key=lambda s: (len(smap[s]), STATES.index(s)), default=None)
    return {"backend": "monday", "url": it["url"], "board_id": it["board"]["id"], "title": it["name"],
            "body": body, "state": state, "raw_state": {k: cols.get(k) for k in ("status", "status_1__1")},
            "columns": cols, "comments": comments}


def _inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`([^`]+)`", r"<i>\1</i>", t)


def to_html(text):
    """Markdown-lite for Monday: **bold**, `code` (italic), '- ' lists, blank line = paragraph.
    '1. ' lines stay paragraphs with their number: Monday shows <ol> as bullets, and the text refers to numbers."""
    out, lst = [], None
    for line in text.splitlines():
        m = re.match(r"^\s*([-*])\s+(.*)$", line)
        kind = "ul" if m else None
        if lst and kind != lst:
            out.append(f"</{lst}>"); lst = None
        if m:
            if not lst:
                out.append(f"<{kind}>"); lst = kind
            out.append(f"<li>{_inline(m.group(2))}</li>")
        elif line.strip():
            out.append(f"<p>{_inline(line.strip())}</p>")
    if lst:
        out.append(f"</{lst}>")
    return "".join(out)


def monday_find(item_id, head):
    d = gql("query($id:[ID!]){items(ids:$id){updates(limit:100){id text_body}}}", {"id": [item_id]})
    for u in d["items"][0]["updates"]:
        if (u["text_body"] or "").strip().startswith(head):
            return u["id"]
    return None


def monday_comment(item_id, body, dry, head=None):
    uid = monday_find(item_id, head) if head else None  # reads are safe in dry-run
    if uid:
        q, v = "mutation($id:ID!,$b:String!){edit_update(id:$id,body:$b){id}}", {"id": uid, "b": to_html(body)}
    else:
        q, v = "mutation($id:ID!,$b:String!){create_update(item_id:$id,body:$b){id}}", {"id": item_id, "b": to_html(body)}
    if dry:
        return {"dry_run": True, "mutation": q, "variables": v}
    r = gql(q, v)
    return {"ok": True, "update_id": (r.get("edit_update") or r.get("create_update"))["id"], "edited": bool(uid)}


def monday_set_state(item_id, state, cfg, dry):
    vals = {**state_map("monday", cfg)[state], **(cfg.get("monday") or {}).get("also", {}).get(state, {})}
    board = gql("query($id:[ID!]){items(ids:$id){board{id}}}", {"id": [item_id]})["items"][0]["board"]["id"]
    q = ("mutation($b:ID!,$i:ID!,$v:JSON!){change_multiple_column_values("
         "board_id:$b,item_id:$i,column_values:$v,create_labels_if_missing:false){id}}")
    v = {"b": board, "i": item_id, "v": json.dumps({k: {"label": x} for k, x in vals.items()})}
    if dry:
        return {"dry_run": True, "mutation": q, "variables": v}
    gql(q, v)
    return {"ok": True, "state": state}


# ---------- dispatch ----------

def read(ref, cfg):
    b, i = parse_ref(ref)
    return gh_read(i, cfg) if b == "github" else monday_read(i, cfg)


def _git_user():
    try:
        return subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


MARKER = os.environ.get("TRACKER_MARKER", "🤖 clarify (agent)" + (f" · posted for {_git_user()}" if _git_user() else ""))


def comment(ref, body, dry, key=None):
    """key: one living comment per key; its first line is `🤖 clarify · <key>` and later calls edit it."""
    b, i = parse_ref(ref)
    if not body.strip():
        die("empty comment")
    head = f"🤖 clarify · {key}" if key else None
    if head:
        body = body if body.startswith(head) else f"{head} · {datetime.now():%d.%m.%Y %H:%M}\n\n{body}"
    elif MARKER and not body.startswith(MARKER):
        body = f"{MARKER}\n\n{body}"
    return gh_comment(i, body, dry, head) if b == "github" else monday_comment(i, body, dry, head)


def set_state(ref, state, cfg, dry):
    if state not in STATES:
        die(f"state must be one of {STATES}")
    b, i = parse_ref(ref)
    return gh_set_state(i, state, cfg, dry) if b == "github" else monday_set_state(i, state, cfg, dry)


def monday_assign(item_id, person, cfg, dry):
    """Replaces the people column (default "person", config monday.assign_column) with exactly one user."""
    col = (cfg.get("monday") or {}).get("assign_column", "person")
    users = gql("{users(limit:500){id name email enabled}}")["users"]
    p = person.strip().lower()
    hits = [u for u in users if u.get("enabled", True) and p in (u["name"].lower(), (u["email"] or "").lower())] or \
           [u for u in users if u.get("enabled", True) and p in u["name"].lower()]
    if len(hits) != 1:
        die(f"monday user '{person}': {len(hits)} matches {[h['name'] for h in hits][:5]}; use the exact name or e-mail")
    board = gql("query($id:[ID!]){items(ids:$id){board{id}}}", {"id": [item_id]})["items"][0]["board"]["id"]
    q = "mutation($b:ID!,$i:ID!,$c:String!,$v:JSON!){change_column_value(board_id:$b,item_id:$i,column_id:$c,value:$v){id}}"
    v = {"b": board, "i": item_id, "c": col,
         "v": json.dumps({"personsAndTeams": [{"id": int(hits[0]["id"]), "kind": "person"}]})}
    if dry:
        return {"dry_run": True, "mutation": q, "variables": v, "user": hits[0]["name"]}
    gql(q, v)
    return {"ok": True, "assigned": hits[0]["name"]}


def gh_assign(gid, login, dry):
    repo, n = gid
    cur = [a["login"] for a in json.loads(sh(["gh", "issue", "view", n, *gh_repo_args(repo), "--json", "assignees"]))["assignees"]]
    cmd = ["gh", "issue", "edit", n, *gh_repo_args(repo), "--add-assignee", login,
           *sum((["--remove-assignee", c] for c in cur if c != login), [])]
    if dry:
        return {"dry_run": True, "cmd": cmd}
    sh(cmd)
    return {"ok": True, "assigned": login}


def assign(ref, person, cfg, dry):
    b, i = parse_ref(ref)
    return gh_assign(i, person, dry) if b == "github" else monday_assign(i, person, cfg, dry)


def create(repo, title, body, state, cfg, dry):
    """New GitHub issue (assess files findings this way), then its state label."""
    cmd = ["gh", "issue", "create", "-R", repo, "--title", title, "--body-file", "-"]
    if dry:
        return {"dry_run": True, "cmd": cmd, "body": body, "state": state}
    url = sh(cmd, body).strip().splitlines()[-1]
    n = url.rstrip("/").rsplit("/", 1)[-1]
    set_state(f"{repo}#{n}", state, cfg, dry)
    return {"ok": True, "url": url}


def link(ref, url, cfg, dry):
    """A link is a comment `Linked: <url>`; skipped if the issue already carries it."""
    issue = read(ref, cfg)
    if url in issue["body"] or any(url in c["body"] for c in issue["comments"]):
        return {"ok": True, "skipped": "already linked"}
    return comment(ref, f"{LINK_PREFIX} {url}", dry)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--config", help="tracker config file (a world overlay names it)")
    sub = ap.add_subparsers(dest="op", required=True)
    sub.add_parser("read").add_argument("ref")
    c = sub.add_parser("comment")
    c.add_argument("ref")
    c.add_argument("--body")
    c.add_argument("--body-file")
    c.add_argument("--key", help="living comment: edit the one with this key instead of posting a new one")
    s = sub.add_parser("set-state")
    s.add_argument("ref")
    s.add_argument("state", choices=STATES)
    l = sub.add_parser("link")
    l.add_argument("ref")
    l.add_argument("url")
    g = sub.add_parser("assign")
    g.add_argument("ref")
    g.add_argument("person")
    n = sub.add_parser("create")
    n.add_argument("repo")
    n.add_argument("--title", required=True)
    n.add_argument("--body-file")
    n.add_argument("--state", default="idea", choices=STATES)
    a = ap.parse_args(argv)
    dry = a.dry_run or os.environ.get("TRACKER_DRY_RUN") == "1"
    cfg = load_config(explicit=a.config)
    if a.op == "read":
        out = read(a.ref, cfg)
    elif a.op == "comment":
        body = a.body if a.body is not None else (open(a.body_file).read() if a.body_file else sys.stdin.read())
        out = comment(a.ref, body, dry, a.key)
    elif a.op == "set-state":
        out = set_state(a.ref, a.state, cfg, dry)
    elif a.op == "create":
        out = create(a.repo, a.title, open(a.body_file).read() if a.body_file else "", a.state, cfg, dry)
    elif a.op == "assign":
        out = assign(a.ref, a.person, cfg, dry)
    else:
        out = link(a.ref, a.url, cfg, dry)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
