# Story 7.3 `#work-agents` channel operations runbook

Date: 2026-04-22
Story: `7-3-work-agents-teams-channel-and-feedback-loop`
Scope: Task 3 (`AC1`, `AC2`, `AC3`, `AC4`, `AC6`)

## Canonical channel operations guide

Channel: `#work-agents`

- Purpose: one async operating lane for onboarding questions, setup blockers, and skill ideas that become reusable FAQ content or routed PR work.
- Owning team: `Epic 7 AI Cohort Operations`
- Primary owner: `story-7-3-channel-owner`
- Secondary owner: `epic-7-facilitator`
- Escalation fallback: `template-maintainer`
- Moderation expectations:
  - Keep all content work-only and cohort-onboarding scoped.
  - Every thread must route to exactly one path: `channel FAQ/discussion`, `template PR`, or `agent-skills PR`.
  - Promote repeated friction into durable docs/FAQ entries instead of one-off answers.

Canonical channel description text:

`This is a work-only collaboration surface for Epic 7 onboarding operations. Start in [assistants-template](../../README.md), triage blockers to template PR or [agent-skills PR](https://github.com/vixxo-copilot/agent-skills), and keep reusable answers pinned for cohort self-service.`

Repository references:

- [`assistants-template`](../../README.md)
- [`agent-skills`](https://github.com/vixxo-copilot/agent-skills)

Routing quick reference (full matrix: [`Task 2 triage policy`](../../_bmad-output/implementation-artifacts/tests/story-7-3-triage-policy.md)):

| Route | Use when | Default owner | SLA |
| --- | --- | --- | --- |
| `channel FAQ/discussion` | Clarification or discussion with no immediate repo change required. | `story-7-3-channel-owner` | initial response same business day |
| `template PR` | `assistants-template` docs/setup/workflow change is required. | `template-maintainer` | triage in 1 business day, PR draft in 2 |
| `agent-skills PR` | `agent-skills` behavior/contract/example change is required. | `agent-skills-maintainer` | triage in 1 business day, PR draft in 3 |

## Starter pinned post template

Use this as the initial pinned post (edit placeholders only):

```text
Welcome to #work-agents. This channel is the async operating lane for onboarding questions, blockers, and skill ideas.

Start here:
- GETTING_STARTED: ../../GETTING_STARTED.md
- Setup guide: ../../docs/setup.md
- MCP guide: ../../docs/mcps.md
- Story 7.2 kickoff handoff: ../../_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-handoff.md

Route each thread to exactly one destination:
- channel FAQ/discussion
- template PR
- agent-skills PR

Carryover queue from Story 7.2:
- Questions: Q-001..Q-003
- Blockers: B-001..B-003
- Action items: A-001..A-003
```

Pinned post reference links (repository-safe markdown format):

- [`GETTING_STARTED.md`](../../GETTING_STARTED.md)
- [`docs/setup.md`](../../docs/setup.md)
- [`docs/mcps.md`](../../docs/mcps.md)
- [`Story 7.2 kickoff handoff`](../../_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-handoff.md)

Pinned content ownership and cadence:

- `story-7-3-channel-owner` updates pinned entries daily on business days.
- `epic-7-facilitator` reviews pinned content weekly during the sweep closeout.
- Update immediately after any routed item changes owner, due date, or SLA state.

## Intake templates

Use one template per incoming item. Required fields must be complete before escalation.

### Question intake template

- Item ID: `Q-<NNN>`
- Source thread link:
- Summary:
- Route decision: `channel FAQ/discussion` | `template PR` | `agent-skills PR`
- Owner:
- Due date:
- SLA target:
- Acceptance signal:

### Blocker intake template

- Item ID: `B-<NNN>`
- Source thread link:
- Blocker detail:
- Impact: `high` | `medium` | `low`
- Route decision: `channel FAQ/discussion` | `template PR` | `agent-skills PR`
- Owner:
- Due date:
- SLA target:
- Acceptance signal:

### Skill suggestion intake template

- Item ID: `A-<NNN>` (or approved continuation ID)
- Source thread link:
- Skill suggestion:
- Current friction:
- Route decision: `channel FAQ/discussion` | `template PR` | `agent-skills PR`
- Owner:
- Due date:
- SLA target:
- Acceptance signal:

## FAQ promotion rule for repeated questions

Repeated >=3 times in one calendar week means the question must be promoted from thread-only responses to durable FAQ content.

Promotion protocol:

1. Identify duplicate question threads during weekly sweep.
2. Open/update one FAQ entry with canonical answer and relevant links.
3. Add the FAQ link to pinned content and note the change in sweep log.
4. If the answer requires repo changes, route to `template PR` or `agent-skills PR` with owner and due date.

## Work-only and security guardrails (AC6)

- No secrets, tokens, credentials, non-corporate email addresses, or non-work context.
- Keep links repository-safe and reusable (no local absolute paths).
- Outbound posting stays draft/runbook-only unless explicitly directed by the user.
