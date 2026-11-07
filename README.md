# engineering

A Claude Code plugin for agent-built software that a human can trust: clarify before building, build against acceptance examples, prove them with a fresh-context verifier, keep PRs short, fold review and QA feedback back into the spec, review and assess with visible results.

## Skills

| Skill | Does |
|---|---|
| `clarify <issue>` | Reads the issue, its links and the code; keeps **one** living comment with finding, goal, numbered acceptance examples and at most 5 questions for the owner; hands the issue to the owner. `--in-flight` writes the spec for work already in progress |
| `build <issue>` | Only on Ready. Plan per acceptance example, tests first, then the `verifier` agent, then `pr` |
| `pr` | Draft PR, at most 15 lines, evidence per example, link to the issue |
| `feedback <issue or pr>` | Reads PR review threads and issue comments together, sorts every point into bug / spec gap / other issue / style, answers in the channel it came from |
| `review <pr>` | Fresh reviewer agents per lens, one visible GitHub review (comment only) |
| `assess <repo>` | Read-only health assessment with a fixed raster; findings become issues in state `idea` |
| `world new personal\|team` | Create a personal layer or a team world from the template; `add-rule`, `add-context` to maintain one |

Several issues at once: `clarify a b c`, `build a b c` (plans in parallel, one approval, builds in worktrees).

## Rules

Core rules (`katalog/kern.yaml`, built into `plugins/engineering/generated/kern.md`) are loaded into every session and subagent inside a git repo. A hook asks before an edit removes assertions or skips tests.

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
