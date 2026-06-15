---
name: bmad-quick-dev
description: >-
  Executes focused implementation quickly from a clear requirement using tests-first
  flow, small diffs, and repository-convention alignment.
---

# BMAD Quick Dev

## When to use

Use this skill when the user asks to:

- implement a story or bug fix quickly
- make targeted feature changes with low process overhead
- translate requirements directly into working code and tests

## Output contract

Return:

1. Implementation summary
2. Files changed
3. Tests added or updated
4. Validation results
5. Remaining risks or follow-ups

## Workflow

1. Clarify the exact requirement and acceptance criteria.
2. Read only the minimal required code surface and existing tests.
3. Write or update failing tests first where practical.
4. Implement the smallest viable change to pass tests.
5. Run focused tests, then broader regression checks.
6. Report scope, evidence, and unresolved risks.

## Guardrails

- Keep changes scoped to the requested outcome.
- Preserve existing architecture and naming conventions.
- Avoid speculative refactors unrelated to acceptance criteria.
- Do not mark work complete without test or runtime evidence.
