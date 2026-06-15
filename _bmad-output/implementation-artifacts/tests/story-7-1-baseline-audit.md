# Story 7.1 Baseline Audit

Date: 2026-04-21
Story: `7-1-write-vixxo-internal-getting-started`
Scope: Task 1 source extraction for onboarding baseline, setup-flow drift, and source-of-truth mapping.

## Onboarding source inventory

| Source | Exists | Primary onboarding role | Notes for Story 7.1 |
| --- | --- | --- | --- |
| `README.md` | yes | quick bootstrap entry point | Has clone + skills install + pointer to `docs/setup.md`; does not cover `./bin/init` flow details. |
| `docs/setup.md` | yes | canonical deep setup guide | Contains prerequisite checks, credential flow, active MCP overview, and troubleshooting. |
| `docs/mcps.md` | yes | full MCP catalog | Canonical active + placeholder matrix; includes auth/transport/env footprint. |
| `.cursor/mcp.README.md` | yes | active MCP wiring details | Detailed per-server auth model for `linear`, `github`, `microsoft-365`, `salesforce`, `gong`. |
| `bin/init` | yes | real executable setup wizard | Current behavioral source for prompt outputs, `.env` materialization, skills install, active MCP checks. |
| `memory/meetings/_template/prep.md` | yes | prep artifact template | Confirms prep output shape expected after meeting-prep workflow. |
| `memory/meetings/_template/meeting.md` | yes | meeting artifact template | Confirms meeting output shape and linked artifact structure (`prep.md`, `agenda.md`, `transcript.md`). |

## Command inventory and verification surface

Observed commands and checks relevant to Story 7.1 AC1/2/3/4/5/8:

- Prereq verification commands in docs:
  - `git --version`
  - `node --version`
  - `npx --version`
  - `docker --version` (implicitly required by setup guidance and by `bin/init` GitHub MCP probe)
  - `sf --version` (via Salesforce prerequisite and `bin/init` probe)
- Bootstrap/setup commands:
  - `git clone YOUR-REPO-URL assistants-template`
  - `cd assistants-template`
  - `npx skills add vixxo-copilot/agent-skills`
  - `cp .env.example .env`
  - `./bin/init`
- Auth and remediation commands:
  - `sf org login web`
  - `cursor .` (launch guidance to preserve environment inheritance)

`bin/init` also executes runtime checks for `npm install`, `npx --version`, `docker --version`, and `sf --version` during post-wizard verification logic.

## bin/init observed behavior snapshot

Current `bin/init` flow (actual implementation behavior):

1. Ensures local dependencies (`npm install`) when missing.
2. Prompts for identity fields and optional MCP interests.
3. Writes:
   - `memory/me/identity.md`
   - `agents/personas/work.md`
   - `.env` from `.env.example` (create or optional overwrite)
4. Runs skills install:
   - `npx skills add vixxo-copilot/agent-skills`
5. Verifies active MCPs from `.cursor/mcp.json` in key order:
   - `linear`
   - `github`
   - `microsoft-365`
   - `salesforce`
   - `gong`
6. Emits deterministic PASS/FAIL summary with remediation guidance.

## Setup-flow drift log (docs vs `bin/init`)

### Drift A — `docs/setup.md` says `./bin/init` does not exist

- Doc statement: setup smoke-test section still says the file "does not yet exist" and frames it as forward reference.
- Actual behavior: `bin/init` is present and production-usable.
- Impact: High onboarding confusion risk; users can skip the canonical wizard path.

### Drift B — README quickstart omits direct `./bin/init` step

- `README.md` quickstart currently routes users to skills install then `docs/setup.md`, without explicit wizard-first path.
- Actual behavior: `bin/init` now orchestrates identity/persona generation, `.env`, skills install, and active MCP summary.
- Impact: Medium; users may execute setup in fragmented/manual order.

### Drift C — manual MCP round-trip guidance vs current wizard checks

- `docs/setup.md` expects manual MCP UI and query checks per server.
- `bin/init` performs deterministic local readiness checks and configuration/auth precondition checks, not full business-query round trips.
- Impact: Medium; docs and wizard both useful but describe different verification depth without clear layering.

### Drift D — prerequisites in docs are richer than README quick path

- `docs/setup.md` covers `git`, Node LTS, `npx`, Docker, and `sf`.
- `README.md` prerequisite list currently includes only `git`, `node`, and `npx`.
- Impact: Medium for first-time users; hidden Docker/`sf` requirements become late failures.

## Source-of-truth mapping

| Topic | Primary source of truth | Secondary source(s) | Story 7.1 use in `GETTING_STARTED.md` |
| --- | --- | --- | --- |
| Internal onboarding framing + quick path | new root `GETTING_STARTED.md` (Story 7.1 output) | `README.md`, `docs/setup.md` | Use as fast lane and link outward for depth. |
| Prerequisite commands and environment checks | `docs/setup.md` + `bin/init` probe logic | `README.md` | Consolidate required checks (`git`, `node`, `npm`, `npx`, Docker, `sf`) in one quick-start sequence. |
| Clone/bootstrap and setup command order | `bin/init` + `README.md` | `docs/setup.md` | Align on clone -> `cd` -> `./bin/init`, then clarify expected outputs. |
| Active MCP set and verification scope | `.cursor/mcp.json` (active keys) + `bin/init` checks | `.cursor/mcp.README.md`, `docs/mcps.md`, `docs/setup.md` | Keep five-server checklist and point to remediation docs. |
| Meeting-prep expected outputs | `memory/meetings/_template/prep.md` + `memory/meetings/_template/meeting.md` | Story 7.1 doc requirements | Validate that prep + meeting artifacts land under `memory/meetings/`. |
| Skills registry command | `bin/init` + `README.md` + `docs/setup.md` | `docs/mcps.md` mentions registry handle | Keep `npx skills add vixxo-copilot/agent-skills` explicit in quick path. |

## Meeting template output expectations

- Prep template path: `memory/meetings/_template/prep.md`
- Meeting template path: `memory/meetings/_template/meeting.md`
- Expected first-run artifact family (Story 7.1 AC5 guidance target):
  - prep-oriented artifact content aligned to prep template sections
  - meeting artifact with links to prep/agenda/transcript references
- Story 7.1 should instruct users to verify generated prep + meeting artifacts under `memory/meetings/` after running meeting-prep.

## AC coverage map (Task 1)

- AC1: inventory confirms canonical doc touchpoints and root quick-path prerequisite context.
- AC2: command inventory captures prerequisite verification surface and Node LTS context references.
- AC3: extracted real `bin/init` behavior and expected generated outputs.
- AC4: extracted active MCP key set and validation flow from `.cursor/mcp.json` + `bin/init`.
- AC5: extracted meeting template outputs and skills invocation expectations.
- AC8: captured canonical link/source mapping and no local absolute-path references.

## Gap analysis summary

- Primary gap: onboarding docs are not yet synchronized to current `bin/init` reality.
- Primary remediation target for Task 3: author a concise internal fast lane that preserves canonical link-outs and avoids duplication.
- Constraint carried forward: keep references work-only and avoid adding local absolute paths or secrets.

## Source references

- `README.md`
- `docs/setup.md`
- `docs/mcps.md`
- `.cursor/mcp.README.md`
- `.cursor/mcp.json`
- `bin/init`
- `memory/meetings/_template/prep.md`
- `memory/meetings/_template/meeting.md`
