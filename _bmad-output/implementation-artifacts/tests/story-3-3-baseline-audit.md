# Story 3.3 Baseline Audit

Captured during Task 1 (Phase 2, Dev agent Amelia). This audit records the upstream `~/Public/gtd-life/memory/me/` source contents that Story 3.3 references only as shape reference — the Derek-specific content is DISCARDED, and the two in-scope target files (`memory/me/identity.md`, `memory/me/preferences.md`) are REBUILT FROM SCAFFOLD with `{{employee_*}}` identity placeholders. This audit enumerates every entry under `~/Public/gtd-life/memory/me/`, records per-file frontmatter / heading shape, runs the boundary-guarded 17-token banned-term regex and the Derek-specific fixed-string scan against each source, explicitly flags the four sibling files and one subdirectory that are EXCLUDED from the port, documents the content classes that MUST be scrubbed versus the thin slice that IS in scope for preferences.md rebuild, and persists the source → target mapping with REBUILD vs EXCLUDED classification. Evidence here drives Task 2's canonical blueprint and Task 4's cross-file scrub probes. Source content lives outside this repository at `~/Public/gtd-life/memory/me/` and is read-only reference material.

Scope lock: Story 3.3 targets exactly two target files at `memory/me/` (`identity.md`, `preferences.md`). Of the six source files and one subdirectory at `~/Public/gtd-life/memory/me/`, only the two with matching filenames are in scope — and even those are REBUILT from scaffold, not ported verbatim. The other four siblings (`family.md`, `food-guide-queen-creek.md`, `ventures.md`, `properties.md`) and one subdirectory (`networking/`) are EXCLUDED — personal-life / Derek-business content with no Vixxo work-template analogue. This audit enumerates those excluded entries explicitly for traceability and to back the AC14 additive-scope lock.

**Port method: REBUILD FROM SCAFFOLD (distinct from Story 3.2).** Story 3.2 ported six of seven `.obsidian/` JSON files verbatim and repaired one (`templates.json`). Story 3.3's sources are fully populated Derek documents with zero reusable content; the ported files are TEMPLATES with `{{employee_*}}` identity placeholders that the Epic 5 Story 5.2 wizard rewrites. The gtd-life sources are read as a catalog of "what shape an identity / preferences file can have" and as a catalog of "what must NOT appear in the port" — not as a starting point to edit.

## gtd-life me/ source inventory

Enumerated on 2026-04-20 from `~/Public/gtd-life/memory/me/` (host: macOS darwin 25.4.0). All six source files are plain UTF-8 Markdown. One subdirectory (`networking/`) contains one contact-note file. No `.DS_Store`, no `*.bak`, no `*.log`, no `*.tmp` files present in the source directory or its subdirectory.

| # | Source path | Bytes | Lines | In scope? | Port mode |
|---|-------------|-------|-------|-----------|-----------|
| 1 | `~/Public/gtd-life/memory/me/identity.md` | 3309 | 63 | **YES** — shape reference only | **REBUILD FROM SCAFFOLD** (discard all Derek content) |
| 2 | `~/Public/gtd-life/memory/me/preferences.md` | 3458 | 71 | **YES** — shape reference only | **REBUILD FROM SCAFFOLD** (discard all Derek content; retain Vixxo-generic tooling slice) |
| 3 | `~/Public/gtd-life/memory/me/family.md` | 948 | 44 | **NO — EXCLUDED** | Personal-life (spouse, children, grandchildren, siblings, parents) — no work-template analogue |
| 4 | `~/Public/gtd-life/memory/me/food-guide-queen-creek.md` | 12237 | 229 | **NO — EXCLUDED** | PII-locale food preferences — no work-template analogue |
| 5 | `~/Public/gtd-life/memory/me/ventures.md` | 2310 | 60 | **NO — EXCLUDED** | Derek side-businesses (MasteryLab, Flowtopic, RevivaGo, Agile Weekly, ManaRank, etc.) — no work-template analogue |
| 6 | `~/Public/gtd-life/memory/me/properties.md` | 609 | 31 | **NO — EXCLUDED** | Derek real-estate holdings — no work-template analogue |
| 7 | `~/Public/gtd-life/memory/me/networking/` (subdir) | — | — | **NO — EXCLUDED** | Personal-contact notes (one file: `inspirecxo-ai-advisory-2026-03-27.md`, 8199 bytes); Story 3.3 ships a flat two-file `memory/me/` directory per AC1 |

