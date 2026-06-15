# Story 3.3: Seed empty identity and preferences files

Status: done

## Story

As a new Vixxo employee who has cloned the `assistants-template` and will later run the Epic 5 setup wizard (`bin/init`) to populate per-employee context,
I want minimal `memory/me/identity.md` and `memory/me/preferences.md` scaffolds with `scope: work` frontmatter, placeholder-driven identity fields (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}`), and bland-but-useful work-only placeholder headings,
so that (a) the `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md` "Context Files" lists have real targets they already reference, (b) the Epic 5 Story 5.2 wizard has deterministic files to rewrite with user answers (name, email, role), (c) new employees see the expected memory-vault `me/` directory on first Obsidian open with no Derek content, and (d) no personal (home, family, blog, RevivaGo, Benji, Flowtopic) context leaks in from the gtd-life reference sources.

## Acceptance Criteria

1. **AC1 — `memory/me/` directory exists with exactly two portable markdown files**
   - Given the cloned `assistants-template` repository after Story 3.3 lands
   - When `memory/me/` is listed (`ls -A memory/me`)
   - Then the directory contains exactly two files: `identity.md` and `preferences.md` — one file per `me/` subsystem (identity skeleton, preferences skeleton) — and no extra files
   - And each file exists, is non-empty, is a valid UTF-8 text file, and ends with a trailing newline (last byte `0x0a`)
   - And each file opens with YAML frontmatter delimited by `---` on line 1 and a closing `---` on a later line, followed by a blank line and a body
   - And the directory contains NO `.DS_Store`, `*.bak`, `*.log`, `*.tmp`, `Icon\r`, or any sentinel file (`.gitkeep`, `.keep`, `empty`, `placeholder`) — `identity.md` and `preferences.md` are themselves git-trackable content making sentinels redundant (same logic as Story 3.1 AC9 and Story 3.2 AC11)
   - And NO subdirectories exist under `memory/me/` (the gtd-life source `me/networking/` is out of scope — Story 3.3 ships a flat two-file directory)

2. **AC2 — `memory/me/identity.md` frontmatter shape (canonical key order, work-only scope)**
   - Given `memory/me/identity.md`
   - When the frontmatter block (lines between the first `---` and the next `---`) is read
   - Then it contains exactly ten keys in canonical order: `type` (literal `identity`), `scope` (literal `work`), `name` (placeholder `"{{employee_name}}"`), `role` (placeholder `"{{employee_role}}"`), `department` (placeholder `"{{employee_department}}"`), `manager` (placeholder `"{{employee_manager}}"`), `email` (placeholder `"{{employee_email}}"`), `created` (literal `YYYY-MM-DD`), `updated` (literal `YYYY-MM-DD`), `tags` (YAML inline array `[identity, work]`)
   - And the `scope` value is the literal string `work` (NOT `personal`, NOT `vixxo`, NOT `mixed`) — work-only declaration matches NFR7 and architecture.md constraint
   - And the `tags` array contains the literal token `work` and NOT the literal token `personal` (carried-forward banned token)
   - And the placeholder string values use the Story 2.1 / 2.3 identity-placeholder vocabulary: `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}` — five tokens total, each wrapped in the `"…"` double-quoted YAML scalar form

3. **AC3 — `memory/me/identity.md` body structure (placeholder-driven, work-only)**
   - Given the body of `memory/me/identity.md` (everything after the closing frontmatter `---`)
   - When the body is read
   - Then the first body heading is `# Identity` (H1) and the body contains at least the following H2 headings in order: `## Name`, `## Role`, `## Department`, `## Manager`, `## Email`, `## Work Scope`, `## Key References`
   - And the body references `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}` at least once each — identity-placeholder discipline matches Story 2.1 (`.cursor/rules/agent-identity.mdc`) and Story 2.3 (`agents/personas/work.md`) precedent
   - And the `## Work Scope` section includes the literal substring `work context only` AND an explicit deferral to `.cursor/rules/agent-identity.mdc` as the scope authority (single source of truth — avoids restating the scope block in three places)
   - And the `## Key References` section lists at minimum `.cursor/rules/agent-identity.mdc`, `agents/personas/work.md`, and `memory/me/preferences.md` (sibling file)
   - And the body contains ZERO real human names, ZERO absolute filesystem paths (`/Users/`, `~/Public/`, `Public/gtd-life`), and ZERO `{{double-curly-brace}}` tokens outside the allowlist `{{employee_name|employee_role|employee_department|employee_manager|employee_email}}`

4. **AC4 — `memory/me/preferences.md` frontmatter shape (canonical key order, work-only scope)**
   - Given `memory/me/preferences.md`
   - When the frontmatter block is read
   - Then it contains exactly five keys in canonical order: `type` (literal `preferences`), `scope` (literal `work`), `created` (literal `YYYY-MM-DD`), `updated` (literal `YYYY-MM-DD`), `tags` (YAML inline array `[preferences, work]`)
   - And the `scope` value is the literal string `work`
   - And the `tags` array contains the literal token `work` and NOT the literal token `personal`
   - And the frontmatter contains ZERO identity-placeholder tokens (`{{employee_*}}`) — identity fields live in `identity.md`; `preferences.md` is workspace-behavior, not operator-identity

