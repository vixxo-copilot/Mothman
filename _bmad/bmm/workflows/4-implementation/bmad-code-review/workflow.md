# BMAD Code Review Workflow

Use this checklist during implementation review:

1. Confirm acceptance criteria have direct implementation evidence.
2. Confirm all `[x]` story tasks are actually completed in code/docs.
3. Cross-check story file list against `git status` and `git diff`.
4. Run full validation/test suites and capture command output.
5. Verify lint/type/static checks (if configured) are green.
6. Record findings with severity and concrete remediation steps.
7. Keep story lifecycle state aligned (`review` until fixes complete, then `done`).
