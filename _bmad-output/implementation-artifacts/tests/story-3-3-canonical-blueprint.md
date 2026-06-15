# Story 3.3 Canonical Blueprint

Locked design for the two authored markdown files under `memory/me/` produced by Tasks 3a–3b (`identity.md` and `preferences.md`). Every lock in this document maps to one or more ACs in Story 3.3 and is enforced by the Task 4 validation harness (`story-3-3-identity-preferences-validation.sh`). Follows the Story 3.1 and Story 3.2 `canonical-blueprint.md` precedent.

This document is a pure specification. It defines the exact frontmatter key-set in canonical order, the exact body heading sequence, the placeholder vocabulary allowlist, the byte-budget bounds, and the banned-term / forbidden-form / Derek-specific fixed-string locks. It does not contain the full body prose of either file — that prose is authored fresh from scaffold in Tasks 3a / 3b (NOT ported verbatim from the gtd-life source, distinct from Story 3.2's port method), constrained by the locks below.

Conventions used throughout:

- **Frontmatter key lock:** the listed keys appear in the listed canonical order inside the YAML frontmatter block opened by `---` on line 1 and closed by `---` on a subsequent line. No extra keys. No reordering. No missing keys.
- **Literal-value lock:** where a specific literal value is required (`type: identity`, `type: preferences`, `scope: work`, the five `{{employee_*}}` placeholder scalars, `tags: [identity, work]`, `tags: [preferences, work]`), the exact byte content of the value is locked.
- **Heading lock:** each listed H1 / H2 heading appears verbatim as a standalone body line, in the listed order. No reordering.
- **Placeholder lock:** only the five identity-placeholder tokens in the `## Placeholder vocabulary lock` section below may appear in `identity.md`. `preferences.md` contains ZERO `{{...}}` tokens of any kind.
- **Banned-term lock:** no token in the 17-token inherited Stories 3.1 / 3.2 banned-term regex set may appear in either file. Additionally, no Derek-specific fixed-string in the defence-in-depth scrub set may appear.
- **Byte budget:** every file satisfies `200 ≤ wc -c ≤ 2048` bytes (AC8).
- **Trailing newline:** every file ends with a single `\n` (last byte `0x0a`). LF only, no CRLF.
- **Encoding:** every file is valid UTF-8.
- **Port method:** REBUILD FROM SCAFFOLD — the gtd-life source `me/identity.md` (2.5KB Derek biography) and `me/preferences.md` (2.9KB Derek preferences) are read for "what shape an identity / preferences file can have" only. Zero Derek sentences carry through. Distinct from Story 3.2's verbatim-with-REPAIR port method.

---

## Blueprint — `memory/me/identity.md`

Maps to AC1, AC2, AC3, AC6, AC7, AC8.

### Frontmatter keys (in canonical order, 10 keys total)

| # | Key | Value type | Literal value or placeholder |
| --- | --- | --- | --- |
| 1 | `type` | string | `identity` |
| 2 | `scope` | string | `work` |
| 3 | `name` | string (quoted) | `"{{employee_name}}"` |
| 4 | `role` | string (quoted) | `"{{employee_role}}"` |
| 5 | `department` | string (quoted) | `"{{employee_department}}"` |
| 6 | `manager` | string (quoted) | `"{{employee_manager}}"` |
| 7 | `email` | string (quoted) | `"{{employee_email}}"` |
| 8 | `created` | string | `YYYY-MM-DD` (literal date-shape token) |
| 9 | `updated` | string | `YYYY-MM-DD` (literal date-shape token) |
| 10 | `tags` | inline array | `[identity, work]` |

### Frontmatter literal-value locks

- `type` value MUST be the literal bare string `identity` (no quotes, no variation).
- `scope` value MUST be the literal bare string `work`. NOT `personal`, NOT `vixxo`, NOT `mixed` — matches NFR7 and architecture.md work-only constraint.
- `name` / `role` / `department` / `manager` / `email` values MUST each be the corresponding `{{employee_*}}` placeholder wrapped in double-quoted YAML scalar form (`"…"`).
- `created` and `updated` values MUST be the literal date-shape token `YYYY-MM-DD` (Epic 5 Story 5.2 wizard rewrites these to the current ISO-8601 date).
- `tags` value MUST be the YAML inline array `[identity, work]`. Token `work` is present; token `personal` is NOT present. Equivalent block-style YAML arrays are NOT permitted (inline-only) — ensures the `grep -Fq 'tags: [identity, work]'` probe is sufficient.

### Body headings (in order, 8 headings total)

1. `# Identity` (H1, literal — no placeholder)
2. `## Name` (H2)
3. `## Role` (H2)
4. `## Department` (H2)
5. `## Manager` (H2)
6. `## Email` (H2)
7. `## Work Scope` (H2)
8. `## Key References` (H2)

### Required body elements

- Each of the five identity-placeholder tokens (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}`) MUST appear at least once in the body (AC3). Natural placement is under the corresponding H2 section (`## Name` → `{{employee_name}}`, etc.), but the harness only verifies each token appears somewhere in the body at least once.
- The `## Work Scope` section MUST contain the literal substring `work context only` (AC3 — matches the Story 2.1 `.cursor/rules/agent-identity.mdc` scope declaration).
- The `## Work Scope` section MUST contain a reference to `.cursor/rules/agent-identity.mdc` as the authoritative scope source (single source of truth — avoids restating scope block in three places).
- The `## Key References` section MUST list at minimum: `.cursor/rules/agent-identity.mdc`, `agents/personas/work.md`, `memory/me/preferences.md` (AC3). Recommended extended list also includes `AGENTS.md`, `CLAUDE.md`, `.cursorrules` (matches the agent-identity rule's `## Key References` block — single source of truth).

### Allowed placeholders in this file

- `{{employee_name}}`
- `{{employee_role}}`
- `{{employee_department}}`
- `{{employee_manager}}`
- `{{employee_email}}`

Plus the literal token `YYYY-MM-DD` in frontmatter only (not a `{{...}}` placeholder; not extracted by the placeholder-allowlist probe).

### Byte budget

- Lower bound: 200 bytes (enforces frontmatter + seven H2 headings + minimal body prose are actually authored).
- Upper bound: 2048 bytes (guards against ported Derek content regression; the gtd-life source `me/identity.md` is ~2500 bytes).
- Harness assertion: `200 ≤ wc -c < identity.md ≤ 2048`.

### Harness probes (`check_task3` + `check_task4`)

- `[[ -f memory/me/identity.md ]]` (existence).
- `[[ -s memory/me/identity.md ]]` (non-empty).
- `head -c 3 memory/me/identity.md` equals `---` (frontmatter opens on line 1).
- `tail -c 1 memory/me/identity.md | od -An -tx1 | tr -d '[:space:]'` equals `0a` (trailing newline).
- `grep -c $'\r' memory/me/identity.md` equals `0` (LF-only, no CRLF).
- Frontmatter block extracted via `awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}'`; within the extracted block:
  - Each of the 10 canonical-order keys appears on its own line anchored `^<key>:`.
  - `grep -Fq 'type: identity'` matches.
  - `grep -Fq 'scope: work'` matches.
  - `grep -Fq 'tags: [identity, work]'` matches.
  - Each of the five `{{employee_*}}` tokens appears on its corresponding key line (`name:` line contains `{{employee_name}}`, etc.).
- Each of the eight body headings (`# Identity`, `## Name`, `## Role`, `## Department`, `## Manager`, `## Email`, `## Work Scope`, `## Key References`) appears as a standalone full line via `grep -Fxq`.
- `grep -Fq 'work context only'` matches (in body).
- `grep -Fq '.cursor/rules/agent-identity.mdc'` matches (in `## Key References`).
- `grep -Fq 'agents/personas/work.md'` matches (in `## Key References`).
- `grep -Fq 'memory/me/preferences.md'` matches (in `## Key References`).
- Placeholder extraction: `grep -oE '\{\{[^}]+\}\}' identity.md | sort -u` produces exactly the five allowlisted tokens (no more, no less than the five `{{employee_*}}` set).
- Byte-budget: `wc -c < identity.md` returns a value in `[200, 2048]`.

---

## Blueprint — `memory/me/preferences.md`

Maps to AC1, AC4, AC5, AC6, AC7, AC8.

### Frontmatter keys (in canonical order, 5 keys total)

| # | Key | Value type | Literal value |
| --- | --- | --- | --- |
| 1 | `type` | string | `preferences` |
| 2 | `scope` | string | `work` |
| 3 | `created` | string | `YYYY-MM-DD` (literal date-shape token) |
| 4 | `updated` | string | `YYYY-MM-DD` (literal date-shape token) |
| 5 | `tags` | inline array | `[preferences, work]` |

### Frontmatter literal-value locks

- `type` value MUST be the literal bare string `preferences`.
- `scope` value MUST be the literal bare string `work`.
- `created` and `updated` values MUST be the literal date-shape token `YYYY-MM-DD`.
- `tags` value MUST be the YAML inline array `[preferences, work]`. Token `work` is present; token `personal` is NOT present.
- Frontmatter contains ZERO `{{employee_*}}` identity-placeholder tokens (identity lives in `identity.md`; `preferences.md` describes workspace-behavior, not operator-identity — AC4).

### Body headings (in order, 6 headings total)

1. `# Preferences` (H1, literal — no placeholder)
2. `## Communication Style` (H2)
3. `## Tooling` (H2)
4. `## Meeting Cadence` (H2)
5. `## Working Hours` (H2)
6. `## AI Assistant` (H2)

### Required body elements

- The `## Tooling` section MUST enumerate the five active Vixxo work MCPs from the Story 2.3 persona: `Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong` (AC5). Each literal name MUST be present somewhere in the body via `grep -Fq`.
- The `## AI Assistant` section MUST defer to `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md` for tone / signing / persona details. The section MUST NOT restate tone or signing conventions — single source of truth.
- The `## Communication Style` section MUST defer to `AGENTS.md` (and / or `.cursor/rules/agent-identity.mdc`) for the communication-style authoritative list (no em dashes, no AI-slop phrases, direct and concise). The section MUST NOT restate the full list — single source of truth.
- The body contains ZERO references to `Chiron`, `Benji`, `Flowtopic`, `Obsidian` (as a personal-tool reference), `gmail` (MCP), `google-calendar` (MCP) — personal-assistant and personal-productivity tokens from the gtd-life source that must not port through (AC5).
- The body contains ZERO `{{…}}` placeholder tokens of any kind (prose-only — AC5 / AC6 reinforcement).

### Allowed placeholders in this file

None. `preferences.md` is prose-only.

Plus the literal token `YYYY-MM-DD` in frontmatter only (not a `{{...}}` placeholder).

### Byte budget

- Lower bound: 200 bytes (enforces frontmatter + five H2 headings + minimal body prose are actually authored).
- Upper bound: 2048 bytes (guards against ported Derek content regression; the gtd-life source `me/preferences.md` is ~2900 bytes).
- Harness assertion: `200 ≤ wc -c < preferences.md ≤ 2048`.

### Harness probes (`check_task3` + `check_task4`)

- `[[ -f memory/me/preferences.md ]]` (existence).
- `[[ -s memory/me/preferences.md ]]` (non-empty).
- `head -c 3 memory/me/preferences.md` equals `---`.
- `tail -c 1 memory/me/preferences.md | od -An -tx1 | tr -d '[:space:]'` equals `0a`.
- `grep -c $'\r' memory/me/preferences.md` equals `0`.
- Frontmatter block extracted via `awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}'`; within the extracted block:
  - Each of the 5 canonical-order keys appears on its own line anchored `^<key>:`.
  - `grep -Fq 'type: preferences'` matches.
  - `grep -Fq 'scope: work'` matches.
  - `grep -Fq 'tags: [preferences, work]'` matches.
  - Frontmatter body contains zero `{{…}}` tokens (`grep -oE '\{\{[^}]+\}\}'` on the extracted frontmatter block produces empty output).
- Each of the six body headings (`# Preferences`, `## Communication Style`, `## Tooling`, `## Meeting Cadence`, `## Working Hours`, `## AI Assistant`) appears as a standalone full line via `grep -Fxq`.
- Each of the five MCP names (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`) appears via `grep -Fq`.
- Whole-file placeholder extraction: `grep -oE '\{\{[^}]+\}\}' preferences.md | wc -l` equals `0` (AC6 — prose-only).
- Byte-budget: `wc -c < preferences.md` returns a value in `[200, 2048]`.

---

## Placeholder vocabulary lock

### Allowlist for `memory/me/identity.md` (5 tokens total)

Only the following `{{...}}` tokens are permitted in `identity.md`. Any `{{...}}` token extracted from `identity.md` that is not in this set FAILS the placeholder-vocabulary gate (AC6).

```
{{employee_name}}
{{employee_role}}
{{employee_department}}
{{employee_manager}}
{{employee_email}}
```

### Allowlist for `memory/me/preferences.md` (0 tokens total)

`preferences.md` contains ZERO `{{...}}` placeholder tokens. The file is prose-only. Any extracted `{{...}}` token from `preferences.md` FAILS the placeholder-vocabulary gate.

### Vocabulary provenance

- `{{employee_name}}` — introduced in Story 2.1 `.cursor/rules/agent-identity.mdc`; architecture.md line 23 names it explicitly.
- `{{employee_role}}` — introduced in Story 2.1 agent-identity.mdc; architecture.md line 23 names it explicitly.
- `{{employee_department}}` — introduced in Story 2.1 agent-identity.mdc; also used by Story 2.3 `agents/personas/work.md`.
- `{{employee_manager}}` — introduced in Story 2.1 agent-identity.mdc; also used by Story 2.3 work persona.
- `{{employee_email}}` — NEW for Story 3.3 (Epic 5 Story 5.2 wizard prompts for email; `identity.md` is the natural home for operator contact info). Forward-referenced in `story-3-1-canonical-blueprint.md` "Forbidden specific placeholder names" block.

### Additional literal tokens (non-placeholder, allowed in frontmatter only)

- `YYYY-MM-DD` — date-shape token in `created` / `updated` values.

This is NOT a `{{...}}` placeholder; it is a literal plaintext token indicating the expected value shape. The Epic 5 Story 5.2 wizard rewrites it to the current ISO-8601 date. It is not extracted by the `grep -oE '\{\{[^}]+\}\}'` placeholder enumeration.

### Forbidden placeholder forms (BOTH files)

- Single-brace `{placeholder}` — confusable with shell-variable interpolation. Probe: `grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}' <file>` MUST return zero matches (note: double-brace `{{…}}` is NOT matched by this probe — the inner brace is immediately followed by another brace, not an alphanumeric character).
- Angle-bracket `<placeholder>` — confusable with XML / HTML tags. Probe: `grep -oE '<[A-Za-z_][A-Za-z0-9_]*>' <file>` MUST return zero matches. Exception: HTML comment `<!-- comment -->` is permitted (`<!-- ... -->` starts with `<!`, not `<[A-Za-z_]`, so the probe does not match HTML comments).
- Percent-wrapped `%placeholder%` — confusable with Windows environment variables. Probe: `grep -oE '%[A-Za-z_][A-Za-z0-9_]*%' <file>` MUST return zero matches.
- Dollar-brace `${placeholder}` — confusable with shell-variable interpolation. Probe: `grep -oE '\$\{[^}]+\}' <file>` MUST return zero matches.

### Forbidden specific placeholder names (even in `{{...}}` form)

- `{{Name}}`, `{{Meeting Title}}`, `{{Decision Title}}`, `{{Reference Title}}`, `{{topic}}`, `{{owner}}`, `{{estimated minutes}}`, `{{person}}`, `{{action}}`, `{{action item}}`, `{{date}}`, `{{company}}`, `{{role}}`, `{{manager or "N/A"}}`, `{{count or "N/A"}}`, `{{Recipient or Moment}}`, `{{name}}` — these are the Story 3.1 note-shape placeholder vocabulary owned by `memory/{meetings,people,decisions,reference,inbox,appreciations}/` templates. They are structurally incompatible with identity-file semantics.

Any occurrence of these 17 note-shape tokens in `identity.md` or `preferences.md` FAILS the placeholder-vocabulary gate.

---

## Banned-term lock

Inherited verbatim from Stories 3.1 / 3.2 Phase-4 F4 post-merge state. Story 3.3 adds ZERO new tokens to the 17-token regex set. Boundary-guarded POSIX-ERE regex, case-insensitive via `grep -iE`.

### 17-token regex set (carried forward from Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2)

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

### Composite boundary-guarded regex (harness constant `BANNED_TERMS_REGEX`)

```
(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])
```

Invoked as `grep -iE` for case-insensitivity. Tested in `regex_self_probe()` with both a carried-forward token (`derek` → positive, `derekson` → boundary-rejected) and the Story-3.1-added token (`personal` → positive, `personally` → boundary-rejected). Story 3.3 adds one additional placeholder-allowlist probe: `{{employee_name}}` → allowlist hit for identity-file context; `{{Meeting Title}}` → allowlist miss for identity-file context.

### Rationale summary (carried forward from Story 2.1 → 3.2, unchanged for 3.3)

- `derek`, `neighbors` — operator's real name (Story 2.1).
- `revivago`, `flowtopic` — personal business tokens (Story 2.2).
- `benji` — personal task-system token (Story 2.3 / 2.4).
- `gtd-life`, `gtdlife` — source-repo reference (Story 2.3).
- `wyoming`, `cheyenne` — example PII geography tokens; templates must not encode any specific location.
- `family`, `wife`, `son`, `daughter`, `dog` — family / personal-life tokens; work-only scope per AC7 / NFR7.
- `home` — personal-life token.
- `blog` — personal output channel; gtd-life has `memory/blog-ideas/`.
- `personal` — Story 3.1 Phase-4 F4 addition; defence-in-depth against residual `personal` scope enumerations. Specifically protects against `scope: personal` or `tags: [..., personal]` in `identity.md` / `preferences.md` frontmatter.

---

## Derek-specific fixed-string backstop (Story 3.3 defence-in-depth)

In addition to the 17-token banned-term regex, the harness runs narrow-scope fixed-string (`grep -Fi`) scans across both authored files for the following Derek-specific tokens that appear verbatim in the gtd-life source `me/identity.md` and `me/preferences.md`. These strings are NOT added to the main 17-token regex because some of them (e.g. `Integrum`, `Laurie`) should not trigger false positives in future unrelated content outside `memory/me/`. Fixed-string enforcement is scoped narrowly to the two Story-3.3-authored files.

### Fixed-string list (harness constant `DEREK_FIXED_STRINGS`, 12 entries)

```
Chiron
MasteryLab
Agile Weekly
Queen Creek
Gangplank
Bodybuilding.com
Integrum
Omarchy
derekneighbors.com
Playrix
Laurie
Deke
```

### Why fixed-string and NOT part of the 17-token regex

- `Chiron` — Derek's AI-agent name from the gtd-life `me/preferences.md` source. A mythological figure name that may legitimately appear elsewhere in non-Derek contexts (e.g. a reference to Greek mythology). Narrow-scope enforcement in `memory/me/*.md` only.
- `MasteryLab`, `Agile Weekly`, `Gangplank`, `Bodybuilding.com`, `Integrum` — Derek's past business / employer names. `Integrum` is a generic Latin-derived word meaning "whole" and may appear in future non-Derek content.
- `Queen Creek` — Derek's location (Arizona). Two-word token that includes a common English noun (`Queen`).
- `Omarchy` — Derek's Linux distro preference. Neologism that may appear in future tech content.
- `derekneighbors.com` — Derek's personal domain. Fixed-string is more robust than regex here.
- `Playrix` — a game company Derek references in `ventures.md` (out-of-scope source file); included here as defence-in-depth in case of careless copy.
- `Laurie`, `Deke` — common first names / nicknames; must not appear in work-only scaffold files.

### Path-reference fixed-string scan (carried forward from Stories 3.1 / 3.2)

Beyond the Derek-specific backstop, the harness runs fixed-string scans for:

- `gtd-life` — source-repo reference (also caught by the 17-token regex; fixed-string is belt-and-suspenders).
- `~/Public/gtd-life` — literal tilde-prefixed filesystem path.
- `Public/gtd-life` — tilde-stripped variant.
- `/Users/` — any absolute macOS home-directory path.

Any match of any of these literal strings in either authored file FAILS the cross-file scrub gate (`check_task4`).

### `personal`-in-tags backstop

The harness runs `grep -Eq '^tags:.*personal' <file>` on each authored file. This MUST return zero matches — backstops AC2 / AC4 tags-array assertion against the narrow regression where `personal` slips into a `tags:` inline array (the boundary-guarded 17-token regex already catches this, but the fixed-string probe is defence-in-depth).

---

## Forbidden-form lock (summary, both files)

The harness enforces the following forbidden-form probes on both `identity.md` and `preferences.md` in `check_task4`:

| Form | Regex probe | Must return |
| --- | --- | --- |
| Single-brace `{name}` | `grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}'` | 0 matches |
| Angle-bracket `<name>` | `grep -oE '<[A-Za-z_][A-Za-z0-9_]*>'` | 0 matches |
| Percent-wrapped `%name%` | `grep -oE '%[A-Za-z_][A-Za-z0-9_]*%'` | 0 matches |
| Dollar-brace `${name}` | `grep -oE '\$\{[^}]+\}'` | 0 matches |
| HTML comment `<!-- … -->` | (permitted; not probed negatively) | — |

The HTML-comment exception matches the Story 3.1 `## Scrub / repair rules` convention. A trailing `<!-- Why: … -->` one-line comment at the end of each authored file is permitted (and recommended per the Story 3.3 Task 3a / 3b authoring guidance).

---

## Directory-state lock

### Directory-count lock

`ls -A memory/me/ | wc -l | tr -d '[:space:]'` MUST equal `2`. Exactly two entries, both regular markdown files, none hidden, none directories, none sentinel files (AC1).

### Forbidden sentinels under `memory/me/`

- `.gitkeep` — `identity.md` and `preferences.md` are git-trackable content; sentinel is redundant (Story 3.1 AC9 / Story 3.2 AC11 precedent).
- `.keep` — same rationale.
- `empty` — same rationale.
- `placeholder` — same rationale.
- `.DS_Store` — macOS Finder metadata.
- `Icon\r` — macOS custom-icon resource-fork sentinel.
- `*.bak`, `*.log`, `*.tmp` — backup / log / scratch files.

Enforced via `find memory/me/ -maxdepth 1 -type f -name '<pattern>'` probes in `check_task3`.

### Forbidden subdirectories under `memory/me/`

- `networking/` — gtd-life source subdir (personal-contact content) is out of scope for Story 3.3.
- Any subdirectory — Story 3.3 ships a flat two-file directory (AC1).

Enforced via `find memory/me/ -mindepth 1 -type d | head -n 1` returning empty in `check_task3`.

---

## Out-of-scope lock (what Story 3.3 does NOT emit)

Explicit exclusion list. Any file or directory here FAILS the scope lock if produced by Story 3.3.

### File-system paths explicitly out of scope

- `memory/me/family.md` — personal-life content (gtd-life source excluded).
- `memory/me/food-guide-queen-creek.md` — personal-life, PII-locale (gtd-life source excluded).
- `memory/me/ventures.md` — Derek side businesses (gtd-life source excluded).
- `memory/me/properties.md` — Derek real-estate (gtd-life source excluded).
- `memory/me/networking/` — personal-contact content (gtd-life source subdir excluded).
- `memory/companies/`, `memory/vixxo/`, `memory/daily/`, `memory/blog-ideas/` — not in Epic 3 scope.
- `identity.md` / `preferences.md` at repo root — WRONG location; identity lives at `memory/me/identity.md` per agent-identity rule and work persona "Context Files" references.

### Files / directories explicitly preserved unchanged by Story 3.3 (AC9 / AC12 invariance)

- `memory/.gitkeep` (0 bytes, from Story 1.1) — byte-for-byte stable.
- The nine Story 3.1 template files under `memory/` (positional byte-count lock via `STORY_3_1_TEMPLATE_BYTES`: `828 / 250 / 513 / 306 / 561 / 588 / 506 / 72 / 211`):
  - `memory/meetings/_template/meeting.md`
  - `memory/meetings/_template/agenda.md`
  - `memory/meetings/_template/prep.md`
  - `memory/meetings/_template/transcript.md`
  - `memory/people/_template.md`
  - `memory/decisions/_template.md`
  - `memory/reference/_template.md`
  - `memory/inbox/_template.md`
  - `memory/appreciations/_template.md`
- The seven Story 3.2 `.obsidian/` JSON files under `memory/.obsidian/` (byte-level invariance owned by Story 3.2's own harness running in `task6` regression; Story 3.3 checks existence + non-empty only):
  - `app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`, `daily-notes.json`, `graph.json`, `templates.json`.
- All Story 1.x / 2.x root context + rule files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `README.md`, `LICENSE`, `.gitignore`, `.cursor/rules/*.mdc`, `agents/personas/work.md`).
- The nine predecessor validation harnesses under `_bmad-output/implementation-artifacts/tests/` (AC10 / AC12 — zero bytes changed during Story 3.3 execution; distinct from Stories 3.1 / 3.2 which each added one line to `story-1-1-scaffold-validation.sh`).
- No new `.gitkeep` / `.keep` / `empty` / `placeholder` sentinel files under `memory/me/` (the two markdown files are themselves git-trackable content; sentinels are redundant).

---

## Cross-AC coverage map

| AC | Lock |
| --- | --- |
| AC1 | `## Directory-state lock` (exactly-two file count + forbidden-sentinel block + forbidden-subdirectory block) + both per-file blueprints (existence + non-empty + trailing newline + frontmatter-opens-on-line-1) |
| AC2 | `memory/me/identity.md` blueprint frontmatter key-order lock (10 keys) + literal-value locks (`type: identity`, `scope: work`, five `{{employee_*}}` quoted scalars, `tags: [identity, work]`) |
| AC3 | `memory/me/identity.md` blueprint body-headings lock (8 headings) + five-placeholder usage requirement + `work context only` literal + `.cursor/rules/agent-identity.mdc` deferral + `## Key References` content |
| AC4 | `memory/me/preferences.md` blueprint frontmatter key-order lock (5 keys) + literal-value locks (`type: preferences`, `scope: work`, `tags: [preferences, work]`) + zero-`{{employee_*}}`-in-frontmatter assertion |
| AC5 | `memory/me/preferences.md` blueprint body-headings lock (6 headings) + five-MCP enumeration (`Linear` / `GitHub` / `Microsoft 365` / `Salesforce` / `Gong`) + deferral-to-persona-and-identity-rule discipline + zero-personal-tools assertion |
| AC6 | `## Placeholder vocabulary lock` section (identity.md 5-token allowlist + preferences.md 0-token allowlist + forbidden forms + forbidden Story 3.1 note-shape vocabulary) |
| AC7 | `## Banned-term lock` section (17-token regex) + `## Derek-specific fixed-string backstop` section (12 tokens) + path-reference fixed-string scans + `personal`-in-tags backstop |
| AC8 | Byte-budget per-file locks (`200 ≤ bytes ≤ 2048`) + LF-only line ending assertion |
| AC9 | `## Out-of-scope lock` section "preserved unchanged" subsection (Story 3.1 template positional byte-count lock + Story 3.2 `.obsidian/` existence lock + `memory/.gitkeep` 0-byte lock + no-new-sentinel-files lock) |
| AC10 | `## Out-of-scope lock` section explicit reference to zero Story 1.1 harness edit required (Story 2.1 commit `0db273b` anticipatory allowlist admits `me`) |
| AC11–AC14 | N/A at blueprint level; handled by Task 4 harness (`check_task1` through `check_task6`), Task 5 zero-edit regression, Task 6 handoff, Task 7 sprint-status. The blueprint is consumed by `check_task2` (existence + required section headers — title `# Story 3.3 Canonical Blueprint`, one section per target file, `## Placeholder vocabulary lock`, `## Banned-term lock`, `## Forbidden-form lock` — the last mapped to `## Derek-specific fixed-string backstop` and `## Forbidden-form lock (summary, both files)` in this document) and `check_task3` / `check_task4` (shape + scrub) gates. |
