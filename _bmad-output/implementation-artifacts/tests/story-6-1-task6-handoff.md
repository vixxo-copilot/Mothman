# Story 6.1 Task 6 Handoff

**Story:** 6.1 — Write shared PII deny-list config
**Phase:** 2 (Dev handoff to review)
**Date:** 2026-04-21
**Agent:** Amelia (Senior Software Engineer) — Task 6
**Scope:** Regression transcript + evidence summary + zero-edit verification + Story 6.2 forward notes

---

## AC-to-evidence map

One row per acceptance criterion AC1–AC11. Each row names the harness gate and/or filesystem evidence that proves the AC is satisfied.

| AC  | Claim                                                                 | Evidence                                                                                                                                                                                                                 |
| --- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AC1 | `.github/pii-denylist.txt` exists, tracked, non-empty, LF-only, trailing `0x0a` | Story 6.1 harness `task3` (`PASS: task3`). File present: `.github/pii-denylist.txt` (2,669 bytes, SHA-256 `b5b11a2c9d7da38308a9f8a1e95de5e89eb2111d2aa3a9e3ff7663bb434d681c`). `git ls-files .github/pii-denylist.txt` returns the path. |
| AC2 | File-format contract (comments / blanks / literal-substring pattern lines; no tabs; ≤200 B; category headers `# === CATEGORY: <name> ===`; opening header comment block) | Story 6.1 harness `task3` gate (line-length ≤ 200 B check via `awk 'length > 200'`, no-tab check, no-trailing-space check, category-header `grep -c '^# === CATEGORY: ' = 6`). |
| AC3 | Six canonical category sections in canonical order; required Names / Businesses / Blog / Scope-Words tokens; marker-comment + sentinel approach for Home Address / Family | Story 6.1 harness `task3` gate (awk line-walk verifies `EXPECTED_CATEGORIES=( Names 'Home Address' Family Businesses 'Blog & Public Content' 'Personal Scope Words' )` in order; per-category token presence via `grep -Fq`). |
| AC4 | 17-token Story-3.x banned-term lock preserved as a UNION across sections; 12-token Story-3.3 defense-in-depth set also present | Story 6.1 harness `task4` gate (iterates `CANONICAL_17_TOKENS` via case-folded `grep -Fiq` against `.github/pii-denylist.txt`; iterates defense-in-depth fixed-string set via `grep -Fq`). |
| AC5 | File contains ZERO raw home addresses, ZERO five-digit zips, ZERO phone numbers, ZERO `@` chars, ZERO minor children's names; `# SAFE-TO-PUBLISH deny-list` sentinel present | Story 6.1 harness `task4` gate (runs AC5 negative-scan probes against stripped pattern-lines stream: street regex → 0, zip regex → 0, phone regex → 0, `@` → 0). Harness `task3` verifies `SAFE_PUBLISH_SENTINEL` presence. |
| AC6 | Header comment block contains five labeled sections: `# Purpose:`, `# CI contract:`, `# How to extend:`, `# Mirror:`, `# Safe-to-publish policy:` | Story 6.1 harness `task3` gate (iterates `HEADER_LABELS=( '# Purpose:' '# CI contract:' '# How to extend:' '# Mirror:' '# Safe-to-publish policy:' )` via `grep -Fq`). |
| AC7 | Deterministic harness wired into harness family at `story-6-1-pii-denylist-validation.sh`; shebang + `set -euo pipefail`; six gates + `all`; exits 0 with exactly 7 `^PASS:` lines in `all` mode | Full transcript below: `PASS: task1` … `PASS: task6` `PASS: all` (7 lines). Harness is `chmod 0755`, present at `_bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh` (27,149 bytes). Harness `task5` self-checks shebang + `set -euo pipefail` + all case arms + all constants + `declare -F regex_self_probe`. |
| AC8 | Ten-predecessor regression gate passes; per-harness `^PASS:` fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7` | Story 6.1 harness `task6` gate invokes each predecessor in `all` mode, captures stdout+stderr, asserts exit 0, and compares `grep -c '^PASS:'` against `REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )`. Passed at 2026-04-21 run (see transcript). |
| AC9 | `docs/pii-denylist.md` exists, UTF-8 / LF / trailing newline / non-empty, seven H2 sections in canonical order | Story 6.1 harness `task3` gate verifies `DOC_PATH` existence and all seven H2 section headers. File present: `docs/pii-denylist.md` (7,432 bytes, SHA-256 `4de2874854705535e68bc7ec2e384a91a62d1c4313932d3ee22c28a198d4f3d4`). `grep -c '^## ' docs/pii-denylist.md` returns `7`. |
| AC10 | `README.md` contains a one-line reference to both `.github/pii-denylist.txt` and `docs/pii-denylist.md`; no prior bytes rewritten; line count does not decrease | Story 6.1 harness `task3` gate: `grep -Fq '.github/pii-denylist.txt' README.md` AND `grep -Fq 'docs/pii-denylist.md' README.md`. README grew from 814 B → 960 B (net +146 B, +1 line); see "Zero-edit verification" below for the Story-3.3 drift reconciliation. |
| AC11 | `sprint-status.yaml` reflects `6-1-…status: backlog → ready-for-dev → review`, `epic-6.status: backlog → in-progress`, `last_updated: 2026-04-21`; no other story regressed | Verified by inspection of `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 flip). Not gated by the Story 6.1 harness itself (sprint-status is out-of-scope for file-shape verification); gated by Task 7 instructions and manual review. |

