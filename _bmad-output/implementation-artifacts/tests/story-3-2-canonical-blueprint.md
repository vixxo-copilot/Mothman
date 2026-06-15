# Story 3.2 Canonical Blueprint

Locked design for the seven portable `.obsidian/` config files ported in Tasks 3a–3c. Every lock in this document maps to one or more ACs in Story 3.2 and is enforced by the Task 4 validation harness (`story-3-2-obsidian-config-validation.sh`). Follows the Story 3.1 `canonical-blueprint.md` precedent.

This document is a pure specification. It defines the exact JSON top-level structure, key inventories (in canonical gtd-life source order), value types, literal-value locks, the one known REPAIR (`templates.json` `"folder": "_templates"` → `""`), and the forbidden-file / banned-term / meeting-slug lock sets. It does not contain the full file bodies — those bytes are authored verbatim-with-REPAIR from the gtd-life source in Tasks 3a–3c, constrained by the locks below.

Conventions used throughout:

- **Top-level structure lock:** each file declares whether its top-level JSON value is an OBJECT (`{…}`) or an ARRAY (`[…]`). No variation permitted.
- **Key-order lock:** for objects, keys appear in the listed order (matching the gtd-life source byte-order as captured 2026-04-20). No reordering, no extra keys, no missing keys.
- **Value-type lock:** every key's value type (string / boolean / number / array / object / null) is locked to the listed type. Numeric precision is preserved verbatim from source (e.g. `centerStrength: 0.518713248970312`).
- **Literal-value lock:** where a specific literal value is required (e.g. `defaultViewMode: "source"`, `folder: "daily"`, `format: "YYYY-MM-DD"`, and the REPAIRED `templates.json` `folder: ""`), the exact byte content of the value is locked.
- **Trailing newline:** every emitted JSON file ends with a single `\n`. LF only, no CRLF. (The gtd-life sources are inconsistent on this — some already end with `\n`, some do not — the port normalizes all seven to end with `\n` for POSIX-tool friendliness.)
- **Encoding:** every emitted JSON file is valid UTF-8.
- **No comments:** JSON has no comment syntax. Every byte in every file is either whitespace, a structural token (`{` `}` `[` `]` `:` `,`), a quoted key, or a quoted/numeric/boolean/null value.

---

## Blueprint — `memory/.obsidian/app.json`

Maps to AC1, AC2, AC10.

### Top-level structure

JSON OBJECT (`{…}`). Not an array.

### Key inventory (3 keys, canonical gtd-life source order)

| # | Key | Value type | Literal value |
| --- | --- | --- | --- |
| 1 | `strictLineBreaks` | boolean | `false` |
| 2 | `showFrontmatter` | boolean | `true` |
| 3 | `defaultViewMode` | string | `"source"` |

### Byte budget

- gtd-life source: 89 bytes (measured 2026-04-20, `wc -c`).
- Port admits minor whitespace variation; harness upper-bound assertion: `≤ 200 bytes`.

### Port method

Verbatim from `~/Public/gtd-life/memory/.obsidian/app.json`. Source is already clean (zero banned tokens, zero path leaks, zero meeting-slug fingerprints). No REPAIR required.

### Harness probes (`check_task3`)

- `grep -Fq '"strictLineBreaks"'`
- `grep -Fq '"showFrontmatter"'`
- `grep -Fq '"defaultViewMode"'`
- `grep -Fq '"defaultViewMode": "source"'`
- Structural sanity: first non-whitespace char is `{`; last non-whitespace char is `}`.
- `grep -c '":' app.json` equals `3`.

---

## Blueprint — `memory/.obsidian/appearance.json`

Maps to AC1, AC3, AC10.

### Top-level structure

JSON OBJECT (`{…}`). Not an array.

### Key inventory (0 keys)

The object is empty. Literal file content is the two bytes `{}` optionally followed by a single trailing newline (`\n`).

### Byte budget

- gtd-life source: 2 bytes (literal `{}`, no trailing newline).
- Port normalizes to 3 bytes (`{}\n`).
- Harness upper-bound assertion: `≤ 10 bytes` (admits whitespace variation without admitting content drift).

### Port method

