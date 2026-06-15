---

## stepsCompleted: [1, 2, 3]
inputDocuments:
  - gtd-life (reference only, private)
status: in-progress
generatedAt: '2026-04-20'

# Vixxo Assistants Template - Epic Breakdown

## Overview

This document defines the epics and stories for building `~/Public/assistants-template`, the Vixxo-deployable personal AI agent template every employee can clone. The template is thin and scrubbed of personal data; all skills live in `~/Public/agent-skills` and install via `npx skills add vixxo-copilot/agent-skills`.

Companion planning lives in `~/Public/agent-skills/_bmad-output/planning-artifacts/epics.md` and covers the registry, static browser, and introspection MCP.

## Requirements Inventory

### Functional Requirements

- FR1: Template Skeleton Bootstrap (directories, LICENSE, README, AGENTS.md, CLAUDE.md, .cursorrules, .gitignore)
- FR2: Generic Agent Identity Rules (work-only, no personal blending, placeholders for employee name)
- FR3: Single Work Persona (collapsed Vixxo-CTO/RevivaGo/Personal into generic Vixxo work persona)
- FR4: Memory Vault Empty Scaffold (all `_template.md` / `_template/` trees, no Derek content, portable `.obsidian/`)
- FR5: Project-Local MCP Config with full Vixxo lineup (active set + placeholders)
- FR6: `.env.example` with per-MCP credential guidance
- FR7: Interactive Setup Wizard (`bin/init`) that collects employee context, generates identity/persona files, and triggers skill install
- FR8: Self-Serve Employee Onboarding Docs (rewritten `docs/setup.md` and `docs/mcps.md`)
- FR9: Skills Install via `npx skills add vixxo-copilot/agent-skills` (no custom loader)
- FR10: PII CI Guardrail blocking PRs that introduce personal content
- FR11: Pilot Rollout to Vixxo AI Cohort with feedback loop

### Non-Functional Requirements

- NFR1: No Derek PII in any shipped content (names, addresses, family, home, RevivaGo, blog)
- NFR2: Works on macOS and Linux (depends only on `git`, `node`, `npx`)
- NFR3: Setup Wizard completes in under 15 minutes on a fresh machine
- NFR4: Secrets never enter the repo (.env in .gitignore, placeholders in .env.example)
- NFR5: Template stays thin (no skill code bundled; all skills come from agent-skills at install time)
- NFR6: MCP config shape remains consistent whether an MCP is active or placeholder (drop-in when wired)
- NFR7: Identity and persona files must explicitly declare "work only" scope

### Additional Requirements

- Template assumes latest BMAD already installed (v6.3.0+)
- Template must work in both Cursor and Claude Code (skills mirrored in .cursor/ and .claude/)
- All planning artifacts live in `_bmad-output/` (BMAD convention)
- New skills sync down from agent-skills; employees do not edit skills in-template

## FR Coverage Map

- FR1: Epic 1 (Stories 1.1, 1.2, 1.3)
- FR2: Epic 2 (Stories 2.1, 2.2, 2.4)
- FR3: Epic 2 (Story 2.3)
- FR4: Epic 3 (Stories 3.1, 3.2, 3.3)
- FR5: Epic 4 (Stories 4.1, 4.2, 4.3)
- FR6: Epic 4 (Story 4.3)
- FR7: Epic 5 (Stories 5.1, 5.2, 5.3)
- FR8: Epic 4 (Story 4.4)
- FR9: Epic 5 (Story 5.3)
- FR10: Epic 6 (Stories 6.1, 6.2)
- FR11: Epic 7 (Stories 7.1, 7.2, 7.3)

## Epic List

### Epic 0: Microsoft 365 MCP maintenance follow-ups (E0)

Capture post-launch maintenance fixes for Microsoft 365 MCP behavior so org-scoped tools remain available in the template without reopening completed delivery epics.

**FRs covered:** Post-release MCP reliability and operations guidance

