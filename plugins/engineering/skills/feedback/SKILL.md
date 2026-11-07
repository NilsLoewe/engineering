---
name: feedback
description: Work through review feedback (PR threads, review bodies) and QA feedback (ticket comments) for one PR and its ticket. Sorts every human point into bug, spec gap, out of scope or style, acts per class, answers in the channel the point came from with what now applies, and keeps the ticket's spec the one place where decisions live. Use for "handle the review", "address feedback on <pr>", "QA asked questions on <ticket>", or when a PR sits in CHANGES_REQUESTED.
argument-hint: <pr-ref> [<ticket-ref>] [--dry-run]
---

# feedback

A decision made in a review thread is lost unless it reaches the spec. QA reads the ticket, not the PR.

`$T` = `python3 ${CLAUDE_PLUGIN_ROOT}/tools/tracker.py` (add `--config <file>` when a world overlay in your context names an engineering tracker config), `$C` = `python3 ${CLAUDE_PLUGIN_ROOT}/tools/feedback_collect.py`. Dry run: add `--dry-run` to every tracker write, and show GitHub replies instead of posting them.

## 1. Collect

`$C <pr-ref> [<ticket-ref>] > fb.json`: every inline thread, review body and PR comment, plus the ticket comments since the PR was opened. Work on `kind: human` points; read `agent` and `bot` points only to see what is already fixed. A review body counts point by point, not as one item. Also read the spec comment (`🤖 clarify · spec`) and the code on the PR branch.

## 2. Classify

Each human point gets exactly one class. Ask: "Does the answer change what the owner or QA would accept?"

| Class | Test | Example |
|---|---|---|
| **a bug** | The code contradicts the spec or loses data, an event or a trace. | A guard files a real event into an archive nobody watches. |
| **b spec gap** | Behaviour nobody decided: who sees what, what happens when, setup, rollout, how QA tests it. | Which sender address maps a mail to a company. |
| **c not this ticket** | Another repo or feature has to change, or it is a follow-up. | The box should mark a first poll as seen. |
| **d style** | Readability, pattern, comment, test shape. Behaviour stays the same. | Comment longer than one line. |

A point that is both a bug and a decision is **b**: the decision comes first. Details and edge cases: [classes.md](classes.md).

## 3. Act per class

- **a** → fix on the PR branch, test first (it fails without the fix), then the `verifier` agent against the spec. Never judge your own fix.
- **b** → back to `clarify`: add a question with a proposal to the spec comment and `$T assign <ticket> <owner>`. Do not pick the answer yourself, not even "for now". Once the owner answered: bump the spec version, then fix. A decision someone reports from Slack or a call goes into the spec, with name and date.
- **c** → propose a new ticket (title, one line why, owner) to the user. Create it only after the user says yes. Never promise "follow-up after merge" without the ticket ref.
- **d** → fix. Check `katalog/*.yaml` for the rule. If the same kind of point came twice in this PR or the rule is missing, name it as a catalog candidate at the end.

## 4. Answer where the point came from

The answer says **what applies now** and **the commit**, in one to three sentences. "Fixed in abc123" alone does not count.

- GitHub point → reply in its thread. Ticket point → reply to that comment in the ticket.
- Never copy a discussion into the other system. The spec comment gets the decision, not the thread.
- Each spec edit adds one line at the end: `**Changes since v<N>:** <what changed, 1 line, with commit or thread link>`.
- A status update in the ticket names what changed for QA, not "all findings fixed, CI green".

## 5. Report

One table: point (link and keyword), class, action, commit or question, answered yes/no. Then the counts per class and the catalog candidates. Stop after the report; `pr` and `clarify` do their own steps.
