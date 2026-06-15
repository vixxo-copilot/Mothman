# Story 7.2 Cohort Logistics and Routing Map

Date: 2026-04-21
Story: `7-2-30-minute-kickoff-with-ai-cohort`
Scope: Task 2 only (`AC1`, `AC4`, `AC5`)

This artifact defines the cohort attendance contract, invite payload, and deterministic routing map used to hand off kickoff outcomes into Story 7.3 workflows.

## Participant matrix (roles and attendance expectations)

| Role class | Attendance expectation | Default owner label | Coverage notes |
| --- | --- | --- | --- |
| Required attendee | Must attend kickoff live | `cohort-participant` | Core AI cohort members expected to complete onboarding in week one. |
| Optional attendee | Join if topic is directly relevant | `platform-observer` | Platform or partner observers; can review notes async if unavailable. |
| Facilitator | Must attend and run agenda | `epic-7-facilitator` | Owns pacing, transitions, and closeout actions. |
| Backup facilitator | Standby for facilitator absence | `backup-facilitator` | Steps in when facilitator is blocked; keeps agenda timebox intact. |
| Note-taker | Must attend and capture outcomes | `kickoff-note-taker` | Captures attendance, key Q&A, blockers, and action items with due dates. |

## Kickoff invite payload text

Subject: `Epic 7 AI Cohort Kickoff (30 minutes) - onboarding alignment`

Meeting metadata:

- Duration: 30 minutes
- Audience: AI cohort required attendees + optional platform observers
- Owner: `epic-7-facilitator`

Invite body contract:

Purpose:
- Align the cohort on kickoff objectives, setup expectations, and week-one execution plan.

Expected outcomes:
- Confirm onboarding success path and role coverage.
- Capture open questions and blockers in kickoff notes.
- Route follow-up work to PR or Story 7.3 channel operations.

Prerequisites:
- Review [`GETTING_STARTED.md`](../../../GETTING_STARTED.md).
- Validate setup flow in [`docs/setup.md`](../../../docs/setup.md).
- Review MCP verification guidance in [`docs/mcps.md`](../../../docs/mcps.md).

Artifact links:
- [`GETTING_STARTED.md`](../../../GETTING_STARTED.md)
- [`docs/setup.md`](../../../docs/setup.md)
- [`docs/mcps.md`](../../../docs/mcps.md)

Follow-up expectations:
- Every blocker or question is logged with owner and due date.
- Every logged item is triaged to one route: `'template PR'`, `'agent-skills PR'`, or `'Story 7.3 channel FAQ'`.
- Story 7.3 handoff fields are completed same day as kickoff.

## Post-kickoff routing map (Story 7.3 handoff inputs)

| Route target | Use when | owner-default | Due-date default |
| --- | --- | --- | --- |
| `'template PR'` | Item requires updates to repository templates, onboarding docs, or baseline workflow files. | `template-maintainer` | `+2 business days` |
| `'agent-skills PR'` | Item requires new skill behavior, updated skill docs, or skill invocation contract changes. | `agent-skills-maintainer` | `+3 business days` |
| `'Story 7.3 channel FAQ'` | Item is clarification, repeat question, or async discussion best handled in cohort channel operations. | `story-7-3-channel-owner` | `same business day` |

Story 7.3 handoff packet fields:

- Kickoff date
- Attendee count (`required`, `optional`, absent list)
- Routed item list with selected target path
- Owner assignment and due date per routed item
- Open blockers requiring escalation

## Attendee question and blocker intake contract

Required kickoff notes fields:

- Attendees present
- Key Q&A
- Blockers
- Action item owner
- Action item due date

Question/blocker intake template:

| Intake ID | Source attendee role | Question or blocker | Route decision | Action item owner | Action item due date |
| --- | --- | --- | --- | --- | --- |
| `Q-001` | `required attendee` | `<captured question>` | `'Story 7.3 channel FAQ'` | `story-7-3-channel-owner` | `<YYYY-MM-DD>` |
| `B-001` | `required attendee` | `<captured blocker>` | `'template PR'` | `template-maintainer` | `<YYYY-MM-DD>` |

## AC coverage map (Task 2)

- AC1: Invite payload includes duration, purpose, expected outcomes, prerequisites, and artifact links.
- AC4: Intake contract explicitly captures attendees, key Q&A, blockers, and action items with owner/due date fields.
- AC5: Routing map provides deterministic triage paths (`'template PR'`, `'agent-skills PR'`, `'Story 7.3 channel FAQ'`) and owner defaults for Story 7.3 handoff.
