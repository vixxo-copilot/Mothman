# Story 3.2 Baseline Audit

Captured during Task 1 (Phase 2, Dev agent Amelia). This audit records the upstream `~/Public/gtd-life/memory/.obsidian/` Obsidian-config contents that Story 3.2 ports into the generic `assistants-template` vault, plus the per-file JSON structure + key map, banned-term scan of the source files, the `workspace.json` exclusion rationale (with evidence), the one known defect requiring repair during the port, out-of-scope `.obsidian` subdirectories / paths, and the source-path → target-path mapping. Evidence here drives Task 2's canonical blueprint and Task 4's cross-file scrub. Source config lives outside this repository at `~/Public/gtd-life/memory/.obsidian/` and is read-only reference material — six of the seven portable files are ported byte-compatible; one (`templates.json`) is REPAIRED to scrub a dangling folder reference; `workspace.json` is EXCLUDED entirely.

Scope lock: Story 3.2 targets exactly seven JSON config files at `memory/.obsidian/` (`app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`, `templates.json`). The audit below enumerates those seven portable sources plus the excluded `workspace.json` for traceability. No community-plugin subdirectory (`plugins/`) is bundled — that content is user-installable and out of scope.

## gtd-life .obsidian source inventory

Enumerated on 2026-04-20 from `~/Public/gtd-life/memory/.obsidian/` (host: macOS darwin 25.4.0). All eight source files are plain UTF-8 JSON. The source `.obsidian/` directory contains NO `plugins/` subdirectory, NO `*.bak` files, NO `*.log` files, NO `.DS_Store`, NO `workspaces.json` (plural). A single `workspace.json` (singular) is present and is EXCLUDED from the port (see "workspace.json exclusion rationale" below).

| # | Source path | Bytes | Lines | Last byte | In scope? |
|---|-------------|-------|-------|-----------|-----------|
| 1 | `~/Public/gtd-life/memory/.obsidian/app.json` | 89 | 4 | `0x7d` (`}`) — no trailing newline in source | YES — port verbatim + add trailing newline |
| 2 | `~/Public/gtd-life/memory/.obsidian/appearance.json` | 2 | 0 | `0x7d` (`}`) — no trailing newline in source | YES — port verbatim (`{}`) + add trailing newline |
| 3 | `~/Public/gtd-life/memory/.obsidian/community-plugins.json` | 3 | 1 | `0x0a` (`\n`) — has trailing newline | YES — port verbatim (`[]\n`) |
| 4 | `~/Public/gtd-life/memory/.obsidian/core-plugins.json` | 701 | 32 | `0x7d` (`}`) — no trailing newline in source | YES — port verbatim + add trailing newline |
| 5 | `~/Public/gtd-life/memory/.obsidian/daily-notes.json` | 68 | 5 | `0x0a` (`\n`) — has trailing newline | YES — port verbatim |
| 6 | `~/Public/gtd-life/memory/.obsidian/graph.json` | 493 | 21 | `0x7d` (`}`) — no trailing newline in source | YES — port verbatim + add trailing newline |
| 7 | `~/Public/gtd-life/memory/.obsidian/templates.json` | 29 | 3 | `0x0a` (`\n`) — has trailing newline | YES — REPAIRED port (see Defect below) |
| 8 | `~/Public/gtd-life/memory/.obsidian/workspace.json` | 7374 | 225 | — | **NO — EXCLUDED** (user-local vault cache; see rationale below) |

**Trailing-newline normalization during port.** Four of the six byte-compatible source files (`app.json`, `appearance.json`, `core-plugins.json`, `graph.json`) do NOT end with a trailing newline in the gtd-life source (Obsidian writes without one on macOS). AC1 requires every ported file to end with a single `\n`; the port adds a trailing newline to those files. This is a POSIX-tool-friendliness normalization (matches `wc -l`, `tail -c 1` expectations) and does not change semantic JSON content. The files' byte-length upper bounds in AC2–AC7 admit this one-byte increase.

