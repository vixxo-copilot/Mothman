# Story 3.2 Task 6 Handoff Package

**Story:** 3.2 — Port portable `memory/.obsidian/` config from gtd-life (seven JSON files; `workspace.json` excluded; `templates.json` REPAIRED)
**Phase:** 2 — Dev handoff
**Date:** 2026-04-20
**Author:** Amelia (Senior Software Engineer, autonomous Dev subagent, wave-3 Tasks 4 → 5 → 6 → 7)
**Sprint-status entry:** `3-2-portable-obsidian-config`
**Linear ID:** AIP-38

This handoff package certifies that Story 3.2 is implementation-complete and ready for Phase 3 code review. It collects the AC-to-evidence map, the full validation command transcript for the Story 3.2 harness plus the eight predecessor regression harnesses, byte-counts + SHA-256 checksums of the seven ported JSON files (for future drift detection), forward-looking notes for downstream stories, and an explicit zero-edit verification that no prior-story artifact was mutated by Story 3.2 beyond the single documented Story 1.1 harness line-155 allowlist integration fix (AC13 / AC15 exception; Story 2.1 / Story 3.1 precedent).

## 1. AC-to-evidence map

Each acceptance criterion maps to a harness gate, file path, or direct scan command that proves it. All `grep` / `find` / `awk` / harness invocations below are reproducible from the repo root.

