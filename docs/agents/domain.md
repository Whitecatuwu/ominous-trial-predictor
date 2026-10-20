# Domain docs

## Layout and reading rules

This repository uses a single-context layout:
- GLOSSARY.md at the repository root.
- Architecture decision records under docs/adr/.

Before exploring domain concepts, read GLOSSARY.md if present.
Before working on architecture, read ADRs relevant to the affected area.
If these files do not exist, proceed silently. The domain-modeling skill
creates them when terms or decisions are resolved.

## Vocabulary and decisions

Use glossary terms consistently in issue titles, proposals, and tests.
When a needed concept is missing, identify the gap for domain-modeling.
Explicitly flag proposals that contradict an existing ADR and explain
why the decision should be reconsidered.