## Per-file JSON structure + key map

### 1. `memory/.obsidian/app.json` (89 bytes; 3 keys)

- Top-level structure: JSON **OBJECT**
- Keys (in source order): `strictLineBreaks`, `showFrontmatter`, `defaultViewMode`
- Value types: boolean, boolean, string
- Canonical values: `strictLineBreaks: false`, `showFrontmatter: true`, `defaultViewMode: "source"`
- Pretty-printed with 2-space indent. Source is CLEAN (zero banned-term hits, zero path leaks, zero meeting-slug fingerprints). Port verbatim.

### 2. `memory/.obsidian/appearance.json` (2 bytes; 0 keys)

- Top-level structure: JSON **OBJECT**
- Keys: none (literal bytes `{}` — no trailing newline in source, two bytes total)
- Source is CLEAN. Port verbatim as `{}\n` (adds trailing newline per AC1).
- Note: AC3 in the story states "the literal bytes `{}\n` is 3 bytes" — matches the ported output; the source is 2 bytes because it has no trailing newline. The upper bound of 10 bytes admits this whitespace variation without admitting content drift.

### 3. `memory/.obsidian/community-plugins.json` (3 bytes; 0 elements)

- Top-level structure: JSON **ARRAY**
- Length: 0 (empty — literal bytes `[]\n`)
- Source is CLEAN. Port verbatim.
- `plugins/` subdirectory does NOT exist at `~/Public/gtd-life/memory/.obsidian/plugins/` — no community-plugin binaries to bundle, matching the template's zero-community-plugin contract.

### 4. `memory/.obsidian/core-plugins.json` (701 bytes; 31 keys)

- Top-level structure: JSON **OBJECT**
- Key count: 31 (verified via `grep -c '":' core-plugins.json` → `31`)
- Keys in source order (with enablement): `file-explorer` (true), `global-search` (true), `switcher` (true), `graph` (true), `backlink` (true), `outgoing-link` (true), `tag-pane` (true), `page-preview` (true), `daily-notes` (true), `templates` (true), `note-composer` (false), `command-palette` (false), `slash-command` (false), `editor-status` (false), `markdown-importer` (true), `zk-prefixer` (false), `random-note` (false), `outline` (true), `word-count` (false), `slides` (false), `audio-recorder` (false), `workspaces` (false), `file-recovery` (false), `publish` (false), `sync` (false), `canvas` (true), `footnotes` (false), `properties` (true), `bookmarks` (true), `bases` (true), `webviewer` (false)
- Enabled (16 total, value `true`): `file-explorer`, `global-search`, `switcher`, `graph`, `backlink`, `outgoing-link`, `tag-pane`, `page-preview`, `daily-notes`, `templates`, `markdown-importer`, `outline`, `canvas`, `properties`, `bookmarks`, `bases`
- Disabled (15 total, value `false`): `note-composer`, `command-palette`, `slash-command`, `editor-status`, `zk-prefixer`, `random-note`, `word-count`, `slides`, `audio-recorder`, `workspaces`, `file-recovery`, `publish`, `sync`, `footnotes`, `webviewer`
- 16 + 15 = 31 keys total. Matches AC5 exactly.
- Source is CLEAN (zero banned-term hits, zero path leaks). Port verbatim. Key order matches the canonical AC5 spec.

### 5. `memory/.obsidian/daily-notes.json` (68 bytes; 3 keys)

- Top-level structure: JSON **OBJECT**
- Keys (in source order): `folder`, `format`, `template`
- Canonical values: `folder: "daily"` (relative-to-vault-root; NOT a Derek-specific absolute path), `format: "YYYY-MM-DD"`, `template: ""` (empty string — gtd-life source does NOT wire a daily-note template)
- Source is CLEAN. Port verbatim.

### 6. `memory/.obsidian/graph.json` (493 bytes; 20 keys)