| AC | Summary | Evidence |
|---|---|---|
| AC1 | `memory/.obsidian/` exists with exactly seven portable JSON files | Harness `check_task3` asserts `[[ -f … ]]` + `[[ -s … ]]` + trailing-newline `od`-probe per file, plus the directory-count block `ls -A memory/.obsidian \| wc -l == 7`. Also: `check_task3` forbidden-file block asserts no `workspace.json`, no `*.bak`/`*.log`/`*.tmp`/`.DS_Store`, no `plugins/` subdirectory. |
| AC2 | `app.json` shape (3 keys, canonical order, ≤200 bytes) | `check_task3` asserts `grep -Fq '"strictLineBreaks"'` + `grep -Fq '"showFrontmatter"'` + `grep -Fq '"defaultViewMode": "source"'`. Measured byte-count: 90 (well under 200-byte upper bound). |
| AC3 | `appearance.json` is empty object `{}` | `check_task3` strips whitespace via `tr -d '[:space:]'` and asserts contents equal literal `{}`. Measured byte-count: 3 (`{}\n`). |
| AC4 | `community-plugins.json` is empty array `[]`; no `plugins/` subdir | `check_task3` asserts stripped contents equal `[]`; forbidden-dir block asserts `[[ ! -d memory/.obsidian/plugins ]]`. Measured byte-count: 3. |
| AC5 | `core-plugins.json` canonical 31-key enabled/disabled map | `check_task3` asserts each of 16 enabled (`"<plugin>": true`) + 15 disabled (`"<plugin>": false`) key-value pairs individually via `grep -Fq`; total key count `grep -c '":'` equals 31. |
| AC6 | `daily-notes.json` 3-key shape (`folder: "daily"`, `format: "YYYY-MM-DD"`, `template: ""`); no absolute path leak | `check_task3` asserts `grep -Fq '"folder": "daily"'`, `grep -Fq '"format": "YYYY-MM-DD"'`, `grep -Fq '"template": ""'`. `check_task4` asserts `/Users/` / `Public/` / `gtd-life` fixed-string scans return zero. |
| AC7 | `graph.json` 20-key shape; `search: ""`; `colorGroups: []`; ≤1024 bytes | `check_task3` asserts `grep -Fq '"search": ""'`, `grep -Fq '"colorGroups": []'`, all 20 canonical keys per AC7, and `grep -o '":' \| wc -l == 20`. Measured byte-count: 494 (under 1024). |
| AC8 | `templates.json` REPAIRED (`folder: ""`, literal `_templates` absent) | `check_task3` asserts `grep -Fq '"folder": ""'` AND `! grep -Fq '_templates'` AND exactly one `":` occurrence. `check_task4` additionally asserts `grep -Fq '_templates' ${TEMPLATES_JSON}` returns zero. |
| AC9 | No `workspace.json`, no `*.bak`, no `bobby`, no absolute-path leak, no meeting-slug fingerprint | `check_task3` forbidden-file block and `check_task4` fixed-string + regex scrub: per-file `grep -Fiq 'bobby'` zero, per-file `grep -Eq '[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+'` zero, per-file `grep -Fq 'gtd-life'`/`'/Users/'`/`'Public/gtd-life'` zero. |
| AC10 | Zero banned-term hits across all seven files (17-token lock) | `check_task4` per-file boundary-guarded regex `(^\|[^A-Za-z])(derek\|neighbors\|revivago\|benji\|flowtopic\|gtd-life\|gtdlife\|wyoming\|cheyenne\|family\|home\|blog\|wife\|son\|daughter\|dog\|personal)($\|[^A-Za-z])` case-insensitive → 0 hits across all seven files. Plus fixed-string `grep -F` scans for `gtd-life` / `~/Public/gtd-life` / `Public/gtd-life` → 0 each. |
| AC11 | `memory/.gitkeep` + nine Story 3.1 templates byte-stable; no new sentinels | `check_task3` AC11 block: `wc -c < memory/.gitkeep` equals 0; each of nine Story 3.1 template files (`meetings/_template/{meeting,agenda,prep,transcript}.md`, `people/_template.md`, `decisions/_template.md`, `reference/_template.md`, `inbox/_template.md`, `appreciations/_template.md`) exists and is non-empty; `find memory/.obsidian -type f -name '.gitkeep'` (+ `.keep`, `empty`, `placeholder`) returns zero. SHA-256 of Story 3.1 templates matches the Story 3.1 handoff fingerprints (preserved via `git status`: no template files appear in the uncommitted working tree). |
| AC12 | Harness exists + wired into the test-harness family | `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh` exists, is executable (`-rwxr-xr-x`, 27227 bytes), uses `#!/usr/bin/env bash` on line 1 + `set -euo pipefail` on line 2. Six gates + `all` dispatcher. `regex_self_probe` exercises `derek`/`derekson`, `personal`/`personally`, plus meeting-slug positive + negative probes per Story 2.4 F4 + Story 3.1 F7 precedent. BSD-grep + GNU-grep compatible; POSIX-bash-3.2 compatible; no `jq`/`node`/`python`/`rg`. Under `all` mode emits exactly 7 `^PASS:` lines (`task1` → `task6` → `all`). |
| AC13 | 8-harness regression clean (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1) | See §2 for full transcript. All 8 predecessors exit `0` with `PASS: all`; per-harness `^PASS:` line-count fingerprint matches `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7`. Zero bytes changed in seven of eight predecessor harnesses; one documented one-line integration fix applied to `story-1-1-scaffold-validation.sh` line 155 memory-allowlist (AC13 exception — see §5). |
| AC14 | Sprint tracker lifecycle transition + epic-3 preserved | `3-2-portable-obsidian-config.status` transitions `backlog → review` (autonomous-swarm status-collapse per Story 2.1 / 2.2 / 2.3 / 2.4 / 3.1 precedent; Phase 1 flip to `ready-for-dev` was performed by the SM, then Phase 2 flip to `review` by Dev). `epic-3.status` preserved at `in-progress` (Story 3.1 opened the epic; Story 3.3 still `backlog`). `last_updated` set to `2026-04-20`. Zero other status values regressed; all comments and entry ordering preserved byte-for-byte. |
| AC15 | Additive-only; no scope creep into 3.3 / Epic 4 / Epic 5 | File List (story file, §File List) enumerates exactly seven `.obsidian/` JSON files + four evidence artifacts under `tests/` (baseline audit, canonical blueprint, harness, this handoff) + the story file + `sprint-status.yaml`. No `memory/me/` (Story 3.3). No `memory/daily/` / `memory/companies/` / `memory/blog-ideas/` / `memory/vixxo/` / `memory/_templates/`. No edits under `.cursor/` / `agents/` / `bin/` / `scripts/` / `docs/` / repo root (outside the documented `story-1-1-scaffold-validation.sh` line-155 allowlist fix). |

## 2. Full validation command transcript

All nine harnesses were run from the repo root at Phase 2 handoff after the Story 1.1 line-155 allowlist integration fix was applied. Each harness exited zero with `PASS: all`.

