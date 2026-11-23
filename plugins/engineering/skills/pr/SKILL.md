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
Screens: <UI change only: one screenshot link per changed state>
Deploy: <order of migration, backfill, flag and other repos' PRs; or "independent">
```

`Screens:` only when the diff changes what a user sees. A screenshot shows the states, not proof of usability; the evidence lines still name the test or the walk-through.

No spec, no file list, no changelog of review rounds, no tool chatter.

`Deploy:` names what must ship first: a provider route or column the code calls, a migration old processes must survive, a backfill. Check the provider is deployed, not only merged.

Refactoring and behaviour change go in separate commits, refactoring first with green tests; the body names both in one line each.

## Steps

1. Check the body: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/pr_check.py <body.md>`. Fix until OK.
2. `gh pr create --draft --body-file <body.md> --title "<imperative, ≤ 70 chars>"`.
3. `python3 ${CLAUDE_PLUGIN_ROOT}/tools/tracker.py link <issue-ref> <pr-url>`, then `set-state <issue-ref> review` only when the PR leaves draft.

## Code comments in the diff

Before opening, scan the diff's comments. A comment says only one of:
- **why** the code is this way (a non-obvious reason),
- an **invariant** the code relies on,
- a **deliberate omission** ("no retry: the caller retries"),
- a **hidden contract**: a side effect, unit or precondition the signature does not show.

Remove comments that contain ticket numbers, review history ("as discussed", "fixed per review"), internals of other repos, or restate the code.