- Top-level structure: JSON **OBJECT**
- Key count: 20 (Story 3.2 AC7 / Task 2 subtask notes both the initial "17" figure and the corrected "20" figure — the canonical count is 20, verified via direct enumeration below)
- Keys in source order (with value type and observed value): `collapse-filter` (bool, `true`), `search` (string, `""` — EMPTY; no carried-over search query), `showTags` (bool, `false`), `showAttachments` (bool, `false`), `hideUnresolved` (bool, `false`), `showOrphans` (bool, `true`), `collapse-color-groups` (bool, `true`), `colorGroups` (array, `[]` — EMPTY; no Derek-authored groups), `collapse-display` (bool, `true`), `showArrow` (bool, `false`), `textFadeMultiplier` (number, `0`), `nodeSizeMultiplier` (number, `1`), `lineSizeMultiplier` (number, `1`), `collapse-forces` (bool, `true`), `centerStrength` (number, `0.518713248970312`), `repelStrength` (number, `10`), `linkStrength` (number, `1`), `linkDistance` (number, `250`), `scale` (number, `1`), `close` (bool, `true`)
- The `search` value is the EMPTY STRING `""` — no `"tmo"` or other carried-over query (AC7 explicit assertion).
- The `colorGroups` value is the EMPTY ARRAY `[]` — no Derek-authored color groups (AC7 explicit assertion).
- `centerStrength: 0.518713248970312` is a non-round number that looks personalized but is a settled UI-drag-result from Obsidian's graph-simulation physics — shape-only; the port preserves the source value verbatim per AC7 ("no numeric value contains a Derek-specific non-default … the assertion is shape-only").
- Source is CLEAN. Port verbatim.

### 7. `memory/.obsidian/templates.json` (29 bytes; 1 key — source) / REPAIRED to 1 key with different value

- Top-level structure: JSON **OBJECT**
- Source keys (1): `folder` with value `"_templates"` — points at `memory/_templates/`, a directory that does NOT exist in this template (Story 3.1 explicitly declined to create the alternate `_templates/` single-file layout in favor of the per-directory `_template.md` / `_template/` convention).
- **Defect / repair:** the source value `"_templates"` would cause the Obsidian Templates plugin to show a "Templates folder does not exist" warning on first open. See "Known defects requiring repair during port" below.
- Source byte sequence (via `od -c`): `{ \n   "folder": "_templates" \n } \n` (pretty-printed, 2-space indent, trailing newline present).
- Source is CLEAN of banned terms / path leaks / meeting-slug fingerprints — the `_templates` token itself is not in the 17-token banned-term lock, nor does it match the meeting-slug regex; the repair is a semantic/UX fix, not a scrub for banned content.

### 8. `memory/.obsidian/workspace.json` (7374 bytes; 225 lines) — EXCLUDED

Enumerated here for traceability only. NOT ported. See "workspace.json exclusion rationale" below for the detailed banned-term scan and exclusion justification.

## Banned-term scan of source files

Regex: `(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])`, case-insensitive via `grep -iE` (the Story 3.1 Phase-4 F4-locked 17-token set; Story 3.2 adds zero tokens). Additional fixed-string scans: `grep -F 'gtd-life'`, `grep -F '/Users/'`, `grep -F 'Public/'`, `grep -Fi 'bobby'`. Meeting-slug regex scan: `grep -E '[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+'`. Executed on 2026-04-20 against each of the seven portable source files and, separately, against the excluded `workspace.json`.

### 17-token banned-term scan (the seven portable source files)

| # | Source file | Banned-term hits | Path-leak hits | Meeting-slug hits | `bobby` hits |
|---|-------------|------------------|----------------|-------------------|--------------|
| 1 | `app.json` | 0 | 0 | 0 | 0 |
| 2 | `appearance.json` | 0 | 0 | 0 | 0 |
| 3 | `community-plugins.json` | 0 | 0 | 0 | 0 |
| 4 | `core-plugins.json` | 0 | 0 | 0 | 0 |
| 5 | `daily-notes.json` | 0 | 0 | 0 | 0 |
| 6 | `graph.json` | 0 | 0 | 0 | 0 |
| 7 | `templates.json` | 0 | 0 | 0 | 0 |

