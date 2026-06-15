# Story 7.2 Task 1 - Kickoff Runbook and Agenda Contract

## Objective

Run one 30-minute kickoff for the Vixxo AI cohort that aligns participants on meeting purpose, expected outcomes, first-week execution, and immediate support paths.

## Audience

- Required: cohort participants, facilitator, note-taker.
- Optional: platform maintainer observer, backup facilitator.
- Out of scope: non-cohort stakeholders without onboarding responsibilities.

## Meeting Success Criteria

- A single calendar invite is prepared with complete meeting metadata for a 30-minute kickoff slot.
- Invite text includes purpose, expected outcomes, prerequisites, and canonical onboarding links.
- Session agenda explicitly covers demo, live setup, and Q&A with strict timeboxes.
- All artifacts and language remain work-only and follow repository privacy/security guardrails.

## Kickoff Invite Contract (Metadata + Payload)

Use this contract before sending the invite:

- Meeting title: `Epic 7 Story 7.2 - Vixxo AI Cohort Kickoff`.
- Duration: `30 minutes`.
- Facilitator owner: cohort facilitator (work account only).
- Attendees: all required cohort participants plus facilitator and note-taker.
- Location: Teams meeting link (or approved internal meeting room URL).
- Invite purpose: align first-week onboarding execution from day one.
- Expected outcomes:
  - Participants can execute the onboarding fast path in `GETTING_STARTED.md`.
  - Participants understand active MCP verification expectations.
  - Participants know where to route blockers after kickoff.
- Prerequisites:
  - Read `GETTING_STARTED.md`.
  - Review `docs/setup.md`.
  - Review `docs/mcps.md`.
  - Prepare workstation with required tools and credentials configured in `.env`.
- Artifact links in invite body:
  - `GETTING_STARTED.md`
  - `docs/setup.md`
  - `docs/mcps.md`

## 30-minute Timeboxed Agenda

| Segment | Timebox | Owner | Output |
| --- | --- | --- | --- |
| Opening + outcomes alignment | 0:00-0:03 (3 min) | Facilitator | Confirm purpose, scope, and success criteria. |
| Demo segment | 0:03-0:11 (8 min) | Facilitator | Walk through onboarding flow and expected first-week artifact outcomes. |
| Live setup segment | 0:11-0:24 (13 min) | Facilitator + cohort | Validate setup path and MCP verification checkpoints in real time. |
| Q&A segment | 0:24-0:29 (5 min) | Note-taker + facilitator | Capture open questions, blockers, and owners for follow-up routing. |
| Close + next actions | 0:29-0:30 (1 min) | Facilitator | Confirm post-kickoff follow-up path and immediate ownership. |

Agenda contract checks:

- Demo segment is present and timeboxed.
- Live setup segment is present and timeboxed.
- Q&A segment is present and timeboxed.
- Total scheduled duration is exactly 30 minutes.

## Pre-flight Checks

Complete before kickoff start:

1. Confirm invite includes links to `GETTING_STARTED.md`, `docs/setup.md`, and `docs/mcps.md`.
2. Confirm facilitator can share screen and access onboarding docs.
3. Confirm note-taker is assigned and can capture blockers/action items.
4. Confirm participants were asked to run prerequisite tool checks from `GETTING_STARTED.md`.
5. Confirm no local absolute paths, secrets, or personal identifiers are present in invite/runbook notes.

## Guardrails (AC6)

- Work-only context: keep content scoped to Vixxo work onboarding.
- No secrets in docs or invite text; credentials remain only in local `.env`.
- No personal email addresses or non-work personal context in kickoff artifacts.
- Keep all artifact references as repository-relative paths.
