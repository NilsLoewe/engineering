<!-- Erzeugt von tools/build_katalog.py aus katalog/. Nicht von Hand ändern. -->
# Lens: Framework and language idiom at the pinned versions

Intent: the code uses its framework the way it works at the versions in the lockfile, not the newest docs. A finding names the API, the pinned version and what it does there; unsure about an API, look it up for that version (Context7 or the installed gem/package source) before you report. Taste is not a finding. Something a linter can catch belongs in the linter config: name the rule instead of repeating it per PR.

- A call that returns a new object (Rails params.permit, merge, frozen or immutable values, map) is used through its result; a mutation of a fresh copy that the next call throws away is a bug. (severity: major) `[fw-result-not-mutated]`
- A validated number or string fits its database column (integer upper bound, string length); otherwise the database raises and the API answers 500 instead of 422. (severity: major) `[fw-bounds-fit-column]`
- Judge every API at the version in the lockfile; an API deprecated or removed at that version is a finding with the version named, a newer API the pinned version lacks is a bug. (severity: minor) `[fw-pinned-version]`
- A React effect, memo or callback lists exactly what its body reads; no unused and no missing dependency, and an intended exception says why in a comment. (severity: minor) `[fw-effect-deps-match]`
- Render bodies and useMemo stay pure (no randomness, no side effects); a value that must stay stable across renders lives in state or a ref. (severity: minor) `[fw-render-pure]`
- Test setup runs inside the test framework's lifecycle (render and renderHook inside a test or a before hook, never at module scope while tests are collected). (severity: minor) `[fw-test-lifecycle]`
- Where the pinned framework has a helper for what the diff hand-rolls (response.parsed_body, have_http_status, normalizes), use it, unless a comment says why not. (severity: minor) `[fw-use-framework-helper]`