```
$ cd /Users/dneighbors/Public/assistants-template
$ TESTS=_bmad-output/implementation-artifacts/tests
$ for h in story-1-1-scaffold-validation.sh \
           story-1-2-root-files-validation.sh \
           story-1-3-root-context-validation.sh \
           story-2-1-agent-identity-validation.sh \
           story-2-2-guardrail-and-formatting-validation.sh \
           story-2-3-work-persona-validation.sh \
           story-2-4-benji-inbox-absence-validation.sh \
           story-3-1-memory-template-tree-validation.sh \
           story-3-2-obsidian-config-validation.sh; do
    echo "=== $h ==="
    out="$(bash $TESTS/$h all 2>&1)"
    rc=$?
    passcount=$(printf '%s\n' "$out" | grep -c '^PASS:')
    tail=$(printf '%s\n' "$out" | grep '^PASS:' | tail -3)
    echo "exit=$rc pass_count=$passcount"
    printf '%s\n' "$tail"
  done

=== story-1-1-scaffold-validation.sh ===
exit=0 pass_count=1
PASS: all
=== story-1-2-root-files-validation.sh ===
exit=0 pass_count=1
PASS: all
=== story-1-3-root-context-validation.sh ===
exit=0 pass_count=1
PASS: all
=== story-2-1-agent-identity-validation.sh ===
exit=0 pass_count=1
PASS: all
=== story-2-2-guardrail-and-formatting-validation.sh ===
exit=0 pass_count=10
PASS: task8
PASS: task9
PASS: all
=== story-2-3-work-persona-validation.sh ===
exit=0 pass_count=7
PASS: task5
PASS: task6
PASS: all
=== story-2-4-benji-inbox-absence-validation.sh ===
exit=0 pass_count=7
PASS: task5
PASS: task6
PASS: all
=== story-3-1-memory-template-tree-validation.sh ===
exit=0 pass_count=7
PASS: task5
PASS: task6
PASS: all
=== story-3-2-obsidian-config-validation.sh ===
exit=0 pass_count=7
PASS: task5
PASS: task6
PASS: all
```

The Story 3.2 harness in isolation (full output, not tail-truncated) emitted exactly:

```
$ bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
$ echo $?
0
```

**Per-harness `^PASS:` line-count fingerprint (measured 2026-04-20):**

| Harness | Expected | Observed | Status |
|---|---|---|---|
| `story-1-1-scaffold-validation.sh` | 1 | 1 | PASS |
| `story-1-2-root-files-validation.sh` | 1 | 1 | PASS |
| `story-1-3-root-context-validation.sh` | 1 | 1 | PASS |
| `story-2-1-agent-identity-validation.sh` | 1 | 1 | PASS |
| `story-2-2-guardrail-and-formatting-validation.sh` | 10 | 10 | PASS |
| `story-2-3-work-persona-validation.sh` | 7 | 7 | PASS |
| `story-2-4-benji-inbox-absence-validation.sh` | 7 | 7 | PASS |
| `story-3-1-memory-template-tree-validation.sh` | 7 | 7 | PASS |
| `story-3-2-obsidian-config-validation.sh` | 7 | 7 | PASS |
| **Total** | **42** | **42** | **PASS** |

This fingerprint is the AC13-mandated regression invariant. Any future story that breaks any of these counts must be treated as a harness regression and stopped at Phase 2.

## 3. Byte-counts and SHA-256 checksums of the seven ported JSON files

For future drift detection (Epic 6 CI gate or manual re-verification), the canonical fingerprint of the seven ported `memory/.obsidian/` JSON files as of 2026-04-20 Phase 2 handoff is:

| File | Bytes | SHA-256 |
|---|---|---|
| `memory/.obsidian/app.json` | 90 | `c39e6f3f3becf132433b3dc698eadcf0600a026e5ea73cb87676ad27b2c7a810` |
| `memory/.obsidian/appearance.json` | 3 | `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356` |
| `memory/.obsidian/community-plugins.json` | 3 | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `memory/.obsidian/core-plugins.json` | 702 | `ac8a3c03d04b14d992f568d7fab290b232f611c7844a3ccbcdb3f0e84b72f280` |
| `memory/.obsidian/daily-notes.json` | 68 | `f21e73a2012255ceda1ea9171cac89cb03c45301772dc2b4eedd357970f1eb78` |
| `memory/.obsidian/graph.json` | 494 | `f75c7af68f6f1a17663d9c4f8359dca4567d91a6f59c48e03c5868b639d19424` |
| `memory/.obsidian/templates.json` | 19 | `935f8fcefa2349412bd80c16f7235117fd462a2fb962d80abcf7d8cfb01c27e8` |
| **Total** | **1379 bytes** | — |