### Epic 1: Bootstrap assistants-template skeleton (E1)

Create the empty structural bones of the template so subsequent epics have a consistent home. No code, no skills, no content — just the repo shape that employees will clone.

**FRs covered:** FR1

### Epic 2: Port and generalize agent identity + rules, work-only (E2)

Port rules and persona files from gtd-life, strip all personal and RevivaGo context, collapse into a single generic Vixxo work persona parameterized by employee name and role.

**FRs covered:** FR2, FR3

### Epic 3: Memory vault empty scaffold (E3)

Reproduce the gtd-life memory vault structure with templates only; zero Derek content. Portable `.obsidian/` config so Obsidian opens cleanly on any machine.

**FRs covered:** FR4

### Epic 4: MCP packaging (project-local) (E4)

Ship a `.cursor/mcp.json` containing the full Vixxo MCP lineup. Active entries wired; placeholder entries commented out with TODOs. `.env.example` enumerates all credential needs. Self-serve setup docs rewritten for new employees.

**FRs covered:** FR5, FR6, FR8

### Epic 5: Interactive setup wizard `bin/init` (E5)

Node-based interactive wizard that collects employee name/email/role, generates `memory/me/identity.md` and `agents/personas/work.md`, copies `.env.example` to `.env`, and runs `npx skills add vixxo-copilot/agent-skills` to pull the current Vixxo skill bundle.

**FRs covered:** FR7, FR9

### Epic 6: PII scrub + CI guardrail (template half of E9)

Add a GitHub Action that blocks PRs introducing banned personal patterns (names, home addresses, family, health, RevivaGo, blog content). Shared deny-list pattern mirrored in agent-skills.

**FRs covered:** FR10

### Epic 7: Pilot rollout to Vixxo AI cohort (E10)

Write Vixxo-internal `GETTING_STARTED.md`, run a 30-minute kickoff with AI cohort participants, stand up a `#personal-agents` Teams channel, and capture feedback that drives PRs back into agent-skills.

**FRs covered:** FR11

---

## Priority Order (Work-First)

Stories execute in tier order. Sprint 0 covers urgent maintenance fixes discovered after the main template rollout; Tier 1 gets the template clonable and bootable with active MCPs; Tier 2 layers the wizard + memory vault; Tier 3 ships the PII guardrail and pilot.

### Sprint 0 - Maintenance Follow-ups

| Order | Story | Description |
| ----- | ----- | ----------- |
| 0     | 0.1   | Enable `--org-mode` for `microsoft-365` MCP and add scope-consent/re-login/admin-approval documentation |

### Tier 1 - Clonable, Bootable Template


| Order | Story | Description                                                                                                                                                          |
| ----- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | 1.1   | Scaffold directory structure and root files                                                                                                                          |
| 2     | 1.2   | Write generic `README.md`, `LICENSE`, `.gitignore`                                                                                                                   |
| 3     | 1.3   | Write generic `AGENTS.md`, `CLAUDE.md`, `.cursorrules`                                                                                                               |
| 4     | 2.1   | Port agent-identity rule (generic, placeholders for employee name)                                                                                                   |
| 5     | 2.2   | Port outbound messaging guardrail, memory-vault protection, teams-dm-formatting, email-triage-thread-defaults rules                                                  |
| 6     | 2.3   | Create single generic `agents/personas/work.md`                                                                                                                      |
| 7     | 2.4   | Confirm `benji-inbox-default.mdc` is NOT ported                                                                                                                      |
| 8     | 4.1   | Write `.cursor/mcp.json` with Active MCPs (Linear, GitHub, Microsoft 365, Salesforce, Gong)                                                                          |
| 9     | 4.2   | Add commented-out placeholders (Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection MCP) |
| 10    | 4.3   | Write `.env.example` with per-MCP sections and wiki/issue links                                                                                                      |


### Tier 2 - Memory Vault + Setup Wizard


