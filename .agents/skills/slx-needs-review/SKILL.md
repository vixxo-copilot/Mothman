---
name: slx-needs-review
description: >-
  Triage helper for SLX review queues that highlights stale items, missing
  approvals, ownership gaps, and the next best action per item.
---

# SLX Needs Review

## When to use

Use this skill when the user asks to:

- triage an "SLX needs review" queue
- identify stale review items and escalation candidates
- prioritize what to review first
- summarize blocked approvals for follow-up

## Output format

Return the review triage in this order:

1. **Queue snapshot** (total items, stale count, urgent count)
2. **Top priority items** (with review reason and deadline risk)
3. **Ownership gaps** (missing reviewer/owner assignments)
4. **Escalation candidates** (why escalation is needed)
5. **Action plan** (ordered next steps)

## Workflow

1. Confirm review scope and SLA or expected response window.
2. Pull review items and classify by age, impact, and dependency state.
3. Detect blockers: missing owner, missing context, and unresolved dependencies.
4. Prioritize items that are urgent, high-impact, or close to breach.
5. Produce a clear queue plan with owner recommendations.

## Linear guidance

- Filter to open work and include due dates when available.
- Prefer explicit status/assignee evidence over inferred urgency.
- Mark confidence lower if any source fields are missing.

## Guardrails

- Do not change ownership or status without explicit user direction.
- Keep recommendations specific and executable.
- Avoid adding tool output noise; summarize only what matters.
