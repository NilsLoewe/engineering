---
name: clarify
description: Clarify an issue before any code is written. Keeps one living comment in the issue - finding, goal, acceptance examples, repos, and at the end the numbered questions for the owner - and edits it on every run instead of posting a new one. Run again after the owner answered to fold the answers in and check Ready. Use for "clarify <issue>", "refine this ticket", or before starting work on an issue that is not Ready.
argument-hint: <issue-ref> [<issue-ref> ...] [--in-flight] [--dry-run]
---

# clarify

The agent clarifies, the owner decides. Never invent an answer.

`$T` means `python3 ${CLAUDE_PLUGIN_ROOT}/tools/tracker.py`. Add `--config <file>` when a world overlay in your context names an engineering tracker config. Dry run (user asks, or `TRACKER_DRY_RUN=1`): add `--dry-run` to every write and show the output instead of claiming it was posted.

**One comment, never more.** Always write with `--key spec`; the tracker edits the existing comment. Never post a second comment, never repost to fix it — edit it. Format, budget and the question checklist: [spec-format.md](spec-format.md). Write in the issue's language.

## Several issues

Given more than one ref: spawn one general-purpose subagent per ref with the Agent tool, at most 4 at a time, each with exactly this task: "Invoke the skill engineering:clarify with the argument <ref> (add --in-flight and --dry-run if this run has them). Return its 3-line summary." A subagent that meets an issue in progress without `--in-flight` reports it and stops; list those refs at the end. Never clarify an issue yourself in the batch and never give a subagent a free-text task instead. Then show one table: ref and title, questions, owner it went to, the main finding.

## First run

1. `$T read <ref>`. State `in-progress` or `review` without `--in-flight`: stop and report it; offer `--in-flight`. State `done`: stop.
2. Follow every link in the issue and its comments. Google Docs/Sheets/Slides: read them with the workspace's drive connector (`drive_read_file` with the id from the URL). Anything you cannot read (Lovable, Loom, images, a missing permission): name it in the comment and do not guess its content.
3. Read the affected code: repos and modules the issue touches, interfaces between repos. **Today's state** (counts, "today it does X") comes from the base branch (`git show origin/<base>:<path>`), not from whatever is checked out; work in progress comes from its feature branch.
4. Sort what you found:
   - **Owner decisions** (behaviour, scope, wording, who may do it, what is done when) → the questions at the end. Each with a proposal the owner can accept with "yes". Few and sharp; blocking ones first.
   - **Technical choices** (contract format, deploy order, class to change) → "For developers", as a proposal. The plan review in `build` approves them, not the owner.
   - Only ask what the issue, comments and code do not answer.
5. `$T comment <ref> --key spec --body-file spec-<ref>.md`. Write it with the Write tool to a file of its own, `spec-<repo>-<number>.md` or `spec-<item-id>.md` in your scratchpad: parallel runs share the scratchpad, and a shared name posts the wrong ticket's text. Then `$T set-state <ref> clarifying`, then `$T assign <ref> <owner>`: the person the questions go to (usually who wrote the issue or the PO; ask the user if unclear). No questions → do not reassign.
6. Tell the user in 3 lines: number of questions, the one finding that matters most, the ref. Stop. Do not implement.

## In flight (`--in-flight`, for issues already in progress, review or QA)

The work exists; the spec becomes the yardstick for review and QA. Never change state or assignee.
1. Read the issue, its links, its PRs (`gh pr list --search <id>` in the affected repos, or links in the issue) and the code on the PR branch and on the base branch.
2. Write the one comment (`--key spec`), head line `**Spec v1 (in flight)** · <state>`:
   - **Finding:** where the work stands (merged where, deployed where) and the biggest gap between the ask and the build.
   - **Acceptance:** what the build must show, written so QA can test it line by line; mark lines the code does not meet yet `(not met yet)`.
   - Questions only where acceptance is impossible without the answer. No questions about decisions the code has already made unless they are wrong.
3. Report the gap in 3 lines. Do not run `set-state` or `assign`.

## Every later run

Re-read the issue, its links and the code from scratch, even when you remember them from this session. Check every fact in the comment again; fix a wrong one by editing the comment. No new answer and no wrong fact → change nothing and say so.

## Second run (owner answered)

1. `$T read <ref>`. Answers are the replies to the clarify comment (`reply_to` = its id) and any later comment by the owner.
2. Edit the comment: fold each answer into goal and acceptance, append it to its question (`→ yes`, `→ no: …`), bump the version. An unclear answer stays open; do not resolve it yourself.
3. `$T read <ref> | python3 ${CLAUDE_PLUGIN_ROOT}/tools/ready_check.py`.
4. READY → tell the user; `$T set-state <ref> ready` only if the user is the owner and says so. NOT READY → list what is missing and `$T assign` the issue back to whoever must answer.

Your own proposal is never an answer, even when the user says "answer them yourself". Write `→ proposal taken over by <user>, <date>` on the question and keep any question the owner or the acceptor must decide (acceptance, wording, limits you made up) open for them. A number or limit you chose yourself is a question, not a fact.