| Order | Story | Description                                                                                    |
| ----- | ----- | ---------------------------------------------------------------------------------------------- |
| 11    | 3.1   | Port all `_template.md` and `_template/` trees from gtd-life/memory                            |
| 12    | 3.2   | Create portable `.obsidian/` config (no Derek vault history)                                   |
| 13    | 3.3   | Seed empty `memory/me/identity.md` and `memory/me/preferences.md` with work-only frontmatter   |
| 14    | 4.4   | Rewrite `docs/setup.md` and `docs/mcps.md` as self-serve employee onboarding                   |
| 15    | 5.1   | Scaffold `bin/init` Node entry point and dependency setup                                      |
| 16    | 5.2   | Wizard prompts: name, email, Vixxo role/title, optional MCPs; write identity and persona files |
| 17    | 5.3   | Wizard runs `npx skills add vixxo-copilot/agent-skills` and verifies active MCPs               |


### Tier 3 - PII Guardrail + Pilot


| Order | Story | Description                                                 |
| ----- | ----- | ----------------------------------------------------------- |
| 18    | 6.1   | Write shared PII deny-list config                           |
| 19    | 6.2   | Add GitHub Action that blocks PRs violating the deny-list   |
| 20    | 7.1   | Write Vixxo-internal `GETTING_STARTED.md` for the AI cohort |
| 21    | 7.2   | Run 30-minute kickoff session with the AI cohort            |
| 22    | 7.3   | Stand up `#personal-agents` Teams channel and feedback loop |


---

## Epic 0: Microsoft 365 MCP maintenance follow-ups

Address post-launch Microsoft 365 MCP configuration and onboarding gaps that prevent org-scoped tools from appearing consistently.

### Story 0.1: Enable `--org-mode` and document M365 consent flow

As a Vixxo employee using the assistants template,
I want the Microsoft 365 MCP to run in org mode with clear onboarding instructions,
So that Teams/SharePoint/shared-mailbox tools appear reliably after auth and consent.

**Acceptance Criteria:**

- `.cursor/mcp.json` entry `microsoft-365` adds `"--org-mode"` to the args array after `@softeria/ms-365-mcp-server@latest`
- `docs/setup.md`, `docs/mcps.md`, and `.cursor/mcp.README.md` explicitly document that enabling org mode can require MCP restart and re-login
- Story guidance includes Graph scope consent expectations for `Chat.ReadWrite`, `ChannelMessage.*`, `Sites.Read.All`, and `User.Read.All`
- Documentation clearly states some scopes may require tenant admin approval and includes next-step guidance when consent is blocked

## Epic 1: Bootstrap assistants-template skeleton

Create the empty structural bones of the template repo.

### Story 1.1: Scaffold directory structure and root files

As a new Vixxo employee,
I want the template repo to have a clear, consistent directory layout when I clone it,
So that I can orient quickly without reading docs.

**Acceptance Criteria:**

- Directories present: `.cursor/rules/`, `agents/personas/`, `bin/`, `docs/`, `memory/`, `scripts/`
- `.gitignore` excludes `node_modules/`, `.env`, `.env.`*, `*.log`, `tmp/`
- Empty `.gitkeep` where needed so git tracks empty dirs

### Story 1.2: Write generic `README.md`, `LICENSE`, `.gitignore`

As a new employee,
I want a README that explains what this is, how to bootstrap it, and where to get help,
So that I can get running in under 15 minutes.

**Acceptance Criteria:**

- `README.md` covers: purpose, quickstart, link to `docs/setup.md`, link to skills registry
- `LICENSE` is the Vixxo internal license file
- No references to Derek, RevivaGo, blog, or gtd-life in any root file

### Story 1.3: Write generic `AGENTS.md`, `CLAUDE.md`, `.cursorrules`

As the AI agent in a cloned template,
I want top-level context files that identify me as a Vixxo employee assistant,
So that I respond with the right tone and guardrails out of the box.

**Acceptance Criteria:**

