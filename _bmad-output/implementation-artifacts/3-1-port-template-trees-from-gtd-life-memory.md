# Story 3.1: Port `_template.md` and `_template/` trees from gtd-life memory

Status: done

## Story

As a new Vixxo employee cloning the `assistants-template`,
I want the same empty memory-vault template tree as `gtd-life/memory/` — namely `memory/meetings/_template/{meeting,agenda,prep,transcript}.md`, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, and `memory/appreciations/_template.md` — with all Derek / RevivaGo / personal-context residue scrubbed out,
so that I can start capturing meetings, people, decisions, references, inbox thoughts, and appreciations using the same battle-tested skeleton the gtd-life vault uses, without inheriting any personal data or single-person biographical assumptions and without waiting on the setup wizard (Epic 5) to land.

## Acceptance Criteria

1. **AC1 — `memory/meetings/_template/` directory template bundle exists with four files**
   - Given the cloned `assistants-template` repository after Story 3.1 lands
   - When `memory/meetings/_template/` is listed
   - Then the directory contains exactly four Markdown files: `meeting.md`, `agenda.md`, `prep.md`, `transcript.md` — one file per meeting lifecycle stage (the document that survives; the pre-meeting agenda; the pre-meeting prep page; the raw transcript) — and no extra files
   - And each file exists, is non-empty, is a valid UTF-8 text file, and ends with a trailing newline
   - And `meeting.md` contains a YAML frontmatter block opened by `---` on line 1 and closed by `---`, with keys `type: meeting`, `date: YYYY-MM-DD`, `time: "HH:MM"`, `attendees: []`, `context: ""`, `location: ""`, `join_url: ""`, `organizer: ""`, `recurring: false`, `action_items: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`
   - And `meeting.md` body contains an H1 title with a `{{Meeting Title}}` placeholder, a doc-link table linking to `prep.md` / `agenda.md` / `transcript.md`, and H2 sections `## Summary`, `## Notes`, `## Decisions`, `## Action Items`
   - And `agenda.md` contains an H1 title with `{{Meeting Title}}`, H2 sections `## Topics` and `## Parking Lot`, and a sample checkbox line with `{{topic}}` / `{{owner}}` / `{{estimated minutes}}` placeholders
   - And `prep.md` contains an H1 title with `{{Meeting Title}}` and H2 sections `## My Objectives`, `## Questions to Raise`, `## Attendee Context`, `## Prior Meeting History`, `## Related Tasks`, `## Commercial Context`
   - And `transcript.md` contains an H1 title with `{{Meeting Title}}`, a `**Source:**` line, a `**Recording:**` line, and a horizontal rule (`---`) separating the header from the transcript body placeholder
   - And the `context:` comment in `meeting.md` frontmatter (if preserved) MUST NOT enumerate `revivago`, `personal`, or any gtd-life-specific context value; allowed enumeration values are work-scoped only (e.g. `vixxo | customer | internal`) or the comment may be omitted entirely

2. **AC2 — `memory/people/_template.md` exists with the canonical person-note shape**
   - Given the cloned repo after Story 3.1 lands
   - When `memory/people/_template.md` is read
   - Then it contains a YAML frontmatter block with keys `type: person`, `company: ""`, `role: ""`, `email: ""`, `last_1on1: ""`, `open_action_items: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`
   - And the body contains an H1 title with `{{Name}}` placeholder, an H2 `## Overview` section with `**Company**`, `**Role**`, `**Reports to**`, `**Direct reports**` bold-label lines (values may be placeholders such as `{{company}}` or `{{manager or "N/A"}}`), and H2 sections `## 1-on-1 History`, `## Action Items`, `## Notes`

3. **AC3 — `memory/decisions/_template.md` exists with the canonical decision-note shape**
   - Given the cloned repo
   - When `memory/decisions/_template.md` is read
   - Then it contains a YAML frontmatter block with keys `type: decision`, `status: open`, `date: YYYY-MM-DD`, `context: ""`, `stakeholders: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`
   - And the body contains an H1 title with `{{Decision Title}}`, and H2 sections `## Context`, `## Alternatives` (with two H3 sub-sections `### Option A: {{name}}` and `### Option B: {{name}}`), `## Decision`, `## Rationale`, `## Implications`

4. **AC4 — `memory/reference/_template.md` exists with the canonical reference-note shape**
   - Given the cloned repo
   - When `memory/reference/_template.md` is read
   - Then it contains a YAML frontmatter block with keys `type: reference`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `context: ""`, `related_to: []`, `tags: []`
   - And the body contains an H1 title with `{{Reference Title}}`, and H2 sections `## Summary`, `## Details`, `## Links`, `## Related notes`

5. **AC5 — `memory/inbox/_template.md` exists with a minimal capture shape**
   - Given the cloned repo
   - When `memory/inbox/_template.md` is read
   - Then it contains a YAML frontmatter block with keys `type: inbox`, `created: YYYY-MM-DD`, `context: ""`, `tags: []`
   - And the body contains a single H1 heading `# Thought`
   - And the `context:` key MUST NOT carry the gtd-life comment `vixxo | revivago | personal`; the value is an empty string and any explanatory comment (if retained) enumerates only work-scoped values (e.g. `# e.g. vixxo | customer | internal`) or the comment is omitted

6. **AC6 — `memory/appreciations/_template.md` exists with a well-formed appreciation-note shape**
   - Given the cloned repo
   - When `memory/appreciations/_template.md` is read
   - Then it contains a PROPERLY-FORMED YAML frontmatter block — opened by `---` on line 1, closed by `---` on a later line, with no `## `-prefixed key lines inside the frontmatter (this is a deliberate repair of the malformed gtd-life source which opens the frontmatter with `---` and then writes `## type: appreciation` as a Markdown heading by mistake)
   - And the frontmatter contains keys `type: appreciation`, `date: YYYY-MM-DD`, `recipient: ""`, `context: ""`, `tags: []`
   - And the body contains an H1 title with `{{Recipient or Moment}}` placeholder and at least two H2 sections (`## What` and `## Why it mattered`) giving the template a useful shape

7. **AC7 — Zero Derek / RevivaGo / personal content in any ported template file**
   - Given every file ported in AC1–AC6
   - When the standard boundary-guarded banned-term scan (carried forward from Story 2.1 / 2.2 / 2.3) runs across each file
   - Then the banned-term regex `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` matches zero occurrences for every token in the standard set: `Derek`, `Neighbors`, `neighborhood` (case-insensitive per prior stories), `RevivaGo`, `revivago`, `Benji`, `benji`, `Flowtopic`, `flowtopic`, `gtd-life`, `gtdlife`, `Wyoming`, `Cheyenne` (example PII from gtd-life), plus the Epic 3 newcomers `family`, `home`, `blog`, `wife`, `son`, `daughter`, `dog`
   - And no file contains the literal strings `gtd-life`, `~/Public/gtd-life`, or any filesystem path that points back at the source repo
   - And no file contains a real human first-or-last name other than the `{{Name}}` / `{{Recipient or Moment}}` / `{{person}}` / `{{owner}}` / `{{manager or "N/A"}}` placeholders