Verbatim from source (empty object). Normalize trailing newline.

### Harness probes (`check_task3`)

- `tr -d '[:space:]' < appearance.json` equals the literal `{}`.
- Structural sanity: first non-whitespace char is `{`; last non-whitespace char is `}`.
- No keys permitted: `grep -c '":' appearance.json` equals `0`.

---

## Blueprint — `memory/.obsidian/community-plugins.json`

Maps to AC1, AC4, AC10.

### Top-level structure

JSON ARRAY (`[…]`). Not an object.

### Element inventory (0 elements)

The array is empty. Literal file content is the two bytes `[]` followed by a single trailing newline (`\n`).

### Byte budget

- gtd-life source: 3 bytes (`[]\n`).
- Port: identical (3 bytes).
- Harness upper-bound assertion: `≤ 10 bytes`.

### Companion directory lock

- `memory/.obsidian/plugins/` MUST NOT exist. Community-plugin binaries are never bundled into a template repo.

### Port method

Verbatim from source (empty array).

### Harness probes (`check_task3`)

- `tr -d '[:space:]' < community-plugins.json` equals the literal `[]`.
- Structural sanity: first non-whitespace char is `[`; last non-whitespace char is `]`.
- `[[ ! -d "${OBSIDIAN_DIR}/plugins" ]]`.

---

## Blueprint — `memory/.obsidian/core-plugins.json`

Maps to AC1, AC5, AC10.

### Top-level structure

JSON OBJECT (`{…}`). Not an array.

### Key inventory (31 keys, canonical gtd-life source order)

Each key is an Obsidian core-plugin ID; each value is a boolean. The gtd-life source ordering (captured 2026-04-20) is preserved byte-compatible. Total: 16 `true` + 15 `false` = 31 keys.

| # | Key | Value type | Literal value |
| --- | --- | --- | --- |
| 1 | `file-explorer` | boolean | `true` |
| 2 | `global-search` | boolean | `true` |
| 3 | `switcher` | boolean | `true` |
| 4 | `graph` | boolean | `true` |
| 5 | `backlink` | boolean | `true` |
| 6 | `outgoing-link` | boolean | `true` |
| 7 | `tag-pane` | boolean | `true` |
| 8 | `page-preview` | boolean | `true` |
| 9 | `daily-notes` | boolean | `true` |
| 10 | `templates` | boolean | `true` |
| 11 | `note-composer` | boolean | `false` |
| 12 | `command-palette` | boolean | `false` |
| 13 | `slash-command` | boolean | `false` |
| 14 | `editor-status` | boolean | `false` |
| 15 | `markdown-importer` | boolean | `true` |
| 16 | `zk-prefixer` | boolean | `false` |
| 17 | `random-note` | boolean | `false` |
| 18 | `outline` | boolean | `true` |
| 19 | `word-count` | boolean | `false` |
| 20 | `slides` | boolean | `false` |
| 21 | `audio-recorder` | boolean | `false` |
| 22 | `workspaces` | boolean | `false` |
| 23 | `file-recovery` | boolean | `false` |
| 24 | `publish` | boolean | `false` |
| 25 | `sync` | boolean | `false` |
| 26 | `canvas` | boolean | `true` |
| 27 | `footnotes` | boolean | `false` |
| 28 | `properties` | boolean | `true` |
| 29 | `bookmarks` | boolean | `true` |
| 30 | `bases` | boolean | `true` |
| 31 | `webviewer` | boolean | `false` |

### Enabled-set summary (16 plugins with value `true`)

`file-explorer`, `global-search`, `switcher`, `graph`, `backlink`, `outgoing-link`, `tag-pane`, `page-preview`, `daily-notes`, `templates`, `markdown-importer`, `outline`, `canvas`, `properties`, `bookmarks`, `bases`.

### Disabled-set summary (15 plugins with value `false`)

`note-composer`, `command-palette`, `slash-command`, `editor-status`, `zk-prefixer`, `random-note`, `word-count`, `slides`, `audio-recorder`, `workspaces`, `file-recovery`, `publish`, `sync`, `footnotes`, `webviewer`.

### Byte budget

