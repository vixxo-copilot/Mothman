---
name: bmad-code-review
description: >-
  Runs a structured adversarial code review focused on correctness, regressions,
  edge cases, and test adequacy with prioritized findings.
---

# BMAD Code Review

## When to use

Use this skill when the user asks to:

- review a pull request or working diff
- identify bugs and risky assumptions before merge
- validate acceptance criteria coverage

## Review output format

Return findings in this order:

1. **Critical** - correctness, data loss, security, or crash risks
2. **High** - likely behavioral regressions
3. **Medium** - edge-case or maintainability concerns
4. **Low** - polish and consistency issues
5. **Test gaps** - missing or weak validation

## Workflow

1. Read requirements and acceptance criteria.
2. Inspect changed files and related test updates.
3. Validate behavior against expected user outcomes.
4. Probe edge cases and failure paths.
5. Verify tests cover the changed behavior.
6. Recommend concrete fixes with file-level guidance.

## Guardrails

- Prioritize functional risk over stylistic preference.
- Do not report speculative issues without evidence.
- Keep findings actionable and reproducible.
