# Story 3.2: Portable `.obsidian/` config

Status: done

## Story

As a new Vixxo employee who has just cloned the `assistants-template` and wants to open the `memory/` directory as an Obsidian vault,
I want a portable, personally-sanitized `memory/.obsidian/` config — Templates plugin, Daily Notes plugin, graph view defaults, and the canonical core-plugin allowlist — ported from `gtd-life/memory/.obsidian/` with the workspace cache, per-user vault history, and any Derek / RevivaGo / personal-content residue scrubbed out,
so that the vault opens cleanly on first launch with sensible defaults (daily notes pointed at a conventional `daily/` folder, templates plugin enabled, graph + backlinks + switcher + properties all on) and without inheriting any of Derek's open-file cache, search queries, or meeting-history references — and without waiting on the setup wizard (Epic 5) to land.

## Acceptance Criteria

1. **AC1 — `memory/.obsidian/` directory exists with exactly seven portable config files**
   - Given the cloned `assistants-template` repository after Story 3.2 lands
   - When `memory/.obsidian/` is listed (`ls -A memory/.obsidian`)
   - Then the directory contains exactly seven JSON files: `app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`, `templates.json` — one file per Obsidian subsystem (global app, appearance theme, community-plugin inventory, core-plugin enablement, daily-notes settings, graph-view settings, templates-plugin settings) — and no extra files
   - And each file exists, is non-empty, is a valid UTF-8 text file, and ends with a trailing newline
   - And each file parses as valid JSON (a well-formed object `{…}` or array `[…]` without trailing commas, unquoted keys, or JavaScript comments)
   - And the directory contains NO `workspace.json`, `workspace.json.bak`, `workspaces.json`, or any file matching the glob `*.bak` / `*.json.bak` / `*.log` (workspace cache and backups are user-local state and must not be committed to a template)
   - And the directory contains NO `.DS_Store`, no `Icon\r`, no macOS resource-fork sentinels
   - And the directory contains NO community-plugin subdirectory (`plugins/` is out of scope; the `community-plugins.json` file ships empty)

2. **AC2 — `app.json` shape (global Obsidian app settings)**
   - Given `memory/.obsidian/app.json`
   - When the file is read
   - Then it parses as a JSON OBJECT (not array) with exactly three keys in the canonical gtd-life order: `strictLineBreaks` (boolean `false`), `showFrontmatter` (boolean `true`), `defaultViewMode` (string `"source"`)
   - And the file byte length does not exceed 200 bytes (sanity upper bound — gtd-life source is 89 bytes; the portable port admits minor whitespace variation)