**Four excluded siblings + one excluded subdirectory = no subdirectory and four files are created in the Story 3.3 port.** Only `identity.md` and `preferences.md` are in scope for Story 3.3; the other four files and one subdirectory are out of scope.

**Zero `{{…}}` placeholder tokens across all six source files** — confirmed via `grep -cE '\{\{[^}]+\}\}'` returning `0` for every file. The gtd-life sources are fully-populated concrete Derek content, not templates. Story 3.3's port method inverts this: the ported files are TEMPLATES with five `{{employee_*}}` identity placeholders that the Epic 5 Story 5.2 wizard rewrites with user answers (name, email, role, department, manager).

## Per-file frontmatter + heading map

### 1. `~/Public/gtd-life/memory/me/identity.md` (3309 bytes; 63 lines) — IN SCOPE (rebuild)

- Frontmatter keys (in source order, 4 keys): `type`, `created`, `updated`, `tags`
- Frontmatter values: `type: identity`, `created: 2026-03-20`, `updated: 2026-03-23`, `tags: [identity, personal]`
- **Scope declaration:** `tags` includes banned token `personal` — this exact string is rejected by Story 3.3's AC7 17-token lock and must be replaced with `work` in the rebuild.
- **Missing keys vs Story 3.3 spec:** source has no `scope`, `name`, `role`, `department`, `manager`, or `email` frontmatter keys. Story 3.3 AC2 requires all six (+ `type`, `created`, `updated`, `tags` = ten keys total in canonical order). Derek's identity fields live in the body as H2 prose, not frontmatter.
- H1: `# Identity`
- H2 sections (in source order, 8 total): `## Name`, `## Location`, `## Current Roles`, `## Career History`, `## Philosophy`, `## Interests`, `## Devices and Environment`, `## Professional Identity`
- **H2 sections retained for Story 3.3 target (renamed / reshaped):** `## Name` only; the other seven are either discarded (Location, Current Roles, Career History, Philosophy, Interests, Devices and Environment, Professional Identity) or replaced with Vixxo-work-template equivalents. Story 3.3 AC3 target H2 list: `## Name`, `## Role`, `## Department`, `## Manager`, `## Email`, `## Work Scope`, `## Key References` — 7 H2s, all different in intent from Derek's bio sections except `## Name`.
- **Body content:** fully populated Derek biography — name (Derek Neighbors), location (Queen Creek, Arizona), current roles (CTO Vixxo, CEO RevivaGo, writer at derekneighbors.com), career history (Bodybuilding.com, Integrum, Gangplank, ASU, angel investor, serial entrepreneur, agile practitioner), philosophy (arete, eudaimonia, Greatness Flywheel, leadership), interests (running, powerlifting, sports, off-road racing, D&D, MTG, music, Playrix), devices (Mac, Omarchy Linux, iPad, Cursor IDE, Claude Code), professional identity prose. **Every sentence is Derek-specific. Zero reusable prose. REBUILD FROM SCAFFOLD — do not attempt verbatim port.**
- **Placeholder tokens:** zero `{{…}}` occurrences. The source is concrete Derek content, not a template.

### 2. `~/Public/gtd-life/memory/me/preferences.md` (3458 bytes; 71 lines) — IN SCOPE (rebuild with thin Vixxo-generic slice)