**Summary (seven portable files):** zero hits across all seven files for all four scan categories. No occurrences of any of the 17 boundary-guarded banned tokens (`derek`, `neighbors`, `revivago`, `benji`, `flowtopic`, `gtd-life`, `gtdlife`, `wyoming`, `cheyenne`, `family`, `home`, `blog`, `wife`, `son`, `daughter`, `dog`, `personal`). No absolute filesystem paths (`/Users/`, `~/`, `Public/`), no `gtd-life` literal references, no `bobby` fixed-string matches, no meeting-title slug fingerprints matching `\d{4}-\d{2}-\d{2}-[a-z-]+`. The six byte-compatible files (`app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`) port verbatim with zero scrubs required for banned-content reasons. `templates.json` is also clean of banned content; its repair is for a different reason (dangling folder reference — see Defect below).

### Banned-content scan (excluded `workspace.json` — evidence for exclusion)

Scanned 2026-04-20. Counts are per-line-match (a single line may contain multiple tokens; counts below reflect `grep -c` line counts, which is the relevant fingerprint for exclusion justification):

| Scan | Count on `workspace.json` |
|------|---------------------------|
| 17-token boundary-guarded regex (`grep -cE`) | **19** lines match |
| `grep -Fc '/Users/'` | 0 |
| `grep -Fc 'gtd-life'` | 0 |
| `grep -Fic 'bobby'` | **7** |
| `grep -Ec '[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+'` (meeting-slug fingerprint) | **30** |

**Sample lines** (representative — first three of many):

```
                "file": "meetings/2026-04-20-bobby-derek-wkly-1-1/agenda.md",
    "meetings/2026-04-20-bobby-derek-wkly-1-1/meeting.md",
    "meetings/2026-04-20-bobby-derek-wkly-1-1/agenda.md",
```

Every match is a recent-file cache entry, open-pane reference, or last-folder-opened pointer recording Derek's own Obsidian session state. The content is not configurable or portable — it is user-local session state that Obsidian rewrites every time the app is closed. Committing it into the template would leak `derek`, `bobby`, `revivago`, `blog-ideas`, and 30 distinct meeting-title slugs into the new-employee's first vault-open experience.

## workspace.json exclusion rationale

**`workspace.json` is out-of-scope; the port emits zero bytes corresponding to this file.**

`workspace.json` is Obsidian's per-vault user-local session cache. Obsidian rewrites it on every pane change, file switch, or app close. Its contents are highly user-specific:

- **Recent-file cache:** last ~20 files opened in each pane, stored as workspace-relative paths. In Derek's source this includes `meetings/2026-04-20-bobby-derek-wkly-1-1/agenda.md`, `meetings/2026-04-20-bobby-derek-wkly-1-1/meeting.md` (and 28 other meeting-slug entries), `companies/revivago/crm-nutrafi.md`, and `blog-ideas/*.md`. None of those files exist in this template, and their path literals alone leak four distinct banned tokens (`bobby`, `derek`, `revivago`, `blog`).
- **Last-opened folder state:** serialized tree-expansion state for the file-explorer sidebar. Pins Derek's expanded directories.
- **Last-active pane layout:** window geometry, split orientation, active tab per pane. User-UI state, not portable configuration.
- **Last-used search query:** if Derek had a `global-search` pane open with a query typed, it persists here. The portable `graph.json` scrubs its own `search` field (empty) but `workspace.json` stores this separately and would re-populate it on first open.

The scans above confirm 19 banned-term regex hits, 7 `bobby` fixed-string hits, and 30 meeting-title slug fingerprint hits inside `workspace.json`. These are not "scrubable" in the sense `templates.json` is scrubable — the banned content is structurally entangled with the file's purpose (it IS the recent-file cache). The portable contract is: Obsidian will create `workspace.json` on first launch based on the new user's own activity. The template ships zero workspace cache.

