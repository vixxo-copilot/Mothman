---
name: review-teams-pulse
description: >-
  Reviews Microsoft Teams activity to identify high-signal threads, unanswered
  asks, decision blockers, and follow-ups that need owner assignment.
---

# Review Teams Pulse

## When to use

Use this skill when the user asks to:

- summarize important Teams activity
- identify missed mentions or pending replies
- detect escalations, blockers, or decision drift in chat threads
- produce a daily pulse report for team communication health

## Output format

Return results in this order:

1. **High-signal threads** (topic, participants, current state)
2. **Unanswered asks** (owner, age, urgency)
3. **Decision blockers** (what is blocked and why)
4. **Recommended follow-ups** (message target, suggested action, due date)

## Workflow

1. Confirm lookback window and channels/chats in scope.
2. Pull recent Teams messages, mentions, and flagged conversation threads.
3. Cluster messages by topic and detect unresolved asks.
4. Prioritize items by urgency, impact, and elapsed response time.
5. Draft concise follow-up actions with owner and expected timing.

## Microsoft 365 guidance

- Use scoped queries and modest page sizes for messages.
- Do not combine `$search` and `$filter` in a single Graph request.
- Keep search expressions properly quoted where required.

## Guardrails

- Do not infer intent without message evidence.
- Distinguish explicit asks from informational chatter.
- Keep output concise and ready to act on.
