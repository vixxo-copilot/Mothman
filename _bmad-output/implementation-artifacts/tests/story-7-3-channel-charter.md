# Story 7.3 Task 1 - Channel Charter and Bootstrap Contract

## Canonical Channel Metadata

- Channel name: `#personal-agents`
- Owning team: `Epic 7 AI Cohort Operations`
- Channel purpose: provide one asynchronous operating lane for onboarding questions, setup blockers, and skill-improvement ideas that can be triaged into durable repo changes.
- Default owners:
  - Primary: `story-7-3-channel-owner`
  - Secondary: `epic-7-facilitator`
  - Escalation fallback: `template-maintainer`
- Moderation expectations:
  - Keep all posts work-only and onboarding-scope.
  - Tag each new thread with one route intent (`FAQ/discussion`, `template PR`, `agent-skills PR`).
  - Convert repeated confusion threads into FAQ updates instead of re-answering ad hoc.
  - Escalate unresolved blockers past SLA to the owning maintainer and facilitator.

## Channel Description Contract

Use this exact channel description text when bootstrapping `#personal-agents`:

`This is a work-only collaboration surface for Epic 7 onboarding operations. Start in [assistants-template](../../../README.md), triage blockers to template PR or [agent-skills PR](https://github.com/vixxo-copilot/agent-skills), and keep reusable answers pinned for cohort self-service.`

Channel description references:

- [`assistants-template`](../../../README.md)
- [`agent-skills`](https://github.com/vixxo-copilot/agent-skills)

## Pinned Content Contract

Required pinned links for onboarding and setup canon:

- [`GETTING_STARTED.md`](../../../GETTING_STARTED.md)
- [`docs/setup.md`](../../../docs/setup.md)
- [`docs/mcps.md`](../../../docs/mcps.md)
- [`Story 7.2 kickoff handoff`](story-7-2-kickoff-handoff.md)

Story 7.2 kickoff carryover context to pin:

- Carry over routed seed items (`Q-001..Q-003`, `B-001..B-003`, `A-001..A-003`) as initial triage queue references.
- Keep escalation starter triggers (`E-001..E-003`) visible until Task 2 matrix and Task 4 sweep log are active.

Starter FAQ seed (from Story 7.2):

1. What should I open first for onboarding?
   - Start with `GETTING_STARTED.md`, then follow `docs/setup.md`, then `docs/mcps.md`.
2. Where do unresolved setup questions go?
   - Post in `#personal-agents` with routing intent and owner field.
3. When does a thread become a PR?
   - Route template/docs fixes to `template PR`; route skill contract/behavior changes to `agent-skills PR`.

Who updates pinned content:

- `story-7-3-channel-owner` maintains pinned links, FAQ entries, and carryover references.
- `epic-7-facilitator` reviews for consistency each weekly sweep.

Update cadence:

- Day 0 bootstrap: publish initial pinned package and FAQ seed.
- Daily business-day check: update ownership/due-date pointers for active blockers.
- Weekly sweep closeout: promote repeated questions and refresh pinned FAQ entries.

## Guardrails (AC6)

- No secrets, tokens, or personal email addresses.
- No local absolute paths (`/Users/`, `/home/`, `file://`) in published channel artifacts.
- Keep all references reusable for future cohorts and aligned to `.cursorrules`, `AGENTS.md`, and `CLAUDE.md`.
