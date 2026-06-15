# Story 2.1 Baseline Audit

## Source rule

- Path: `~/Public/gtd-life/.cursor/rules/agent-identity.mdc`
- Size: 8343 bytes, 162 lines
- Accessible: yes

### Source frontmatter

```yaml
description: Baseline identity and context for every Cursor conversation in gtd-life
globs:
alwaysApply: true
```

### Source section list (ordered, verbatim headings)

1. `# Agent Identity`
2. `## CRITICAL: Outbound Messaging Guardrail`
3. `## Messaging Rules`
   - `### Outlook Reply Formatting (Comment-Based Flow)`
   - `### Teams Chat Formatting`
   - `### Signing Convention`
4. `## Who Derek Is`
5. `## Communication Preferences`
6. `## This Workspace`
   - `### Available Tools`
   - `### Context Switching`
   - `### Email and Calendar Routing (Hard Rule)`
7. `## Key References`

### Source identity-sensitive content inventory

- Named agent: "Chiron" (to be genericized to unnamed assistant).
- Addressee: "Derek" / "Deke" / "Derek Neighbors" (to be replaced by `{{employee_name}}`).
- Biographical block: CTO Vixxo, CEO RevivaGo, Writer at derekneighbors.com, Agile Weekly newsletter, MasteryLab.co, Bodybuilding.com CTO, Gangplank co-founder, ASU instructor.
- Personal context references: RevivaGo (Gmail, Google Calendar), personal/blog (Gmail, Google Calendar), `family.md`, `ventures.md`, `vixxo-cto.md`, `revivago-ceo.md`, `personal.md`.
- Messaging payloads: detailed Outlook Graph API `Comment` reply workflow, Teams HTML `send-chat-message` payload, Chiron sign-off (`-- Chiron (Deke's AI)`).
- Communication preferences: Derek-specific humor, meme lord, no em dashes, no AI slop phrases.

All of the above items are out of scope for Story 2.1 and must be either removed or deferred to Story 2.2 / Story 2.3 sibling artifacts.

## Target path

- Path: `/Users/dneighbors/Public/assistants-template/.cursor/rules/agent-identity.mdc`
- Current state: does **not** exist.
- Directory state: `.cursor/rules/` contains only `.gitkeep` (Story 1.1 sentinel). Confirmed via directory listing on 2026-04-20.

## Banned-term set for Story 2.1 scrub scan

Case-insensitive, whole-file scan of `.cursor/rules/agent-identity.mdc`. Any match is a FAIL.

Identity/biography terms:

- `Derek`
- `Deke`
- `Neighbors`
- `Chiron`
- `RevivaGo`
- `derekneighbors.com`
- `Agile Weekly`
- `MasteryLab`
- `Bodybuilding.com`
- `Gangplank`
- `ASU`
- `gtd-life`
- `arete`
- `eudaimonia`
- `blog`

Email/calendar-stack terms (M365-only in Vixxo template):

- `Gmail`
- `Google Calendar`
- `Google Workspace`
- `personal email`

Deferred-content signal (Story 2.2 owns detailed Outlook workflow; identity rule must not inline it):

- `Outlook` (any occurrence here is a deferral violation, not a PII violation)

## Required present tokens (AC2 and AC4 positive gates)

- `Vixxo employee` (verbatim)
- `work context only` (verbatim)
- `alwaysApply: true` (frontmatter)
- `{{employee_name}}` (placeholder)
- `{{employee_role}}` (placeholder)

## Confirmation of prerequisites

- Story 1.1 scaffold in place (`.cursor/rules/.gitkeep` present).
- Story 1.3 root files present (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) and use matching `{{employee_name}}` / `{{employee_role}}` placeholders.
- No pre-existing `.cursor/rules/*.mdc` files to conflict with.

Baseline complete. Proceeds to Task 2 blueprint lock.
