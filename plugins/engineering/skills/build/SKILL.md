---
name: build
description: Start implementing an issue, gated on Ready. Checks the spec block, plans in plan mode, implements, hands the diff to the verifier agent, then opens the PR via the pr skill. Use for "build <issue>", "implement <issue>", "start work on <issue>".
argument-hint: <issue-ref> [<issue-ref> ...]
---

# build

No Ready, no code. `$T` = `python3 ${CLAUDE_PLUGIN_ROOT}/tools/tracker.py`. Add `--config <file>` when a world overlay in your context names an engineering tracker config.

1. `$T read <ref> | python3 ${CLAUDE_PLUGIN_ROOT}/tools/ready_check.py`. Not READY → stop, report what is missing, offer `clarify`. Do not work around it.
2. Read the rules the reviewer will hold you to, before you plan: list the files you expect to touch, pick the lenses from `${CLAUDE_PLUGIN_ROOT}/generated/linsen/index.json` and every lens index a world overlay in your context names, as `review` step 2 does but including lenses marked `review: false` and without the limit of 4, and read their files. The plan names, per lens, the rules the change touches and how it meets them. A review that finds what a lens already said is a build defect, not review feedback.
3. Enter plan mode. The plan names, per acceptance line of the spec comment (line 1 = AE1, ...), the test that will prove it. Cross-repo: the provider's contract change is step one, each consumer after it. For every value that crosses a repo (field, parameter, digit count, flag, status code), the plan cites the other side's file:line at its default branch, and for behaviour you rely on, which deployed version provides it; a guard that waits for a value nobody sends yet is dead code. For every new validation or scope, the plan lists the paths that skip it.
4. After the plan is approved: `$T set-state <ref> in-progress`, then implement on a branch. Write the tests for the examples first.
   - Bug fix: run the new spec against the unfixed code and keep the failing output before you apply the fix.
   - A spec fails and you think it failed before your change: run it on the base branch and keep that failure. Without it, your change caused it.
   - UI change (a changed file matches the globs of lens `ux`): run skill `engineering:ui-check change <local url>` before the verifier. Mandatory: its report is the evidence for every acceptance line a user sees and no test asserts, and the PR cannot leave draft without its `Screens:` line (a hook denies `gh pr ready`).
5. Spawn the `verifier` agent with: the spec block, the branch/base, the test command. You wrote the code, so you do not judge it (rule 5).
6. Any example "not proven" or "contradicted" → fix and verify again, or report the gap. Never mark it proven yourself.
7. Then run the `pr` skill.

## Several issues

Two phases, so the user approves every plan once and up front:
1. **Plan, in parallel.** One subagent per ref (Agent tool, at most 4 at a time), read-only: "Check Ready for <ref> with ready_check.py. Not ready: return NOT READY and what is missing. Ready: return a plan as in steps 2 and 3 of skill engineering:build, without changing files." Not ready → leave it out and say so.
2. **Approve, once.** Show all plans together and ask with one AskUserQuestion which to build as planned, which to change, which to drop.
3. **Build, in parallel.** One subagent per approved ref with `isolation: "worktree"`: "Implement <ref> with skill engineering:build, using this approved plan instead of plan mode: <plan>." Steps 4–7 apply unchanged, including verifier and pr.
   - Tests that need Docker: follow the repo's CLAUDE.md on parallel test runs. If it says nothing, run Docker-based builds one at a time.
4. Show one table: ref, PR link, verifier result, what is open.

If the spec turns out wrong or incomplete while building: stop, comment the question in the issue, `$T set-state <ref> clarifying`. That return is a signal, not a failure.
