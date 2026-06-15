# Story 3.1 Task 6 Handoff Package

**Story:** 3.1 — Port `_template.md` and `_template/` trees from gtd-life memory
**Phase:** 2 — Dev handoff
**Date:** 2026-04-20
**Author:** Amelia (Senior Software Engineer, autonomous Dev subagent, wave-3 resumed)
**Sprint-status entry:** `3-1-port-template-trees-from-gtd-life-memory`
**Linear ID:** AIP-31

This handoff package certifies that Story 3.1 is implementation-complete and ready for Phase 3 code review. It collects the AC-to-evidence map, the full validation command transcript, per-file byte counts + SHA-256 checksums for drift detection, forward-looking notes for downstream stories, and an explicit zero-edit verification that no prior-story artifact was mutated by Story 3.1 (with one explicitly-scoped integration exception documented below).

## 1. AC-to-evidence map

Each acceptance criterion maps to a harness gate, file path, or direct scan command that proves it. All `grep` / `find` / `awk` / harness invocations below are reproducible from the repo root.

| AC | Summary | Evidence |
|---|---|---|
| AC1 | `memory/meetings/_template/` bundle exists with four files | Harness `check_task3` (`_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh task3`) asserts all four files exist, are non-empty, have trailing newlines, have frontmatter-delimited YAML in `meeting.md`, and contain the required H1/H2 headings + doc-link table cells (`[prep.md](prep.md)`, `[agenda.md](agenda.md)`, `[transcript.md](transcript.md)`). See also `ls memory/meetings/_template/` → `agenda.md meeting.md prep.md transcript.md`. |
| AC2 | `memory/people/_template.md` has canonical person-note shape | Harness `check_task3` verifies 9 frontmatter keys in order (`type, company, role, email, last_1on1, open_action_items, created, updated, tags`), H1 `# {{Name}}`, H2 sections `## Overview` / `## 1-on-1 History` / `## Action Items` / `## Notes`, and the four bold-label lines (`**Company**`, `**Role**`, `**Reports to**`, `**Direct reports**`). |
| AC3 | `memory/decisions/_template.md` has canonical decision-note shape | Harness `check_task3` verifies 8 frontmatter keys in order (`type, status, date, context, stakeholders, created, updated, tags`), H1 `# {{Decision Title}}`, H2 sections `## Context`, `## Alternatives`, `## Decision`, `## Rationale`, `## Implications`, and H3 sub-sections `### Option A: {{name}}` / `### Option B: {{name}}`. |
| AC4 | `memory/reference/_template.md` has canonical reference-note shape | Harness `check_task3` verifies 6 frontmatter keys in order (`type, created, updated, context, related_to, tags`), H1 `# {{Reference Title}}`, H2 sections `## Summary` / `## Details` / `## Links` / `## Related notes`. |
| AC5 | `memory/inbox/_template.md` has minimal capture shape + scrubbed context | Harness `check_task3` verifies 4 frontmatter keys (`type, created, context, tags`), H1 `# Thought`, and (Defect #3 repair) the presence of `context: ""` (empty-string) instead of the gtd-life source's `context: vixxo | revivago | personal` personal-enumeration value. |
| AC6 | `memory/appreciations/_template.md` has well-formed frontmatter + body | Harness `check_task3` verifies (Defect #1 repair) that the file does NOT contain `## type: appreciation` as an H2 heading, that frontmatter is opened by `---` on line 1 and closed by `---` on line 7, that keys `type, date, recipient, context, tags` appear in order, and that body contains H1 `# {{Recipient or Moment}}` + H2 sections `## What` and `## Why it mattered`. |
| AC7 | Zero Derek / RevivaGo / personal content in any ported file | Harness `check_task4` runs the boundary-guarded banned-term regex `(^\|[^A-Za-z])(derek\|neighbors\|revivago\|benji\|flowtopic\|gtd-life\|gtdlife\|wyoming\|cheyenne\|family\|home\|blog\|wife\|son\|daughter\|dog)($\|[^A-Za-z])` (case-insensitive via `grep -iE`) across all nine ported files → 0 hits. Also `grep -Fq 'gtd-life'` path-reference scan across all nine files → 0 hits. |
| AC8 | Placeholder vocabulary is `{{...}}` only + on the allowlist | Harness `check_task4` extracts all `{{...}}` tokens via `grep -oE '\{\{[^}]+\}\}'` and asserts every token appears on the 17-entry allowlist (`{{Meeting Title}}, {{Name}}, {{topic}}, {{owner}}, {{estimated minutes}}, {{person}}, {{action}}, {{date}}, {{company}}, {{role}}, {{manager or "N/A"}}, {{count or "N/A"}}, {{Decision Title}}, {{Reference Title}}, {{Recipient or Moment}}, {{action item}}, {{name}}`). Additional probes assert zero single-brace `{x}`, zero angle-bracket `<x>`, zero percent-wrapped `%x%`, zero shell-interpolation `${x}`, and zero `{{employee_*}}` identity-placeholder leakage. |
| AC9 | `.gitkeep` sentinels handled correctly | `memory/.gitkeep` remains at byte-count 0 (Story 1.1 byte-for-byte identity). No `.gitkeep` added to the six new subdirectories (`memory/meetings/`, `people/`, `decisions/`, `reference/`, `inbox/`, `appreciations/`) — each contains `_template.md` content-bearing files which provide git-trackable content. Verify with `find memory -name '.gitkeep'` → single `memory/.gitkeep` hit. |
| AC10 | Harness exists and is wired into the test-harness family | File `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh` exists, is executable (`-rwxr-xr-x`), uses `#!/usr/bin/env bash` + `set -euo pipefail`, implements gates `task1`–`task6` + `all`, uses only `bash` / `grep` / `find` / `awk` / `sed` / shell built-ins (no `rg`, no Python), implements `regex_self_probe` exercising `derek`/`derekson` + `family`/`familial` + placeholder-form probes, and is BSD-grep + GNU-grep compatible. `check_task5` is the self-check gate. |
| AC11 | Regression runs all predecessor harnesses cleanly | See the full command transcript in §2 below. All 8 harnesses (Story 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1) exit `0` with `PASS: all`. Zero bytes changed in six of the seven predecessor harnesses; one documented one-line integration fix was applied to the Story 1.1 harness memory-allowlist in main context — see §5 below for the rationale. No edits to `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files, `agents/personas/work.md`, root context files, `README.md`, `LICENSE`, `.gitignore`, or `memory/.gitkeep`. |
| AC12 | Sprint tracker lifecycle transition | Story entry `3-1-port-template-trees-from-gtd-life-memory.status` transitions `backlog → ready-for-dev → review` across Phases 1 and 2 (Phase 1 flip applied at SM pass; Phase 2 flip applied by this handoff commit). `epic-3.status` transitions `backlog → in-progress` at Phase 1. `last_updated` set to `2026-04-20`. Zero other status values regressed; all comments and entry ordering preserved byte-for-byte. |
| AC13 | Additive-only scope; no creep into 3.2 / 3.3 | File List (story file, §File List) enumerates exactly the nine memory template files + three evidence artifacts under `tests/` + this handoff document + the harness + this story file + `sprint-status.yaml`. No `.obsidian/` config (3.2). No `memory/me/identity.md` / `preferences.md` (3.3). No `memory/companies/` / `memory/daily/` / `memory/blog-ideas/` / `memory/vixxo/`. No edits under `.cursor/` / `agents/` / `bin/` / `scripts/` / `docs/` / repo root (outside the documented Story 1.1 harness integration fix). |

## 2. Full validation command transcript

All 8 harnesses were re-run at Phase 2 handoff from the repo root after the Story 1.1 memory-allowlist integration fix was applied in main context. Each harness exited zero with `PASS: all`.

```
$ for h in story-1-1-scaffold-validation.sh \
           story-1-2-root-files-validation.sh \
           story-1-3-root-context-validation.sh \
           story-2-1-agent-identity-validation.sh \
           story-2-2-guardrail-and-formatting-validation.sh \
           story-2-3-work-persona-validation.sh \
           story-2-4-benji-inbox-absence-validation.sh \
           story-3-1-memory-template-tree-validation.sh; do
    echo "=== Running: $h ==="
    bash _bmad-output/implementation-artifacts/tests/$h all
    echo "  exit=$?"
  done

=== Running: story-1-1-scaffold-validation.sh ===
PASS: all
  exit=0
=== Running: story-1-2-root-files-validation.sh ===
PASS: all
  exit=0
=== Running: story-1-3-root-context-validation.sh ===
PASS: all
  exit=0
=== Running: story-2-1-agent-identity-validation.sh ===
PASS: all
  exit=0
=== Running: story-2-2-guardrail-and-formatting-validation.sh ===
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: task7
PASS: task8
PASS: task9
PASS: all
  exit=0
=== Running: story-2-3-work-persona-validation.sh ===
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
  exit=0
=== Running: story-2-4-benji-inbox-absence-validation.sh ===
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
  exit=0
=== Running: story-3-1-memory-template-tree-validation.sh ===
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
  exit=0
```

The Story 3.1 harness's own `task6` regression gate — which invokes all seven predecessor harnesses internally — also exits `0` with `PASS: task6` as shown above, confirming the regression chain is healthy end-to-end.

## 3. Byte counts and SHA-256 checksums (drift detection)

Recorded from the repo root on 2026-04-20. Use this table to detect any future drift in the ported template files.

| File | Bytes | SHA-256 |
|---|---|---|
| `memory/meetings/_template/meeting.md` | 828 | `945b583beaf93febf1668e27092716d9a57ce7705f75f53b55c87c09d4cded41` |
| `memory/meetings/_template/agenda.md` | 250 | `9227b56a4d53bf16fff3b285ed96499da6d0a08486bc808b00ff2be63d45468c` |
| `memory/meetings/_template/prep.md` | 513 | `6826a6b59dc912df88b04996ced6f272a6c7d593a50f8a00870a54a291125a9e` |
| `memory/meetings/_template/transcript.md` | 306 | `bc907c346398c7befbe092887357562e512a64bd36644032b26c7d2349c640d7` |
| `memory/people/_template.md` | 561 | `a7891249a642d33b0c7f61d563ce945c2a3fb8630ce0b39d2c1c13ce51a44160` |
| `memory/decisions/_template.md` | 588 | `a2f3cbf4ec4fa9b5a987ca70d426e2f8642afd3f306fd3047db1597fe2b98601` |
| `memory/reference/_template.md` | 506 | `0b289b578647eeeb01c64254d70947b78a7d14aca629721c6f43136f8f431044` |
| `memory/inbox/_template.md` | 72 | `1863a74e435b75ee618327eadc958e5de32b77be529565a660a0c01eafdc179e` |
| `memory/appreciations/_template.md` | 211 | `5f0393cc4ac33fe6d9852a6724fac632c2d6c6e65f1899a049a1d6a3a34c605d` |

Reproduce via:

```
for f in memory/meetings/_template/meeting.md \
         memory/meetings/_template/agenda.md \
         memory/meetings/_template/prep.md \
         memory/meetings/_template/transcript.md \
         memory/people/_template.md \
         memory/decisions/_template.md \
         memory/reference/_template.md \
         memory/inbox/_template.md \
         memory/appreciations/_template.md; do
    bytes=$(wc -c < "$f" | tr -d ' ')
    sha=$(shasum -a 256 "$f" | awk '{print $1}')
    printf '%s  %s  %s\n' "$bytes" "$sha" "$f"
  done
```

## 4. Forward-looking notes (downstream-story integration points)

- **Story 3.2 (`.obsidian/` portable config)** will reference these nine template file paths in its Obsidian Templates-plugin configuration. The paths `memory/meetings/_template/{meeting,agenda,prep,transcript}.md`, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md` are now stable and should not be renamed. The appreciations-template defect is REPAIRED in Story 3.1; Story 3.2's Templates-plugin config can trust that `appreciations/_template.md` contains properly-formed YAML frontmatter.
- **Story 3.3 (seed `memory/me/identity.md` + `preferences.md`)** will create the `memory/me/` subdirectory. The Story 3.1 harness does not assert absence of `memory/me/` (it only asserts the six Story-3.1-scoped subdirectories have correct shape). The Story 1.1 harness's memory allowlist (`me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations`) already admits `me` as a valid subdir, so Story 3.3 can land without further allowlist edits.
- **Epic 4 Story 4.1 (`.cursor/mcp.json`)** references `memory/people/` and `memory/meetings/` in persona Available-MCP context without needing template edits. Story 3.1's placeholder discipline (`{{Name}}`, `{{Meeting Title}}`, etc.) is orthogonal to the identity-placeholder discipline (`{{employee_name}}`, `{{employee_role}}`) owned by Stories 2.1 / 2.3 / 3.3.
- **Epic 5 Story 5.2 (wizard)** will WRITE to `memory/me/identity.md` (Story 3.3 territory) and may fill in placeholders in `memory/meetings/_template/` bundle files during onboarding. The placeholder allowlist in the Story 3.1 blueprint is the source of truth for which placeholder tokens the wizard may substitute.
- **Epic 6 Story 6.2 (GitHub Action — CI gate)** can invoke `bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh all` directly as a PR-blocking CI gate. The harness is GitHub-Actions-native: exits `0` on pass, `1` on fail, emits single-line `PASS:` / `FAIL:` markers that parse cleanly in GitHub's log renderer.
- **Future drift detection:** the SHA-256 table in §3 is the canonical checksum snapshot for drift detection. Any future story that edits any of the nine template files must update §3 via an explicit story-scoped change; the CI gate from 6.2 should capture drift automatically via its `task3` shape gate.

## 5. Zero-edit verification (predecessor artifacts)

Story 3.1 is additive-only with one scoped integration exception documented in §6. Every prior-story artifact listed below was verified present, non-empty, and structurally intact at the end of Story 3.1's Phase 2 handoff.

**Seven predecessor harnesses (Story 1.1 has a one-line integration fix; the other six are byte-for-byte stable):**

| Harness | Bytes | Status |
|---|---|---|
| `tests/story-1-1-scaffold-validation.sh` | 6204 | **Modified** — one-line integration fix (see §6). |
| `tests/story-1-2-root-files-validation.sh` | 6712 | Unchanged. |
| `tests/story-1-3-root-context-validation.sh` | 7194 | Unchanged. |
| `tests/story-2-1-agent-identity-validation.sh` | 15697 | Unchanged. |
| `tests/story-2-2-guardrail-and-formatting-validation.sh` | 33598 | Unchanged. |
| `tests/story-2-3-work-persona-validation.sh` | 31054 | Unchanged. |
| `tests/story-2-4-benji-inbox-absence-validation.sh` | 14458 | Unchanged. |

**Identity + rule + persona + context files (all unchanged):**

- `.cursor/rules/agent-identity.mdc` (Story 2.1)
- `.cursor/rules/outbound-messaging-guardrail.mdc` (Story 2.2)
- `.cursor/rules/memory-vault-protection.mdc` (Story 2.2)
- `.cursor/rules/teams-dm-formatting.mdc` (Story 2.2)
- `.cursor/rules/email-triage-thread-defaults.mdc` (Story 2.2)
- `agents/personas/work.md` (Story 2.3)

**Root context + metadata (all unchanged):**

- `AGENTS.md`, `CLAUDE.md`, `.cursorrules` (Story 1.3)
- `README.md`, `LICENSE`, `.gitignore` (Story 1.2)
- `memory/.gitkeep` (Story 1.1 — byte-count 0, byte-for-byte identity)

Reproduce via `git diff HEAD --stat -- .cursor/rules/ agents/personas/ AGENTS.md CLAUDE.md .cursorrules README.md LICENSE .gitignore memory/.gitkeep` (expected: no output, i.e. zero diffs).

## 6. Story 1.1 harness integration fix (documented exception)

**Context.** Story 3.1's regression gate initially failed because the Story 1.1 scaffold-validation harness's `check_task6` memory-allowlist regex (`^(\.gitkeep|.+\.md|me|mcp|obsidian)$`) did not admit the six new Story-3.1 memory subdirectories (`meetings`, `people`, `decisions`, `reference`, `inbox`, `appreciations`). This produced `FAIL: Unexpected non-scaffold content in memory: ...` when the Story 1.1 harness was invoked against a repo containing Story 3.1's additions.

**Resolution.** Following the Story 2.1 precedent (commit `0db273b` amended the same Story 1.1 harness's memory-allowlist to admit `me|mcp|obsidian` in anticipation of Epic 3 subdirs), the orchestrator applied a one-line integration fix in main context that extends the allowlist with the six Story-3.1-scoped subdir names. Diff:

```
-        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian)$' || true)"
+        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian|meetings|people|decisions|reference|inbox|appreciations)$' || true)"
```

**Classification.** This is an orchestrator-applied integration fix, not a Story 3.1 scope expansion. Story 3.1's creates-only scope (AC13) is unchanged. The Story 1.1 harness edit follows the established pattern from Story 2.1 of amending the scaffold-validation allowlist when a downstream story legitimately adds a new subdirectory under `memory/`. Both the amended Story 1.1 harness and the new Story 3.1 harness now pass cleanly in the full 8-harness regression suite.

**Post-fix verification.** The full regression suite (§2) passes; every other predecessor harness remains byte-for-byte stable; the Story 3.1 harness's `task6` gate (which invokes Story 1.1 as one of its seven sub-harnesses) also passes cleanly. The AC11 text about "zero bytes changed in any of those seven prior harnesses" is technically modulo this one-line integration fix — same precedent as Story 2.1's handoff relative to the Story 1.1 allowlist. Future Epic-3 / Epic-4 stories that add new subdirs under `memory/` should extend the same allowlist in the same pattern.

## 7. Ready-for-review certification

Story 3.1 is implementation-complete at Phase 2 Dev handoff:

- All 9 template files exist with correct shapes, zero banned tokens, zero gtd-life path references, and placeholder vocabulary confined to the `{{...}}` allowlist.
- The Story 3.1 validation harness exists, is executable, implements all 6 gates + `all` dispatcher, and passes in both isolated and regression invocation.
- The full 8-harness regression suite passes cleanly (exit 0, `PASS: all` on every harness).
- No prior-story artifact was mutated, with the sole documented exception of the Story 1.1 harness's one-line memory-allowlist extension (applied in main context, following the Story 2.1 precedent).
- The sprint tracker has been transitioned `ready-for-dev → review` for the story entry, `epic-3.status` remains `in-progress` (first-story-opens-epic rule applied at Phase 1), and `last_updated` is `2026-04-20`.
- Evidence artifacts (`story-3-1-baseline-audit.md`, `story-3-1-canonical-blueprint.md`, `story-3-1-task6-handoff.md` — this file) are in place under `_bmad-output/implementation-artifacts/tests/`.

Ready for Phase 3 Senior Developer Review.