---

## Full validation command transcript

The Story 6.1 harness `all` gate internally invokes all ten predecessor harnesses (`task6` regression gate) AND the Story 6.1 gates `task1`–`task5`. Running the Story 6.1 harness in `all` mode therefore proves the full 11-harness chain passes. Below is the captured transcript from a clean invocation at 2026-04-21.

### Command

```bash
bash _bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh all
```

### stdout

```
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
```

### Exit code

```
0
```

### Fingerprint

- 7 total `^PASS:` lines (matches AC7 contract: `task1`→`task6` + `all`).
- Exit 0.
- Runtime: ~5.5 minutes on a developer laptop (the `task6` regression gate invokes the ten predecessor harnesses serially).

### Individual predecessor harness fingerprints (captured by `task6`)

The `task6` gate invokes each of these commands, asserts exit 0, and asserts `grep -c '^PASS:'` equals the positional entry in `REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )`. Success of the Story 6.1 harness `all` gate is proof that every fingerprint below matched.

| # | Command                                                                                   | Expected `^PASS:` count |
| - | ----------------------------------------------------------------------------------------- | ----------------------- |
| 1 | `bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all`                      | 1                       |
| 2 | `bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all`                    | 1                       |
| 3 | `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all`                  | 1                       |
| 4 | `bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all`                | 1                       |
| 5 | `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all`      | 10                      |
| 6 | `bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all`                  | 7                       |
| 7 | `bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all`           | 7                       |
| 8 | `bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh all`          | 7                       |
| 9 | `bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh all`               | 7                       |
| 10 | `bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh all`          | 7                       |

All ten predecessor harnesses exited `0` with `PASS: all` and matched their expected `^PASS:` line-count fingerprints. Per the Story 6.1 task-6 instructions, serial invocation of each predecessor harness individually was deferred to the Story 6.1 `task6` regression gate (which invokes them under `2>&1` capture and enforces both exit code AND pass-count fingerprint); that gate's `PASS: task6` emission is authoritative.

---

## Byte-counts and SHA-256 checksums

Measured 2026-04-21 via `wc -c <path>` and `shasum -a 256 <path>`.

| File                                                                                            | Bytes  | SHA-256                                                            |
| ----------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------ |
| `.github/pii-denylist.txt`                                                                      | 2,669  | `b5b11a2c9d7da38308a9f8a1e95de5e89eb2111d2aa3a9e3ff7663bb434d681c` |
| `docs/pii-denylist.md`                                                                          | 7,432  | `4de2874854705535e68bc7ec2e384a91a62d1c4313932d3ee22c28a198d4f3d4` |
| `_bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh`              | 27,149 | `853a7a6096e3dfcf201843176361a10c0a183f980aadb2d97a21659e0f73062f` |
| `_bmad-output/implementation-artifacts/tests/story-6-1-baseline-audit.md`                       | 29,533 | `51559d0bbaa8b211b4950ac25ee443618471205906790cff2cde4ed0d9d31d2e` |
| `_bmad-output/implementation-artifacts/tests/story-6-1-canonical-blueprint.md`                  | 37,705 | `294d9feca01c6c588102052ad8aaa0f26f5cc98c5117eb7184eb2462629c9cb9` |

Reproduce locally:

```bash
for f in \
  .github/pii-denylist.txt \
  docs/pii-denylist.md \
  _bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh \
  _bmad-output/implementation-artifacts/tests/story-6-1-baseline-audit.md \
  _bmad-output/implementation-artifacts/tests/story-6-1-canonical-blueprint.md; do
  wc -c "$f"; shasum -a 256 "$f";
done
```

---

## Zero-edit verification

`git diff --stat origin/main -- <harness>` run on each of the ten predecessor harnesses at 2026-04-21. Nine are byte-stable; one has a deliberate 1-line drift reconciliation explained below.

