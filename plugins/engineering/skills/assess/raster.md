# Assessment raster

Every number names its source (command, file:line). One section per subagent.

| # | Section | Measure |
|---|---|---|
| 1 | **Architecture vs docs** | layers, core models, integrations; does CLAUDE.md/ARCHITECTURE.md still match the code (versions, hosting, counts)? List each drift with file:line |
| 2 | **Hotspots** | churn × size in the window (`git log --since=<N>.days --numstat`), largest files/classes/methods, files with many fix commits; top 15 |
| 3 | **Second ways and dead code** | the same problem solved twice (services, helpers, components), dead paths, commented-out code, TODO/FIXME/HACK, unused files/routes/dependencies (heuristic + sample) |
| 4 | **Tests and gates** | test types and counts, coverage if current, flakiness signs (sleep, retries), what CI runs, whether CI is actually running, branch protection (`gh api repos/<o>/<r>/branches/<b>/protection`), security scanners, e2e/system tests |
| 5 | **Comments and docs** | rough comment density, comments with ticket numbers or review history, stale comments (sample), oversized docs and memory files |
| 6 | **Data changes** | migrations in the window, irreversible ones, data changes inside schema migrations, seeds that run on deploy |
| 7 | **Security and privacy** | secrets in the repo, personal data in logs, scoping of queries by user/tenant (sample), outbound calls without timeout |
| 8 | **Onboarding** | can a second person start: setup steps, secrets handling, seed data, local test run equal to CI, CONTRIBUTING/PR template |
| 9 | **Delivery** | merged vs deployed (how far is main ahead of production), release cadence, open release PRs |

Rules from context (core and world) are a yardstick: name 5–10 concrete places for each rule that matters, not every rule.

## Report

```
# Assessment <repo>
Stand: <date> · window <N> days · read-only

## Urgent (🔴)
## Numbers            (table: number, source)
## Findings per section
## Clean-up list      (impact × effort; what, where, why now, S/M/L, risk)
## Not measured (⚠️)
```
