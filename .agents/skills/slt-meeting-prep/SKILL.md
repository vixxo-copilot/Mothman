---
name: slt-meeting-prep
description: >-
  Prepares senior leadership team meeting briefs with clear outcomes, risks,
  decision asks, and evidence-backed talking points.
---

# SLT Meeting Prep

## When to use

Use this skill when the user asks to:

- prepare for a senior leadership team meeting
- build a leadership pre-read with decision asks
- summarize business risk and delivery confidence for executives
- produce concise talking points for SLT updates

## Output format

Return the prep brief in this order:

1. **Meeting objective and outcomes**
2. **Executive snapshot** (headline, confidence, top risk)
3. **Decision asks** (owner, decision deadline, impact)
4. **Risk and mitigation view**
5. **Talking points** (role-specific, concise)
6. **Follow-ups to capture live**

## Workflow

1. Confirm SLT audience, meeting objective, and target decisions.
2. Pull supporting signals from calendar, communication, and work tracking.
3. Distill updates into impact-oriented headlines and explicit asks.
4. Build decision-ready talking points with evidence and trade-offs.
5. End with a short checklist for in-room follow-through.

## Microsoft 365 and Linear guidance

- Use Microsoft 365 calendar and message context for meeting readiness.
- Do not combine `$search` and `$filter` in the same Graph request.
- Pull Linear delivery signals to ground risks and deadlines.

## Guardrails

- Do not invent metrics, commitments, or executive positions.
- Keep language concise, neutral, and action-focused.
- Highlight unknowns explicitly when context is incomplete.