3. **AC3 — `appearance.json` shape (theme / accent color / font)**
   - Given `memory/.obsidian/appearance.json`
   - When the file is read
   - Then it parses as an EMPTY JSON OBJECT (`{}` — no keys) — matching the gtd-life source exactly (the user will configure theme + accent color on first open; the template ships neutral defaults via Obsidian's built-in behavior)
   - And the file byte length does not exceed 10 bytes (the literal bytes `{}\n` is 3 bytes; some editors may add a trailing newline — upper bound admits whitespace without admitting content drift)

4. **AC4 — `community-plugins.json` shape (no community plugins shipped)**
   - Given `memory/.obsidian/community-plugins.json`
   - When the file is read
   - Then it parses as an EMPTY JSON ARRAY (`[]` — no enabled community plugins) — matching the gtd-life source exactly (the template ships zero community plugins; the user can install their own after cloning)
   - And the file byte length does not exceed 10 bytes (the literal bytes `[]\n` is 3 bytes; admits whitespace without admitting content drift)
   - And the directory `memory/.obsidian/plugins/` does NOT exist (no bundled community-plugin binaries / main.js / manifest.json blobs — those are user-installable, out of scope, and would bloat the template)

5. **AC5 — `core-plugins.json` shape (canonical enabled/disabled map)**
   - Given `memory/.obsidian/core-plugins.json`
   - When the file is read
   - Then it parses as a JSON OBJECT whose keys are Obsidian core-plugin IDs and whose values are booleans — matching the gtd-life source exactly (31 keys total, byte-for-byte identical)
   - And the following plugins are enabled (value `true`): `file-explorer`, `global-search`, `switcher`, `graph`, `backlink`, `outgoing-link`, `tag-pane`, `page-preview`, `daily-notes`, `templates`, `markdown-importer`, `outline`, `canvas`, `properties`, `bookmarks`, `bases`
   - And the following plugins are disabled (value `false`): `note-composer`, `command-palette`, `slash-command`, `editor-status`, `zk-prefixer`, `random-note`, `word-count`, `slides`, `audio-recorder`, `workspaces`, `file-recovery`, `publish`, `sync`, `footnotes`, `webviewer`
   - And no additional keys beyond the 31 listed above are present (no personal-tweak plugins from Derek's vault leak through)

6. **AC6 — `daily-notes.json` shape (folder + format; no user-specific template path)**
   - Given `memory/.obsidian/daily-notes.json`
   - When the file is read
   - Then it parses as a JSON OBJECT with exactly three keys in canonical gtd-life order: `folder` (string `"daily"`), `format` (string `"YYYY-MM-DD"`), `template` (empty string `""`)
   - And the `folder` value is the relative-to-vault-root string `"daily"` — a conventional Obsidian daily-notes folder name (NOT a Derek-specific vault path like `/Users/dneighbors/...`)
   - And the `template` value is the EMPTY STRING `""` — matching the gtd-life source exactly (gtd-life does NOT wire a daily-note template; neither does the portable template — daily notes open blank)
   - And the file contains NO absolute filesystem path (no `/Users/`, no `~/`, no `Public/`, no `gtd-life`)

7. **AC7 — `graph.json` shape (graph-view defaults; zero user-specific state)**
   - Given `memory/.obsidian/graph.json`
   - When the file is read
   - Then it parses as a JSON OBJECT with graph-view default settings — matching the gtd-life source shape (20 keys: `collapse-filter`, `search`, `showTags`, `showAttachments`, `hideUnresolved`, `showOrphans`, `collapse-color-groups`, `colorGroups`, `collapse-display`, `showArrow`, `textFadeMultiplier`, `nodeSizeMultiplier`, `lineSizeMultiplier`, `collapse-forces`, `centerStrength`, `repelStrength`, `linkStrength`, `linkDistance`, `scale`, `close`)
   - And the `search` key is the EMPTY STRING `""` (no carried-over user search query like `"tmo"` or anything else — gtd-life source is already clean; the port asserts cleanliness)
   - And the `colorGroups` key is an EMPTY ARRAY `[]` (no Derek-authored color-group definitions carry through)
   - And no numeric value contains a Derek-specific non-default (e.g. `centerStrength` may remain at the gtd-life-observed `0.518713248970312` or be reset to a round default — the port preserves source values; the assertion is shape-only)
   - And the file byte length does not exceed 1024 bytes (gtd-life source is 493 bytes; upper bound admits whitespace without admitting structural drift)

8. **AC8 — `templates.json` shape (REPAIRED — no dangling folder reference)**
   - Given `memory/.obsidian/templates.json`
   - When the file is read
   - Then it parses as a JSON OBJECT with exactly one key: `folder`
   - And the `folder` VALUE is the EMPTY STRING `""` (NOT the gtd-life source value `"_templates"`, which points at `memory/_templates/` — a directory that does NOT exist in this template and that Story 3.1 explicitly declined to create in favor of the per-directory `_template.md` convention; pointing the templates plugin at a non-existent folder produces a confusing user-facing error on first open)
   - And this is the one KNOWN REPAIR for Story 3.2 (analogous to Story 3.1's Defect #1–#3 repairs): the gtd-life source string `"_templates"` is scrubbed to `""` because the downstream directory it referenced is out of scope in this template
   - And the emitted file does NOT contain the literal string `_templates` anywhere (not as a key, not as a value, not in any comment — there are no comments in JSON) — a grep for `_templates` across this file MUST return zero matches

9. **AC9 — No `workspace.json` / no user-local vault cache / no Derek vault history**
   - Given `memory/.obsidian/`
   - When the directory is scanned
   - Then NO file named `workspace.json`, `workspace.json.bak`, `workspaces.json` exists
   - And NO file matching `*.bak`, `*.log`, `*.tmp`, `.DS_Store` exists
   - And NO file anywhere under `memory/.obsidian/` contains the literal string `bobby` (boundary-guarded, case-insensitive — Derek's colleague name leaks through workspace.json recent-file references if the file is mistakenly committed)
   - And NO file contains any absolute filesystem path prefix (`/Users/`, `~/Public/`, `Public/gtd-life`, `gtd-life/memory/`)
   - And NO file contains a meeting-title slug matching `\d{4}-\d{2}-\d{2}-[a-z-]+` (e.g. `2026-04-20-bobby-derek-wkly-1-1`) — this is a workspace-cache fingerprint and its presence anywhere under `memory/.obsidian/` indicates `workspace.json` sneaked in

10. **AC10 — Zero Derek / RevivaGo / personal content in any ported config file**
    - Given every file ported in AC1–AC8
    - When the standard boundary-guarded banned-term scan (carried forward from Story 2.1 / 2.2 / 2.3 / 2.4 / 3.1, identical 17-token set) runs across each file
    - Then the regex `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` matches zero occurrences, case-insensitive, for every token in the inherited lock: `derek`, `neighbors`, `revivago`, `benji`, `flowtopic`, `gtd-life`, `gtdlife`, `wyoming`, `cheyenne`, `family`, `home`, `blog`, `wife`, `son`, `daughter`, `dog`, `personal` (17 tokens — the exact Story 3.1 post-Phase-4 F4 set; no new tokens added for Story 3.2; no tokens removed)
    - And no file contains the literal strings `gtd-life`, `~/Public/gtd-life`, `Public/gtd-life`, or any filesystem path that points back at the source repo (fixed-string `grep -F` scan)
    - And no file contains a real human first-or-last name (no `Derek`, no `Bobby`, no `Jeff Stegman`, no `Shawn Robinson`, no `Jim McCarthy` — these names appear in the gtd-life `workspace.json` source which is explicitly excluded from the port per AC9; this AC10 assertion covers the seven ported files as an independent backstop)
    - And no file contains the `blog-ideas`, `companies/revivago`, or any gtd-life-specific folder-slug reference

11. **AC11 — Existing scaffold sentinels and Story 3.1 template files are byte-for-byte stable**
    - Given `memory/.gitkeep` (from Story 1.1, byte-for-byte 0-byte file) AND the nine `memory/` template files from Story 3.1 (`meetings/_template/{meeting,agenda,prep,transcript}.md`, `people/_template.md`, `decisions/_template.md`, `reference/_template.md`, `inbox/_template.md`, `appreciations/_template.md`) AND their parent directories (`meetings/`, `meetings/_template/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/`)
    - When Story 3.2 creates `memory/.obsidian/` and its seven JSON files
    - Then `memory/.gitkeep` remains byte-for-byte unchanged (size 0, mtime may shift but content does not)
    - And none of the nine Story 3.1 template files are touched (SHA-256 of each file matches the Story 3.1 Task 6 handoff fingerprint; byte-length and content identical)
    - And no new `.gitkeep`, `.keep`, `empty`, or `placeholder` sentinel files are added anywhere under `memory/.obsidian/` (the seven JSON config files are themselves git-trackable content, making sentinels redundant — same logic as Story 3.1 AC9)
    - And no new sentinels are added under `memory/meetings/`, `memory/meetings/_template/`, `memory/people/`, `memory/decisions/`, `memory/reference/`, `memory/inbox/`, `memory/appreciations/` (Story 3.1 invariance preserved)

12. **AC12 — Validation/CI harness exists and is wired into the test-harness family**
    - Given the existing harness family under `_bmad-output/implementation-artifacts/tests/`
    - When Story 3.2 lands
    - Then a new deterministic harness `story-3-2-obsidian-config-validation.sh` exists at `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh`, is marked executable (`chmod +x`), uses `#!/usr/bin/env bash` on line 1 and `set -euo pipefail` on line 2
    - And the harness implements gates `task1` (baseline audit evidence present and structured — `story-3-2-baseline-audit.md`), `task2` (canonical blueprint evidence present and structured — `story-3-2-canonical-blueprint.md`), `task3` (per-file shape verification across the seven ported JSON files: existence + non-empty + valid JSON + required keys per AC2–AC8 + `workspace.json` absence per AC9 + Story 3.1 template invariance per AC11), `task4` (cross-file scrub: boundary-guarded banned-term scan across the seven JSON files + literal `gtd-life` / `~/Public/gtd-life` / `Public/gtd-life` path-reference scans + no-`bobby` scan per AC9 + no meeting-slug fingerprint scan per AC9 + the `_templates` scrub assertion per AC8), `task5` (self-check: shebang, `set -euo pipefail`, all case arms, all declared constants, `regex_self_probe` definition via `declare -F` per Story 2.4 F4 and Story 3.1 precedent), `task6` (regression — invokes Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 harnesses in `all` mode and asserts each exits zero with the expected `^PASS:` line count), plus an `all` dispatcher
    - And the harness exits `0` with `PASS: all` on success; exits `1` and emits `FAIL: <gate>: <reason>` on stderr on failure — matching the Story 2.1 / 2.2 / 2.3 / 2.4 / 3.1 contract
    - And the harness is BSD-grep and GNU-grep compatible, POSIX-bash-3.2 compatible, and uses only `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tr`, `sort`, `cut`, and shell built-ins (no `rg`, no `jq`, no Python, no `node` — JSON shape assertions use grep-based key probes, not a JSON parser)
    - And the harness implements `regex_self_probe` that exercises the boundary-guarded banned-term regex against at least two tokens (one carried-forward `derek` → positive, `derekson` → boundary-rejected; one Epic-3-added `personal` → positive, `personally` → boundary-rejected) — guards against a mis-parsing host grep (same pattern as Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1)
    - And when invoked in `all` mode, the harness emits exactly 7 lines matching `^PASS:` on stdout (`PASS: task1` → `PASS: task6` → `PASS: all`) — fingerprint compatible with the Story 3.1 pass-count convention

13. **AC13 — Regression-runs all eight predecessor harnesses cleanly (extends Story 3.1's seven-harness chain by one)**
    - Given all prior harnesses in `_bmad-output/implementation-artifacts/tests/` (Story 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1 — eight predecessors; Story 3.1 is new to this regression chain relative to Story 3.1's own seven-harness chain)
    - When the Story 3.2 regression gate (`task6`) runs
    - Then `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, `bash story-2-1-agent-identity-validation.sh all`, `bash story-2-2-guardrail-and-formatting-validation.sh all`, `bash story-2-3-work-persona-validation.sh all`, `bash story-2-4-benji-inbox-absence-validation.sh all`, and `bash story-3-1-memory-template-tree-validation.sh all` each exit `0` with `PASS: all`
    - And the per-harness `^PASS:` line-count fingerprint (measured 2026-04-20) is 1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 respectively — the harness MUST fail if any sub-harness emits a different count (Story 3.1 Phase-4 F7 precedent)
    - And zero bytes are changed in any of those eight prior harnesses during Story 3.2 execution. **Exception: a single-line additive extension to `story-1-1-scaffold-validation.sh`'s `memory/` allowlist on line 155, admitting the new Story 3.2 subdirectory literal `\.obsidian` (dot-prefixed because Obsidian uses a hidden directory), is permitted. This follows Story 2.1's precedent (commit `0db273b` added `me|mcp|obsidian` anticipating future Epic-3 subdirs) and Story 3.1's Phase-4 F1 precedent (added `meetings|people|decisions|reference|inbox|appreciations` on the same line). The line 155 regex transitions from `^(\.gitkeep|.+\.md|me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations)$` to `^(\.gitkeep|.+\.md|me|mcp|obsidian|\.obsidian|meetings|people|decisions|reference|inbox|appreciations)$` — a single `|\.obsidian` insertion. This is the minimal-change pattern the Story 1.1 harness was designed to accept.**
    - And zero bytes are changed in `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files (`outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`), `agents/personas/work.md`, the root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`), `README.md`, `LICENSE`, `.gitignore`, `memory/.gitkeep`, and any of the nine Story 3.1 template files under `memory/` — Story 3.2 is additive only (new `memory/.obsidian/` directory + seven JSON files + new harness + new evidence artifacts + sprint-status flip + this story file, plus the Story 2.1 / Story 3.1 F1-precedent one-line allowlist extension in `story-1-1-scaffold-validation.sh` documented above)

14. **AC14 — Sprint tracker lifecycle reflects the story transition and epic-3 remains in-progress**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When Story 3.2 opens at Phase 1 (SM pass) and again at Phase 2 (Dev handoff)
    - Then the `3-2-portable-obsidian-config.status` entry is updated `backlog → ready-for-dev` at Phase 1, and `ready-for-dev → review` at Phase 2 (the autonomous-swarm lifecycle may collapse interim states per Story 2.1 / 2.2 / 2.3 / 2.4 / 3.1 precedent — a single `backlog → review` on-disk transition is acceptable as long as the final pre-review status is `review`)
    - And `epic-3.status` remains `in-progress` throughout Story 3.2 (Story 3.1 opened the epic; Story 3.3 is still `backlog`; the epic does NOT transition to `done` until every story in it is `done`)
    - And `last_updated` is set to `2026-04-20` on the Phase 1 edit
    - And no other story's status is regressed; every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` is preserved byte-for-byte (zero reordering, zero comment drift, zero key addition/removal beyond the two value flips — the `3-2-...status` flip at Phase 1 and Phase 2 — and the `last_updated` value change)

15. **AC15 — Story is additive; no scope creep into Stories 3.3 / Epic 4 / Epic 5 territory**
    - Given the scope of Story 3.2
    - When the working-set file list is reviewed
    - Then Story 3.2 creates ONLY: the seven JSON config files under `memory/.obsidian/`, the harness, three test-evidence files (baseline audit, canonical blueprint, handoff package), and this story file
    - And Story 3.2 does NOT create `memory/me/identity.md` or `memory/me/preferences.md` (Story 3.3's scope), `memory/daily/` (deferred — Obsidian creates this folder lazily on first daily note; if the user wants a daily template it is out of Story 3.2 scope per AC6 which asserts `template: ""`), `memory/companies/`, `memory/blog-ideas/`, or any content under `memory/vixxo/`
    - And Story 3.2 does NOT create or edit any files under `.cursor/`, `agents/`, `bin/`, `scripts/`, `docs/`, or the repo root (no `.obsidian/` at repo root — the Obsidian vault root is `memory/`, so the config lives at `memory/.obsidian/`)
    - And Story 3.2 does NOT port `workspace.json` from the gtd-life source; the absence of `workspace.json` is part of the portable-config contract
    - And Story 3.2 modifies ONLY: `_bmad-output/implementation-artifacts/sprint-status.yaml` (Story 3.2 status flips + `last_updated`) and this story file (Dev Agent Record / Change Log / File List / checkboxes at Dev handoff). **Exception: a single-line additive extension to `story-1-1-scaffold-validation.sh`'s `memory/` allowlist on line 155 admitting `\.obsidian`, is permitted. This follows Story 2.1's precedent (commit `0db273b`) and Story 3.1's Phase-4 F1 precedent, and is the minimal-change pattern the Story 1.1 harness was designed to accept.**

## Tasks / Subtasks

- [x] Task 1 — Baseline audit of gtd-life `.obsidian/` sources and Derek/workspace-cache inventory (AC: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10) **[Parallelizable with Task 2]**
  - [x] Enumerate every file at `~/Public/gtd-life/memory/.obsidian/`. Record each file's (a) byte length, (b) line count, (c) JSON top-level structure (object vs array), (d) key list (for objects) or length (for arrays), (e) any banned-term hits under the boundary-guarded 17-token lock, (f) any absolute-filesystem-path leaks (`/Users/`, `~/`, `Public/`), (g) any meeting-title slug fingerprints matching `\d{4}-\d{2}-\d{2}-[a-z-]+`.
  - [x] Specifically flag the `workspace.json` file as EXCLUDED from the port: record its byte length (observed ~7374 bytes), line count, and document every banned-term hit inside it so future auditors understand why it is excluded (Derek + Bobby + revivago + blog-ideas references throughout the recent-file cache). The baseline audit must state explicitly: "`workspace.json` is out-of-scope; the port emits zero bytes corresponding to this file."
  - [x] Identify the one KNOWN REPAIR needed for the port: `templates.json` in the gtd-life source has `"folder": "_templates"` pointing at a directory (`memory/_templates/`) that Story 3.1 explicitly declined to create. The repair is to change the value to `""` (empty string) so the Templates plugin is enabled but has no configured source folder — the user may configure one later, or use the per-directory `_template.md` convention Story 3.1 established. Document this repair with rationale.
  - [x] Confirm the six other portable config files (`app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`) are already clean in the gtd-life source: zero banned-term hits, zero absolute-path leaks, zero meeting-slug fingerprints, zero community-plugin bundling (`plugins/` subdirectory absent or empty). Record the evidence.
  - [x] Record the known Obsidian-specific directories that are explicitly OUT OF SCOPE for Story 3.2: `memory/.obsidian/plugins/` (community-plugin binaries — never bundled in a template), `memory/daily/` (Obsidian auto-creates on first daily note; Story 3.2 does not pre-create), `memory/_templates/` (Story 3.1 declined this layout), `memory/workspace.json` (does not exist; the workspace cache lives inside `.obsidian/` anyway), `.obsidian/` at repo root (wrong location — Obsidian vault root is `memory/`, not repo root).
  - [x] Persist all findings at `_bmad-output/implementation-artifacts/tests/story-3-2-baseline-audit.md` with sections: `# Story 3.2 Baseline Audit`, `## gtd-life .obsidian source inventory`, `## Per-file JSON structure + key map`, `## Banned-term scan of source files`, `## workspace.json exclusion rationale`, `## Known defects requiring repair during port`, `## Out-of-scope .obsidian subdirectories and paths`, `## Mapping: source path → target path (or EXCLUDED)`.

- [x] Task 2 — Canonical blueprint for the seven ported config files (AC: 1, 2, 3, 4, 5, 6, 7, 8) **[Parallelizable with Task 1]**
  - [x] Author a blueprint document at `_bmad-output/implementation-artifacts/tests/story-3-2-canonical-blueprint.md` that specifies, for each of the seven target files, the EXACT JSON top-level structure (object vs array), the EXACT key set (for objects) in the canonical order observed in the gtd-life source, the EXACT value type (string / boolean / number / array / object) for each key, and any EXACT literal values that must be preserved verbatim (e.g. `defaultViewMode: "source"`, `folder: "daily"`, `format: "YYYY-MM-DD"`, `template: ""`, `folder: ""` for templates.json — the REPAIRED value). Follow the Story 3.1 `canonical-blueprint.md` precedent.
  - [x] Blueprint for `memory/.obsidian/app.json`: top-level OBJECT; keys `strictLineBreaks` (bool `false`), `showFrontmatter` (bool `true`), `defaultViewMode` (string `"source"`).
  - [x] Blueprint for `memory/.obsidian/appearance.json`: top-level OBJECT; no keys (literal bytes `{}`).
  - [x] Blueprint for `memory/.obsidian/community-plugins.json`: top-level ARRAY; zero elements (literal bytes `[]`).
  - [x] Blueprint for `memory/.obsidian/core-plugins.json`: top-level OBJECT; exactly 31 keys matching the gtd-life source exactly. Enabled (`true`): `file-explorer`, `global-search`, `switcher`, `graph`, `backlink`, `outgoing-link`, `tag-pane`, `page-preview`, `daily-notes`, `templates`, `markdown-importer`, `outline`, `canvas`, `properties`, `bookmarks`, `bases`. Disabled (`false`): `note-composer`, `command-palette`, `slash-command`, `editor-status`, `zk-prefixer`, `random-note`, `word-count`, `slides`, `audio-recorder`, `workspaces`, `file-recovery`, `publish`, `sync`, `footnotes`, `webviewer`. Total 16 true + 15 false = 31 keys.
  - [x] Blueprint for `memory/.obsidian/daily-notes.json`: top-level OBJECT; keys `folder` (string `"daily"`), `format` (string `"YYYY-MM-DD"`), `template` (empty string `""`).
  - [x] Blueprint for `memory/.obsidian/graph.json`: top-level OBJECT; 17 keys in gtd-life-source order: `collapse-filter` (bool), `search` (EMPTY STRING `""` — explicit), `showTags` (bool), `showAttachments` (bool), `hideUnresolved` (bool), `showOrphans` (bool), `collapse-color-groups` (bool), `colorGroups` (EMPTY ARRAY `[]` — explicit), `collapse-display` (bool), `showArrow` (bool), `textFadeMultiplier` (number), `nodeSizeMultiplier` (number), `lineSizeMultiplier` (number), `collapse-forces` (bool), `centerStrength` (number), `repelStrength` (number), `linkStrength` (number), `linkDistance` (number), `scale` (number), `close` (bool). Note: the gtd-life source has 20 keys; the blueprint lists all 20 (the earlier "17" figure was a miscount — the canonical spec is all 20 keys per `cat graph.json`).
  - [x] Blueprint for `memory/.obsidian/templates.json` (REPAIRED shape; do NOT copy the source verbatim): top-level OBJECT; exactly one key `folder` with the REPAIRED value `""` (empty string). Source value `"_templates"` is scrubbed because it points at a non-existent directory in this template.
  - [x] Blueprint forbidden-file lock: list every file that must be ABSENT from `memory/.obsidian/`: `workspace.json`, `workspace.json.bak`, `workspaces.json`, `*.bak`, `*.log`, `*.tmp`, `.DS_Store`. Also lock forbidden subdirectory: `memory/.obsidian/plugins/` must not exist.
  - [x] Blueprint banned-term lock: reuse the Story 3.1 17-token set verbatim (`derek, neighbors, revivago, benji, flowtopic, gtd-life, gtdlife, wyoming, cheyenne, family, home, blog, wife, son, daughter, dog, personal`). Story 3.2 adds ZERO new tokens. Also lock additional path-reference fixed strings (`~/Public/gtd-life`, `Public/gtd-life`, `/Users/`) and the Obsidian-specific `bobby` name fixed-string scan (AC9 backstop for `workspace.json` leakage). Also lock the meeting-slug regex `[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+` — any match indicates `workspace.json` sneaked in.

- [x] Task 3a — Port `memory/.obsidian/app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json` (AC: 1, 2, 3, 4, 5, 10) **[Parallelizable with Tasks 3b, 3c once Task 2 blueprint is written]**
  - [x] Create the directory `memory/.obsidian/` (bash: `mkdir -p memory/.obsidian`). The Story 1.1 harness allowlist at `story-1-1-scaffold-validation.sh:155` requires a coordinated integration fix to admit `\.obsidian` — see Task 5 for the one-line allowlist extension.
  - [x] Author `memory/.obsidian/app.json` per the Task 2 blueprint. Port the gtd-life source (`~/Public/gtd-life/memory/.obsidian/app.json`) VERBATIM — the source is already clean. Three keys, valid JSON, trailing newline.
  - [x] Author `memory/.obsidian/appearance.json` with the literal bytes `{}\n` (empty JSON object + trailing newline). The gtd-life source is already `{}`; port verbatim.
  - [x] Author `memory/.obsidian/community-plugins.json` with the literal bytes `[]\n` (empty JSON array + trailing newline). The gtd-life source is already `[]`; port verbatim.
  - [x] Author `memory/.obsidian/core-plugins.json` per the Task 2 blueprint. Port the gtd-life source VERBATIM (31 keys, clean JSON). Preserve key order and boolean values exactly.
  - [x] After authoring the four files, run a per-file banned-term scan (`grep -iE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'`) and a path-reference scan (`grep -F 'gtd-life'`, `grep -F '/Users/'`, `grep -F 'Public/'`) and confirm zero hits each.

- [x] Task 3b — Port `memory/.obsidian/daily-notes.json`, `graph.json` (AC: 1, 6, 7, 10) **[Parallelizable with Tasks 3a, 3c]**
  - [x] Author `memory/.obsidian/daily-notes.json` per the Task 2 blueprint. Port the gtd-life source VERBATIM — the source is already clean. Three keys in canonical order: `folder: "daily"`, `format: "YYYY-MM-DD"`, `template: ""`. The `"daily"` folder value is a relative-to-vault-root path; no absolute path leak possible.
  - [x] Author `memory/.obsidian/graph.json` per the Task 2 blueprint. Port the gtd-life source VERBATIM — the source is already clean (the `search` key is `""`, `colorGroups` is `[]`, no Derek-authored customizations). Preserve all numeric values exactly (e.g. `centerStrength: 0.518713248970312`, `repelStrength: 10`, `linkDistance: 250`).
  - [x] After authoring the two files, run the same banned-term + path-reference scans as Task 3a. Confirm zero hits each. Additionally confirm the `search` key's value is the empty string (no `"tmo"` or other carried-over query) and the `colorGroups` key's value is the empty array.

- [x] Task 3c — Port (REPAIRED) `memory/.obsidian/templates.json` (AC: 1, 8, 10) **[Parallelizable with Tasks 3a, 3b]**
  - [x] Author `memory/.obsidian/templates.json` with the REPAIRED content — do NOT copy the gtd-life source verbatim. Emit the single-key JSON object `{"folder": ""}` with a trailing newline. Use either the pretty-printed form `{\n  "folder": ""\n}\n` (4-space indent matching the other Obsidian JSON files in this bundle) or the compact form `{"folder": ""}\n` — either is acceptable as long as it parses as valid JSON.
  - [x] The gtd-life source value `"_templates"` points at `memory/_templates/`, a directory that Story 3.1 explicitly declined to create in favor of the per-directory `_template.md` convention. Pointing the Templates plugin at a non-existent folder would show a confusing warning on first Obsidian open. The REPAIR is to emit `""` (empty string), which disables the folder reference without disabling the Templates plugin itself (the plugin remains `true` in `core-plugins.json`).
  - [x] After authoring, verify the emitted file contains ZERO occurrences of the literal string `_templates` (`grep -F '_templates' memory/.obsidian/templates.json` → empty). Also run the banned-term + path-reference scans.

- [x] Task 4 — Author the deterministic validation harness (AC: 12, 13) **[Sequential — depends on Task 2 blueprint AND Tasks 3a–3c config files existing]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh`. Model on `story-3-1-memory-template-tree-validation.sh`. `#!/usr/bin/env bash` on line 1, `set -euo pipefail` on line 2, `chmod +x`. POSIX-bash-3.2, BSD+GNU-grep compatible. No `jq`, no `node`, no Python.
  - [x] Declare constants at the top:
    - `PROJECT_ROOT`, `TESTS_DIR`, `SELF_PATH` — standard harness boilerplate
    - `MEMORY_DIR="${PROJECT_ROOT}/memory"`
    - `OBSIDIAN_DIR="${MEMORY_DIR}/.obsidian"`
    - Seven file-path constants: `APP_JSON="${OBSIDIAN_DIR}/app.json"`, `APPEARANCE_JSON="${OBSIDIAN_DIR}/appearance.json"`, `COMMUNITY_PLUGINS_JSON="${OBSIDIAN_DIR}/community-plugins.json"`, `CORE_PLUGINS_JSON="${OBSIDIAN_DIR}/core-plugins.json"`, `DAILY_NOTES_JSON="${OBSIDIAN_DIR}/daily-notes.json"`, `GRAPH_JSON="${OBSIDIAN_DIR}/graph.json"`, `TEMPLATES_JSON="${OBSIDIAN_DIR}/templates.json"`
    - Forbidden-file constant: `WORKSPACE_JSON="${OBSIDIAN_DIR}/workspace.json"` — asserted absent
    - `BASELINE_AUDIT_PATH="${TESTS_DIR}/story-3-2-baseline-audit.md"`
    - `BLUEPRINT_PATH="${TESTS_DIR}/story-3-2-canonical-blueprint.md"`
    - Eight prior-harness paths: `STORY_1_1_HARNESS`, `STORY_1_2_HARNESS`, `STORY_1_3_HARNESS`, `STORY_2_1_HARNESS`, `STORY_2_2_HARNESS`, `STORY_2_3_HARNESS`, `STORY_2_4_HARNESS`, `STORY_3_1_HARNESS`
    - `BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'` — 17 tokens (identical to Story 3.1)
    - `MEETING_SLUG_REGEX='[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+'` — workspace-cache fingerprint per AC9
    - `STORY_3_1_TEMPLATE_FILES=( meetings/_template/meeting.md meetings/_template/agenda.md meetings/_template/prep.md meetings/_template/transcript.md people/_template.md decisions/_template.md reference/_template.md inbox/_template.md appreciations/_template.md )` — nine files asserted byte-stable per AC11
  - [x] Implement `regex_self_probe()` that exercises both the banned-term regex (`derek` matches; `derekson` is boundary-rejected; `personal` matches; `personally` is boundary-rejected — two-token positive+negative coverage matching Story 3.1 F4 precedent) AND a meeting-slug positive/negative probe (`2026-04-20-bobby-derek-wkly-1-1` matches; `foo-bar-baz` does not match `MEETING_SLUG_REGEX`). Fail-fast `fail "regex probe: ..."` on mismatch.
  - [x] `check_task1` — require `BASELINE_AUDIT_PATH` exists, contains title `# Story 3.2 Baseline Audit`, and contains each required section header (`gtd-life .obsidian source inventory`, `Per-file JSON structure + key map`, `Banned-term scan of source files`, `workspace.json exclusion rationale`, `Known defects requiring repair during port`, `Out-of-scope .obsidian subdirectories and paths`, `Mapping: source path → target path`).
  - [x] `check_task2` — require `BLUEPRINT_PATH` exists, contains title `# Story 3.2 Canonical Blueprint`, and contains one section per target file (seven) plus `## Forbidden-file lock`, `## Banned-term lock`, and `## Meeting-slug fingerprint lock` sections.
  - [x] `check_task3` — per-file shape verification:
    - For each of the seven target JSON files: assert `[[ -f <path> ]]`, assert `[[ -s <path> ]]`, assert trailing-newline via `tail -c 1 | od -An -tx1 | tr -d '[:space:]'` equals `0a`, assert the file parses as valid JSON by running `python3 -c "import json,sys; json.load(open(sys.argv[1]))" <file>` — WAIT: the project constraint forbids Python. Alternative: use a grep-based structural probe — for object files assert first non-whitespace char is `{` and last is `}`; for array files assert first is `[` and last is `]`. Use `head -c 1 <file>` and `tr -d '[:space:]' < <file> | tail -c 1`. Valid-JSON assertion is STRUCTURAL (shape probe), not semantic.
    - For `app.json`: assert `grep -Fq '"strictLineBreaks"'`, `grep -Fq '"showFrontmatter"'`, `grep -Fq '"defaultViewMode"'`, and `grep -Fq '"defaultViewMode": "source"'`.
    - For `appearance.json`: assert contents stripped of whitespace equals `{}` via `tr -d '[:space:]' < <file>` and compare to literal `{}`.
    - For `community-plugins.json`: assert contents stripped of whitespace equals `[]`.
    - For `core-plugins.json`: assert 16 specific `true` keys and 15 specific `false` keys each via `grep -Fq '"<plugin>": true'` / `grep -Fq '"<plugin>": false'` (key-value pair assertions). Also count total key occurrences (`grep -c '":' <file>`) and assert count is exactly 31.
    - For `daily-notes.json`: assert `grep -Fq '"folder": "daily"'`, `grep -Fq '"format": "YYYY-MM-DD"'`, `grep -Fq '"template": ""'`.
    - For `graph.json`: assert `grep -Fq '"search": ""'` (Derek's `"tmo"` search scrubbed / absent), `grep -Fq '"colorGroups": []'` (no Derek-authored groups), and that each of the 20 canonical keys per blueprint is present via `grep -Fq '"<key>":'`.
    - For `templates.json`: assert `grep -Fq '"folder": ""'` (REPAIRED value), AND `! grep -Fq '_templates'` (source value scrubbed — zero occurrences), AND exactly one top-level key (strip whitespace, assert contents match the literal `{"folder":""}` or confirm `grep -c '":' <file>` equals 1).
    - Forbidden-file block (AC9): assert `[[ ! -f "${WORKSPACE_JSON}" ]]`; iterate forbidden patterns (`*.bak`, `*.log`, `*.tmp`, `.DS_Store`) via `find "${OBSIDIAN_DIR}" -type f -name "<pattern>"` and fail on any match; assert `[[ ! -d "${OBSIDIAN_DIR}/plugins" ]]`.
    - Directory-count block (AC1 exactness, Story 3.1 Phase-4 F2 precedent): assert `ls -A "${OBSIDIAN_DIR}" | wc -l | tr -d '[:space:]'` equals `7`.
    - AC11 invariance block: assert `wc -c < "${MEMORY_DIR}/.gitkeep" | tr -d '[:space:]'` equals `0`; assert each of the nine Story 3.1 template files exists and is non-empty; assert no new `.gitkeep|.keep|empty|placeholder` files exist under `memory/.obsidian/` via `find "${OBSIDIAN_DIR}" -type f -name "<sentinel>"`.
  - [x] `check_task4` — cross-file scrub:
    - For each of the seven JSON files, run `grep -iEq "${BANNED_TERMS_REGEX}" <file>` and FAIL the gate if any match.
    - Fixed-string path-reference scans per file: `grep -Fq 'gtd-life'`, `grep -Fq '~/Public/gtd-life'`, `grep -Fq 'Public/gtd-life'`, `grep -Fq '/Users/'` — each MUST return zero.
    - Fixed-string `bobby` scan per file (AC9 backstop): `grep -Fiq 'bobby'` MUST return zero across all seven files.
    - Meeting-slug regex scan per file: `grep -Eq "${MEETING_SLUG_REGEX}"` MUST return zero across all seven files (workspace-cache fingerprint — if present, `workspace.json` content leaked into a sibling file).
    - `templates.json`-specific `_templates` scrub assertion (AC8 cross-check): `grep -Fq '_templates' "${TEMPLATES_JSON}"` MUST return zero.
  - [x] `check_task5` — self-check. Assert `head -n 1` equals `#!/usr/bin/env bash`; assert `grep -Fq 'set -euo pipefail'`; assert every case arm present (`task1)`–`task6)` and `all)`); assert each declared constant name appears (`OBSIDIAN_DIR=`, the seven file-path constants, `WORKSPACE_JSON=`, `BASELINE_AUDIT_PATH=`, `BLUEPRINT_PATH=`, eight `STORY_*_HARNESS=`, `BANNED_TERMS_REGEX=`, `MEETING_SLUG_REGEX=`, `STORY_3_1_TEMPLATE_FILES=`); assert `declare -F regex_self_probe >/dev/null 2>&1` (Story 2.4 F4 + Story 3.1 precedent).
  - [x] `check_task6` — regression. Arg tuple per harness: `"HARNESS_PATH|display_name|expected_pass_count"`. For each of the eight predecessor harness paths, `require_file_exists` and invoke `bash "${harness}" all 2>&1`. Capture combined stdout/stderr. Count `^PASS:` lines and compare to the expected-count fingerprint: 1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 for Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1. Echo captured output on non-zero exit or count mismatch per Story 2.2 Phase 4 F6 + Story 3.1 F7 pattern; `fail` with sub-harness name on any violation.
  - [x] Implement the `mode` dispatcher: `case "${mode}" in task1) check_task1 ;; ... task6) check_task6 ;; all) check_task1; echo "PASS: task1"; ...; check_task6; echo "PASS: task6" ;; *) fail "unknown mode: ${mode}" ;; esac`; end with `echo "PASS: ${mode}"`. Under `all` mode emits exactly 7 `^PASS:` lines.
  - [x] Add header comment block stating: (a) Story 3.2 is the portable Obsidian-config port from gtd-life; (b) scope is seven JSON files at `memory/.obsidian/`; (c) `workspace.json` is intentionally excluded (user-local vault cache with Derek / Bobby / revivago leakage); (d) `templates.json` is the one REPAIRED file (source `"_templates"` → `""`); (e) regression chain extends Story 3.1's seven-harness chain by one (adds Story 3.1 as the eighth predecessor).

- [x] Task 5 — Apply the Story 1.1 allowlist integration fix AND run the regression (AC: 12, 13) **[Sequential — depends on Task 4 harness existing and Tasks 3a–3c config files landed]**
  - [x] Apply the Story 1.1 harness integration fix at `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh:155`. The single one-line change: the `memory)` branch allowlist regex currently reads `grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations)$'` — extend it to `grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian|\.obsidian|meetings|people|decisions|reference|inbox|appreciations)$'` by inserting `|\.obsidian` after `obsidian`. This admits the hidden Obsidian-config directory as a valid `memory/` subdir. Follows Story 2.1 commit `0db273b` and Story 3.1 Phase-4 F1 precedent. Classified as an integration fix, not a Story 3.2 scope expansion. AC13 and AC15 encode this exception explicitly.
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh all`. Capture the full transcript. Expect `PASS: task1` → `PASS: task6` → `PASS: all`, exit 0, exactly 7 `^PASS:` lines.
  - [x] Re-run each of the eight predecessor harnesses individually in `all` mode. All eight must exit `0` with `PASS: all`. Verify the per-harness `^PASS:` line-count fingerprint matches 1 / 1 / 1 / 1 / 10 / 7 / 7 / 7.
  - [x] Capture the full command-and-transcript log for inclusion in the Task 6 handoff artifact.

- [x] Task 6 — Handoff readiness package (AC: 12, 13, 15) **[Sequential — depends on Task 5]**
  - [x] Persist `_bmad-output/implementation-artifacts/tests/story-3-2-task6-handoff.md` with: (a) AC-to-file map (one row per AC pointing at the harness gate, file path, or grep output that proves it); (b) full validation command transcript (Story 3.2 harness + eight regression harnesses); (c) byte-counts and SHA-256 checksums of the seven ported JSON files (for future drift detection); (d) forward-looking notes: Story 3.3 will add `memory/me/identity.md` + `memory/me/preferences.md`; Epic 4 Story 4.1 will reference `memory/` paths in mcp.json context; Epic 5 Story 5.2 (wizard) may seed Obsidian-adjacent preferences; Epic 6 Story 6.2 can invoke this harness as a CI gate; Obsidian users may manually configure the Templates plugin folder on first open (since Story 3.2 sets it to `""`).
  - [x] Include a "zero-edit verification" block listing each of the eight predecessor harnesses (accounting for the documented Story 1.1 line-155 integration-fix exception), the four Story 2.2 rule files, Story 2.1 `agent-identity.mdc`, Story 2.3 `agents/personas/work.md`, the nine Story 3.1 template files, the root context files, `README.md`, `LICENSE`, `.gitignore`, `memory/.gitkeep` — each asserted present, non-empty where appropriate, and (for the Story 3.1 templates) byte-for-byte identical to the Story 3.1 Task 6 handoff fingerprint.
  - [x] Explicitly document the Story 1.1 line-155 integration fix as an AC13 / AC15 exception, referencing both the Story 2.1 commit `0db273b` precedent and the Story 3.1 Phase-4 F1 precedent. State the exact one-line change: `me|mcp|obsidian|meetings|...` → `me|mcp|obsidian|\.obsidian|meetings|...` (insertion of `|\.obsidian` after `obsidian`).

- [x] Task 7 — Sprint tracker and story status synchronization (AC: 14) **[Independent; typically last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `3-2-portable-obsidian-config.status` from `backlog` to `ready-for-dev` during Phase 1 (SM pass); then to `review` at Dev handoff. Single `backlog → review` on-disk transition acceptable per Story 2.1 / 2.2 / 2.3 / 2.4 / 3.1 autonomous-swarm precedent.
  - [x] Do NOT modify `epic-3.status` — it remains `in-progress` (Story 3.1 opened the epic; Story 3.3 is still `backlog`; epic does not close until 3.3 is done).
  - [x] Update `last_updated` in `sprint-status.yaml` to `2026-04-20` on the Phase 1 edit.
  - [x] Preserve every comment, blank line, inline spacing, and entry ordering byte-for-byte. The only diff between pre-edit and post-edit files must be the `status:` value change for `3-2-...` (once at Phase 1, once at Phase 2) plus the `last_updated` value change.

## Dev Notes

### Artifact availability

- Planning / tracking artifacts used by this story:
  - `_bmad/bmm/config.yaml` (BMAD v6.3.0; `user_name: Vixxo Employee`; `planning_artifacts` / `implementation_artifacts` path variables).
  - `_bmad-output/planning-artifacts/epics.md` — Epic 3 Story 3.2 AC at lines 266–274; Epic 3 overview at lines 252–286.
  - `_bmad-output/planning-artifacts/architecture.md` — 26 lines. Confirms template-only scope, macOS/Linux portability, `{{…}}` placeholder convention (though Story 3.2 JSON files have no placeholders), secrets-via-.gitignore discipline. Story 3.2 inherits all four constraints; the placeholder-discipline constraint is inapplicable to JSON config files.
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — story key `3-2-portable-obsidian-config`, Linear `AIP-38`, current status `backlog`; `epic-3.status` currently `in-progress` (opened by Story 3.1); `last_updated: "2026-04-20"`.
  - Prior story files (all `done`): `1-1-scaffold-directory-structure-and-root-files.md`, `1-2-write-generic-readme-license-gitignore.md`, `1-3-write-generic-agents-claude-cursorrules.md`, `2-1-port-agent-identity-rule-generic.md`, `2-2-port-guardrail-and-formatting-rules.md`, `2-3-create-single-generic-work-persona.md`, `2-4-confirm-benji-inbox-default-not-ported.md`, `3-1-port-template-trees-from-gtd-life-memory.md`. Pattern source for harness structure, banned-term regex discipline, POSIX-ERE boundary guards, Phase-4 F-series review-fix pattern (especially F1 allowlist exception, F4 `personal` banned-token, F7 PASS-count fingerprints), autonomous-swarm status-collapse convention.
  - gtd-life source config (reference only; scrubbed / repaired during port): `~/Public/gtd-life/memory/.obsidian/app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`, `templates.json` (REPAIR source — `folder: "_templates"` scrubbed), `workspace.json` (EXCLUDED — user-local vault cache with Derek / Bobby / revivago / blog-ideas references).
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` — does not exist. Story 3.2 relies on epics.md + architecture.md + sprint-status.yaml + prior-story-file patterns for all requirements.
  - `_bmad-output/planning-artifacts/ux-design-specification.md` — does not exist. Story 3.2 has no UX surface (file-system JSON config only), so absence is not a blocker.
  - `_bmad/bmm/workflows/4-implementation/bmad-create-story/template.md` — does not exist at the configured path. Story 3.2 uses the emergent shape from Stories 1.1 → 3.1 (Status + Story statement + ACs + Tasks/Subtasks + Dev Notes sub-sections + Change Log + Dev Agent Record + Review Follow-ups + Senior Developer Review).

### Epic 3 story partition (why 3.2 is ".obsidian/ only, no identity")

- **Story 3.1 (done):** Ported the empty per-directory `_template.md` / `_template/` tree (nine files) under `memory/`. Created `meetings/_template/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/`. Introduced the 17-token banned-term lock and the 8-harness regression chain discipline.
- **Story 3.2 (this story):** Port the portable `memory/.obsidian/` config (seven JSON files — Templates + Daily Notes + core-plugin allowlist + graph defaults + app settings). Depends on the `memory/` tree existing (Story 3.1 provides that). Does NOT port `workspace.json` (user-local vault cache leaks Derek / Bobby / revivago references). Scrubs `templates.json` `folder: "_templates"` → `""` to avoid pointing the Templates plugin at a non-existent directory.
- **Story 3.3 (backlog):** Seed `memory/me/identity.md` and `memory/me/preferences.md` with `scope: work` frontmatter and placeholder body. These are the targets of the Epic 5 setup wizard. Story 3.2 does NOT create `memory/me/`; Story 3.3 will populate it. Story 3.3 landing will also re-test Story 3.2's harness as the ninth predecessor in its regression chain.

Story 3.2 is deliberately narrow. Its entire job is: "make Obsidian open the `memory/` vault cleanly on first launch, with sensible Templates + Daily Notes defaults, without inheriting any of Derek's workspace cache or vault history." Identity (3.3) and the setup-wizard-driven personalization (Epic 5) are downstream.

### Why port verbatim + scrub + exclude-workspace rather than rewrite from scratch

The gtd-life `memory/.obsidian/` bundle is a production-hardened Obsidian config that already pairs correctly with the nine Story-3.1-ported template files (core-plugins enables `templates` + `daily-notes` + `properties`; app-level `showFrontmatter: true` matches the YAML-frontmatter templates; graph defaults are neutral). Rewriting these config values from scratch would risk breaking the Obsidian-plugin-to-template-file contract (e.g. disabling `properties` would hide the frontmatter in the sidebar; disabling `templates` would make the Templates plugin unavailable for users who want to author custom templates).

Two classes of changes allowed during the port:

1. **EXCLUDE `workspace.json` entirely.** This file is user-local vault state (recent-file cache, open-pane layout, last-search-query text). Committing Derek's `workspace.json` into the template would pollute a new employee's first Obsidian open with references to `meetings/2026-04-20-bobby-derek-wkly-1-1/agenda.md`, `companies/revivago/crm-nutrafi.md`, and `blog-ideas/` — all files that don't exist in the template and whose paths alone leak banned tokens (`bobby`, `derek`, `revivago`, `blog`). The portable contract is: Obsidian will create `workspace.json` on first launch based on the user's own activity. The template ships zero workspace cache.
2. **REPAIR `templates.json` value.** The gtd-life source has `"folder": "_templates"` pointing at `memory/_templates/`, a folder that Story 3.1 explicitly declined to create in favor of the per-directory `_template.md` convention. Keeping the source value would show a confusing "Templates folder does not exist" warning on first open. The REPAIR is to set `"folder": ""`, which leaves the Templates plugin enabled but unconfigured — the user can either point it at a folder they create (e.g. `memory/_templates/`) or leave it empty and use the per-directory templates directly.

Everything else (app settings, appearance, community-plugin inventory, core-plugin enablement, daily-notes folder name, graph-view defaults) is ported byte-compatible because those values are generic Obsidian defaults, not Derek-specific customizations.

### Banned-term set for Story 3.2 (identical to Story 3.1's 17-token lock)

Story 3.2 inherits the Story 3.1 Phase-4-locked 17-token banned-term set verbatim. Zero new tokens added; zero tokens removed. Boundary-guarded regex: `(^|[^A-Za-z])TOKEN($|[^A-Za-z])`, case-insensitive via `grep -iE`.

**Carried forward from Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 (all 17 tokens):**

- `derek`, `neighbors` — Derek's name
- `revivago`, `flowtopic` — personal business tokens
- `benji` — personal task-system token
- `gtd-life`, `gtdlife` — source-repo reference
- `wyoming`, `cheyenne` — example PII location tokens
- `family`, `wife`, `son`, `daughter`, `dog` — family/personal-life tokens
- `home` — personal-life token
- `blog` — personal output channel
- `personal` (Story 3.1 Phase-4 F4 addition) — generic personal-scope token

**Story-3.2-specific fixed-string scans (ADDITIONAL defence-in-depth, NOT part of the 17-token regex):**

- `bobby` — Derek's colleague name leaked through `workspace.json` recent-file references. Fixed-string scan `grep -Fiq 'bobby'` across each of the seven ported JSON files. Not added to the 17-token regex because `bobby` is a common first name that should not trigger a false positive in future unrelated content (e.g. `bobbypin` in a reference note would still pass the main banned-term lock). But for the narrow scope of `.obsidian/` config files, a fixed-string backstop is appropriate.
- `gtd-life`, `~/Public/gtd-life`, `Public/gtd-life`, `/Users/` — path-reference fixed-string scans carried forward from Story 3.1 Task 4's `check_task4`.
- Meeting-slug regex `[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+` — workspace-cache fingerprint. If any ported JSON file contains a match, `workspace.json` content has leaked into a sibling file.

The harness MUST reject any of the 17 regex tokens (boundary-guarded, case-insensitive) in any of the seven ported files, AND any of the additional fixed-string or regex probes above.

### JSON-shape discipline (no `jq`, no `node`, no Python — grep-based probes only)

The project architectural constraint forbids introducing new dependencies. `jq` is not universally installed (macOS ships without it by default; GitHub Actions `macos-latest` requires a `brew install jq` step). `node` and `python` are available on most developer machines but introducing them into the harness would break the "POSIX-bash + grep + awk + sed + find" tool discipline established by every predecessor harness.

**JSON-shape assertions in `check_task3` use grep-based probes, not a JSON parser:**

- **Structural sanity:** First non-whitespace char is `{` (object) or `[` (array); last non-whitespace char is `}` or `]` respectively. Implementation: `head -c 1 <file>` (after `tr -d '[:space:]'` pre-filter) and equivalent tail check. Catches empty files, broken bytes, and grossly malformed JSON.
- **Key presence:** `grep -Fq '"<key>":'` per expected key. Fixed-string matching avoids regex-escaping pitfalls around dashes (`core-plugins.json` keys include `file-explorer`, `global-search`, etc.).
- **Key-value pair assertions:** `grep -Fq '"<key>": "<value>"'` for string values; `grep -Fq '"<key>": true'` / `grep -Fq '"<key>": false'` for booleans. Matches the Story 3.1 Phase-4 F5 frontmatter-key-value helper pattern (`assert_frontmatter_key_value`).
- **Exact-content assertions** for tiny files: `appearance.json` and `community-plugins.json` can be asserted as literal `{}` / `[]` after stripping whitespace via `tr -d '[:space:]' < <file>`. No parser needed.
- **Forbidden-substring assertions:** `grep -Fq '_templates' <file>` MUST return zero for `templates.json` (AC8 REPAIR verification). Fixed-string avoids regex complications.
- **Key-count assertions:** `grep -c '":' <file>` counts `":` pairs, which approximates key count for well-formed JSON. Combined with key-presence probes, this catches extra-key regressions (e.g. a rogue community-plugin ID sneaking into `core-plugins.json`).

This discipline avoids adding `jq` or `python` as a dependency. It is shape-verification, not semantic JSON validation — a file that is valid JSON but has the wrong structure will be caught by the key-presence probes; a file that is malformed JSON but happens to contain the right substrings will be caught by the structural-sanity probe (first/last character). The Obsidian app itself is the semantic validator — if the shape passes all probes, Obsidian will open the vault cleanly. This is consistent with the Story 2.2 / 2.3 / 3.1 approach of shape-only verification.

### Previous story learnings to carry forward

- **POSIX-ERE boundary guards** (Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1): `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` works on macOS BSD grep, GNU grep, and busybox/Alpine grep identically. Do NOT use `\b`, `\<`, `\>`, or Perl-compatible regex.
- **`regex_self_probe` fail-fast** (all prior stories): probe must exercise BOTH a positive case (token matches) and a negative case (boundary-embedded substring does not match) for at least one token. Story 3.2 should exercise at least two tokens (one from the carried-forward set: `derek` + `derekson`; one Epic-3-added: `personal` + `personally`) in both directions, AND one meeting-slug probe (`2026-04-20-bobby-derek-wkly-1-1` matches; `foo-bar-baz` does not).
- **Phase 4 F6 sub-harness capture** (Story 2.2): `check_task6` regression gate must capture combined stdout/stderr (`2>&1`) when invoking sub-harnesses, echo the captured output on non-zero exit, and fail with the sub-harness name.
- **Phase 4 F7 PASS-count fingerprint** (Story 3.1): `check_task6` MUST assert exact `^PASS:` line count per sub-harness, not just non-zero exit. Empirical counts for Story 3.2 regression chain (measured 2026-04-20): 1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 for Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1.
- **Phase 4 F1 allowlist-exception codification** (Story 3.1): when a predecessor harness needs a one-line additive extension to accept new downstream scaffold, the extension is classified as an integration fix following Story 2.1 commit `0db273b` precedent, and the current story's ACs must codify the exception explicitly. Story 3.2's `\.obsidian` insertion at `story-1-1-scaffold-validation.sh:155` is the third such extension (Story 2.1 added `me|mcp|obsidian`; Story 3.1 added `meetings|people|decisions|reference|inbox|appreciations`; Story 3.2 adds `\.obsidian`).
- **Phase 4 F2 per-directory exact-count assertions** (Story 3.1): `check_task3` must assert exact file count per scaffolded directory, not just existence. Story 3.2 asserts `ls -A memory/.obsidian/ | wc -l` equals `7`.
- **Phase 4 F3 sentinel invariance** (Story 3.1): `check_task3` must assert `memory/.gitkeep` is 0 bytes AND no new `.gitkeep|.keep|empty|placeholder` sentinels exist under the newly-scaffolded subdirectory.
- **Phase 4 F4 `personal` banned token** (Story 3.1): the 17-token lock is inherited verbatim. No new banned tokens for Story 3.2.
- **Phase 4 F5 discriminator value assertions** (Story 3.1): Story 3.1 uses `assert_frontmatter_key_value` to verify `type: meeting|person|decision|…` on template frontmatter. Story 3.2's analogous pattern is JSON-key-value assertions via `grep -Fq '"<key>": "<value>"'`.
- **Autonomous-swarm status collapse** (Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1): `backlog → ready-for-dev → review` may collapse to a single on-disk `backlog → review` transition. Record the skipped hop in the Change Log.
- **Story 2.4 F4 `declare -F` probe presence** (inherited by Story 3.1): `check_task5` probe presence check uses `declare -F <function_name> >/dev/null 2>&1`, not `grep -Fq '<function_name>'`.
- **Additive-only discipline** (Story 2.4 AC8, Story 3.1 AC11/AC13): Story 3.2 may create new files only under `memory/.obsidian/` + `_bmad-output/implementation-artifacts/tests/` + this story file, plus the single-line Story 1.1 harness integration fix. Any other edit is a regression.
- **Commit-message shape** (Epic 1 / 2 / 3 git log): `feat(epic-N): <change> (Story <key>)`. Story 3.2's commit should read `feat(epic-3): port portable obsidian config (Story 3-2-portable-obsidian-config)`.

### Architectural constraints

- **No runtime service, no application code.** Story 3.2 is pure file-system scaffolding plus a shell harness. No Node, no Python, no web surface. The JSON files are Obsidian config consumed by the Obsidian desktop app, not runtime code of the template itself.
- **No new dependencies.** `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tr`, `sort`, `cut`, `od`, `mkdir` are universally available on macOS and Linux developer machines and on `ubuntu-latest` / `macos-latest` CI images. Do not introduce `jq`, `yq`, `rg`, `node`, `python`, or any other tool that is not POSIX-ubiquitous.
- **macOS / Linux portability.** POSIX-bash-3.2 compatible (macOS default `/bin/bash` is 3.2 without `brew install bash`). BSD-grep and GNU-grep compatible. No `find -printf` (GNU-only); use `find -print | head -n1` idioms. No `readlink -f` (GNU-only); use `cd "$(dirname ...)" && pwd`.
- **No shell-state mutation.** No `shopt -s nocaseglob`, no `LANG=` reassignment, no `export LC_ALL=`. Case-insensitive logic is per-invocation via `grep -i` or `tr '[:upper:]' '[:lower:]'`.
- **UTF-8 files with trailing newline.** Every emitted JSON file is UTF-8, ends with a single `\n`, has no CRLF line endings (LF only). Obsidian writes JSON files without trailing newlines on some platforms; the port explicitly adds a trailing newline for POSIX-tool friendliness (`wc -l`, `tail -c 1`).
- **`.gitignore` contract preserved.** `memory/` is NOT in `.gitignore`; the seven ported JSON files ARE committed to git. This is correct — they are portable defaults, not secrets. Confirm no `memory/` or `memory/.obsidian/` entry sneaks into `.gitignore`. `workspace.json` is NOT committed because it is not ported, not because `.gitignore` excludes it (the `.gitignore` contract remains byte-for-byte stable; workspace-cache absence is enforced by the harness `check_task3` forbidden-file block).
- **Obsidian-vault-root convention.** Obsidian treats the directory containing `.obsidian/` as the vault root. Placing `.obsidian/` at `memory/.obsidian/` correctly makes `memory/` the vault root. Placing it at the repo root would make the WHOLE repository the vault (undesirable — `_bmad-output/`, `.cursor/`, `scripts/` etc. would show up in Obsidian's file-explorer sidebar).

### Project Structure Notes

- **Target files for this story (new — 11 files total):**
  - Obsidian config files (7):
    - `memory/.obsidian/app.json`
    - `memory/.obsidian/appearance.json`
    - `memory/.obsidian/community-plugins.json`
    - `memory/.obsidian/core-plugins.json`
    - `memory/.obsidian/daily-notes.json`
    - `memory/.obsidian/graph.json`
    - `memory/.obsidian/templates.json` (REPAIRED — `"folder": ""` not `"_templates"`)
  - Test evidence (4):
    - `_bmad-output/implementation-artifacts/tests/story-3-2-baseline-audit.md`
    - `_bmad-output/implementation-artifacts/tests/story-3-2-canonical-blueprint.md`
    - `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh` (executable, 0755)
    - `_bmad-output/implementation-artifacts/tests/story-3-2-task6-handoff.md`
- **Target files for this story (modified):**
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (`3-2-portable-obsidian-config.status` flip, `last_updated` update; `epic-3.status` preserved at `in-progress`)
  - `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` line 155 (single one-line additive extension admitting `\.obsidian` — integration fix per Story 2.1 / Story 3.1 precedent)
  - This story file (Dev Agent Record / Change Log / File List / checkboxes at Dev handoff)
- **Directory state expectations AFTER Story 3.2 lands:**
  - `memory/` contains `.gitkeep` (from Story 1.1, 0 bytes unchanged), six Story 3.1 subdirs (`meetings/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/`, all with Story 3.1 templates byte-stable), plus the NEW `.obsidian/` subdir. No `me/`, no `companies/`, no `daily/`, no `blog-ideas/`, no `vixxo/`, no `_templates/` — those are out of scope (`me/` is Story 3.3; the rest are not in any current Epic 3 story).
  - `memory/.obsidian/` contains exactly seven files: `app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`, `templates.json`. NO `workspace.json`, NO `*.bak`, NO `*.log`, NO `.DS_Store`, NO `plugins/` subdirectory.
  - All Story 1.x / 2.x / 3.1 artifacts remain byte-for-byte stable.
- **Forward-compatibility:**
  - Story 3.3 (`memory/me/identity.md`, `memory/me/preferences.md`) will add `memory/me/` subdir. Story 3.2's harness does NOT assert absence of `memory/me/` (it only asserts the seven `.obsidian/` files exist and are correctly-shaped plus Story 3.1 template invariance). Story 3.3 can land without Story 3.2 harness regression.
  - Epic 4 Story 4.1 / 4.4 (mcp.json, docs) do not touch `memory/`; independent of Story 3.2.
  - Epic 5 Story 5.2 (wizard) will WRITE to `memory/me/identity.md` (Story 3.3 territory) and may optionally re-open Obsidian with a welcome note — neither of which regresses Story 3.2's config files.
  - Epic 6 Story 6.2 (GitHub Action) can invoke `bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh all` directly as a CI gate — harness contract is GitHub-Actions-native (exit 0 on pass, 1 on fail, exactly 7 `^PASS:` lines).
  - User-facing Obsidian behavior on first open: vault opens at `memory/`, file-explorer shows `meetings/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/` (+ `me/` after Story 3.3). Templates plugin is enabled but has no configured folder — user can point it at `memory/_templates/` (which they'd create) or use the per-directory `_template.md` convention directly. Daily-notes plugin is enabled and will auto-create `memory/daily/` on first daily-note action. Graph view shows the template files linked to each other (via the `related_to` / `context` frontmatter fields Story 3.1 established). No community plugins installed.

### Testing Notes

- **Suggested manual smoke commands (post-port, pre-harness):**
  - `ls memory/.obsidian/` (expect: `app.json appearance.json community-plugins.json core-plugins.json daily-notes.json graph.json templates.json`)
  - `ls memory/.obsidian/ | wc -l | tr -d ' '` (expect: `7`)
  - `grep -F '_templates' memory/.obsidian/templates.json` (expect: empty — REPAIR verified)
  - `grep -F '"folder": ""' memory/.obsidian/templates.json` (expect: matches)
  - `grep -F '"folder": "daily"' memory/.obsidian/daily-notes.json` (expect: matches)
  - `grep -F '"search": ""' memory/.obsidian/graph.json` (expect: matches)
  - `[[ ! -f memory/.obsidian/workspace.json ]] && echo "workspace.json correctly absent"` (expect: correctly absent)
  - `[[ ! -d memory/.obsidian/plugins ]] && echo "plugins/ correctly absent"` (expect: correctly absent)
  - `grep -riE '(^|[^A-Za-z])(derek|revivago|benji|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])' memory/.obsidian/` — expect empty output
  - `grep -rF 'gtd-life' memory/.obsidian/` — expect empty output
  - `grep -riF 'bobby' memory/.obsidian/` — expect empty output
  - `grep -rE '[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+' memory/.obsidian/` — expect empty output (no workspace-cache meeting-slug leakage)
- **Harness invocation:**
  - `bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh all` — expect `PASS: task1` → `PASS: task6` → `PASS: all`, exit `0`, exactly 7 `^PASS:` lines.
  - `bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh task3` — exercises the seven-file shape verification in isolation.
  - `bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh task4` — exercises the cross-file scrub in isolation.
- **Regression (each must exit 0 with `PASS: all`; per-harness `^PASS:` line count in parens):**
  - `bash story-1-1-scaffold-validation.sh all` (1)
  - `bash story-1-2-root-files-validation.sh all` (1)
  - `bash story-1-3-root-context-validation.sh all` (1)
  - `bash story-2-1-agent-identity-validation.sh all` (1)
  - `bash story-2-2-guardrail-and-formatting-validation.sh all` (10)
  - `bash story-2-3-work-persona-validation.sh all` (7)
  - `bash story-2-4-benji-inbox-absence-validation.sh all` (7)
  - `bash story-3-1-memory-template-tree-validation.sh all` (7)
- **Self-contained harness:** no network, no external tools beyond `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`.

### Parallelization guidance

- **Task 1 (baseline audit) || Task 2 (canonical blueprint)** — both are pure-write operations against distinct evidence files (`story-3-2-baseline-audit.md` vs `story-3-2-canonical-blueprint.md`). No runtime coupling. A Dev swarm runs them concurrently in two subagents.
- **Tasks 3a / 3b / 3c (port config files)** are pairwise parallelizable AFTER Task 2 lands the blueprint. Each task writes to disjoint file paths under `memory/.obsidian/`:
  - 3a writes four files (`app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`)
  - 3b writes two files (`daily-notes.json`, `graph.json`)
  - 3c writes one file (`templates.json`) — the REPAIR
  No shared-file contention across 3a–3c. A Dev swarm may run all three concurrently. The directory `memory/.obsidian/` is created idempotently via `mkdir -p` by whichever task runs first.
- **Task 4 (harness)** is sequential — must run AFTER Task 2 (blueprint encoded as constants in the harness) AND AFTER Tasks 3a–3c (so `check_task3` has files to verify).
- **Task 5 (integration fix + regression)** is sequential — applies the Story 1.1 harness line-155 allowlist extension first, then runs the 9-harness test suite (Story 3.2 + 8 predecessors). Runs after Task 4 harness exists.
- **Task 6 (handoff)** is sequential — depends on Task 5 transcript.
- **Task 7 (sprint tracker)** is independent; Phase-1 edit flips status at story-creation time (SM pass), Phase-2 edit at Dev handoff.
- **Shared-file contention across the whole plan:**
  - Task 1 writes `story-3-2-baseline-audit.md` (unique).
  - Task 2 writes `story-3-2-canonical-blueprint.md` (unique).
  - Tasks 3a / 3b / 3c write seven distinct JSON paths under `memory/.obsidian/` (no overlap).
  - Task 4 writes `story-3-2-obsidian-config-validation.sh` (unique).
  - Task 5 modifies `story-1-1-scaffold-validation.sh` line 155 (single-line additive edit — exclusive write) and runs read-only regression.
  - Task 6 writes `story-3-2-task6-handoff.md` (unique).
  - Task 7 modifies `sprint-status.yaml` (exclusive write).
  - This story file is written by Task 7 (SM-pass edits) and by the Dev swarm (handoff edits); serialize story-file writes per phase.

**Swarm parallelization summary (MOST IMPORTANT — orchestrator uses this to launch parallel dev agents):**

- **Parallel wave 1 (independent evidence artifacts):** Task 1 || Task 2 — two subagents, no coupling.
- **Parallel wave 2 (independent config-file authoring; 3-way fan-out):** Task 3a || Task 3b || Task 3c — three subagents, each writing to disjoint JSON paths. Depends on wave 1 complete (Task 2 blueprint available).
- **Sequential after wave 2:** Task 4 (harness) → Task 5 (allowlist fix + regression) → Task 6 (handoff).
- **Independent throughout:** Task 7 (sprint tracker) — run at Phase 1 (SM pass) and Phase 2 (Dev handoff).

### References

- `_bmad/bmm/config.yaml` — BMAD module metadata and artifact path variables.
- `_bmad-output/planning-artifacts/epics.md` lines 266–274 — Epic 3 Story 3.2 statement and acceptance criteria (source of truth).
- `_bmad-output/planning-artifacts/epics.md` lines 252–286 — Epic 3 overview and Story 3.1 / 3.3 relationship.
- `_bmad-output/planning-artifacts/architecture.md` lines 1–26 — portability, secret-management, no-new-deps discipline.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` lines 103–120 — Epic 3 block (current `in-progress` state, Story 3.1 done, Stories 3.2 / 3.3 `backlog`).
- `_bmad-output/implementation-artifacts/3-1-port-template-trees-from-gtd-life-memory.md` — Story 3.1 canonical precedent: 17-token banned-term lock, 8-harness regression chain (from Story 3.2's perspective), Phase-4 F1/F2/F3/F4/F5/F7 review-fix patterns, allowlist-exception codification, per-directory count assertions, sentinel invariance, PASS-count fingerprints.
- `_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md` — canonical blueprint discipline; six-gate `task1`–`task6` + `all` dispatcher; banned-term set and boundary-guard discipline.
- `_bmad-output/implementation-artifacts/2-4-confirm-benji-inbox-default-not-ported.md` — additive-only discipline; autonomous-swarm status-collapse precedent; F1 / F3 / F4 review fixes to carry forward.
- `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` — direct harness model: gate naming, constant declaration style, `regex_self_probe` pattern, `check_task6` per-harness spec-loop fingerprint, forbidden-form probes.
- `_bmad-output/implementation-artifacts/tests/story-3-1-canonical-blueprint.md` — blueprint authoring style to mirror (section headers, key-order locks, banned-term lock block, placeholder allowlist block — Story 3.2 has no placeholder allowlist since JSON has no placeholder tokens; that section is replaced by `## Forbidden-file lock` and `## Meeting-slug fingerprint lock`).
- `_bmad-output/implementation-artifacts/tests/story-3-1-task6-handoff.md` — handoff-artifact structure to mirror (AC-to-evidence map, regression transcript, SHA-256 fingerprint table, forward-looking notes, zero-edit verification, integration-fix exception documentation).
- `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` — specifically line 155 (`memory)` branch allowlist regex) — target of the Story 3.2 one-line integration fix.
- `~/Public/gtd-life/memory/.obsidian/app.json` — gtd-life source (port verbatim).
- `~/Public/gtd-life/memory/.obsidian/appearance.json` — gtd-life source (port verbatim; already `{}`).
- `~/Public/gtd-life/memory/.obsidian/community-plugins.json` — gtd-life source (port verbatim; already `[]`).
- `~/Public/gtd-life/memory/.obsidian/core-plugins.json` — gtd-life source (port verbatim; 31 keys, clean).
- `~/Public/gtd-life/memory/.obsidian/daily-notes.json` — gtd-life source (port verbatim; 3 keys, clean).
- `~/Public/gtd-life/memory/.obsidian/graph.json` — gtd-life source (port verbatim; already clean, no Derek search queries or colorGroups).
- `~/Public/gtd-life/memory/.obsidian/templates.json` — gtd-life source (REPAIR required: `folder: "_templates"` → `folder: ""`).
- `~/Public/gtd-life/memory/.obsidian/workspace.json` — gtd-life source (EXCLUDED — user-local vault cache; contains Derek / Bobby / revivago / blog-ideas references; must not be ported).
- Git log (`git log --oneline -n 20`) — Epic 1 / 2 / 3 commit style `feat(epic-N): <change> (Story <key>)`. Story 3.2 follows `feat(epic-3): port portable obsidian config (Story 3-2-portable-obsidian-config)`.

## Change Log

- 2026-04-20 (Phase 1, Bob — SM): Story file authored from Epic 3 Story 3.2 spec (epics.md lines 266–274). Extended the 1-AC epic skeleton into 15 acceptance criteria to cover per-file shape (AC1–AC8), `workspace.json` exclusion + vault-cache hygiene (AC9), banned-term scrub (AC10), Story 3.1 invariance (AC11), harness wiring (AC12), 8-harness regression with Story 1.1 allowlist exception codification (AC13), sprint lifecycle (AC14), and additive-scope discipline (AC15). Task plan: 7 tasks with Tasks 3a–3c fanned out for 3-way parallelization on config-file authoring. `sprint-status.yaml` flipped `3-2-portable-obsidian-config.status` `backlog → ready-for-dev`, preserved `epic-3.status` at `in-progress` (Story 3.1 already opened the epic; Story 3.3 still backlog), and updated `last_updated` to `2026-04-20`. Ready for Phase 2 Dev swarm pickup.
- 2026-04-20 (Phase 3, Amelia — Senior Dev review-fix pass): Applied all 7 findings from the code-review report (3 HIGH: F1 AC7 self-contradiction, F2 missing key-count assertions, F3 `grep -c` → `grep -o | wc -l` counting technique; 2 MEDIUM: F4 Story-3.1-template byte-count assertions, F5 byte-budget upper bounds for core-plugins / daily-notes / templates; 2 LOW: F6 baseline-audit typo, F7 redundant `_templates` scrub cleanup). Harness hardening: converted all key-count assertions to `grep -o '":' | wc -l` (safe under `set -euo pipefail` via `{ grep -o …; || true; }` brace group to survive 0-match case for `appearance.json`); added key-count assertions for `app.json` (3), `appearance.json` (0), `daily-notes.json` (3), `graph.json` (20); added byte-budget upper bounds for `core-plugins.json` (≤1024), `daily-notes.json` (≤200), `templates.json` (≤64); added `templates.json` stripped-literal check (`== '{"folder":""}'`); added per-file byte-count assertions for the nine Story 3.1 templates (828 / 250 / 513 / 306 / 561 / 588 / 506 / 72 / 211, keyed off the Story 3.1 Task-6 handoff fingerprint); removed the duplicate `_templates` scrub from `check_task4` (invariant now owned solely by `check_task3`); added new `STORY_3_1_TEMPLATE_BYTES` constant to the `check_task5` self-check list. Story-file AC7 prose corrected to read "20 keys" (matching the already-listed 20 keys); blueprint `graph.json` section's "AC7 key-count correction" caveat dropped; handoff AC7 row reworded to cite AC7 as ground truth + new `grep -o '":' | wc -l == 20` assertion. Baseline-audit "Three of the six" → "Four of the six" typo fixed. 9-harness regression re-run end-to-end: PASS fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7`, all exit 0. Story 3.2 harness PASS-line count unchanged at 7 (`task1` → `task6` → `all`). Flipped `Status: review → done`. Sprint-status `3-2-portable-obsidian-config.status` flipped `review → done`; `epic-3.status: in-progress` preserved (Story 3.3 still backlog); `last_updated: "2026-04-20"` preserved.

## Dev Agent Record

### Agent Model Used

- To be filled by Dev subagents during Phase 2 execution. Expected slots: wave-1 (Task 1 audit) || (Task 2 blueprint); wave-2 (Task 3a config ports) || (Task 3b config ports) || (Task 3c templates.json REPAIR); wave-3 sequential (Task 4 harness → Task 5 allowlist fix + regression → Task 6 handoff → Task 7 sprint flip).
- 2026-04-20 Task 2 (wave-1 parallel slot): Amelia (claude-opus-4) — canonical blueprint authoring.
- 2026-04-20 Task 1 (wave-1 parallel slot): Amelia (Claude Opus 4.7) — baseline audit authoring.
- 2026-04-20 Task 3b (wave-2 parallel slot): Amelia (Claude Opus 4.7) — ported `memory/.obsidian/daily-notes.json` + `graph.json` per canonical blueprint.
- 2026-04-20 Task 3c (wave-2 parallel slot): Amelia (Claude Opus 4.7) — REPAIRED `templates.json` port (`folder: "_templates"` → `folder: ""`).
- 2026-04-20 Tasks 4 / 5 / 6 / 7 (wave-3 sequential): Amelia (Claude Opus 4.7) — authored validation harness, applied Story 1.1 allowlist integration fix, ran 9-harness regression, produced Task 6 handoff package, flipped sprint-status to `review`.
- 2026-04-20 Phase 3 Senior Developer Review fix pass: Amelia (Claude Opus 4.7) — applied all 7 review findings (F1–F7), re-ran 9-harness regression, flipped Status + sprint-status to `done`.

### Debug Log References

- To be filled by Dev subagents.
- 2026-04-20 Task 2: Directly read the seven gtd-life `.obsidian/` source files under `~/Public/gtd-life/memory/.obsidian/` to capture empirical key inventories and byte lengths (`ls -la` + per-file `Read` tool). Confirmed `graph.json` has 20 top-level keys (AC7 prose shows an illustrative 17-key excerpt — blueprint reconciles this by stating the empirical count and noting the AC7 upper-bound byte budget already admits the 20-key shape). Confirmed `core-plugins.json` ordering: 10 enabled, 4 disabled, 1 enabled (markdown-importer), 2 disabled, 1 enabled (outline), 7 disabled, 1 enabled (canvas), 1 disabled (footnotes), 3 enabled (properties, bookmarks, bases), 1 disabled (webviewer) — 16 true + 15 false = 31 keys matching AC5.
- 2026-04-20 Task 3b: used `mkdir -p memory/.obsidian/` (idempotent; directory created by this agent as parallel Task 3a had not yet materialised it). `daily-notes.json` copied byte-for-byte from `~/Public/gtd-life/memory/.obsidian/daily-notes.json` (68 bytes, trailing `0a` already present — `diff` against source returned no differences). `graph.json` authored from the canonical blueprint preserving all 20 keys in source order and numeric precision (`centerStrength: 0.518713248970312`, `repelStrength: 10`, `linkDistance: 250`); source was 493 bytes without trailing newline, port is 494 bytes with trailing newline per blueprint normalization. Verification scans against the two ported files: 17-token boundary-guarded banned-term regex → zero matches; `bobby` fixed-string → zero; meeting-slug regex `[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+` → zero; fixed-string `gtd-life` / `/Users/` / `Public/` → zero each. Key-count probes: `daily-notes.json` `grep -c '":' == 3`, `graph.json` `grep -c '":' == 20` (empirical count per blueprint, not AC7-prose 17). All 20 graph-key presence probes passed; `"search": ""`, `"colorGroups": []`, `"folder": "daily"`, `"format": "YYYY-MM-DD"`, `"template": ""` all matched.
- 2026-04-20 Task 1: no debugging required. Enumerated `~/Public/gtd-life/memory/.obsidian/` (7 portable JSON + 1 excluded `workspace.json`); ran 17-token boundary-guarded banned-term regex, path-leak fixed-string scans (`/Users/`, `gtd-life`, `~/`, `Public/`), `bobby` fixed-string scan, and meeting-slug regex (`[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+`) against all eight sources. Observed byte/line counts: app.json 89/4 (no trailing newline), appearance.json 2/0 (no trailing newline), community-plugins.json 3/1 (has trailing newline), core-plugins.json 701/32 (no trailing newline), daily-notes.json 68/5 (has trailing newline), graph.json 493/21 (no trailing newline), templates.json 29/3 (has trailing newline), workspace.json 7374/225. Seven portable files: zero hits across all four scan categories — port-verbatim with trailing-newline normalization where absent. `workspace.json`: 19 banned-term regex hits, 7 `bobby` fixed-string hits, 30 meeting-slug fingerprint hits → EXCLUDED from port. `templates.json`: clean of banned content but `folder: "_templates"` points at a non-existent directory (Story 3.1 declined `_templates/` layout) → REPAIR to `folder: ""`. No `plugins/` subdirectory exists at source; `community-plugins.json` is `[]` as expected.
- 2026-04-20 Task 3a: ported four files under `memory/.obsidian/` (verbatim from gtd-life source with trailing-newline normalization for `app.json`, `appearance.json`, `core-plugins.json`; `community-plugins.json` already had a trailing newline at source). Emitted byte counts: `app.json` 90, `appearance.json` 3, `community-plugins.json` 3, `core-plugins.json` 702 — each byte-compatible with the source plus the normalized trailing `\n`. Ran the four required scans per file: 17-token boundary-guarded banned-term regex → 0 hits, `bobby` case-insensitive fixed-string → 0 hits, path-reference fixed-string (`gtd-life`, `/Users/`, `Public/`) → 0 hits, meeting-slug regex `[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+` → 0 hits. Structural sanity: `app.json` / `appearance.json` / `core-plugins.json` first non-whitespace `{`, last `}`; `community-plugins.json` first `[`, last `]`. Trailing-newline probe (`tail -c 1 | od -An -tx1`) returned `0a` for all four. `core-plugins.json` key count via `grep -c '":'` equals `31` (16 `true` + 15 `false` matching the AC5 / blueprint canonical order). `app.json` literal-value probes confirmed `"strictLineBreaks"`, `"showFrontmatter"`, `"defaultViewMode": "source"` all present. Task 3a scope strictly honored: no other tasks touched, no harness modified, no sprint-status modified, no `plugins/` subdir created.
- 2026-04-20 Tasks 4–7 (sequential, single agent): authored `story-3-2-obsidian-config-validation.sh` modeled on Story 3.1 harness; constants declared per Task 4 subtask spec (seven file-path constants + `WORKSPACE_JSON` + `BASELINE_AUDIT_PATH` + `BLUEPRINT_PATH` + eight `STORY_*_HARNESS` + `BANNED_TERMS_REGEX` (17-token, identical to Story 3.1) + `MEETING_SLUG_REGEX` (`[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+`) + `STORY_3_1_TEMPLATE_FILES` nine-entry array); `regex_self_probe()` exercises `derek`/`derekson`, `personal`/`personally`, and meeting-slug positive/negative (including a bare-date negative probe to prove the `YYYY-MM-DD` literal in `daily-notes.json` does not false-trip). Applied the Story 1.1 line-155 allowlist extension (single-character-set insertion of `|\.obsidian` after `obsidian`). Self-check passed. Ran Story 3.2 harness in `all` mode: `PASS: task1` → `PASS: task6` → `PASS: all`, exit 0, 7 `^PASS:` lines. Ran all 9 harnesses individually: per-harness PASS-count fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7` — exact match. No harness emitted unexpected output. Wrote `story-3-2-task6-handoff.md` with AC-to-evidence map (15 rows), full 9-harness transcript, byte-count + SHA-256 fingerprint table for the seven ported files (total 1379 bytes), zero-edit verification block, Story 1.1 integration-fix exception documentation, and forward-looking notes for Stories 3.3 / Epic 4 / Epic 5 / Epic 6 + Obsidian user-experience notes. Flipped `sprint-status.yaml` `3-2-portable-obsidian-config.status` from `ready-for-dev` to `review`; preserved `epic-3.status: in-progress`, `last_updated: "2026-04-20"`, and byte-for-byte comment/ordering discipline (only the two single-line value changes). Updated this story file Status line `ready-for-dev` → `review` and marked every remaining Task 4 / 5 / 6 / 7 subtask `[x]`. SHA-256 fingerprints captured for drift detection: app.json `c39e6f3f…`, appearance.json `ca3d163b…`, community-plugins.json `37517e5f…`, core-plugins.json `ac8a3c03…`, daily-notes.json `f21e73a2…`, graph.json `f75c7af6…`, templates.json `935f8fce…`.

### Completion Notes List

- To be filled by Dev subagents.
- 2026-04-20 Task 3b: Two portable `.obsidian/` config files ported under `memory/.obsidian/` per the Task 2 canonical blueprint. `daily-notes.json` is byte-for-byte identical to the gtd-life source (3 keys in canonical order: `folder: "daily"`, `format: "YYYY-MM-DD"`, `template: ""`; 68 bytes with trailing `\n`). `graph.json` is the blueprint-canonical 20-key object in source order with all numeric precision preserved (`centerStrength: 0.518713248970312`, etc.) and trailing-newline normalization applied (493-byte source → 494-byte port). Both files pass every required scan: 17-token banned-term regex zero-match, `bobby` fixed-string zero-match, meeting-slug regex zero-match, and path-leak fixed-string scans zero-match. Per-file shape probes all pass including `grep -c '":' == 20` on `graph.json` (per blueprint, not AC7-prose 17) and `grep -c '":' == 3` on `daily-notes.json`. Did NOT touch Tasks 1 / 2 / 3a / 3c / 4 / 5 / 6 / 7; did NOT modify `sprint-status.yaml`, any harness, or any other prior-story artifact. Directory `memory/.obsidian/` was created by this agent (parallel Task 3a had not yet materialised it); `mkdir -p` is idempotent so parallel Task 3a / 3c siblings can still safely create the same directory.
- 2026-04-20 Task 2: Canonical blueprint authored at `_bmad-output/implementation-artifacts/tests/story-3-2-canonical-blueprint.md`. Structure mirrors Story 3.1 precedent: one section per target file (seven sections), `## Forbidden-file lock`, `## Banned-term lock`, `## Meeting-slug fingerprint lock`, `## Out-of-scope lock`, `## Cross-AC coverage map`. All seven per-file sections declare top-level structure (object vs array), full key inventory with types and literal values in canonical gtd-life source order, byte budget (source + upper bound), port method (verbatim or REPAIRED), and harness probe list. The `templates.json` REPAIR (`"folder": "_templates"` → `""`) is documented with source value, port value, rationale, effect, classification, byte budget, and explicit `_templates` forbidden-substring lock. The 17-token banned-term regex is reproduced verbatim from Story 3.1 (zero new tokens). The `bobby` fixed-string backstop and meeting-slug regex `[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+` are documented as Story-3.2-specific additions to defend against `workspace.json` leakage. Out-of-scope lock enumerates forbidden paths (`workspace.json`, `plugins/`, `memory/daily/`, `memory/_templates/`, `memory/me/`, repo-root `.obsidian/`) and preserved-unchanged paths (`memory/.gitkeep` + nine Story 3.1 template files). AC7 key-count discrepancy (prose 17 vs empirical 20) is resolved explicitly inside the `graph.json` section.
- 2026-04-20 Task 1 (baseline audit) complete. Evidence artifact written at `_bmad-output/implementation-artifacts/tests/story-3-2-baseline-audit.md` with all eight required sections (title + seven `##` sections per Task 1's persistence subtask and per the harness `check_task1` gate). Audit confirms six portable files (`app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`) are already clean in the gtd-life source and port verbatim (with trailing-newline normalization for four that lack one). `templates.json` is the ONE defect / repair — `folder` value scrubbed from `"_templates"` → `""`. `workspace.json` is EXCLUDED with 56 total leakage fingerprints documented (19 banned-term + 7 `bobby` + 30 meeting-slug). Out-of-scope paths fully enumerated. Task 1 subtasks marked `[x]`. Did NOT touch Tasks 2 / 3a / 3b / 3c / 4 / 5 / 6 / 7. Did NOT modify `sprint-status.yaml`, any harness, `memory/.obsidian/` (does not yet exist), or any other prior-story artifact.
- 2026-04-20 Task 3a (port four portable `.obsidian/` config files) complete. Created `memory/.obsidian/` via `mkdir -p` (idempotent). Authored the four files verbatim from `~/Public/gtd-life/memory/.obsidian/`: `app.json` (3-key object, 90 bytes), `appearance.json` (empty object `{}`, 3 bytes), `community-plugins.json` (empty array `[]`, 3 bytes), `core-plugins.json` (31-key object, 702 bytes). Each file ends with a single `\n` (normalization applied where source lacked trailing newline). All four verification scans passed with zero hits (banned-term regex, `bobby` fixed-string, path-reference fixed-string, meeting-slug regex). `core-plugins.json` key count verified at 31. `app.json` literal values for `strictLineBreaks`, `showFrontmatter`, `defaultViewMode: "source"` verified present. Task 3a subtasks marked `[x]`. Strict scope: did NOT touch Tasks 1 / 2 / 3b / 3c / 4 / 5 / 6 / 7; did NOT modify `sprint-status.yaml`, any harness, or any other prior-story artifact; did NOT create `memory/.obsidian/plugins/` or any other `.obsidian/` subdirectory.
- 2026-04-20 Task 3c (REPAIRED `templates.json` port) complete. Authored `memory/.obsidian/templates.json` fresh (not copied from gtd-life source) with pretty-printed body `{\n  "folder": ""\n}\n` — 19 bytes, trailing-newline terminated (last byte `0a`), matching the 4-space-indent style of sibling Obsidian JSON configs. Verification results: `grep -iE` 17-token banned-term regex → 0 matches; `grep -Fi 'bobby'` → 0 matches; `grep -E` meeting-slug regex `[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+` → 0 matches; `grep -F '_templates'` → 0 matches (REPAIR verified — source string `"_templates"` scrubbed); `grep -F '"folder": ""'` → match confirmed (REPAIRED value emitted); fixed-string path-reference scans (`gtd-life`, `/Users/`, `Public/`) → 0 matches each. Byte budget 19 bytes well within the blueprint upper bound of 64. Created `memory/.obsidian/` via `mkdir -p` (idempotent; may have been created concurrently by parallel Task 3a/3b agents). Touched ONLY `memory/.obsidian/templates.json` and this story file (Task 3c subtask checkboxes + Dev Agent Record / File List entries). Did NOT touch Tasks 1 / 2 / 3a / 3b / 4 / 5 / 6 / 7, `sprint-status.yaml`, any harness, or any other prior-story artifact.

### File List

- To be filled by Dev subagents at Phase 2 handoff. Expected Created list: `_bmad-output/implementation-artifacts/tests/story-3-2-baseline-audit.md`, `_bmad-output/implementation-artifacts/tests/story-3-2-canonical-blueprint.md`, `memory/.obsidian/app.json`, `memory/.obsidian/appearance.json`, `memory/.obsidian/community-plugins.json`, `memory/.obsidian/core-plugins.json`, `memory/.obsidian/daily-notes.json`, `memory/.obsidian/graph.json`, `memory/.obsidian/templates.json`, `memory/.obsidian/` directory, `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh`, `_bmad-output/implementation-artifacts/tests/story-3-2-task6-handoff.md`. Expected Modified list: this story file, `_bmad-output/implementation-artifacts/sprint-status.yaml`, `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` (one-line line-155 allowlist extension — documented AC13 / AC15 exception).
- 2026-04-20 Task 2 Created:
  - `_bmad-output/implementation-artifacts/tests/story-3-2-canonical-blueprint.md` (canonical blueprint for seven ported `.obsidian/` JSON files; per-file key inventories in canonical gtd-life source order; templates.json REPAIR spec; 17-token banned-term lock + `bobby` fixed-string backstop + meeting-slug regex; out-of-scope lock; AC coverage map).
- 2026-04-20 Task 1 Created:
  - `_bmad-output/implementation-artifacts/tests/story-3-2-baseline-audit.md` (baseline audit of `~/Public/gtd-life/memory/.obsidian/`; inventory of 7 portable JSON + excluded `workspace.json`; per-file JSON structure + key maps; banned-term / path-leak / `bobby` / meeting-slug scans with counts; `workspace.json` exclusion rationale with 19 + 7 + 30 fingerprint counts; `templates.json` `"_templates"` → `""` defect / repair spec; out-of-scope paths; source → target mapping).
- 2026-04-20 Task 1 Modified: this story file (Task 1 subtask checkboxes marked `[x]`; Dev Agent Record / File List appended — Task 1 entries only; no other changes).
- 2026-04-20 Task 3b Created:
  - `memory/.obsidian/` (directory; `mkdir -p` idempotent — may have been created by a parallel Task 3a or 3c sibling).
  - `memory/.obsidian/daily-notes.json` (68 bytes; 3 keys `folder: "daily"` / `format: "YYYY-MM-DD"` / `template: ""`; trailing newline; byte-for-byte identical to gtd-life source).
  - `memory/.obsidian/graph.json` (494 bytes; 20 keys in canonical source order per blueprint; `search: ""`, `colorGroups: []`, all numeric values preserved verbatim from source; trailing newline normalized).
- 2026-04-20 Task 3b Modified: this story file (Task 3b subtask checkboxes marked `[x]`; Dev Agent Record / File List appended — Task 3b entries only; no other changes).
- 2026-04-20 Task 3a Created:
  - `memory/.obsidian/` (new directory)
  - `memory/.obsidian/app.json` (verbatim port of gtd-life source + trailing-newline normalization; 90 bytes; 3-key object `strictLineBreaks: false`, `showFrontmatter: true`, `defaultViewMode: "source"`)
  - `memory/.obsidian/appearance.json` (verbatim empty object `{}` + trailing newline; 3 bytes)
  - `memory/.obsidian/community-plugins.json` (verbatim empty array `[]` + trailing newline; 3 bytes)
  - `memory/.obsidian/core-plugins.json` (verbatim port of gtd-life source + trailing-newline normalization; 702 bytes; 31-key object, 16 `true` + 15 `false` per blueprint)
- 2026-04-20 Task 3a Modified: this story file (Task 3a subtask checkboxes marked `[x]`; Dev Agent Record / File List appended — Task 3a entries only; no other changes).
- 2026-04-20 Task 3c Created:
  - `memory/.obsidian/templates.json` (REPAIRED — single-key JSON object `{"folder": ""}` pretty-printed with trailing newline; 19 bytes; source gtd-life value `"_templates"` scrubbed to `""` per AC8 Defect #1 repair to avoid dangling reference to non-existent `memory/_templates/` directory).
  - `memory/.obsidian/` directory (created idempotently via `mkdir -p`; parallel Tasks 3a / 3b may have created it concurrently).
- 2026-04-20 Task 3c Modified: this story file (Task 3c subtask checkboxes marked `[x]`; Dev Agent Record / File List appended — Task 3c entries only; no other changes).
- 2026-04-20 Tasks 4–7 Created:
  - `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh` (executable `0755`; 6 gates + `all`; POSIX-bash-3.2 compatible; no `jq`/`node`/`python`; sub-harness stderr capture in `check_task6`; `declare -F regex_self_probe` probe-presence idiom).
  - `_bmad-output/implementation-artifacts/tests/story-3-2-task6-handoff.md` (AC-to-evidence map; full 9-harness transcript; byte-count + SHA-256 fingerprint table for seven ported JSON files; zero-edit verification block; Story 1.1 integration-fix exception documentation; forward-looking notes).
- 2026-04-20 Tasks 4–7 Modified:
  - `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` (single-line additive extension on line 155: `|\.obsidian` inserted into the `memory)` branch allowlist regex — documented AC13 / AC15 exception following Story 2.1 commit `0db273b` + Story 3.1 Phase-4 F1 precedent).
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (Story 3.2 status flipped `ready-for-dev → review`; `epic-3.status: in-progress` preserved; `last_updated: "2026-04-20"` preserved).
  - This story file (Status line flipped `ready-for-dev → review`; Task 4 / 5 / 6 / 7 subtask checkboxes marked `[x]`; Dev Agent Record / File List appended — wave-3 sequential entries; no prior-task checkboxes or entries mutated).
- 2026-04-20 Phase 3 Senior Developer Review fix pass — Modified:
  - `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh` (F2 + F3 + F4 + F5 + F7 — added 4 key-count assertions, switched to `grep -o '":' | wc -l` occurrence-counting with `pipefail`-safe brace-group guard, added 3 byte-budget upper bounds, added per-file byte-count fingerprints for the nine Story 3.1 templates via new `STORY_3_1_TEMPLATE_BYTES` array, added `templates.json` stripped-literal `{"folder":""}` assertion, removed redundant `_templates` scrub from `check_task4`, extended `check_task5` self-check list by one constant).
  - `_bmad-output/implementation-artifacts/3-2-portable-obsidian-config.md` (F1 — AC7 prose `"17 keys including" → "20 keys:"`; Change Log appended; Status `review → done`; Senior Developer Review + Review Follow-ups sections populated; Dev Agent Record + File List appended).
  - `_bmad-output/implementation-artifacts/tests/story-3-2-canonical-blueprint.md` (F1 — dropped `graph.json` "AC7 key-count correction" caveat; section reframed to cite AC7 as ground truth).
  - `_bmad-output/implementation-artifacts/tests/story-3-2-baseline-audit.md` (F6 — `"Three of the six" → "Four of the six"` typo fix on line 22).
  - `_bmad-output/implementation-artifacts/tests/story-3-2-task6-handoff.md` (F1 — AC7 row reworded to cite AC7 as ground truth + the new `grep -o '":' | wc -l == 20` assertion; downstream prose note aligned).
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (Story 3.2 status flipped `review → done`; `epic-3.status: in-progress` preserved; `last_updated: "2026-04-20"` preserved).

## Review Follow-ups (AI)

Phase 3 Senior Developer Review (2026-04-20, Amelia). All 7 findings applied; 9-harness regression re-run end-to-end, PASS fingerprint unchanged (`1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7`).

- [x] **F1 (HIGH) — AC7 self-contradiction resolved.** Story line 61 AC7 prose updated `"17 keys including" → "20 keys:"` to match the already-listed 20 keys. Blueprint "AC7 key-count correction" caveat (around `graph.json` section, line ~245) dropped — AC7 is now the ground truth. Handoff AC7 row reworded to cite AC7 directly and reference the new `grep -o '":' | wc -l == 20` assertion instead of "empirical count per blueprint". Secondary blueprint note in `graph.json` key-inventory section rewritten for consistency.
- [x] **F2 (HIGH) — Missing key-count assertions added.** Added `grep -o '":' | wc -l` occurrence-count assertions in `check_task3` for `app.json` (`== 3`), `appearance.json` (`== 0`), `daily-notes.json` (`== 3`), and `graph.json` (`== 20`). Each follows the existing core-plugins / templates pattern but uses the F3 corrected idiom.
- [x] **F3 (HIGH) — Counting technique corrected.** Replaced `grep -c '":'` (counts matching LINES — unsafe for compact JSON) with `grep -o '":' | wc -l` (counts OCCURRENCES, reliable on BSD + GNU grep) for `core-plugins.json`, `templates.json`, and the four new F2 assertions. Wrapped each `grep -o` in a `{ grep -o …; || true; }` brace group so `pipefail` does not kill the harness when the occurrence count is 0 (necessary for `appearance.json`). Also added the companion stripped-literal check for `templates.json`: `tr -d '[:space:]' == '{"folder":""}'`.
- [x] **F4 (MEDIUM) — Byte-count assertions for 9 Story 3.1 templates added.** New `STORY_3_1_TEMPLATE_BYTES` indexed-array constant (positional mapping to `STORY_3_1_TEMPLATE_FILES`) holds the byte-count fingerprint from the Story 3.1 Task-6 handoff: `meeting.md=828`, `agenda.md=250`, `prep.md=513`, `transcript.md=306`, `people/_template.md=561`, `decisions/_template.md=588`, `reference/_template.md=506`, `inbox/_template.md=72`, `appreciations/_template.md=211`. `check_task3` AC11 block loops both arrays by index and asserts `wc -c < <file> == expected`. Any future template-file drift now fails `check_task3`. Constant added to `check_task5` self-check list.
- [x] **F5 (MEDIUM) — Byte-budget upper bounds added.** `check_task3` now asserts `core-plugins.json <= 1024`, `daily-notes.json <= 200`, `templates.json <= 64` — matching the blueprint budgets. Pattern mirrors the existing `app.json (<=200)`, `appearance.json (<=10)`, `community-plugins.json (<=10)`, `graph.json (<=1024)` checks.
- [x] **F6 (LOW) — Baseline-audit off-by-one fixed.** Baseline-audit line 22: `"Three of the six byte-compatible source files" → "Four of the six byte-compatible source files"` — the parenthetical list already correctly names four (app.json, appearance.json, core-plugins.json, graph.json).
- [x] **F7 (LOW) — Redundant `_templates` scrub removed (Option A).** Removed the duplicate `grep -Fq '_templates' "${TEMPLATES_JSON}"` block from `check_task4` (lines 481-484 pre-fix). Single-point-of-truth for AC8 `_templates` REPAIR assertion is `check_task3`'s `TEMPLATES_JSON` block. `check_task4` now holds only cross-file scrubs (banned terms, path references, `bobby`, meeting-slug); the AC8 `_templates` assertion is cleanly mapped to `check_task3`. Replacement comment explains the invariant-to-gate mapping.

## Senior Developer Review (AI)

**Reviewer:** Amelia (Senior Software Engineer, autonomous Dev subagent)
**Date:** 2026-04-20
**Context:** Phase 3 Senior Developer Review — applied the 7 findings returned by the upstream code-review report (3 HIGH, 2 MEDIUM, 2 LOW; `CHANGES_REQUESTED`).
**Scope reviewed:** `_bmad-output/implementation-artifacts/3-2-portable-obsidian-config.md`, `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh`, `_bmad-output/implementation-artifacts/tests/story-3-2-canonical-blueprint.md`, `_bmad-output/implementation-artifacts/tests/story-3-2-baseline-audit.md`, `_bmad-output/implementation-artifacts/tests/story-3-2-task6-handoff.md`.

### Outcome

**APPROVED** after review-fix pass. All 7 findings resolved; full 9-harness regression re-run end-to-end with fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7` (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2). Story 3.2 harness PASS-line count unchanged at 7 — new assertions integrated into the existing 6 gates + `all` dispatcher without adding a gate. Story 3.2 flipped `review → done`; `sprint-status.yaml` flipped `3-2-portable-obsidian-config.status` `review → done` with `epic-3.status: in-progress` preserved (Story 3.3 still backlog).

### Findings and resolutions

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F1 | HIGH | AC7 prose said "17 keys including" but listed 20 — internal contradiction masked by the "AC7 key-count correction" caveat in the blueprint. | Story AC7 reworded to "20 keys:" (ground truth). Blueprint caveat dropped; section reframed to cite AC7 as ground truth. Handoff AC7 row reworded (see Follow-ups F1). |
| F2 | HIGH | `check_task3` was missing key-count assertions promised by the blueprint for `app.json`, `appearance.json`, `daily-notes.json`, `graph.json` — only `core-plugins.json` and `templates.json` had them. | Added the four missing assertions using the F3 corrected counting technique (see Follow-ups F2). |
| F3 | HIGH | Counting idiom `grep -c '":'` counts MATCHING LINES, which silently passes for compact JSON where many `":` appear on one line (would pass even if someone collapsed `core-plugins.json` to a single line). | Switched to `grep -o '":' \| wc -l` (occurrence counting — reliable on BSD + GNU grep). Wrapped in `{ grep -o …; \|\| true; }` to survive `pipefail` when count is 0 (appearance.json). Also added stripped-literal check for `templates.json` (`== '{"folder":""}'`). |
| F4 | MEDIUM | AC11 Story-3.1-template invariance block only asserted existence + non-empty — would silently pass if a template file were truncated/modified while remaining non-empty. | Added `STORY_3_1_TEMPLATE_BYTES` indexed-array constant with 9 expected byte counts pulled verbatim from the Story 3.1 Task-6 handoff. `check_task3` now asserts `wc -c <file> == expected` per template. Constant listed in `check_task5` self-check. |
| F5 | MEDIUM | Byte-budget upper bounds missing for `core-plugins.json`, `daily-notes.json`, `templates.json` — other five files had them but these three did not. | Added `<= 1024` / `<= 200` / `<= 64` assertions matching blueprint budgets. |
| F6 | LOW | Baseline-audit prose off-by-one: "Three of the six byte-compatible source files" contradicted the parenthetical list of 4 files. | Changed to "Four of the six byte-compatible source files". |
| F7 | LOW | Redundant `_templates` scrub appeared in both `check_task3` (primary AC8 gate) and `check_task4` (post-loop). Choice: Option A (remove from check_task4). | Removed the duplicate from `check_task4`; single-point-of-truth invariant now lives in `check_task3`. Replacement comment in `check_task4` documents the mapping. |

### Verification

- **Syntax.** `bash -n` on the harness returns clean.
- **Story 3.2 harness isolated.** `bash story-3-2-obsidian-config-validation.sh all` → `PASS: task1` through `PASS: task6` then `PASS: all`, exit 0, exactly 7 `^PASS:` lines (unchanged from pre-fix).
- **Full 9-harness regression.** All nine predecessors + Story 3.2 exit 0 with PASS fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7`. `task6` gate inside the Story 3.2 harness itself passes cleanly, confirming the regression chain is end-to-end healthy.
- **No new failures introduced.** The F3 `pipefail` interaction (grep exit-1 on 0 matches) was caught and resolved via the `{ grep -o …; || true; }` brace group before final regression run. This was the only behavior regression during the review-fix pass; it was local to the new assertions and never present in the pre-fix harness.

### Deferred / not applied

None. All 7 findings applied in full; no scope reductions.

### Notes for future review passes

- The `grep -o | wc -l` idiom is now the project standard for JSON key-count assertions; Stories 3.3 / 4.x / 5.x should adopt the same pattern (with the brace-group `|| true` guard) if they add analogous gates.
- `STORY_3_1_TEMPLATE_BYTES` is a point-in-time fingerprint — any future story that legitimately edits a Story 3.1 template file must update this array in the Story 3.2 harness in the same commit. The harness will fail closed otherwise, which is desirable for drift detection.
- The `templates.json` stripped-literal `== '{"folder":""}'` assertion is stricter than the blueprint byte-budget (64) + single-key assertion alone. If a future story intentionally changes the templates-plugin folder value (e.g. to `"daily"`), both the blueprint, the AC8 prose, and this assertion must be updated atomically.