Reproduction:

```
$ for f in memory/.obsidian/*.json; do
    bytes=$(wc -c < "$f" | tr -d ' ')
    sha=$(shasum -a 256 "$f" | awk '{print $1}')
    printf '%s  %s  %s\n' "$bytes" "$sha" "$f"
  done
```

**Byte-count commentary:**

- `app.json` 90 bytes (source 89 + trailing-newline normalization); within AC2 ≤200-byte budget.
- `appearance.json` 3 bytes (`{}\n`); within AC3 ≤10-byte budget.
- `community-plugins.json` 3 bytes (`[]\n`); within AC4 ≤10-byte budget.
- `core-plugins.json` 702 bytes (source 701 + trailing-newline normalization); 31-key canonical map.
- `daily-notes.json` 68 bytes (byte-for-byte identical to source).
- `graph.json` 494 bytes (source 493 + trailing-newline normalization); within AC7 ≤1024-byte budget; 20-key shape (per AC7 ground truth) preserved verbatim including `centerStrength: 0.518713248970312`.
- `templates.json` 19 bytes (REPAIRED; pretty-printed `{\n  "folder": ""\n}\n`); within blueprint 64-byte upper bound.

## 4. Forward-looking notes for downstream stories

**Immediate successors (Epic 3):**

- **Story 3.3 — `memory/me/identity.md` + `memory/me/preferences.md`:** Will create `memory/me/` and two `scope: work` frontmatter markdown files. Story 3.2 does NOT pre-create `memory/me/` — that is strictly Story 3.3 territory. Story 3.3's regression chain will add Story 3.2 as the ninth predecessor harness.
- Obsidian users may manually configure the Templates plugin folder on first open (Story 3.2 ships `folder: ""`). If the user creates `memory/_templates/`, pointing the plugin there is an end-user action, not a template concern.

**Epic 4 (MCP packaging):**

- Epic 4 Story 4.1 will write `.cursor/mcp.json` referencing `memory/` paths in MCP server context. Independent of Story 3.2 (no `.obsidian/` touch).
- Epic 4 Stories 4.2–4.4 (`.env.example`, docs) do not touch `memory/`.

**Epic 5 (setup wizard `bin/init`):**

- Epic 5 Story 5.2 wizard writes to `memory/me/identity.md` / `preferences.md` (Story 3.3 scope). The wizard may optionally re-open Obsidian with a welcome note — does NOT regress Story 3.2's `.obsidian/` config files.
- The wizard could seed a daily-note template or populate `_templates/` if desired — both out of Story 3.2 scope but compatible with the `folder: ""` default.

**Epic 6 (PII scrub + CI guardrail):**

- Epic 6 Story 6.2 can invoke this harness directly as a CI gate:
  ```
  bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh all
  ```
  Harness contract: exit 0 on pass, 1 on fail, exactly 7 `^PASS:` lines on stdout. GitHub-Actions-native.
- The 17-token banned-term regex + fixed-string `bobby` + meeting-slug regex + `_templates` forbidden-substring probes are all re-runnable as standalone CI checks.

**User-facing Obsidian behavior on first open (post-3.2, pre-3.3):**

- Vault opens at `memory/`; file-explorer sidebar shows `meetings/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/` (Story 3.1).
- Templates plugin enabled but unconfigured (Obsidian prompts silently; no error banner).
- Daily-notes plugin enabled; will auto-create `memory/daily/` on first daily-note action with `YYYY-MM-DD.md` naming.
- Graph view shows the nine Story 3.1 template files linked via their `related_to` / `context` frontmatter relationships.
- Zero community plugins installed; user can install their own freely.
- No references to Derek, Bobby, RevivaGo, gtd-life, or any meeting-cache slugs.

## 5. Zero-edit verification + integration-fix exception

**Byte-for-byte stable across Story 3.2 execution** (verified via `git status` + harness `check_task3` AC11 block):