- `CLAUDE.md` and `AGENTS.md` mirror each other (standard practice)
- `.cursorrules` summarises critical guardrails (outbound messaging, memory protection)
- All three use `{{employee_name}}` and `{{employee_role}}` placeholders
- Work-only language throughout; no "personal" or "RevivaGo" mentions

## Epic 2: Port and generalize agent identity + rules, work-only

Port Cursor rules from gtd-life with every personal bias stripped.

### Story 2.1: Port agent-identity rule (generic)

As the AI in a fresh template,
I want a rule that names me and explains my relationship to the employee,
So that I call them by name and respect Vixxo cultural norms.

**Acceptance Criteria:**

- `.cursor/rules/agent-identity.mdc` uses `{{employee_name}}` placeholder
- Rule explicitly states "Vixxo employee; work context only"
- Removes all Derek-specific biographical content from source

### Story 2.2: Port guardrail and formatting rules

As the AI in the template,
I want the same outbound-messaging, memory-protection, Teams formatting, and email-triage rules as gtd-life,
So that employees inherit proven guardrails without starting from scratch.

**Acceptance Criteria:**

- Port `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`
- Remove any Derek-specific examples; replace with neutral ones
- Each rule file ends with a brief one-line "why" comment

### Story 2.3: Create single generic `agents/personas/work.md`

As the AI,
I want one work persona file that parameterizes the employee's role, department, and key stakeholders,
So that I do not blend personal context into work tasks.

**Acceptance Criteria:**

- Single file at `agents/personas/work.md`
- Frontmatter fields: `type`, `scope: work`, `role`, `department`, placeholders for name and manager
- Body lists standard MCPs available (Linear, GitHub, M365, Salesforce, Gong)
- No RevivaGo, blog, or personal content

### Story 2.4: Confirm `benji-inbox-default.mdc` is NOT ported

As a template maintainer,
I want Benji-specific rules explicitly excluded,
So that the personal task system does not leak into the work template.

**Acceptance Criteria:**

- `.cursor/rules/benji-inbox-default.mdc` is not present in the template
- A CI assertion or checklist item confirms the absence

## Epic 3: Memory vault empty scaffold

### Story 3.1: Port `_template.md` and `_template/` trees from gtd-life

As a new employee,
I want the same memory vault structure as gtd-life with empty templates only,
So that I can start capturing meetings, people, decisions immediately.

**Acceptance Criteria:**

- `memory/meetings/_template/` contains `meeting.md`, `agenda.md`, `prep.md`, `transcript.md`
- `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md` all present
- Zero Derek content in any file

### Story 3.2: Portable `.obsidian/` config

As an employee,
I want Obsidian to open my memory vault cleanly,
So that templates, daily notes, and graph view work on first open.

**Acceptance Criteria:**

- `.obsidian/` contains Templates and Daily Notes config, no Derek vault history, no workspace cache

### Story 3.3: Seed empty `memory/me/identity.md` and `memory/me/preferences.md`

As an employee,
I want minimal identity and preference skeletons scoped explicitly to work,
So that the setup wizard has a target file to populate from my answers.

**Acceptance Criteria:**

- Frontmatter includes `scope: work`
- Body contains placeholder headings only; no Derek facts
- Both files are ready to be filled by the setup wizard

## Epic 4: MCP packaging (project-local)

### Story 4.1: Write `.cursor/mcp.json` with Active MCPs

As an employee,
I want Linear, GitHub, Microsoft 365, Salesforce, and Gong wired out of the box,
So that I can use the most common Vixxo work MCPs after running the wizard.

**Acceptance Criteria:**

- `.cursor/mcp.json` contains working entries for Linear, GitHub, M365, Salesforce, Gong
- Credentials referenced via env vars (no secrets in repo)

### Story 4.2: Add commented-out placeholders for pending MCPs

As a template maintainer,
I want consistent placeholder shapes for MCPs not yet wired,
So that wiring them later is a drop-in edit.

**Acceptance Criteria:**

