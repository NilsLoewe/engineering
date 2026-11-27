---
name: pr
description: Open a draft pull request with a short body that links the issue and shows evidence per acceptance example, without repeating the spec. Also holds the code-comment policy. Use for "open a PR", "write the PR description", or at the end of build.
argument-hint: <issue-ref> [verifier report]
---

# pr

The PR points to the issue and proves the examples. The spec lives in the issue only.

## Body (budget: 15 non-empty lines)

```
Closes <issue link>          # or "Refs" if it does not finish the issue; Monday/Linear: full URL
                             # cross-repo: also "Contract: <provider PR link>"
<What and why in 1-3 sentences. Why, not how.>

Evidence
- AE1: <test file:line or command> — <result>
- AE2: not proven — <why>    # copy the verifier's verdicts, never upgrade them

Risk: <what could break, where; or "low: <reason>">
Screens: <UI change only: line from ui-check, or "n/a: <why nothing visible changed>">
Deploy: <order of migration, backfill, flag and other repos' PRs; or "independent">
```

`Screens:` is required when the diff changes a file of lens `ux`; a hook denies `gh pr ready` (and `gh pr create` without `--draft`) without it. Take the line from the `ui-check` report. A screenshot shows the states, not proof of usability; the evidence lines still name the test or the walk-through.

No spec, no file list, no changelog of review rounds, no tool chatter.

## The repo's PR template wins

Look for it first: `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE/*.md`, `docs/pull_request_template.md`, `pull_request_template.md` (on the base branch: `git show origin/<base>:<path>`). If one exists, the body **is that template, filled**: keep its headings in order, delete its `<!-- -->` hints, and put the lines above into the matching sections instead of the block format:

| Template section (typical names) | Gets |
|---|---|
| Links / Ticket / Task | `Closes <issue link>` |
| Description / Summary | what and why, 1-3 sentences |
| Changes / What changed | 1-3 bullets on behaviour, not a file list |
| Test Cases / Testing | `Evidence`, then one line per acceptance example |
| Screenshots | the `Screens:` line; image links only where the world names a host for them (a local `tmp/` path is not a screenshot) |
| Reviewer notes / Notes | `Risk:` and `Deploy:` (no such section: put them under the description) |

A section the template marks optional ("delete if none", "remove this if not applicable") goes when empty; every other section stays, with `n/a: <why>` if there is nothing to say. Never answer a frontend template with backend headings or the plugin block: reviewers read their template, and in SEON agent UI PRs lost the Screenshots section that way (0 of 20, 2026-11). The budget counts content lines only; headings, `---` and table separators are free.

`Deploy:` names what must ship first: a provider route or column the code calls, a migration old processes must survive, a backfill. Check the provider is deployed, not only merged.

Refactoring and behaviour change go in separate commits, refactoring first with green tests; the body names both in one line each.

## Steps

1. Check the body: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/pr_check.py [--ui] [--template <template.md>] <body.md>` (`--ui` when the diff changes a file of lens `ux`; `--template` with the repo template you found). Fix until OK.
2. `gh pr create --draft --body-file <body.md> --title "<imperative, ≤ 70 chars>"`.
3. `python3 ${CLAUDE_PLUGIN_ROOT}/tools/tracker.py link <issue-ref> <pr-url>`, then `set-state <issue-ref> review` only when the PR leaves draft.

## Code comments in the diff

Before opening, scan the diff's comments. A comment says only one of:
- **why** the code is this way (a non-obvious reason),
- an **invariant** the code relies on,
- a **deliberate omission** ("no retry: the caller retries"),
- a **hidden contract**: a side effect, unit or precondition the signature does not show.

Remove comments that contain ticket numbers, review history ("as discussed", "fixed per review"), internals of other repos, or restate the code.
