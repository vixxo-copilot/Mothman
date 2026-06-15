# Story 7.1 Canonical Blueprint

Captured: 2026-04-21. Scope: Task 2 only (`GETTING_STARTED.md` blueprint contract for AC1, AC2, AC3, AC4, AC5, AC7, AC8).

This blueprint locks one canonical shape for the future root `GETTING_STARTED.md`, scoped to Vixxo internal cohort onboarding. It defines section order, command snippets, expected outcomes, and canonical links so Story 7.1 Task 3 can author content without drift.

## Section order lock — `GETTING_STARTED.md`

The authored root document must use this H2 sequence exactly, top to bottom, once each:

1. `## 15-minute quick path`
2. `## Prerequisites and environment checks`
3. `## Clone, bootstrap, and first-run setup`
4. `## Verify active MCPs (five-server checklist)`
5. `## Run first meeting prep`
6. `## Troubleshooting and escalation`

Order rationale:

- The quick path provides a <15-minute linear flow for first success.
- Prerequisites and setup isolate checks from remediation.
- MCP verification happens after `./bin/init` so outcomes align with wizard summary.
- Meeting-prep is last so participants can prove real workflow value.
- Troubleshooting/escalation closes the loop and points to support paths.

## Command snippets and expected outcomes lock

### Step 1: Prerequisites checks

```bash
git --version
node --version
npm --version
npx --version
docker --version
sf --version
```

Expected guidance in `GETTING_STARTED.md`:

- Node guidance calls out modern Active LTS lines (Node 24 or Node 22) and avoids EOL lines.
- Failures route users to deeper setup instructions in `docs/setup.md`.

### Step 2: Clone and bootstrap

```bash
git clone YOUR-REPO-URL assistants-template
cd assistants-template
./bin/init
```

Expected outcomes to lock:

- `memory/me/identity.md created or updated`
- `agents/personas/work.md created or updated`
- `.env created from .env.example (or left untouched if already present)`
- `Post-wizard summary includes PASS/FAIL status per active MCP`

### Step 3: Skills bundle reference

```bash
npx skills add vixxo-copilot/agent-skills
```

Expected guidance:

- Keep this command in the setup sequence so participants can confirm the shared skills bundle is available.
- Note that modern `bin/init` already performs the install; command remains documented as the explicit fallback verification command.

## MCP verification contract (five active servers)

`GETTING_STARTED.md` must include an explicit checklist for these keys from `.cursor/mcp.json`:

- `linear`
- `github`
- `microsoft-365`
- `salesforce`
- `gong`

Pass/fail interpretation to lock:

- PASS means the server initializes and responds to a simple probe.
- FAIL means setup is incomplete or auth/session state is invalid; route remediation to `docs/setup.md`, `docs/mcps.md`, and `.cursor/mcp.README.md`.
- The checklist must mention reading the post-wizard summary and interpreting per-server PASS/FAIL before proceeding to meeting-prep.

## Meeting-prep invocation and artifact contract

Invocation lock for first meeting flow:

- In Cursor agent chat, invoke the installed skill by name: `meeting-prep`.
- If slash-command UX is enabled, `/meeting-prep` is equivalent.

First realistic scenario (must be documented in `GETTING_STARTED.md`):

- Example: "Prepare for first weekly Vixxo cohort kickoff with platform maintainers."

Output verification lock:

- `meeting-prep output folder exists under memory/meetings/`
- `prep.md and meeting.md exist for the target meeting`

Recommended artifact checks in doc content:

- Confirm the generated prep file captures objectives and attendee context.
- Confirm the meeting file links prep/agenda/transcript structure for follow-on execution.

## Link contract (canonical and non-redundant)

Required links that must appear exactly once in the main flow:

- [`README.md`](README.md)
- [`docs/setup.md`](docs/setup.md)
- [`docs/mcps.md`](docs/mcps.md)
- [`.cursor/mcp.README.md`](.cursor/mcp.README.md)
- [`bin/init`](bin/init)

Canonical source mapping (avoid duplicate explanations):

- Repo overview and orientation: [`README.md`](README.md)
- Detailed workstation/bootstrap troubleshooting: [`docs/setup.md`](docs/setup.md)
- MCP catalog and credential surface: [`docs/mcps.md`](docs/mcps.md)
- Active MCP transport/auth specifics: [`.cursor/mcp.README.md`](.cursor/mcp.README.md)
- Wizard behavior source: [`bin/init`](bin/init)

Guardrail lock for links:

- Use repo-relative links only.
- Do not use local absolute paths.
- Do not duplicate topic ownership across multiple sections when one canonical source exists.

## Content contract summary (AC mapping for Task 2)

- AC1: Locks root-doc purpose and section shape for a 15-minute internal cohort fast path.
- AC2: Locks prerequisite checks (`git`, `node`, `npm`, `npx`, Docker, `sf`) and Node Active LTS guidance.
- AC3: Locks clone + bootstrap flow (`git clone`, `cd`, `./bin/init`) with explicit expected wizard outcomes plus skills command reference.
- AC4: Locks five-server MCP checklist and pass/fail interpretation with remediation references.
- AC5: Locks meeting-prep invocation and output verification under `memory/meetings/` including a realistic first-meeting scenario.
- AC7: Reserves troubleshooting/escalation section and requires explicit support-path references.
- AC8: Locks required cross-links and canonical-source discipline with repo-relative path requirements.
