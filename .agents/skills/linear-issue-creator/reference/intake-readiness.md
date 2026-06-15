# Intake-Readiness Bar

Every issue this skill creates must clear the automated **`intake-audit:v1`**
readiness check before it lands in an execution backlog. An in-Linear readiness
agent applies the same bar: when an issue fails, it posts a "needs work" comment
and moves the issue to a **Needs Clarification** state. Author issues that pass
on the first audit run.

Pick the checklist that matches the issue's Work Type. The Work Type also selects
the description template below.

## Bug readiness checklist

A `Bug` clears the bar only when its description contains **all** of:

1. **Ordered steps to reproduce** — a numbered list someone else could follow.
2. **Expected result** — what should happen.
3. **Actual result** — what actually happens (the defect).
4. **Domain identifiers** — at least the ones that apply: SR #, order #,
   customer, environment (prod/test). Never leave this empty for a bug.

What good looks like (the `intake-audit:v1` reference example):

```text
Steps to reproduce:
1. Open SR #72760207 in Siebel prod
2. Submit scope with full work description text

Expected: Full work description appears in scope sent to provider
Actual:   Only first word ("Hello") appears in scope

SR #: 72760207 | Customer: [name] | Environment: prod
```

## Story / Chore / Feature readiness checklist

Non-bug execution work clears the bar only when its description contains
**all** of:

1. **Clear problem statement** — the problem or need being solved.
2. **Desired outcome** — what "done" looks like / the expected behavior.
3. **Identifiers / affected systems** — system(s), customer, and requester where
   known, so the work has concrete domain context.

## Business Request items

Decomposition Side 1 business-request items use the Feature/Improvement template
below. They still need a clear problem statement, desired outcome, requester,
and any deadline, but they are not held to the bug repro-steps bar because they
describe a business ask, not a reproducible defect.

## Readiness gate (run before any draft)

For each issue, evaluate the parsed content against the checklist for its Work
Type:

- If every required field is present, mark it **Readiness: PASS**.
- If any required field is missing from the source, mark it
  **Readiness: NEEDS INPUT** and list exactly which fields are missing. Do
  **not** silently create it — ask the user to supply the missing details, or to
  explicitly confirm creating a lower-quality item that will likely fail
  `intake-audit:v1`. Prefer gathering the missing context first.

Surface the readiness result in the draft so the user sees it before confirming.

## Description templates

Use real Markdown with real newlines. Never emit literal `\n` escape sequences
in the description string — they render as visible `\n` text in Linear.

### Bug template

```markdown
## Problem

[One-line problem statement]

## Steps to Reproduce

1. [ordered step]
2. [ordered step]

## Expected vs Actual

- **Expected:** [what should happen]
- **Actual:** [what happens instead]

## Identifiers

SR #: [...] | Order #: [...] | Customer: [...] | Environment: [prod/test]

## Context

**Source:** [Email / Teams / Slack / Verbal note]
**Requester:** [Name if known]
**Date:** [Date if known]

## Original Feedback

> [Quoted original text from the feedback]
```

### Story / Chore / Feature / Business Request template

```markdown
## Request

[Parsed requirements in clear bullet points]

## Desired Outcome

[What "done" looks like / the expected behavior once delivered]

## Identifiers / Affected Systems

System(s): [...] | Customer: [...] | Requester: [...]

## Context

**Source:** [Email / Teams / Slack / Verbal note]
**Requester:** [Name if known]
**Date:** [Date if known]

## Original Feedback

> [Quoted original text from the feedback]
```
