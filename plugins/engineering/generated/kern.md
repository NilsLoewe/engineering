<!-- Erzeugt von tools/build_katalog.py aus katalog/. Nicht von Hand ändern. -->
# Core rules (always apply)

- Every new guard, branch or fix has a test that fails when the change is removed; happy-path-only or self-confirming tests do not count. `[kern-test-fails-without-fix]`
- Before adding a helper, hook, scope or component, find how the codebase already does it and reuse that; never add a second way. `[kern-reuse-existing-pattern]`
- Never swallow an error or return early without a trace; report it (error tracker, error state, user message) or let it fail loudly. `[kern-no-silent-failure]`
- Remove dead code in the same change - unused methods, exports, variables, props, branches. `[kern-remove-dead-code]`
- A comment states a why, an invariant or a deliberate omission of the current code; no history, ticket numbers or other repos' internals, and never longer than the code it explains. `[kern-comment-why-only]`
- Keep secrets and personal data out of logs, job arguments, error reports and the browser console. `[kern-no-secrets-in-logs]`
- The PR description matches the code - behaviour, deploy order, manual steps; unrelated changes go into their own PR. `[kern-pr-text-matches-code]`
- For every field, parameter or signal that crosses a repo, open the other side's source at its merged or deployed ref and compare type, casing, null vs empty, ranges, version and deploy order. `[kern-check-the-other-side]`
- Validate every request parameter and every value interpolated into a path, query or regex. `[kern-validate-input]`
- Names say what a thing is in domain terms; rename when the scope grows. `[kern-honest-names]`
- Do not run the same query, request or parse twice in one path; no per-row fan-out. `[kern-query-once]`
- A new validation, scope or guard names every path that skips it (bulk updates, raw SQL, imports, other writers, unscoped reads) and covers or rejects each. `[kern-list-bypass-paths]`