- Frontmatter keys (in source order, 4 keys): `type`, `created`, `updated`, `tags`
- Frontmatter values: `type: preferences`, `created: 2026-03-20`, `updated: 2026-04-18`, `tags: [preferences, personal]`
- **Scope declaration:** `tags` includes banned token `personal` — rejected by AC7; must be replaced with `work` in the rebuild.
- **Missing keys vs Story 3.3 spec:** source has no `scope` key. Story 3.3 AC4 requires `scope: work` as the second key (5 keys total in canonical order: `type`, `scope`, `created`, `updated`, `tags`).
- H1: `# Preferences`
- H2 sections (in source order, 8 H2 + 1 H3): `## Food (Queen Creek / San Tan)`, `## Email Conventions`, `## Communication Style`, `## AI Agent`, `## Tool Preferences` (with nested H3 `### Context Routing Guardrails (Agent)`), `## Inbox Conventions`, `## Workflow Habits`, `## Device Usage`
- **H2 sections retained for Story 3.3 target (renamed / reshaped):** none ported verbatim. Story 3.3 AC5 target H2 list: `## Communication Style`, `## Tooling`, `## Meeting Cadence`, `## Working Hours`, `## AI Assistant` (5 H2s). Overlap with source:
  - `## Communication Style` — title same, content REBUILT (source lists Derek's em-dash ban + AI-slop phrases + "meme lord" self-description; Story 3.3 body defers to `AGENTS.md` and `.cursor/rules/agent-identity.mdc` for tone — single source of truth, does not restate).
  - `## Tooling` — source `## Tool Preferences` + `### Context Routing Guardrails` together; content REBUILT. Source lists Cursor, Claude Code, Obsidian, Git, Benji.so, Flowtopic plus gmail / google-calendar MCPs as personal-context routing. Story 3.3 target lists only the five active Vixxo MCPs from Story 2.3 persona (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`); scrubs Benji, Flowtopic, gmail, google-calendar, Obsidian, Cursor, Claude Code references.
  - `## AI Assistant` — source `## AI Agent` near-match title (renamed in target). Content REBUILT. Source names Chiron (Derek's AI), Deke (signing nickname), KY-ron pronunciation. Story 3.3 target defers to `agents/personas/work.md` for persona and `.cursor/rules/agent-identity.mdc` for identity — single source of truth; does not restate.
  - `## Meeting Cadence`, `## Working Hours` — NOT in source. New Story 3.3 additions for work-template coverage.
  - `## Food (Queen Creek / San Tan)`, `## Email Conventions`, `## Inbox Conventions`, `## Workflow Habits`, `## Device Usage` — EXCLUDED from target (personal-life or Derek-specific content).
- **Placeholder tokens:** zero `{{…}}` occurrences. Source is concrete Derek content.
- **Thin in-scope slice for rebuild:** the five Vixxo active MCPs (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`) are the only concrete tool references ported through — and they come not from this source file but from Story 2.3's `agents/personas/work.md` and `.cursor/rules/agent-identity.mdc`, which are the canonical source of truth for Vixxo tooling in this template.

### 3. `~/Public/gtd-life/memory/me/family.md` (948 bytes; 44 lines) — EXCLUDED

- Frontmatter keys (4): `type`, `created`, `updated`, `tags` with `type: family` and `tags: [family, personal]`.
- H1 / H2 sections: `# Family`, `## Spouse`, `## Children`, `## Grandchildren`, `## Siblings`, `## Parents`.
- Content: 18 real first / last names (spouse Laurie Neighbors, children Brittany / Ashley / Noah, grandchildren Thorin / Stevie / Matthew / Scottie, siblings Lisa / Robin / Melissa "Missy" / Melinda "Mindy", parents Steve / Charlene "Kay").
- **Rationale for exclusion:** personal-life content. Work template ships no family-relationship tracking. Even the FILE NAME (`family.md`) contains a banned token (`family`) from the 17-token lock.

### 4. `~/Public/gtd-life/memory/me/food-guide-queen-creek.md` (12237 bytes; 229 lines) — EXCLUDED

- Frontmatter keys: `type`, `created`, `updated`, `tags`, `area` with `type: food-guide` and `tags: [food, queen-creek, arizona, personal, preferences]` and `area: "Queen Creek / San Tan Valley, AZ (~85142)"`.
- H1 `# Food guide (Queen Creek home base)` plus ~25 H2 / H3 sections covering distance tiers, solo-vs-spouse anchor picks, Mexican / BBQ / burgers / Asian / breakfast lists, no-fly list, etc.
- **Rationale for exclusion:** personal-life content. PII-locale reveals (`Queen Creek`, `San Tan Valley`, `85142` zip code). Spouse-preference content. Work template ships no food / location preference tracking.

### 5. `~/Public/gtd-life/memory/me/ventures.md` (2310 bytes; 60 lines) — EXCLUDED

- Frontmatter keys (4): `type`, `created`, `updated`, `tags` with `type: ventures` and `tags: [ventures, projects, personal, side-projects]`.
- H1 / H2 / H3 sections: `# Ventures and Side Projects`, `## Active Ventures`, `### MasteryLab`, `### Agile Weekly`, `### Derex Tools`, `### Flowtopic`, `### Auction Scout`, `## Hobby and Experimental Projects`, `### ManaRank`, `### groove.rb`, `### Township Cards`, `### Fight Simulator`.
- Content: Derek's personal side-businesses and hobby projects. Mentions Vixxo and RevivaGo in the introductory paragraph.
- **Rationale for exclusion:** Derek-specific side-venture tracking. Every named venture is Derek-owned. Work template ships no side-business tracking.

### 6. `~/Public/gtd-life/memory/me/properties.md` (609 bytes; 31 lines) — EXCLUDED

- Frontmatter keys (4): `type`, `created`, `updated`, `tags` with `type: properties` and `tags: [properties, real-estate, personal]`.
- H1 / H2 sections: `# Properties`, `## Primary Residence`, `## Long-Term Rental`, `## Short-Term Rental`, `## Beach House (For Sale)`.
- Content: Derek's real-estate holdings (Queen Creek AZ primary, Phoenix AZ "Turtle House" rental, Clarksville AZ "Apple House" short-term, Encinitas CA beach house for sale).
- **Rationale for exclusion:** Derek-specific real-estate tracking. Work template ships no real-estate tracking.

### 7. `~/Public/gtd-life/memory/me/networking/` (subdirectory; 1 file) — EXCLUDED

- Single file: `inspirecxo-ai-advisory-2026-03-27.md` (8199 bytes).
- Content: contact-note for a specific personal-networking event.
- **Rationale for exclusion:** personal-networking content. Story 3.3 AC1 ships a FLAT two-file `memory/me/` directory with NO subdirectories. Work template ships no networking contact-note tracking (if added later, the Story 3.1 `memory/people/` template tree is the natural home — not a personal-me subdirectory).

## Banned-term scan of source files

Regex: `(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])`, case-insensitive via `grep -iE` (the Story 3.1 Phase-4 F4-locked 17-token set; Story 3.3 inherits verbatim, adds zero tokens, removes zero tokens). Executed on 2026-04-20.

| # | Source file | 17-token regex line hits (`grep -cE`) | Distinct tokens observed |
|---|-------------|----------------------------------------|--------------------------|
| 1 | `identity.md` | 4 | `Derek`, `RevivaGo`, `blog`, `home`, `personal` |
| 2 | `preferences.md` | 9 | `Derek`, `RevivaGo`, `Benji`, `Flowtopic`, `blog`, `home`, `personal` |
| 3 | `family.md` | 2 | `Neighbors`, `family`, `personal` |
| 4 | `food-guide-queen-creek.md` | 36 | `Derek`, `Laurie`, `wife`, `personal` (plus many locale / food-term incidentals) |
| 5 | `ventures.md` | 3 | `Derek`, `personal` |
| 6 | `properties.md` | 1 | `personal` |

**Total:** 55 regex hits across the six source files. Every in-scope source file (identity.md + preferences.md) has at least four regex hits each and contains `personal` in the tags array (the exact banned token added in Story 3.1 Phase-4 F4). The banned-token density in the sources confirms that verbatim-port-with-scrub would require rewriting nearly every sentence — REBUILD FROM SCAFFOLD is the correct port method.

## Derek-specific fixed-string scan of source files

Additional fixed-string scans via `grep -Fi` (defence-in-depth beyond the 17-token regex). These tokens are Derek-specific names, brands, locations, and tools that appear verbatim in the sources and would silently port through on a careless copy. They are NOT part of the 17-token regex because some (`Integrum`, `Laurie`) could legitimately appear in non-Derek contexts elsewhere — narrow-scope fixed-string enforcement is appropriate only for `memory/me/*.md` Story 3.3 authored files.

| Fixed string | identity.md | preferences.md | family.md | ventures.md | properties.md |
|--------------|-------------|----------------|-----------|-------------|---------------|
| `Chiron` | 0 | 4 | 0 | 0 | 0 |
| `MasteryLab` | 1 | 0 | 0 | 1 | 0 |
| `Agile Weekly` | 1 | 0 | 0 | 1 | 0 |
| `Queen Creek` | 2 | 1 | 0 | 0 | 1 |
| `Gangplank` | 1 | 0 | 0 | 0 | 0 |
| `Bodybuilding.com` | 1 | 0 | 0 | 0 | 0 |
| `Integrum` | 1 | 0 | 0 | 0 | 0 |
| `Omarchy` | 1 | 1 | 0 | 0 | 0 |
| `derekneighbors.com` | 1 | 0 | 0 | 0 | 0 |
| `Playrix` | 1 | 0 | 0 | 1 | 0 |
| `Laurie` | 0 | 1 | 1 | 0 | 0 |
| `Deke` | 0 | 1 | 0 | 0 | 0 |
| `Obsidian` | 0 | 1 | 0 | 0 | 0 |
| `Cursor` | 1 | 1 | 0 | 0 | 0 |
| `Claude Code` | 1 | 1 | 0 | 0 | 0 |
| `gmail` | 0 | 1 | 0 | 0 | 0 |
| `google-calendar` | 0 | 1 | 0 | 0 | 0 |
| `Vixxo` | 3 | 3 | 0 | 1 | 0 |

**Note on `Vixxo`:** retained — `Vixxo` is the employer name and a legitimate token in the work-template context. It is allowed in Story 3.3 output files (e.g. "Vixxo business hours" prose is acceptable). It is NOT part of the Derek-specific scrub list.

**Note on `Cursor` and `Claude Code`:** these are tool brand names that appear in Derek's device list. Story 3.3 target `preferences.md` does NOT list them (the tooling section lists only the five Vixxo MCPs per Story 2.3 persona); the rebuild scrubs these personal-tooling references.

**Note on `Obsidian`:** the Story 3.2 `memory/.obsidian/` config lives in the same vault and is referenced from `.cursor/rules/agent-identity.mdc` / `AGENTS.md`, but Story 3.3 target `preferences.md` does NOT mention `Obsidian` directly (AC5 explicit prohibition).

**Story 3.3 fixed-string scrub list (rebuild output MUST contain ZERO of these):** `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`, `Obsidian`, `Cursor`, `Claude Code`, `gmail`, `google-calendar`. The story spec's Task 4 harness constants enumerate the 12-token subset `DEREK_FIXED_STRINGS=( Chiron MasteryLab "Agile Weekly" "Queen Creek" Gangplank "Bodybuilding.com" Integrum Omarchy derekneighbors.com Playrix Laurie Deke )` — this is the AUTHORED fixed-string scrub set for the harness. `Obsidian`, `Cursor`, `Claude Code`, `gmail`, `google-calendar` are additionally caught by AC5's explicit prohibition of those five tokens in `preferences.md` body.

**Real human name scan.** `grep -F` against `Derek | Laurie | Deke | Brittany | Ashley | Noah | Thorin | Stevie | Matthew | Scottie | Lisa | Robin | Melissa | Melinda | Missy | Mindy | Steve | Charlene | Kay` across all five markdown files: **45 distinct hits** total, 10 of them on `Derek` alone across the five files. Story 3.3 target files contain ZERO real human names (only `{{employee_name}}` placeholder and `{{employee_manager}}` placeholder) — the rebuild inverts the naming density.

**Path-leak scan.** `grep -cF '/Users/'` and `grep -cF 'gtd-life'` across all five markdown files: **0 hits** each. The gtd-life sources do not embed absolute filesystem paths. This is consistent with the Story 3.2 baseline audit's finding that the vault content itself is path-leak-free; path leaks in `workspace.json` (Story 3.2 excluded file) are user-local session cache, not authored content.

## Out-of-scope files and subdirectories

The following source entries are explicitly OUT OF SCOPE for Story 3.3. The port MUST NOT create matching files or directories in the `assistants-template` repo as part of this story (AC14):

| Source path | Reason OUT OF SCOPE for Story 3.3 |
|-------------|-----------------------------------|
| `~/Public/gtd-life/memory/me/family.md` | Personal-life (spouse, children, grandchildren, siblings, parents). 2 banned-term hits. File name itself is a banned token (`family`). Work template ships no family tracking. |
| `~/Public/gtd-life/memory/me/food-guide-queen-creek.md` | PII-locale (Queen Creek, San Tan Valley, 85142 zip), spouse-preference content. 36 banned-term hits — the highest density of any source file. Work template ships no food / location preferences. |
| `~/Public/gtd-life/memory/me/ventures.md` | Derek side-businesses (MasteryLab, Flowtopic, Derex Tools, Auction Scout, ManaRank, groove.rb, Township Cards, Fight Simulator). Every venture is Derek-owned. Work template ships no side-business tracking. |
| `~/Public/gtd-life/memory/me/properties.md` | Derek real-estate holdings (Queen Creek primary, Phoenix "Turtle House", Clarksville "Apple House", Encinitas beach house). Work template ships no real-estate tracking. |
| `~/Public/gtd-life/memory/me/networking/` (subdir) | Personal-networking contact notes. AC1 requires a FLAT two-file `memory/me/` directory with NO subdirectories. If contact-note tracking is added later, `memory/people/` (Story 3.1 template tree) is the correct home — not a personal-me subdirectory. |
| `~/Public/gtd-life/memory/me/networking/inspirecxo-ai-advisory-2026-03-27.md` | Specific contact note for a personal-networking event. Falls under the excluded `networking/` subdir above. |

No Story 3.3 target file or directory should reference any of the above paths. The Story 3.3 output under `memory/me/` contains exactly two files (`identity.md`, `preferences.md`) and zero subdirectories.

## Content classes to scrub vs retain

**Classes SCRUBBED during the rebuild (zero mention in Story 3.3 output):**

1. **Derek biography.** Name, location, current roles, career history, philosophy, interests, devices, professional identity prose. Every sentence of the gtd-life `me/identity.md` body is Derek-specific. REBUILD FROM SCAFFOLD — the target body uses `{{employee_*}}` placeholders and Vixxo-work-template-generic prose.
2. **Personal business tokens.** `RevivaGo`, `MasteryLab`, `derekneighbors.com`, `Agile Weekly`, `Gangplank`, `Bodybuilding.com`, `Integrum`. Zero mention in Story 3.3 output. (Note: `Vixxo` is retained as the employer name — it is legitimate work-template content and NOT in the scrub list.)
3. **Personal-life tokens.** `Queen Creek`, `Arizona`, `family`, `home`, `running`, `powerlifting`, `D&D`, `Magic: The Gathering`, `Playrix Township`, `endurance running`. Zero mention. (Note: `personal` is in the 17-token banned-term regex — caught by AC7 automatically.)
4. **Personal-tool references.** `Chiron`, `Benji.so`, `Flowtopic`, `Obsidian`, `Git` (Derek's "version everything"), `gmail` MCP, `google-calendar` MCP, `Omarchy Linux`, `Cursor IDE` (as Derek's tool), `Claude Code` (as Derek's tool). Zero mention in Story 3.3 output. The rule is: if the token appears as a Derek-specific tooling preference in the gtd-life source, scrub.
5. **Personal communication rules.** Chiron signing format (`- Chiron (Deke's AI)`), "meme lord" self-description, Derek's anti-AI-slop phrase list, the em-dash ban (note: the em-dash ban is encoded in `AGENTS.md` as a single source of truth and is NOT restated in Story 3.3 `preferences.md`; the Story 3.3 `## Communication Style` section defers to `AGENTS.md` and `.cursor/rules/agent-identity.mdc`).
6. **Personal context-routing guardrails.** `## Context Routing Guardrails (Agent)` subsection in source `preferences.md` routes personal / blog email to gmail MCP and personal / blog calendar to google-calendar MCP. Zero mention in Story 3.3 output. Story 3.3 `preferences.md` is work-only (AC4 `scope: work`); there is no personal / work split to route between.
7. **Inbox conventions with banned contexts.** Source `## Inbox Conventions` sets `context` to one of `vixxo`, `revivago`, or `personal`. Story 3.3 does NOT include an Inbox Conventions section; Story 3.1's `memory/inbox/_template.md` owns inbox shape, and Story 2.2's outbound-messaging-guardrail owns drafting discipline. Single source of truth.
8. **Workflow habits / device usage.** Source lists morning briefing, context switching across Vixxo / RevivaGo / blog / personal, AI-assisted email triage, fitness routine, Mac laptop (work), Omarchy Linux (home), iPad / phone (mobile). Zero mention in Story 3.3 output.

**Thin slice RETAINED in Story 3.3 output (from Vixxo canon sources, NOT from gtd-life source files):**

1. **Five active Vixxo MCPs.** `Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`. Sourced from Story 2.3 `agents/personas/work.md` and `.cursor/rules/agent-identity.mdc`, NOT from gtd-life `me/preferences.md` (which lists personal-context tooling). Story 3.3 `preferences.md` `## Tooling` section enumerates these five MCPs as the baseline tooling set (AC5 explicit requirement).
2. **Work-only email / calendar stack: `Microsoft 365`.** Sourced from `.cursor/rules/agent-identity.mdc` (which declares Microsoft 365 as the work email + calendar MCP). Included via the `## Tooling` MCP list.
3. **Work-only task system: `Linear`.** Sourced from Story 2.3 persona. Included via the `## Tooling` MCP list.
4. **Deferrals to single-source-of-truth rule files.** Story 3.3 `preferences.md` body defers to `AGENTS.md` and `.cursor/rules/agent-identity.mdc` for communication-style / tone, and to `agents/personas/work.md` and `.cursor/rules/agent-identity.mdc` for AI-assistant persona. The preferences file does NOT restate those rules (avoids three-way drift between the rule files, the persona file, and the preferences file).
5. **Five `{{employee_*}}` identity placeholders.** `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}`. Sourced from Story 2.1 `.cursor/rules/agent-identity.mdc` (four placeholders) + Story 3.3 additive extension by one (`{{employee_email}}`). Used ONLY in `identity.md` frontmatter and body (AC2, AC3, AC6); `preferences.md` uses zero placeholders (AC4, AC5, AC6 — prose-only).

## Mapping: source path → target path (or EXCLUDED)

| # | Source path (read-only reference) | Target path (authored into assistants-template) | Port mode |
|---|-----------------------------------|-------------------------------------------------|-----------|
| 1 | `~/Public/gtd-life/memory/me/identity.md` | `memory/me/identity.md` | **REBUILD FROM SCAFFOLD** — discard all body prose; rebuild ~200–2048 bytes with 10-key frontmatter (`type: identity`, `scope: work`, five `{{employee_*}}` placeholders, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: [identity, work]`) + 7 H2 body sections per AC3 |
| 2 | `~/Public/gtd-life/memory/me/preferences.md` | `memory/me/preferences.md` | **REBUILD FROM SCAFFOLD** — discard all body prose; rebuild ~200–2048 bytes with 5-key frontmatter (`type: preferences`, `scope: work`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: [preferences, work]`) + 5 H2 body sections per AC5; retain only the five-MCP Vixxo tooling list and the deferrals to rule files |
| 3 | `~/Public/gtd-life/memory/me/family.md` | — | **EXCLUDED** (personal-life; 2 banned-term hits; file name itself is a banned token) |
| 4 | `~/Public/gtd-life/memory/me/food-guide-queen-creek.md` | — | **EXCLUDED** (PII-locale, spouse-preferences; 36 banned-term hits — highest density) |
| 5 | `~/Public/gtd-life/memory/me/ventures.md` | — | **EXCLUDED** (Derek side-businesses; every named venture is Derek-owned) |
| 6 | `~/Public/gtd-life/memory/me/properties.md` | — | **EXCLUDED** (Derek real-estate holdings) |
| 7 | `~/Public/gtd-life/memory/me/networking/` (subdir) | — | **EXCLUDED** (AC1 requires flat two-file directory; personal-networking content) |
| 8 | `~/Public/gtd-life/memory/me/networking/inspirecxo-ai-advisory-2026-03-27.md` | — | **EXCLUDED** (falls under the networking/ subdir above) |

Both target paths are new files (none exist in `assistants-template` yet — confirmed by `find memory/me -type f` returning empty at audit time). No file replacement, no merge, no pre-existing content collision. The target directory `memory/me/` itself is new and must be created by Tasks 3a / 3b (`mkdir -p memory/me`). UTF-8 encoding and LF line endings are required per AC8 / Dev Notes "Architectural constraints". Each emitted file ends with a single `\n` for POSIX-tool friendliness.

**Story 1.1 allowlist zero-edit invariant.** The `memory/` subdirectory allowlist at `story-1-1-scaffold-validation.sh:155` already admits `me` as a legitimate subdirectory slug (Story 2.1 commit `0db273b` forward-compatibility insertion: `me|mcp|obsidian|\.obsidian|meetings|people|decisions|reference|inbox|appreciations`). Story 3.3 requires ZERO edit to that harness — AC10 codifies this invariant. This is the first Epic-3 story that does not require a Story 1.1 allowlist extension (distinct from Stories 3.1 and 3.2, which each added one line).

---

End of Story 3.3 Baseline Audit. Task 2 (canonical blueprint) consumes the per-file frontmatter shape + heading map above and the content-class retention rules. Tasks 3a / 3b consume the source → target REBUILD mapping. Task 4 (harness) consumes the 17-token banned-term regex, the 12-token Derek-specific fixed-string scrub set, and the placeholder-allowlist rules as cross-file-scrub probes in `check_task4`.