5. **AC5 — `memory/me/preferences.md` body structure (placeholder-driven, work-only)**
   - Given the body of `memory/me/preferences.md`
   - When the body is read
   - Then the first body heading is `# Preferences` (H1) and the body contains at least the following H2 headings in order: `## Communication Style`, `## Tooling`, `## Meeting Cadence`, `## Working Hours`, `## AI Assistant`
   - And the `## Tooling` section enumerates the five active Vixxo MCPs from Story 2.3 persona (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`) as the baseline tooling set
   - And the `## AI Assistant` section defers to `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md` for tone / signing / persona details (avoids restating Story 2.1 + 2.3 content — single source of truth)
   - And the body contains ZERO references to `Chiron`, `Benji`, `Flowtopic`, `Obsidian`, `gmail`, `google-calendar` (personal-assistant and personal-productivity tokens from the gtd-life source that must not port through), ZERO real human names, ZERO absolute filesystem paths, and ZERO `{{double-curly-brace}}` tokens of any kind (preferences body uses prose, not placeholders)

6. **AC6 — Placeholder discipline: identity-placeholder vocabulary allowlisted; no other brace / bracket / dollar-brace forms**
   - Given both files `memory/me/identity.md` and `memory/me/preferences.md`
   - When every `{{…}}` token is extracted via `grep -oE '\{\{[^}]+\}\}'`
   - Then every extracted token must be a member of the five-item identity-placeholder allowlist: `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}`
   - And `preferences.md` yields ZERO extracted tokens (prose-only, AC5 reinforcement)
   - And `identity.md` yields at minimum five distinct tokens (all five allowlisted placeholders used at least once, per AC3 body assertion)
   - And neither file contains any single-brace `{name}` form, any angle-bracket `<name>` form, any percent-wrapped `%name%` form, or any shell-interpolation `${name}` form — those forms are reserved for future interpolation contexts and their presence would confuse the Story 5.2 wizard's find-and-replace pass
   - And the content-shape placeholder vocabulary used by Story 3.1 memory templates (`{{Name}}`, `{{Meeting Title}}`, `{{Decision Title}}`, `{{Reference Title}}`, `{{topic}}`, `{{owner}}`, `{{estimated minutes}}`, `{{person}}`, `{{action}}`, `{{date}}`, `{{company}}`, `{{role}}`, `{{manager or "N/A"}}`, `{{count or "N/A"}}`, `{{Recipient or Moment}}`, `{{action item}}`, `{{name}}`) MUST NOT appear in `identity.md` or `preferences.md` — those are note-shape placeholders owned by Story 3.1 and are structurally incompatible with identity-file semantics

7. **AC7 — Zero Derek / RevivaGo / personal content in either file (17-token banned-term lock, identical to Stories 3.1 / 3.2)**
   - Given both `memory/me/identity.md` and `memory/me/preferences.md`
   - When the standard boundary-guarded banned-term scan (carried forward from Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2, identical 17-token set) runs across each file
   - Then the regex `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` matches zero occurrences, case-insensitive (`grep -iE`), for every token in the inherited lock: `derek`, `neighbors`, `revivago`, `benji`, `flowtopic`, `gtd-life`, `gtdlife`, `wyoming`, `cheyenne`, `family`, `home`, `blog`, `wife`, `son`, `daughter`, `dog`, `personal` (17 tokens — the exact Story 3.1 post-Phase-4 F4 set; no new tokens added for Story 3.3; no tokens removed)
   - And neither file contains the literal strings `gtd-life`, `~/Public/gtd-life`, `Public/gtd-life`, `/Users/`, `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy` — fixed-string `grep -F` scan defence-in-depth (these strings appear verbatim in the gtd-life source `me/identity.md` and `me/preferences.md` and would silently port through on a careless verbatim copy)
   - And neither file contains any real human first-or-last name (no `Derek`, no `Laurie`, no `Deke`)

8. **AC8 — Byte-budget bounds per file (lower bound ensures scaffold is actually authored; upper bound guards against content drift)**
   - Given `memory/me/identity.md` and `memory/me/preferences.md`
   - When `wc -c` is run on each file
   - Then `identity.md` byte length is in the range `200 ≤ bytes ≤ 2048` — lower bound enforces frontmatter + seven H2 headings + minimal body prose; upper bound guards against ported Derek content regression (gtd-life source `me/identity.md` is ~2500 bytes of Derek biography; our scaffold is smaller)
   - And `preferences.md` byte length is in the range `200 ≤ bytes ≤ 2048` — same rationale (gtd-life source `me/preferences.md` is ~2900 bytes)
   - And both files use LF line endings (no CRLF) — grep `$'\r'` (literal carriage return) MUST return zero matches across both files

9. **AC9 — Story 3.2 `.obsidian/` config and Story 3.1 template-tree invariance (byte-for-byte stable)**
   - Given the seven Story 3.2 `memory/.obsidian/` JSON files (`app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`, `templates.json`) AND the nine Story 3.1 template files (`meetings/_template/{meeting,agenda,prep,transcript}.md`, `people/_template.md`, `decisions/_template.md`, `reference/_template.md`, `inbox/_template.md`, `appreciations/_template.md`) AND `memory/.gitkeep` (Story 1.1)
   - When Story 3.3 creates `memory/me/` and its two markdown files
   - Then `memory/.gitkeep` remains byte-for-byte unchanged (size 0)
   - And each of the nine Story 3.1 template files remains byte-for-byte identical to the Story 3.1 Task-6 handoff fingerprint (positional byte-count lock — Story 3.2 harness's `STORY_3_1_TEMPLATE_BYTES` array is the authoritative vector: `828 / 250 / 513 / 306 / 561 / 588 / 506 / 72 / 211`)
   - And each of the seven Story 3.2 `.obsidian/` JSON files remains byte-for-byte identical to the Story 3.2 Task-6 handoff fingerprint (SHA-256 vector captured 2026-04-20: `app.json c39e6f3f…`, `appearance.json ca3d163b…`, `community-plugins.json 37517e5f…`, `core-plugins.json ac8a3c03…`, `daily-notes.json f21e73a2…`, `graph.json f75c7af6…`, `templates.json 935f8fce…`)
   - And no new `.gitkeep`, `.keep`, `empty`, or `placeholder` sentinel files are added anywhere under `memory/me/` (the two markdown files are themselves git-trackable content making sentinels redundant — Story 3.1 AC9 / Story 3.2 AC11 precedent)
   - And no new sentinels are added under `memory/meetings/`, `memory/meetings/_template/`, `memory/people/`, `memory/decisions/`, `memory/reference/`, `memory/inbox/`, `memory/appreciations/`, or `memory/.obsidian/` (Stories 3.1 / 3.2 invariance preserved)

10. **AC10 — Story 1.1 allowlist requires ZERO amendment (forward-compatibility precedent preserved)**
    - Given the Story 1.1 scaffold-validation harness at `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` line 155
    - When Story 3.3 creates the `memory/me/` subdirectory
    - Then NO edit to that line (or any other line of that harness) is required — the `memory/` allowlist regex already admits `me` as a legitimate subdirectory slug via the Story 2.1 commit `0db273b` forward-compatibility insertion (`me|mcp|obsidian|\.obsidian|meetings|people|decisions|reference|inbox|appreciations`)
    - And `story-1-1-scaffold-validation.sh` is asserted byte-stable during Story 3.3 execution — zero bytes change; the Story 2.1 / 3.1 / 3.2 precedent of documenting a one-line additive amendment is explicitly NOT invoked for this story because the anticipatory Story 2.1 insertion already covers Story 3.3's new subdirectory
    - And Story 3.3's task plan includes a short verification step (`diff` against a pre-edit baseline) confirming zero bytes changed in `story-1-1-scaffold-validation.sh`
    - And if an unexpected allowlist amendment IS later found necessary (e.g. BSD vs GNU grep divergence, or a regex-character-class bug), it MUST be codified in this AC as an explicit exception following the Story 3.2 AC13 / AC15 exception-codification precedent

11. **AC11 — Validation harness exists and is wired into the test-harness family**
    - Given the existing harness family under `_bmad-output/implementation-artifacts/tests/`
    - When Story 3.3 lands
    - Then a new deterministic harness `story-3-3-identity-preferences-validation.sh` exists at `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh`, is marked executable (`chmod +x`), uses `#!/usr/bin/env bash` on line 1 and `set -euo pipefail` on line 2
    - And the harness implements gates `task1` (baseline audit evidence present and structured — `story-3-3-baseline-audit.md`), `task2` (canonical blueprint evidence present and structured — `story-3-3-canonical-blueprint.md`), `task3` (per-file shape verification across the two authored markdown files: existence + non-empty + trailing newline + frontmatter block + frontmatter keys in canonical order per AC2 / AC4 + `scope: work` literal + required body H2 headings per AC3 / AC5 + Story 3.1 / Story 3.2 invariance per AC9 + byte-budget bounds per AC8 + directory-count-exactly-two per AC1), gate `task4` (cross-file scrub: boundary-guarded banned-term scan + literal `gtd-life` / `/Users/` / `Chiron` / `MasteryLab` / `Gangplank` fixed-string scans + placeholder-allowlist extraction + forbidden-bracket-form probes + `personal`-in-tags fixed-string probe), `task5` (self-check: shebang, `set -euo pipefail`, all case arms, all declared constants, `regex_self_probe` definition via `declare -F` per Story 2.4 F4 + Story 3.1 / 3.2 precedent), `task6` (regression — invokes Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 harnesses in `all` mode and asserts each exits zero with the expected `^PASS:` line count fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7`), plus an `all` dispatcher
    - And the harness exits `0` with `PASS: all` on success; exits `1` and emits `FAIL: <gate>: <reason>` on stderr on failure — matching the Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 contract
    - And the harness is BSD-grep and GNU-grep compatible, POSIX-bash-3.2 compatible, and uses only `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`, and shell built-ins (no `rg`, no `jq`, no Python, no `node` — frontmatter-key-order assertions use `awk` line-walks, not a YAML parser)
    - And the harness implements `regex_self_probe` that exercises the boundary-guarded banned-term regex against at least two tokens — one carried-forward (`derek` → positive, `derekson` → boundary-rejected) and one Epic-3-added (`personal` → positive, `personally` → boundary-rejected) — AND at least one placeholder-allowlist probe (`{{employee_name}}` → allowlist hit, `{{Meeting Title}}` → allowlist miss for identity-file semantics) — guards against a mis-parsing host grep or a mis-escaped allowlist (same pattern as Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2)
    - And when invoked in `all` mode, the harness emits exactly 7 lines matching `^PASS:` on stdout (`PASS: task1` → `PASS: task6` → `PASS: all`) — fingerprint compatible with the Stories 3.1 / 3.2 pass-count convention

12. **AC12 — Regression-runs all nine predecessor harnesses cleanly (extends Story 3.2's eight-harness chain by one)**
    - Given all prior harnesses in `_bmad-output/implementation-artifacts/tests/` (Story 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2 — nine predecessors; Story 3.2 is new to this regression chain relative to Story 3.2's own eight-harness chain)
    - When the Story 3.3 regression gate (`task6`) runs
    - Then `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, `bash story-2-1-agent-identity-validation.sh all`, `bash story-2-2-guardrail-and-formatting-validation.sh all`, `bash story-2-3-work-persona-validation.sh all`, `bash story-2-4-benji-inbox-absence-validation.sh all`, `bash story-3-1-memory-template-tree-validation.sh all`, and `bash story-3-2-obsidian-config-validation.sh all` each exit `0` with `PASS: all`
    - And the per-harness `^PASS:` line-count fingerprint (measured 2026-04-20) is `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7` respectively — the harness MUST fail if any sub-harness emits a different count (Story 3.1 Phase-4 F7 + Story 3.2 precedent)
    - And zero bytes are changed in any of those nine prior harnesses during Story 3.3 execution (Story 3.2's final paragraph of AC13 is inverted here — Story 3.3 requires NO integration-fix exception because the Story 2.1 anticipatory allowlist already admits `me`; see AC10)
    - And zero bytes are changed in `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files (`outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`), `agents/personas/work.md`, the root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`), `README.md`, `LICENSE`, `.gitignore`, `memory/.gitkeep`, any of the nine Story 3.1 template files under `memory/`, or any of the seven Story 3.2 `.obsidian/` JSON files — Story 3.3 is additive only (new `memory/me/` directory + two markdown files + new harness + new evidence artifacts + sprint-status flip + this story file)

13. **AC13 — Sprint tracker lifecycle reflects the story transition and epic-3 flips to `done` when Story 3.3 closes**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When Story 3.3 opens at Phase 1 (SM pass) and again at Phase 2 (Dev handoff) and again at Phase 3 (review approval)
    - Then the `3-3-seed-empty-identity-and-preferences.status` entry is updated `backlog → ready-for-dev` at Phase 1, `ready-for-dev → review` at Phase 2, and `review → done` at Phase 3 (the autonomous-swarm lifecycle may collapse interim states per Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 precedent — a single `backlog → review` on-disk transition is acceptable as long as the final pre-review status is `review`)
    - And `epic-3.status` remains `in-progress` until Story 3.3 reaches `done`, at which point it flips to `done` (Story 3.3 is the final Epic 3 story; Stories 3.1 and 3.2 are already `done`; the epic closes when every story in it is `done`)
    - And `last_updated` is set to `2026-04-20` on the Phase 1 edit
    - And no other story's status is regressed; every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` is preserved byte-for-byte (zero reordering, zero comment drift, zero key addition/removal beyond the three value flips on `3-3-…status` across the three phases, the one `epic-3.status` flip at Phase 3, and the `last_updated` value change)

14. **AC14 — Story is additive; no scope creep into Epic 4 / Epic 5 / Epic 6 territory**
    - Given the scope of Story 3.3
    - When the working-set file list is reviewed
    - Then Story 3.3 creates ONLY: the two markdown files under `memory/me/`, the harness, three test-evidence files (baseline audit, canonical blueprint, Task 6 handoff), and this story file
    - And Story 3.3 does NOT create `memory/companies/`, `memory/vixxo/`, `memory/daily/`, `memory/me/networking/`, `memory/me/ventures.md`, `memory/me/properties.md`, `memory/me/family.md`, `memory/me/food-guide-queen-creek.md` (all gtd-life `me/` files / subdirs that are out of scope — personal-life content or Derek-specific venture tracking that has no place in a Vixxo work template)
    - And Story 3.3 does NOT create or edit any files under `.cursor/`, `agents/`, `bin/`, `scripts/`, `docs/`, `_bmad/`, `.github/`, `_bmad-output/planning-artifacts/`, or the repo root (no `identity.md` at repo root — identity lives at `memory/me/identity.md` per agent-identity rule and work persona "Context Files" references)
    - And Story 3.3 does NOT port any Derek biographical content (career history, location, philosophy, interests, devices, professional identity prose) from the gtd-life `me/identity.md` source — the port method is "scrub and rebuild from scaffold" not "verbatim-with-repairs" (distinct from Story 3.2's port method)
    - And Story 3.3 does NOT port any Derek preferences content (food guide, communication-style anti-phrase list, Chiron AI-agent name, personal MCP list, context-routing guardrails) from the gtd-life `me/preferences.md` source — same rationale
    - And Story 3.3 does NOT invoke or require the Epic 5 setup wizard (`bin/init`) — the wizard will rewrite these files in Story 5.2 using the placeholder-driven substitution pattern; Story 3.3's job is to create the target files with the correct placeholders and shape so Story 5.2 has deterministic input
    - And Story 3.3 modifies ONLY: `_bmad-output/implementation-artifacts/sprint-status.yaml` (Story 3.3 status flips + `last_updated` + `epic-3.status` flip at Phase 3) and this story file (Dev Agent Record / Change Log / File List / checkboxes at Dev handoff)

## Tasks / Subtasks

- [x] Task 1 — Baseline audit of gtd-life `me/` sources and Derek-content inventory (AC: 2, 3, 4, 5, 7, 14) **[Parallelizable with Task 2]**
  - [x] Enumerate every file and subdirectory at `~/Public/gtd-life/memory/me/`. Record each entry's (a) path, (b) byte length, (c) line count (for files), (d) frontmatter key list in source order, (e) all banned-term hits under the boundary-guarded 17-token lock, (f) all real-human-name hits (fixed-string scan for `Derek`, `Laurie`, `Deke`), (g) all filesystem-path leaks (`/Users/`, `~/`, `Public/`, `gtd-life`), (h) all Derek-specific substrings (`Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `Benji`, `Flowtopic`, `RevivaGo`, `Vixxo`, `blog`, `gmail`, `google-calendar`, `Obsidian`, `Cursor`, `Claude Code`), (i) all `{{double-curly-brace}}` tokens (expecting zero — gtd-life sources are concrete, not templated).
  - [x] Specifically flag the FOUR siblings explicitly excluded from the port: `family.md` (personal-life), `food-guide-queen-creek.md` (personal-life, PII-locale), `ventures.md` (Derek side businesses), `properties.md` (Derek real-estate), plus the `networking/` subdirectory (personal-contact content). Record byte lengths, banned-term-hit counts, and a one-sentence rationale for each exclusion. The baseline audit must state explicitly: "Only `identity.md` and `preferences.md` are in scope for Story 3.3; the other four files and one subdirectory are out of scope."
  - [x] Identify the classes of content that must be SCRUBBED from the port:
    - Derek biography (name, location, current roles, career history, philosophy, interests, devices, professional identity prose) — REBUILD from scaffold, do not attempt verbatim port
    - Personal business tokens (`RevivaGo`, `MasteryLab`, `derekneighbors.com`, `Agile Weekly`, `Gangplank`, `Bodybuilding.com`, `Integrum`) — zero mention in port
    - Personal-life tokens (`Queen Creek`, `Arizona`, `family`, `home`, `running`, `powerlifting`, `D&D`, `Magic: The Gathering`, `Playrix Township`) — zero mention in port
    - Personal-tool references (`Chiron`, `Benji.so`, `Flowtopic`, `Obsidian`, `Git`, `gmail` MCP, `google-calendar` MCP, `Omarchy Linux`) — some are generic (git); the rule is: if the token appears as a Derek-specific tooling preference, scrub; if it is a generic Vixxo work MCP from Story 2.3 (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`), retain in `preferences.md` as the allowlisted baseline
    - Personal communication rules (Chiron signing format, "meme lord" self-description, Derek's anti-AI-slop phrase list, em-dash-ban — but note: the em-dash ban is already encoded in AGENTS.md and is NOT restated in `preferences.md`; single source of truth)
  - [x] Confirm neither gtd-life source file uses `{{employee_*}}` identity-placeholder tokens (expected: zero — gtd-life source is fully-populated Derek content, not template skeletons). Story 3.3's port method inverts this: the ported files are TEMPLATES with identity-placeholder tokens that the Epic 5 wizard later rewrites.
  - [x] Record the known Vixxo tooling-preferences content that IS in scope for `preferences.md`: the five active MCPs (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong` — from Story 2.3 persona), the work-only email/calendar stack (`Microsoft 365` — from `.cursor/rules/agent-identity.mdc`), the task system (`Linear` — from persona), and deferrals to existing single-source-of-truth rule files (agent-identity for tone + scope; outbound-messaging-guardrail for drafting discipline; teams-dm-formatting for Teams messages).
  - [x] Persist all findings at `_bmad-output/implementation-artifacts/tests/story-3-3-baseline-audit.md` with sections: `# Story 3.3 Baseline Audit`, `## gtd-life me/ source inventory`, `## Per-file frontmatter + heading map`, `## Banned-term scan of source files`, `## Derek-specific fixed-string scan of source files`, `## Out-of-scope files and subdirectories`, `## Content classes to scrub vs retain`, `## Mapping: source path → target path (or EXCLUDED)`.

- [x] Task 2 — Canonical blueprint for the two authored markdown files (AC: 2, 3, 4, 5, 6, 7, 8) **[Parallelizable with Task 1]**
  - [x] Author a blueprint document at `_bmad-output/implementation-artifacts/tests/story-3-3-canonical-blueprint.md` that specifies, for each of the two target files, the EXACT frontmatter key set in canonical order with types and literal values (or placeholder vocabulary per AC2 / AC4), the EXACT body-heading sequence (H1 + H2 list in order per AC3 / AC5), byte-budget (lower and upper bound per AC8), and the placeholder / banned-term locks per AC6 / AC7. Follow the Story 3.1 / Story 3.2 `canonical-blueprint.md` precedent.
  - [x] Blueprint for `memory/me/identity.md`:
    - Frontmatter keys in canonical order: `type: identity`, `scope: work`, `name: "{{employee_name}}"`, `role: "{{employee_role}}"`, `department: "{{employee_department}}"`, `manager: "{{employee_manager}}"`, `email: "{{employee_email}}"`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: [identity, work]` (ten keys total)
    - Body headings in order: `# Identity` (H1), `## Name` (H2), `## Role` (H2), `## Department` (H2), `## Manager` (H2), `## Email` (H2), `## Work Scope` (H2), `## Key References` (H2)
    - Body prose uses each of the five identity-placeholder tokens at least once
    - Body `## Work Scope` section includes literal substring `work context only` and defers to `.cursor/rules/agent-identity.mdc`
    - Body `## Key References` section lists `.cursor/rules/agent-identity.mdc`, `agents/personas/work.md`, `memory/me/preferences.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules` (same list as the agent-identity rule's Key References block — single source of truth)
    - Byte budget: 200 ≤ bytes ≤ 2048
  - [x] Blueprint for `memory/me/preferences.md`:
    - Frontmatter keys in canonical order: `type: preferences`, `scope: work`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: [preferences, work]` (five keys total)
    - Body headings in order: `# Preferences` (H1), `## Communication Style` (H2), `## Tooling` (H2), `## Meeting Cadence` (H2), `## Working Hours` (H2), `## AI Assistant` (H2)
    - Body `## Tooling` section enumerates `Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong` as the active MCP baseline (matches Story 2.3 persona)
    - Body `## AI Assistant` section defers to `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md` for tone / signing / persona
    - Body `## Communication Style` section defers to `AGENTS.md` communication-style list (no em dashes, no AI-slop phrases, direct and concise) — single source of truth; the preferences file does not restate the list
    - Byte budget: 200 ≤ bytes ≤ 2048
    - Zero `{{…}}` placeholder tokens (preferences body is prose, not templated — AC6 reinforcement)
  - [x] Blueprint placeholder vocabulary lock: reuse the Story 3.1 five-item identity-placeholder allowlist (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}`) — exactly the five tokens documented in Story 3.1 canonical-blueprint `## Placeholder vocabulary lock` (identity-file subsection). Story 3.3 adds ZERO new identity placeholders. The note-shape vocabulary (`{{Name}}`, `{{Meeting Title}}`, etc.) is explicitly FORBIDDEN in Story 3.3 output files.
  - [x] Blueprint banned-term lock: reuse the Stories 3.1 / 3.2 17-token set verbatim (`derek, neighbors, revivago, benji, flowtopic, gtd-life, gtdlife, wyoming, cheyenne, family, home, blog, wife, son, daughter, dog, personal`). Story 3.3 adds ZERO new tokens. Also lock the Derek-specific fixed-string scrub set: `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `gmail`, `google-calendar`, `Playrix`, `Laurie`, `Deke` — fixed-string scans (not in the 17-token regex because these names contain substrings that may legitimately appear in non-Derek contexts; narrow-scope fixed-string enforcement in `memory/me/*.md` only).
  - [x] Blueprint forbidden-form lock: list every bracket / interpolation form that must NOT appear in either authored file: single-brace `{x}`, angle-bracket `<x>`, percent `%x%`, dollar-brace `${x}`, HTML-ish `<!-- x -->` (except Story 3.1 / 3.2 "why" comment convention, which is permitted). Pattern: `grep -oE '<[A-Za-z_]+>' file | wc -l == 0`, `grep -oE '%[A-Za-z_]+%' file | wc -l == 0`, `grep -oE '\$\{[^}]+\}' file | wc -l == 0`, and the single-brace probe `grep -oE '\{[^{][^}]*[^}]\}' file | grep -v '^\{\{' | wc -l == 0` (matches `{foo}` but not `{{foo}}`).

- [x] Task 3a — Author `memory/me/identity.md` (AC: 1, 2, 3, 6, 7, 8) **[Parallelizable with Task 3b once Task 2 blueprint is written]**
  - [x] Create the directory `memory/me/` (bash: `mkdir -p memory/me`). The Story 1.1 harness allowlist at `story-1-1-scaffold-validation.sh:155` already admits `me` as a legitimate `memory/` subdir slug — no allowlist extension required (AC10).
  - [x] Author `memory/me/identity.md` per the Task 2 blueprint. Use the following skeleton shape (exact byte content is Dev's choice within the byte-budget and shape constraints):

    ```markdown
    ---
    type: identity
    scope: work
    name: "{{employee_name}}"
    role: "{{employee_role}}"
    department: "{{employee_department}}"
    manager: "{{employee_manager}}"
    email: "{{employee_email}}"
    created: YYYY-MM-DD
    updated: YYYY-MM-DD
    tags: [identity, work]
    ---

    # Identity

    ## Name

    {{employee_name}}

    ## Role

    {{employee_role}}

    ## Department

    {{employee_department}}

    ## Manager

    {{employee_manager}}

    ## Email

    {{employee_email}}

    ## Work Scope

    Vixxo work context only. This file captures {{employee_name}}'s role and
    relationships for the assistants template; no personal-life content is
    stored or referenced here. For the full scope declaration see
    `.cursor/rules/agent-identity.mdc`.

    ## Key References

    - `.cursor/rules/agent-identity.mdc`
    - `agents/personas/work.md`
    - `memory/me/preferences.md`
    - `AGENTS.md`
    - `CLAUDE.md`
    - `.cursorrules`

    <!-- Why: identity skeleton; Epic 5 setup wizard rewrites placeholders with employee answers. -->
    ```

  - [x] After authoring, run the harness checks in isolation: `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh task3` and `task4` (only effective once Task 4 harness lands; for Task 3a standalone verification use manual grep probes): the 17-token banned-term regex `grep -iE` → 0 matches; fixed-string scans for `gtd-life`, `/Users/`, `Public/`, `Chiron`, `MasteryLab`, `Gangplank`, `Omarchy`, `Deke`, `Laurie` → 0 matches each; placeholder extraction `grep -oE '\{\{[^}]+\}\}'` → every token is a member of the five-item allowlist; first byte is `---`; trailing-newline `tail -c 1 | od -An -tx1` equals `0a`; byte budget 200 ≤ `wc -c` ≤ 2048.

- [x] Task 3b — Author `memory/me/preferences.md` (AC: 1, 4, 5, 6, 7, 8) **[Parallelizable with Task 3a once Task 2 blueprint is written]**
  - [x] Create the directory `memory/me/` (idempotent `mkdir -p` — may already exist from parallel Task 3a).
  - [x] Author `memory/me/preferences.md` per the Task 2 blueprint. Use the following skeleton shape (exact byte content is Dev's choice within byte-budget and shape constraints):

    ```markdown
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

    Active Vixxo work MCPs for this template:

    - Linear
    - GitHub
    - Microsoft 365
    - Salesforce
    - Gong

    Configuration lives in `.cursor/mcp.json` (Epic 4). Credential wiring
    lives in `.env.example` (Epic 4).

    ## Meeting Cadence

    Captured in `memory/meetings/` using the Story 3.1 meeting templates.
    Morning briefing and end-of-day wrap cadence is Vixxo-team-dependent;
    the assistants template does not prescribe a specific schedule.

    ## Working Hours

    Work-only; Vixxo business hours. Deferred requests outside scope per
    `.cursor/rules/agent-identity.mdc`.

    ## AI Assistant

    See `agents/personas/work.md` for persona and
    `.cursor/rules/agent-identity.mdc` for identity. This file does not
    restate persona or signing conventions; the rule files are the single
    source of truth.

    <!-- Why: preferences skeleton; work-only, defers to upstream rule files for tone and persona. -->
    ```

  - [x] After authoring, run the same isolation checks as Task 3a (banned-term regex, Derek fixed-string scans, zero `{{…}}` tokens, first-byte `---`, trailing newline, byte budget).

- [x] Task 4 — Author the deterministic validation harness (AC: 11, 12) **[Sequential — depends on Task 2 blueprint AND Tasks 3a / 3b files existing]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh`. Model on `story-3-2-obsidian-config-validation.sh`. `#!/usr/bin/env bash` on line 1, `set -euo pipefail` on line 2, `chmod +x`. POSIX-bash-3.2, BSD+GNU-grep compatible. No `jq`, no `node`, no Python, no `yq`.
  - [x] Declare constants at the top:
    - `PROJECT_ROOT`, `TESTS_DIR`, `SELF_PATH` — standard harness boilerplate.
    - `MEMORY_DIR="${PROJECT_ROOT}/memory"`
    - `ME_DIR="${MEMORY_DIR}/me"`
    - `IDENTITY_MD="${ME_DIR}/identity.md"`
    - `PREFERENCES_MD="${ME_DIR}/preferences.md"`
    - `BASELINE_AUDIT_PATH="${TESTS_DIR}/story-3-3-baseline-audit.md"`
    - `BLUEPRINT_PATH="${TESTS_DIR}/story-3-3-canonical-blueprint.md"`
    - Nine prior-harness paths: `STORY_1_1_HARNESS`, `STORY_1_2_HARNESS`, `STORY_1_3_HARNESS`, `STORY_2_1_HARNESS`, `STORY_2_2_HARNESS`, `STORY_2_3_HARNESS`, `STORY_2_4_HARNESS`, `STORY_3_1_HARNESS`, `STORY_3_2_HARNESS`
    - `BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'` — 17 tokens (identical to Stories 3.1 / 3.2)
    - `DEREK_FIXED_STRINGS=( Chiron MasteryLab "Agile Weekly" "Queen Creek" Gangplank "Bodybuilding.com" Integrum Omarchy derekneighbors.com Playrix Laurie Deke )` — Story-3.3-specific defence-in-depth fixed-string scans
    - `IDENTITY_PLACEHOLDER_ALLOWLIST=( '{{employee_name}}' '{{employee_role}}' '{{employee_department}}' '{{employee_manager}}' '{{employee_email}}' )` — five tokens (Story 2.1 / 2.3 identity-placeholder vocabulary)
    - `IDENTITY_FRONTMATTER_KEYS=( type scope name role department manager email created updated tags )` — ten keys in canonical order
    - `PREFERENCES_FRONTMATTER_KEYS=( type scope created updated tags )` — five keys in canonical order
    - `IDENTITY_BODY_HEADINGS=( '# Identity' '## Name' '## Role' '## Department' '## Manager' '## Email' '## Work Scope' '## Key References' )`
    - `PREFERENCES_BODY_HEADINGS=( '# Preferences' '## Communication Style' '## Tooling' '## Meeting Cadence' '## Working Hours' '## AI Assistant' )`
    - `MIN_BYTES=200`, `MAX_BYTES=2048` — byte-budget lower and upper bounds per AC8
    - `STORY_3_1_TEMPLATE_FILES` + `STORY_3_1_TEMPLATE_BYTES` — copy the nine-entry + nine-entry positional-mapping arrays verbatim from Story 3.2 harness (AC9 invariance)
    - `STORY_3_2_OBSIDIAN_FILES=( app.json appearance.json community-plugins.json core-plugins.json daily-notes.json graph.json templates.json )` — seven entries (AC9 invariance; assert existence + non-empty, not byte-count — byte counts vary by emit style, so we rely on Story 3.2's harness to own the detailed shape invariance via `task6` regression)
  - [x] Implement `regex_self_probe()` that exercises:
    - Banned-term regex: `derek` + `smith` → positive; `derekson` → boundary-rejected; `personal` + `note` → positive; `personally` → boundary-rejected (two-token positive+negative coverage matching Stories 3.1 / 3.2)
    - Placeholder-allowlist bash-array membership: `{{employee_name}}` → hit; `{{Meeting Title}}` → miss (identity-file semantic check; note-shape token is not allowlisted for Story 3.3 context)
    - Fail-fast `fail "regex probe: ..."` on mismatch.
  - [x] `check_task1` — require `BASELINE_AUDIT_PATH` exists, contains title `# Story 3.3 Baseline Audit`, and contains each required section header (`gtd-life me/ source inventory`, `Per-file frontmatter + heading map`, `Banned-term scan of source files`, `Derek-specific fixed-string scan of source files`, `Out-of-scope files and subdirectories`, `Content classes to scrub vs retain`, `Mapping: source path → target path`).
  - [x] `check_task2` — require `BLUEPRINT_PATH` exists, contains title `# Story 3.3 Canonical Blueprint`, contains one section per target file (two) plus `## Placeholder vocabulary lock`, `## Banned-term lock`, `## Forbidden-form lock` sections.
  - [x] `check_task3` — per-file shape verification:
    - AC1 — directory count: `ls -A "${ME_DIR}" | wc -l | tr -d '[:space:]'` equals `2`.
    - For each target file (`IDENTITY_MD`, `PREFERENCES_MD`): assert `[[ -f <path> ]]`, `[[ -s <path> ]]`, trailing newline via `tail -c 1 | od -An -tx1 | tr -d '[:space:]'` equals `0a`, first-3-bytes equals `---\n` via `head -c 3 | tr -d '[:space:]'` equals `---`.
    - AC8 byte budgets: `wc -c` returns a value in `[MIN_BYTES, MAX_BYTES]` for each file.
    - AC8 LF-only line endings: `grep -c $'\r' <file>` returns `0`.
    - AC2 `identity.md` frontmatter: walk the first `---`/`---` block with `awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}'` to extract the frontmatter body; assert each of the ten keys in `IDENTITY_FRONTMATTER_KEYS` appears on its own line via `grep -Fq "^<key>:"` (anchored with `awk` line-walk since `grep -F` doesn't anchor; use `awk '/^type:/{found=1}...'` or equivalent). Assert literal `type: identity` and `scope: work` and `tags: [identity, work]` (or YAML-equivalent) are present; assert ten identity-placeholder-bearing lines match the five `{{employee_*}}` placeholders (`name`, `role`, `department`, `manager`, `email` keys each contain their respective `{{employee_*}}` token).
    - AC4 `preferences.md` frontmatter: analogous — five keys in order, `type: preferences`, `scope: work`, `tags: [preferences, work]`, zero `{{…}}` tokens in frontmatter.
    - AC3 `identity.md` body headings: assert each of the eight `IDENTITY_BODY_HEADINGS` appears as a standalone line via `grep -Fxq`; assert `work context only` literal substring is present in body.
    - AC5 `preferences.md` body headings: assert each of the six `PREFERENCES_BODY_HEADINGS` appears as a standalone line; assert each of the five MCP names (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`) is present via `grep -Fq`.
    - AC9 Story 3.1 invariance: loop `STORY_3_1_TEMPLATE_FILES` / `STORY_3_1_TEMPLATE_BYTES` by index and assert `wc -c < <file>` equals the expected byte count (copy the Story 3.2 harness's `check_task3` AC11 block verbatim).
    - AC9 Story 3.2 invariance: loop `STORY_3_2_OBSIDIAN_FILES` and assert each exists and is non-empty under `memory/.obsidian/`; assert `memory/.obsidian/workspace.json` does NOT exist; assert `memory/.obsidian/plugins/` does NOT exist (byte-level invariance is enforced by Story 3.2's own harness running in `task6` regression, so this gate checks shape only to avoid double-ownership of the invariant).
    - AC1 forbidden-sentinel block: loop `.gitkeep .keep empty placeholder` patterns under `${ME_DIR}` via `find -type f -name` and fail on any match.
    - AC1 subdirectory block: assert `find "${ME_DIR}" -mindepth 1 -type d | head -n 1` returns empty (no subdirectories).
    - AC9 `memory/.gitkeep` invariance: `wc -c < "${MEMORY_DIR}/.gitkeep"` equals `0`.
  - [x] `check_task4` — cross-file scrub:
    - Banned-term regex scan per file (`IDENTITY_MD`, `PREFERENCES_MD`): `grep -iE "${BANNED_TERMS_REGEX}"` returns zero matches (AC7).
    - Derek fixed-string scans: loop `DEREK_FIXED_STRINGS` and assert `grep -Fi` returns zero matches per file (AC7 defence-in-depth).
    - Path-reference fixed-string scans: `gtd-life`, `/Users/`, `Public/`, `~/` — zero matches per file (AC7 + AC14).
    - Placeholder extraction (AC6): `grep -oE '\{\{[^}]+\}\}' <file>` → for `identity.md`, every extracted token must be a member of `IDENTITY_PLACEHOLDER_ALLOWLIST` (assert via a bash-function `is_in_array token array_name` helper); for `preferences.md`, the extraction must return zero tokens (AC5 reinforcement).
    - Forbidden-form probes (AC6): angle-bracket `<name>` → zero matches (exception: `<!-- comment -->` HTML comments are permitted — scan for `<[A-Za-z_][A-Za-z0-9_]*>` pattern, not `<!--`); percent-wrapped `%name%` → zero; dollar-brace `${name}` → zero; single-brace `{name}` (not double) — use `grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}'` to catch `{foo}` while double-brace probe uses `\{\{…\}\}`.
    - `personal`-in-tags probe: `grep -Eq '^tags:.*personal' <file>` → zero matches per file (AC2 / AC4 tags assertion backstop).
  - [x] `check_task5` — self-check. Assert `head -n 1` equals `#!/usr/bin/env bash`; assert `grep -Fq 'set -euo pipefail'`; assert every case arm present (`task1)`–`task6)` and `all)`); assert each declared constant name appears (`ME_DIR=`, `IDENTITY_MD=`, `PREFERENCES_MD=`, `BASELINE_AUDIT_PATH=`, `BLUEPRINT_PATH=`, nine `STORY_*_HARNESS=`, `BANNED_TERMS_REGEX=`, `DEREK_FIXED_STRINGS=`, `IDENTITY_PLACEHOLDER_ALLOWLIST=`, `IDENTITY_FRONTMATTER_KEYS=`, `PREFERENCES_FRONTMATTER_KEYS=`, `IDENTITY_BODY_HEADINGS=`, `PREFERENCES_BODY_HEADINGS=`, `MIN_BYTES=`, `MAX_BYTES=`, `STORY_3_1_TEMPLATE_FILES=`, `STORY_3_1_TEMPLATE_BYTES=`, `STORY_3_2_OBSIDIAN_FILES=`); assert `declare -F regex_self_probe >/dev/null 2>&1` (Story 2.4 F4 + Stories 3.1 / 3.2 precedent).
  - [x] `check_task6` — regression. Arg tuple per harness: `"HARNESS_PATH|display_name|expected_pass_count"`. For each of the nine predecessor harness paths, `require_file_exists` and invoke `bash "${harness}" all 2>&1`. Capture combined stdout/stderr. Count `^PASS:` lines via `grep -c '^PASS:'` and compare to the expected-count fingerprint: `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7` for Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2. Echo captured output on non-zero exit or count mismatch per Story 2.2 Phase 4 F6 + Stories 3.1 F7 / 3.2 pattern; `fail` with sub-harness name on any violation.
  - [x] Implement the `mode` dispatcher: `case "${mode}" in task1) check_task1 ;; ... task6) check_task6 ;; all) check_task1; echo "PASS: task1"; ...; check_task6; echo "PASS: task6" ;; *) fail "unknown mode: ${mode}" ;; esac`; end with `echo "PASS: ${mode}"`. Under `all` mode emits exactly 7 `^PASS:` lines.
  - [x] Add header comment block stating: (a) Story 3.3 is the empty identity + preferences scaffolding under `memory/me/`; (b) scope is two markdown files with `scope: work` frontmatter and five identity-placeholder tokens; (c) gtd-life `me/` sources are REBUILT FROM SCAFFOLD, not ported verbatim (distinct from Story 3.2 port method); (d) regression chain extends Story 3.2's eight-harness chain by one (adds Story 3.2 as the ninth predecessor); (e) the Story 1.1 allowlist at line 155 requires ZERO amendment (Story 2.1 commit `0db273b` already admits `me`; AC10 codifies this invariant).

- [x] Task 5 — Run the full 10-harness regression and capture the transcript (AC: 11, 12) **[Sequential — depends on Task 4 harness existing and Tasks 3a / 3b files landed]**
  - [x] Confirm NO edit to `story-1-1-scaffold-validation.sh` line 155 (or any other line) is required or applied. Verify via `diff` against a pre-Task-5 baseline (or `git diff --stat _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` returns zero lines). AC10 encodes this invariant.
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh all`. Capture the full transcript. Expect `PASS: task1` → `PASS: task6` → `PASS: all`, exit 0, exactly 7 `^PASS:` lines.
  - [x] Re-run each of the nine predecessor harnesses individually in `all` mode (`1.1`, `1.2`, `1.3`, `2.1`, `2.2`, `2.3`, `2.4`, `3.1`, `3.2`). All nine must exit `0` with `PASS: all`. Verify the per-harness `^PASS:` line-count fingerprint matches `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7`.
  - [x] Capture the full command-and-transcript log for inclusion in the Task 6 handoff artifact.

- [x] Task 6 — Handoff readiness package (AC: 11, 12, 14) **[Sequential — depends on Task 5]**
  - [x] Persist `_bmad-output/implementation-artifacts/tests/story-3-3-task6-handoff.md` with: (a) AC-to-file map (one row per AC pointing at the harness gate, file path, or grep output that proves it); (b) full validation command transcript (Story 3.3 harness + nine regression harnesses — 10 harnesses total); (c) byte-counts and SHA-256 checksums of the two authored markdown files (for future drift detection); (d) forward-looking notes: Epic 4 Story 4.1 will reference `memory/me/identity.md` + `memory/me/preferences.md` context in `.cursor/mcp.json` documentation (not edit them); Epic 5 Story 5.2 (wizard) will rewrite the five identity placeholders with user answers from `prompts` (name, email, role, department, manager) and update `created: YYYY-MM-DD` / `updated: YYYY-MM-DD` to the current date; Epic 6 Story 6.2 can invoke this harness as a CI gate; Epic 3 closes with this story — `epic-3.status` flips from `in-progress` to `done` when Story 3.3 reaches `done` (AC13).
  - [x] Include a "zero-edit verification" block listing each of the nine predecessor harnesses (asserted byte-stable — no Story 1.1 allowlist amendment needed, distinct from Stories 3.1 / 3.2 precedent), the four Story 2.2 rule files, Story 2.1 `agent-identity.mdc`, Story 2.3 `agents/personas/work.md`, the nine Story 3.1 template files, the seven Story 3.2 `.obsidian/` JSON files, the root context files, `README.md`, `LICENSE`, `.gitignore`, `memory/.gitkeep` — each asserted present, non-empty where appropriate, and (for the Story 3.1 templates and Story 3.2 JSON files) byte-for-byte identical to the respective predecessor-story Task 6 handoff fingerprint.
  - [x] Explicitly document the `story-1-1-scaffold-validation.sh` zero-edit invariant as a non-exception, referencing Story 2.1 commit `0db273b` (which anticipatorily added `me|mcp|obsidian`) as the forward-compatibility mechanism that obviates a Story-3.3-specific amendment. This is the first Epic 3 story that does NOT require a Story 1.1 allowlist extension.

- [x] Task 7 — Sprint tracker and story status synchronization (AC: 13) **[Independent; typically last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `3-3-seed-empty-identity-and-preferences.status` from `backlog` to `ready-for-dev` during Phase 1 (SM pass); then to `review` at Dev handoff; then to `done` at Phase 3 review approval. Single `backlog → review` on-disk transition acceptable per Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 autonomous-swarm precedent.
  - [x] Preserve `epic-3.status` at `in-progress` through Phases 1 and 2; flip to `done` at Phase 3 review approval (Story 3.3 is the final Epic 3 story; Stories 3.1 and 3.2 are already `done`).
  - [x] Update `last_updated` in `sprint-status.yaml` to `2026-04-20` on the Phase 1 edit.
  - [x] Preserve every comment, blank line, inline spacing, and entry ordering byte-for-byte. The only diff between pre-edit and post-edit files must be the `status:` value changes for `3-3-…` (once at each of three phases) plus the `epic-3.status` flip at Phase 3 plus the `last_updated` value change.

## Dev Notes

### Artifact availability

- Planning / tracking artifacts used by this story:
  - `_bmad/bmm/config.yaml` (BMAD v6.3.0; `user_name: Vixxo Employee`; `planning_artifacts` / `implementation_artifacts` path variables).
  - `_bmad-output/planning-artifacts/epics.md` — Epic 3 Story 3.3 AC at lines 276–286; Epic 3 overview at lines 252–286.
  - `_bmad-output/planning-artifacts/architecture.md` — 26 lines. Confirms template-only scope, macOS/Linux portability, `{{employee_name}}` / `{{employee_role}}` placeholder-driven identity-fields convention (architecture.md line 23 names these two tokens explicitly — Story 3.3 extends the set to five by adding `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}` per Story 2.1 / 2.3 precedent), secrets-via-.gitignore discipline.
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — story key `3-3-seed-empty-identity-and-preferences`, Linear `AIP-41`, current status `backlog`; `epic-3.status: in-progress` (Story 3.1 opened, Stories 3.1 + 3.2 now `done`); `last_updated: "2026-04-20"`.
  - Prior story files (all `done`): `1-1-…`, `1-2-…`, `1-3-…`, `2-1-…`, `2-2-…`, `2-3-…`, `2-4-…`, `3-1-…`, `3-2-portable-obsidian-config.md`. Pattern source for harness structure, banned-term regex discipline, POSIX-ERE boundary guards, Phase-4 F-series review-fix pattern, autonomous-swarm status-collapse convention, Story-3.2 F1–F7 review-fix harness idioms (`grep -o '":' | wc -l` occurrence counting, byte-budget upper bounds, STORY_3_1_TEMPLATE_BYTES positional fingerprint, stripped-literal `templates.json` assertion).
  - Existing identity-placeholder files (byte-stable during this story, read for placeholder vocabulary reference only): `.cursor/rules/agent-identity.mdc` (uses `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`) and `agents/personas/work.md` (uses all four plus is silent on `{{employee_email}}`).
  - gtd-life source reference (scrubbed / rebuilt during port): `~/Public/gtd-life/memory/me/identity.md` (Derek biography — REBUILD from scaffold) and `~/Public/gtd-life/memory/me/preferences.md` (Derek personal preferences — REBUILD from scaffold). Other `me/` siblings (`family.md`, `food-guide-queen-creek.md`, `ventures.md`, `properties.md`, `networking/`) are explicitly EXCLUDED — personal-life content with no work-template analogue.
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` — does not exist. Story 3.3 relies on epics.md + architecture.md + sprint-status.yaml + prior-story-file patterns for all requirements.
  - `_bmad-output/planning-artifacts/ux-design-specification.md` — does not exist. Story 3.3 has no UX surface (file-system markdown only), so absence is not a blocker.
  - `_bmad/bmm/workflows/4-implementation/bmad-create-story/template.md` — does not exist at the configured path. Story 3.3 uses the emergent shape from Stories 1.1 → 3.2 (Status + Story statement + ACs + Tasks/Subtasks + Dev Notes sub-sections + Change Log + Dev Agent Record + Review Follow-ups + Senior Developer Review).

### Epic 3 story partition (why 3.3 is "me/ skeletons only, wizard integration comes in Epic 5")

- **Story 3.1 (done):** Ported the empty per-directory `_template.md` / `_template/` tree (nine files) under `memory/`. Introduced the 17-token banned-term lock, the identity-placeholder / note-shape-placeholder separation, and the 7-harness regression-chain discipline.
- **Story 3.2 (done):** Ported the portable `memory/.obsidian/` config (seven JSON files) with `workspace.json` EXCLUDED and `templates.json` REPAIRED (`"_templates"` → `""`). Extended the regression chain to 8 harnesses. Introduced the `STORY_3_1_TEMPLATE_BYTES` positional fingerprint for downstream invariance checks.
- **Story 3.3 (this story):** Seed `memory/me/identity.md` and `memory/me/preferences.md` with `scope: work` frontmatter, five identity placeholders (`{{employee_name}}` / `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}` / `{{employee_email}}`), and placeholder-driven body prose. Extends the regression chain to 9 harnesses. Closes Epic 3 — `epic-3.status` flips to `done` at Phase 3 review approval.
- **Epic 5 Story 5.2 (backlog):** The `bin/init` setup wizard will rewrite the five identity placeholders with user answers (name, email, role) and update `created` / `updated` timestamps. Story 3.3 is the wizard's TARGET FILES; Story 5.2 is the wizard code. Story 3.3 does NOT invoke or depend on the wizard.

Story 3.3 is deliberately narrow. Its entire job is: "create the two target files the setup wizard will rewrite, with correct frontmatter shape + correct placeholder vocabulary + work-only scope + zero Derek content, and confirm all prior scaffolding remains byte-stable." The wizard (Epic 5), the MCP config (Epic 4), and the PII CI guardrail (Epic 6) are downstream.

### Why rebuild from scaffold rather than port verbatim + scrub (distinct from Story 3.2 port method)

The gtd-life `memory/me/identity.md` and `memory/me/preferences.md` files are **fully populated Derek content** — 2.5KB of biography (location, roles, career history, philosophy, interests, devices, professional identity prose) and 2.9KB of personal preferences (food guide references, Chiron AI name, personal tools, personal-context routing guardrails, device usage). Unlike Story 3.2's `.obsidian/` JSON sources — which are generic Obsidian defaults with one REPAIR needed — Story 3.3's sources are personal documents with zero reusable structure beyond "file has frontmatter + H1 + H2 sections."

**Port method inversion:** Story 3.3 discards the source content entirely and REBUILDS the two files from scaffolds that match the architecture.md `{{employee_*}}` placeholder-driven convention. The gtd-life sources are read in Task 1 (Baseline Audit) as a reference for "what shape an identity / preferences file can have" and as a catalog of "what must NOT appear in the port," not as a starting point to edit.

**Consequence:** Story 3.3's byte budgets are smaller than the gtd-life sources (200–2048 bytes vs 2500–2900 bytes), the structure is simpler (seven H2s vs eleven; five H2s vs eleven), and every line of body prose is authored fresh around the identity placeholders — not derived from any Derek sentence. The AC7 fixed-string scrub list (`Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `Playrix`, `Laurie`, `Deke`) is a defence-in-depth backstop that would catch any careless paste.

### Placeholder vocabulary (five tokens; Story 2.1 / 2.3 precedent extended by 1)

- `{{employee_name}}` — architecture.md-named; also used by `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md`
- `{{employee_role}}` — architecture.md-named; also used by agent-identity and work persona
- `{{employee_department}}` — introduced by Story 2.1 agent-identity.mdc; also used by work persona
- `{{employee_manager}}` — introduced by Story 2.1 agent-identity.mdc; also used by work persona
- `{{employee_email}}` — NEW for Story 3.3; Epic 5 Story 5.2 wizard prompts for email; the identity file is the natural home for it. Story 2.1 / 2.3 did not include `{{employee_email}}` because those files describe scope and persona, not contact info — `identity.md` describes who-the-employee-is which includes contact info. This extends the five-item identity-placeholder vocabulary already documented in `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` lines 451–455 (which lists all five including `{{employee_email}}` as a forward-looking reference to "Story 5.2 wizard scope").

No content-shape placeholders (`{{Name}}`, `{{Meeting Title}}`, etc.) appear in `memory/me/*.md` — that vocabulary is owned by Story 3.1 memory templates. The harness `check_task4` enforces this separation via the placeholder-allowlist extraction gate (AC6).

### Banned-term set for Story 3.3 (identical to Stories 3.1 / 3.2's 17-token lock)

Story 3.3 inherits the Stories 3.1 / 3.2 Phase-4-locked 17-token banned-term set verbatim. Zero new tokens added; zero tokens removed. Boundary-guarded regex: `(^|[^A-Za-z])TOKEN($|[^A-Za-z])`, case-insensitive via `grep -iE`.

**Carried forward from Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 (all 17 tokens):**

- `derek`, `neighbors` — Derek's name
- `revivago`, `flowtopic` — personal business tokens
- `benji` — personal task-system token
- `gtd-life`, `gtdlife` — source-repo reference
- `wyoming`, `cheyenne` — example PII location tokens
- `family`, `wife`, `son`, `daughter`, `dog` — family/personal-life tokens
- `home` — personal-life token
- `blog` — personal output channel
- `personal` (Story 3.1 Phase-4 F4 addition) — generic personal-scope token

**Story-3.3-specific fixed-string scans (ADDITIONAL defence-in-depth, NOT part of the 17-token regex):**

- `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke` — Derek-specific tokens that appear in the gtd-life source `me/*.md` files and must not port through. Fixed-string scans (`grep -Fi`) across both authored files. Not added to the 17-token regex because some of these strings (e.g. `Integrum` — a generic word meaning "whole" — or `Laurie` — a common first name) should not trigger false positives in future unrelated content; narrow-scope fixed-string enforcement in `memory/me/*.md` is appropriate.
- `gtd-life`, `~/Public/gtd-life`, `Public/gtd-life`, `/Users/` — path-reference fixed-string scans carried forward from Stories 3.1 / 3.2.

The harness MUST reject any of the 17 regex tokens (boundary-guarded, case-insensitive) in either authored file, AND any of the additional fixed-string probes above.

### Markdown-shape discipline (no YAML parser, no `yq` — grep + awk probes only)

The project architectural constraint forbids introducing new dependencies. `yq` is not POSIX-ubiquitous (macOS ships without it; GitHub Actions `macos-latest` requires `brew install yq`). The harness uses the same discipline as Story 3.1's frontmatter-verification approach:

- **Frontmatter block delimitation:** `head -c 3 <file>` equals `---`; walk `awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}'` to extract the body of the first `---`/`---` block.
- **Key presence within frontmatter:** For each expected key in the canonical-order array, assert a line matching `^<key>:` appears in the extracted frontmatter body. Use `awk` for line-anchored matching since `grep -Fq` doesn't anchor.
- **Key-value literal assertions:** `grep -Fq '"type: identity"'` for string literals, `grep -Fq 'scope: work'` for bare-string literals. Matches the Story 3.1 Phase-4 F5 frontmatter-key-value helper pattern.
- **Body-heading anchored assertions:** `grep -Fxq '<heading>'` (the `-x` flag anchors the match to the full line, preventing partial matches like `## Name` accidentally matching `## Names of tools`).
- **Placeholder extraction:** `grep -oE '\{\{[^}]+\}\}' <file>` emits all matched tokens on separate lines; loop and membership-test against the five-entry bash array.
- **Byte budget:** `wc -c < <file>` returns an integer; bash arithmetic `[[ <n> -ge 200 ]] && [[ <n> -le 2048 ]]` validates bounds.
- **Line-ending check:** `grep -c $'\r' <file>` — match-count of literal CR byte; must equal `0`.

This discipline avoids adding `yq` or any YAML parser. It is shape-verification, not semantic YAML validation — a file that is valid YAML but has the wrong structure will be caught by the key-presence probes; a file that is malformed YAML but happens to contain the right substrings will be caught by the first-3-bytes + closing `---` probe. Obsidian and the Cursor / Claude agents are the semantic validators — if the shape passes all probes, they will read the files correctly.

### Previous story learnings to carry forward

- **POSIX-ERE boundary guards** (Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2): `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` works on macOS BSD grep, GNU grep, and busybox/Alpine grep identically. Do NOT use `\b`, `\<`, `\>`, or Perl-compatible regex.
- **`regex_self_probe` fail-fast** (all prior stories): probe must exercise BOTH a positive case (token matches) and a negative case (boundary-embedded substring does not match) for at least one token. Story 3.3 exercises at least two tokens (`derek` + `derekson`; `personal` + `personally`) in both directions, AND one placeholder-allowlist probe (`{{employee_name}}` → allowlist hit; `{{Meeting Title}}` → allowlist miss).
- **Phase 4 F6 sub-harness capture** (Story 2.2): `check_task6` regression gate must capture combined stdout/stderr (`2>&1`) when invoking sub-harnesses, echo the captured output on non-zero exit, and fail with the sub-harness name.
- **Phase 4 F7 PASS-count fingerprint** (Stories 3.1 / 3.2): `check_task6` MUST assert exact `^PASS:` line count per sub-harness, not just non-zero exit. Empirical counts for Story 3.3 regression chain (measured 2026-04-20): `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7` for Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2.
- **Phase 4 F1 allowlist-exception codification** (Stories 3.1 / 3.2): when a predecessor harness needs a one-line additive extension to accept new downstream scaffold, the extension is classified as an integration fix following Story 2.1 commit `0db273b` precedent, and the current story's ACs must codify the exception explicitly. **Story 3.3 INVERTS this: no allowlist extension is needed because Story 2.1's commit `0db273b` already admitted `me` forward-compatibly. AC10 codifies the zero-edit invariant.** This is the first Epic-3 story that does not require a Story 1.1 allowlist extension.
- **Phase 4 F2 per-directory exact-count assertions** (Story 3.1 / 3.2): `check_task3` must assert exact file count per scaffolded directory. Story 3.3 asserts `ls -A memory/me/ | wc -l` equals `2`.
- **Phase 4 F3 sentinel invariance** (Stories 3.1 / 3.2): `check_task3` must assert `memory/.gitkeep` is 0 bytes AND no new `.gitkeep|.keep|empty|placeholder` sentinels exist under the newly-scaffolded subdirectory.
- **Phase 4 F4 `personal` banned token** (Stories 3.1 / 3.2): the 17-token lock is inherited verbatim. No new banned tokens for Story 3.3.
- **Phase 4 F5 discriminator-value assertions** (Story 3.1): `assert_frontmatter_key_value` pattern — for `type: identity` / `type: preferences` / `scope: work` assertions.
- **Story 3.2 F3 `grep -o '":' | wc -l` occurrence counting** (Story 3.2 review fix): not directly applicable to Story 3.3 (no JSON files), but the equivalent for markdown key-count is `grep -c '^<key>:' <file>` on the extracted frontmatter body — `grep -c` counts MATCHING LINES which is safe for YAML (one key per line).
- **Story 3.2 F4 positional-fingerprint byte-count arrays** (Story 3.2 review fix): Story 3.3 reuses `STORY_3_1_TEMPLATE_BYTES` verbatim for AC9 Story 3.1 invariance. Story 3.3 does NOT introduce a `STORY_3_2_OBSIDIAN_BYTES` equivalent — Story 3.2's own harness (running in `task6` regression) already enforces that invariance byte-for-byte, and duplicating it in Story 3.3 would violate single-source-of-truth. Story 3.3 checks only Story 3.2 file existence + non-empty, relying on `task6` regression for deeper invariance.
- **Autonomous-swarm status collapse** (all prior): `backlog → ready-for-dev → review → done` may collapse to a single on-disk `backlog → review` or `backlog → done` transition. Record the skipped hops in the Change Log.
- **Story 2.4 F4 `declare -F` probe presence** (inherited by Stories 3.1 / 3.2): `check_task5` probe presence check uses `declare -F <function_name> >/dev/null 2>&1`, not `grep -Fq '<function_name>'`.
- **Additive-only discipline** (Story 2.4 AC8, Stories 3.1 / 3.2): Story 3.3 may create new files only under `memory/me/` + `_bmad-output/implementation-artifacts/tests/` + this story file. Any other edit is a regression. Zero harness edits required (AC10).
- **Commit-message shape** (Epic 1 / 2 / 3 git log): `feat(epic-N): <change> (Story <key>)`. Story 3.3's commit should read `feat(epic-3): seed empty identity and preferences (Story 3-3-seed-empty-identity-and-preferences)`. The epic-closing commit on Phase 3 (Story 3.3 → done + epic-3 → done) may read `feat(epic-3): close Epic 3 memory vault scaffold (Story 3-3-seed-empty-identity-and-preferences)` at Dev's discretion.

### Architectural constraints

- **No runtime service, no application code.** Story 3.3 is pure file-system scaffolding plus a shell harness. No Node, no Python, no web surface. The markdown files are read by Obsidian, Cursor, and Claude Code — not by runtime code in this template.
- **No new dependencies.** `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`, `mkdir` are universally available on macOS and Linux developer machines and on `ubuntu-latest` / `macos-latest` CI images. Do not introduce `jq`, `yq`, `rg`, `node`, `python`, or any other tool that is not POSIX-ubiquitous.
- **macOS / Linux portability.** POSIX-bash-3.2 compatible (macOS default `/bin/bash` is 3.2 without `brew install bash`). BSD-grep and GNU-grep compatible. No `find -printf` (GNU-only); no `readlink -f` (GNU-only).
- **No shell-state mutation.** No `shopt -s nocaseglob`, no `LANG=` reassignment, no `export LC_ALL=`. Case-insensitive logic is per-invocation via `grep -i`.
- **UTF-8 files with trailing newline, LF line endings.** Every emitted markdown file is UTF-8, ends with a single `\n`, has no CRLF line endings (LF only).
- **`.gitignore` contract preserved.** `memory/` is NOT in `.gitignore`; `memory/me/identity.md` and `memory/me/preferences.md` ARE committed to git. This is correct — they are portable scaffolds with identity-placeholder tokens, not secrets. The Epic 5 wizard will rewrite these locally after clone; rewritten content may or may not be committed (that's the employee's choice and is governed by Epic 6 PII CI guardrail).
- **Obsidian-vault integration.** Both files are under the Obsidian vault root (`memory/`). The Templates plugin in `memory/.obsidian/core-plugins.json` is enabled. The Properties plugin is enabled, which means Obsidian will render the frontmatter as a property panel — the canonical key order in AC2 / AC4 determines the property-panel ordering. The `scope: work` property (lowercase string) will render as a tag-like property in the sidebar, reinforcing the work-only declaration visually.
- **Placeholder-driven identity-fields (architecture.md line 23).** Architecture.md names `{{employee_name}}` and `{{employee_role}}` explicitly. Story 2.1 (agent-identity rule) and Story 2.3 (work persona) extended the set to four (+ `{{employee_department}}`, `{{employee_manager}}`). Story 3.3 extends to five (+ `{{employee_email}}`). The five-item vocabulary is now the project canonical set.

### Project Structure Notes

- **Target files for this story (new — 6 files total):**
  - Memory-me files (2):
    - `memory/me/identity.md`
    - `memory/me/preferences.md`
  - Test evidence (4):
    - `_bmad-output/implementation-artifacts/tests/story-3-3-baseline-audit.md`
    - `_bmad-output/implementation-artifacts/tests/story-3-3-canonical-blueprint.md`
    - `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` (executable, 0755)
    - `_bmad-output/implementation-artifacts/tests/story-3-3-task6-handoff.md`
- **Target files for this story (modified — 2 files):**
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (`3-3-seed-empty-identity-and-preferences.status` flips, `epic-3.status` flip at Phase 3, `last_updated` update)
  - This story file (Dev Agent Record / Change Log / File List / checkboxes at Dev handoff and Phase 3 review approval)
- **Zero files modified outside the working set.** In particular `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` is NOT edited (AC10 zero-edit invariant — distinct from Stories 3.1 / 3.2 which each added one line).
- **Directory state expectations AFTER Story 3.3 lands:**
  - `memory/` contains `.gitkeep` (from Story 1.1, 0 bytes unchanged), six Story 3.1 subdirs (`meetings/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/`, all with Story 3.1 templates byte-stable), the Story 3.2 `.obsidian/` subdir (seven JSON files byte-stable), plus the NEW `me/` subdir. No `companies/`, no `daily/`, no `blog-ideas/`, no `vixxo/`, no `_templates/` — those are out of scope.
  - `memory/me/` contains exactly two files: `identity.md`, `preferences.md`. No subdirectories (`networking/` from gtd-life source is out of scope). NO `.gitkeep`, NO `*.bak`, NO `*.log`, NO `.DS_Store`.
  - All Story 1.x / 2.x / 3.1 / 3.2 artifacts remain byte-for-byte stable.
  - `story-1-1-scaffold-validation.sh` remains byte-for-byte stable (distinct from Stories 3.1 / 3.2).
- **Forward-compatibility:**
  - Epic 4 Story 4.1 / 4.4 (mcp.json, docs) reference `memory/me/identity.md` + `memory/me/preferences.md` context paths but do NOT edit them. Independent of Story 3.3 shape.
  - Epic 5 Story 5.2 (wizard) is the primary consumer. It will:
    - Read `memory/me/identity.md` and `memory/me/preferences.md` as templates.
    - Prompt for employee name, email, role (plus department + manager from the persona scope).
    - Rewrite the five identity placeholders with user answers.
    - Update `created: YYYY-MM-DD` and `updated: YYYY-MM-DD` to the current ISO-8601 date.
    - Leave the rest of the file untouched.
  - Epic 5 Story 5.3 (wizard skills install) is downstream of 5.2 and does not touch these files.
  - Epic 6 Story 6.2 (GitHub Action) can invoke `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh all` directly as a CI gate — harness contract is GitHub-Actions-native (exit 0 on pass, 1 on fail, exactly 7 `^PASS:` lines). The CI gate runs BEFORE the wizard in pre-commit mode to catch template drift; it runs AFTER the wizard in post-clone mode only if the repo maintainer chooses to.
  - Epic 3 closure: with Story 3.3 `done`, Epic 3 status flips from `in-progress` to `done` (the final transition of the Epic 3 lifecycle).
  - User-facing Obsidian behavior on first open: file-explorer shows `memory/me/identity.md` and `memory/me/preferences.md` alongside the six Story 3.1 subdirs. Properties plugin renders `scope: work`, `tags: [identity, work]` / `[preferences, work]` visually. Graph view shows the two files with no forward-links (they defer to rule files, which are outside the vault). Daily-notes plugin is unaffected.

### Testing Notes

- **Suggested manual smoke commands (post-authoring, pre-harness):**
  - `ls memory/me/` (expect: `identity.md preferences.md`)
  - `ls memory/me/ | wc -l | tr -d ' '` (expect: `2`)
  - `head -c 3 memory/me/identity.md` (expect: `---`)
  - `head -c 3 memory/me/preferences.md` (expect: `---`)
  - `grep -Fq 'scope: work' memory/me/identity.md && echo "identity scope work"` (expect: matches)
  - `grep -Fq 'scope: work' memory/me/preferences.md && echo "preferences scope work"` (expect: matches)
  - `grep -Fxq '# Identity' memory/me/identity.md` (expect: matches)
  - `grep -Fxq '# Preferences' memory/me/preferences.md` (expect: matches)
  - `grep -oE '\{\{[^}]+\}\}' memory/me/identity.md | sort -u` (expect: exactly the five `{{employee_*}}` tokens, no others)
  - `grep -oE '\{\{[^}]+\}\}' memory/me/preferences.md | wc -l | tr -d ' '` (expect: `0`)
  - `grep -riE '(^|[^A-Za-z])(derek|revivago|benji|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])' memory/me/` — expect empty output
  - `grep -rF 'gtd-life' memory/me/` — expect empty output
  - `grep -rFi 'Chiron' memory/me/` — expect empty output
  - `grep -rFi 'MasteryLab' memory/me/` — expect empty output
  - `grep -rFi 'Queen Creek' memory/me/` — expect empty output
  - `wc -c memory/me/identity.md memory/me/preferences.md` (expect: both in `[200, 2048]`)
  - `tail -c 1 memory/me/identity.md | od -An -tx1 | tr -d ' \n'` (expect: `0a`)
  - `tail -c 1 memory/me/preferences.md | od -An -tx1 | tr -d ' \n'` (expect: `0a`)
  - `diff _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh <(git show HEAD:_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh) | wc -l` (expect: `0` — zero bytes changed, AC10 invariant)
- **Harness invocation:**
  - `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh all` — expect `PASS: task1` → `PASS: task6` → `PASS: all`, exit `0`, exactly 7 `^PASS:` lines.
  - `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh task3` — exercises the two-file shape verification in isolation.
  - `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh task4` — exercises the cross-file scrub in isolation.
- **Regression (each must exit 0 with `PASS: all`; per-harness `^PASS:` line count in parens):**
  - `bash story-1-1-scaffold-validation.sh all` (1)
  - `bash story-1-2-root-files-validation.sh all` (1)
  - `bash story-1-3-root-context-validation.sh all` (1)
  - `bash story-2-1-agent-identity-validation.sh all` (1)
  - `bash story-2-2-guardrail-and-formatting-validation.sh all` (10)
  - `bash story-2-3-work-persona-validation.sh all` (7)
  - `bash story-2-4-benji-inbox-absence-validation.sh all` (7)
  - `bash story-3-1-memory-template-tree-validation.sh all` (7)
  - `bash story-3-2-obsidian-config-validation.sh all` (7)
- **Self-contained harness:** no network, no external tools beyond `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`.

### Parallelization guidance

- **Task 1 (baseline audit) || Task 2 (canonical blueprint)** — both are pure-write operations against distinct evidence files (`story-3-3-baseline-audit.md` vs `story-3-3-canonical-blueprint.md`). No runtime coupling. A Dev swarm runs them concurrently in two subagents.
- **Tasks 3a / 3b (author identity.md and preferences.md)** are pairwise parallelizable AFTER Task 2 lands the blueprint. Each task writes to a disjoint file path under `memory/me/`:
  - 3a writes `memory/me/identity.md`
  - 3b writes `memory/me/preferences.md`

  No shared-file contention across 3a / 3b. A Dev swarm may run both concurrently. The directory `memory/me/` is created idempotently via `mkdir -p` by whichever task runs first.
- **Task 4 (harness)** is sequential — must run AFTER Task 2 (blueprint encoded as constants in the harness) AND AFTER Tasks 3a / 3b (so `check_task3` has files to verify).
- **Task 5 (regression)** is sequential — runs AFTER Task 4 harness exists. Notably does NOT apply any integration fix (AC10 zero-edit invariant), distinguishing it from Stories 3.1 / 3.2 Task 5.
- **Task 6 (handoff)** is sequential — depends on Task 5 transcript.
- **Task 7 (sprint tracker)** is independent; Phase-1 edit flips status at story-creation time (SM pass), Phase-2 edit at Dev handoff, Phase-3 edit (including `epic-3.status` flip) at review approval.
- **Shared-file contention across the whole plan:**
  - Task 1 writes `story-3-3-baseline-audit.md` (unique).
  - Task 2 writes `story-3-3-canonical-blueprint.md` (unique).
  - Tasks 3a / 3b write two distinct markdown paths under `memory/me/` (no overlap).
  - Task 4 writes `story-3-3-identity-preferences-validation.sh` (unique).
  - Task 5 runs read-only regression; no file writes (distinct from Stories 3.1 / 3.2 Task 5 which wrote a one-line edit to `story-1-1-scaffold-validation.sh`).
  - Task 6 writes `story-3-3-task6-handoff.md` (unique).
  - Task 7 modifies `sprint-status.yaml` (exclusive write).
  - This story file is written by Task 7 (SM-pass edits) and by the Dev swarm (handoff + Phase 3 edits); serialize story-file writes per phase.

**Swarm parallelization summary (MOST IMPORTANT — orchestrator uses this to launch parallel dev agents):**

- **Parallel wave 1 (independent evidence artifacts):** Task 1 || Task 2 — two subagents, no coupling.
- **Parallel wave 2 (independent markdown authoring; 2-way fan-out):** Task 3a || Task 3b — two subagents, each writing to disjoint markdown paths. Depends on wave 1 complete (Task 2 blueprint available).
- **Sequential after wave 2:** Task 4 (harness) → Task 5 (regression, zero-edit verified) → Task 6 (handoff).
- **Independent throughout:** Task 7 (sprint tracker) — run at Phase 1 (SM pass), Phase 2 (Dev handoff), Phase 3 (review approval with epic-3 closure).

### References

- `_bmad/bmm/config.yaml` — BMAD module metadata and artifact path variables.
- `_bmad-output/planning-artifacts/epics.md` lines 276–286 — Epic 3 Story 3.3 statement and acceptance criteria (source of truth).
- `_bmad-output/planning-artifacts/epics.md` lines 252–286 — Epic 3 overview and Stories 3.1 / 3.2 / 3.3 relationship.
- `_bmad-output/planning-artifacts/architecture.md` lines 1–26 — portability, secret-management, no-new-deps discipline; line 23 identity-placeholder convention (`{{employee_name}}`, `{{employee_role}}`).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` lines 103–120 — Epic 3 block (Stories 3.1 / 3.2 `done`, Story 3.3 `backlog`; `epic-3.status: in-progress`).
- `_bmad-output/implementation-artifacts/3-2-portable-obsidian-config.md` — Story 3.2 canonical precedent: 17-token banned-term lock, 8-harness regression chain (from Story 3.3's perspective), Phase-4 F1/F2/F3/F4/F5/F7 review-fix patterns, integration-fix exception codification (which Story 3.3 INVERTS to a zero-edit invariant), per-directory count assertions, sentinel invariance, PASS-count fingerprints, `STORY_3_1_TEMPLATE_BYTES` positional fingerprint array.
- `_bmad-output/implementation-artifacts/3-1-port-template-trees-from-gtd-life-memory.md` — Story 3.1 canonical precedent: 17-token banned-term lock introduction, identity-placeholder vs note-shape-placeholder separation, `{{employee_*}}` five-item allowlist (including `{{employee_email}}` as a forward-looking reference to Story 5.2 wizard scope), forbidden-bracket-form discipline.
- `_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md` — Story 2.3 persona-file precedent: five-MCP active set (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`), four-item identity-placeholder usage (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`), `scope: work` frontmatter discipline.
- `_bmad-output/implementation-artifacts/2-1-port-agent-identity-rule-generic.md` — Story 2.1 agent-identity-rule precedent: anticipatory Story 1.1 allowlist extension (commit `0db273b` added `me|mcp|obsidian` to line 155), four-item identity-placeholder vocabulary, `work context only` scope declaration.
- `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh` — direct harness model: gate naming, constant declaration style, `regex_self_probe` pattern, `check_task6` per-harness spec-loop fingerprint, forbidden-form probes, `STORY_3_1_TEMPLATE_BYTES` positional-fingerprint-array idiom.
- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` — blueprint authoring style to mirror (section headers, key-order locks, banned-term lock block, placeholder allowlist block — Story 3.3 restates the five-item identity-placeholder allowlist with `{{employee_email}}` as the NEW entry for this story's scope).
- `_bmad-output/implementation-artifacts/tests/story-3-2-task6-handoff.md` — handoff-artifact structure to mirror (AC-to-evidence map, regression transcript, SHA-256 fingerprint table, forward-looking notes, zero-edit verification, integration-fix exception documentation — Story 3.3 handoff inverts to document the zero-edit non-exception).
- `.cursor/rules/agent-identity.mdc` — reference for identity placeholder usage and `## Key References` list content (Story 3.3 identity.md reuses the same Key References list).
- `agents/personas/work.md` — reference for persona frontmatter shape and five-MCP active set (Story 3.3 preferences.md reuses the same Tooling section content).
- `~/Public/gtd-life/memory/me/identity.md` — gtd-life source reference (REBUILD from scaffold; do NOT port verbatim; read for "what shape an identity file can have" only).
- `~/Public/gtd-life/memory/me/preferences.md` — gtd-life source reference (REBUILD from scaffold; do NOT port verbatim; read for "what shape a preferences file can have" only).
- `~/Public/gtd-life/memory/me/family.md`, `food-guide-queen-creek.md`, `ventures.md`, `properties.md`, `networking/` — gtd-life source siblings (EXCLUDED — personal-life content with no work-template analogue).
- Git log (`git log --oneline -n 20`) — Epic 1 / 2 / 3 commit style `feat(epic-N): <change> (Story <key>)`. Story 3.3's commit should read `feat(epic-3): seed empty identity and preferences (Story 3-3-seed-empty-identity-and-preferences)`. The Phase-3 epic-closing commit may read `feat(epic-3): close Epic 3 memory vault scaffold (Story 3-3-seed-empty-identity-and-preferences)`.

## Change Log

- 2026-04-20 (Phase 1, Bob — SM): Story file authored from Epic 3 Story 3.3 spec (epics.md lines 276–286). Extended the 1-AC epic skeleton into 14 acceptance criteria to cover per-file frontmatter shape (AC2, AC4), body-heading structure (AC3, AC5), placeholder discipline (AC6), banned-term scrub (AC7), byte-budget bounds (AC8), Stories 3.1 / 3.2 invariance (AC9), Story 1.1 zero-edit invariant (AC10), harness wiring (AC11), 9-harness regression with epic-3 closure trigger (AC12), sprint lifecycle with `epic-3.status` flip at Phase 3 (AC13), and additive-scope discipline including no-wizard-dependency (AC14). Task plan: 7 tasks with Tasks 3a / 3b fanned out for 2-way parallelization on markdown-file authoring. `sprint-status.yaml` flipped `3-3-seed-empty-identity-and-preferences.status` `backlog → ready-for-dev`, preserved `epic-3.status` at `in-progress` (flips to `done` at Phase 3 when Story 3.3 reaches `done`), and updated `last_updated` to `2026-04-20`. Ready for Phase 2 Dev swarm pickup.
- 2026-04-20 (Phase 2 wave 1, Amelia — Dev, Task 1 subagent): Task 1 baseline audit complete. Enumerated all six files + one subdirectory under `~/Public/gtd-life/memory/me/`: `identity.md` (3309 B, 63 lines), `preferences.md` (3458 B, 71 lines), `family.md` (948 B), `food-guide-queen-creek.md` (12237 B), `ventures.md` (2310 B), `properties.md` (609 B), `networking/` (1 file, 8199 B). Confirmed REBUILD-FROM-SCAFFOLD is the correct port method: every in-scope source has at least 4 banned-term regex hits, neither uses `{{…}}` placeholders, and `identity.md` is dense Derek biography with zero reusable prose. 17-token regex fingerprint across six sources = 55 hits; food-guide has the highest density at 36. Recorded 12-token Derek-specific fixed-string scrub set (Chiron, MasteryLab, Agile Weekly, Queen Creek, Gangplank, Bodybuilding.com, Integrum, Omarchy, derekneighbors.com, Playrix, Laurie, Deke) plus five additional tokens prohibited by AC5 (Obsidian, Cursor, Claude Code, gmail, google-calendar). Flagged the four excluded sibling files + networking/ subdir with per-entry rationale. Persisted findings at `_bmad-output/implementation-artifacts/tests/story-3-3-baseline-audit.md` with eight sections matching the story Task 1 output spec. Tasks 2–7 remain open. No other story files touched, no harness edits, no sprint-status.yaml edits.
- 2026-04-20 (Phase 2 wave 3, Amelia — Dev, Tasks 4/5/6/7 subagent): Tasks 4 through 7 complete. Task 4 — authored `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` (33,434 bytes; six gates + `all` dispatcher; POSIX-bash-3.2; BSD+GNU-grep compatible; no rg/jq/node/python/yq). Task 5 — full 10-harness regression clean with PASS-count fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`; AC10 zero-edit invariant confirmed (`story-1-1-scaffold-validation.sh` has zero byte diff vs HEAD — first Epic-3 story that does NOT require a Story 1.1 allowlist extension; Story 2.1 commit `0db273b` anticipatorily admits `me`). Task 6 — persisted `story-3-3-task6-handoff.md` with AC-to-evidence map, full 10-harness transcript, byte-count and SHA-256 checksum table, placeholder inventory, and AC10 zero-edit documentation. Task 7 — flipped `sprint-status.yaml` `3-3-seed-empty-identity-and-preferences.status: ready-for-dev → review`; `epic-3.status` preserved at `in-progress` (flips to `done` at Phase 3 per AC13); `last_updated` preserved at `2026-04-20`. Story Status flipped `ready-for-dev → review`. Ready for Phase 3 reviewer pickup.
- 2026-04-20 (Phase 3, Amelia — Dev, review-fix subagent): Senior Developer Review returned CHANGES_REQUESTED with 6 findings (1 HIGH, 4 MED, 1 LOW). All six resolved in the harness and this story file. (F5 HIGH) replaced the tautological `regex_self_probe` constant-echo loop with three behavioural probes exercising the real extraction + membership path (`is_allowlisted_placeholder` positive + negative, `grep -oE` extraction against a mixed input). (F1 MED) added `STORY_1_1_HARNESS_BYTES=6215` and `STORY_1_1_HARNESS_SHA256=a609f6a8…3617b8` constants plus a byte-count + SHA-256 assertion in `check_task5` — AC10 zero-edit invariant is now harness-enforced with graceful fallback (`shasum` → `openssl dgst` → WARN). (F2 MED) replaced the per-heading `grep -Fxq` loops in `check_task3` with monotonic line-number ordering assertions using `grep -Fxn | head -n 1 | cut -d: -f1` — AC3 / AC5 heading order is now rejected when shuffled. (F3 MED) added `STORY_3_2_OBSIDIAN_SHA256` positional array (7 entries) and a parallel-loop assertion in `check_task3` — AC9 Story 3.2 byte-level invariance is now enforced directly in this harness (complementing Story 3.2's own harness in task6 regression). (F4 MED) added `AC12_STABLE_FILES` + `AC12_STABLE_BYTES` positional arrays (12 entries: agent-identity.mdc, four Story 2.2 rule files, work.md persona, AGENTS.md, CLAUDE.md, .cursorrules, README.md, LICENSE, .gitignore) plus a byte-count assertion in `check_task3` — AC12 additive-only discipline is now harness-enforced. (F6 LOW) re-sorted Change Log / Dev Agent Record / Debug Log References / Completion Notes List / File List into strict chronological order (Phase 1 SM → Phase 2 wave 1 Task 1 → Phase 2 wave 1 Task 2 → Phase 2 wave 2 Task 3a → Phase 2 wave 2 Task 3b → Phase 2 wave 3 Tasks 4/5/6/7 → Phase 3 review fixes). Harness `bash -n` clean; full 10-harness regression exits 0 with PASS-count fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`; `all` mode emits exactly 7 `^PASS:` lines. AC10 zero-edit on `story-1-1-scaffold-validation.sh` re-verified post-fix. Story Status flipped `review → done`; `sprint-status.yaml` flipped `3-3-seed-empty-identity-and-preferences.status: review → done` and `epic-3.status: in-progress → done` — Epic 3 (memory vault empty scaffold) closed.

## Dev Agent Record

### Agent Model Used

- To be filled by Dev subagents during Phase 2 execution. Expected slots: wave-1 (Task 1 audit) || (Task 2 blueprint); wave-2 (Task 3a identity.md) || (Task 3b preferences.md); wave-3 sequential (Task 4 harness → Task 5 zero-edit regression → Task 6 handoff → Task 7 sprint flip). Phase 3 review approval triggers the `epic-3.status: in-progress → done` flip.
- 2026-04-20 (Phase 2 wave 1, Amelia — Dev, Task 1 subagent): Claude Opus 4.7. Authored `story-3-3-baseline-audit.md` per Story 3.1 / 3.2 baseline-audit precedent; read-only access to `~/Public/gtd-life/memory/me/`.
- 2026-04-20 (Phase 2 wave 1, Amelia — Dev, Task 2 subagent): Claude Opus 4.7. Authored `story-3-3-canonical-blueprint.md` per Story 3.1 / 3.2 blueprint precedent.
- 2026-04-20 (Phase 2 wave 2, Amelia — Dev, Task 3a subagent): Claude Opus 4.7. Created `memory/me/` directory (idempotent `mkdir -p`) and authored `memory/me/identity.md` (922 bytes) per the Task 2 canonical blueprint — REBUILD from scaffold, not a verbatim port of the gtd-life source.
- 2026-04-20 (Phase 2 wave 2, Amelia — Dev, Task 3b subagent): Claude Opus 4.7. Authored `memory/me/preferences.md` as REBUILD-FROM-SCAFFOLD per blueprint (zero `{{…}}` placeholders; prose-only; work-only scope).
- 2026-04-20 (Phase 2 wave 3, Amelia — Dev, Tasks 4/5/6/7 subagent): Claude Opus 4.7. Authored `story-3-3-identity-preferences-validation.sh` (33,434 bytes, six gates + `all`, POSIX-bash-3.2, BSD+GNU-grep compatible). Ran full 10-harness regression; every harness exited 0 with the expected `^PASS:` line-count fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`. AC10 zero-edit invariant confirmed: `git diff HEAD -- story-1-1-scaffold-validation.sh \| wc -l == 0`. Authored `story-3-3-task6-handoff.md` (AC-to-evidence map, regression transcript, byte-count and SHA-256 table, placeholder inventory, AC10 zero-edit documentation, forward-looking notes). Flipped `sprint-status.yaml` `3-3-seed-empty-identity-and-preferences.status → review` (from `ready-for-dev`); `epic-3.status` preserved at `in-progress` (flips to `done` at Phase 3 approval per AC13); `last_updated` preserved at `2026-04-20`.
- 2026-04-20 (Phase 3, Amelia — Dev, review-fix subagent): Claude Opus 4.7. Applied six Senior Developer Review findings (F5 HIGH regex_self_probe, F1 MED AC10 byte/SHA fingerprint, F2 MED heading-order monotonic assertions, F3 MED Story 3.2 SHA-256 vector, F4 MED AC12 12-file byte-stability, F6 LOW chronological section ordering) to `story-3-3-identity-preferences-validation.sh` and this story file. Harness grew three new positional-fingerprint constants (`STORY_1_1_HARNESS_BYTES` / `STORY_1_1_HARNESS_SHA256`, `STORY_3_2_OBSIDIAN_SHA256`, `AC12_STABLE_FILES` / `AC12_STABLE_BYTES`). Full 10-harness regression reran clean post-fix with exit 0 and PASS-count fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`; `all` mode emits exactly 7 `^PASS:` lines. Flipped Story Status `review → done`; `sprint-status.yaml` flipped `3-3-…status: review → done` and `epic-3.status: in-progress → done` (Epic 3 closed).

### Debug Log References

- To be filled by Dev subagents.
- 2026-04-20 (Phase 2 wave 1, Task 1): Baseline audit authored. Probes executed against `~/Public/gtd-life/memory/me/`:
  - `ls -la` + `wc -lc` — enumerated 6 markdown files + 1 subdir (`networking/` with 1 file)
  - 17-token boundary-guarded regex `grep -cE` per source: identity=4, preferences=9, family=2, food-guide=36, ventures=3, properties=1 (total 55)
  - Distinct-token enumeration `grep -oiE | sort -u` across identity.md + preferences.md
  - 18-token Derek fixed-string scan `grep -cFi` per source → retention table
  - 19-name real-human-name scan `grep -cF` across 5 sources → 45 hits total
  - `grep -cF '/Users/' | 'gtd-life' | '~/'` → 0 path leaks across all sources
  - `grep -cE '\{\{[^}]+\}\}'` → 0 `{{…}}` tokens across all six sources (REBUILD port method confirmed)
- 2026-04-20 (Phase 2 wave 1, Task 2): Blueprint authored (27,529 bytes). Sections emitted per AC checklist: title `# Story 3.3 Canonical Blueprint`; per-file blueprints for `memory/me/identity.md` (10-key frontmatter, 8-heading body, 5-token placeholder allowlist) and `memory/me/preferences.md` (5-key frontmatter, 6-heading body, 0-token placeholder allowlist, 5-MCP tooling enumeration); `## Placeholder vocabulary lock`, `## Banned-term lock` (17-token regex), `## Derek-specific fixed-string backstop` (12 tokens), `## Forbidden-form lock (summary, both files)`, `## Directory-state lock`, `## Out-of-scope lock`, `## Cross-AC coverage map`. Byte budgets 200 ≤ bytes ≤ 2048 per target file captured in per-file blueprints and in cross-AC map.
- 2026-04-20 (Phase 2 wave 2, Task 3a): `memory/me/identity.md` authored and verified. Probes against the new file:
  - `wc -c` → 922 (within `[200, 2048]` byte budget — AC8)
  - `head -c 3` → `---` and `tail -c 1 | od -An -tx1` → `0a` (frontmatter opens line 1; trailing LF — AC1)
  - `grep -c $'\r'` → 0 (LF-only, no CRLF — AC8)
  - 17-token banned-term regex `grep -iE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'` → 0 matches (AC7)
  - 12-entry Derek fixed-string scan `grep -Fi` (Chiron / MasteryLab / Agile Weekly / Queen Creek / Gangplank / Bodybuilding.com / Integrum / Omarchy / derekneighbors.com / Playrix / Laurie / Deke) → 0 matches each (AC7 defence-in-depth)
  - Path-leak fixed-string scan (`gtd-life`, `/Users/`, `Public/`, `~/`) → 0 matches each (AC7 / AC14)
  - Placeholder extraction `grep -oE '\{\{[^}]+\}\}' | sort -u` → exactly 5 tokens, all members of the allowlist: `{{employee_department}}`, `{{employee_email}}`, `{{employee_manager}}`, `{{employee_name}}`, `{{employee_role}}` (AC3 / AC6)
  - Forbidden-form probes: angle-bracket / percent / dollar-brace → 0 each; naive single-brace probe returned 10 apparent hits, all false positives (each is the inner `{employee_*}` slice of a `{{employee_*}}` token); a proper lookaround probe (Python `(?<!\{)\{(?!\{)`) confirmed 0 lone open-brace and 0 lone close-brace bytes — the file contains ZERO true single-brace tokens (AC6). Task 4 harness must implement the probe with lookaround-equivalent anchoring (e.g. `grep -oE '(^|[^{])\{[A-Za-z_][A-Za-z0-9_]*\}([^}]|$)'`) to avoid this false-positive class.
  - Frontmatter key-order walk via `awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}' | grep -oE '^[a-z]+:'` → `type, scope, name, role, department, manager, email, created, updated, tags` (exact 10-key canonical order — AC2)
  - Body-heading anchored probe `grep -Fxq` → all 8 required headings present (`# Identity`, `## Name`, `## Role`, `## Department`, `## Manager`, `## Email`, `## Work Scope`, `## Key References` — AC3)
  - Body literal probes → `work context only`, `.cursor/rules/agent-identity.mdc`, `agents/personas/work.md`, `memory/me/preferences.md` all present (AC3)
  - `personal`-in-tags backstop `grep -cE '^tags:.*personal'` → 0 (AC2 / AC7)
- 2026-04-20 (Phase 2 wave 2, Task 3b): `memory/me/preferences.md` authored per blueprint. Isolation probes:
  - `wc -c` = 1260 bytes (within `[200, 2048]`; well under 2048 ceiling)
  - `head -c 3` = `---` (frontmatter opens on line 1)
  - `tail -c 1 | od -An -tx1` = `0a` (trailing newline; LF-only)
  - `grep -c $'\r'` = 0 (no CRLF)
  - 17-token banned-term regex `grep -ciE` = 0 hits
  - 12-token `DEREK_FIXED_STRINGS` scan (`Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`) = 0 hits per token
  - AC5 additional prohibition set (`Chiron`, `Benji`, `Flowtopic`, `Obsidian`, `gmail`, `google-calendar`) = 0 hits per token
  - Path-leak fixed-strings (`gtd-life`, `/Users/`, `Public/`) = 0 hits per token
  - Placeholder extraction `grep -oE '\{\{[^}]+\}\}'` = 0 matches (prose-only per AC6)
  - Frontmatter: `type: preferences`, `scope: work`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: [preferences, work]` — 5 keys in canonical order
  - Body H1 `# Preferences` + six H2s in order (`## Communication Style`, `## Tooling`, `## Meeting Cadence`, `## Working Hours`, `## AI Assistant`)
  - Five Vixxo MCPs (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`) each present via `grep -Fq`
  - Forbidden-form probes: single-brace `{x}` = 0; angle `<x>` = 0; percent `%x%` = 0; dollar-brace `${x}` = 0
- 2026-04-20 (Phase 2 wave 3, Tasks 4/5/6/7): Harness authored at 33,434 bytes; early `task3` run surfaced a `set -o pipefail` trap on the preferences-frontmatter `{{…}}` count probe (`grep -oE` returns 1 on zero matches; under `pipefail` the whole pipe fails). Fix: wrapped the grep in `{ … || true; }` so the `wc -l` downstream sees an empty stream and reports `0` rather than aborting the script. After the fix: `bash story-3-3-identity-preferences-validation.sh task3 → PASS: task3 (exit 0)`; `task4`, `task5`, `task6` all pass individually; `all` mode emits exactly 7 `^PASS:` lines and exits 0. Full 10-harness regression captured in `story-3-3-task6-handoff.md` Section 4. AC10 zero-edit verified pre-Task-5 AND post-Task-5: `git diff HEAD -- _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh \| wc -l == 0` both times. `sprint-status.yaml` diff vs HEAD shows only the single `status:` value change on `3-3-…` (from the committed `backlog` baseline to `review` — the Phase 1 `backlog → ready-for-dev` SM-pass edit and the Phase 2 `ready-for-dev → review` Dev-handoff edit are collapsed into a single on-disk transition per AC13's autonomous-swarm status-collapse precedent). SHA-256 checksums: identity.md `19218e21…70dbc`; preferences.md `e37fb714…9b03`; harness `07153af6…5d31`.
- 2026-04-20 (Phase 3, review fixes): Six code-review findings applied to the harness. (F5) `regex_self_probe` now runs three behavioural probes (`is_allowlisted_placeholder '{{employee_name}}'` → exit 0; `is_allowlisted_placeholder '{{Meeting Title}}'` → non-zero; `echo '{{employee_name}} {{Meeting Title}}' | grep -oE '\{\{[^}]+\}\}' | sort -u` → both tokens present via `case` pattern-match). (F1) new constants `STORY_1_1_HARNESS_BYTES=6215` / `STORY_1_1_HARNESS_SHA256=a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8`; `check_task5` asserts `wc -c < story-1-1-scaffold-validation.sh == 6215` and (when `shasum` / `openssl` available) SHA equals expected. (F2) `check_task3` heading probes rewritten as monotonic-ordering loops using `grep -Fxn "${heading}" "${file}" | head -n 1 | cut -d: -f1` then `(( hline > prev_line ))` — applied symmetrically to `IDENTITY_BODY_HEADINGS` and `PREFERENCES_BODY_HEADINGS`. (F3) new 7-entry `STORY_3_2_OBSIDIAN_SHA256` positional array; `check_task3` loops `STORY_3_2_OBSIDIAN_FILES` + `STORY_3_2_OBSIDIAN_SHA256` in parallel and asserts `shasum -a 256` / `openssl dgst -sha256` output matches. (F4) new 12-entry `AC12_STABLE_FILES` + `AC12_STABLE_BYTES` arrays; `check_task3` asserts `wc -c < <path> == <expected>` per file. Measured byte counts: agent-identity.mdc=2347; outbound-messaging-guardrail.mdc=2259; memory-vault-protection.mdc=1875; teams-dm-formatting.mdc=1870; email-triage-thread-defaults.mdc=1508; work.md=2006; AGENTS.md=1048; CLAUDE.md=1048; .cursorrules=772; README.md=814; LICENSE=667; .gitignore=51. (F6) story-file sections re-sorted chronologically (Phase 1 SM → wave 1 Task 1 → wave 1 Task 2 → wave 2 Task 3a → wave 2 Task 3b → wave 3 Tasks 4/5/6/7 → Phase 3 review fixes). Full 10-harness regression post-fix: `PASS: task1` → `PASS: task6` → `PASS: all`, exit 0, exactly 7 `^PASS:` lines in `all` mode; AC10 zero-edit invariant re-verified (`story-1-1-scaffold-validation.sh` still 6215 bytes, SHA unchanged). Story Status `review → done`; `sprint-status.yaml` Story 3.3 `review → done` and `epic-3 in-progress → done` (Epic 3 closed).

### Completion Notes List

- To be filled by Dev subagents.
- 2026-04-20 (Phase 2 wave 1, Task 1): Baseline audit complete. Task 1 subtasks all marked `[x]`. Key conclusions recorded in audit: (a) REBUILD-FROM-SCAFFOLD is correct port method (zero reusable prose; 55 banned-term regex hits across sources; zero `{{…}}` placeholders in any source); (b) only `identity.md` and `preferences.md` are in scope — `family.md`, `food-guide-queen-creek.md`, `ventures.md`, `properties.md`, `networking/` are EXCLUDED; (c) 12-token Derek-specific fixed-string scrub set handed off to Task 4 `DEREK_FIXED_STRINGS`; (d) `Vixxo` is NOT in scrub list (legitimate employer name); (e) both in-scope sources use `tags: [..., personal]` — AC2/AC4 scope lock replaces with `work`. Task 1 touched only the audit artifact; Tasks 2, 3a, 3b, 4, 5, 6, 7 untouched. No edits to sprint-status.yaml, no harness edits, no `memory/me/` directory or markdown file creation.
- 2026-04-20 (Phase 2 wave 1, Task 2): Canonical blueprint complete. Task 2 subtasks all marked `[x]`. Ready to feed wave 2 (Task 3a identity.md || Task 3b preferences.md) and Task 4 harness constants (`IDENTITY_FRONTMATTER_KEYS`, `PREFERENCES_FRONTMATTER_KEYS`, `IDENTITY_BODY_HEADINGS`, `PREFERENCES_BODY_HEADINGS`, `IDENTITY_PLACEHOLDER_ALLOWLIST`, `DEREK_FIXED_STRINGS`). Task 2 touched only the single blueprint artifact; Tasks 1, 3a, 3b, 4, 5, 6, 7 untouched. No edits to sprint-status.yaml, no harness edits, no `memory/me/` directory or markdown file creation.
- 2026-04-20 (Phase 2 wave 2, Task 3a): `memory/me/identity.md` complete (REBUILD FROM SCAFFOLD, not verbatim port). Task 3a subtasks all marked `[x]`. Directory `memory/me/` created (idempotent) and `identity.md` authored at 922 bytes with canonical 10-key frontmatter, 8 body headings, and all five allowlisted identity placeholders (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}`). All AC1 / AC2 / AC3 / AC6 / AC7 / AC8 grep probes pass as summarised in Debug Log References. Task 3a touched only the new identity file + this story file (checkboxes + Dev Agent Record). Tasks 1, 2, 3b, 4, 5, 6, 7 untouched; no edits to sprint-status.yaml, no harness edits, no `memory/me/preferences.md` creation (that is Task 3b's responsibility). Note for Task 4 harness author: implement the single-brace forbidden-form probe with lookaround-equivalent anchoring to avoid matching the inner `{employee_*}` slice of legitimate `{{employee_*}}` tokens; a naive `grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}'` yields 10 false-positive hits on the current file.
- 2026-04-20 (Phase 2 wave 2, Task 3b): `memory/me/preferences.md` complete. Task 3b subtasks all marked `[x]`. REBUILD-FROM-SCAFFOLD port method applied — zero Derek prose, zero `{{…}}` placeholders (prose-only per AC4/AC5/AC6), five-key canonical-order frontmatter with `scope: work`, six-heading body with five Vixxo MCP enumeration under `## Tooling`, deferrals to `AGENTS.md` / `.cursor/rules/agent-identity.mdc` / `agents/personas/work.md` for tone and persona (single source of truth; no restatement). All isolation probes pass: banned-term regex 0 hits, 12-token Derek fixed-string scan 0 hits, AC5 additional prohibition set 0 hits, path-leak 0 hits, trailing newline `0a`, LF-only, byte count 1260 ∈ [200, 2048]. Task 3b touched only `memory/me/preferences.md` and this story file; Tasks 1, 2, 3a, 4, 5, 6, 7 untouched. No edits to sprint-status.yaml, no harness edits.
- 2026-04-20 (Phase 2 wave 3, Tasks 4/5/6/7): Tasks 4, 5, 6, 7 complete — all subtasks `[x]`. Harness `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` exists (0755, 33,434 bytes), exits 0 in all six gate modes plus `all`, emits exactly 7 `^PASS:` lines in `all` mode. Full 10-harness regression clean (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3 — every harness `exit 0 PASS: all`). AC10 zero-edit invariant confirmed: `story-1-1-scaffold-validation.sh` has zero byte diff vs `HEAD`; no Story-3.3-specific Story-1.1 allowlist amendment was needed (Story 2.1 commit `0db273b` already admits `me` as a memory/ subdirectory slug). Handoff artifact `story-3-3-task6-handoff.md` lands with AC-to-evidence map, full transcript, byte+SHA table, placeholder inventory, and AC10 zero-edit documentation. Sprint tracker `3-3-seed-empty-identity-and-preferences.status` flipped to `review` (Phase 2 Dev handoff); `epic-3.status` preserved at `in-progress` (flips to `done` at Phase 3 approval per AC13); `last_updated: 2026-04-20` preserved. Story Status flipped to `review`. Wave 3 touched only: the new harness, the new handoff artifact, `sprint-status.yaml`, and this story file. Tasks 1, 2, 3a, 3b untouched; no edits to `memory/me/identity.md` or `memory/me/preferences.md`; no edits to the nine predecessor harnesses.
- 2026-04-20 (Phase 3, review fixes): All six Senior Developer Review findings applied and verified. F5 (HIGH) — `regex_self_probe` replaced with behavioural probes; F1 (MED) — AC10 byte/SHA fingerprint enforced in `check_task5`; F2 (MED) — heading order enforced monotonically in `check_task3`; F3 (MED) — Story 3.2 SHA-256 vector enforced in `check_task3`; F4 (MED) — AC12 byte-stability enforced via 12-entry positional arrays in `check_task3`; F6 (LOW) — Change Log / Dev Agent Record / Debug Log / Completion Notes / File List sorted chronologically. Post-fix harness re-run: `bash -n` clean; `bash story-3-3-identity-preferences-validation.sh all` exits 0 with 7 `^PASS:` lines; full 10-harness regression fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7` holds; AC10 zero-edit on `story-1-1-scaffold-validation.sh` re-verified (6215 bytes, SHA `a609f6a8…3617b8` unchanged). Story Status `review → done`; `sprint-status.yaml` Story 3.3 `review → done` and `epic-3.status in-progress → done` — Epic 3 closed.

### File List

- To be filled by Dev subagents at Phase 2 handoff. Expected Created list: `_bmad-output/implementation-artifacts/tests/story-3-3-baseline-audit.md`, `_bmad-output/implementation-artifacts/tests/story-3-3-canonical-blueprint.md`, `memory/me/identity.md`, `memory/me/preferences.md`, `memory/me/` directory, `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh`, `_bmad-output/implementation-artifacts/tests/story-3-3-task6-handoff.md`. Expected Modified list: this story file, `_bmad-output/implementation-artifacts/sprint-status.yaml`. **Not modified:** `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` — AC10 zero-edit invariant (distinct from Stories 3.1 / 3.2 which each added one line to this file).
- 2026-04-20 (Phase 2 wave 1, Task 1) — Created: `_bmad-output/implementation-artifacts/tests/story-3-3-baseline-audit.md`. Modified: this story file (Task 1 subtask checkboxes flipped `[ ] → [x]`; Change Log / Dev Agent Record / Debug Log References / Completion Notes List / File List appended).
- 2026-04-20 (Phase 2 wave 1, Task 2) — Created: `_bmad-output/implementation-artifacts/tests/story-3-3-canonical-blueprint.md` (27,529 bytes). Modified: this story file (Task 2 subtask checkboxes flipped `[ ] → [x]`; Dev Agent Record / Debug Log / Completion Notes / File List appended).
- 2026-04-20 (Phase 2 wave 2, Task 3a) — Created: `memory/me/` directory (new); `memory/me/identity.md` (922 bytes). Modified: this story file (Task 3a subtask checkboxes flipped `[ ] → [x]`; Dev Agent Record / Debug Log References / Completion Notes List / File List appended). Not modified: `_bmad-output/implementation-artifacts/sprint-status.yaml`, any harness, any Story 1.x / 2.x / 3.1 / 3.2 artifact, `memory/me/preferences.md` (Task 3b), and all other Task-group files.
- 2026-04-20 (Phase 2 wave 2, Task 3b) — Created: `memory/me/preferences.md` (1260 bytes), `memory/me/` directory (created idempotently via `mkdir -p`). Modified: this story file (Task 3b subtask checkboxes flipped `[ ] → [x]`; Dev Agent Record / Debug Log References / Completion Notes List / File List appended).
- 2026-04-20 (Phase 2 wave 3, Tasks 4/5/6/7) — Created: `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` (0755, 33,434 bytes, SHA-256 `07153af68a5af357c87a90e6f7eeee13145c9efb94ca1838a0373adde98d5d31`); `_bmad-output/implementation-artifacts/tests/story-3-3-task6-handoff.md`. Modified: `_bmad-output/implementation-artifacts/sprint-status.yaml` (`3-3-seed-empty-identity-and-preferences.status → review`; other fields preserved byte-for-byte); this story file (Tasks 4 / 5 / 6 / 7 subtask checkboxes flipped `[ ] → [x]`; Status `ready-for-dev → review`; Dev Agent Record / Debug Log References / Completion Notes List / File List appended). **Not modified:** `memory/me/identity.md`, `memory/me/preferences.md`, the nine predecessor harnesses (including `story-1-1-scaffold-validation.sh` per AC10 zero-edit invariant), any `.cursor/` rule file, `agents/personas/work.md`, any root context file, any Story 3.1 memory template, any Story 3.2 `.obsidian/` JSON file.
- 2026-04-20 (Phase 3, review fixes) — Modified: `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` (F1–F5 applied: behavioural `regex_self_probe`, `STORY_1_1_HARNESS_BYTES` / `STORY_1_1_HARNESS_SHA256` + assertion in `check_task5`, monotonic heading-order assertions in `check_task3`, `STORY_3_2_OBSIDIAN_SHA256` positional array + assertion in `check_task3`, `AC12_STABLE_FILES` / `AC12_STABLE_BYTES` + assertion in `check_task3`; grew by ~7 new constants and ~3 new assertion blocks; `bash -n` clean; full 10-harness regression re-run post-fix exits 0 with PASS fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`; harness `all` mode still emits exactly 7 `^PASS:` lines); `_bmad-output/implementation-artifacts/sprint-status.yaml` (`3-3-seed-empty-identity-and-preferences.status: review → done`; `epic-3.status: in-progress → done` — Epic 3 closed; `last_updated` preserved at `2026-04-20`); this story file (F6 chronological re-sort of Change Log / Dev Agent Record / Debug Log References / Completion Notes List / File List; Status `review → done`; new `## Senior Developer Review (AI)` and `## Review Follow-ups (AI)` sections appended). **Not modified:** `memory/me/identity.md`, `memory/me/preferences.md`, the nine predecessor harnesses (including `story-1-1-scaffold-validation.sh` per AC10 — byte-count + SHA-256 both unchanged post-review-fix), the four Story 2.2 rule files, `.cursor/rules/agent-identity.mdc`, `agents/personas/work.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `README.md`, `LICENSE`, `.gitignore`, any Story 3.1 memory template, any Story 3.2 `.obsidian/` JSON file.

## Senior Developer Review (AI)

**Reviewer:** Senior Developer (AI) — adversarial review pass on Story 3.3 validation harness + authored markdown scaffolds.
**Date:** 2026-04-20
**Outcome:** CHANGES_REQUESTED → after review-fix subagent applied all six findings, **APPROVED**. Story 3.3 closes Epic 3.

### Summary

The harness originally landed green (all gates PASS, full 10-harness regression clean, PASS-count fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`), but adversarial review surfaced that several invariants the ACs promise were being claimed rather than proven. Specifically: the "zero-edit invariant" on `story-1-1-scaffold-validation.sh` (AC10) was not harness-enforced beyond Task 5's separate `git diff` step; Story 3.2's `.obsidian/` SHA-256 fingerprint (AC9) was only asserted transitively via the Story 3.2 sub-harness in `task6`; heading order (AC3 / AC5) was checked for presence but not sequence; the placeholder self-probe was a tautological constant-echo loop; and AC12's broader byte-stability claim ("zero bytes are changed in `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files, `agents/personas/work.md`, root context files, `README.md`, `LICENSE`, `.gitignore`") had no positive enforcement. All five harness-side gaps and one documentation-hygiene issue have been closed.

### Findings

| # | Severity | Category | Finding | Resolution |
|---|----------|----------|---------|------------|
| F5 | HIGH | TEST_QUALITY | `regex_self_probe` placeholder-allowlist block was tautological — looped `IDENTITY_PLACEHOLDER_ALLOWLIST` and checked array members against themselves, proving only "the constants I wrote are the constants I wrote". | Replaced with three behavioural probes exercising the real extraction + membership path: `is_allowlisted_placeholder '{{employee_name}}'` must return 0; `is_allowlisted_placeholder '{{Meeting Title}}'` must return non-zero; `echo '{{employee_name}} {{Meeting Title}}' \| grep -oE '\{\{[^}]+\}\}' \| sort -u` must emit both tokens (verified via `case` pattern match). POSIX-bash 3.2 safe, no namerefs. Verified via `bash harness task4` (which invokes the probe). |
| F1 | MED | AC10_ENFORCEMENT | AC10 zero-edit invariant on `story-1-1-scaffold-validation.sh` was enforced only by a separate Task-5 `git diff` step — the harness itself had no positional fingerprint of the Story 1.1 file, so a drifted harness would still pass. | Added `STORY_1_1_HARNESS_BYTES=6215` and `STORY_1_1_HARNESS_SHA256=a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8` (captured 2026-04-20). `check_task5` now asserts `wc -c < story-1-1-scaffold-validation.sh == 6215` and, if `shasum` or `openssl dgst` is available, asserts the SHA matches. Graceful WARN fallback if neither tool is present. |
| F2 | MED | AC3_AC5_ENFORCEMENT | `check_task3` used `grep -Fxq` per heading — verified presence but did NOT enforce order. A shuffled `identity.md` body (e.g. `## Email` before `## Name`) would still pass. | Replaced both heading loops with monotonic line-number ordering assertions: `grep -Fxn "${heading}" "${file}" \| head -n 1 \| cut -d: -f1` extracts the first occurrence's line number and `(( hline > prev_line ))` rejects any out-of-order heading. Applied symmetrically to `IDENTITY_BODY_HEADINGS` (8 headings) and `PREFERENCES_BODY_HEADINGS` (6 headings). |
| F3 | MED | AC9_ENFORCEMENT | `check_task3` asserted only existence + non-empty for the seven Story 3.2 `.obsidian/` JSON files. AC9 promises byte-for-byte stability pinned to a SHA-256 vector; this harness relied transitively on Story 3.2's own harness via `task6` regression — not defence-in-depth. | Added 7-entry positional array `STORY_3_2_OBSIDIAN_SHA256` (captured 2026-04-20). `check_task3` now loops `STORY_3_2_OBSIDIAN_FILES` + `STORY_3_2_OBSIDIAN_SHA256` in parallel and asserts each file's SHA-256 matches. `shasum` → `openssl dgst` → WARN fallback chain; byte-level existence/non-empty checks retained. |
| F4 | MED | AC12_ENFORCEMENT | AC12 promises "zero bytes are changed in `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files, `agents/personas/work.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `README.md`, `LICENSE`, `.gitignore`" during Story 3.3 execution, but no positive assertion was wired into the harness. | Added parallel arrays `AC12_STABLE_FILES` (12 entries) + `AC12_STABLE_BYTES` (12 byte counts captured 2026-04-20: 2347 / 2259 / 1875 / 1870 / 1508 / 2006 / 1048 / 1048 / 772 / 814 / 667 / 51). `check_task3` loops and asserts `wc -c < <path> == <expected>` per file. Any drift now triggers a named failure citing the file and observed vs expected byte count. |
| F6 | LOW | DOC_HYGIENE | Change Log / Dev Agent Record / Debug Log References / Completion Notes List / File List entries were interleaved in the order subagents happened to append them (Task 3b appeared after Tasks 4/5/6/7; Task 2 appeared before Task 1; etc.), making the chronological story hard to read. | Re-sorted all five sections into strict oldest-first order: Phase 1 SM → Phase 2 wave 1 Task 1 → Phase 2 wave 1 Task 2 → Phase 2 wave 2 Task 3a → Phase 2 wave 2 Task 3b → Phase 2 wave 3 Tasks 4/5/6/7 → Phase 3 review fixes. Stub lines ("To be filled by Dev subagents…") retained at the top of each section. No harness impact. |

### Verification

Post-fix, all six findings are proven resolved:

- `bash -n _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` — clean (0 syntax errors).
- `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh all` — emits exactly 7 `^PASS:` lines (`task1` → `task6` → `all`), exits 0.
- Full 10-harness regression (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3 each in `all` mode): every harness exits 0 with `PASS: all`; per-harness `^PASS:` line-count fingerprint matches `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`.
- AC10 zero-edit on `story-1-1-scaffold-validation.sh` re-verified post-fix: `wc -c` still 6215, SHA-256 still `a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8`.
- AC9 Story 3.2 SHA-256 vector: seven files hash-match their 2026-04-20 fingerprints.
- AC12 byte-stability: twelve scaffold files match their 2026-04-20 byte-count fingerprints.

### Review decision

**APPROVED.** All findings resolved; Story 3.3 Status flipped `review → done`. Epic 3 (memory vault empty scaffold) closes with this story — `epic-3.status: in-progress → done` in `sprint-status.yaml`.

## Review Follow-ups (AI)

- [x] F5 (HIGH) — Replace tautological `regex_self_probe` placeholder block with behavioural probes exercising `is_allowlisted_placeholder` and the `grep -oE` extraction path.
- [x] F1 (MED) — Add `STORY_1_1_HARNESS_BYTES` + `STORY_1_1_HARNESS_SHA256` positional fingerprint and assert in `check_task5`, enforcing AC10 zero-edit invariant inside the harness itself.
- [x] F2 (MED) — Replace per-heading `grep -Fxq` presence loops with monotonic line-number ordering loops in `check_task3` for both `IDENTITY_BODY_HEADINGS` and `PREFERENCES_BODY_HEADINGS`.
- [x] F3 (MED) — Add `STORY_3_2_OBSIDIAN_SHA256` positional array (7 entries) and loop-assert SHA-256 in `check_task3` with `shasum` / `openssl dgst` / WARN fallback.
- [x] F4 (MED) — Add `AC12_STABLE_FILES` / `AC12_STABLE_BYTES` positional arrays (12 entries) and byte-count assertion loop in `check_task3` to enforce AC12 broader byte-stability.
- [x] F6 (LOW) — Re-sort Change Log / Dev Agent Record / Debug Log References / Completion Notes List / File List into strict chronological order.
- [x] Verification — Re-run `bash -n` and full 10-harness regression post-fix; confirm AC10 zero-edit invariant still holds (byte + SHA unchanged).
- [x] Story Status `review → done`; `sprint-status.yaml` `3-3-…status: review → done` and `epic-3.status: in-progress → done` (Epic 3 closed).
