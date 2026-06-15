---
name: daily-briefing
description: >-
  Builds a work-only morning briefing from Outlook and calendar signals, Linear
  priorities, and Teams activity so the day starts with clear actions.
---

# Daily Briefing (Work-Only)

## When to use

Use this skill when the user asks to:

- prepare a morning work briefing
- identify top tasks and delivery risk for today
- summarize urgent collaboration activity
- compile follow-ups before the first meeting block

## Output format

Return the briefing in this order:

1. **Priority items** (must-do today, ordered by urgency and business impact)
2. **Blockers and risks** (dependencies, waiting states, and escalation needs)
3. **Follow-ups** (messages, tickets, or meetings that need owner/date)
4. **Unresolved items** (missing context that blocks confident action)

## Workflow

1. Confirm scope: timezone, lookback window, and what "today" covers.
2. Pull Outlook inbox + calendar signals from Microsoft 365 tools:
   - urgent mail and flagged threads
   - meeting load, prep gaps, and timing conflicts
3. Pull Linear work signals:
   - active issues with due-date pressure
   - blocked work, stale items, and ownership gaps
4. Pull Teams signals:
   - direct mentions and high-signal threads
   - open decisions or asks awaiting response
5. Merge findings into the output format and propose the first execution sequence.

## Guardrails

- Keep evidence grounded in system data; label assumptions clearly.
- Avoid speculative priorities when urgency indicators are missing.
- Keep each action concise and executable by the user in one pass.
- Focus strictly on Outlook, Linear, and Teams operating context.

## Microsoft 365 and Linear guidance

- Do not combine `$search` and `$filter` on the same Microsoft Graph request.
- Keep Microsoft Graph message search queries double-quoted.
- Use modest page sizes and follow `@odata.nextLink` for continuation.
- Use Linear cursor pagination (`first`/`after`) for issue lists.
