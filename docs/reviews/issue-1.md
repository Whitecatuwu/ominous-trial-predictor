# Issue #1 review

Date: 2026-10-20 (Asia/Taipei).

Scope: [#1 — 26.2 原版參考查詢可重現](https://github.com/Whitecatuwu/ominous-trial-predictor/issues/1), under SPEC.md. User-approved base: `da2c1f80826c9f8408005156008b0e7533383c81`.

Applied the `code-review` skill with independent read-only Standards and Spec agents. To honor the requested review-before-commit order, both inspected `git diff --cached da2c1f8 --` against the complete staged candidate rather than the then-unchanged HEAD. No commits existed after the base at review time. No source changes were needed after review.

## Standards

No Standards findings.

Reviewed the complete staged candidate, including Java adapter/normalizer, Python wrapper and tests, Docker configuration, fixtures, evidence, version data, and documentation.

- No documented-standard violations found under AGENTS.md and its referenced SPEC.md conventions.
- No meaningful actionable baseline smells found. The adapter invokes vanilla logic; calculation-core separation and independent product JAR requirements remain future work, correctly outside issue #1.
- Version status consistently remains `unverified`; documentation distinguishes reference-query evidence from core and release acceptance.
- Staged whitespace checks passed. Working files matched the staged candidate.

Limitations: read-only source/evidence review; Docker and tests were not rerun by this reviewer, and upstream Minecraft behavior was not independently revalidated.

## Spec

No actionable findings for issue #1.

- Missing/partial requirements: none within #1. Fixed official artifacts and Java image, seed/XYZ/world-state records, rerunnable Docker commands, complete normalized item/effect data, fixed reference cases, and separate version progress are present.
- Scope creep: none. Implementation stays within the development reference query and supporting evidence.
- Implemented-looking but incorrect behavior: none identified. The observer calls vanilla dispensing logic; zero mixed seeds produce `requires_world_state` with `result: null`; instant effects have null base durations; 26.2 remains `unverified`.

Inspected source, fixtures, and saved five-invocation evidence without running tests or Docker. These are dispensing candidates and weights with a fresh world/cache premise. Offline core comparisons remain zero; 10,000-case core validation, Windows 11 release acceptance, existing caches, and actual event timing are outside this issue.

Standards: 0 findings, no worst issue. Spec: 0 findings, no worst issue.

## Main-agent validation

- `python scripts/reference.py prepare`: passed official outer/inner JAR hash checks and Java 25 compilation with `-Xlint:all,-classfile -Werror`.
- `python -m py_compile scripts/reference.py validation/reference/tests/test_query.py`: passed.
- `python -m unittest discover -s validation/reference/tests -v`: passed, 2 test methods, 5 fresh-world invocations, 143.649 seconds. The fixed-case method covers 3 seeds / 19 rows (18 `ok`, 1 `requires_world_state`) and runs original-registry compound/instant normalization assertions in each fixture invocation.
- Same-input results matched across two fresh worlds; all three fixed-case expected/actual SHA-256 pairs matched.
- Independently checked all 30 archived artifact hashes and 8 source hashes against staged Git blobs; all matched.
- `git diff --cached --check`: passed.

See [evidence summary](../../validation/reference/evidence/2026-10-20/summary.json) and [full suite log](../../validation/reference/evidence/2026-10-20/full-suite.log). Host was Windows 10 x64; Windows 11 product/release acceptance was not run. All target versions remain `unverified`. Issue #2 was not started.
