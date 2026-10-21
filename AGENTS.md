# Repository guidelines

- Before implementation, test design, or version-support changes, read `SPEC.md` for behavior and release gates. Keep versions `unverified` until its evidence requirements pass.
- For current module paths, build wrappers, checks, EULA consent, and environment diagnostics, read `README.md`. For evidence handling or bytecode exploration, read `docs/development.md`.
- Before changing the reference adapter, read `docs/reference-26.2.md`; it documents registry initialization and world-state boundaries.
- Separate the future calculation core, CLI, GUI, version data, translations, and fixtures. Deliver independent GUI and CLI JARs sharing the pure core; validate that core before completing interfaces.
- Java: four spaces, UpperCamelCase classes, lowerCamelCase methods/variables, UPPER_SNAKE_CASE constants. Keep calculation independent of UI/files and structured identifiers in English.
- Python tests: use native pytest with plain `assert`, fixtures, `pytest.mark.parametrize`, and `monkeypatch`; do not use unittest. When updating existing unittest tests, convert them to native pytest.
- Use focused Conventional Commits. PRs describe behavior, relevant spec sections, validation, and limitations; GUI changes include screenshots and version claims include reproducible evidence.
- Before completing a review, check whether changed behavior invalidates README, agent navigation, or validation documentation. Use the check command for mechanical rules and review for behavioral consistency.

## Agent navigation

- Before reading or publishing tickets, read `docs/agents/issue-tracker.md`. Issues: Whitecatuwu/ominous-trial-predictor.
- Before triaging issues, read `docs/agents/triage-labels.md`; use the five default triage labels.
- Before exploring domain concepts or proposing architecture changes, read `docs/agents/domain.md` (single-context layout).
