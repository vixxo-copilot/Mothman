# Story 2.3 Canonical Blueprint

Locked design for the single generic `agents/personas/work.md` authored in Task 3. Every lock in this document maps to one or more ACs in Story 2.3 and is enforced by the Task 5 validation harness.

## Section layout lock (nine headers, exact order)

1. `# Work Persona`
2. `## Role`
3. `## Responsibilities`
4. `## Available MCPs`
5. `## Email`
6. `## Calendar`
7. `## Task System`
8. `## Communication Tone`
9. `## Context Files`

No other headers. No `### Voice Directives` subsection (that was Derek-specific voice biography; Story 2.3 AC6 explicitly forbids it). No `## Key People` section (coworker roster lives outside this story per Epic 3). No `## Context` section (that was the personal-persona wrapper; replaced by `## Role`).

## Frontmatter lock (AC2)

```
---
type: persona
scope: work
role: "{{employee_role}}"
department: "{{employee_department}}"
name: "{{employee_name}}"
manager: "{{employee_manager}}"
tags: [persona, work, vixxo]
---
```

- Every placeholder value is double-quoted so the YAML parser treats `{{...}}` as a literal string.
- `tags` is an inline bracketed list with exactly three items in the locked order `[persona, work, vixxo]` — comma+space separated, no trailing comma. The ordering is fixed so the validation harness can `grep -Fxq` an exact-line match.
- No `company:` key (the `revivago` gtd-life source uses `company: revivago`; Story 2.3 replaces this with `scope: work` + the `vixxo` tag).

## `## Available MCPs` table lock (AC3)

```
| MCP | Purpose |
| --- | --- |
| **Linear** | Vixxo work task and project management |
| **GitHub** | Source control, code review, repository documentation |
| **Microsoft 365** | Outlook email and calendar |
| **Salesforce** | CRM, pipeline, accounts, contacts |
| **Gong** | Call recordings, transcripts, deal intelligence |
```

Five rows, fixed order. Each MCP proper name is bold-wrapped (`**Name**`) so `grep -Fq` over `**Linear**`, `**GitHub**`, `**Microsoft 365**`, `**Salesforce**`, `**Gong**` succeeds exactly once per token. No Slack row, no Notion row, no placeholder-MCP row.

## `## Role` paragraph lock

One short paragraph in generic Vixxo phrasing. Uses only `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_name}}`. No hard-coded title (`CTO`, `VP`, etc.). No headcount. No legacy-systems list. No AI-transformation branding. Reporting line phrased as "Reports to `{{employee_manager}}`." A single pointer defers `Scope` and `Who the Employee Is` to `.cursor/rules/agent-identity.mdc` (no duplication of the identity rule's body).

## `## Responsibilities` bullets lock

3–6 bullets, generic Vixxo work framing, keyed off `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}`. No coworker names, no legacy systems (ADO, Siebel, SalesLogix), no team counts, no "AI transformation" branding. Representative phrasing:

- Deliver the objectives of `{{employee_department}}` as `{{employee_role}}` at Vixxo.
- Coordinate with `{{employee_manager}}` and cross-functional partners across the business.
- Use approved Vixxo systems, MCPs, and tooling.
- Maintain clear written artifacts, decisions, and follow-ups.

## `## Email` lock (AC5)

Exact one-line value: `Microsoft 365 (Outlook).`

No mailbox address. No `{{employee_email}}` placeholder (that token is Story 5.2 wizard scope).

## `## Calendar` lock (AC5)

Exact one-line value: `Microsoft 365 (Outlook calendar).`

## `## Task System` lock (AC5)

Exact one-line value: `Linear (Vixxo work task system).`

No Notion, no Benji, no personal task system.

## `## Communication Tone` lock (AC6)

3–6 lines. Content lock: concise and direct; evidence-backed; plain business English; match Vixxo cultural norms; defer outbound drafting discipline to `.cursor/rules/outbound-messaging-guardrail.mdc` (single reference, no restatement of the draft-then-approve workflow). Explicitly EXCLUDED:

- `### Voice Directives` subsection (do not create one)
- NVC / Non-Violent Communication content
- "Lift people up" framing
- "Bias to action" framing
- Humor / meme / emoji guidance
- Sign-off preferences (those live in the outbound rule)
- Any proper-name voice biography ("Derek", "as Derek", etc.)

## `## Context Files` lock (AC7)

Six bullets, in this exact order:

1. `.cursor/rules/agent-identity.mdc`
2. `memory/me/identity.md`
3. `memory/me/preferences.md`
4. `AGENTS.md`
5. `CLAUDE.md`
6. `.cursorrules`

No `memory/companies/**` paths. No `memory/me/family.md`, `memory/me/ventures.md`, `memory/me/properties.md`. No sibling persona references.

## "Why" comment terminator lock (AC8)

One-line HTML comment placed after the final section, separated by one blank line. Locked form:

```
<!-- Why: single generic Vixxo work persona keeps scope clean; anything outside Vixxo work belongs outside the template. -->
```

The comment body contains zero banned terms — verified during Task 4 scrub.

## Placeholder contract lock

Only four placeholder tokens appear in the persona body:

- `{{employee_name}}`
- `{{employee_role}}`
- `{{employee_department}}`
- `{{employee_manager}}`

No new tokens introduced. Parity with `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, and all five `.cursor/rules/*.mdc` files (Story 1.3 + 2.1 + 2.2 set).

## Cross-AC coverage map

| AC | Lock |
| --- | --- |
| AC1 | Target path + nine-header layout + frontmatter delimiters |
| AC2 | Frontmatter key/value lock + placeholder contract |
| AC3 | Five-MCP table lock (active set only; no placeholder MCPs, no Slack/Notion/Google/Benji) |
| AC4 | Banned-term scrub + POSIX-ERE boundary guards + regex self-probe |
| AC5 | `## Email`, `## Calendar`, `## Task System` one-liner locks |
| AC6 | Communication Tone 3–6-line lock; `### Voice Directives` absence; outbound-rule pointer |
| AC7 | Context Files six-bullet lock; identity-rule deferral; no sibling-persona references |
| AC8 | HTML "why" comment terminator after final section |
| AC9 | Task 5 harness gates (`task1`–`task6` + `all`) + regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 harnesses |
| AC10 | Sprint tracker lifecycle (`backlog → ready-for-dev → review` via single-line transition per Story 2.1/2.2 pattern) |
