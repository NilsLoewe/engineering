---
name: assess
description: Read-only assessment of a repository's current state - measures architecture drift, hotspots, second ways, tests and CI gates, docs, data changes, security and onboarding, with every number backed by the command that produced it - then proposes findings as issues in state idea. Use for "assess <repo>", "review the status quo", "code health check", or before someone new joins a codebase.
argument-hint: <repo path> [<repo path> ...] [--days N]
---

# assess

Measure first, judge second. Read only; the only writes are the report and, after the user's OK, the issues. Default window 90 days. Raster and report format: [raster.md](raster.md).

1. **Scope.** Repos given, their CLAUDE.md/AGENTS.md/README/ARCHITECTURE.md and docs. Files that start with `> 🧊 EINGEFROREN` are pointers, not content.
2. **Measure in parallel.** At most 5 subagents: bundle small sections (e.g. 5+8, 6+9), one per repo for several repos; read-only, each returning findings with number, source command and file:line.
3. **Write the report** where the world's context says reports go; none named → `docs/assess-<YYYY-MM-DD>.md` in the repo. Date at the top, findings before interpretation, ⚠️ on everything not measured.
4. **Propose issues.** One issue per finding worth acting on, at most 15, each: what, where (file:line), why now, size S/M/L, risk. Show the list to the user once and ask which to file (AskUserQuestion, multiSelect). Then for each chosen one: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/tracker.py create <owner/repo> --title "<imperative>" --body-file <f> --state idea` (add `--config <file>` when a world overlay names one). From there it goes through `clarify` like any issue.
5. **Report** in 5 lines: the three most urgent findings, issues filed, report path.

Never fix anything during an assessment. A finding that is urgent (data loss, security, a stopped pipeline) goes to the top of the report and into your reply, marked 🔴.