- gtd-life source: 701 bytes.
- Port: byte-compatible with source.
- Harness upper-bound assertion: `≤ 1024 bytes`.

### Port method

Verbatim from source (31 keys, boolean values, canonical order). No REPAIR required.

### Harness probes (`check_task3`)

- For each of the 16 enabled plugins: `grep -Fq '"<plugin>": true'`.
- For each of the 15 disabled plugins: `grep -Fq '"<plugin>": false'`.
- Key-count probe: `grep -c '":' core-plugins.json` equals `31`.
- Structural sanity: first non-whitespace `{`; last non-whitespace `}`.
- Allowlist: no key outside the 31 above may appear. Enforced via the key-count probe combined with the per-key grep of every canonical name.

---

## Blueprint — `memory/.obsidian/daily-notes.json`

Maps to AC1, AC6, AC10.

### Top-level structure

JSON OBJECT (`{…}`). Not an array.

### Key inventory (3 keys, canonical gtd-life source order)

| # | Key | Value type | Literal value |
| --- | --- | --- | --- |
| 1 | `folder` | string | `"daily"` |
| 2 | `format` | string | `"YYYY-MM-DD"` |
| 3 | `template` | string | `""` (empty string) |

### Literal-value locks

- `folder` value is the relative-to-vault-root string `"daily"`. NOT an absolute filesystem path. NOT `/Users/…`, NOT `~/…`, NOT `Public/…`, NOT `gtd-life/…`.
- `format` value is the strftime-style date token `"YYYY-MM-DD"`.
- `template` value is the EMPTY STRING `""`. No daily-note template is wired. Daily notes open blank on first launch.

### Byte budget

- gtd-life source: 68 bytes.
- Port: byte-compatible with source.
- Harness upper-bound assertion: `≤ 200 bytes`.

### Port method

Verbatim from source. No REPAIR required.

### Harness probes (`check_task3`)

- `grep -Fq '"folder": "daily"'`
- `grep -Fq '"format": "YYYY-MM-DD"'`
- `grep -Fq '"template": ""'`
- Absolute-path absence: `grep -Fq '/Users/'`, `grep -Fq '~/'`, `grep -Fq 'Public/'`, `grep -Fq 'gtd-life'` MUST each return zero.
- `grep -c '":' daily-notes.json` equals `3`.

---

## Blueprint — `memory/.obsidian/graph.json`

Maps to AC1, AC7, AC10.

### Top-level structure

JSON OBJECT (`{…}`). Not an array.

### Key inventory (20 keys, canonical gtd-life source order)

AC7 is the ground truth: 20 keys, listed below in canonical source order, with `≤ 1024-byte` upper-bound budget (source 493 bytes).

| # | Key | Value type | Literal value |
| --- | --- | --- | --- |
| 1 | `collapse-filter` | boolean | `true` |
| 2 | `search` | string | `""` (empty — no user query) |
| 3 | `showTags` | boolean | `false` |
| 4 | `showAttachments` | boolean | `false` |
| 5 | `hideUnresolved` | boolean | `false` |
| 6 | `showOrphans` | boolean | `true` |
| 7 | `collapse-color-groups` | boolean | `true` |
| 8 | `colorGroups` | array | `[]` (empty — no user groups) |
| 9 | `collapse-display` | boolean | `true` |
| 10 | `showArrow` | boolean | `false` |
| 11 | `textFadeMultiplier` | number | `0` |
| 12 | `nodeSizeMultiplier` | number | `1` |
| 13 | `lineSizeMultiplier` | number | `1` |
| 14 | `collapse-forces` | boolean | `true` |
| 15 | `centerStrength` | number | `0.518713248970312` |
| 16 | `repelStrength` | number | `10` |
| 17 | `linkStrength` | number | `1` |
| 18 | `linkDistance` | number | `250` |
| 19 | `scale` | number | `1` |
| 20 | `close` | boolean | `true` |

### Literal-value locks (sanity)

- `search` value is the EMPTY STRING `""`. AC7 explicitly asserts this: no carried-over user query (`"tmo"` or otherwise). The gtd-life source is already clean; the port asserts cleanliness.
- `colorGroups` value is the EMPTY ARRAY `[]`. No Derek-authored color-group definitions carry through.
- Numeric values (e.g. `centerStrength: 0.518713248970312`) are preserved verbatim from source. The assertion is shape-only; exact numeric precision is a byte-compat convenience rather than a semantic lock.

