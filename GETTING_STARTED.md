# GETTING_STARTED (Vixxo Internal Cohort)

This guide is scoped to Vixxo internal cohort onboarding for `assistants-template`. Use it for first-day setup and first meeting-prep success without 1:1 maintainer help.

Primary orientation source: [`README.md`](README.md)

## 15-minute quick path

Follow these steps top-to-bottom:

1. Run prerequisite checks (below) and confirm you are on a modern Node LTS line.
2. Clone the repo and run the setup wizard.
3. Confirm active MCP PASS/FAIL results.
4. Run your first `meeting-prep` flow and verify artifacts under `memory/meetings/`.
5. If blocked, use the troubleshooting/escalation path in this file.

Target time: under 15 minutes for a clean workstation.

## Prerequisites and environment checks

Run:

```bash
git --version
node --version
npm --version
npx --version
docker --version
sf --version
```

Node guidance: prefer Node 24 LTS or Node 22 LTS (modern Active LTS lines). Avoid EOL branches for setup and MCP tooling stability.

For full environment setup depth and remediation details, use the canonical guide at [`docs/setup.md`](docs/setup.md).

## Clone, bootstrap, and first-run setup

Run:

```bash
git clone YOUR-REPO-URL assistants-template
cd assistants-template
./bin/init
```

Canonical wizard behavior source: [`bin/init`](bin/init)

Expected wizard prompts and outcomes:

- Prompts for your identity profile (name, email, role) and optional MCP interests.
- `memory/me/identity.md` created or updated.
- `agents/personas/work.md` created or updated.
- `.env` created from `.env.example` when missing (or left in place / optionally overwritten if already present).
- Shared skills bundle install step via `npx skills add vixxo-copilot/agent-skills`.
- Post-wizard summary with per-server PASS/FAIL for active MCPs.

If you need to rerun the skills step manually, run:

```bash
npx skills add vixxo-copilot/agent-skills
```

## Verify active MCPs (five-server checklist)

Read the post-wizard summary after `./bin/init` and confirm all five active keys are present:

- `linear`
- `github`
- `microsoft-365`
- `salesforce`
- `gong`

Interpretation:

- PASS means the server initialized correctly for local setup readiness.
- FAIL means setup or auth is incomplete for that server and must be fixed before relying on MCP workflows.

Use these canonical remediation references:

- MCP catalog and credential surface: [`docs/mcps.md`](docs/mcps.md)
- Active-server wiring/auth behavior: [`.cursor/mcp.README.md`](.cursor/mcp.README.md)

## Run first meeting prep

In Cursor agent chat, invoke `meeting-prep`. If slash-command UX is enabled in your environment, `/meeting-prep` is equivalent.

Realistic first scenario:

- Prepare for first weekly Vixxo cohort kickoff with platform maintainers.

Verify output artifacts under `memory/meetings/`:

- A meeting folder for the target session exists.
- `prep.md` exists and includes objectives, questions, attendee context, and prior-meeting context.
- `meeting.md` exists and links prep/agenda/transcript structure for execution follow-through.

## Troubleshooting and escalation

Guardrails:

- Keep secrets out of git: keep credentials in `.env only`; never commit real secrets.
- Keep all prompts, notes, and outputs work-only.
- Avoid non-work data leakage; include only business-needed data in work artifacts.

Escalation path now:

- Open an internal tracker ticket with error details and reproduction steps.
- Post the ticket link in the Vixxo AI support channel for platform triage.

Forward references for cohort workflows:

- Story 7.2 will formalize kickoff artifact packaging and handoff conventions.
- Story 7.3 will formalize cohort communication channel workflows and feedback loops.