- Commented JSON blocks for Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection MCP
- Each block ends with `// TODO: wiring; see <link or issue>`

### Story 4.3: Write `.env.example`

As an employee,
I want a single file listing every credential the template can consume,
So that I know what secrets to provision before running MCPs.

**Acceptance Criteria:**

- Section per MCP with variable name, purpose, and wiring link
- Marked `status: active | placeholder` per MCP

### Story 4.4: Rewrite `docs/setup.md` and `docs/mcps.md`

As a new employee,
I want self-serve onboarding docs,
So that I can stand up the template without paging Derek.

**Acceptance Criteria:**

- `docs/setup.md` covers prerequisites, clone, wizard, verify
- `docs/mcps.md` has a table: MCP, status (active/placeholder), env vars, link to internal wiki or issue
- Both docs reference the skills registry and `npx skills add vixxo-copilot/agent-skills`

## Epic 5: Interactive setup wizard

### Story 5.1: Scaffold `bin/init` Node entry point

As an employee,
I want `./bin/init` to be runnable right after clone,
So that I can bootstrap with one command.

**Acceptance Criteria:**

- `bin/init` executable, uses Node only (no bash-specific assumptions)
- Reads a tiny `package.json` for deps (`prompts` or similar)

### Story 5.2: Wizard prompts and file generation

As an employee,
I want to be asked for my name, email, role, and optional MCPs,
So that the template personalises without me editing files.

**Acceptance Criteria:**

- Prompts: name, email, Vixxo role/title, optional MCPs (checkboxes)
- Generates `memory/me/identity.md` and `agents/personas/work.md` from answers
- Copies `.env.example` to `.env`, leaves secrets blank

### Story 5.3: Wizard runs skills install and verifies

As an employee,
I want the wizard to install skills and verify my active MCPs,
So that I know the template works before I close the terminal.

**Acceptance Criteria:**

- Runs `npx skills add vixxo-copilot/agent-skills`
- Attempts a simple call against each active MCP and reports PASS/FAIL
- On FAIL, prints the exact fix command or wiki link

## Epic 6: PII scrub + CI guardrail (template half of E9)

### Story 6.1: Write shared PII deny-list config

As the template maintainer,
I want a single source of truth for banned personal patterns,
So that both repos enforce the same policy.

**Acceptance Criteria:**

- `.github/pii-denylist.txt` or similar in the template
- Covers Derek's full names, home address, family members, RevivaGo, blog content
- Referenced by the CI workflow

### Story 6.2: GitHub Action blocks PRs violating the deny-list

As a reviewer,
I want CI to fail fast when someone accidentally adds personal content,
So that we do not ship PII in merges.

**Acceptance Criteria:**

- Workflow runs on every PR
- Fails loudly with the offending file and line
- Runs in under 30 seconds

## Epic 7: Pilot rollout to Vixxo AI cohort

### Story 7.1: Write Vixxo-internal `GETTING_STARTED.md`

As a cohort participant,
I want a single doc that gets me from "clone" to "first meeting prep" in under 15 minutes,
So that I can experience the template without Derek walking me through it.

**Acceptance Criteria:**

- Covers: prerequisites, clone, `bin/init`, verify MCPs, run `meeting-prep` skill
- Lives inside template

### Story 7.2: 30-minute kickoff with AI cohort

As Derek,
I want a single group kickoff for the cohort,
So that adoption starts with shared context and energy.

**Acceptance Criteria:**

- Calendar invite sent
- Agenda: demo, setup live, Q&A
- Deck or Loom link stored in cohort folder

### Story 7.3: `#personal-agents` Teams channel and feedback loop

As a cohort participant,
I want one channel to ask questions, file bugs, and suggest skills,
So that friction turns into fixes fast.

**Acceptance Criteria:**

- Channel exists, description points to both repos
- Triage policy documented (issue here vs skill PR vs template PR)
- Weekly sweep produces at least one PR for the first two weeks