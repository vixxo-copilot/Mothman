---
type: preferences
scope: work
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [preferences, work]
---

# Preferences

## Communication Style

Direct, concise, evidence-backed. Match Vixxo cultural norms. See
`AGENTS.md` and `.cursor/rules/agent-identity.mdc` for the authoritative
tone and style guidance; this section defers to those files.

## Tooling

### MCP servers

Active Vixxo work MCPs for this template:

- Linear
- GitHub
- Microsoft 365
- Salesforce
- Gong

MCP configuration lives in `.cursor/mcp.json`. MCP credential wiring lives in
`.env.example`.

### PolyAI (skill — not MCP)

- **polyai** — Conversations API, health check, outbound call audit, Jupiter
  config, metrics (`VALID_SR`, `API_OK`)
- **polyai-vixxo-bridge** — VixxoLink MCP wiring in Agent Studio only

Credentials: `POLYAI_API_KEY`, `POLYAI_REGION`, `POLYAI_ACCOUNT_ID`,
`POLYAI_PROJECT_ID` in `.env`. Skill path: `.agents/skills/polyai/`.

## Meeting Cadence

Captured in `memory/meetings/` using the Story 3.1 meeting templates.
Morning briefing and end-of-day wrap cadence is Vixxo-team-dependent;
the assistants template does not prescribe a specific schedule.

## Working Hours

Work-only; Vixxo business hours. Deferred requests outside scope per
`.cursor/rules/agent-identity.mdc`.

## AI Assistant

See `agents/personas/work.md` for the assistant persona and
`.cursor/rules/agent-identity.mdc` for operator identity. This file does
not restate persona or signing conventions; the rule files are the
single source of truth.

<!-- Why: preferences skeleton; work-only, defers to upstream rule files for tone and assistant persona. -->
