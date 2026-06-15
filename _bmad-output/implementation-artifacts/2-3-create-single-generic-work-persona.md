# Story 2.3: Create single generic `agents/personas/work.md`

Status: done

## Story

As the AI in a cloned Vixxo `assistants-template` workspace,
I want a single generic work persona at `agents/personas/work.md` — parameterized by the employee's name, role, department, and manager, and listing the five active Vixxo MCPs —
so that I never blend personal, RevivaGo, or multi-persona context into work tasks and the identity rule's `Key References` pointer (`agents/personas/work.md`, landed in Story 2.1) resolves to a real file.

## Acceptance Criteria

1. **AC1 — Single persona file exists at `agents/personas/work.md` (not a `.gitkeep`) with correct frontmatter**
   - Given the cloned `assistants-template` repository after Stories 2.1 and 2.2 landed `.cursor/rules/agent-identity.mdc` and the sibling guardrail/formatting rules
   - When `agents/personas/` is listed
   - Then `agents/personas/work.md` exists as a real markdown file (no `.gitkeep`, no zero-byte placeholder)
   - And the file begins with a YAML frontmatter block delimited by `---` on line 1 and a matching `---` line
   - And no other persona files exist in `agents/personas/` (no `vixxo-cto.md`, `revivago-ceo.md`, `personal.md`, or any sibling persona — this story collapses the legacy multi-persona layout per Epic 2 FR3)
   - And `agents/personas/.gitkeep` is either removed or retained as an empty sentinel; if retained, it must remain zero-byte and must not be treated as a persona file by any validation harness

