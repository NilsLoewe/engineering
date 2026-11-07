<!-- Erzeugt von tools/build_katalog.py aus katalog/. Nicht von Hand ändern. -->
# Core rules (always apply)

- Every new guard, branch or fix has a test that fails when the change is removed; happy-path-only or self-confirming tests do not count. `[kern-test-fails-without-fix]`
- Before adding a helper, hook, scope or component, find how the codebase already does it and reuse that; never add a second way. `[kern-reuse-existing-pattern]`
- Never swallow an error or return early without a trace; report it (error tracker, error state, user message) or let it fail loudly. `[kern-no-silent-failure]`
- Remove dead code in the same change - unused methods, exports, variables, props, branches. `[kern-remove-dead-code]`
- A comment states a why, an invariant or a deliberate omission of the current code; no history, ticket numbers or other repos' internals. `[kern-comment-why-only]`
- Keep secrets and personal data out of logs, job arguments, error reports and the browser console. `[kern-no-secrets-in-logs]`
- The PR description matches the code - behaviour, deploy order, manual steps; unrelated changes go into their own PR. `[kern-pr-text-matches-code]`
- Check every cross-repo contract (field, casing, nullability, version, deploy order) in the other repo's source, not by assumption. `[kern-check-the-other-side]`
- Validate every request parameter and every value interpolated into a path, query or regex. `[kern-validate-input]`
- Names say what a thing is in domain terms; rename when the scope grows. `[kern-honest-names]`
- Do not run the same query, request or parse twice in one path; no per-row fan-out. `[kern-query-once]`