### Byte budget

- gtd-life source: 493 bytes.
- Port: byte-compatible with source.
- Harness upper-bound assertion: `≤ 1024 bytes`.

### Port method

Verbatim from source. No REPAIR required — source is already clean (empty `search`, empty `colorGroups`, no Derek-specific extensions).

### Harness probes (`check_task3`)

- For each of the 20 keys: `grep -Fq '"<key>":'`.
- `grep -Fq '"search": ""'` (AC7 scrub assertion).
- `grep -Fq '"colorGroups": []'` (AC7 scrub assertion).
- Structural sanity: first non-whitespace `{`; last non-whitespace `}`.
- `grep -c '":' graph.json` equals `20`.

---

## Blueprint — `memory/.obsidian/templates.json` (REPAIRED shape)

Maps to AC1, AC8, AC10. This file REPAIRS a dangling folder reference in the gtd-life source; the port MUST NOT copy the source value verbatim.

### Top-level structure

JSON OBJECT (`{…}`). Not an array.

### Key inventory (1 key)

| # | Key | Value type | Literal value |
| --- | --- | --- | --- |
| 1 | `folder` | string | `""` (REPAIRED — empty string) |

### REPAIR spec

- **Source value:** `"_templates"` (gtd-life source points at `memory/_templates/`).
- **Port value:** `""` (empty string).
- **Why the REPAIR:** the gtd-life source references `memory/_templates/`, a directory that Story 3.1 explicitly declined to create in favor of the per-directory `_template.md` convention. Shipping the Templates plugin pointed at a non-existent folder produces a confusing "Templates folder does not exist" warning on the user's first Obsidian open.
- **Effect of the REPAIR:** the Templates plugin remains ENABLED (`core-plugins.json` `"templates": true`) but has no configured source folder. The user may:
  - Point the plugin at a folder they create themselves (e.g. `memory/_templates/`) via Obsidian's Settings → Templates pane, or
  - Leave the folder blank and use the Story 3.1 per-directory `_template.md` convention directly.
- **Classification:** this is the ONE KNOWN REPAIR for Story 3.2, analogous to Story 3.1's Defect #1–#3 repairs for `appreciations/_template.md`. It is documented in the baseline audit (Task 1) and codified in AC8.

### Byte budget

- gtd-life source: 29 bytes (pretty-printed `{\n  "folder": "_templates"\n}\n`).
- Port: approximately 19 bytes pretty-printed (`{\n  "folder": ""\n}\n`) or 15 bytes compact (`{"folder":""}\n`). Either form is acceptable.
- Harness upper-bound assertion: `≤ 64 bytes`.

### Forbidden-substring lock

- The emitted file MUST NOT contain the literal string `_templates` anywhere. A `grep -F '_templates' memory/.obsidian/templates.json` MUST return zero matches. This is the REPAIR-verification assertion in `check_task3` and `check_task4`.

### Port method

Author fresh (do NOT copy from source). Emit either the pretty-printed form matching the sibling Obsidian JSON files' indentation style, or the compact form. The harness is agnostic between the two, enforcing only the key/value/structure locks.

### Harness probes (`check_task3` + `check_task4`)

- `grep -Fq '"folder": ""'` (REPAIRED value present).
- `grep -Fq '_templates' templates.json` MUST return zero (REPAIRED value — source string scrubbed).
- `grep -c '":' templates.json` equals `1`.
- Structural sanity: first non-whitespace `{`; last non-whitespace `}`.

---

## Forbidden-file lock

The following files MUST NOT exist anywhere under `memory/.obsidian/`. Enforced by `check_task3` forbidden-file block.

### Forbidden filenames (exact match)

- `workspace.json` — user-local vault cache (open-pane layout, recent-file list, last-search query). Leaks Derek / Bobby / revivago / blog-ideas references. AC9 asserts its absence.
- `workspace.json.bak` — backup form of the above.
- `workspaces.json` — plural variant used by the disabled `workspaces` core plugin.

