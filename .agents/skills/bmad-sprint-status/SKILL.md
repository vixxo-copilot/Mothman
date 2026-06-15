---
name: bmad-sprint-status
description: >-
  Summarizes sprint progress, highlights delivery risk, and recommends the next
  best workflow action from current story states.
---

# BMAD Sprint Status

## When to use

Use this skill when the user asks to:

- check sprint progress and blockers
- summarize story and epic status quickly
- decide what workflow to run next

## Output format

Return:

1. **Sprint snapshot** (counts by status)
2. **At-risk items** (story key and reason)
3. **Recommended next action** (workflow + target story)
4. **Suggested mitigation steps**

## Workflow

1. Read current sprint status data source.
2. Classify epics/stories by lifecycle status.
3. Detect risk patterns (stale work, review pile-up, blocked progression).
4. Select a single next workflow recommendation.
5. Present concise status plus mitigation actions.

## Guardrails

- Preserve status terminology used by the project.
- Flag unknown status values explicitly.
- Keep recommendations tied to visible evidence.