**No `workspaces.json` (plural) or `workspace.json.bak` file exists in the gtd-life source.** The only workspace-related file is the single `workspace.json` excluded above.

The harness's `check_task3` forbidden-file block enforces this by asserting `[[ ! -f memory/.obsidian/workspace.json ]]` and by iterating the `*.bak`, `*.log`, `*.tmp`, `.DS_Store` globs with `find -name` and failing on any match. The cross-file scrub's `check_task4` independently asserts zero occurrences of the meeting-slug fingerprint regex across the seven ported JSON files, which would trip if any `workspace.json` content had leaked into a sibling file.

## Known defects requiring repair during port

One defect MUST be repaired (not copied) during the Story 3.2 port:

### Defect #1 — `templates.json` `folder: "_templates"` dangling folder reference (SCRUB / SEMANTIC REPAIR)

**Source bytes** (29 bytes, 3 lines, trailing newline present):

```
{
  "folder": "_templates"
}
```

**Problem:** the `folder` value `"_templates"` points at `memory/_templates/` — a directory that does NOT exist in this template. Story 3.1 explicitly declined to create the alternate single-file `_templates/` tree in favor of the per-directory `_template.md` / `_template/` convention (see Story 3.1 baseline audit, "Out-of-scope directories", row `~/Public/gtd-life/memory/_templates/`). If the Templates plugin is pointed at a non-existent folder on first open, Obsidian shows a user-facing warning ("Templates folder does not exist") and the Insert Template command fails with no candidates. This is a confusing first-launch experience.

**Required port output:** the REPAIRED content is the single-key JSON object `{"folder": ""}` with a trailing newline. Either the pretty-printed form (`{\n  "folder": ""\n}\n`, 4-space or 2-space indent acceptable) or the compact form (`{"folder": ""}\n`) is acceptable as long as it parses as valid JSON. Setting the value to the EMPTY STRING `""` disables the folder reference without disabling the Templates plugin itself (the plugin remains `true` in `core-plugins.json`). The user may later point the plugin at a folder they create (e.g. `memory/_templates/`) or use the per-directory `_template.md` convention Story 3.1 established.

**Verification contract:** the emitted `memory/.obsidian/templates.json` MUST contain ZERO occurrences of the literal string `_templates` (AC8 cross-check; `grep -Fq '_templates'` must return non-zero exit / empty output). This repair is analogous to Story 3.1's Defect #1 (malformed YAML frontmatter in `appreciations/_template.md`), #2 (banned `context:` value in `inbox/_template.md`), and #3 (banned `context:` inline comment in `meeting.md`): the source is instructive but not authoritative where it encodes a bug or a reference to out-of-scope downstream content.

## Out-of-scope .obsidian subdirectories and paths

The following Obsidian-adjacent directories and paths are explicitly OUT OF SCOPE for Story 3.2. The port MUST NOT create matching directories or files in the assistants-template repo as part of this story:

