# engineering

A Claude Code plugin for agent-built software that a human can trust: clarify before building, build against acceptance examples, prove them with a fresh-context verifier, keep PRs short, fold review and QA feedback back into the spec, review and assess with visible results.

## Skills

| Skill | Does |
|---|---|
| `clarify <issue>` | Reads the issue, its links and the code; keeps **one** living comment with finding, goal, numbered acceptance examples and at most 5 questions for the owner; hands the issue to the owner. `--in-flight` writes the spec for work already in progress |
| `build <issue>` | Only on Ready. Reads the lenses for the files it will touch, plans per acceptance example, tests first, then the `verifier` agent, then `pr` |
| `pr` | Draft PR that fills the repo's PR template when there is one; at most 15 content lines, evidence per example, deploy order, link to the issue |
| `feedback <issue or pr>` | Reads PR review threads and issue comments together, sorts every point into bug / spec gap / other issue / style, answers in the channel it came from |
| `review <pr>` | Fresh reviewer agents per lens, one visible GitHub review per head (comment only): blocker and major as threads, at most 5 minor folded into the body, then a brief for the human reviewer: what only a person can judge, what was verified |
| `ui-check change\|explore <url>` | Walks the UI in Chrome Beta via the chrome-devtools MCP: `change` goes through every changed screen's states and writes the evidence for verifier and PR (mandatory in `build` for UI changes); `explore` plays a persona through everyday tasks and files friction as issues. Never production |
| `assess <repo>` | Read-only health assessment with a fixed raster; findings become issues in state `idea` |
| `world new personal\|team` | Create a personal layer or a team world from the template; `add-rule`, `add-context` to maintain one |

Several issues at once: `clarify a b c`, `build a b c` (plans in parallel, one approval, builds in worktrees).

## Rules

Core rules (`katalog/kern.yaml`, built into `plugins/engineering/generated/kern.md`) are loaded into every session and subagent inside a git repo. A hook asks before an edit removes assertions or skips tests. A second hook denies starting the user's Google Chrome headless or with a debugging port, opening a host the world lists under `browser.never`, and a UI PR leaving draft without a `Screens:` line.

Lenses (`katalog/linsen.yaml`) are short rule lists that `review` picks by the changed files: `design` (code smells), `ux` (states, feedback, controls and wording for every app with an interface) and `framework` (APIs judged at the versions in the lockfile). A world lens with `ersetzt: <core lens>` takes that lens's place in its repos. `build` reads the matching lenses before it plans, including those a world marks `review: aus` (kept for writing, not run in review).

## Ready needs people, not only text

A world can require a human owner and an approval of the acceptance lines before Ready (`tracker.ready` in its overlay: `owner_column`, `owner_not`, `approvers`). `ready_check.py --config <overlay.json>` then checks the owner column and the line `Acceptance approved by <name>, <date>` against a comment by that person.

## Measuring the review agent

`tools/review_stats.py <owner/repo> --since <date>` counts per rule how agent findings ended: fixed, changed under the thread, dismissed (`not a defect`, `not this ticket`, `deliberate`) or open. `feedback` answers with these tags. A rule that is mostly dismissed is a candidate for removal. On PRs an agent wrote, "fixed" measures compliance more than value.

## Worlds

The core knows no company. A **world overlay** is a second plugin that adds, only in its own repos (matched by `git remote`):
- world rules (e.g. tenant scoping, i18n),
- the tracker config (Monday board states, GitHub labels),
- lenses for `review`,
- context files (process, owners, where reports go).

Start one from `templates/overlay/`. A repo can override the tracker config with `.engineering.json` (`{"tracker": {...}}`).

## Install

Step by step, with checks: [`docs/setup.md`](docs/setup.md). Own rules, a methods wiki, a team world: [`docs/worlds.md`](docs/worlds.md).


```
claude plugin marketplace add NilsLoewe/engineering
claude plugin install engineering@engineering
```

A team repo can declare the marketplace and its overlay in a checked-in `.claude/settings.json` (`extraKnownMarketplaces`, `enabledPlugins`), so everyone who opens the repo is offered both.

## Trackers

GitHub issues work without config (labels `status:idea|clarifying|ready|in-progress|review|done`). Monday needs `monday.states` from an overlay or `.engineering.json`; the token comes from `MONDAY_TOKEN`, `MONDAY_TOKEN_FILE` or `./.env`.

## Building a catalog

`python3 tools/build_katalog.py [--katalog DIR --out DIR --titel TITLE] [--check] [--mit-kandidaten]` builds core rules and lenses from YAML; overlays use the same tool for their own catalog. Budgets: rules file ≤ 2 KB, ≤ 15 rules per lens.