### Forbidden glob patterns

- `*.bak` — any editor / Obsidian backup.
- `*.json.bak` — more-specific backup pattern.
- `*.log` — any log file.
- `*.tmp` — any scratch / temp file.
- `.DS_Store` — macOS Finder metadata.
- `Icon\r` — macOS custom-icon resource-fork sentinel (carriage-return filename).

### Forbidden subdirectories

- `memory/.obsidian/plugins/` — community-plugin binaries / `main.js` / `manifest.json` blobs. NEVER bundled in a template.

### Directory-count lock

`ls -A memory/.obsidian/ | wc -l` MUST equal `7`. Exactly seven entries, all of them regular JSON files, none hidden, none directories, none resource-fork sentinels.

---

## Banned-term lock

Inherited verbatim from Story 3.1 Phase-4 F4 post-merge state. Story 3.2 adds ZERO new tokens to the 17-token regex set. Boundary-guarded POSIX-ERE regex, case-insensitive via `grep -iE`.

### 17-token regex set (carried forward from Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1)

```
derek
neighbors
revivago
benji
flowtopic
gtd-life
gtdlife
wyoming
cheyenne
family
home
blog
wife
son
daughter
dog
personal
```

### Composite boundary-guarded regex (harness constant)

```
(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])
```

Invoked as `grep -iE` for case-insensitivity. Tested in `regex_self_probe()` with both a carried-forward token (`derek` → positive, `derekson` → boundary-rejected) and the Story-3.1-added token (`personal` → positive, `personally` → boundary-rejected).

### Path-reference fixed-string lock (defence-in-depth beyond the regex)

The harness additionally runs fixed-string (`grep -F`) scans across each of the seven ported files for:

- `gtd-life` — source-repo reference (also caught by the regex; fixed-string is belt-and-suspenders).
- `~/Public/gtd-life` — literal tilde-prefixed filesystem path from the operator's machine.
- `Public/gtd-life` — tilde-stripped variant.
- `/Users/` — any absolute macOS home-directory path.

Any match of any of these literal strings FAILS the cross-file scrub gate (`check_task4`).

### Story-3.2-specific fixed-string backstop: `bobby`

`bobby` is Derek's colleague name. It appears in the excluded `workspace.json` source through recent-file cache entries (e.g. `meetings/2026-04-20-bobby-derek-wkly-1-1/agenda.md`). Although `workspace.json` is not ported, the port asserts a fixed-string `grep -Fiq 'bobby'` scan across each of the seven ported files as a defence-in-depth backstop — any match indicates that workspace-cache content has leaked into a sibling file.

**Why fixed-string and NOT part of the 17-token regex:** `bobby` is a common first name. Adding it to the main banned-term regex would trigger false positives in future unrelated content (e.g. `bobbypin` in a reference note). Within the narrow scope of `.obsidian/` config files — none of which legitimately carry first-name content — a fixed-string backstop is appropriate without generalizing the token to the full vault.

---

## Meeting-slug fingerprint lock

The `workspace.json` source file carries recent-file references that match the following shape:

- `2026-04-20-bobby-derek-wkly-1-1/agenda.md`
- `2026-03-17-some-meeting-slug/notes.md`

These are meeting-title slugs: ISO-date-prefix + lowercase kebab-case tail.

### Regex (harness constant `MEETING_SLUG_REGEX`)

```
[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+
```

The harness runs `grep -Eq "${MEETING_SLUG_REGEX}"` across each of the seven ported files. Any match FAILS `check_task4` — its presence would indicate that `workspace.json` content leaked into a sibling file.

### `regex_self_probe()` coverage

- Positive: `2026-04-20-bobby-derek-wkly-1-1` matches.
- Negative: `foo-bar-baz` does NOT match (no ISO-date prefix).

### Why the `YYYY-MM-DD` literal in `daily-notes.json` does NOT trigger this regex

The literal `YYYY-MM-DD` inside `daily-notes.json` (`"format": "YYYY-MM-DD"`) is alphabetic — it contains no digits — so it cannot match the `[0-9]{4}-[0-9]{2}-[0-9]{2}` prefix. No false positive.

---

## Out-of-scope lock (what Story 3.2 does NOT emit)