- **Root context files:** `AGENTS.md`, `CLAUDE.md`, `.cursorrules` — no edits.
- **Root files (Story 1.2):** `README.md`, `LICENSE`, `.gitignore` — no edits.
- **Memory sentinel (Story 1.1):** `memory/.gitkeep` — remains 0 bytes.
- **Story 2.1 rule:** `.cursor/rules/agent-identity.mdc` — no edits.
- **Story 2.2 rules (four):** `.cursor/rules/outbound-messaging-guardrail.mdc`, `.cursor/rules/memory-vault-protection.mdc`, `.cursor/rules/teams-dm-formatting.mdc`, `.cursor/rules/email-triage-thread-defaults.mdc` — no edits.
- **Story 2.3 persona:** `agents/personas/work.md` — no edits.
- **Story 3.1 template files (nine):** `memory/meetings/_template/meeting.md`, `memory/meetings/_template/agenda.md`, `memory/meetings/_template/prep.md`, `memory/meetings/_template/transcript.md`, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md` — byte-for-byte identical to Story 3.1 Task 6 handoff fingerprint (confirmed by absence of any of these paths in `git status`; harness `check_task3` AC11 block re-asserts existence + non-empty).
- **Predecessor harnesses (seven of eight):** `story-1-2-root-files-validation.sh`, `story-1-3-root-context-validation.sh`, `story-2-1-agent-identity-validation.sh`, `story-2-2-guardrail-and-formatting-validation.sh`, `story-2-3-work-persona-validation.sh`, `story-2-4-benji-inbox-absence-validation.sh`, `story-3-1-memory-template-tree-validation.sh` — zero bytes changed.
- **Evidence artifacts for prior stories:** all prior `story-*-baseline-audit.md`, `story-*-canonical-blueprint.md`, `story-*-task*-handoff.md` files — no edits.

**Integration-fix exception (AC13 / AC15):**

A single one-line additive extension was applied to `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` line 155. This is the third instance of this pattern in the project history:

- Story 2.1 commit `0db273b` added `me|mcp|obsidian` to anticipate future Epic-3 memory subdirs.
- Story 3.1 Phase-4 F1 added `meetings|people|decisions|reference|inbox|appreciations` on the same line to admit the template-tree scaffolding.
- Story 3.2 (this story) adds `\.obsidian` on the same line to admit the hidden Obsidian-config directory.

**Exact change** (line 155 of `story-1-1-scaffold-validation.sh`):

```diff
       "memory")
-        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations)$' || true)"
+        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian|\.obsidian|meetings|people|decisions|reference|inbox|appreciations)$' || true)"
         ;;
```

A single `|\.obsidian` token inserted after `obsidian` in the `memory)` branch allowlist. The `\.` is ERE-escaped because `.obsidian` is a dot-prefixed hidden directory name; without the escape `.obsidian` would match any single-char-plus-`obsidian` pattern. Matches the minimal-change pattern the Story 1.1 harness was designed to accept; classified as an integration fix (not a Story 3.2 scope expansion). AC13 and AC15 explicitly codify this exception.

## 6. Phase 3 handoff contract

Phase 3 (Senior Developer Review) should verify:

1. Run `bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh all`. Expect exit 0, `PASS: task1 … PASS: task6 … PASS: all`, exactly 7 `^PASS:` lines.
2. Run the full nine-harness regression per §2. Expect exit 0 / fingerprint 1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 (total 42 `^PASS:` lines).
3. Verify `git diff` scope is: seven new `memory/.obsidian/*.json` files + four new evidence files under `tests/` + this handoff file + `sprint-status.yaml` two-value edit (`3-2-...status` + `last_updated`) + this story file (Dev Agent Record / Change Log / File List / checkboxes) + the single-line `story-1-1-scaffold-validation.sh` line-155 allowlist extension. Any other file change is a regression.
4. Verify the `templates.json` REPAIR: `grep -F '_templates' memory/.obsidian/templates.json` must return empty.
5. Verify `workspace.json` absence: `[[ ! -f memory/.obsidian/workspace.json ]]`.
6. Verify no Derek / Bobby / RevivaGo / gtd-life / meeting-slug content leaked into any ported file (the harness `check_task4` gate does this; also reproducible with the manual smoke commands in the story `### Testing Notes` section).
7. On approval, Phase 4 flips `3-2-portable-obsidian-config.status` `review → done` and may also flip `epic-3.status` if Story 3.3 ships together; otherwise `epic-3.status` remains `in-progress` until 3.3 lands.

Story 3.2 is complete and ready for review.