| # | Predecessor harness                                                                                     | Bytes  | Diff vs `origin/main`         |
| - | -------------------------------------------------------------------------------------------------------- | ------ | ----------------------------- |
| 1 | `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh`                           | 6,215  | (no change)                   |
| 2 | `_bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh`                         | 6,712  | (no change)                   |
| 3 | `_bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh`                       | 7,194  | (no change)                   |
| 4 | `_bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh`                     | 15,697 | (no change)                   |
| 5 | `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh`           | 33,598 | (no change)                   |
| 6 | `_bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh`                       | 31,054 | (no change)                   |
| 7 | `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh`                | 14,458 | (no change)                   |
| 8 | `_bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh`               | 32,767 | (no change)                   |
| 9 | `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh`                    | 30,494 | (no change)                   |
| 10 | `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh`              | 40,661 | **1 file changed, 1 insertion(+), 1 deletion(-)** |

### Story-3.3 deliberate 1-line drift reconciliation

One predecessor harness was deliberately updated by a single byte-reconciliation change during Story 6.1 Task 5:

```diff
--- a/_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh
+++ b/_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh
@@ -258,7 +258,7 @@ AC12_STABLE_BYTES=(
   1048
   1048
   772
-  814
+  960
   667
   51
 )
```

**Context.** Story 3.3's `AC12_STABLE_BYTES` array encodes the expected byte count for each file in `AC12_STABLE_FILES`. Index 9 of that array corresponds to `README.md`. Story 3.3 locked the README at 814 bytes to guarantee later stories would not reflow or rewrite existing README prose.

**Conflict.** Story 6.1 AC10 REQUIRES adding a one-line reference to `.github/pii-denylist.txt` and `docs/pii-denylist.md` inside `README.md`. That addition grew the README from 814 B to 960 B (net +146 B, exactly one new line under `## Help`). Without the `AC12_STABLE_BYTES[9]` update, the Story 3.3 harness would fail — blocking Story 6.1's own `task6` regression gate in a deadlock.

**Resolution.** Story 6.1 AC10 and Story 3.3 AC12 are resolved in favor of AC10 (the newer, explicit requirement to reference the guardrail files from the README) and the `AC12_STABLE_BYTES` entry was updated `814 → 960` to absorb the AC10-required growth. This is the MINIMAL possible edit to the predecessor harness: one numeric literal changed, no logic altered, no assertions relaxed. The spirit of Story 3.3 AC12 (the README must not be REWRITTEN; existing prose must be byte-stable) is preserved because:

1. The existing 814 bytes of `README.md` content are byte-stable (no reflow, no prose edits, no section removal).
2. The growth is strictly additive: one new bullet point appended under `## Help`.
3. Any future Story 6.x or later that adds another README line will incur the same single-literal adjustment, which is the correct lifecycle for a stable-byte invariant that evolves by explicit-addition.

**Rationale citation.** Story 3.3 Dev Notes anticipated exactly this scenario: future stories that ADD README content must bump the stable-byte literal rather than reverting the README addition. Story 6.1 follows that guidance.

**Net zero-edit posture.** All other nine predecessor harnesses remain byte-identical to `origin/main`. No other predecessor artifact under `.cursor/rules/`, `agents/personas/`, `memory/`, `.obsidian/`, or the root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `LICENSE`, `.gitignore`) was touched by Story 6.1.

---

## Forward-looking notes for Story 6.2

Story 6.2 builds the GitHub Action that consumes `.github/pii-denylist.txt` and blocks PRs introducing banned tokens. Story 6.1 fixes the contract; the notes below capture the exact exclusion set, loading strategy, and boundary-guard wrapping that Story 6.2's workflow should adopt.

### Pattern loading strategy

```bash
# Load non-comment, non-blank lines as banned patterns.
mapfile -t PATTERNS < <(grep -vE '^(#|$)' .github/pii-denylist.txt)
```

- `grep -vE '^(#|$)'` drops comment lines (leading `#`) and empty lines in a single POSIX-ERE pass.
- Result: one literal substring per array element.
- Expected pattern count at the time of Story 6.1 handoff: ~29 patterns (17 canonical + 12 Story-3.3 defense-in-depth, distributed across six categories, minus the two fork-local sentinels which are audit anchors not real tokens — see AC3 rationale in the story file).

### POSIX-ERE boundary-guard wrapping

For each pattern `P` loaded above, Story 6.2's scanner constructs the regex at runtime:

```
(^|[^A-Za-z])P($|[^A-Za-z])
```

- Prevents false positives on compounds (`homepage` must not match `home`, `family-friendly` must not match `family`).
- Works identically on BSD grep (macOS), GNU grep (Linux / `ubuntu-latest`), and busybox/Alpine grep — verified by the ten predecessor harnesses that use the same construction inline.
- Does NOT rely on `\b`, `\<`, `\>`, or Perl-compatible regex. No `-P` flag is required or permitted.
- Scan is case-insensitive: use `grep -riE`.

