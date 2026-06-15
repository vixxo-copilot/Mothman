# Story 2.3 Baseline Audit

Captured during Task 1 (Phase 2, Dev agent Amelia). This audit records the upstream source-persona contents that the generic `agents/personas/work.md` file collapses into, plus the Story 2.3 banned-term set, active-MCP lock, and source-to-target collapse map. Evidence here drives Task 2's canonical blueprint and Task 4's cross-file scrub. Source personas live outside this repository at `~/Public/gtd-life/agents/personas/` and are read-only reference material — no content is ported verbatim.

## Source Persona: `vixxo-cto.md` (structural donor)

Path: `~/Public/gtd-life/agents/personas/vixxo-cto.md`

### Frontmatter

- `type: persona`
- `role: "CTO - AI"`
- `company: vixxo`
- `tags: [persona, vixxo, work, technical-leadership]`

### Top-level section list

1. `# Vixxo CTO - AI`
2. `## Role`
3. `## Responsibilities`
4. `## Key People`
5. `## Available MCPs`
6. `## Email`
7. `## Calendar`
8. `## Task System`
9. `## Communication Tone`
10. `### Voice Directives (apply when drafting as Derek)`
11. `## Context Files`

### MCP table content

| MCP | Purpose |
|-----|---------|
| Linear | Engineering task and project management |
| Salesforce | CRM, pipeline, accounts, contacts |
| Gong | Call recordings, transcripts, deal intelligence |
| Microsoft 365 | Outlook email and calendar |
| Slack | Team communication |
| GitHub | Source control, repo documentation |

### Email / Calendar / Task System

- Email: Microsoft 365 / Outlook (includes a hard-coded employee mailbox)
- Calendar: Microsoft Outlook (via M365)
- Task System: Linear (Vixxo workspace)

### Communication tone paragraph

Technical leadership framing. Direct, evidence-based. Includes a dedicated `### Voice Directives` subsection with NVC, "Lift people up", "Bias to action" — this is Derek-specific voice biography and is a negative donor in the collapse map.

### Context Files list

- `memory/companies/vixxo/overview.md`
- `memory/companies/vixxo/tools.md`
- `memory/companies/vixxo/org-chart.md`

## Source Persona: `revivago-ceo.md` (negative donor)

Path: `~/Public/gtd-life/agents/personas/revivago-ceo.md`

### Frontmatter

- `type: persona`
- `role: CEO`
- `company: revivago`
- `tags: [persona, revivago, work, executive]`

### Section list

- `# RevivaGo CEO`, `## Role`, `## Responsibilities`, `## Key People`, `## Available MCPs`, `## Email`, `## Calendar`, `## Task System`, `## Communication Tone`, `## Context Files`.

### MCP table

Notion, Gmail, Google Calendar, Slack, GitHub.

### Email / Calendar / Task System

- Email: Gmail
- Calendar: Google Calendar
- Task System: Notion

### Collapse posture

Entire file is excluded. Every section references the banned `revivago` scope token (company name), Gmail/Google stack, Notion task system, VeinCraft/Daddy Bootcamps/After the Stork sub-brands, and peptide content — all banned-term territory.

## Source Persona: `personal.md` (negative donor)

Path: `~/Public/gtd-life/agents/personas/personal.md`

### Frontmatter

- `type: persona`
- `role: personal`
- `company: none`
- `tags: [persona, personal, blog, side-projects]`

### Section list

- `# Personal`, `## Context`, `## Responsibilities`, `## Available Tools`, `## Email`, `## Calendar`, `## Task System`, `## Communication Tone`, `## Context Files`.

### Tool table

Benji.so, Gmail, Google Calendar, Flowtopic, GitHub, Obsidian.

### Email / Calendar / Task System

- Email: Gmail (personal)
- Calendar: Google Calendar (personal)
- Task System: Benji.so

### Collapse posture

Entire file is excluded. References blog content, MasteryLab, Agile Weekly, Flowtopic, Benji.so, Obsidian, family, fitness, side ventures — all banned.

## Target location confirmation

- `agents/personas/` directory exists from Story 1.1 scaffold with a zero-byte `.gitkeep` sentinel.
- `agents/personas/work.md` does NOT yet exist prior to Task 3.
- `.gitkeep` will remain in place after Task 3 authoring.

## Story 2.3 banned-term set (consolidated)

Inherited from Story 2.2 (which extended Story 2.1):

- `Derek`, `Deke`, `Neighbors`, `Chiron`, `RevivaGo`, `derekneighbors.com`, `Agile Weekly`, `MasteryLab`, `Bodybuilding.com`, `Gangplank`, `ASU`, `gtd-life`, `arete`, `eudaimonia`, `blog`, `Gmail`, `Google Calendar`, `Google Workspace`, `Google Drive`, `Google Chat`, `personal email`, `Slack`, `Benji`.

Persona-specific additions (Story 2.3):

- `Notion`, `Flowtopic`, `VeinCraft`, `Daddy Bootcamps`, `After the Stork`, `peptide`, `family`, `Laurie`, `Bobby Hunnicutt`, `Brandon Franz`, `Eric Burt`, `Gino Flores`, `Viswa Vadlamani`, `Jignesh Patel`, `Jim Reavey`.

Boundary-guarded tokens (POSIX-ERE `(^|[^A-Za-z])TOKEN($|[^A-Za-z])`): `asu`, `blog`, `deke`, `arete`, `eudaimonia`, `slack`, `benji`, `family`. The `family` token is boundary-guarded because legitimate English words ("familiar", "multifamily") would false-positive on a naive substring match.

## Active-MCP lock (Vixxo work only)

Byte-for-byte aligned with `.cursor/rules/agent-identity.mdc` `## Available Tools (overview)`:

1. **Linear** — Vixxo work task and project management
2. **GitHub** — source control, code review, repository documentation
3. **Microsoft 365** — Outlook email and calendar
4. **Salesforce** — CRM, pipeline, accounts, contacts
5. **Gong** — call recordings, transcripts, deal intelligence

Placeholder MCPs (Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection) are Story 4.2 territory and MUST NOT appear in the persona body.

## Source-to-target collapse map

| Source file | Role in collapse | Port disposition |
| ----------- | ---------------- | ---------------- |
| `vixxo-cto.md` | Structural donor | Skeleton only: section layout, MCP table shape, email/calendar/task-system stanza pattern. No proper names, no role-specific bullets, no coworker roster, no Derek voice-biography subsection. |
| `revivago-ceo.md` | Negative donor | Entire file excluded. Confirms the `revivago`, Gmail/Google, Notion scrub. |
| `personal.md` | Negative donor | Entire file excluded. Confirms the blog, MasteryLab, Agile Weekly, Benji, Flowtopic, family scrub. |

Three source personas collapse into one target: `agents/personas/work.md` — a single generic Vixxo-work persona parameterized by `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`. Epic 2 FR3 coverage.
