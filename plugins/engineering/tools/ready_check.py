#!/usr/bin/env python3
"""Ready check (rule 1) against the latest `[engineering:spec]` block.

    tracker.py read <ref> | ready_check.py      # or: ready_check.py spec.md
Exit 0 = ready, 1 = not ready (missing criteria listed), 2 = no spec block.
Format: skills/clarify/spec-format.md
"""
import json, re, sys

MARKERS = ("🤖 clarify · spec", "[engineering:spec]")
MARKER = MARKERS[0]
# Headings in English and German: clarify writes the spec in the issue's language.
SECTIONS = {"problem": "problem", "goal": "problem", "ziel": "problem",
            "acceptance": "examples", "akzeptanz": "examples",
            "open questions": "questions", "offene fragen": "questions",
            "repos": "repos", "affected": "repos", "for developers": "repos",
            "für entwickler": "repos", "fuer entwickler": "repos"}
OTHER = ("not included", "out of scope", "verification", "notes", "decisions", "nicht dabei", "nicht enthalten")
EDGE = re.compile(r"\((edge|error|grenze|fehler)\)|\b(edge|error) case\b", re.I)
PROPOSAL = re.compile(r"Proposal|Vorschlag")
NONE = re.compile(r"^\s*[-*]?\s*(none|keine|n/a|—|-)?\.?\s*$", re.I)


def latest_block(text_or_json):
    try:
        j = json.loads(text_or_json)
        texts = [j.get("body", "")] + [c["body"] for c in j.get("comments", [])]
    except ValueError:
        texts = [text_or_json]
    blocks = [t[t.index(m):] for t in texts for m in MARKERS if m in t]
    return blocks[-1] if blocks else None


HEAD = re.compile(r"^[#*\s]*(" + "|".join(SECTIONS) + r")[^:\n]{0,40}:?\**:?\s*(.*)$", re.I)
OTHER_HEAD = re.compile(r"^[#*\s]*(" + "|".join(OTHER) + r")\b[^:\n]{0,40}:?\**:?", re.I)


def parse(block):
    sec, out = None, {v: [] for v in SECTIONS.values()}
    for line in block.splitlines()[1:]:
        if any(mk in line for mk in MARKERS):
            break
        m = HEAD.match(line)
        if OTHER_HEAD.match(line):  # any other heading ends the current section, wherever it stands
            sec = None
        elif m:
            sec = SECTIONS[m.group(1).lower()]
            if m.group(2).strip("* "):
                out[sec].append(m.group(2).strip("* "))
        elif sec and line.strip():
            out[sec].append(line.strip())
    return out


def check(block):
    s = parse(block)
    ex = [l for l in s["examples"] if not re.fullmatch(r"\|?[\s:|-]+\|?", l)]
    rows = [l for l in ex if l.startswith("|")]
    if rows:  # table: first row is the header
        ex = [l for l in ex if not l.startswith("|")] + rows[1:]
    qs = [l for l in s["questions"] if not NONE.match(l)]
    numbered = [l for l in qs if re.match(r"^[-*]?\s*\**(Q\d+|\d+\.)", l)]
    # Once questions are numbered, only numbered lines count: wrapped lines and the
    # heading's tail ("· please reply …") are not questions, even when all are answered.
    qs = [l for l in (numbered or qs) if "→" not in l]  # "→ yes" = answered
    missing = []
    if not " ".join(s["problem"]).strip():
        missing.append("problem/value not described")
    if not ex:
        missing.append("no acceptance examples")
    elif not any(EDGE.search(l) for l in ex):
        missing.append("no edge or error example (mark one '(edge)' or '(error)')")
    chained = [i + 1 for i, l in enumerate(ex) if re.search(r"\band then\b", l, re.I)]
    if chained:
        missing.append("acceptance line(s) " + ", ".join(map(str, chained)) + " chain steps with 'and then': one trigger per line")
    double = [l.split(".")[0].strip("*- ") for l in qs if PROPOSAL.split(l)[0].count("?") > 1]
    if double:
        missing.append("question(s) " + ", ".join(double) + " ask two things: one decision per question")
    if qs:
        missing.append(f"{len(qs)} open question(s)")
    if not any(not NONE.match(l) for l in s["repos"]):
        missing.append("affected repos/interfaces not named")
    return missing


def main():
    if sys.argv[1:2] in (["-h"], ["--help"]):
        sys.exit(print(__doc__))
    src = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    block = latest_block(src)
    if block is None:
        print(f"NOT READY: no {MARKER} block found. Run clarify first.")
        sys.exit(2)
    missing = check(block)
    print("READY" if not missing else "NOT READY:\n- " + "\n- ".join(missing))
    lines = [l for l in block.splitlines()[1:] if l.strip()]
    if len(lines) > 20:  # budget from spec-format.md; a warning, not a gate
        print(f"warning: the comment has {len(lines)} lines, budget is 20: shorten it")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