2. **AC2 — Frontmatter carries the required persona metadata with `scope: work` and placeholders for name and manager**
   - Given `agents/personas/work.md`
   - When its frontmatter is parsed
   - Then the frontmatter contains the following keys, each with the exact value form below:
     - `type: persona`
     - `scope: work`
     - `role: "{{employee_role}}"`
     - `department: "{{employee_department}}"`
     - `name: "{{employee_name}}"`
     - `manager: "{{employee_manager}}"`
     - `tags: [persona, work, vixxo]` (exact list; ordering is fixed so the validation harness can grep-match)
   - And no frontmatter key carries a hard-coded employee proper name, company name other than `vixxo`, department, or manager identifier
   - And no additional placeholder tokens are introduced beyond the Story 1.3 / 2.1 / 2.2 approved set (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`); if a future story needs a new token it MUST follow the `{{snake_case}}` convention and be recorded in this story's Dev Notes

3. **AC3 — Body lists the five active Vixxo MCPs and references no other MCP stack**
   - Given the body of `agents/personas/work.md`
   - When the `## Available MCPs` section is scanned
   - Then the section lists exactly these five MCPs as the active set, in this order: **Linear**, **GitHub**, **Microsoft 365**, **Salesforce**, **Gong**
   - And the list form is a markdown table with columns `MCP` and `Purpose` (matching the source persona table shape) OR a bulleted `**MCP** — purpose` list (one bullet per MCP); whichever form is locked in Task 2's blueprint, the five MCP proper names appear as bold-rendered tokens so a `grep -Fq` on `**Linear**`, `**GitHub**`, `**Microsoft 365**`, `**Salesforce**`, `**Gong**` succeeds once per token
   - And the MCP list matches the Story 2.1 `agent-identity.mdc` `## Available Tools (overview)` active set byte-for-byte (no drift between the identity rule and the persona)
   - And the section does NOT list Slack, Notion, Gmail, Google Calendar, Google Workspace, Google Drive, Flowtopic, Benji, Benji.so, Obsidian (as an MCP — Obsidian is a memory-vault viewer, not an MCP), or any other non-Vixxo-active MCP
   - And the ChatFPT, Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, Elastic, and agent-skills Introspection MCPs (Story 4.2 placeholders) are NOT listed in the persona body — placeholder MCPs are Story 4.2's responsibility and must not leak into the persona

4. **AC4 — Zero RevivaGo, blog, or personal content; banned-term scrub passes**
   - Given `agents/personas/work.md`
   - When the file is scanned case-insensitively with the Story 2.2 banned-term set
   - Then the file contains zero occurrences of: `Derek`, `Deke`, `Neighbors`, `Chiron`, `RevivaGo`, `derekneighbors.com`, `Agile Weekly`, `MasteryLab`, `Bodybuilding.com`, `Gangplank`, `ASU`, `gtd-life`, `arete`, `eudaimonia`, `blog`, `Gmail`, `Google Calendar`, `Google Workspace`, `Google Drive`, `Google Chat`, `personal email`, `Slack`, `Benji`, `Notion`, `Flowtopic`, `VeinCraft`, `Daddy Bootcamps`, `After the Stork`, `peptide`, `family`, and any real employee or coworker proper names from the source persona files
   - And the scrub uses the Story 2.2 POSIX-ERE boundary guards (so `ASU`, `blog`, `deke`, `arete`, `eudaimonia`, `slack`, `benji` do not false-positive on legitimate English fragments)
   - And a regex self-probe verifies the host grep honors those boundary guards (fail-fast if not)
   - And the file contains zero email addresses (no `@`-joined mailbox+domain pattern), zero phone numbers, zero Microsoft Graph user IDs / UPNs, and zero Teams `chatId` strings

5. **AC5 — M365-only email and calendar routing in the persona body**
   - Given `agents/personas/work.md`
   - When the `## Email`, `## Calendar`, and `## Task System` sections are reviewed
   - Then `## Email` names only `Microsoft 365` (phrased as `Microsoft 365` — with `(Outlook)` clarification permitted per the Story 2.2 convention)
   - And `## Calendar` names only `Microsoft 365` (same clarification permitted)
   - And `## Task System` names only `Linear` (Linear is the Vixxo work task system; Notion, Benji, Benji.so, and any personal task system are explicitly absent)
   - And no section mentions Gmail, Google Calendar, Google Workspace, Google Drive, Outlook.com, personal email, SMS, iMessage, or any non-Vixxo stack

6. **AC6 — Voice and tone are generic Vixxo-work only; no "draft as Derek" / NVC biography block**
   - Given the `## Communication Tone` section
   - When the body is reviewed
   - Then the tone description is concise (≤ 8 lines), addresses `{{employee_name}}` generically (no hard-coded biographical preference), and sets the expectation that messages drafted for `{{employee_name}}` read as their own voice (deferral to `.cursor/rules/outbound-messaging-guardrail.mdc` for the draft-then-approve workflow, not restated here)
   - And the source rule's `### Voice Directives (apply when drafting as Derek)` subsection (NVC, "Lift people up", "Bias to action") is NOT ported — those were Derek-specific voice biography and belong to no one else's persona; the persona body references the Story 2.2 outbound-messaging rule by relative path (`.cursor/rules/outbound-messaging-guardrail.mdc`) as the single source of truth for drafting discipline
   - And no paragraph contains the words `Derek`, `NVC`, `Non-Violent Communication`, `Lift people up`, `Bias to action`, or any rhetorical phrasing that names a specific human voice

7. **AC7 — Cross-reference integrity with Story 2.1 `agent-identity.mdc` and Epic 3 memory paths**
   - Given the Story 2.1 identity rule (which already references `agents/personas/work.md` in both `## Work Persona` and `## Key References`)
   - When `agents/personas/work.md` is reviewed
   - Then the persona body contains a `## Context Files` (or equivalently named `## Related Files`) section that points to:
     - `.cursor/rules/agent-identity.mdc` (identity rule; do not restate its `## Scope` / `## Who the Employee Is` blocks in the persona body)
     - `memory/me/identity.md` (Story 3.3 target)
     - `memory/me/preferences.md` (Story 3.3 target)
     - `AGENTS.md`, `CLAUDE.md`, `.cursorrules` (Story 1.3 outputs)
   - And the persona body does NOT reference `memory/companies/vixxo/org-chart.md`, `memory/companies/vixxo/overview.md`, `memory/companies/vixxo/tools.md`, `memory/companies/revivago/**`, `memory/companies/blog/**`, `memory/me/family.md`, `memory/me/properties.md`, or `memory/me/ventures.md` — those paths are gtd-life-specific and are out of scope for the template per Epic 3
   - And no sibling persona file is referenced (no `vixxo-cto.md`, `revivago-ceo.md`, `personal.md`); the persona is singular
   - And `.cursor/rules/agent-identity.mdc` is NOT regressed by this story (zero edits; the identity rule already references `agents/personas/work.md`)

8. **AC8 — File ends with a one-line "why" comment (Epic 2 convention)**
   - Given `agents/personas/work.md`
   - When the last non-blank line is inspected
   - Then the last non-blank line is a single-line comment — HTML comment (`<!-- ... -->`), markdown blockquote (`>`), or italic-wrapped single line (`_..._`) — that states in one sentence why the persona exists (e.g. `<!-- Why: single generic work persona keeps Vixxo work scope clean; any personal, RevivaGo, or multi-persona content belongs outside the template. -->`)
   - And the "why" comment is itself scrubbed — contains no banned terms and no hard-coded employee / manager / coworker proper names
   - And the "why" comment is placed AFTER the final body section (not inside the frontmatter block) so YAML parsers do not try to interpret it

9. **AC9 — Deterministic validation harness exists and passes; regression-runs Story 1.x, 2.1, and 2.2 harnesses**
   - Given this story's test directory `_bmad-output/implementation-artifacts/tests/`
   - When `bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all` is run
   - Then it prints `PASS: all` and exits `0`
   - And individual gates `task1` through `taskN` each print `PASS: <task>` when invoked independently
   - And the harness covers: file existence at `agents/personas/work.md`, no-other-personas negative check, frontmatter shape (every AC2 key with the exact value form, `tags` list exact match), required section headers (per Task 2 blueprint), active-MCP list exact match (`**Linear**`, `**GitHub**`, `**Microsoft 365**`, `**Salesforce**`, `**Gong**`; no other MCP tokens), M365-only routing assertions (AC5), banned-term scan with POSIX-ERE boundary guards and regex self-probe (AC4), placeholder parity across the rule pack + root context files + new persona (AC2), identity-block-deferral guard (AC6/AC7 — persona must not restate `## Scope` / `## Who the Employee Is` blocks from `agent-identity.mdc`), no-Derek-voice-directives guard (AC6), "why"-comment terminator (AC8), and regression invocation of `story-1-1-scaffold-validation.sh all`, `story-1-2-root-files-validation.sh all`, `story-1-3-root-context-validation.sh all`, `story-2-1-agent-identity-validation.sh all`, and `story-2-2-guardrail-and-formatting-validation.sh all`

10. **AC10 — Sprint tracker lifecycle reflects the story transition; epic and sibling-story states are preserved**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When Story 2.3 opens at Phase 1 (SM pass) and again at Phase 2 (Dev handoff)
    - Then the `2-3-create-single-generic-work-persona.status` entry is updated `backlog → ready-for-dev` (Phase 1) and `ready-for-dev → review` (Phase 2 handoff; the autonomous-swarm lifecycle may collapse the interim states per the Story 2.1/2.2 precedent — the on-disk single-line transition is acceptable as long as the final status before review commits is `review`)
    - And `epic-2.status` remains `in-progress` (Story 2.4 remains backlog; epic does not yet flip to `done`)
    - And no other story's status is regressed, and every comment, blank line, and section block in `sprint-status.yaml` is preserved byte-for-byte (zero reordering, zero comment drift)

## Tasks / Subtasks

- [x] Task 1 — Baseline audit of source persona files and target location (AC: 1, 2, 3, 4, 5, 6, 7)
  - [x] Read `~/Public/gtd-life/agents/personas/vixxo-cto.md`, `~/Public/gtd-life/agents/personas/revivago-ceo.md`, and `~/Public/gtd-life/agents/personas/personal.md`. Capture each source file's frontmatter, top-level section list, MCP table content, email/calendar/task-system stack, communication-tone paragraph, and Context Files list.
  - [x] Confirm the target path `agents/personas/work.md` does not yet exist (Story 1.1 placed only `agents/personas/.gitkeep` under `agents/personas/`). Confirm the directory exists (Story 1.1 scaffold).
  - [x] Record the Story 2.3 banned-term set: Story 2.2 list (Story 2.1 identity/biography carryover + `slack` + `benji`) PLUS persona-specific additions (`Notion`, `Flowtopic`, `VeinCraft`, `Daddy Bootcamps`, `After the Stork`, `peptide`, `family`, and any real employee or coworker proper names). Personal coworker names from the source persona files are explicitly banned so the persona stays role-only.
  - [x] Record the source-to-target collapse map: `vixxo-cto.md` contributes the persona skeleton (role, responsibilities shape, MCP table, email/calendar/task system); `revivago-ceo.md` and `personal.md` contribute ONLY the negative assertions (none of their content is ported). All three source files collapse into the single generic `agents/personas/work.md` per Epic 2 FR3.
  - [x] Record the active-MCP lock: Linear, GitHub, Microsoft 365, Salesforce, Gong (matches Story 2.1 `agent-identity.mdc` `## Available Tools (overview)`). Placeholder MCPs (Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection) are Story 4.2's responsibility and must NOT appear in the persona.
  - [x] Persist baseline evidence at `_bmad-output/implementation-artifacts/tests/story-2-3-baseline-audit.md`, one subsection per source file plus the consolidated banned-term list, active-MCP lock, and collapse map.

- [x] Task 2 — Design canonical generic persona blueprint (AC: 1, 2, 3, 5, 6, 7, 8) **[Sequential — depends on Task 1]**
  - [x] Lock the file section layout (exact headers, exact order): `# Work Persona`, `## Role`, `## Responsibilities`, `## Available MCPs`, `## Email`, `## Calendar`, `## Task System`, `## Communication Tone`, `## Context Files`.
  - [x] Lock the frontmatter shape and exact value forms per AC2: `type: persona`, `scope: work`, `role: "{{employee_role}}"`, `department: "{{employee_department}}"`, `name: "{{employee_name}}"`, `manager: "{{employee_manager}}"`, `tags: [persona, work, vixxo]`.
  - [x] Lock the `## Available MCPs` table shape: markdown table with header `| MCP | Purpose |`, five rows in the fixed order Linear / GitHub / Microsoft 365 / Salesforce / Gong. Lock the per-MCP one-line purpose: Linear (Vixxo work task and project management), GitHub (source control, code review, repository documentation), Microsoft 365 (Outlook email and calendar), Salesforce (CRM, pipeline, accounts, contacts), Gong (call recordings, transcripts, deal intelligence). Purpose strings are short and Vixxo-generic.
  - [x] Lock the `## Role` paragraph: one short paragraph in generic Vixxo phrasing, using only `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` placeholders (plus `{{employee_name}}` as addressee if necessary). No company storyline, no transformation narrative, no legacy-systems list, no AI-platform branding. Reporting line phrased as "Reports to `{{employee_manager}}`." with no real employee proper names.
  - [x] Lock the `## Responsibilities` bullet list: 3–6 generic Vixxo work bullets keyed off `{{employee_role}}` and `{{employee_department}}`. Do not copy the source CTO bullets verbatim; rewrite for role-neutral phrasing (e.g. "Deliver the objectives of `{{employee_department}}` as `{{employee_role}}`", "Coordinate with `{{employee_manager}}` and cross-functional partners", "Use approved Vixxo systems, MCPs, and tooling"). Personal coworker names are explicitly banned.
  - [x] Lock the `## Email`, `## Calendar`, `## Task System` one-line values: `Microsoft 365 (Outlook).`, `Microsoft 365 (Outlook calendar).`, `Linear (Vixxo work task system).` No email address (no `{{employee_email}}` placeholder introduced here — that placeholder is Story 5.2 wizard scope). No phone number. No personal task system.
  - [x] Lock the `## Communication Tone` paragraph: 3–6 lines. Key content: concise and direct; evidence-backed; plain business English; match Vixxo cultural norms; when drafting outbound messages, follow `.cursor/rules/outbound-messaging-guardrail.mdc` (draft-then-approve). Explicitly lock OUT of the paragraph: Derek's NVC guidance, "Lift people up" framing, "Bias to action" framing, humor/memes/emoji guidance, sign-off preferences. Explicitly lock OUT a `### Voice Directives` subsection (do not create one).
  - [x] Lock the `## Context Files` bullet list: `.cursor/rules/agent-identity.mdc`, `memory/me/identity.md`, `memory/me/preferences.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`. Exactly six bullets, in that order. No `memory/companies/...` paths, no `memory/me/family.md`, no `memory/me/ventures.md`, no `memory/me/properties.md`.
  - [x] Lock the one-line "why" comment terminator per AC8. Recommended: `<!-- Why: single generic work persona keeps Vixxo work scope clean; personal, RevivaGo, and multi-persona content belong outside the template. -->`. Verify the chosen terminator contains zero banned terms.
  - [x] Persist the locked blueprint at `_bmad-output/implementation-artifacts/tests/story-2-3-canonical-blueprint.md` with one subsection per persona section plus a cross-AC coverage table (matching the structure of Story 2.1 / 2.2 blueprints).

- [x] Task 3 — Author `agents/personas/work.md` per blueprint (AC: 1, 2, 3, 5, 6, 7, 8) **[Sequential — depends on Task 2; can run in parallel with Task 5 harness-scaffold]**
  - [x] Create the file at `agents/personas/work.md` (sibling to `.gitkeep` under `agents/personas/`; leave the `.gitkeep` in place for Story 1.1 scaffold harness compatibility).
  - [x] Write frontmatter exactly per Task 2's lock: `type: persona`, `scope: work`, `role: "{{employee_role}}"`, `department: "{{employee_department}}"`, `name: "{{employee_name}}"`, `manager: "{{employee_manager}}"`, `tags: [persona, work, vixxo]`. Frontmatter values that contain placeholders MUST be double-quoted so the YAML parser does not try to interpret `{{...}}` as a YAML tag or alias.
  - [x] Header: `# Work Persona` (exactly; no `# Vixxo Work Persona` or any other variant).
  - [x] `## Role` paragraph per Task 2's lock. Keep to one short paragraph. Placeholders only; no hard-coded `Vixxo CTO`, `Chief Technology Officer`, or any other titled role.
  - [x] `## Responsibilities` bullet list per Task 2's lock. 3–6 generic bullets keyed off `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}`. No legacy-systems references (ADO, Siebel, SalesLogix). No team-count numbers. No "AI transformation" branding.
  - [x] `## Available MCPs` table per Task 2's lock. Exactly five rows (Linear, GitHub, Microsoft 365, Salesforce, Gong) with the locked one-line purposes. No Slack row. No Notion row. No placeholder-MCP row.
  - [x] `## Email` one-liner per Task 2's lock (Microsoft 365 (Outlook).).
  - [x] `## Calendar` one-liner per Task 2's lock (Microsoft 365 (Outlook calendar).).
  - [x] `## Task System` one-liner per Task 2's lock (Linear (Vixxo work task system).).
  - [x] `## Communication Tone` paragraph per Task 2's lock. Reference `.cursor/rules/outbound-messaging-guardrail.mdc` once, as a pointer to the sibling guardrail; do not restate the draft-then-approve workflow in the persona body. Do NOT create a `### Voice Directives` subsection.
  - [x] `## Context Files` bullet list per Task 2's lock: six bullets in the locked order.
  - [x] Terminate the file with the locked one-line "why" comment (AC8), placed on its own line after the final body section, separated from the preceding content by exactly one blank line.
  - [x] Write a single pointer line in the `## Role` section (or opening block) deferring the `Scope` and `Who the Employee Is` blocks to `.cursor/rules/agent-identity.mdc` so the persona does not duplicate the identity rule's content.

- [x] Task 4 — Cross-file scrub, placeholder parity, and deferred-content checks (AC: 2, 3, 4, 5, 6, 7) **[Sequential — depends on Task 3 artifact]**
  - [x] Run the Story 2.3 banned-term scan over `agents/personas/work.md` in two passes: (1) unbounded case-insensitive regex over the long tokens (`neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|gtd-life|gmail|google calendar|google workspace|google drive|google chat|personal email|slack|benji|notion|flowtopic|veincraft|daddy bootcamps|after the stork|peptide|laurie|bobby hunnicutt|brandon franz|eric burt|gino flores|viswa vadlamani|jignesh patel|jim reavey`); (2) POSIX-ERE boundary-guarded scan over the short tokens `(^|[^A-Za-z])(derek|deke|asu|blog|arete|eudaimonia|family)($|[^A-Za-z])`. Require zero matches on each pass. Note: `family` is boundary-guarded because "family" fragments legitimately appear in larger English words; the persona is role-and-tool-only and should not reference family at all.
  - [x] Run a regex self-probe against a synthetic input (e.g. `derek\nderekolor\nchiron\nbloghouse\nlog\nfamily\nfamiliar\n`) and confirm the host `grep -E` matches only `derek`, `chiron`, `family` under the boundary-guarded alternation (correctly skipping `derekolor`, `bloghouse`, `log`, `familiar`). Fail-fast if the host grep does not honor the boundary guards.
  - [x] Verify the placeholder inventory across the persona body: only `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` appear; no new token is introduced. Capture the unique set via `grep -oE '\{\{[a-z_]+\}\}' agents/personas/work.md | sort -u`.
  - [x] Cross-check placeholder parity with `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, and all five `.cursor/rules/*.mdc` files. The cross-pack allowlist stays `{{employee_name}}` / `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}`.
  - [x] Deferred-content guard: verify the persona body does NOT contain the strings `Vixxo employee` AND `work context only` together (those tokens belong to `.cursor/rules/agent-identity.mdc`; AC2's `scope: work` frontmatter value is sufficient for persona-level scope declaration).
  - [x] Anti-voice-biography guard: verify zero occurrences of `### Voice Directives`, `NVC`, `Non-Violent Communication`, `Lift people up`, `Bias to action`.
  - [x] Email-address pattern guard: verify zero matches for `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`.
  - [x] Active-MCP-list exact match: verify the `## Available MCPs` section contains `**Linear**`, `**GitHub**`, `**Microsoft 365**`, `**Salesforce**`, `**Gong**` exactly once each (positive assertion) AND contains zero matches for `**Slack**`, `**Notion**`, `**Gmail**`, `**Google Calendar**`, `**Google Workspace**`, `**Flowtopic**`, `**Benji**`, `**Benji.so**`, `**Obsidian**`, `**Freshdesk**`, `**Dynamics**`, `**VixxoNow**`, `**VixxoLink**`, `**Gateway**`, `**ZoomInfo**`, `**HubSpot**`, `**AWS Connect**`, `**ChatFPT**`, `**Elastic**`, `**Introspection**` (negative assertion).
  - [x] Sibling-persona absence guard: verify `agents/personas/vixxo-cto.md`, `agents/personas/revivago-ceo.md`, `agents/personas/personal.md` do NOT exist in the template.
  - [x] Record the Task 4 evidence inline in the story file's `Dev Agent Record` (grep output captured, counts documented).

- [x] Task 5 — Deterministic validation harness (AC: 9) **[Scaffoldable in parallel with Task 3; final wiring depends on Task 3 artifact]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh`. POSIX-bash-3.2 compatible, `set -euo pipefail`, shebang `#!/usr/bin/env bash`. Print `PASS: <gate>` / `FAIL: <gate>: <reason>` to stderr on failure. Mark the file executable (`chmod +x`). Model on `story-2-2-guardrail-and-formatting-validation.sh`.
  - [x] Gates (suggested): `task1` baseline-audit-evidence (title + required sections + every Story 2.3 banned-term entry); `task2` blueprint-evidence (title + required sections + every locked section header); `task3` persona-file-shape (file exists, frontmatter shape per AC2, required section headers exact-line match, active-MCP table shape); `task4` cross-file scrub + placeholder parity + deferred-content guards; `task5` self-check (harness well-formed); `task6` regression against `story-1-1`, `story-1-2`, `story-1-3`, `story-2-1`, `story-2-2` harnesses; `all` runs every gate in order.
  - [x] Reuse the Story 2.2 POSIX-ERE boundary-guard regex and extend the alternation with `family` (boundary-guarded). Include a `regex_self_probe` that probes all boundary-guarded tokens (`asu`, `blog`, `deke`, `arete`, `eudaimonia`, `slack`, `benji`, `family`) against synthetic inputs — fail-fast if the host grep does not honor the boundary guards.
  - [x] Frontmatter validation: parse the YAML block between the first two `---` delimiters with `awk`; assert each of the seven required keys (`type`, `scope`, `role`, `department`, `name`, `manager`, `tags`) is present with the exact value form from AC2. For `tags`, assert the inline list matches `[persona, work, vixxo]` exactly (bracket-delimited, comma+space separated, no ordering drift).
  - [x] Required section headers (exact-line match via `grep -Fxq`): `# Work Persona`, `## Role`, `## Responsibilities`, `## Available MCPs`, `## Email`, `## Calendar`, `## Task System`, `## Communication Tone`, `## Context Files`.
  - [x] Active-MCP list exact match: `grep -Fq` each of `**Linear**`, `**GitHub**`, `**Microsoft 365**`, `**Salesforce**`, `**Gong**` (positive); `grep -Fq` absence of every banned MCP token listed in Task 4 (negative).
  - [x] M365-only routing check: `## Email`, `## Calendar` sections contain `Microsoft 365`; zero mention of Gmail / Google Calendar / Google Workspace / Google Drive / personal email / Outlook.com.
  - [x] Task-system check: `## Task System` names `Linear`; zero mention of Notion / Benji / Benji.so / Benji inbox.
  - [x] Sibling-persona absence: `agents/personas/vixxo-cto.md`, `agents/personas/revivago-ceo.md`, `agents/personas/personal.md` do not exist (test with `[[ ! -e ... ]]` per file; fail the gate if any exists).
  - [x] "Why"-comment terminator check: last non-blank line matches `^<!--.*-->$` OR `^>.*$` OR `^_.*_$`, with the line containing zero banned terms (reuse the Story 2.2 `require_why_comment_terminator` helper pattern with literal `<`/`>` via `grep -Eq`, not `[[ =~ \<...\> ]]`).
  - [x] Voice-biography absence guard: zero matches (case-insensitive) for `### Voice Directives`, `NVC`, `Non-Violent Communication`, `Lift people up`, `Bias to action`.
  - [x] Self-check gate: shebang on line 1, `set -euo pipefail` present, every `task1)` through `task6)` and `all)` case branch declared, banned-term regex / required-headers / allowed-placeholders / path constants defined, `regex_self_probe` function present.
  - [x] Regression gate: `task6` invokes `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, `bash story-2-1-agent-identity-validation.sh all`, `bash story-2-2-guardrail-and-formatting-validation.sh all`. Each sub-invocation captures combined stdout/stderr and echoes it to stderr on non-zero exit (Story 2.2 Phase 4 F6 pattern). All five must return zero.

- [x] Task 6 — Regression and handoff readiness package (AC: 7, 9, 10) **[Sequential — runs all prior gates]**
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all` locally and capture the full transcript (every `PASS: <gate>` line plus the final `PASS: all`).
  - [x] Re-run Story 1.1, 1.2, 1.3, 2.1, and 2.2 harnesses in `all` mode. All five must exit `0` with `PASS: all`.
  - [x] Verify `.cursor/rules/agent-identity.mdc` still references `agents/personas/work.md` under `## Work Persona` and `## Key References` (zero-edit verification).
  - [x] Persist the handoff artifact at `_bmad-output/implementation-artifacts/tests/story-2-3-task6-handoff.md` with (a) an AC-to-file map (one row per AC with evidence pointer — story file, persona file, harness gate, or grep output), (b) the full validation command transcript (Story 2.3 harness + five regression harnesses), and (c) a forward-looking note that Story 2.4 will assert `.cursor/rules/benji-inbox-default.mdc` is NOT present (complementary scrub), Story 3.3 will populate `memory/me/identity.md` and `memory/me/preferences.md` (the persona's Context Files references), and Story 5.2 (wizard) will fill the placeholders in `agents/personas/work.md` from the interactive prompt answers.

- [x] Task 7 — Sprint tracker and story status synchronization (AC: 10) **[Independent; typically last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `2-3-create-single-generic-work-persona.status` from `backlog` to `ready-for-dev` during the story-creation Phase 1 (SM pass); then to `review` at Dev handoff per the Story 2.1 / 2.2 autonomous-swarm pattern (the on-disk single-line transition is acceptable).
  - [x] Preserve `epic-2.status` as `in-progress` (already `in-progress`; Story 2.4 remains `backlog`; epic does not yet flip to `done`).
  - [x] Update `last_updated` in `sprint-status.yaml` to today's date (`2026-04-20`) on the Phase 1 edit. Do not introduce any other key change.
  - [x] Preserve every comment, blank line, and entry ordering in `sprint-status.yaml` byte-for-byte. The file is a human-curated YAML with inline comment sections that must not be reordered or stripped.

- [x] Review Follow-ups (AI) — Phase 4 adversarial-review fixes (AC: 1, 4, 9)
  - [x] **F1 (HIGH, AC9)** — Extend `check_task4` placeholder-parity with a cross-pack loop over `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, all five `.cursor/rules/*.mdc`, and `agents/personas/work.md`. Added `PARITY_FILES` constant; every discovered `{{snake_case}}` token across the nine files must belong to the four-item allowlist. `check_task5` self-check asserts `PARITY_FILES=` is present.
  - [x] **F2 (MEDIUM, AC1)** — Replace hardcoded three-file sibling-persona loop with directory enumeration `for entry in "${PERSONAS_DIR}"/*.md` that rejects anything other than `work.md`. Added `agents/personas/.gitkeep` zero-byte sentinel assertion (Story 1.1 scaffold dependency).
  - [x] **F3 (MEDIUM, AC4)** — Added `PHONE_PATTERN_REGEX`, `GUID_PATTERN_REGEX` (Graph UPN / user-id), `TEAMS_CHATID_REGEX` constants plus three new grep guards in `check_task4`. Also factored the existing email-address pattern into `EMAIL_PATTERN_REGEX` for consistency. `check_task5` self-check asserts all four constants are defined.
  - [x] **F4 (MEDIUM, AC4)** — Moved `derek` into the POSIX-ERE boundary-guarded alternation group in `BANNED_TERMS_REGEX` so harness implementation matches the Task 4 subtask spec at story line 138.
  - [x] **F5 (LOW, doc)** — Added the matching `derek` probe pair to `regex_self_probe`; probe count is now genuinely nine (Dev Agent Record Task 5 entry remains accurate).
  - [x] **F6 (LOW, doc)** — Dev Agent Record Task 4 entry now lists explicit grep invocations and observed counts for all nine Task 4 sub-gates (previously only two were recorded).

## Senior Developer Review (AI)

**Reviewer:** Adversarial Code Reviewer (BMAD Phase 3 subagent — Claude Opus 4.7).
**Review Date:** 2026-04-20.
**Recommendation (pre-fix):** CHANGES_REQUESTED.
**Recommendation (post-fix):** APPROVE — every finding resolved on disk; harness + five regression harnesses green after fixes.

### Findings and resolution

| ID | Severity | Category | File | Description | Resolution |
| --- | --- | --- | --- | --- | --- |
| F1 | HIGH | AC_MISSING | `tests/story-2-3-work-persona-validation.sh` | Cross-pack placeholder parity scan only covered `agents/personas/work.md`, never the rule pack or root context files despite the Task 4 subtask explicitly committing to that guard. | Added `PARITY_FILES` constant (9 files) and a nested parity loop in `check_task4`; `check_task5` self-check now asserts `PARITY_FILES=` is defined. |
| F2 | MEDIUM | AC_MISSING | `tests/story-2-3-work-persona-validation.sh` | Sibling-persona absence hardcoded to three filenames; AC1 says "or any sibling persona". `.gitkeep` zero-byte assertion also missing. | Added `for entry in "${PERSONAS_DIR}"/*.md` enumeration that rejects anything other than `work.md`; added `.gitkeep` zero-byte assertion. Kept the original three-name loop as an explicit belt-and-suspenders check for the named gtd-life donors. |
| F3 | MEDIUM | AC_MISSING | `tests/story-2-3-work-persona-validation.sh` | AC4 listed phone / UPN-GUID / Teams `chatId` absence but only the email pattern was implemented. | Added `PHONE_PATTERN_REGEX`, `GUID_PATTERN_REGEX`, `TEAMS_CHATID_REGEX` constants plus three new grep guards in `check_task4`; refactored email scan to use the new `EMAIL_PATTERN_REGEX` constant. `check_task5` self-check asserts all four constants are present. |
| F4 | MEDIUM | TEST_QUALITY | `tests/story-2-3-work-persona-validation.sh` | `derek` was unbounded in `BANNED_TERMS_REGEX` while Task 4 spec required the boundary-guarded form. Harness diverged from its own spec. | Moved `derek` into the boundary-guarded alternation group so harness matches Task 4 subtask spec at story line 138. Added corresponding probe pair in `regex_self_probe`. |
| F5 | LOW | DOCUMENTATION | `2-3-create-single-generic-work-persona.md` + `tests/story-2-3-task6-handoff.md` | Dev Agent Record and handoff doc said "nine" probe tokens; harness only had eight. | Added the `derek` probe pair in the same pass as F4; probe count is now honestly nine. Documentation now accurate. |
| F6 | LOW | DOCUMENTATION | `2-3-create-single-generic-work-persona.md` | Dev Agent Record Task 4 recorded only two of nine sub-gate grep outputs. | Expanded Task 4 completion note to list explicit grep invocations and observed counts for all nine sub-gates (banned-term, placeholder inventory, email/phone/GUID/Teams chatId, voice biography, non-M365 routing, banned-MCP absence, sibling-persona absence + generic enumeration + `.gitkeep` zero-byte, identity-rule pointer, cross-pack parity). |

### Test evidence after fixes

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
```

Regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 harnesses — every harness exits 0 with `PASS: all` (Story 2.2 prints nine per-task PASS lines plus `PASS: all`).

### Non-blocking observations (carry to Story 2.4 / Story 3.3)

- AC10 (sprint-tracker lifecycle) is evidence-only — no harness gate reads `sprint-status.yaml`. Matches Story 2.1 / 2.2 precedent; no change in this story.
- `story-2-3-task6-handoff.md` is evidence-only, not harness-asserted. Matches prior-story precedent.

## Dev Notes

### Artifact availability

- Available planning/tracking artifacts:
  - `_bmad/bmm/config.yaml` (module metadata, artifact paths, BMAD v6.3.0, `user_name: Vixxo Employee`).
  - `_bmad-output/planning-artifacts/epics.md` (Epic 2 Story 2.3 statement and ACs at lines 228–239; FR3 coverage).
  - `_bmad-output/planning-artifacts/architecture.md` (placeholder-driven identity fields, rule-pack location `.cursor/rules/`, work-only template posture).
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (story lifecycle; Story 2.3 Linear ID `AIP-28`).
  - Prior story files `1-1-scaffold-directory-structure-and-root-files.md`, `1-2-write-generic-readme-license-gitignore.md`, `1-3-write-generic-agents-claude-cursorrules.md`, `2-1-port-agent-identity-rule-generic.md`, `2-2-port-guardrail-and-formatting-rules.md` (pattern, validation-harness model, scrub discipline, placeholder contract, cross-reference model).
  - Landed Story 2.1 artifact `.cursor/rules/agent-identity.mdc` — its `## Work Persona` and `## Key References` sections already point at `agents/personas/work.md`; this story's job is to author the target file the pointer resolves to.
  - Landed Story 2.2 artifacts — the four sibling `.cursor/rules/*.mdc` rules plus `story-2-2-guardrail-and-formatting-validation.sh` harness.
  - `~/Public/gtd-life/agents/personas/vixxo-cto.md`, `revivago-ceo.md`, `personal.md` — upstream source material. `vixxo-cto.md` is the skeleton donor (structure); `revivago-ceo.md` and `personal.md` are negative-assertion donors (their content is explicitly excluded).
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` (not present; rely on epics.md + sprint tracker).
  - `_bmad-output/planning-artifacts/ux-design-specification.md` (not relevant — persona file is markdown/frontmatter content only, no UI surface).
- Implementation anchors: Epic 2 Story 2.3 ACs, Story 2.1 / 2.2 harness pattern (POSIX-ERE boundary probe, extension-based scaffold allowlist, cross-file parity, "why"-comment terminator), Story 2.1 `agent-identity.mdc` `Available Tools (overview)` active-MCP list (canonical source of truth for the persona's MCP table).

### Epic 2 story partition (why 2.3 is persona-only)

- Story 2.1 (done): `.cursor/rules/agent-identity.mdc` — identity, scope, MCP overview, persona pointer. Added the `agents/personas/work.md` pointer that this story now satisfies.
- Story 2.2 (done): four sibling `.cursor/rules/*.mdc` rules — outbound messaging, memory-vault protection, Teams DM formatting, email triage thread defaults.
- Story 2.3 (this story): `agents/personas/work.md` — single generic work persona collapsing the three gtd-life personas (vixxo-cto, revivago-ceo, personal) into one Vixxo-work-only persona. FR3 coverage.
- Story 2.4: confirm `.cursor/rules/benji-inbox-default.mdc` is NOT ported. Complementary to this story's Benji scrub.

Do NOT pre-implement Story 2.4 here. This story's scrub actively fails on `benji`; Story 2.4's directory-level negative assertion is complementary, not superseded.

### Source-to-target collapse map (three personas → one)

#### `~/Public/gtd-life/agents/personas/vixxo-cto.md` (structural donor)

| Source concept | Generic target |
| -------------- | -------------- |
| `type: persona` | KEPT |
| `role: "CTO - AI"` | Replaced with `{{employee_role}}` placeholder |
| `company: vixxo` | Replaced by frontmatter `scope: work` + `tags: [persona, work, vixxo]` (company scope is a tag, not a company-specific field) |
| `tags: [persona, vixxo, work, technical-leadership]` | Replaced with `[persona, work, vixxo]` (role-agnostic; "technical-leadership" was CTO-specific) |
| `# Vixxo CTO - AI` header | Replaced with `# Work Persona` (role-agnostic) |
| `## Role` paragraph naming manager and team counts | Replaced with generic `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}` phrasing; no headcount, no legacy-systems list |
| `## Responsibilities` bullets naming ADO/Siebel/SalesLogix/ChatFPT/AI invoicing | Replaced with 3–6 generic Vixxo work bullets |
| `## Key People` section naming specific coworkers | ENTIRELY REMOVED — persona is role-only; coworker roster lives in (future) `memory/companies/vixxo/org-chart.md` outside this story's scope |
| `## Available MCPs` table (Linear / Salesforce / Gong / Microsoft 365 / Slack / GitHub) | Replaced with the five-MCP active set (Linear / GitHub / Microsoft 365 / Salesforce / Gong). Slack REMOVED per Story 2.2 AC5 banned-term set |
| `## Email: Microsoft 365 / Outlook (derek.neighbors@vixxo.com)` | Replaced with `Microsoft 365 (Outlook).` — zero email address |
| `## Calendar: Microsoft Outlook (via M365)` | Replaced with `Microsoft 365 (Outlook calendar).` |
| `## Task System: Linear (Vixxo workspace)` | Replaced with `Linear (Vixxo work task system).` |
| `## Communication Tone` paragraph + `### Voice Directives (apply when drafting as Derek)` subsection (NVC / Lift people up / Bias to action) | Replaced with 3–6 generic Vixxo lines; `### Voice Directives` subsection ENTIRELY REMOVED (Derek-specific voice biography) |
| `## Context Files` bullets pointing at `memory/companies/vixxo/overview.md` / `tools.md` / `org-chart.md` | Replaced with `.cursor/rules/agent-identity.mdc` + `memory/me/identity.md` + `memory/me/preferences.md` + `AGENTS.md` + `CLAUDE.md` + `.cursorrules` |

#### `~/Public/gtd-life/agents/personas/revivago-ceo.md` (negative donor)

| Source concept | Generic target |
| -------------- | -------------- |
| Entire file — RevivaGo business context, CEO role, Gmail/Google Calendar/Notion/Slack MCPs, VeinCraft/Daddy Bootcamps sub-brands | ENTIRELY EXCLUDED — `revivago` is banned-term set |

#### `~/Public/gtd-life/agents/personas/personal.md` (negative donor)

| Source concept | Generic target |
| -------------- | -------------- |
| Entire file — Blog, MasteryLab, Agile Weekly, side projects, family, fitness, Benji.so, Flowtopic, Obsidian | ENTIRELY EXCLUDED — `blog`, `masterylab`, `agile weekly`, `benji`, `flowtopic`, `family` all in banned-term set |

### Placeholder contract (this story)

Only four placeholder tokens appear in `agents/personas/work.md`:

- `{{employee_name}}` — frontmatter `name` value + optionally addressee in prose
- `{{employee_role}}` — frontmatter `role` value + `## Role` paragraph
- `{{employee_department}}` — frontmatter `department` value + `## Role` paragraph
- `{{employee_manager}}` — frontmatter `manager` value + `## Role` / `## Responsibilities` reporting-line reference

Do NOT introduce `{{employee_email}}`, `{{assistant_name}}`, `{{company}}`, `{{employee_title}}`, or any other new placeholder. If Story 5.2 (wizard) needs a new token later, it owns that decision; Story 2.3 is locked to the existing four-token set for cross-pack parity with `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, and all five `.cursor/rules/*.mdc` files.

### Architectural constraints

- Template is repository-first; no runtime service, no code ships in `agents/personas/`. The persona is static markdown with YAML frontmatter.
- Frontmatter keys and values must be valid YAML parseable by standard loaders; placeholder values MUST be double-quoted strings so `{{...}}` does not get interpreted as a YAML tag, alias, or flow-map key.
- No code examples, no fenced JSON, no Graph API payloads in the persona body (those live in `.cursor/rules/teams-dm-formatting.mdc` per Story 2.2). The persona is prose + table + bullet lists only.
- `agents/personas/` directory is singular by design — exactly one persona file, no sibling files beyond the `.gitkeep` sentinel (Story 1.1). Multi-persona context switching is out of scope for this template.
- macOS / Linux portability: no persona content assumes a shell, binary, or OS-specific path. All referenced paths are workspace-relative.

### Previous story learnings to carry forward

- Story 1.1: `agents/personas/` directory scaffolded with a `.gitkeep` sentinel. The Story 1.1 validation harness uses an extension-based allowlist for `.cursor/rules/*.mdc`; it does NOT have a specific check for `agents/personas/*.md` content, so adding `work.md` does not require a Story 1.1 harness edit.
- Story 1.2: banned-term scrub discipline applies to every new content artifact (including personas).
- Story 1.3: placeholder parity across root context files — this story must preserve the four-token set and add no new tokens.
- Story 2.1: POSIX-ERE boundary guards (`(^|[^A-Za-z])TOKEN($|[^A-Za-z])`) for `ASU`, `blog`, `deke`, `arete`, `eudaimonia` — this story extends the pattern to `family`.
- Story 2.1: `regex_self_probe` fail-fast guard catches a mis-parsing host grep before the banned-term scan silently fails open. Reuse and extend.
- Story 2.1: harness outputs `PASS: <gate>` / `FAIL: <gate>: <reason>`, exits 0 on pass and 1 on fail, uses `bash` + `grep` + `awk` + `sed` only (no `rg`, no Python).
- Story 2.1 / 2.2: the autonomous-swarm lifecycle collapses `backlog → ready-for-dev → review` into one on-disk transition per story (interim states transit-only, not committed). Story 2.3 may follow the same pattern; record the skipped hops in the Change Log if so.
- Story 2.2 Phase 4: `require_why_comment_terminator` must use `grep -Eq '^<!--.*-->$'` (literal `<` / `>`), not bash `[[ =~ \<...\> ]]` (GNU regex interprets `\<`/`\>` as word-boundary anchors — BSD-incompatible). Reuse the Phase-4-fixed helper.
- Story 2.2 Phase 4: sub-harness invocations in the regression gate must capture combined stdout/stderr and echo on non-zero exit (F6 pattern), so a downstream regression surfaces the offending gate name.
- Story 2.2: the four-file guardrail pack uses one pointer-only line per sibling to defer to `agent-identity.mdc` for identity; this story follows the same deferral pattern — the persona points at `.cursor/rules/agent-identity.mdc` once and does not restate its `## Scope` / `## Who the Employee Is` blocks.

### Content locks (why each section is generic-only)

- **`## Role`**: Generic so any Vixxo employee — from an IC engineer to a senior manager to a VP — can use the same persona template by filling in `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}`. Named titles (CTO, CEO, Engineering Manager, etc.) are OUT because they bake a hiring-level assumption into the persona.
- **`## Responsibilities`**: Role-keyed bullets ("Deliver the objectives of `{{employee_department}}` as `{{employee_role}}`") instead of function-specific ones ("Drive AI transformation across 14 engineering teams"). The latter is Derek-CTO-specific.
- **`## Available MCPs`**: Locked to the Story 2.1 / Epic 4 Story 4.1 active set. Placeholder MCPs (Freshdesk, Dynamics, etc.) are Story 4.2 territory and must not leak here. Slack is explicitly banned (Teams is the Vixxo chat surface per Story 2.2 AC5). Notion / Benji / Flowtopic / Google properties are personal-context MCPs from the gtd-life source pack and are banned.
- **`## Email` / `## Calendar`**: Microsoft 365 only — no email address placeholder is introduced here (the wizard fills a real employee email into `memory/me/identity.md`, not the persona).
- **`## Task System`**: Linear — matches the `.cursor/rules/agent-identity.mdc` active-MCP set and the Epic 4 Story 4.1 MCP lineup.
- **`## Communication Tone`**: 3–6 lines of generic Vixxo-culture phrasing plus a single pointer to `.cursor/rules/outbound-messaging-guardrail.mdc`. The source `### Voice Directives (apply when drafting as Derek)` subsection is a Derek-biography block and is explicitly OUT — not because NVC is wrong, but because voice biography belongs to an individual employee's own identity file (`memory/me/identity.md`, Story 3.3), not to a shared template persona.
- **`## Context Files`**: Six bullets, in the order specified. Does NOT list `memory/companies/vixxo/org-chart.md` (Vixxo-org-specific; future-epic scope), `memory/companies/revivago/**` (personal-company, banned), or `memory/companies/blog/**` (banned).

### Current Cursor/Obsidian persona-file platform notes (2026)

- Persona files at `agents/personas/*.md` are plain markdown loaded on-demand by the identity rule (`.cursor/rules/agent-identity.mdc` `## Work Persona` section points at `agents/personas/work.md`). The file is not Cursor-specific — any tool that reads markdown + YAML frontmatter (Obsidian, Claude Code, custom loaders) can consume it.
- YAML frontmatter is the standard. Cursor / Claude Code / Obsidian Dataview all parse the `---`-delimited block. Single-line `key: value` pairs plus a `tags: [a, b, c]` inline list are the portable shape.
- Placeholder values inside YAML strings — `role: "{{employee_role}}"` — MUST be quoted so the YAML parser treats the placeholder as a literal string. Unquoted `role: {{employee_role}}` is invalid YAML (the `{` starts a flow-mapping token).

### Microsoft 365 / MCP notes

- The active-MCP set for Vixxo is (Linear, GitHub, Microsoft 365, Salesforce, Gong). This list is the source-of-truth both for Story 2.1 `agent-identity.mdc` `## Available Tools (overview)` and for this story's `## Available MCPs` table. Epic 4 Story 4.1 will land the `.cursor/mcp.json` wiring; Story 4.2 will add commented placeholders for the rest. The persona does not list placeholder MCPs because an employee persona should declare only tools the employee is authorized and wired to use.
- Microsoft 365 is referenced as the email + calendar stack. "Outlook" is allowed as a parenthetical clarification (`Microsoft 365 (Outlook)`) because Outlook is the client surface for M365 mail / calendar. Story 2.2 AC4 established this phrasing convention; Story 2.3 inherits it.
- Teams is referenced only through the `.cursor/rules/outbound-messaging-guardrail.mdc` pointer — the persona does not re-declare Teams messaging rules.

### Project Structure Notes

- Target files for this story (new):
  - `agents/personas/work.md`
- Artifacts produced by this story under `_bmad-output/implementation-artifacts/tests/`:
  - `story-2-3-baseline-audit.md`
  - `story-2-3-canonical-blueprint.md`
  - `story-2-3-work-persona-validation.sh`
  - `story-2-3-task6-handoff.md`
- Directory state: `agents/personas/` exists with a `.gitkeep` sentinel (Story 1.1). This story adds `work.md` as a sibling to `.gitkeep`. Do NOT remove `.gitkeep` (leaving it allows Story 1.1's scaffold harness to continue asserting the directory exists without coupling it to persona-file content).
- Adjacent paths that must remain intact:
  - `.cursor/rules/agent-identity.mdc` (Story 2.1; zero edits — already points at `agents/personas/work.md`).
  - `.cursor/rules/outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc` (Story 2.2; zero edits).
  - `AGENTS.md`, `CLAUDE.md`, `.cursorrules` (Story 1.3; zero edits).
  - `README.md`, `LICENSE`, `.gitignore` (Story 1.2; zero edits).
- Forward-compatibility:
  - Story 2.4 will assert `.cursor/rules/benji-inbox-default.mdc` is NOT present. This story's scrub actively fails on `benji`; Story 2.4's directory-level negative assertion is complementary.
  - Story 3.3 will populate `memory/me/identity.md` and `memory/me/preferences.md` — the two memory-vault paths this persona's `## Context Files` section references.
  - Story 5.2 (wizard prompts) will replace the four placeholders in `agents/personas/work.md` with real values from the interactive prompt answers. Story 2.3 is the wizard's target file for persona generation.
  - Epic 4 Story 4.1 will wire the five active MCPs in `.cursor/mcp.json`; the persona's `## Available MCPs` table is the human-readable companion to that machine-readable config.

### Testing Notes

- Suggested manual commands:
  - `rg -n "\\{\\{employee_(name|role|department|manager)\\}\\}" agents/personas/work.md` for placeholder coverage.
  - `rg -n -i "derek|deke|neighbors|chiron|revivago|agile weekly|masterylab|bodybuilding\\.com|gangplank|gtd-life|gmail|google calendar|google workspace|personal email|slack|benji|notion|flowtopic|veincraft|daddy bootcamps|after the stork|peptide|family|laurie|bobby hunnicutt|brandon franz|eric burt|gino flores|viswa vadlamani|jignesh patel|jim reavey" agents/personas/work.md` for scrub compliance (expect zero matches).
  - `rg -n "scope:\\s*work" agents/personas/work.md` for AC2 `scope: work` gate.
  - `rg -n "\\*\\*Linear\\*\\*|\\*\\*GitHub\\*\\*|\\*\\*Microsoft 365\\*\\*|\\*\\*Salesforce\\*\\*|\\*\\*Gong\\*\\*" agents/personas/work.md` for AC3 active-MCP gate.
  - `rg -n "Microsoft 365" agents/personas/work.md` for AC5 routing gate.
  - `bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all`
- Regression (each must exit 0 with `PASS: all`):
  - `bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all`
- Keep the Story 2.3 harness self-contained (no network, no external tools beyond `bash`, `grep`, `awk`, `sed`; `rg` is explicitly optional — every required scan has a portable `grep -E` / `grep -Fq` equivalent).

### Parallelization guidance

- Task 1 (baseline audit) is sequential — no dependencies, but produces the lock inputs for Task 2.
- Task 2 (canonical blueprint) is sequential — depends on Task 1.
- Task 3 (author `agents/personas/work.md`) and Task 5 (scaffold validation harness) are pairwise parallelizable once Task 2 is locked. Task 3 is the single-file authoring task (no internal parallelization possible — same file); Task 5 scaffolds the harness against the Task 2 blueprint's locked headers, required tokens, and forbidden-content lists, then wires the final gates to the real Task 3 artifact at the end.
- Task 4 (cross-file scrub) is sequential — depends on Task 3's artifact.
- Task 6 (regression + handoff) is sequential — depends on all prior (runs the Task 5 harness plus all five predecessor harnesses).
- Task 7 (sprint tracker) is independent of Tasks 1–6 but typically runs last; the Phase 1 `backlog → ready-for-dev` flip is the SM-pass edit made when this story file is authored, and the Phase 2 `ready-for-dev → review` flip is the Dev-handoff edit.

**Swarm parallelization summary:**

- **Sequential prerequisites:** Task 1 → Task 2 (both must complete before Tasks 3–5 begin).
- **Parallel pair:** Task 3 (authoring) || Task 5 (harness scaffold) can run concurrently in two subagents once Task 2 is locked.
- **Sequential post-authoring:** Task 4 (scrub/parity) after Task 3 artifact lands; Task 6 (regression + handoff) after Tasks 3, 4, and 5 land.
- **Last:** Task 7 (sprint tracker) can run any time after Phase 1 SM pass (done at story creation) or at Phase 2 Dev handoff; does not share any file with Tasks 1–6.
- **Shared-file contention:** Tasks 1, 2, 3, 5, 6, 7 each write to distinct files under `_bmad-output/implementation-artifacts/tests/` (or `agents/personas/work.md` for Task 3, or `sprint-status.yaml` for Task 7). Only this story file itself (Dev Agent Record + File List + checkboxes) is written by every task — serialize story-file edits per task or batch them at the end of each task's pass.

### References

- `_bmad/bmm/config.yaml` (BMAD module metadata, artifact path variables, version context).
- `_bmad-output/planning-artifacts/epics.md` lines 228–239 (Epic 2 Story 2.3 statement and acceptance criteria), lines 52–57 (FR3 coverage), lines 72–77 (Epic 2 scope).
- `_bmad-output/planning-artifacts/architecture.md` (placeholder-driven identity fields, rule-pack location, work-only posture).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` lines 89–92 (story key `2-3-create-single-generic-work-persona`, Linear `AIP-28`, lifecycle states).
- `_bmad-output/implementation-artifacts/1-1-scaffold-directory-structure-and-root-files.md` (extension-based `.cursor/rules/*.mdc` allowlist; `agents/personas/.gitkeep` sentinel).
- `_bmad-output/implementation-artifacts/1-2-write-generic-readme-license-gitignore.md` (scrub discipline pattern).
- `_bmad-output/implementation-artifacts/1-3-write-generic-agents-claude-cursorrules.md` (placeholder usage, validation harness model, status lifecycle).
- `_bmad-output/implementation-artifacts/2-1-port-agent-identity-rule-generic.md` (POSIX-ERE banned-term regex, `regex_self_probe`, `## Work Persona` + `## Key References` pointers that Story 2.3 satisfies).
- `_bmad-output/implementation-artifacts/2-2-port-guardrail-and-formatting-rules.md` (consolidated banned-term set, `require_why_comment_terminator` Phase-4 form, F6 sub-harness-capture pattern, placeholder parity across rule pack).
- `.cursor/rules/agent-identity.mdc` (Story 2.1 output; points at `agents/personas/work.md` — this story authors the target file).
- `_bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh` (harness pattern to inherit — banned-term regex, self-check, regression invocation).
- `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (harness pattern — F1–F6 Phase 4 improvements: fenced-block absence guards, `grep -Eq` terminator, F6 sub-harness capture).
- `~/Public/gtd-life/agents/personas/vixxo-cto.md` (structural donor — reference only, never copy verbatim; coworker names explicitly banned).
- `~/Public/gtd-life/agents/personas/revivago-ceo.md` (negative donor — entire file content is banned-term territory; zero port).
- `~/Public/gtd-life/agents/personas/personal.md` (negative donor — entire file content is banned-term territory; zero port).
- Git log (`git log --oneline -n 15`) for recent Epic 2 commit style: `feat(epic-2): <change> (Story <key>)`. Story 2.3 commits should follow the same pattern (`feat(epic-2): create single generic work persona (Story 2-3-create-single-generic-work-persona)`).
- [Cursor Rules Documentation (v6.x)](https://cursor.com/docs/rules) (frontmatter keys; persona-file loading via `alwaysApply: true` identity rule pointer).
- [Obsidian YAML frontmatter](https://help.obsidian.md/Editing+and+formatting/Properties) (frontmatter parsing conventions for persona files consumed by the memory-vault viewer).

## Change Log

- 2026-04-20 (Phase 1, Bob — SM): Story file authored from Epic 2 Story 2.3 spec. `sprint-status.yaml` flipped `2-3-create-single-generic-work-persona.status` `backlog → ready-for-dev` and `last_updated` updated to `2026-04-20`. `epic-2.status` remains `in-progress` (Stories 2.1 and 2.2 already `done`; Story 2.4 remains `backlog`; epic does not yet flip to `done`). Ready for Phase 2 Dev swarm pickup.
- 2026-04-20 (Phase 2, Amelia — Dev): All seven tasks implemented and validated. Authored `agents/personas/work.md` per Task 2 blueprint (single generic Vixxo work persona with frontmatter, nine sections, five-MCP table, M365-only routing, outbound-rule pointer, six Context Files bullets, sanitized "why" comment terminator). Persisted baseline audit, canonical blueprint, and Task 6 handoff artifacts under `_bmad-output/implementation-artifacts/tests/`. Wired `story-2-3-work-persona-validation.sh` with six gates (`task1`–`task6` + `all`), reusing the Story 2.2 POSIX-ERE boundary-guard pattern and extending the alternation with `family` plus a nine-token `regex_self_probe`. Final harness run: `PASS: all`. Regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 harnesses: `PASS: all` on every one. `sprint-status.yaml` `2-3-create-single-generic-work-persona.status` flipped `ready-for-dev → review`; `epic-2.status` preserved as `in-progress`; `last_updated` preserved at `2026-04-20`. Story ready for code review.
- 2026-04-20 (Phase 4, Amelia — Review follow-up): Six adversarial-review findings resolved in one pass. F1 (HIGH) — added cross-pack placeholder parity loop over `AGENTS.md` / `CLAUDE.md` / `.cursorrules` / five `.cursor/rules/*.mdc` / `agents/personas/work.md`. F2 (MEDIUM) — added generic `agents/personas/*.md` sibling-enumeration guard and `agents/personas/.gitkeep` zero-byte assertion. F3 (MEDIUM) — added `PHONE_PATTERN_REGEX`, `GUID_PATTERN_REGEX`, `TEAMS_CHATID_REGEX` constants plus scans; refactored email scan to use the new `EMAIL_PATTERN_REGEX` constant. F4 (MEDIUM) — moved `derek` into the POSIX-ERE boundary-guarded alternation group to match Task 4 spec. F5 (LOW) — added `derek` probe pair; `regex_self_probe` now genuinely exercises nine tokens. F6 (LOW) — Dev Agent Record Task 4 entry now enumerates explicit grep evidence for all nine sub-gates. `check_task5` self-check extended to assert every new constant is defined. Final harness run after fixes: Story 2.3 `PASS: all`; full regression (1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3) all green.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (Cursor, BMAD autonomous Dev swarm — agent Amelia).

### Debug Log References

- Initial harness run exited 1 at `task3` Context Files bullet check because `grep -Fxq "${bullet}"` interpreted the leading `-` of each bullet as an option flag. Fix: switched to `grep -Fxq -- "${bullet}"`. Re-run: `PASS: all`.
- No other failures. No regression. No halt conditions.

### Completion Notes List

- **Task 1** — Baseline audit artifact at `_bmad-output/implementation-artifacts/tests/story-2-3-baseline-audit.md` captures all three upstream personas (`vixxo-cto.md`, `revivago-ceo.md`, `personal.md`), the consolidated banned-term set (Story 2.1 + 2.2 carryover + Story 2.3 persona-specific additions), the active-MCP lock (Linear / GitHub / Microsoft 365 / Salesforce / Gong), and the source-to-target collapse map. Target path `agents/personas/work.md` confirmed to not exist pre-Task-3; `agents/personas/.gitkeep` confirmed present (Story 1.1 scaffold).
- **Task 2** — Canonical blueprint at `_bmad-output/implementation-artifacts/tests/story-2-3-canonical-blueprint.md` locks the nine-header layout, the seven-key frontmatter shape (AC2), the five-row MCP table (AC3), the three M365 routing one-liners (AC5), the 3–6-line Communication Tone stanza with the outbound-rule pointer and no `### Voice Directives` subsection (AC6), the six-bullet Context Files list (AC7), the HTML "why" comment terminator (AC8), and the four-token placeholder contract.
- **Task 3** — `agents/personas/work.md` authored per Task 2 blueprint. Frontmatter uses `scope: work` (replacing the gtd-life `company:` key) with double-quoted placeholder values. `# Work Persona` header (no `# Vixxo Work Persona` variant). `## Role` paragraph is placeholder-only with a single pointer deferring `Scope` and `Who the Employee Is` to `.cursor/rules/agent-identity.mdc`. Four generic Responsibilities bullets (within the 3–6 lock). Five-MCP table with one bold-wrapped proper name per row. Routing one-liners match the blueprint verbatim. Communication Tone references `.cursor/rules/outbound-messaging-guardrail.mdc` exactly once and carries no voice-biography content. Six Context Files bullets in locked order. Sanitized one-line "why" comment terminator after the final section, separated by exactly one blank line.
- **Task 4** — Cross-file scrub passes every gate. Explicit grep evidence (all counts verified at harness run):
  - `grep -n -i -E "${BANNED_TERMS_REGEX}" agents/personas/work.md | wc -l` → `0`
  - `grep -oE '\{\{[a-z_]+\}\}' agents/personas/work.md | sort -u` → exactly four tokens (`{{employee_department}}`, `{{employee_manager}}`, `{{employee_name}}`, `{{employee_role}}`)
  - `grep -E "${EMAIL_PATTERN_REGEX}" agents/personas/work.md | wc -l` → `0`
  - `grep -E "${PHONE_PATTERN_REGEX}" agents/personas/work.md | wc -l` → `0`
  - `grep -E "${GUID_PATTERN_REGEX}" agents/personas/work.md | wc -l` → `0`
  - `grep -E "${TEAMS_CHATID_REGEX}" agents/personas/work.md | wc -l` → `0`
  - `grep -iE "${VOICE_BIOGRAPHY_REGEX}" agents/personas/work.md | wc -l` → `0`
  - `grep -iE "${NON_M365_ROUTING_REGEX}" agents/personas/work.md | wc -l` → `0`
  - `grep -Fc '**Slack**' agents/personas/work.md` (and each other banned MCP token) → `0`
  - `[[ -e agents/personas/vixxo-cto.md ]] || [[ -e agents/personas/revivago-ceo.md ]] || [[ -e agents/personas/personal.md ]]` → all three absent
  - `for f in agents/personas/*.md; do echo "$f"; done` → single entry `agents/personas/work.md` only (generic sibling-absence enumeration per review fix F2)
  - `[[ ! -s agents/personas/.gitkeep ]]` → true (zero-byte Story 1.1 sentinel preserved per review fix F2)
  - `grep -Fq 'agents/personas/work.md' .cursor/rules/agent-identity.mdc` → exit 0 (identity-rule pointer intact)
  - Cross-pack placeholder parity over AGENTS.md / CLAUDE.md / .cursorrules / five `.cursor/rules/*.mdc` + `agents/personas/work.md` → every discovered token belongs to the four-item allowlist (closes review fix F1).
- **Task 5** — Harness at `_bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh` (executable). Reuses Story 2.2 POSIX-ERE boundary-guard regex extended with `family` and (post-review) with boundary-guarded `derek`. `regex_self_probe` covers nine boundary-guarded tokens (`derek`, `ASU`, `blog`, `deke`, `arete`, `eudaimonia`, `slack`, `benji`, `family` — each with a positive and a negative synthetic case). Gates `task1`–`task6` plus `all`. Regression gate captures combined stdout/stderr on non-zero exit per Story 2.2 Phase 4 F6 pattern. Review-follow-up additions: `EMAIL_PATTERN_REGEX`, `PHONE_PATTERN_REGEX`, `GUID_PATTERN_REGEX`, `TEAMS_CHATID_REGEX`, `PARITY_FILES` constants (each asserted by the self-check gate).
- **Task 6** — `_bmad-output/implementation-artifacts/tests/story-2-3-task6-handoff.md` persists the AC-to-file evidence map and the full validation transcript. `bash story-2-3-work-persona-validation.sh all` → `PASS: all`. Regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 harnesses → each exits 0 with its `PASS: all`.
- **Task 7** — `sprint-status.yaml` `2-3-create-single-generic-work-persona.status` flipped `ready-for-dev → review`. `epic-2.status` preserved as `in-progress`. `last_updated` preserved at `"2026-04-20"` (Phase 1 had already set it). All comments, blank lines, and entry ordering preserved byte-for-byte.

### File List

- `agents/personas/work.md` (new — Task 3)
- `_bmad-output/implementation-artifacts/tests/story-2-3-baseline-audit.md` (new — Task 1)
- `_bmad-output/implementation-artifacts/tests/story-2-3-canonical-blueprint.md` (new — Task 2)
- `_bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh` (new, executable — Task 5)
- `_bmad-output/implementation-artifacts/tests/story-2-3-task6-handoff.md` (new — Task 6)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — Task 7: `2-3-create-single-generic-work-persona.status` → `review`)
- `_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md` (modified — task checkboxes, Dev Agent Record, Change Log)
