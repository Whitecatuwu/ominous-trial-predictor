# Repository Guidelines

## Project Structure & Module Organization

This repository is currently specification-only. Read `SPEC.md` before implementation, test design, or changes to supported versions; it defines the accepted behavior and release gates. No source, tests, assets, or build configuration exist yet.

When scaffolding, separate the pure calculation core, CLI, GUI, version data, translations, and validation fixtures. Produce independent GUI and CLI JARs sharing the same core. Document the actual module paths when introduced. Validate the core before completing interfaces.

## Build, Test, and Development Commands

Run commands from the repository root:

- `java -version` — check the required 64-bit Java 25 runtime.
- `git status --short` — inspect pending changes.
- `git diff --check` — check tracked changes for whitespace errors.

Build, launch, lint, and test commands are not configured. Add reproducible commands and a build wrapper when introducing the build system. Acceptance targets Windows 11 x64; normal execution must work offline. Docker Minecraft instances are for development and version validation.

## Coding Style & Naming Conventions

For new Java code, use four-space indentation, `UpperCamelCase` classes, `lowerCamelCase` methods and variables, and `UPPER_SNAKE_CASE` constants. Keep calculation logic independent of UI and file handling. No formatter or linter is configured yet; document any tools introduced.

Keep structured output keys and identifiers in English. Follow `SPEC.md` for localization, numeric bounds, CSV parsing, and source preservation.

## Testing Guidelines

No test framework or coverage percentage is established. Introduce automated tests with the core; use descriptive names such as `CsvImporterTest`.

Follow `SPEC.md` section 10: each target version requires vanilla reference results, fixed edge cases, and at least 10,000 reproducible seed/coordinate combinations. Save inputs, expected and actual results, and pass records. Separately validate 10,000-row GUI/CLI batches, malformed rows, cancellation, exports, and exit codes. Keep versions `unverified` until evidence satisfies the specification.

## Commit & Pull Request Guidelines

There is no commit history yet. Use focused Conventional Commits, for example `feat(core): add seed validation` or `docs: clarify CSV contract`.

PRs should explain what changed, why, relevant specification sections or issues, validation commands and results, and remaining limitations. Include screenshots for GUI changes and reproducible evidence for version-support claims.