Explicit exclusion list. Any file or directory here FAILS the scope lock if produced by Story 3.2.

### File-system paths explicitly out of scope

- `memory/.obsidian/workspace.json` — user-local vault cache. Excluded per AC9.
- `memory/.obsidian/workspace.json.bak` / `workspaces.json` — workspace-cache backup variants.
- `memory/.obsidian/plugins/` — community-plugin binary directory.
- `memory/.obsidian/snippets/` — user-local CSS snippets.
- `memory/.obsidian/themes/` — user-local theme bundles.
- `memory/daily/` — Obsidian creates this lazily on first daily note; Story 3.2 does NOT pre-create.
- `memory/_templates/` — Story 3.1 explicitly declined this layout; Story 3.2 honours that decision via the `templates.json` REPAIR (`folder: ""`).
- `memory/me/` (and `memory/me/identity.md`, `memory/me/preferences.md`) — Story 3.3 scope.
- `memory/companies/`, `memory/blog-ideas/`, `memory/vixxo/` — not in any current Epic 3 story; never ported.
- `.obsidian/` at repo root — WRONG location. The Obsidian vault root is `memory/`, so the config must live at `memory/.obsidian/` only.

### Files / directories explicitly preserved unchanged by Story 3.2 (AC11 invariance)

- `memory/.gitkeep` (0 bytes, from Story 1.1) — byte-for-byte stable.
- The nine Story 3.1 template files under `memory/`:
  - `memory/meetings/_template/meeting.md`
  - `memory/meetings/_template/agenda.md`
  - `memory/meetings/_template/prep.md`
  - `memory/meetings/_template/transcript.md`
  - `memory/people/_template.md`
  - `memory/decisions/_template.md`
  - `memory/reference/_template.md`
  - `memory/inbox/_template.md`
  - `memory/appreciations/_template.md`
- No new `.gitkeep` / `.keep` / `empty` / `placeholder` sentinel files under `memory/.obsidian/` (the seven JSON files are themselves git-trackable content; sentinels are redundant).

---

## Cross-AC coverage map

| AC | Lock |
| --- | --- |
| AC1 | Seven per-file blueprints + `## Forbidden-file lock` (no `workspace.json`, no `*.bak/*.log`, no `plugins/` subdir) + directory-count lock (`ls -A memory/.obsidian/ | wc -l == 7`) |
| AC2 | `memory/.obsidian/app.json` blueprint (3 keys: `strictLineBreaks` / `showFrontmatter` / `defaultViewMode`) |
| AC3 | `memory/.obsidian/appearance.json` blueprint (empty object `{}`) |
| AC4 | `memory/.obsidian/community-plugins.json` blueprint (empty array `[]`) + `plugins/` subdirectory absence |
| AC5 | `memory/.obsidian/core-plugins.json` blueprint (31-key object; 16 `true` + 15 `false`) |
| AC6 | `memory/.obsidian/daily-notes.json` blueprint (3 keys: `folder: "daily"` / `format: "YYYY-MM-DD"` / `template: ""`) + absolute-path absence |
| AC7 | `memory/.obsidian/graph.json` blueprint (20 keys, empirical count — AC7-prose 17 is an illustrative excerpt) + empty `search` + empty `colorGroups` |
| AC8 | `memory/.obsidian/templates.json` blueprint (REPAIRED — `folder: ""` not `"_templates"`) + `_templates` forbidden-substring scrub |
| AC9 | `## Forbidden-file lock` section (`workspace.json` / `*.bak` / `.DS_Store` absences) + `## Meeting-slug fingerprint lock` + `bobby` fixed-string backstop |
| AC10 | `## Banned-term lock` section (17-token regex + path-reference fixed-string + `bobby` backstop) |
| AC11 | `## Out-of-scope lock` section (Story 3.1 template invariance + `memory/.gitkeep` 0-byte stability + no new sentinels) |
| AC12–AC15 | N/A at blueprint level; handled by Task 4 harness, Task 5 regression, Task 6 handoff, Task 7 sprint-status. The blueprint is consumed by `check_task2` (existence + required section headers) and `check_task3` / `check_task4` (shape + scrub) gates. |