| Path | Reason OUT OF SCOPE for Story 3.2 |
|------|-----------------------------------|
| `memory/.obsidian/plugins/` | Community-plugin binaries (`main.js`, `manifest.json`, CSS blobs). Never bundled in a template — each plugin has its own licensing, update cadence, and installation model. Users install community plugins from the Obsidian plugin marketplace after cloning. The gtd-life source does NOT have a `plugins/` subdirectory either, so there is nothing to port; the template ships `community-plugins.json: []` with no accompanying binaries. |
| `memory/.obsidian/workspace.json` | User-local vault cache (recent files, pane layout, search state). Excluded — see "workspace.json exclusion rationale" above. Obsidian will create a fresh file on first launch. |
| `memory/.obsidian/workspaces.json` | Plural form — multi-workspace profile state. Does not exist in the gtd-life source; does not exist in the port. |
| `memory/.obsidian/workspace.json.bak` / `*.bak` / `*.log` / `*.tmp` / `.DS_Store` | Obsidian backup / log / tmp files and macOS metadata. User-local noise. Never committed. |
| `memory/daily/` | Daily-notes directory. Obsidian creates this lazily on first daily-note action. Story 3.2 does NOT pre-create it (AC15). The `daily-notes.json` `folder: "daily"` value is a relative-to-vault-root pointer; the directory is created on-demand by the Daily Notes plugin. |
| `memory/_templates/` | Story 3.1 explicitly declined this alternate layout. The `templates.json` REPAIR scrubs the source's `"_templates"` folder reference specifically because this directory will not exist in the template. |
| `.obsidian/` at repo root | Wrong location. Obsidian treats the directory containing `.obsidian/` as the vault root; placing it at repo root would make the WHOLE repository (`_bmad-output/`, `.cursor/`, `scripts/`, etc.) a vault. The correct location is `memory/.obsidian/` so the vault root is `memory/`. |
| `~/Public/gtd-life/memory/.obsidian/` (and any parent) | Read-only source. Not referenced by any ported file (confirmed via per-file `grep -F 'gtd-life'` → 0 hits across the seven portable files). |

No Story 3.2 target file or directory should reference any of the above paths.

## Mapping: source path → target path (or EXCLUDED)

| # | Source path (read-only reference) | Target path (ported into assistants-template) | Port mode |
|---|-----------------------------------|-----------------------------------------------|-----------|
| 1 | `~/Public/gtd-life/memory/.obsidian/app.json` | `memory/.obsidian/app.json` | port-verbatim + add trailing newline |
| 2 | `~/Public/gtd-life/memory/.obsidian/appearance.json` | `memory/.obsidian/appearance.json` | port-verbatim (`{}`) + add trailing newline |
| 3 | `~/Public/gtd-life/memory/.obsidian/community-plugins.json` | `memory/.obsidian/community-plugins.json` | port-verbatim (`[]\n`; already has trailing newline) |
| 4 | `~/Public/gtd-life/memory/.obsidian/core-plugins.json` | `memory/.obsidian/core-plugins.json` | port-verbatim + add trailing newline |
| 5 | `~/Public/gtd-life/memory/.obsidian/daily-notes.json` | `memory/.obsidian/daily-notes.json` | port-verbatim (already has trailing newline) |
| 6 | `~/Public/gtd-life/memory/.obsidian/graph.json` | `memory/.obsidian/graph.json` | port-verbatim + add trailing newline |
| 7 | `~/Public/gtd-life/memory/.obsidian/templates.json` | `memory/.obsidian/templates.json` | REPAIR Defect #1 (`"folder": "_templates"` → `"folder": ""`) |
| 8 | `~/Public/gtd-life/memory/.obsidian/workspace.json` | — | **EXCLUDED** (zero bytes emitted; user-local vault cache; 19 banned-term hits, 7 `bobby` hits, 30 meeting-slug fingerprint hits) |
| 9 | `~/Public/gtd-life/memory/.obsidian/plugins/` (does not exist in source) | — | **OUT OF SCOPE** (no community-plugin binaries bundled) |

All seven target paths are new files (none exist in `assistants-template` yet — confirmed by `find memory -type d -name '.obsidian'` at audit time returning empty). No file-replacement, no merge, no pre-existing content collision. The target directory `memory/.obsidian/` itself is new and must be created by Task 3a (`mkdir -p memory/.obsidian`). UTF-8 encoding and LF line endings are required per AC1 / Dev Notes "Architectural constraints". Each emitted file ends with a single `\n` for POSIX-tool friendliness.

---

End of Story 3.2 Baseline Audit. Task 2 (canonical blueprint) consumes the per-file JSON structure + key map above and the one known defect repair. Tasks 3a / 3b / 3c consume the source → target mapping. Task 4 (harness) consumes the workspace.json exclusion fingerprints (meeting-slug regex, `bobby` fixed-string) as cross-file-scrub probes in `check_task4`.