### Exclusion set (directories and files the scan MUST skip)

| Path or pattern                                                     | Rationale                                                                                                                                              |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `.git/`                                                             | Version control metadata; never scanned.                                                                                                               |
| `.github/pii-denylist.txt`                                          | The deny-list itself — it literally contains every banned pattern by design and must never match itself.                                               |
| `docs/pii-denylist.md`                                              | The human-facing policy doc enumerates deny-list categories and tokens as worked examples; matches here are audit evidence, not PII leaks.             |
| `_bmad-output/implementation-artifacts/**/*.md`                     | BMAD story files (e.g. `3-3-seed-empty-identity-and-preferences.md`, `6-1-write-shared-pii-denylist-config.md`) enumerate banned tokens as audit evidence. |
| `_bmad-output/implementation-artifacts/**/*.sh`                     | Validation harnesses embed banned-term regex inline (the exact inversion of the deny-list — harness code MUST contain the tokens it scans for).         |
| `_bmad/**`                                                          | BMAD module internals (config, workflows, tasks) — upstream framework; not application content and not Vixxo-authored.                                  |
| `node_modules/`                                                     | If present (skill-bundle install artifacts); never scanned.                                                                                            |

Implementation sketch:

```bash
grep -riE \
  --exclude-dir=.git \
  --exclude-dir=_bmad \
  --exclude-dir=node_modules \
  --exclude='.github/pii-denylist.txt' \
  --exclude='docs/pii-denylist.md' \
  --exclude='_bmad-output/implementation-artifacts/*.md' \
  --exclude='_bmad-output/implementation-artifacts/tests/*.md' \
  --exclude='_bmad-output/implementation-artifacts/tests/*.sh' \
  --exclude='_bmad-output/implementation-artifacts/*.sh' \
  -- "${GUARDED_REGEX}" .
```

(Story 6.2 Dev will finalize exact `--exclude` / `--exclude-dir` syntax; the above is directional.)

### Self-match guard

The deny-list file itself MUST be excluded from the scan. Story 6.1 enforces a precondition (`# SAFE-TO-PUBLISH deny-list` sentinel lives ONLY in the header comment block, never in a pattern line) via the Story 6.1 harness `task4` anti-self-match guard:

```bash
grep -vE '^(#|$)' "${DENYLIST_PATH}" | grep -Fq 'SAFE-TO-PUBLISH'  # expected: exit 1 (no match)
```

Story 6.2 should likewise assert this invariant in its workflow pre-flight — a trivial sanity check that catches accidental insertions of sentinels into pattern lines.

### Performance budget

Epic 6 Story 6.2 AC stipulates the workflow must complete in under 30 seconds. With ~29 patterns, the simplest implementation (one `grep -riE` per pattern) scans the tree ~29 times. On a shallow repo like `assistants-template`, each scan completes in well under one second; the 29-pattern total stays comfortably within budget. If Story 6.2 needs faster scans for larger consumer forks, the patterns can be joined with `|` into a single POSIX-ERE alternation:

```
((^|[^A-Za-z])(derek|neighbors|revivago|…)($|[^A-Za-z]))
```

This is the recommended optimization and is POSIX-ERE compatible.

### Additional Story 6.2 considerations

- **Workflow trigger:** `pull_request` on all branches targeting `main`, with `paths-ignore` for the same exclusion set above (defense-in-depth; skip the workflow entirely for PRs that only touch excluded paths).
- **Failure output:** Story 6.2's workflow should print the offending file + line number + matched pattern (not the full literal context, which could itself leak PII from a bad PR). Example: `FAIL: src/app.ts:42 matched banned pattern 'derek' (category: Names)`.
- **Fork-local override (optional, not required for Story 6.2 MVP):** If `.github/pii-denylist.local.txt` exists, Story 6.2 could union its patterns into the scan. Gitignored by convention; consumer-fork-local. Out of scope for Story 6.2 MVP per Story 6.1 Dev Notes.
- **No per-repo or per-user PII ever committed.** Story 6.2's workflow, like Story 6.1's deny-list, must remain safe-to-publish.

---

## Handoff checklist

- [x] Story 6.1 harness `all` run passed — 7 `^PASS:` lines, exit 0.
- [x] Ten-predecessor regression asserted by `task6` gate with fingerprint `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`.
- [x] Byte counts and SHA-256 checksums captured for all five Story 6.1 artifacts.
- [x] Zero-edit verification captured for all ten predecessor harnesses; one deliberate 1-line drift documented with rationale.
- [x] Forward-looking Story 6.2 notes captured (exclusion set, pattern loading, boundary-guard wrapping, performance budget).
- [x] This handoff artifact committed at `_bmad-output/implementation-artifacts/tests/story-6-1-task6-handoff.md`.

Story 6.1 is ready for Phase 3 review.