8. **AC8 — Placeholder vocabulary is consistent across files**
   - Given every file ported in AC1–AC6
   - When placeholders are enumerated
   - Then the only allowed placeholder forms are `{{double-curly-brace-name}}` (e.g. `{{Meeting Title}}`, `{{Name}}`, `{{topic}}`, `{{owner}}`, `{{estimated minutes}}`, `{{person}}`, `{{action}}`, `{{date}}`, `{{company}}`, `{{role}}`, `{{manager or "N/A"}}`, `{{count or "N/A"}}`, `{{Decision Title}}`, `{{Reference Title}}`, `{{Recipient or Moment}}`, `{{action item}}`, `{{name}}`) and canonical date/time tokens (`YYYY-MM-DD`, `HH:MM`)
   - And NO single-curly-brace placeholders, NO `%PLACEHOLDER%` shell-style placeholders, NO `<PLACEHOLDER>` XML-style placeholders, NO `${PLACEHOLDER}` shell-style placeholders — the template vocabulary is `{{…}}` exclusively, matching the placeholder discipline established by `.cursor/rules/agent-identity.mdc` in Story 2.1 and `agents/personas/work.md` in Story 2.3
   - And no file contains a `{{employee_name}}` or `{{employee_role}}` placeholder (those are identity-file placeholders owned by Story 2.1 / 2.3 / 3.3; templates use content-shape placeholders like `{{Name}}` / `{{Meeting Title}}` because they describe the shape of a future memory note, not the operator's identity)

9. **AC9 — Existing directory sentinels (`.gitkeep`) are handled correctly**
   - Given `memory/` was scaffolded in Story 1.1 with a single `memory/.gitkeep` (and no per-subdir `.gitkeep` files yet)
   - When Story 3.1 creates the six target subdirectories (`meetings/_template/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/`)
   - Then the top-level `memory/.gitkeep` from Story 1.1 remains byte-for-byte unchanged (additive discipline from Story 2.4 AC8)
   - And no new `.gitkeep` files are added to the six new subdirectories (the `_template*.md` files already provide git-trackable content, making `.gitkeep` redundant)
   - And no empty/tracking sentinels (`.keep`, `empty`, `placeholder`) are introduced

10. **AC10 — Validation/CI harness exists and is wired into the test-harness family**
    - Given the existing harness family under `_bmad-output/implementation-artifacts/tests/`
    - When Story 3.1 lands
    - Then a new deterministic harness `story-3-1-memory-template-tree-validation.sh` exists at `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`, is marked executable (`chmod +x`), uses `#!/usr/bin/env bash` on line 1 and `set -euo pipefail` on line 2
    - And the harness implements gates `task1` (baseline audit evidence), `task2` (canonical blueprint evidence), `task3` (file existence + frontmatter keys + required headers across all nine ported files), `task4` (cross-file banned-term scan + placeholder-vocabulary scan + gtd-life path-reference scan), `task5` (self-check: shebang, `set -euo pipefail`, all case arms, constants, `regex_self_probe`), `task6` (regression — invokes Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 harnesses in `all` mode and asserts each exits zero), plus an `all` dispatcher
    - And the harness exits `0` with `PASS: all` on success; exits `1` and emits `FAIL: <gate>: <reason>` on stderr on failure — matching the Story 2.1 / 2.2 / 2.3 / 2.4 contract
    - And the harness is BSD-grep and GNU-grep compatible, POSIX-bash-3.2 compatible, and uses only `bash`, `grep`, `find`, `awk`, `sed`, and shell built-ins (no `rg`, no Python)
    - And the harness implements `regex_self_probe` that exercises the boundary-guarded banned-term regex against at least two tokens (one positive, one negative case per token) — guards against a mis-parsing host grep (same pattern as Story 2.1 / 2.2 / 2.3 / 2.4)

11. **AC11 — Regression-runs all predecessor harnesses cleanly with no edits to prior story artifacts**
    - Given all prior harnesses in `_bmad-output/implementation-artifacts/tests/` (Story 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4)
    - When the Story 3.1 regression gate (`task6`) runs
    - Then `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, `bash story-2-1-agent-identity-validation.sh all`, `bash story-2-2-guardrail-and-formatting-validation.sh all`, `bash story-2-3-work-persona-validation.sh all`, and `bash story-2-4-benji-inbox-absence-validation.sh all` each exit `0` with `PASS: all`
    - And zero bytes are changed in any of those seven prior harnesses during Story 3.1 execution. **Exception: a single-line additive extension to `story-1-1-scaffold-validation.sh`'s `memory/` allowlist on line 155, admitting the six new Story 3.1 subdirectory names (`meetings|people|decisions|reference|inbox|appreciations`), is permitted. This follows Story 2.1's precedent (commit `0db273b`, which did the analogous one-line extension adding `me|mcp|obsidian` in anticipation of future Epic-3 subdirectories) and is the minimal-change pattern the Story 1.1 harness was designed to accept.**
    - And zero bytes are changed in `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files (`outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`), `agents/personas/work.md`, the root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`), `README.md`, `LICENSE`, `.gitignore`, `memory/.gitkeep` — Story 3.1 is additive only (new template files + new harness + new evidence artifacts + sprint-status flip + this story file, plus the Story 2.1-precedent one-line allowlist extension in `story-1-1-scaffold-validation.sh` documented above)

12. **AC12 — Sprint tracker lifecycle reflects the story transition and epic-3 promotion**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When Story 3.1 opens at Phase 1 (SM pass) and again at Phase 2 (Dev handoff)
    - Then the `3-1-port-template-trees-from-gtd-life-memory.status` entry is updated `backlog → ready-for-dev` at Phase 1, and `ready-for-dev → review` at Phase 2 (the autonomous-swarm lifecycle may collapse interim states per Story 2.1 / 2.2 / 2.3 / 2.4 precedent — a single `backlog → review` on-disk transition is acceptable as long as the final pre-review status is `review`)
    - And `epic-3.status` is flipped `backlog → in-progress` at Phase 1 (Story 3.1 is the FIRST story in Epic 3; the first-story-opens-epic rule from the sprint-status header applies)
    - And `last_updated` is set to `2026-04-20` on the Phase 1 edit
    - And no other story's status is regressed; every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` is preserved byte-for-byte (zero reordering, zero comment drift, zero key addition/removal beyond the two value flips and the `last_updated` value change)

13. **AC13 — Story is additive; no scope creep into Stories 3.2 / 3.3 territory**
    - Given the scope of Story 3.1
    - When the working-set file list is reviewed
    - Then Story 3.1 creates ONLY: the nine template files under `memory/` (four under `meetings/_template/`, five under `people/` / `decisions/` / `reference/` / `inbox/` / `appreciations/` as single `_template.md` files), the harness, three test-evidence files (baseline audit, canonical blueprint, handoff package), and this story file
    - And Story 3.1 does NOT create `.obsidian/` config (that is Story 3.2's scope), `memory/me/identity.md` (Story 3.3), `memory/me/preferences.md` (Story 3.3), `memory/companies/`, `memory/daily/`, `memory/blog-ideas/`, or any content under `memory/vixxo/`
    - And Story 3.1 does NOT create or edit any files under `.cursor/`, `agents/`, `bin/`, `scripts/`, `docs/`, or the repo root
    - And Story 3.1 modifies ONLY: `_bmad-output/implementation-artifacts/sprint-status.yaml` (status flips + `last_updated`) and this story file (Dev Agent Record / Change Log / File List / checkboxes at Dev handoff). **Exception: a single-line additive extension to `story-1-1-scaffold-validation.sh`'s `memory/` allowlist on line 155, admitting the six new Story 3.1 subdirectory names, is permitted. This follows Story 2.1's precedent (commit `0db273b`) and is the minimal-change pattern the Story 1.1 harness was designed to accept.**

## Tasks / Subtasks

- [x] Task 1 — Baseline audit of gtd-life template sources and Derek/RevivaGo/personal-content inventory (AC: 1, 2, 3, 4, 5, 6, 7, 8, 13) **[Parallelizable with Task 2]**
  - [x] Enumerate every file at `~/Public/gtd-life/memory/meetings/_template/*.md`, `~/Public/gtd-life/memory/people/_template.md`, `~/Public/gtd-life/memory/decisions/_template.md`, `~/Public/gtd-life/memory/reference/_template.md`, `~/Public/gtd-life/memory/inbox/_template.md`, `~/Public/gtd-life/memory/appreciations/_template.md`. Record each file's (a) frontmatter keys, (b) H1/H2/H3 headings, (c) any placeholder tokens, (d) any banned-term hits (`Derek`, `RevivaGo`, `Benji`, `revivago`, `benji`, `family`, `home`, `blog`, gtd-life-specific context values like `vixxo | revivago | personal`).
  - [x] Specifically flag two known gtd-life issues that MUST be repaired during the port (not merely copied): (1) `meetings/_template/meeting.md` frontmatter has `context: "" # vixxo | revivago | personal` — this inline comment enumerates personal-scope context values and MUST be scrubbed to work-scoped values (e.g. `# e.g. vixxo | customer | internal`) or removed. (2) `inbox/_template.md` frontmatter has `context: vixxo | revivago | personal` (value, not comment) — MUST be changed to an empty-string value `context: ""` with an optional work-scoped comment.
  - [x] Flag one known structural defect in the gtd-life source: `appreciations/_template.md` opens with `---` (frontmatter start) then writes `## type: appreciation` (an H2 heading) inside the frontmatter block — the frontmatter never closes and `type` is never actually set as a YAML key. The port MUST repair this into a properly-formed frontmatter (`---\n...keys...\n---`) before emitting the file.
  - [x] Inspect `~/Public/gtd-life/memory/_templates/*.md` (the alternate single-file template tree at the vault root). Record that these exist but are OUT OF SCOPE for Story 3.1 (the story targets per-directory `_template.md` / `_template/` conventions, not the top-level `_templates/` folder). Document this scope boundary.
  - [x] Record the known gtd-life directories that are explicitly OUT OF SCOPE for Story 3.1: `memory/daily/` (handled by Story 3.2 / obsidian config), `memory/companies/` (not in any current Epic 3 story), `memory/blog-ideas/` (personal; banned), `memory/vixxo/` (company-specific content; not template), `memory/me/` (Story 3.3), `memory/_templates/` (alternate layout; not the per-dir convention this story enforces).
  - [x] Persist all findings at `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md` with sections: `# Story 3.1 Baseline Audit`, `## gtd-life source inventory`, `## Per-file frontmatter + heading map`, `## Banned-term scan of source files`, `## Known defects requiring repair during port`, `## Out-of-scope directories`, `## Placeholder vocabulary across source files`, `## Mapping: source path → target path`.

- [x] Task 2 — Canonical blueprint for the nine ported files (AC: 1, 2, 3, 4, 5, 6, 8) **[Parallelizable with Task 1]**
  - [x] Author a blueprint document at `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` that specifies, for each of the nine target files, the EXACT frontmatter keys (in order), the EXACT H1/H2/H3 heading text (in order), and the allowed placeholder tokens. The harness's `task3` gate reads this blueprint (or encodes it as constants) to assert shape. Follow the Story 2.3 `canonical-blueprint.md` precedent.
  - [x] Blueprint for `memory/meetings/_template/meeting.md`: frontmatter keys `type, date, time, attendees, context, location, join_url, organizer, recurring, action_items, created, updated, tags` in order; body headers `# {{Meeting Title}}`, `## Summary`, `## Notes`, `## Decisions`, `## Action Items`; doc-link table with `[prep.md](prep.md)`, `[agenda.md](agenda.md)`, `[transcript.md](transcript.md)` cells.
  - [x] Blueprint for `memory/meetings/_template/agenda.md`: body headers `# Agenda -- {{Meeting Title}}`, `## Topics`, `## Parking Lot`; one checkbox placeholder line `- [ ] {{topic}} ({{owner}}, {{estimated minutes}})`.
  - [x] Blueprint for `memory/meetings/_template/prep.md`: body headers `# Prep -- {{Meeting Title}}`, `## My Objectives`, `## Questions to Raise`, `## Attendee Context`, `## Prior Meeting History`, `## Related Tasks`, `## Commercial Context`.
  - [x] Blueprint for `memory/meetings/_template/transcript.md`: body headers `# Transcript -- {{Meeting Title}}`; `**Source:**` line + `**Recording:**` line + horizontal rule (`---`).
  - [x] Blueprint for `memory/people/_template.md`: frontmatter keys `type, company, role, email, last_1on1, open_action_items, created, updated, tags` in order; body headers `# {{Name}}`, `## Overview`, `## 1-on-1 History`, `## Action Items`, `## Notes`; `## Overview` contains bold-label lines `**Company**`, `**Role**`, `**Reports to**`, `**Direct reports**`.
  - [x] Blueprint for `memory/decisions/_template.md`: frontmatter keys `type, status, date, context, stakeholders, created, updated, tags` in order; body headers `# {{Decision Title}}`, `## Context`, `## Alternatives`, `### Option A: {{name}}`, `### Option B: {{name}}`, `## Decision`, `## Rationale`, `## Implications`.
  - [x] Blueprint for `memory/reference/_template.md`: frontmatter keys `type, created, updated, context, related_to, tags` in order; body headers `# {{Reference Title}}`, `## Summary`, `## Details`, `## Links`, `## Related notes`.
  - [x] Blueprint for `memory/inbox/_template.md`: frontmatter keys `type, created, context, tags` in order with `context: ""` (empty string, no personal enumeration); body single heading `# Thought`.
  - [x] Blueprint for `memory/appreciations/_template.md` (REPAIRED shape; do not copy the malformed source): frontmatter keys `type, date, recipient, context, tags` in order opened and closed by `---`; body headers `# {{Recipient or Moment}}`, `## What`, `## Why it mattered`.
  - [x] Blueprint banned-term lock: list every banned token the harness must reject under `## Banned-term lock`. Set: `derek, neighbors, revivago, benji, flowtopic, gtd-life, gtdlife, wyoming, cheyenne, family, home, blog, wife, son, daughter, dog` (all boundary-guarded, case-insensitive). Also lock placeholder-vocabulary allowlist under `## Placeholder vocabulary lock`: `{{Meeting Title}}, {{Name}}, {{topic}}, {{owner}}, {{estimated minutes}}, {{person}}, {{action}}, {{date}}, {{company}}, {{role}}, {{manager or "N/A"}}, {{count or "N/A"}}, {{Decision Title}}, {{Reference Title}}, {{Recipient or Moment}}, {{action item}}, {{name}}` plus literal tokens `YYYY-MM-DD`, `HH:MM`.

- [x] Task 3a — Port `memory/meetings/_template/` bundle (AC: 1, 7, 8) **[Parallelizable with 3b–3f once Task 2 blueprint is written]**
  - [x] Create the directory `memory/meetings/_template/` (bash: `mkdir -p memory/meetings/_template`).
  - [x] Author `memory/meetings/_template/meeting.md` per the Task 2 blueprint. Port the gtd-life source (`~/Public/gtd-life/memory/meetings/_template/meeting.md`) VERBATIM for structure but scrub the `context:` inline comment (`# vixxo | revivago | personal` → `# e.g. vixxo | customer | internal` OR remove the comment entirely). Keep all frontmatter keys in source order. Ensure the doc-link table and all four H2 sections (`## Summary`, `## Notes`, `## Decisions`, `## Action Items`) are present. End file with a single trailing newline.
  - [x] Author `memory/meetings/_template/agenda.md` per the Task 2 blueprint. Port the gtd-life source structure byte-compatible (two H2 sections, one checkbox placeholder line). No banned tokens present in source; port clean.
  - [x] Author `memory/meetings/_template/prep.md` per the Task 2 blueprint. Port all six H2 sections (`## My Objectives`, `## Questions to Raise`, `## Attendee Context`, `## Prior Meeting History`, `## Related Tasks`, `## Commercial Context`). The source references `memory/people/` (for attendee context) and `Salesforce / deal context` (for commercial) — these are allowed generic references and should be preserved. No banned tokens.
  - [x] Author `memory/meetings/_template/transcript.md` per the Task 2 blueprint. Port the header shape (`**Source:**`, `**Recording:**`, horizontal rule, placeholder comment). The source enumerates `gong | teams | manual | otter | none` for the Source field — these are neutral tool names and may be kept, except confirm `otter` is OK (not a PII token). No banned tokens.
  - [x] After authoring all four files, run a per-file banned-term scan locally (`grep -iE '(^|[^A-Za-z])(derek|revivago|benji|family|home|blog)($|[^A-Za-z])'` across the four files) and confirm zero hits.

- [x] Task 3b — Port `memory/people/_template.md` (AC: 2, 7, 8) **[Parallelizable with 3a, 3c–3f]**
  - [x] Create the directory `memory/people/` (bash: `mkdir -p memory/people`).
  - [x] Author `memory/people/_template.md` per the Task 2 blueprint. Port the gtd-life source shape. Ensure frontmatter keys appear in source order (`type, company, role, email, last_1on1, open_action_items, created, updated, tags`). Ensure body has `# {{Name}}`, `## Overview` (with `**Company**`, `**Role**`, `**Reports to**`, `**Direct reports**` bold-label lines), `## 1-on-1 History`, `## Action Items`, `## Notes`. Preserve `{{Name}}`, `{{company}}`, `{{role}}`, `{{manager or "N/A"}}`, `{{count or "N/A"}}`, `{{action item}}` placeholders.
  - [x] Scan for banned tokens. `1-on-1` is NOT a banned token; it contains `on` which is a substring of `donations` etc. but boundary-guarded scans won't match `-on-` or `1-on-1`. No repair needed. Preserve as-is.

- [x] Task 3c — Port `memory/decisions/_template.md` (AC: 3, 7, 8) **[Parallelizable with 3a, 3b, 3d–3f]**
  - [x] Create the directory `memory/decisions/` (bash: `mkdir -p memory/decisions`).
  - [x] Author `memory/decisions/_template.md` per the Task 2 blueprint. Port the gtd-life source shape. Frontmatter keys in source order (`type, status, date, context, stakeholders, created, updated, tags`). Body: `# {{Decision Title}}`, `## Context`, `## Alternatives` (with two H3 sub-sections `### Option A: {{name}}`, `### Option B: {{name}}`), `## Decision`, `## Rationale`, `## Implications`. No banned tokens in source; port clean.

- [x] Task 3d — Port `memory/reference/_template.md` (AC: 4, 7, 8) **[Parallelizable with 3a–3c, 3e–3f]**
  - [x] Create the directory `memory/reference/` (bash: `mkdir -p memory/reference`).
  - [x] Author `memory/reference/_template.md` per the Task 2 blueprint. Port the gtd-life source shape. Frontmatter keys in source order (`type, created, updated, context, related_to, tags`). Body: `# {{Reference Title}}`, `## Summary`, `## Details`, `## Links`, `## Related notes`. Preserve the inline comment under `## Related notes` that explains cross-linking via the `related_to` frontmatter field — it is generic and useful. No banned tokens.

- [x] Task 3e — Port `memory/inbox/_template.md` (AC: 5, 7, 8) **[Parallelizable with 3a–3d, 3f]**
  - [x] Create the directory `memory/inbox/` (bash: `mkdir -p memory/inbox`).
  - [x] Author `memory/inbox/_template.md` per the Task 2 blueprint. Port the gtd-life source shape BUT scrub the personal-enumerated `context:` value. Source has `context: vixxo | revivago | personal` (as a frontmatter VALUE, which is a YAML syntax error anyway — the pipe characters don't mean "or" in YAML). Rewrite to `context: ""` with an optional comment `# e.g. vixxo | customer | internal`. Frontmatter keys: `type, created, context, tags`. Body: single `# Thought` H1 heading.

- [x] Task 3f — Port `memory/appreciations/_template.md` (REPAIR + AUTHOR, AC: 6, 7, 8) **[Parallelizable with 3a–3e]**
  - [x] Create the directory `memory/appreciations/` (bash: `mkdir -p memory/appreciations`).
  - [x] REPAIR the malformed gtd-life source. Source structure: `---\n\n## type: appreciation\n\ndate: YYYY-MM-DD\nrecipient: ""\ncontext: ""\ntags: []` — frontmatter opens with `---` but never closes; `type: appreciation` is written as an H2 heading inside the frontmatter (YAML syntax error); keys `date`, `recipient`, `context`, `tags` appear as plain text inside an unclosed frontmatter block, not as YAML keys. The port MUST emit a PROPERLY-FORMED file, not copy the defect.
  - [x] Author the repaired file with: frontmatter opened by `---` on line 1, keys in order (`type: appreciation`, `date: YYYY-MM-DD`, `recipient: ""`, `context: ""`, `tags: []`), frontmatter closed by `---` on the following line. Body: `# {{Recipient or Moment}}` H1, `## What` H2 (short description of what the appreciation is for), `## Why it mattered` H2 (why it's worth capturing). Empty-section convention matches the other ported templates.
  - [x] No banned tokens in source; no banned tokens in the repaired version. Confirm with a local scan.

- [x] Task 4 — Author the deterministic validation harness (AC: 10, 11) **[Sequential — depends on Task 2 blueprint AND Tasks 3a–3f templates existing]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`. Model on `story-2-3-work-persona-validation.sh`. `#!/usr/bin/env bash` on line 1, `set -euo pipefail` on line 2, `chmod +x`. POSIX-bash-3.2, BSD+GNU-grep compatible.
  - [x] Declare constants at the top:
    - `MEMORY_DIR="${PROJECT_ROOT}/memory"`
    - `MEETINGS_TEMPLATE_DIR="${MEMORY_DIR}/meetings/_template"`
    - Nine file-path constants: `MEETING_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/meeting.md"`, `AGENDA_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/agenda.md"`, `PREP_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/prep.md"`, `TRANSCRIPT_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/transcript.md"`, `PEOPLE_TEMPLATE="${MEMORY_DIR}/people/_template.md"`, `DECISIONS_TEMPLATE="${MEMORY_DIR}/decisions/_template.md"`, `REFERENCE_TEMPLATE="${MEMORY_DIR}/reference/_template.md"`, `INBOX_TEMPLATE="${MEMORY_DIR}/inbox/_template.md"`, `APPRECIATIONS_TEMPLATE="${MEMORY_DIR}/appreciations/_template.md"`
    - `BASELINE_AUDIT_PATH="${TESTS_DIR}/story-3-1-baseline-audit.md"`
    - `BLUEPRINT_PATH="${TESTS_DIR}/story-3-1-canonical-blueprint.md"`
    - Seven prior-harness paths: `STORY_1_1_HARNESS`, `STORY_1_2_HARNESS`, `STORY_1_3_HARNESS`, `STORY_2_1_HARNESS`, `STORY_2_2_HARNESS`, `STORY_2_3_HARNESS`, `STORY_2_4_HARNESS`
    - `BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])'` (case-insensitive via `grep -iE`)
    - `PLACEHOLDER_ALLOWLIST="..."` newline-separated allowed placeholder tokens (per Task 2 blueprint)
  - [x] Implement `regex_self_probe()` that exercises both the banned-term regex (`derek` matches; `derekson` is boundary-rejected; `family` matches; `familial` boundary-rejected) AND the placeholder-allowlist shape (`{{Meeting Title}}` allowed; `{employee_name}` single-brace rejected). Fail-fast `fail "regex probe: ..."` on mismatch.
  - [x] `check_task1` — require `BASELINE_AUDIT_PATH` exists, contains title `# Story 3.1 Baseline Audit`, and contains each required section header (`gtd-life source inventory`, `Per-file frontmatter + heading map`, `Banned-term scan of source files`, `Known defects requiring repair during port`, `Out-of-scope directories`, `Placeholder vocabulary across source files`, `Mapping: source path → target path`).
  - [x] `check_task2` — require `BLUEPRINT_PATH` exists, contains title `# Story 3.1 Canonical Blueprint`, and contains one section per target file plus `## Banned-term lock` and `## Placeholder vocabulary lock` sections.
  - [x] `check_task3` — per-file shape verification. For each of the nine target files: assert `[[ -f <path> ]]`, assert `[[ -s <path> ]]` (non-empty), assert frontmatter opens with `---` on line 1 and closes with `---` on a subsequent line (count `---` occurrences; must be ≥ 2 for YAML-frontmatter files, or verify via `awk` that lines 1 and N both equal `---`). For each required frontmatter key per the blueprint, assert it appears in the frontmatter block (not body) via `awk '/^---$/{n++;next} n==1' <file> | grep -Fxq "<key>: ..."` or equivalent. For each required H1/H2/H3 header per the blueprint, assert it appears in the file via `grep -Fxq`. For the meetings bundle, additionally assert the doc-link table in `meeting.md` contains `[prep.md](prep.md)`, `[agenda.md](agenda.md)`, `[transcript.md](transcript.md)`. For `appreciations/_template.md`, additionally assert the file does NOT contain `## type: appreciation` as a heading (the defect from gtd-life) — this is the "repaired, not copied" assertion.
  - [x] `check_task4` — cross-file scrub. For each of the nine target files, run `grep -iEq "${BANNED_TERMS_REGEX}" <file>` and FAIL the gate if any match. Additionally run `grep -Fq 'gtd-life' <file>` and FAIL if any file contains the literal string `gtd-life` (path reference). Additionally enumerate placeholders: use `grep -oE '\{\{[^}]+\}\}' <file> | sort -u` to extract placeholder tokens from each file, then assert every extracted token appears in the allowlist (or is `YYYY-MM-DD` / `HH:MM`) — anything not in the allowlist is a violation. Also assert zero single-brace `{placeholder}`, zero `<placeholder>`, zero `%placeholder%`, zero `${placeholder}` tokens (via targeted regex probes).
  - [x] `check_task5` — self-check. Assert `head -n 1` equals `#!/usr/bin/env bash`; assert `grep -Fq 'set -euo pipefail'`; assert every case arm present (`task1)`–`task6)` and `all)`); assert each declared constant name appears (`MEMORY_DIR=`, `MEETINGS_TEMPLATE_DIR=`, the nine file-path constants, `BASELINE_AUDIT_PATH=`, `BLUEPRINT_PATH=`, seven `STORY_*_HARNESS=`, `BANNED_TERMS_REGEX=`, `PLACEHOLDER_ALLOWLIST=`); assert `declare -F regex_self_probe >/dev/null 2>&1` (F4 pattern from Story 2.4 review).
  - [x] `check_task6` — regression. For each of the seven predecessor harness paths, `require_file_exists` and invoke `bash "${harness}" all 2>&1`. Capture combined stdout/stderr; echo on non-zero exit per Story 2.2 Phase 4 F6 pattern; `fail` with sub-harness name on any non-zero exit. All seven must return zero.
  - [x] Implement the `mode` dispatcher: `case "${mode}" in task1) check_task1 ;; ... task6) check_task6 ;; all) check_task1; echo "PASS: task1"; ...; check_task6; echo "PASS: task6" ;; *) fail "unknown mode: ${mode}" ;; esac`; end with `echo "PASS: ${mode}"`.
  - [x] Add header comment block stating: (a) Story 3.1 is the memory-template tree port from gtd-life; (b) scope is nine files (four under `meetings/_template/`, five single-file `_template.md` under five sibling subdirs); (c) `.obsidian/` is Story 3.2; (d) `memory/me/identity.md` + `preferences.md` is Story 3.3; (e) regression chain extends Story 2.4's seven-harness chain.

- [x] Task 5 — Regression run (AC: 10, 11) **[Sequential — depends on Task 4 harness existing and Tasks 3a–3f templates landed]**
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh all`. Capture the full transcript.
  - [x] Re-run each predecessor harness individually in `all` mode. All seven must exit `0` with `PASS: all`.
  - [x] Capture the full command-and-transcript log for inclusion in the Task 6 handoff artifact.

- [x] Task 6 — Handoff readiness package (AC: 10, 11, 13) **[Sequential — depends on Task 5]**
  - [x] Persist `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` with: (a) AC-to-file map (one row per AC pointing at the harness gate, file path, or grep output that proves it); (b) full validation command transcript (Story 3.1 harness + seven regression harnesses); (c) byte-counts and SHA-256 checksums of the nine ported template files (for future drift detection); (d) forward-looking notes: Story 3.2 will add `.obsidian/`; Story 3.3 will add `memory/me/identity.md` + `preferences.md`; Epic 4 Story 4.1 will reference `memory/people/` in the persona's Available-MCP context without needing template changes; Epic 6 Story 6.2 can invoke this harness as a CI gate.
  - [x] Include a "zero-edit verification" block listing each of the seven predecessor harnesses, the four Story 2.2 rule files, Story 2.1 `agent-identity.mdc`, Story 2.3 `agents/personas/work.md`, the root context files, `README.md`, `LICENSE`, `.gitignore`, `memory/.gitkeep` — each asserted present and non-empty (full byte-for-byte identity verifiable via `git diff HEAD`).

- [x] Task 7 — Sprint tracker and story status synchronization (AC: 12) **[Independent; typically last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `3-1-port-template-trees-from-gtd-life-memory.status` from `backlog` to `ready-for-dev` during Phase 1 (SM pass); then to `review` at Dev handoff. Single `backlog → review` on-disk transition acceptable per Story 2.1 / 2.2 / 2.3 / 2.4 autonomous-swarm precedent. **[Phase 1 `backlog → ready-for-dev` complete at SM pass; Phase 2 `ready-for-dev → review` complete at Dev handoff 2026-04-20 after orchestrator's Story 1.1 harness integration fix unblocked the regression suite.]**
  - [x] Flip `epic-3.status` from `backlog` to `in-progress` on the Phase 1 edit (Story 3.1 is the first story in Epic 3; the first-story-opens-epic rule applies per the sprint-status header comment). **[Completed at Phase 1 SM pass.]**
  - [x] Update `last_updated` in `sprint-status.yaml` to `2026-04-20` on the Phase 1 edit. **[Completed at Phase 1 SM pass; unchanged at Phase 2 handoff — same calendar day.]**
  - [x] Preserve every comment, blank line, inline spacing, and entry ordering byte-for-byte. The only diff between pre-edit and post-edit files must be the two `status:` value changes (`3-1-...` entry and `epic-3` entry) plus the `last_updated` value change.

## Dev Notes

### Artifact availability

- Planning / tracking artifacts used by this story:
  - `_bmad/bmm/config.yaml` (BMAD v6.3.0; `user_name: Vixxo Employee`; `planning_artifacts` / `implementation_artifacts` path variables).
  - `_bmad-output/planning-artifacts/epics.md` — Epic 3 Story 3.1 AC at lines 254–264; Epic 3 overview at lines 252–286.
  - `_bmad-output/planning-artifacts/architecture.md` — present but thin (24 lines). Confirms template-only scope, macOS/Linux portability, `{{…}}` placeholder convention, secrets-via-.gitignore discipline. Story 3.1 inherits all four constraints.
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — story key `3-1-port-template-trees-from-gtd-life-memory`, Linear `AIP-31`, current status `backlog`; `epic-3.status` currently `backlog`.
  - Prior story files (all `done`): `1-1-scaffold-directory-structure-and-root-files.md`, `1-2-write-generic-readme-license-gitignore.md`, `1-3-write-generic-agents-claude-cursorrules.md`, `2-1-port-agent-identity-rule-generic.md`, `2-2-port-guardrail-and-formatting-rules.md`, `2-3-create-single-generic-work-persona.md`, `2-4-confirm-benji-inbox-default-not-ported.md`. Pattern source for harness structure, banned-term regex discipline, POSIX-ERE boundary guards, Phase-4 F-series review-fix pattern, autonomous-swarm status-collapse convention.
  - gtd-life source templates (reference only; never installed into the template): `~/Public/gtd-life/memory/meetings/_template/{meeting,agenda,prep,transcript}.md`, `~/Public/gtd-life/memory/people/_template.md`, `~/Public/gtd-life/memory/decisions/_template.md`, `~/Public/gtd-life/memory/reference/_template.md`, `~/Public/gtd-life/memory/inbox/_template.md`, `~/Public/gtd-life/memory/appreciations/_template.md`.
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` — does not exist. Story 3.1 relies on epics.md + architecture.md + sprint-status.yaml + prior-story-file patterns for all requirements.
  - `_bmad-output/planning-artifacts/ux-design-specification.md` — does not exist. Story 3.1 has no UX surface (file-system scaffolding only), so absence is not a blocker.
  - `_bmad/bmm/workflows/4-implementation/bmad-create-story/template.md` — does not exist at the configured path. Story 3.1 uses the emergent shape from Stories 1.1 → 2.4 (which form a de-facto template): Status line + Story statement + ACs + Tasks/Subtasks + Dev Notes (Artifact availability / Architectural constraints / Previous story learnings / Project Structure Notes / Testing Notes / Parallelization guidance / References) + Change Log + Dev Agent Record (populated by Dev) + Review Follow-ups (populated by Review) + Senior Developer Review (populated by Review).

### Epic 3 story partition (why 3.1 is "templates only, no personalization")

- **Story 3.1 (this story):** Port the empty per-directory template tree (`_template.md` / `_template/`) from gtd-life/memory with all Derek / RevivaGo / personal-context / malformed-frontmatter residue scrubbed. Creates nine template files. No identity, no preferences, no `.obsidian/` config.
- **Story 3.2 (backlog):** Port the portable `.obsidian/` config (Templates + Daily Notes + graph view) without Derek's vault history or workspace cache. Depends on the `memory/` tree existing (Story 3.1 provides that). Separate concern — Obsidian config is a separate layer from the template notes themselves.
- **Story 3.3 (backlog):** Seed `memory/me/identity.md` and `memory/me/preferences.md` with `scope: work` frontmatter and placeholder body. These are the targets of the Epic 5 setup wizard. Story 3.1 does NOT create `memory/me/`; it remains empty for 3.3 to populate.

Story 3.1 is deliberately narrow. Its entire job is: "make the vault-structure skeleton exist, matching gtd-life conventions, with zero personal leakage." Identity (3.3), Obsidian wiring (3.2), and wizard-driven personalization (Epic 5) are all downstream.

### Why port verbatim + scrub rather than rewrite from scratch

The gtd-life memory vault is a production-hardened set of templates that already interoperates with the agent-skills bundle (meeting-prep, person-note-fill, decision-capture, inbox-triage, appreciation-capture). Rewriting these templates from scratch would risk breaking the skill-to-template contract (skills that assume specific frontmatter keys or H2 sections). Porting verbatim — then scrubbing only the personal-context residue and repairing the known appreciations-frontmatter defect — preserves skill compatibility for the future `npx skills add vixxo-copilot/agent-skills` flow (Epic 5 Story 5.3).

Three classes of changes allowed during the port:
1. **Scrub personal-context enumerations** in inline comments (`# vixxo | revivago | personal` → `# e.g. vixxo | customer | internal` or remove). Applies to `meetings/_template/meeting.md` and `inbox/_template.md`. This removes `revivago` and `personal` context tokens without changing the shape of the template.
2. **Repair malformed frontmatter** in `appreciations/_template.md` — the gtd-life source has a YAML-syntax-invalid opening (`---` followed by `## type: appreciation` as a Markdown heading, never closed). The port MUST emit a properly-formed `---\n...\n---` frontmatter and add a minimal useful body (`## What`, `## Why it mattered`).
3. **Strip gtd-life-internal cross-references** if any. Auditing the source shows none are present — all template files use generic `{{placeholder}}` tokens and reference generic siblings (`memory/people/`, `memory/decisions/`). No port-time rewrite required beyond items 1 and 2.

Everything else — frontmatter key names, section headings, placeholder forms, checkbox conventions, doc-link tables — is ported byte-compatible to preserve skill compatibility.

### Banned-term set for Story 3.1

Story 3.1 extends the Story 2.1 / 2.2 / 2.3 / 2.4 banned-term set with Epic-3-specific tokens. Boundary-guarded regex: `(^|[^A-Za-z])TOKEN($|[^A-Za-z])`, case-insensitive via `grep -iE`.

**Carried forward from prior stories:**
- `derek`, `neighbors` — Derek's name (Story 2.1)
- `revivago`, `flowtopic` — personal business tokens (Story 2.2)
- `benji` — personal task-system token (Story 2.3 / 2.4)
- `gtd-life`, `gtdlife` — source-repo reference (Story 2.3)

**Added by Story 3.1:**
- `wyoming`, `cheyenne` — example PII location tokens (template files should not reference any specific geography)
- `family`, `wife`, `son`, `daughter`, `dog` — family/personal-life tokens (work-only scope)
- `home` — personal-life token
- `blog` — personal output channel (gtd-life has `memory/blog-ideas/`; the template must not reference it)

The harness MUST reject any of these 16 tokens (boundary-guarded, case-insensitive) in any of the nine ported files. The `gtd-life` path-reference scan is an additional `grep -Fq 'gtd-life'` check on top of the boundary-guarded regex (because `gtd-life` is hyphenated and the hyphen is not an alphabetic boundary).

### Placeholder vocabulary discipline

The template-vault files use `{{double-curly-brace}}` placeholders. This is a deliberate divergence from the identity-file placeholders (`{{employee_name}}`, `{{employee_role}}`) used by `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md` — those represent the operator's identity; these represent the SHAPE of a future note instance.

**Allowed placeholders in template files (per AC8):**

- Meeting-related: `{{Meeting Title}}`, `{{topic}}`, `{{owner}}`, `{{estimated minutes}}`, `{{person}}`, `{{action}}`, `{{date}}`
- Person-related: `{{Name}}`, `{{company}}`, `{{role}}`, `{{manager or "N/A"}}`, `{{count or "N/A"}}`, `{{action item}}`
- Decision-related: `{{Decision Title}}`, `{{name}}` (option name)
- Reference-related: `{{Reference Title}}`
- Appreciation-related: `{{Recipient or Moment}}`

**Forbidden placeholder forms in template files:**

- Single-brace `{placeholder}` — confusable with shell-variable syntax
- Angle-bracket `<placeholder>` — confusable with XML/HTML tags
- Percent-wrapped `%placeholder%` — confusable with Windows env vars
- Dollar-brace `${placeholder}` — confusable with shell-variable interpolation
- `{{employee_name}}`, `{{employee_role}}` — operator-identity placeholders; these belong in identity/persona files, not memory templates

The harness enforces the allowlist by extracting all `{{...}}` tokens from each file (`grep -oE '\{\{[^}]+\}\}' | sort -u`) and failing if any extracted token is not in the allowlist.

### Known gtd-life source defects to repair during port (do NOT copy verbatim)

1. **`appreciations/_template.md` has a malformed YAML frontmatter block.** Source bytes:
   ```
   ---

   ## type: appreciation

   date: YYYY-MM-DD
   recipient: ""
   context: ""
   tags: []
   ```
   Problem: `---` opens a YAML frontmatter block; `## type: appreciation` is then a Markdown H2 heading, not a YAML key; the frontmatter is never closed (no terminating `---`); keys `date`, `recipient`, `context`, `tags` are orphaned plain text, not YAML. The port MUST emit a properly-formed file:
   ```
   ---
   type: appreciation
   date: YYYY-MM-DD
   recipient: ""
   context: ""
   tags: []
   ---

   # {{Recipient or Moment}}

   ## What

   <!-- What are you appreciating? -->

   ## Why it mattered

   <!-- Why is this worth capturing? -->
   ```
2. **`inbox/_template.md` frontmatter has `context: vixxo | revivago | personal` as a VALUE** (not a comment). This is a YAML value that reads as the single string `"vixxo | revivago | personal"` — not what the author meant. Problem: (a) it enumerates `revivago` and `personal`, both banned; (b) it uses pipe-or semantics that aren't YAML. The port MUST change this to `context: ""` with an optional inline comment `# e.g. vixxo | customer | internal` (using only work-scoped enumeration values).
3. **`meetings/_template/meeting.md` frontmatter has `context: "" # vixxo | revivago | personal`** — the VALUE is correctly empty-string but the INLINE COMMENT enumerates personal-scope context values. Scrub the comment to `# e.g. vixxo | customer | internal` or remove it.

Defects 2 and 3 are personal-scope enumeration scrubs; defect 1 is a structural repair. All three are mandatory during the port.

**Known Story 1.1 harness allowlist exception (documented 2026-04-20 Phase 4 F1 review fix):** `story-1-1-scaffold-validation.sh` line 155 — its `memory/` subdir allowlist regex — is extended in a single additive line from `me|mcp|obsidian` to `me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations` to admit the six new Story 3.1 subdirectories. This is the same minimal-change pattern Story 2.1 used (commit `0db273b` added `me|mcp|obsidian`) and is classified as an integration fix, not a Story 3.1 scope expansion. AC11 and AC13 encode this exception explicitly. No other bytes in any predecessor harness are changed.

### Previous story learnings to carry forward

- **POSIX-ERE boundary guards** (Stories 2.1 / 2.2 / 2.3 / 2.4): `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` works on macOS BSD grep, GNU grep, and busybox/Alpine grep identically. Do NOT use `\b`, `\<`, `\>`, or Perl-compatible regex.
- **`regex_self_probe` fail-fast** (all prior stories): probe must exercise BOTH a positive case (token matches) and a negative case (boundary-embedded substring does not match) for at least one token. Story 3.1 should exercise at least two tokens (one from the carried-forward set, one from the Epic-3-added set) in both directions.
- **Phase 4 F6 sub-harness capture** (Story 2.2): `check_task6` regression gate must capture combined stdout/stderr (`2>&1`) when invoking sub-harnesses, echo the captured output on non-zero exit, and fail with the sub-harness name.
- **Autonomous-swarm status collapse** (Stories 2.1 / 2.2 / 2.3 / 2.4): `backlog → ready-for-dev → review` may collapse to a single on-disk `backlog → review` transition. Record the skipped hop in the Change Log.
- **Story 2.4 F4 review fix** — `check_task5` probe presence check uses `declare -F <function_name> >/dev/null 2>&1`, not `grep -Fq '<function_name>'` (a commented-out or deleted function body must not satisfy the gate). Story 3.1's `check_task5` applies the same pattern.
- **Story 2.4 F3 review fix** — `find` repo-wide scans use only `_bmad-output/` and `.git/` exclusions to match AC verbatim. If Story 3.1's harness needs a repo-wide scan, the exclusion set is `_bmad-output/` + `.git/` (no `_bmad/` exclusion — empirically verified safe).
- **Story 2.4 F1 review fix** — filesystem enumeration loops must be case-insensitive. Story 3.1's file enumeration is over EXACT paths (nine known files), not a glob, so case-sensitivity is moot — but the banned-term scan uses `grep -iE` to catch case-variant tokens regardless.
- **Additive-only discipline** (Story 2.4 AC8 precedent): Story 3.1 may create new files and modify only `sprint-status.yaml` + this story file. Any surprise edit to a prior story artifact is a regression.
- **Commit-message shape** (Epic 1 / 2 git log): `feat(epic-N): <change> (Story <key>)`. Story 3.1's commit should read `feat(epic-3): port template trees from gtd-life memory (Story 3-1-port-template-trees-from-gtd-life-memory)`.

### Architectural constraints

- **No runtime service, no application code.** Story 3.1 is pure file-system scaffolding plus a shell harness. No Node, no Python, no web surface.
- **No new dependencies.** `bash`, `grep`, `find`, `awk`, `sed`, `mkdir` are universally available on macOS and Linux developer machines and on `ubuntu-latest` / `macos-latest` CI images. Do not introduce `rg`, `yq`, or any other tool that is not POSIX-ubiquitous.
- **macOS / Linux portability.** POSIX-bash-3.2 compatible (macOS default `/bin/bash` is 3.2 without `brew install bash`). BSD-grep and GNU-grep compatible. No `find -printf` (GNU-only); use `find -print | head -n1` idioms. No `readlink -f` (GNU-only); use `cd "$(dirname ...)" && pwd`.
- **No shell-state mutation.** No `shopt -s nocaseglob`, no `LANG=` reassignment, no `export LC_ALL=`. Case-insensitive logic is per-invocation via `grep -i` or `tr '[:upper:]' '[:lower:]'`.
- **UTF-8 files with trailing newline.** Every emitted template file is UTF-8, ends with a single `\n`, has no CRLF line endings (LF only). Use `printf '%s\n'` or heredoc-to-file with trailing newline to guarantee this.
- **`.gitignore` contract preserved.** `memory/` is NOT in `.gitignore`; the nine ported template files ARE committed to git. This is correct — they are content, not secrets. Confirm no `memory/` entry sneaks into `.gitignore`.
- **Placeholder-driven identity discipline (architecture.md constraint).** Identity placeholders (`{{employee_name}}`, `{{employee_role}}`) are reserved for `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md`. Template files use content-shape placeholders (`{{Name}}`, `{{Meeting Title}}`) — the architecture.md "placeholder-driven identity fields" rule applies only to identity files, not to memory-note shapes.

### Project Structure Notes

- **Target files for this story (new — 12 files total):**
  - Template files (9):
    - `memory/meetings/_template/meeting.md`
    - `memory/meetings/_template/agenda.md`
    - `memory/meetings/_template/prep.md`
    - `memory/meetings/_template/transcript.md`
    - `memory/people/_template.md`
    - `memory/decisions/_template.md`
    - `memory/reference/_template.md`
    - `memory/inbox/_template.md`
    - `memory/appreciations/_template.md`
  - Test evidence (3):
    - `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md`
    - `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md`
    - `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (executable, 0755)
    - `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md`
- **Target files for this story (modified):**
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (`3-1-...status` flip, `epic-3.status` flip, `last_updated` update)
  - This story file (Dev Agent Record / Change Log / File List / checkboxes at Dev handoff)
- **Directory state expectations AFTER Story 3.1 lands:**
  - `memory/` contains `.gitkeep` (from Story 1.1), plus six subdirs: `meetings/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/`. No `me/`, no `companies/`, no `daily/`, no `blog-ideas/`, no `vixxo/` — those are out of scope.
  - `memory/meetings/` contains only `_template/` (a subdirectory with 4 files). No `.gitkeep` added (template files provide git-trackable content).
  - `memory/people/`, `memory/decisions/`, `memory/reference/`, `memory/inbox/`, `memory/appreciations/` each contain exactly one file: `_template.md`. No `.gitkeep` added.
  - `.cursor/rules/` remains exactly six entries (`.gitkeep` + five `.mdc` files from Story 2.1 / 2.2).
  - `agents/personas/` remains exactly two entries (`.gitkeep` + `work.md`).
  - All Story 1.x and Story 2.x artifacts remain byte-for-byte stable.
- **Forward-compatibility:**
  - Story 3.2 (`.obsidian/` config) will reference these template files in its Templates plugin config. The template filenames (`_template.md`, `_template/meeting.md`, etc.) must remain stable after Story 3.1 lands — Story 3.2 consumes them, does not rewrite them.
  - Story 3.3 (`memory/me/identity.md`, `memory/me/preferences.md`) will create a new `memory/me/` subdirectory. Story 3.1's harness does NOT assert absence of `memory/me/` (it only asserts the six Story-3.1-scoped subdirs exist and are correctly-shaped). Story 3.3 can land without Story 3.1 harness regression.
  - Epic 4 Story 4.1 / 4.4 (mcp.json, docs) do not touch `memory/`; independent of Story 3.1.
  - Epic 5 Story 5.2 (wizard) will WRITE to `memory/me/identity.md` (Story 3.3 territory) and may reference `memory/_template.md` paths in its output; Story 3.1 establishes those paths are stable.
  - Epic 6 Story 6.2 (GitHub Action) can invoke `bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh all` directly as a CI gate — harness contract is GitHub-Actions-native (exit 0 on pass, 1 on fail).

### Testing Notes

- **Suggested manual smoke commands (post-port, pre-harness):**
  - `ls memory/` (expect: `.gitkeep appreciations decisions inbox meetings people reference`)
  - `ls memory/meetings/_template/` (expect: `agenda.md meeting.md prep.md transcript.md`)
  - `find memory -name '_template.md'` (expect: 5 paths: people, decisions, reference, inbox, appreciations)
  - `head -20 memory/appreciations/_template.md` (expect: properly-formed `---` frontmatter, `type: appreciation` as YAML key not H2, closing `---`)
  - `grep -rE '(^|[^A-Za-z])(derek|revivago|benji|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])' memory/` — expect empty output
  - `grep -rF 'gtd-life' memory/` — expect empty output
  - `grep -roE '\{\{[^}]+\}\}' memory/ | cut -d: -f2 | sort -u` — lists all placeholder tokens; manually verify all are in the allowlist
- **Harness invocation:**
  - `bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh all` — expect `PASS: task1` → `PASS: task6` → `PASS: all`, exit `0`.
  - `bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh task3` — exercises the nine-file shape verification in isolation.
- **Regression (each must exit 0 with `PASS: all`):**
  - `bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all`
- **Self-contained harness:** no network, no external tools beyond `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tr`, `sort`, `cut`.

### Parallelization guidance

- **Task 1 (baseline audit) || Task 2 (canonical blueprint)** — both are pure-write operations against distinct evidence files (`story-3-1-baseline-audit.md` vs `story-3-1-canonical-blueprint.md`). No runtime coupling. A Dev swarm runs them concurrently in two subagents.
- **Tasks 3a–3f (port template files)** are all pairwise parallelizable AFTER Task 2 lands the blueprint (because each subagent reads the blueprint to know what shape to emit). Each task writes to distinct file paths:
  - 3a writes four files under `memory/meetings/_template/`
  - 3b writes `memory/people/_template.md`
  - 3c writes `memory/decisions/_template.md`
  - 3d writes `memory/reference/_template.md`
  - 3e writes `memory/inbox/_template.md`
  - 3f writes `memory/appreciations/_template.md`
  No shared-file contention across 3a–3f. A Dev swarm may run all six concurrently.
- **Task 4 (harness)** is sequential — must run AFTER Task 2 (blueprint encoded as constants in the harness) AND AFTER Tasks 3a–3f (so `check_task3` has files to verify).
- **Task 5 (regression)** is sequential — runs after Task 4 harness exists.
- **Task 6 (handoff)** is sequential — depends on Task 5 transcript.
- **Task 7 (sprint tracker)** is independent; Phase-1 edit flips statuses at story-creation time (SM pass), Phase-2 edit at Dev handoff.
- **Shared-file contention across the whole plan:**
  - Task 1 writes `story-3-1-baseline-audit.md` (unique).
  - Task 2 writes `story-3-1-canonical-blueprint.md` (unique).
  - Tasks 3a–3f write nine distinct template paths under `memory/` (no overlap).
  - Task 4 writes `story-3-1-memory-template-tree-validation.sh` (unique).
  - Task 6 writes `story-3-1-task6-handoff.md` (unique).
  - Task 7 modifies `sprint-status.yaml` (exclusive write).
  - This story file is written by Task 7 (SM-pass edits) and by the Dev swarm (handoff edits); serialize story-file writes per phase.

**Swarm parallelization summary (MOST IMPORTANT — orchestrator uses this to launch parallel dev agents):**

- **Parallel wave 1 (independent evidence artifacts):** Task 1 || Task 2 — two subagents, no coupling.
- **Parallel wave 2 (independent template-file authoring; 6-way fan-out):** Task 3a || Task 3b || Task 3c || Task 3d || Task 3e || Task 3f — six subagents, each writing to distinct file paths. Depends on wave 1 complete (Task 2 blueprint available).
- **Sequential after wave 2:** Task 4 (harness) → Task 5 (regression) → Task 6 (handoff).
- **Independent throughout:** Task 7 (sprint tracker) — run at Phase 1 (SM pass) and Phase 2 (Dev handoff).

### References

- `_bmad/bmm/config.yaml` — BMAD module metadata and artifact path variables.
- `_bmad-output/planning-artifacts/epics.md` lines 254–264 — Epic 3 Story 3.1 statement and acceptance criteria (source of truth).
- `_bmad-output/planning-artifacts/epics.md` lines 252–286 — Epic 3 overview and Story 3.2 / 3.3 relationship.
- `_bmad-output/planning-artifacts/architecture.md` lines 1–26 — placeholder discipline, portability, secret-management.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` lines 103–120 — Epic 3 block (current `backlog` state for both the epic and all three stories).
- `_bmad-output/implementation-artifacts/2-1-port-agent-identity-rule-generic.md` — POSIX-ERE banned-term regex, `regex_self_probe` seed pattern.
- `_bmad-output/implementation-artifacts/2-2-port-guardrail-and-formatting-rules.md` — Phase 4 F6 sub-harness-capture pattern in `check_task6` regression gate.
- `_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md` — canonical blueprint discipline; six-gate `task1`–`task6` + `all` dispatcher; banned-term set and boundary-guard discipline.
- `_bmad-output/implementation-artifacts/2-4-confirm-benji-inbox-default-not-ported.md` — additive-only discipline (AC8); autonomous-swarm status-collapse precedent; F1 / F3 / F4 review fixes to carry forward.
- `_bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh` — harness pattern to model (`PROJECT_ROOT`, `TESTS_DIR`, `SELF_PATH`, `fail()`, `require_file_exists()` helpers).
- `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` — Phase 4 F-series refinements.
- `_bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh` — canonical-blueprint-to-harness binding pattern; frontmatter-inside-body scanning via `awk '/^---$/{n++;next} n==1'` extraction.
- `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh` — `declare -F <fn>` probe-presence idiom; case-insensitive filesystem enumeration idiom; `find` repo-wide exclusion set.
- `~/Public/gtd-life/memory/meetings/_template/meeting.md` — gtd-life source (reference only; `context:` comment scrubbed during port).
- `~/Public/gtd-life/memory/meetings/_template/agenda.md` — gtd-life source (reference only; port verbatim structure).
- `~/Public/gtd-life/memory/meetings/_template/prep.md` — gtd-life source (reference only; port verbatim structure).
- `~/Public/gtd-life/memory/meetings/_template/transcript.md` — gtd-life source (reference only; port verbatim structure).
- `~/Public/gtd-life/memory/people/_template.md` — gtd-life source (reference only; port verbatim structure).
- `~/Public/gtd-life/memory/decisions/_template.md` — gtd-life source (reference only; port verbatim structure).
- `~/Public/gtd-life/memory/reference/_template.md` — gtd-life source (reference only; port verbatim structure).
- `~/Public/gtd-life/memory/inbox/_template.md` — gtd-life source (reference only; `context:` value scrubbed during port).
- `~/Public/gtd-life/memory/appreciations/_template.md` — gtd-life source (reference only; malformed frontmatter REPAIRED during port, not copied).
- Git log (`git log --oneline -n 15`) — Epic 2 commit style `feat(epic-2): <change> (Story <key>)`. Story 3.1 follows `feat(epic-3): port template trees from gtd-life memory (Story 3-1-port-template-trees-from-gtd-life-memory)`.

## Change Log

- 2026-04-20 (Phase 1, Bob — SM): Story file authored from Epic 3 Story 3.1 spec (epics.md lines 254–264). Extended the 8-AC epic skeleton into 13 acceptance criteria to cover per-file shape (AC1–AC6), zero-personal-content scrub (AC7), placeholder-vocabulary discipline (AC8), `.gitkeep` handling (AC9), harness wiring (AC10), regression (AC11), sprint lifecycle with epic-3 promotion (AC12), and additive-scope discipline (AC13). Task plan: 7 tasks with Tasks 3a–3f fanned out for 6-way parallelization on template-file authoring. `sprint-status.yaml` flipped `3-1-port-template-trees-from-gtd-life-memory.status` `backlog → ready-for-dev`, flipped `epic-3.status` `backlog → in-progress` (first-story-opens-epic), and updated `last_updated` to `2026-04-20`. Ready for Phase 2 Dev swarm pickup.
- 2026-04-20 (Phase 4, Amelia — Dev, Senior Developer Review fixes applied): Adversarial code review returned 7 findings (3 HIGH: F1 AC11/AC13 allowlist-exception codification, F2 AC1 per-directory exact-count assertions, F3 AC9 sentinel/.gitkeep invariance; 4 MEDIUM: F4 `personal` banned-token, F5 discriminator key-value asserts, F6 `{{name}}` allowlist enumeration in AC8, F7 per-sub-harness PASS line-count fingerprinting). All 7 applied: (1) AC11 + AC13 amended with explicit Story 2.1-precedent allowlist exception language + matching Dev Notes entry; (2) `check_task3` extended with a 6-row per-directory `ls -A | wc -l | tr -d '[:space:]'` count-spec loop plus an AC9 block that asserts `memory/.gitkeep` exists and is 0 bytes, and that no `.gitkeep|.keep|empty|placeholder` files exist at `find -mindepth 2 -type f` under `memory/`; (3) `BANNED_TERMS_REGEX` extended 16→17 tokens with `personal`; `regex_self_probe` extended with `personal note` (positive) and `personally` (negative) probes; blueprint's `## Banned-term lock` section extended to match; (4) new helper `assert_frontmatter_key_value` added; `check_task3` now asserts `type:` discriminators on all six templates (`meeting`, `person`, `decision`, `reference`, `inbox`, `appreciation`) plus `status: open` on decisions and `recurring: false` on meeting.md (if present, skipped gracefully); (5) `{{name}}` added to AC8 placeholder enumeration in the story file (blueprint + harness allowlist already listed it); (6) `check_task6` refactored into a per-harness spec loop that fingerprints `^PASS:` line counts — empirically captured as 1/1/1/1/10/7/7 across Stories 1.1/1.2/1.3/2.1/2.2/2.3/2.4. Full 8-harness regression re-run after fixes: all exit `0` with `PASS: all`. Story 3.1 harness `task3` pass-line trace now covers the two new Phase-4 F2 + F3 blocks; `task4` now exercises the enlarged banned-term regex; `task5` constant list unchanged; `task6` pass-count fingerprint matches empirical truth. Sprint-status.yaml `3-1-port-template-trees-from-gtd-life-memory.status` flipped `review → done`. Story `Status:` line flipped `review → done`. `epic-3.status` preserved at `in-progress` (Stories 3.2 / 3.3 still open). `last_updated` preserved at `2026-04-20` (same calendar day).
- 2026-04-20 (Phase 2, Amelia — Dev, wave-3 resumed): Regression blocker from the prior wave-3 HALT resolved. Orchestrator applied a one-line integration fix in main context to `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` (line 155): the `memory)` branch allowlist regex was extended from `^(\.gitkeep|.+\.md|me|mcp|obsidian)$` to `^(\.gitkeep|.+\.md|me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations)$` — the same pattern Story 2.1 commit `0db273b` used when it added `me|mcp|obsidian` in anticipation of Epic 3 subdirectories. This is an integration fix following an established precedent, not a Story 3.1 scope expansion. With the fix in place, Task 5 regression across all 8 harnesses (Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1) passes cleanly — every harness exits `0` with `PASS: all`. Task 6 handoff package authored at `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` (AC-to-evidence map, full regression transcript, SHA-256 checksums, forward-looking notes, zero-edit verification, documented integration-fix exception). Task 7 Phase-2 `ready-for-dev → review` flip applied to `sprint-status.yaml` (`epic-3.status` remains `in-progress`; `last_updated` remains `2026-04-20` — same calendar day). Story `Status:` line flipped `ready-for-dev → review`. Ready for Phase 3 Senior Developer Review.

## Dev Agent Record

### Agent Model Used

- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-1 slot (Task 2 only).
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-1 slot (Task 1 only). Read-only against `~/Public/gtd-life/memory/`; write-only to the new audit artifact and this story file's Task 1 checkboxes + Dev Agent Record additions.
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-2 slot (Task 3e only). Read-only against `~/Public/gtd-life/memory/inbox/_template.md`; write-only to `memory/inbox/_template.md` and this story file's Task 3e checkboxes + Dev Agent Record / File List additions.
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-2 slot (Task 3b only). Read-only against `~/Public/gtd-life/memory/people/_template.md`; write-only to `memory/people/_template.md` plus Task 3b checkboxes and appended Dev Agent Record entries in this story file.
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-2 slot (Task 3f only). Read-only against `~/Public/gtd-life/memory/appreciations/_template.md` (Defect #1 malformed-frontmatter source); write-only to `memory/appreciations/_template.md` (REPAIRED emission) and this story file's Task 3f checkboxes + Dev Agent Record additions.
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-2 slot (Task 3d only). Read-only against `~/Public/gtd-life/memory/reference/_template.md`; write-only to `memory/reference/_template.md` and this story file's Task 3d checkboxes + Dev Agent Record additions.
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-3 sequential slot (Tasks 4, 5, 6, 7). Authored `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Task 4), attempted Task 5 regression, and HALTED per the critical-rule `If harness F5 regression fails on any prior story's harness, STOP and report — do NOT mutate sprint-status.yaml`. Tasks 6 and 7 (Dev-handoff flip) intentionally deferred. See HALT entry below.
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm Phase-4 review-fix slot. Applied all 7 findings (F1 AC11/AC13 + F2 count asserts + F3 sentinel invariance + F4 `personal` banned token + F5 key-value asserts + F6 `{{name}}` AC8 enumeration + F7 PASS-count fingerprints). Modified three files (`story-3-1-memory-template-tree-validation.sh`, `story-3-1-canonical-blueprint.md`, `3-1-port-template-trees-from-gtd-life-memory.md`) plus `sprint-status.yaml` (single `review → done` flip). Did NOT touch any of the nine `memory/` template files, any predecessor harness, or any of the Task 1 / Task 2 / Task 6 evidence artifacts. Full 8-harness regression re-run post-fix confirmed all green.
- Amelia (Senior Software Engineer) — Claude Opus 4.7, autonomous Dev subagent, BMAD v6 swarm wave-3 RESUMED slot (Tasks 5, 6, 7 only). Orchestrator applied the one-line Story 1.1 harness memory-allowlist integration fix in main context (following Story 2.1 precedent). This subagent ran the 8-harness regression (all `PASS: all`, exit 0), authored `story-3-1-task6-handoff.md`, flipped `sprint-status.yaml` `3-1-port-template-trees-from-gtd-life-memory.status` from `ready-for-dev` to `review`, and flipped this story file's `Status:` line from `ready-for-dev` to `review`. Task 4 harness file was NOT modified by this run (untouched per the resume instructions). All nine template files (Tasks 3a–3f) untouched. `epic-3.status` and `last_updated` in `sprint-status.yaml` preserved (already at correct Phase-1 values).

### Debug Log References

- None; Task 2 is pure-spec authoring with no runtime execution. Blueprint verified via structural grep for the four harness-required anchors (title `# Story 3.1 Canonical Blueprint`, nine `## Blueprint —` sections, `## Banned-term lock`, `## Placeholder vocabulary lock`).
- Task 3e verification executed 2026-04-20 from repo root against `memory/inbox/_template.md` (8 lines, 72 bytes, UTF-8, LF-only, trailing newline):
  - `grep -iEc '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])' memory/inbox/_template.md` → `0`.
  - `grep -Fc 'gtd-life' memory/inbox/_template.md` → `0`.
  - `grep -oE '\{\{[^}]+\}\}' memory/inbox/_template.md | sort -u` → empty (no placeholders permitted per blueprint; inbox template is minimal-capture).
  - `grep -n '^context:' memory/inbox/_template.md` → `4:context: ""` (Defect #3 repair verified — gtd-life source value `vixxo | revivago | personal` scrubbed to empty string).
  - `grep -Fxn '# Thought' memory/inbox/_template.md` → `8:# Thought` (single H1 heading per blueprint).
  - `awk '/^---$/{n++} END{print n}' memory/inbox/_template.md` → `2` (frontmatter opens on line 1 and closes on line 6).
- Task 1 scans executed 2026-04-20 from repo root:
  - `ls -la ~/Public/gtd-life/memory/{meetings/_template,people,decisions,reference,inbox,appreciations}/` — enumerated the nine in-scope source files plus neighboring content.
  - `wc -lc` on the nine sources — captured byte/line counts for the inventory table.
  - Banned-term regex `grep -niE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])'` across all nine sources — 2 hits total: `meetings/_template/meeting.md:6` and `inbox/_template.md:4`, both matching `revivago` inside a `context:` comment/value. No hits in the remaining seven files.
  - Placeholder enumeration `grep -oE '\{\{[^}]+\}\}' <file> | sort -u` across all nine sources — 17 distinct `{{…}}` tokens, all already in the allowed form.
  - Literal-string scan `grep -F 'gtd-life'` across all nine sources — zero hits.
  - Post-write verification: all eight required section headers present in the audit artifact. Artifact size: 18,177 bytes / 245 lines.
- Task 3a scans executed 2026-04-20 from repo root:
  - `mkdir -p memory/meetings/_template` — created the bundle directory (sibling `memory/people/`, `memory/reference/` already existed from prior swarm-wave work).
  - Banned-term regex `grep -niE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])'` across the four ported files — zero hits (confirmed `revivago` scrubbed from the `context:` comment in `meeting.md`).
  - Literal-string scan `grep -nF 'gtd-life'` across the four ported files — zero hits.
  - Placeholder enumeration `grep -hoE '\{\{[^}]+\}\}' | sort -u` across the four files — 7 distinct tokens: `{{Meeting Title}}`, `{{action}}`, `{{date}}`, `{{estimated minutes}}`, `{{owner}}`, `{{person}}`, `{{topic}}` — all members of the Task 2 blueprint allowlist.
  - Forbidden placeholder form probes (single-brace `{x}`, percent `%x%`, dollar-brace `${x}`) across the four files — zero hits.
  - Trailing-newline verification via `tail -c 1 | xxd -p`: all four files end with `0x0a` (LF). Byte counts: `agenda.md`=250, `meeting.md`=828, `prep.md`=513, `transcript.md`=306.
- Task 3f scans executed 2026-04-20 from repo root:
  - `ls -la memory/appreciations/` — confirmed the directory did not pre-exist; `mkdir -p memory/appreciations` created it fresh.
  - `cat ~/Public/gtd-life/memory/appreciations/_template.md` — confirmed the Defect #1 malformed-frontmatter source (8 lines: line 1 `---`, line 3 `## type: appreciation` as H2, lines 5–8 orphaned `date`/`recipient`/`context`/`tags` keys outside a valid YAML block, no closing `---`). The source was read-only; the emitted file is a REPAIR, not a copy.
  - `grep -n '^## type: appreciation' memory/appreciations/_template.md` — zero hits in the emitted file. Defect #1 structural repair confirmed: `type: appreciation` appears as a YAML key inside a properly-closed frontmatter block, NOT as an H2 heading.
  - `grep -nE '^---$' memory/appreciations/_template.md` — exactly two hits (lines 1 and 7) confirming the frontmatter opens on line 1 and closes on line 7 before any body heading.
  - `grep -iE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])' memory/appreciations/_template.md` — zero hits across all 16 banned tokens (boundary-guarded, case-insensitive).
  - `grep -oE '\{\{[^}]+\}\}' memory/appreciations/_template.md | sort -u` — exactly one placeholder token: `{{Recipient or Moment}}`, which is on the Story 2 canonical blueprint's placeholder-vocabulary allowlist.
- Task 3d scans executed 2026-04-20 from repo root:
  - `ls -la memory/` — confirmed only `memory/.gitkeep` present pre-port (no collision at `memory/reference/`).
  - `mkdir -p memory/reference/` — directory created; no `.gitkeep` added (per AC9).
  - Verbatim port of `~/Public/gtd-life/memory/reference/_template.md` (26 lines, 506 bytes) to `memory/reference/_template.md` — source already clean per Task 1 audit (zero banned hits, zero literal `gtd-life` hits); no scrub required.
  - `wc -lc memory/reference/_template.md` — 26 lines, 506 bytes (byte-compatible with source).
  - Frontmatter verification: keys `type, created, updated, context, related_to, tags` appear in source order; opened by `---` on line 1; closed by `---` on line 8.
  - Heading verification: H1 `# {{Reference Title}}` present; H2 sections `## Summary`, `## Details`, `## Links`, `## Related notes` present in blueprint order.
  - Banned-term regex `grep -niE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])' memory/reference/_template.md` — 0 hits.
  - Literal-string scan `grep -Fn 'gtd-life' memory/reference/_template.md` — 0 hits.
  - Placeholder enumeration `grep -oE '\{\{[^}]+\}\}' memory/reference/_template.md | sort -u` — single token `{{Reference Title}}` (matches AC8 allowlist).
  - Trailing-newline check: file ends with single `\n`, UTF-8, LF line endings.
- Task 3b scans executed 2026-04-20 from repo root against `memory/people/_template.md` (34 lines, 561 bytes, UTF-8, LF-only, trailing newline — byte-compatible with `~/Public/gtd-life/memory/people/_template.md`):
  - `grep -iE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])' memory/people/_template.md` — exit 1 (zero hits); boundary-guarded banned-term lock satisfied across all 16 tokens.
  - `grep -nF 'gtd-life' memory/people/_template.md` — exit 1 (zero hits); literal path-reference scrub satisfied.
  - `awk '/^---$/{n++;next} n==1' memory/people/_template.md` — extracted nine frontmatter keys in blueprint-locked order: `type: person`, `company: ""`, `role: ""`, `email: ""`, `last_1on1: ""`, `open_action_items: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`.
  - `grep -nE '^#{1,3} ' memory/people/_template.md` — confirmed five headings in blueprint-locked order at lines 13 / 15 / 22 / 26 / 32: `# {{Name}}`, `## Overview`, `## 1-on-1 History`, `## Action Items`, `## Notes`.
  - `grep -Fq` probes for each required `## Overview` bold-label — all four present: `**Company**`, `**Role**`, `**Reports to**`, `**Direct reports**`.
  - `grep -oE '\{\{[^}]+\}\}' memory/people/_template.md | sort -u` — six distinct placeholders, all on the AC8 / blueprint allowlist: `{{Name}}`, `{{action item}}`, `{{company}}`, `{{count or "N/A"}}`, `{{manager or "N/A"}}`, `{{role}}`.
  - `grep -oE '(^|[^{])\{[^{][^}]*\}' memory/people/_template.md` — exit 1 (zero hits); single-brace placeholder form absent.
- Task 4 + attempted Task 5 regression executed 2026-04-20 from repo root by wave-3 subagent:
  - Authored `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (chmod +x) modelled on `story-2-4-benji-inbox-absence-validation.sh`. Six gates plus `all` dispatcher. Constants declared: `PROJECT_ROOT`, `TESTS_DIR`, `SELF_PATH`, `MEMORY_DIR`, `MEETINGS_TEMPLATE_DIR`, nine file-path constants (`MEETING_TEMPLATE`, `AGENDA_TEMPLATE`, `PREP_TEMPLATE`, `TRANSCRIPT_TEMPLATE`, `PEOPLE_TEMPLATE`, `DECISIONS_TEMPLATE`, `REFERENCE_TEMPLATE`, `INBOX_TEMPLATE`, `APPRECIATIONS_TEMPLATE`), `BASELINE_AUDIT_PATH`, `BLUEPRINT_PATH`, seven `STORY_*_HARNESS` paths (1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4), `BANNED_TERMS_REGEX` (16-token boundary-guarded POSIX-ERE), `PLACEHOLDER_ALLOWLIST` (17-token newline-separated).
  - Helper functions: `fail`, `require_file_exists`, `require_file_nonempty`, `read_frontmatter` (grep/awk first-two-`---` extractor, same shape as Story 2.3 harness), `assert_frontmatter_keys` (key presence + Defect #1 `## KEY:` H2-heading guard), `require_exact_headers` (heredoc-driven `grep -Fxq`), `regex_self_probe` (positive+negative probes for `derek` and `family` tokens plus `{{Meeting Title}}` / `{employee_name}` placeholder-form probe — two-token coverage as required by AC10).
  - Individual-gate transcript (from `bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh <gate>`):
    - `task1` → `PASS: task1` → `PASS: task1` (dispatcher tail), exit 0
    - `task2` → `PASS: task2` → `PASS: task2`, exit 0
    - `task3` → `PASS: task3` → `PASS: task3`, exit 0 (all nine file shapes, trailing-newline byte check via `tail -c 1 | od`, frontmatter keys, H1/H2/H3 headers, doc-link table cells in `meeting.md`, Defect #1 "repaired-not-copied" assertion in `appreciations/_template.md`, Defect #3 `context: ""` empty-string repair in `inbox/_template.md` — all verified)
    - `task4` → `PASS: task4` → `PASS: task4`, exit 0 (banned-term scan across all nine files → 0 hits; fixed-string `gtd-life` / `~/Public/gtd-life` / `/gtd-life/` scans → 0 hits; placeholder enumeration → all extracted tokens on 17-token allowlist; forbidden identity-placeholder names `{{employee_*}}` → 0 hits; forbidden single-brace / angle-bracket / percent / dollar-brace forms → 0 hits)
    - `task5` → `PASS: task5` → `PASS: task5`, exit 0 (shebang on line 1, `set -euo pipefail` present, all seven case arms + `all` dispatcher present, all 22 declared-constant names present, `declare -F regex_self_probe` satisfied per Story 2.4 F4 pattern)
    - `task6` → FAIL, exit 1, stderr transcript:

      ```
      FAIL: Unexpected non-scaffold content in memory: appreciations
      decisions
      inbox
      meetings
      people
      reference
      FAIL: task6: story-1-1-scaffold-validation.sh all returned non-zero
      ```

  - Running the Story 1.1 harness in isolation (`bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all`) reproduces the identical failure: its `check_task6` allowlist regex for entries under `memory/` (line ~155: `grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian)$'`) does not admit the six Story 3.1 subdirectories. This cascades to every predecessor harness that invokes Story 1.1 in its own `task6` regression chain: Story 2.1, 2.2, 2.3, and 2.4 each emit `FAIL: task6: story-1-1-scaffold-validation.sh all returned non-zero` transitively. Verified Story 2.1 harness in isolation — same failure trace. Story 1.2 and 1.3 harnesses pass cleanly (they do not invoke Story 1.1 in their regression chains).
  - **HALT RECORDED** per the autonomous-swarm critical rule *"If harness F5 regression fails on any prior story's harness, STOP and report — do NOT mutate sprint-status.yaml."* The Story 3.1 harness itself is healthy (gates task1–task5 all PASS clean). The regression blocker is a scope gap in the Story 1.1 harness's `memory/` allowlist — it was refactored by Story 2.1 (commit `0db273b`) to be extension-based + a literal-name allowlist (`me|mcp|obsidian`) anticipating future subdirs, but the six Story 3.1 subdirs were not included when that allowlist was authored. Resolving the HALT requires a human decision between two mutually-exclusive paths:
    - **Path A (recommended) — Extend the Story 1.1 allowlist.** Specifically, change the `memory)` branch regex in `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` (line ~155) from `grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian)$'` to an inclusive form, e.g. `grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations)$'`. Precedent: Story 2.1's commit `0db273b` did a similar one-line refactor with the rationale "so downstream stories do not need to edit the scaffold harness". This minimal one-line edit unblocks the Story 3.1 regression. If accepted, AC11 must be amended to acknowledge the Story-2.1-style one-line allowlist extension as an allowed exception (or the Story 1.1 harness's `check_task6` must be refactored to truly stop hard-coding memory/ subdir names — e.g. accept any directory name whose contents conform to the downstream story's shape).
    - **Path B — Amend Story 3.1 scope** to avoid creating new top-level memory subdirectories (e.g. consolidate all nine templates into a flat `memory/_templates/*.md` layout). This conflicts with AC1–AC6 which mandate the per-directory `_template.md` / `_template/` shape, and with the forward-compatibility assumption that Story 3.2 (`.obsidian/` templates plugin config) and Epic 4 Story 4.1 will reference these paths.

    Path A is the recommended resolution. Either way, the decision belongs to the story owner / SM; the autonomous Dev subagent did not apply either option.
  - Sprint-status.yaml Dev-handoff flip (`ready-for-dev → review`) DEFERRED by the wave-3 subagent per the same critical rule. The file remains in the Phase-1 SM-pass state (`3-1-port-template-trees-from-gtd-life-memory.status: ready-for-dev`, `epic-3.status: in-progress`, `last_updated: 2026-04-20`) — zero additional edits made by the wave-3 subagent.
  - Story-file `Status:` line remains `ready-for-dev` (not flipped to `review`) for the same reason.

### Completion Notes List

- Phase 4 Senior Developer Review fixes complete (all 7 findings resolved; see Change Log entry dated 2026-04-20 Phase 4 for the per-finding summary and the `## Senior Developer Review (AI)` section below for the review audit). Post-fix 8-harness regression: each of Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 exits `0` with `PASS: all`. Empirical PASS line counts 1/1/1/1/10/7/7/7 (the 7 predecessor harnesses + Story 3.1 itself) match the Phase-4 F7 fingerprint hardcoded in `check_task6`. Sprint-status.yaml `3-1-port-template-trees-from-gtd-life-memory.status` flipped `review → done`; story `Status:` flipped to `done`. No other files modified beyond the harness + blueprint + story file + sprint-status. Review artifacts preserved (Task 1 audit, Task 2 blueprint, Task 6 handoff). Harness `bash -n` syntax-check passes; POSIX bash 3.2 compatibility preserved (no associative arrays, no GNU-only grep flags, no `find -printf`, no `readlink -f`, no ripgrep, no Python).
- Task 3e (Port `memory/inbox/_template.md`) complete. Created directory `memory/inbox/` and authored `memory/inbox/_template.md` (8 lines, 72 bytes, UTF-8, LF, trailing newline) per the Task 2 canonical blueprint. Frontmatter keys in blueprint order: `type: inbox`, `created: YYYY-MM-DD`, `context: ""`, `tags: []`, opened by `---` on line 1 and closed by `---` on line 6. Body: single literal `# Thought` H1 on line 8 (no placeholders). Defect #3 repair applied: the gtd-life source carried `context: vixxo | revivago | personal` as a frontmatter VALUE on line 4; the port rewrites this to `context: ""` (empty string), scrubbing both the `revivago` banned token and the `personal`/`vixxo` enumeration. No optional explanatory comment retained (blueprint permits but does not require it). Verified against blueprint with boundary-guarded banned-term scan (16 tokens, zero hits), `gtd-life` fixed-string scan (zero hits), placeholder enumeration (empty set, as required for this minimal-capture template), and structural grep for the `# Thought` H1. Task 3e scope is exclusive to this single file; Tasks 1, 2, 3a, 3b, 3c, 3d, 3f, 4, 5, 6, 7 and `sprint-status.yaml` untouched by this run.
- Task 2 (Canonical blueprint authoring) complete. Authored `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` containing nine per-file blueprint sections (one per target template file under `memory/`), a `## Banned-term lock` section enumerating the 16 tokens plus the composite POSIX-ERE boundary-guarded regex and path-reference scrub, and a `## Placeholder vocabulary lock` section enumerating the 17-item `{{...}}` allowlist, two literal frontmatter tokens (`YYYY-MM-DD`, `HH:MM`), the four forbidden bracket forms, and the five forbidden `{{employee_*}}` identity-placeholder names. Blueprint structure matches Story 2.3 canonical-blueprint precedent and wires cleanly into the future Task 4 harness's `check_task2`, `check_task3`, and `check_task4` gates via the AC coverage map.
- Task 3d (Port `memory/reference/_template.md`) complete. Created directory `memory/reference/` and authored `memory/reference/_template.md` (506 bytes, 26 lines, UTF-8, LF line endings, trailing newline) via verbatim port from `~/Public/gtd-life/memory/reference/_template.md`. Source was already clean per Task 1 baseline audit (0 banned-term hits, 0 `gtd-life` literal hits, 100% `{{…}}` placeholder-form compliance), so no port-time scrub required. Verified against Task 2 canonical blueprint: frontmatter keys `type, created, updated, context, related_to, tags` in source order, `---`/`---` frontmatter delimiters on lines 1 and 8, body H1 `# {{Reference Title}}` + H2 sections `## Summary`, `## Details`, `## Links`, `## Related notes` in blueprint order, inline `<!-- Cross-links to memory/people, memory/meetings, memory/companies, memory/decisions, etc. ... -->` comment preserved under `## Related notes` (all references are generic; zero banned tokens). Single placeholder `{{Reference Title}}` in body — matches AC8 allowlist. Post-write per-file banned-term scan (boundary-guarded regex for all 16 tokens) returned 0 hits; literal-string `gtd-life` scan returned 0 hits. No `.gitkeep` sentinel added to `memory/reference/` (per AC9). Task 3d scope strictly limited to this single file + its parent directory + this story file's Task 3d checkboxes / Dev Agent Record / File List additions; no other tasks touched. Ready for Task 4 harness verification (`check_task3` gate will read this file per blueprint constants).
- Task 3f (Port `memory/appreciations/_template.md` with Defect #1 structural repair) complete. Created the directory `memory/appreciations/` and emitted `memory/appreciations/_template.md` as a REPAIRED file, not a verbatim copy of the malformed gtd-life source. The gtd-life source opens with `---` on line 1 and then writes `## type: appreciation` as a Markdown H2 heading (YAML syntax error — the frontmatter never closes and `type` is never set as a YAML key; `date`, `recipient`, `context`, `tags` appear as orphaned plain text). The emitted file repairs this by: (a) emitting `type: appreciation` as a YAML KEY (no `##` prefix) inside the frontmatter block; (b) closing the frontmatter with `---` on line 7 before any body heading; (c) emitting the canonical `# {{Recipient or Moment}}` H1 after the closing `---` and one blank line; (d) adding the two required H2 body sections `## What` and `## Why it mattered` per the Story 2 canonical blueprint, each with a single HTML-comment hint line. Frontmatter keys appear in the blueprint-locked order: `type`, `date`, `recipient`, `context`, `tags`. Zero banned tokens (all 16 tokens boundary-guarded, case-insensitive). Zero `gtd-life` path references. Single placeholder `{{Recipient or Moment}}` is on the allowlist. The emitted file does NOT contain the line `## type: appreciation` — satisfies the "repaired, not copied" assertion the Task 4 harness enforces in `check_task3`. File is UTF-8, LF line endings, ends with a single trailing newline. Tasks 1, 2, 3a, 3b, 3c, 3d, 3e, 4, 5, 6, 7 outside Task 3f scope; untouched by this run. `sprint-status.yaml` not modified.
- Task 3a (Port `memory/meetings/_template/` bundle) complete. Created the directory `memory/meetings/_template/` and authored all four ported template files verbatim-with-scrubs from the gtd-life source per the Task 2 canonical blueprint. (1) `meeting.md` — ported frontmatter in source order (13 keys: `type, date, time, attendees, context, location, join_url, organizer, recurring, action_items, created, updated, tags`) with Defect #2 scrubbed: `context: "" # vixxo | revivago | personal` → `context: "" # e.g. vixxo | customer | internal`. Body ported verbatim (H1 `# {{Meeting Title}}`, doc-link table with `[prep.md](prep.md)` / `[agenda.md](agenda.md)` / `[transcript.md](transcript.md)` cells, H2 sections `## Summary`, `## Notes`, `## Decisions`, `## Action Items`, plus the `{{person}}: {{action}} (due: {{date}})` checkbox line). (2) `agenda.md` — ported byte-compatible (H1 `# Agenda -- {{Meeting Title}}`, H2 `## Topics` with the `- [ ] {{topic}} ({{owner}}, {{estimated minutes}})` checkbox, H2 `## Parking Lot`). (3) `prep.md` — ported byte-compatible (H1 `# Prep -- {{Meeting Title}}` + six H2 sections in source order). (4) `transcript.md` — ported byte-compatible (H1 `# Transcript -- {{Meeting Title}}`, `**Source:** <!-- gong | teams | manual | otter | none -->`, `**Recording:** <!-- URL or path if available -->`, horizontal rule `---`, placeholder comment). All four files end with a single LF (`0x0a`) trailing newline; banned-term and placeholder-vocabulary scans clean; no `gtd-life` literal path references. Task 3a deliverable feeds Task 4's `check_task3` shape gate (nine-file verification) and `check_task4` cross-file scrub gate. Tasks 1, 2, 3b–3f, 4–7 outside Task 3a scope; untouched by this run.
- Task 3b (Port `memory/people/_template.md`) complete. Created directory `memory/people/` via `mkdir -p` and authored `memory/people/_template.md` (561 bytes, 34 lines, UTF-8, LF line endings, trailing newline) as a verbatim port of `~/Public/gtd-life/memory/people/_template.md`. Per the Task 1 baseline audit, the source was already clean (zero banned-term hits, zero `gtd-life` literal hits, fully blueprint-conformant placeholder forms), so no port-time scrub was required. Verified against the Task 2 canonical blueprint: frontmatter keys `type, company, role, email, last_1on1, open_action_items, created, updated, tags` appear in source order inside a properly-delimited `---`/`---` block (lines 1 and 11); body H1 `# {{Name}}` on line 13; H2 sections `## Overview`, `## 1-on-1 History`, `## Action Items`, `## Notes` in blueprint order; all four required bold-label lines (`**Company**`, `**Role**`, `**Reports to**`, `**Direct reports**`) present under `## Overview`; the `<!-- Append new entries at the top. Format: ### YYYY-MM-DD -->` comment preserved under `## 1-on-1 History`; the `- [ ] {{action item}}` checkbox preserved under `## Action Items`; the `<!-- General notes, context, working style, preferences. -->` comment preserved under `## Notes`. Placeholder enumeration extracted six distinct tokens — `{{Name}}`, `{{action item}}`, `{{company}}`, `{{count or "N/A"}}`, `{{manager or "N/A"}}`, `{{role}}` — every one on the AC8 allowlist. Post-write banned-term scan (boundary-guarded regex for all 16 tokens, case-insensitive) returned zero hits; literal-string `gtd-life` scan returned zero hits; single-brace/XML/percent/dollar-brace forbidden-form probes returned zero hits. No `.gitkeep` sentinel added to `memory/people/` (per AC9). Task 3b scope strictly limited to this one file + its parent directory + this story file's Task 3b checkboxes / Dev Agent Record / File List additions; Tasks 3a/3c/3d/3e/3f, Task 4 harness, Task 6 handoff, and Task 7 sprint tracker not touched.
- Task 1 (Baseline audit) complete. Produced `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md` (18,177 bytes, 245 lines) with all eight required sections (`# Story 3.1 Baseline Audit`, `## gtd-life source inventory`, `## Per-file frontmatter + heading map`, `## Banned-term scan of source files`, `## Known defects requiring repair during port`, `## Out-of-scope directories`, `## Placeholder vocabulary across source files`, `## Mapping: source path → target path`). Inventoried the nine in-scope gtd-life source files with byte/line counts, per-file frontmatter key lists (in source order), and H1/H2/H3 heading maps. Ran the Story 3.1 boundary-guarded banned-term regex across all nine sources and confirmed exactly two hits — both `revivago` inside `context:` scope markers (`meetings/_template/meeting.md:6` inline comment, `inbox/_template.md:4` frontmatter value) — with zero hits for the other 14 banned tokens. Flagged the three mandatory port repairs: (1) Defect #1 `appreciations/_template.md` malformed YAML frontmatter (`---` opener, no closer, `## type: appreciation` as an H2 heading, orphaned keys) — structural repair required; (2) Defect #2 `inbox/_template.md` `context: vixxo | revivago | personal` value — scrub to empty string; (3) Defect #3 `meetings/_template/meeting.md` `context: "" # vixxo | revivago | personal` inline comment — scrub or remove. Documented the seven out-of-scope gtd-life directories (alternate `memory/_templates/` layout, `memory/daily/`, `memory/companies/`, `memory/blog-ideas/`, `memory/vixxo/`, `memory/me/`, `memory/.obsidian/`). Locked the 17-token `{{…}}` placeholder vocabulary with 100% form compliance in source (zero single-brace, zero XML-style, zero percent-wrapped, zero shell-interpolation, zero identity-placeholder leakage). Locked the source → target mapping for all nine template files with port-mode annotations (6 port-verbatim, 2 port-verbatim+scrub, 1 REPAIR+author-body for appreciations). Task 1 deliverable feeds Task 2's canonical blueprint (frontmatter/heading maps + placeholder allowlist) and Task 4's `check_task1` harness gate (required section headers). Tasks 2–7 outside Task 1 scope; untouched by this run.
- Task 4 (Author the deterministic validation harness) complete. Emitted `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (executable, 0755) modelled on `story-2-4-benji-inbox-absence-validation.sh`. Six gates + `all` dispatcher, POSIX-bash-3.2 compatible, BSD+GNU-grep compatible, no rg, no python. Gates task1–task5 pass clean in isolation (verified by running each gate individually). Task 5 (Regression run) ATTEMPTED — the Story 3.1 harness's own `task6` regression gate reproduces the failure that every seven-harness execution now shows: the Story 1.1 harness's `check_task6` allowlist at `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh:155` (`grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian)$'`) does not admit Story 3.1's six new memory subdirectories (`appreciations`, `decisions`, `inbox`, `meetings`, `people`, `reference`). This cascades through Story 2.1 / 2.2 / 2.3 / 2.4 (all of which invoke Story 1.1 in their own regression chains). The Story 3.1 harness itself is healthy — gates 1–5 all PASS. Task 6 (Handoff package) and Task 7 (Dev-handoff sprint-status flip) NOT executed per critical rule: *"If harness F5 regression fails on any prior story's harness, STOP and report — do NOT mutate sprint-status.yaml."* Story status remains `ready-for-dev` (not flipped to `review`). See Debug Log References for the full individual-gate transcript and the two-path HALT resolution guidance.
- Task 5 / Task 6 / Task 7 (Regression + handoff + sprint-flip, wave-3 RESUMED) complete. Following the orchestrator's Story 1.1 harness memory-allowlist integration fix (applied in main context, following the Story 2.1 commit `0db273b` precedent — the `memory)` branch allowlist at line 155 was extended from `^(\.gitkeep|.+\.md|me|mcp|obsidian)$` to `^(\.gitkeep|.+\.md|me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations)$`), this resumed wave-3 subagent ran the full 8-harness regression suite from the repo root. All 8 harnesses (`story-1-1-scaffold-validation.sh`, `story-1-2-root-files-validation.sh`, `story-1-3-root-context-validation.sh`, `story-2-1-agent-identity-validation.sh`, `story-2-2-guardrail-and-formatting-validation.sh`, `story-2-3-work-persona-validation.sh`, `story-2-4-benji-inbox-absence-validation.sh`, `story-3-1-memory-template-tree-validation.sh`) exited `0` with `PASS: all`. The Story 3.1 harness's own `task6` gate — which invokes the seven predecessor harnesses internally — also exits `0`. Task 6 handoff artifact `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` authored with seven sections: (1) AC-to-evidence map (13 rows, one per AC), (2) full 8-harness command transcript, (3) per-file SHA-256 + byte-count table for drift detection, (4) forward-looking notes for Stories 3.2 / 3.3 / Epic 4 / Epic 5 / Epic 6, (5) zero-edit verification for seven predecessor harnesses + identity/rule/persona files + root context + root metadata, (6) explicit documentation of the Story 1.1 harness integration-fix exception, (7) ready-for-review certification. Task 7 Phase-2 flip applied: `sprint-status.yaml` `3-1-port-template-trees-from-gtd-life-memory.status` → `review`; `epic-3.status` preserved at `in-progress`; `last_updated` preserved at `2026-04-20` (same calendar day); all comments, blank lines, inline spacing, and entry ordering preserved byte-for-byte (only three value-level changes across the whole YAML file). Story `Status:` line flipped `ready-for-dev → review`. This resumed wave-3 subagent did NOT touch: any of the nine `memory/` template files (Tasks 3a–3f territory), the Story 3.1 harness itself (Task 4 territory), any of the seven predecessor harnesses (the Story 1.1 integration fix was applied by the orchestrator in main context before this subagent resumed), the baseline-audit artifact (Task 1 territory), the canonical-blueprint artifact (Task 2 territory), or any `.cursor/` / `agents/` / root-context / root-metadata files.
- Task 3c (Port `memory/decisions/_template.md`) complete. Created directory `memory/decisions/` and authored `memory/decisions/_template.md` (36 lines, 588 bytes, UTF-8, LF line endings, single trailing newline). Ported byte-compatible from `~/Public/gtd-life/memory/decisions/_template.md` — source was pre-scrubbed (zero banned-term hits under the Story 3.1 boundary-guarded regex, zero `gtd-life` literal-string hits, zero malformed frontmatter), so port was verbatim with no structural repairs. Verified against Story 3.1 canonical blueprint: (a) frontmatter opens `---` on line 1 and closes `---` on line 10 with exactly eight keys in spec order (`type: decision`, `status: open`, `date: YYYY-MM-DD`, `context: ""`, `stakeholders: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`); (b) body headings in spec order: `# {{Decision Title}}` (H1, line 12), `## Context` (H2, line 14), `## Alternatives` (H2, line 18), `### Option A: {{name}}` (H3, line 22), `### Option B: {{name}}` (H3, line 24), `## Decision` (H2, line 26), `## Rationale` (H2, line 30), `## Implications` (H2, line 34); (c) placeholder enumeration yields exactly `{{Decision Title}}` and `{{name}}` — both in the Story 3.1 placeholder vocabulary allowlist; zero single-brace `{...}`, zero angle-bracket `<...>`, zero percent-wrapped `%...%`, zero dollar-brace `${...}` placeholders; zero identity-placeholder leakage (`{{employee_*}}`). Verification commands run from repo root: boundary-guarded banned-term regex (`grep -iEn '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])'`) → 0 hits; fixed-string `grep -Fn 'gtd-life'` → 0 hits; placeholder enumeration `grep -oE '\{\{[^}]+\}\}' | sort -u` → 2 allowlist-valid tokens. Tasks 1, 2, 3a, 3b, 3d, 3e, 3f, 4, 5, 6, 7 outside Task 3c scope; untouched by this run. No edits to `sprint-status.yaml`.

### File List

Created:

- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` (Task 2)
- `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md` (Task 1; 18,177 bytes, 245 lines, UTF-8, LF line endings, trailing newline)
- `memory/reference/_template.md` (Task 3d; 506 bytes, 26 lines, UTF-8, LF line endings, trailing newline; verbatim port from `~/Public/gtd-life/memory/reference/_template.md` — source already clean, no scrub required)
- `memory/reference/` directory (Task 3d; created via `mkdir -p`; no `.gitkeep` sentinel added per AC9)
- `memory/people/_template.md` (Task 3b; 561 bytes, 34 lines, UTF-8, LF line endings, trailing newline; verbatim port from `~/Public/gtd-life/memory/people/_template.md` — source already clean, no scrub required)
- `memory/people/` directory (Task 3b; created via `mkdir -p`; no `.gitkeep` sentinel added per AC9)
- `memory/inbox/_template.md` (Task 3e; 72 bytes, 8 lines, UTF-8, LF line endings, trailing newline; port with Defect #3 repair — source frontmatter VALUE `context: vixxo | revivago | personal` scrubbed to `context: ""`)
- `memory/inbox/` directory (Task 3e; created via `mkdir -p`; no `.gitkeep` sentinel added per AC9)
- `memory/decisions/_template.md` (Task 3c; 588 bytes, 36 lines, UTF-8, LF line endings, trailing newline; verbatim port from `~/Public/gtd-life/memory/decisions/_template.md` — source already clean, no scrub required)
- `memory/decisions/` directory (Task 3c; created via `mkdir -p`; no `.gitkeep` sentinel added per AC9)
- `memory/appreciations/_template.md` (Task 3f; UTF-8, LF line endings, trailing newline; REPAIRED emission of the Defect #1 malformed-frontmatter gtd-life source — properly-formed YAML frontmatter with keys `type: appreciation`, `date: YYYY-MM-DD`, `recipient: ""`, `context: ""`, `tags: []` in blueprint-locked order opened by `---` on line 1 and closed by `---` on line 7; body `# {{Recipient or Moment}}` H1 + `## What` H2 + `## Why it mattered` H2 with HTML-comment hints; zero banned tokens; zero `gtd-life` literal path references; single allowlisted placeholder `{{Recipient or Moment}}`; file does NOT contain `## type: appreciation` as a heading — "repaired, not copied" assertion satisfied)
- `memory/appreciations/` directory (Task 3f; created via `mkdir -p`; no `.gitkeep` sentinel added per AC9)
- `memory/meetings/_template/meeting.md` (Task 3a; 828 bytes, UTF-8, LF line endings, trailing newline; port with Defect #2 scrub — inline comment on `context:` rewritten from `# vixxo | revivago | personal` to `# e.g. vixxo | customer | internal`; 13-key frontmatter in source order; doc-link table + four H2 sections preserved)
- `memory/meetings/_template/agenda.md` (Task 3a; 250 bytes, UTF-8, LF line endings, trailing newline; verbatim port from `~/Public/gtd-life/memory/meetings/_template/agenda.md` — source already clean)
- `memory/meetings/_template/prep.md` (Task 3a; 513 bytes, UTF-8, LF line endings, trailing newline; verbatim port from `~/Public/gtd-life/memory/meetings/_template/prep.md` — source already clean, six H2 sections preserved)
- `memory/meetings/_template/transcript.md` (Task 3a; 306 bytes, UTF-8, LF line endings, trailing newline; verbatim port from `~/Public/gtd-life/memory/meetings/_template/transcript.md` — source already clean; `**Source:**` / `**Recording:**` bold-label lines + horizontal rule preserved)
- `memory/meetings/_template/` directory (Task 3a; created via `mkdir -p`; no `.gitkeep` sentinel added per AC9)
- `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` (Task 6 wave-3 RESUMED subagent; 2026-04-20; UTF-8, LF line endings, trailing newline; seven sections — (1) AC-to-evidence map, (2) full 8-harness regression command transcript, (3) per-file SHA-256 + byte-count table for drift detection across all nine ported template files, (4) forward-looking notes for Stories 3.2 / 3.3 / Epic 4 / Epic 5 / Epic 6, (5) zero-edit verification for seven predecessor harnesses + identity / rule / persona / context / metadata files, (6) documented Story 1.1 harness integration-fix exception, (7) ready-for-review certification)
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Task 4 wave-3 subagent; executable 0755; UTF-8, LF line endings, trailing newline; six gates — `task1` baseline-audit evidence, `task2` canonical-blueprint evidence, `task3` per-file shape (existence + frontmatter keys + required headers + doc-link table in `meeting.md` + Defect #1 "repaired-not-copied" assertion in `appreciations/_template.md` + Defect #3 `context: ""` repair in `inbox/_template.md`), `task4` cross-file scrub (banned-term regex + fixed-string `gtd-life` scans + placeholder-vocabulary allowlist + forbidden placeholder-form probes + forbidden identity-placeholder names), `task5` self-check (shebang + `set -euo pipefail` + every case arm + 22 declared constants + `declare -F regex_self_probe` probe-presence), `task6` regression against seven predecessor harnesses (Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4) — plus `all` dispatcher; gates 1–5 pass clean; gate 6 fails due to Story 1.1 allowlist scope gap — see Dev Agent Record HALT entry)

Modified:

- `_bmad-output/implementation-artifacts/3-1-port-template-trees-from-gtd-life-memory.md` (Task 2 subtasks marked `[x]` and Dev Agent Record populated for Task 2 scope by the Task 2 subagent; Task 1 subtasks marked `[x]` and Dev Agent Record entries for Task 1 appended by this Task 1 subagent — additive, no overwrite of Task 2 entries; Task 3d subtasks marked `[x]` and Dev Agent Record / File List entries for Task 3d appended by the Task 3d subagent — additive, no overwrite of prior Task entries; Task 5 / Task 6 / Task 7 subtasks marked `[x]`, Dev Agent Record / Change Log / File List entries for the RESUMED wave-3 run appended, and `Status:` line flipped `ready-for-dev → review` by the RESUMED wave-3 subagent — additive, no overwrite of prior Task entries; Phase-4 review-fix edits applied by the review-fix subagent — AC8 allowlist gains `{{name}}`, AC11 + AC13 gain the Story 1.1 allowlist-exception language, Dev Notes gains the "Known Story 1.1 harness allowlist exception" paragraph, Change Log gains the 2026-04-20 Phase-4 entry, Dev Agent Record / Completion Notes / File List gain review-fix entries, `## Review Follow-ups (AI)` and `## Senior Developer Review (AI)` populated, and `Status:` flipped `review → done` — additive, no overwrite of prior Task entries)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 RESUMED wave-3 subagent — single value-level change: `3-1-port-template-trees-from-gtd-life-memory.status` flipped `ready-for-dev → review`; `epic-3.status` preserved at `in-progress`; `last_updated` preserved at `2026-04-20` — no comments, blank lines, inline spacing, or entry ordering modified; Phase-4 review-fix subagent — single additional value-level change: `3-1-port-template-trees-from-gtd-life-memory.status` flipped `review → done`; `epic-3.status` still preserved at `in-progress` (Stories 3.2 / 3.3 still open); `last_updated` still at `2026-04-20`)
- `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` (integration fix applied by the orchestrator in main context — NOT by any Story 3.1 subagent — following the Story 2.1 commit `0db273b` precedent; single one-line change to the `memory)` branch allowlist regex on line 155: `me|mcp|obsidian` extended to `me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations` to admit the six new Story 3.1 subdirectories; classified as an integration fix, not a Story 3.1 scope expansion; codified as an AC11 / AC13 exception in the Phase-4 F1 review fix; documented in the Task 6 handoff package §6)
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Phase-4 review-fix subagent — F2 per-directory count assertions (6-row spec loop via `ls -A | wc -l | tr -d '[:space:]'`) + F3 AC9 sentinel invariance block (`memory/.gitkeep` size check + `find -mindepth 2 -type f -name <sentinel>` negative check) added to `check_task3`; F4 `personal` appended to `BANNED_TERMS_REGEX` (16→17 tokens) + positive/negative self-probes added to `regex_self_probe`; F5 new helper `assert_frontmatter_key_value` added and wired into `check_task3` for `type:` discriminators on all six templates (`meeting`, `person`, `decision`, `reference`, `inbox`, `appreciation`), plus `status: open` on decisions and `recurring: false` on meeting.md (conditional); F7 `check_task6` refactored into a per-harness spec loop that fingerprints `^PASS:` line counts (1/1/1/1/10/7/7 empirical)
- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` (Phase-4 review-fix subagent — F4 `## Banned-term lock` token list + composite regex + rationale list extended with `personal`; F6 no edit needed — `{{name}}` was already present in the `## Placeholder vocabulary lock` allowlist)

Unchanged (explicit — Task 1 + Task 2 scopes are strictly additive; no other files touched):

- All nine `memory/` template files (Tasks 3a–3f scope)
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Task 4 scope)
- `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` (Task 6 scope)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (already at `ready-for-dev` / `in-progress` from Phase 1 SM pass; Task 7 Dev-handoff flip is out of Task 1 + Task 2 scope)
- All nine `~/Public/gtd-life/memory/*/_template*.md` source files (read-only during Task 1 audit)
- All seven predecessor harnesses `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3,2-4}-*.sh` (not invoked during Task 1)

Unchanged (explicit — Task 3d scope is strictly limited to `memory/reference/_template.md` + its parent directory + this story file's Task 3d edits; no other files touched):

- Eight of the nine `memory/` template files (Tasks 3a, 3b, 3c, 3e, 3f scope — `meetings/_template/{meeting,agenda,prep,transcript}.md`, `people/_template.md`, `decisions/_template.md`, `inbox/_template.md`, `appreciations/_template.md`)
- `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md` (Task 1 artifact; read-only during Task 3d)
- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` (Task 2 artifact; read-only during Task 3d)
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Task 4 scope)
- `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` (Task 6 scope)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 scope)
- `~/Public/gtd-life/memory/reference/_template.md` (read-only during Task 3d port)
- All seven predecessor harnesses `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3,2-4}-*.sh` (not invoked during Task 3d)
- `memory/.gitkeep` (byte-for-byte unchanged per AC9)

Unchanged (explicit — Task 3e scope is strictly limited to `memory/inbox/_template.md` + its parent directory + this story file's Task 3e edits; no other files touched):

- Eight of the nine `memory/` template files (Tasks 3a, 3b, 3c, 3d, 3f scope — `meetings/_template/{meeting,agenda,prep,transcript}.md`, `people/_template.md`, `decisions/_template.md`, `reference/_template.md`, `appreciations/_template.md`)
- `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md` (Task 1 artifact; read-only during Task 3e)
- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` (Task 2 artifact; read-only during Task 3e)
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Task 4 scope)
- `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` (Task 6 scope)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 scope)
- `~/Public/gtd-life/memory/inbox/_template.md` (read-only during Task 3e port)
- All seven predecessor harnesses `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3,2-4}-*.sh` (not invoked during Task 3e)
- `memory/.gitkeep` (byte-for-byte unchanged per AC9)

Unchanged (explicit — Task 3c scope is strictly limited to `memory/decisions/_template.md` + its parent directory + this story file's Task 3c edits; no other files touched):

- Eight of the nine `memory/` template files (Tasks 3a, 3b, 3d, 3e, 3f scope — `meetings/_template/{meeting,agenda,prep,transcript}.md`, `people/_template.md`, `reference/_template.md`, `inbox/_template.md`, `appreciations/_template.md`)
- `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md` (Task 1 artifact; read-only during Task 3c)
- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` (Task 2 artifact; read-only during Task 3c)
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Task 4 scope)
- `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` (Task 6 scope)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 scope)
- `~/Public/gtd-life/memory/decisions/_template.md` (read-only during Task 3c port)
- All seven predecessor harnesses `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3,2-4}-*.sh` (not invoked during Task 3c)
- `memory/.gitkeep` (byte-for-byte unchanged per AC9)

Unchanged (explicit — Task 3a scope is strictly limited to the four files under `memory/meetings/_template/` + its parent directory + this story file's Task 3a edits; no other files touched):

- Five of the nine `memory/` template files (Tasks 3b, 3c, 3d, 3e, 3f scope — `people/_template.md`, `decisions/_template.md`, `reference/_template.md`, `inbox/_template.md`, `appreciations/_template.md`)
- `_bmad-output/implementation-artifacts/tests/story-3-1-baseline-audit.md` (Task 1 artifact; read-only during Task 3a)
- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` (Task 2 artifact; read-only during Task 3a)
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (Task 4 scope)
- `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` (Task 6 scope)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 scope; not modified)
- All four `~/Public/gtd-life/memory/meetings/_template/*.md` source files (read-only during Task 3a port)
- All seven predecessor harnesses `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3,2-4}-*.sh` (not invoked during Task 3a)
- `memory/.gitkeep` (byte-for-byte unchanged per AC9)

## Review Follow-ups (AI)

- [x] **F1 (HIGH)** — Amend AC11 / AC13 to codify the Story 1.1 harness `memory/` allowlist exception (Story 2.1 precedent, commit `0db273b`). Added explicit exception language in both ACs plus a matching "Known Story 1.1 harness allowlist exception" paragraph in Dev Notes. Files: `_bmad-output/implementation-artifacts/3-1-port-template-trees-from-gtd-life-memory.md` (AC11, AC13, Dev Notes).
- [x] **F2 (HIGH)** — Enforce AC1 "exactly N files, no extras" via per-directory positive-count assertions in `check_task3`. Added a 6-row `count_specs` loop asserting `memory/meetings/_template/` = 4 entries and `memory/{people,decisions,reference,inbox,appreciations}/` = 1 entry each. POSIX-safe (`ls -A | wc -l | tr -d '[:space:]'`). File: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`.
- [x] **F3 (HIGH)** — Add AC9 sentinel / `.gitkeep` invariance assertions. `check_task3` now asserts `memory/.gitkeep` exists and is exactly 0 bytes, AND that no `.gitkeep|.keep|empty|placeholder` files exist anywhere at `find -mindepth 2 -type f` under `memory/`. File: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`.
- [x] **F4 (MEDIUM)** — Add `personal` to `BANNED_TERMS_REGEX` (16→17 tokens) and to the blueprint's `## Banned-term lock` section. Extended `regex_self_probe` with `personal note` (positive) and `personally` (negative boundary-guard) cases. Files: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`, `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md`.
- [x] **F5 (MEDIUM)** — Assert discriminator frontmatter key VALUES, not just key names. Added helper `assert_frontmatter_key_value` and wired `type: meeting|person|decision|reference|inbox|appreciation` into `check_task3`, plus `status: open` on decisions and `recurring: false` on meeting.md (conditional on key presence). File: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`.
- [x] **F6 (MEDIUM)** — Add `{{name}}` to the AC8 enumerated allowlist in the story file. Blueprint's `## Placeholder vocabulary lock` already listed `{{name}}` (no edit needed). Harness `PLACEHOLDER_ALLOWLIST` already listed `{{name}}` (no edit needed). Files: `_bmad-output/implementation-artifacts/3-1-port-template-trees-from-gtd-life-memory.md` (AC8 enumeration).
- [x] **F7 (MEDIUM)** — Fingerprint per-sub-harness `^PASS:` line counts in `check_task6`. Refactored into a `regressions` spec loop that runs each predecessor harness, counts `^PASS:` lines, and fails on count mismatch. Empirically measured on 2026-04-20 via `bash <harness> all | grep -c '^PASS:'`: 1 / 1 / 1 / 1 / 10 / 7 / 7 across Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4. File: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`.

## Senior Developer Review (AI)

**Reviewer:** Senior Developer (AI) — adversarial code review, Phase 3. **Date:** 2026-04-20. **Disposition (pre-fix):** CHANGES_REQUESTED (3 HIGH + 4 MEDIUM findings). **Disposition (post-fix, this section):** APPROVED — all 7 findings resolved, full 8-harness regression passes green. **Scope reviewed:** nine ported `memory/` template files, harness `story-3-1-memory-template-tree-validation.sh`, blueprint `story-3-1-canonical-blueprint.md`, baseline audit `story-3-1-baseline-audit.md`, handoff artifact `story-3-1-task6-handoff.md`, story file `3-1-port-template-trees-from-gtd-life-memory.md`, `sprint-status.yaml`, and the Story 1.1 allowlist integration fix.

### Review summary

Story 3.1 ports the nine memory-vault template files from gtd-life with a thorough baseline audit, a locked canonical blueprint, and a harness that extends the Story 2.4 seven-harness regression chain. The port correctly scrubs Defects #1 (`appreciations/_template.md` malformed frontmatter), #2 (`inbox/_template.md` `context:` VALUE), and #3 (`meeting.md` `context:` inline comment). The harness hits all required shape gates. Seven gaps identified:

| # | Sev | Title | Status |
| --- | --- | --- | --- |
| F1 | HIGH | AC11 / AC13 must codify the Story 1.1 allowlist exception explicitly | Resolved |
| F2 | HIGH | AC1 "exactly N files" not enforced — only existence + non-empty | Resolved |
| F3 | HIGH | AC9 sentinel / `.gitkeep` invariance not asserted by harness | Resolved |
| F4 | MED | `personal` not in `BANNED_TERMS_REGEX` (defence-in-depth gap) | Resolved |
| F5 | MED | Frontmatter key PRESENCE asserted; VALUES silently driftable | Resolved |
| F6 | MED | `{{name}}` absent from AC8 enumeration (allowed in blueprint + harness, undocumented in AC) | Resolved |
| F7 | MED | `check_task6` aggregates exit-zero but doesn't fingerprint sub-harness PASS line counts | Resolved |

### Finding detail + resolution

- **F1 (HIGH) — AC11 / AC13 codification of Story 1.1 allowlist exception.** Problem: AC11 says "zero bytes changed in any of those seven prior harnesses" and AC13 says "Story 3.1 modifies ONLY sprint-status.yaml and this story file", but reality is that `story-1-1-scaffold-validation.sh` line 155 gained a one-line memory-subdir allowlist extension (Story 2.1 precedent, commit `0db273b`). An honest acceptance contract must name the exception. Resolution: AC11 amended with inline "Exception: a single-line additive extension to `story-1-1-scaffold-validation.sh`'s memory/ allowlist on line 155…" wording, AC13 gained the parallel exception clause, and Dev Notes gained a dedicated "Known Story 1.1 harness allowlist exception (documented 2026-04-20 Phase 4 F1 review fix)" paragraph. Evidence file + lines: `_bmad-output/implementation-artifacts/3-1-port-template-trees-from-gtd-life-memory.md` AC11, AC13, Dev Notes (post-defects list).

- **F2 (HIGH) — AC1 "exactly N files, no extras" enforcement.** Problem: `check_task3` only asserted file presence and non-emptiness; a regression adding a stray `memory/meetings/_template/notes.md` or `memory/people/other.md` would pass. Resolution: new `count_specs` loop in `check_task3` asserts `memory/meetings/_template/` has exactly 4 entries and each of `memory/{people,decisions,reference,inbox,appreciations}/` has exactly 1 entry using POSIX-safe `ls -A | wc -l | tr -d '[:space:]'`. Evidence file + lines: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` `check_task3` (count-spec loop at the top of the gate body).

- **F3 (HIGH) — AC9 sentinel invariance.** Problem: AC9 forbids new `.gitkeep|.keep|empty|placeholder` files under `memory/*/*` and requires `memory/.gitkeep` to remain byte-for-byte stable (0 bytes, Story 1.1 scaffold). Harness did not verify either. Resolution: `check_task3` now asserts `memory/.gitkeep` exists and is exactly 0 bytes (via `wc -c <file | tr -d '[:space:]'`), then iterates four sentinel names and runs `find "${MEMORY_DIR}" -mindepth 2 -name "${sentinel}" -type f` for each, failing on any hit. Evidence: same harness file, `check_task3` (AC9 block immediately after the count-spec loop).

- **F4 (MEDIUM) — `personal` banned-term defence-in-depth.** Problem: the banned-term set covers 16 tokens (derek / neighbors / revivago / benji / flowtopic / gtd-life / gtdlife / wyoming / cheyenne / family / home / blog / wife / son / daughter / dog), but Defects #2 and #3 both enumerate `personal` as a scope value — if a future regression re-introduces the enumeration, the current regex misses it. Resolution: `BANNED_TERMS_REGEX` extended to include `personal`; `regex_self_probe` extended with `personal note` (positive) + `personally` (negative; boundary guard must reject embedded letters); blueprint's `## Banned-term lock` section's token list + composite regex + rationale list extended to match. Confirmed via scan: zero `personal`-boundary hits in any of the nine ported files. Evidence: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (`BANNED_TERMS_REGEX=`, `regex_self_probe`); `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` (`## Banned-term lock`).

- **F5 (MEDIUM) — discriminator frontmatter VALUES.** Problem: `assert_frontmatter_keys` only verified key presence; a copy-paste that flipped `type: meeting` to `type: person` would pass because both files have a `type:` key. Resolution: new helper `assert_frontmatter_key_value "key" "expected" "file"` performs `grep -Eq "^${key}:[[:space:]]*${expected_value}[[:space:]]*$"`. Wired in for six `type:` discriminators (`meeting`, `person`, `decision`, `reference`, `inbox`, `appreciation`) plus `status: open` on decisions and `recurring: false` on meeting.md (conditional on key presence; skipped gracefully per spec when absent). Evidence: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` (`assert_frontmatter_key_value` helper + 7 call sites inside `check_task3`).

- **F6 (MEDIUM) — `{{name}}` in AC8 enumeration.** Problem: decisions/_template.md uses `{{name}}` in its two H3 Option sub-sections; the blueprint's allowlist and the harness's `PLACEHOLDER_ALLOWLIST` already permitted it, but AC8's inline enumeration omitted it, creating a story-vs-harness contract drift. Resolution: AC8 enumeration extended to include `{{name}}`. Verified blueprint's `## Placeholder vocabulary lock` already lists `{{name}}` (no edit); harness's `PLACEHOLDER_ALLOWLIST` already includes `{{name}}` (no edit). Evidence: `_bmad-output/implementation-artifacts/3-1-port-template-trees-from-gtd-life-memory.md` AC8 (second bullet, allowlist enumeration).

- **F7 (MEDIUM) — sub-harness PASS line-count fingerprints.** Problem: `check_task6` only asserted non-zero exit per predecessor harness; a harness that silently lost a `check_taskN` + matching `PASS:` echo would still exit zero if the remaining gates passed. Resolution: `check_task6` refactored into a `regressions` spec loop that, for each predecessor harness, runs it, counts `^PASS:` lines, and fails on count mismatch. Expected counts hardcoded from empirical measurement on 2026-04-20 (`bash <harness> all | grep -c '^PASS:'`): 1 / 1 / 1 / 1 / 10 / 7 / 7 for Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4. Evidence: `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` `check_task6` (spec loop replacing the flat 7-call if-chain).

### Post-fix verification

- `bash -n _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` — OK (no syntax errors).
- Full 8-harness regression from repo root, 2026-04-20:
  - `story-1-1-scaffold-validation.sh all` → rc=0, 1 PASS line (`PASS: all`)
  - `story-1-2-root-files-validation.sh all` → rc=0, 1 PASS line
  - `story-1-3-root-context-validation.sh all` → rc=0, 1 PASS line
  - `story-2-1-agent-identity-validation.sh all` → rc=0, 1 PASS line
  - `story-2-2-guardrail-and-formatting-validation.sh all` → rc=0, 10 PASS lines
  - `story-2-3-work-persona-validation.sh all` → rc=0, 7 PASS lines
  - `story-2-4-benji-inbox-absence-validation.sh all` → rc=0, 7 PASS lines
  - `story-3-1-memory-template-tree-validation.sh all` → rc=0, 7 PASS lines
- `grep -riE '(^|[^A-Za-z])personal($|[^A-Za-z])' memory/` → no hits (pre-existing scrubs sufficient; no template content regressions introduced).
- No `memory/` template file content modified during Phase 4 (all nine ported files byte-for-byte stable). No predecessor harness modified beyond the Story 2.1-precedent one-line allowlist extension on `story-1-1-scaffold-validation.sh` line 155, which is now codified as an AC11 / AC13 exception.

### Approval

All 7 findings are resolved. Story 3.1 meets the amended acceptance criteria. Sprint-status.yaml `3-1-port-template-trees-from-gtd-life-memory.status` flipped `review → done`; story `Status:` flipped to `done`. `epic-3.status` remains `in-progress` (Stories 3.2 and 3.3 still backlog).
