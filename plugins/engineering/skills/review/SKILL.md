---
name: review
description: Review a pull request with fresh-context reviewer agents against the spec, the core and world rules and the matching lenses, and post one visible GitHub review (comment only, never approve). Use for "review <pr>", "review this PR", or before marking a PR ready.
argument-hint: <pr-url | owner/repo#n> [--dry-run]
---

# review

You orchestrate; you do not review. Reviewers are subagents that did not write the code (rule 5). `$T` = `python3 ${CLAUDE_PLUGIN_ROOT}/tools/tracker.py` (add `--config <file>` when a world overlay in your context names an engineering tracker config).

1. **Gather.** `gh pr view <n> -R <repo> --json title,body,headRefOid,files` and `gh pr diff <n> -R <repo>`. Ticket link in the body → `$T read <ref>`, take the `🤖 clarify · spec` comment. No spec → say so in the review body; review against the PR text.
2. **Pick lenses.** Read `${CLAUDE_PLUGIN_ROOT}/generated/linsen/index.json` and every lens index a world overlay in your context names. A lens applies when a changed file matches its `pfade` and, if it has `inhalt`, an added line matches that regex. At most 4 lenses; prefer the ones whose files the diff touches most.
3. **Review in parallel.** One general-purpose subagent per lens plus one general reviewer, each with: the diff, the spec, its lens file (the general reviewer: core and world rules from context, plus "does the code do what the spec says, and nothing else"). Task: "Report only real problems you can point to in the diff, as JSON `[{path, line, severity, rule, text}]`; line = line number in the new file; severity blocker (breaks data, security, the spec) | major (wrong behaviour, missing test for a new branch) | minor; text = what is wrong, why it matters, the fix, ≤ 4 sentences. No style taste, no praise, no summary."
4. **Merge.** One list; drop duplicates (same path, nearby line, same problem); keep at most 5 minor. A finding without a concrete line goes in with the nearest changed line or none.
5. **Post.** Write the list to a file of its own (`review-<repo>-<pr>.json` in your scratchpad, never a shared name), then `python3 ${CLAUDE_PLUGIN_ROOT}/tools/review_post.py <repo> <n> <file>` (add `--dry-run` for a dry run). It posts one review with event COMMENT; lines GitHub cannot anchor go into the body.
6. **Report** in 3 lines: counts by severity, the most serious finding, the review link. Whether blocker/major block the merge is the world's rule (see its context).

Repeated findings of the same kind across PRs are rule candidates for the world catalog (rule 6); name them, do not add them yourself.
