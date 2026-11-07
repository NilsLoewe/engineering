# The clarify comment

**One comment per issue**, edited in place on every run (`--key spec`). It reads top to bottom for the owner: what we found and what will be built, then the questions. Answers come as replies to this comment.

Markdown-lite only: `**bold**`, `- ` lists, `1. ` lines, blank lines. The tracker turns it into HTML (Monday) or keeps it (GitHub); numbered lines keep their visible number, so "question 3" always points somewhere. Do not write the `🤖 clarify · spec` head line; the tracker adds it.

Budget: **≤ 20 lines** in total, each line ≤ 25 words, **at most 5 questions**. Details (telegrams, class names, test data) belong in the code and the PR.

```
**Spec v1** · waiting for <owner> | READY

**Finding:** <the one thing the owner must know, 1-2 sentences; omit if nothing surprising>

**Goal:** <who gets what, 1-2 sentences>

**Acceptance**
1. <situation> → <observable result>
2. (edge) <situation> → <result>
3. (error) <situation> → <result>

**Not included:** <scope cuts, or "nothing">

**For developers:** <repos in order, provider first; technical proposals in one line each>

**Open questions for <owner>** · please reply to this comment, e.g. "1 yes, 2 no: …"
1. **(blocking) <short question>?** Proposal: <concrete default>.
2. **<short question>?** Proposal: <…>.
```

One question = one decision with one proposal, so "4 yes" settles it. Two decisions are two questions; never join them with "and" or a second question mark.
Acceptance and questions are numbered separately; an acceptance line that depends on a question names it: `… (per question 2)`. No questions: `**Open questions:** none`.
After answers: each question line ends with `→ yes` / `→ no: <answer>` (`ready_check.py` counts lines without `→` as open), the head line says `Spec v2`.

- Concrete values (IDs, labels, texts) from the issue where they exist.
- One trigger and one observable result per line; split a line that chains steps with "and then".
- For every number in the issue (limit, timeout, count, duration), one line exactly at the boundary.
- When the issue limits who may act, one line in which the wrong role or another company is refused.
- At least one `(edge)` or `(error)` line. `ready_check.py` checks the headings **Goal**, **Acceptance**, **Open questions**, **For developers**, in any order.
- Cross-repo: provider first, expand before the consumer switches.

## Question checklist

From the questions developers asked *after* starting work (analysis of 363 tickets, 11/2026). Ask only where the issue is silent, and only what the owner decides.

1. **One or many?** (types per record, entries per item, children per parent)
2. **Empty, missing, fallback** — what if the thing does not exist? Old records?
3. **Source of truth** — where does the data come from, who wins on conflict?
4. **Who may do it** — role, tenant, company.
5. **Final list or wording** — is it final, who confirms it?
6. **Existing data and rollout** — backfill? feature flag?
7. **What the user sees on failure.**
8. **How to accept it** — test data, environment, who accepts.
9. **How many, how fast** — expected volume and how long the operator may wait, as an observable result.
10. **The need behind a prescribed solution** — the issue names a screen, field or technique: which operator problem does it solve? State that problem as the Goal.
11. **More than one goal** — propose slices that each work end to end, one issue each.

Interfaces between repos (field, type, format, deploy order) are not owner questions: decide them as a proposal under **For developers**.
