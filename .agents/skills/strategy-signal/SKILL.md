---
name: strategy-signal
description: >-
  Distills delivery context into concise strategic signals that surface risk,
  confidence, decisions needed, and recommended leadership actions.
---

# Strategy Signal

## When to use

Use this skill when the user asks to:

- convert project updates into leadership signals
- summarize delivery confidence and risk
- highlight decision points for managers or SLT
- prepare a concise strategy snapshot before weekly reviews

## Output format

Return the signal in this order:

1. **Current signal** (green/yellow/red with one-line rationale)
2. **What changed** (facts since the previous update)
3. **Strategic risks** (business impact, owner, trigger)
4. **Decisions required** (who decides, by when, consequence of delay)
5. **Recommended next actions** (top 3, ordered)

## Workflow

1. Confirm the scope (initiative, timeframe, and audience).
2. Gather current delivery facts from provided notes and connected systems.
3. Separate evidence from assumptions and label unknowns clearly.
4. Compute the signal from impact, urgency, and confidence indicators.
5. Convert findings into decision-ready bullets for leadership consumption.
6. End with explicit asks, owners, and due dates.

## Linear guidance

- Keep list and search calls bounded to active issues.
- Prefer ownership, due date, and blocking-state evidence over narrative interpretation.
- If Linear data is unavailable, mark confidence reduced and state what is missing.

## Guardrails

- Do not fabricate confidence, metrics, or blockers.
- Keep language neutral and action-oriented.
- Avoid filler prose; prioritize concise decision support.
