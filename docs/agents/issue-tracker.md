# Issue tracker: GitHub

Repository: Whitecatuwu/ominous-trial-predictor.
Issues and ticket specifications live in GitHub Issues. Use the gh CLI
with --repo Whitecatuwu/ominous-trial-predictor.

## Operations

- Publish a ticket: gh issue create.
- Read a ticket: gh issue view <number> --json number,title,body,labels,comments.
- List tickets: gh issue list, using appropriate state and label filters.
- Comment: gh issue comment <number>.
- Apply or remove labels: gh issue edit <number> --add-label / --remove-label.
- Close a completed ticket: gh issue close <number>.
- For multiline bodies and comments, write a UTF-8 temporary file and
  pass --body-file.

## Parent tickets and dependencies

Use native GitHub sub-issues and issue dependencies when available.
Otherwise, record "Part of #<parent>" and "Blocked by: #<number>"
at the top of child issue bodies, and list children in the parent.
A ticket is unblocked when all its blockers are closed.

For wayfinder, use one map issue labelled wayfinder:map and child tickets
labelled wayfinder:<type> (research, prototype, grilling, or task).
Choose the first open child in map order with no open blockers or assignee.
Claim it by assigning yourself. On resolution, record the result, close
the child, and add a decision pointer to the map.

## Pull requests as a triage surface

PRs as a request surface: no.
