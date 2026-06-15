# Story 7.3 Triage Policy and Routing Matrix

Date: 2026-04-22
Story: `7-3-personal-agents-teams-channel-and-feedback-loop`
Scope: Task 2 only (`AC3`, `AC6`)

This artifact defines deterministic routing for `#personal-agents` questions, blockers, and skill ideas, then maps Story 7.2 seed items to a single route with owner, due date, and SLA.

## Route decision matrix

| Route destination | Use when | Owner default | SLA expectation | Required handoff metadata |
| --- | --- | --- | --- | --- |
| `channel FAQ/discussion` | Clarification, repeated onboarding question, or discussion item that does not require a repository code change yet. | `story-7-3-channel-owner` | Initial response same business day; FAQ promotion decision within 1 business day. | `item-id`, `source-thread-link`, `summary`, `route-decision`, `owner`, `due-date`, `sla-target`, `acceptance-signal` |
| `template PR` | Change is required in `assistants-template` docs, setup flow, scripts, or onboarding workflow baseline. | `template-maintainer` | Triage within 1 business day; PR draft within 2 business days. | `item-id`, `source-thread-link`, `summary`, `route-decision`, `owner`, `due-date`, `sla-target`, `acceptance-signal` |
| `agent-skills PR` | Change is required in `agent-skills` behavior, skill docs, invocation contracts, or examples. | `agent-skills-maintainer` | Triage within 1 business day; PR draft within 3 business days. | `item-id`, `source-thread-link`, `summary`, `route-decision`, `owner`, `due-date`, `sla-target`, `acceptance-signal` |

Deterministic route policy:

1. If the issue requires a skill implementation or invocation-contract edit, choose `agent-skills PR`.
2. Else if the issue requires template/docs/workflow baseline changes, choose `template PR`.
3. Else choose `channel FAQ/discussion`.
4. Every intake item maps to exactly one route decision.

## Story 7.2 seed-case routing map

Source handoff artifact: [`story-7-2-kickoff-handoff.md`](./story-7-2-kickoff-handoff.md)

| Seed ID | Type | Source summary | Route destination | Owner | Due date | SLA |
| --- | --- | --- | --- | --- | --- | --- |
| `Q-001` | question | First artifact to open before setup. | `channel FAQ/discussion` | `story-7-3-channel-owner` | `2026-04-22` | same business day FAQ response |
| `Q-002` | question | Where repeated clarifications should be handled. | `channel FAQ/discussion` | `story-7-3-channel-owner` | `2026-04-22` | same business day FAQ response |
| `Q-003` | question | Owner path for skill invocation contract updates. | `agent-skills PR` | `agent-skills-maintainer` | `2026-04-23` | triage in 1 business day; PR draft in 3 business days |
| `B-001` | blocker | Invite payload and links are not centralized. | `template PR` | `template-maintainer` | `2026-04-23` | triage in 1 business day; PR draft in 2 business days |
| `B-002` | blocker | Troubleshooting answers are not indexed for async reuse. | `channel FAQ/discussion` | `story-7-3-channel-owner` | `2026-04-22` | initial mitigation same business day; follow-up post in 1 business day |
| `B-003` | blocker | Frequently skipped setup prerequisite needs durable fix. | `template PR` | `template-maintainer` | `2026-04-24` | triage in 1 business day; checklist patch in 2 business days |
| `A-001` | action-item | Publish kickoff FAQ seed entries in channel package. | `channel FAQ/discussion` | `story-7-3-channel-owner` | `2026-04-22` | publish starter FAQ within 1 business day |
| `A-002` | action-item | Prepare template update PR for invite payload and prerequisites. | `template PR` | `template-maintainer` | `2026-04-23` | triage in 1 business day; PR draft in 2 business days |
| `A-003` | action-item | Open skill guidance PR for invocation contract clarification. | `agent-skills PR` | `agent-skills-maintainer` | `2026-04-23` | triage in 1 business day; PR draft in 3 business days |

## Triage tags and minimum intake metadata

Required triage tags:

- `triage/question` for clarifications and FAQ candidates.
- `triage/blocker` for blocking setup/workflow issues.
- `triage/skill-idea` for skill capability and invocation improvements.
- `route/faq` for `channel FAQ/discussion` decisions.
- `route/template-pr` for `template PR` decisions.
- `route/agent-skills-pr` for `agent-skills PR` decisions.

Minimum intake metadata before escalation to a PR route:

1. `item-id` in deterministic format (seed-style `Q-*`, `B-*`, `A-*` or approved continuation ID).
2. `source-thread-link` to the Teams thread/message that captured the request.
3. `summary` of the problem/request in one to three work-only sentences.
4. `route-decision` selected from the route matrix with short rationale.
5. `owner` assigned (default owner unless explicitly overridden with reason).
6. `due-date` in `YYYY-MM-DD`.
7. `sla-target` text aligned with route SLA.
8. `acceptance-signal` describing completion proof (`FAQ update link`, `template PR URL`, or `agent-skills PR URL`).

## Guardrails and work-only scope (AC6)

- No secrets, tokens, credentials, personal email addresses, or non-work personal context are allowed in intake or routing artifacts.
- Outbound posting behavior is restricted to draft/runbook documentation unless explicitly directed by the user.
- All references are repository-safe relative links so future cohorts can reuse the policy without local environment assumptions.

## AC coverage map (Task 2)

- AC3: Decision matrix is deterministic and includes route, owner default, SLA, and handoff metadata.
- AC3: Story 7.2 seed items (`Q-*`, `B-*`, `A-*`) are mapped to route, owner, due date, and SLA.
- AC6: Guardrails explicitly enforce work-only scope and repository-safe links.
