---
name: meeting-prep
description: >-
  Builds a pre-meeting brief from available context (participants, recent work,
  open decisions, risks, and agenda) so the user can walk into meetings prepared.
  Use when the user asks for meeting prep, pre-read summaries, talking points,
  or stakeholder briefings.
---

# Meeting Prep

## When to use

Use this skill when the user asks for help preparing for:

- A 1:1, team sync, customer call, or leadership review
- A recurring status meeting that needs quick context refresh
- A decision meeting where risks, blockers, and asks must be explicit

Trigger phrases include:

- "prep me for this meeting"
- "build a pre-read"
- "summarize context for this call"
- "what should I walk in with?"

## Output format

Return a concise prep brief with these sections:

1. **Meeting snapshot** (title, time, objective, participants)
2. **What changed since last touchpoint** (facts only)
3. **Open decisions and blockers**
4. **Stakeholder-specific talking points**
5. **Recommended agenda** (time-boxed bullets)
6. **Follow-ups to capture live**

## Workflow

1. Confirm meeting basics: topic, audience, outcome needed.
2. Gather context from available sources:
   - user's notes and provided links
   - relevant project files in `{project-root}`
   - issue/project trackers when connected
   - recent communication threads when connected
3. Separate facts from assumptions. Mark unknowns explicitly.
4. Draft the brief in the output format above.
5. Add a "questions to ask in the room" section for unresolved items.
6. End with a short checklist the user can reference during the meeting.

## Guardrails

- Do not fabricate participant roles, decisions, or commitments.
- If critical context is missing, state exactly what is missing.
- Keep tone neutral and action-oriented.
- Prefer short bullets over long prose.
