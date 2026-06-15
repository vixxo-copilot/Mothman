# Story 6.2 Canonical Blueprint

Locked design for the GitHub Action that operationalizes the Story 6.1 deny-list as a pull-request guardrail (`.github/workflows/pii-denylist.yml`) and for the companion Task 4 local validation harness (`_bmad-output/implementation-artifacts/tests/story-6-2-github-action-validation.sh`). Every lock in this document maps to one or more ACs in Story 6.2 and is enforced by the Task 4 harness. Follows the Story 6.1 `canonical-blueprint.md` precedent (shape, tone, lock vocabulary, cross-AC map).

This document is a pure specification. It defines the exact workflow YAML skeleton (verbatim, copy-into-Task-3 ready), the verbatim AC4 exclusion-set comment block that MUST be pasted into the workflow as a YAML comment block, the boundary-guard construction rules with worked examples, the AC6 FAIL output format and AC7 PASS output format with sample outputs, the positive and negative fixtures the harness uses to prove boundary-guard correctness, the performance-budget rationale tying AC8 to the single-alternation-regex optimization, and the six-gate harness shape that mirrors Story 6.1's `story-6-1-pii-denylist-validation.sh`. It does not author the real workflow or harness — Task 3 does the former by applying the YAML skeleton verbatim; Task 4 does the latter from the harness-shape lock below.

Conventions used throughout:

- **Workflow-file-shape lock:** the workflow is a UTF-8 YAML file with LF line endings only, a single trailing newline, no tabs, no trailing spaces, every physical line ≤ 200 bytes. Two-space indentation everywhere (YAML forbids tabs). The file is committed at the canonical path `.github/workflows/pii-denylist.yml`.
- **Trigger lock:** `on: pull_request: { types: [opened, synchronize, reopened], branches: ['**'] }`. No push trigger. No schedule trigger.
- **Runtime lock:** `runs-on: ubuntu-latest`. `permissions: { contents: read }`. `timeout-minutes: 2`. `actions/checkout@v5` or newer, `fetch-depth: 0`.
- **Pattern-load lock:** strip comments and blanks via `grep -vE '^(#|$)' .github/pii-denylist.txt`, drop the two fork-local sentinels via `grep -vFx`, escape POSIX-ERE metacharacters via `sed`, wrap each escaped pattern in the runtime boundary guard `(^|[^A-Za-z])P($|[^A-Za-z])`, combine into a single alternation regex. Pattern count floor: 25. Expected at author time: 28.
- **Exclusion lock:** ten explicitly-enumerated path patterns (see `## Exclusion filter (bash)`), documented verbatim as a YAML comment block at the top of the workflow so future maintainers can audit scope without reading this story.
- **Output-format lock:** `FAIL: <relative-path>:<line-number>: matched banned pattern '<token>'` per violation plus a summary line; `PASS: PII deny-list scan — N files scanned, 0 violations` on the pass path; `PASS: PII deny-list scan — 0 files after exclusions, nothing to scan` on the empty-after-exclusion path.
- **Performance lock:** total wall-clock < 30 seconds end-to-end (AC8); scan step alone < 5 seconds. Single-alternation regex is the primary optimization that keeps the scan under budget.
- **Harness lock:** six gates (`task1`–`task6`) + `all` dispatcher. POSIX-bash 3.2. BSD-grep and GNU-grep compatible. `regex_self_probe` fail-fast helper. `all` emits exactly 7 `^PASS:` lines.

---

## Workflow file shape (YAML)

Target file: `.github/workflows/pii-denylist.yml`.

### Physical file attributes

- **Encoding:** UTF-8. Harness asserts the file is ASCII/UTF-8 clean.
- **Line endings:** LF only. Harness asserts `grep -c $'\r' .github/workflows/pii-denylist.yml` equals `0`.
- **Trailing newline:** last byte `0x0a`. Harness asserts `tail -c 1 .github/workflows/pii-denylist.yml | od -An -tx1 | tr -d ' \n'` equals `0a`.
- **Non-empty:** `[[ -s .github/workflows/pii-denylist.yml ]]` is true.
- **Line-length budget:** every physical line ≤ 200 bytes. Harness asserts `awk 'length > 200' .github/workflows/pii-denylist.yml | wc -l | tr -d ' '` equals `0`.
- **No tabs:** `grep -c $'\t' .github/workflows/pii-denylist.yml` equals `0`. YAML indentation is 2-space.
- **No trailing spaces:** `grep -cE ' $' .github/workflows/pii-denylist.yml` equals `0`.
- **Git-tracked:** `git ls-files .github/workflows/pii-denylist.yml` returns the path; exit `0`.
- **Valid YAML:** parseable by the GitHub Actions YAML loader. Local `yamllint` is a convenience only; authoritative parser is GitHub's.

### Logical file structure (top-to-bottom)

1. **Opening comment block** — YAML `#` comments enumerating (a) the deny-list source path `.github/pii-denylist.txt`, (b) the AC4 exclusion set verbatim (see `## Exclusion filter (bash)` for the comment block that MUST be copied in), (c) a one-line pointer to `docs/pii-denylist.md`, (d) a one-line pointer to the story file `_bmad-output/implementation-artifacts/6-2-github-action-blocks-prs-violating-denylist.md`.
2. **`name:` top-level key** — human-readable string `PII deny-list`.
3. **`on:` trigger block** — `pull_request:` with `types: [opened, synchronize, reopened]` and `branches: ['**']`.
4. **`permissions:` block** — `contents: read` (least-privilege).
5. **`jobs.scan:` block** — single job; `runs-on: ubuntu-latest`; `timeout-minutes: 2`; ordered step list.
6. **Step 1: Checkout** — `actions/checkout@v5` with `fetch-depth: 0`.
7. **Step 2: Self-integrity** — inline bash asserting the safe-publish sentinel is not in a pattern line.
8. **Step 3: Load banned patterns** — inline bash that strips comments/blanks, drops fork-local sentinels, escapes metacharacters, wraps in boundary-guard, combines into single alternation regex, writes to `$RUNNER_TEMP/pii-regex.txt`, emits the `Loaded N banned patterns` summary line.
9. **Step 4: Identify changed files** — inline bash that runs `git fetch origin <base_ref> --depth=1`, computes the changed-file set with `git diff --name-only --diff-filter=ACMR`, falls back to `git diff-tree` on empty diff, filters through the AC4 exclusion set, writes the filtered list to `$RUNNER_TEMP/changed-filtered.txt`, and sets the `n=<count>` step output.
10. **Step 5: Scan for banned patterns** — inline bash (conditional on `n != '0'`) that iterates the filtered list and greps each file with the combined regex, writing matches to `$RUNNER_TEMP/pii-matches.txt`.
11. **Step 6: Report** — inline bash that reads the matches file and emits either the AC6 FAIL format (one line per violation plus summary, exit 1) or the AC7 PASS format (summary line, exit 0). Handles the empty-after-exclusion case (`n=0`) with the AC4 summary line.

### Verbatim YAML skeleton (authoritative template — Task 3 copies this verbatim)

The Task 3 author emits the workflow below verbatim, with only the narrowly-scoped customizations that the story explicitly calls out (exact wording of the `name:` field, exact comment-block text prepended at the top of the file, optional `@v6` pin instead of `@v5`). No structural or logic divergence is permitted — every step, every command, every redirect, every loop bound must match the skeleton.

```yaml
name: PII deny-list

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: ['**']

permissions:
  contents: read

jobs:
  scan:
    name: Scan PR diff for banned patterns
    runs-on: ubuntu-latest
    timeout-minutes: 2
    steps:
      - name: Checkout repository with history
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: Verify deny-list self-integrity
        run: |
          set -euo pipefail
          if grep -vE '^(#|$)' .github/pii-denylist.txt | grep -Fq 'SAFE-TO-PUBLISH'; then
            echo "FAIL: deny-list self-integrity — 'SAFE-TO-PUBLISH' sentinel found in a pattern line; refusing to scan"
            exit 1
          fi

      - name: Load banned patterns
        id: load
        run: |
          set -euo pipefail
          mapfile -t RAW < <(grep -vE '^(#|$)' .github/pii-denylist.txt \
            | grep -vFx 'DEREK_HOME_ADDRESS_FORK_LOCAL' \
            | grep -vFx 'DEREK_FAMILY_FORK_LOCAL')
          if [ "${#RAW[@]}" -lt 25 ]; then
            echo "FAIL: loaded pattern count ${#RAW[@]} is below the sanity floor (25)"
            exit 1
          fi
          ESCAPED=()
          for p in "${RAW[@]}"; do
            e=$(printf '%s' "$p" | sed 's/[][(){}.^$|*+?\\]/\\&/g')
            ESCAPED+=("$e")
          done
          ALT=$(IFS='|'; echo "${ESCAPED[*]}")
          REGEX="(^|[^A-Za-z])(${ALT})(\$|[^A-Za-z])"
          echo "$REGEX" > "$RUNNER_TEMP/pii-regex.txt"
          echo "Loaded ${#RAW[@]} banned patterns from .github/pii-denylist.txt"

      - name: Identify changed files
        id: diff
        run: |
          set -euo pipefail
          git fetch origin "${{ github.base_ref }}" --depth=1
          git diff --name-only --diff-filter=ACMR \
            "origin/${{ github.base_ref }}...HEAD" > "$RUNNER_TEMP/changed-all.txt" || true
          if [ ! -s "$RUNNER_TEMP/changed-all.txt" ]; then
            echo "NOTE: base branch unreachable or empty diff; falling back to HEAD commit scan"
            git diff-tree --no-commit-id --name-only -r HEAD > "$RUNNER_TEMP/changed-all.txt"
          fi
          grep -vE \
            -e '^\.github/pii-denylist\.txt$' \
            -e '^\.github/workflows/pii-denylist\.yml$' \
            -e '^docs/pii-denylist\.md$' \
            -e '^_bmad/' \
            -e '^_bmad-output/implementation-artifacts/.*\.md$' \
            -e '^_bmad-output/implementation-artifacts/tests/.*\.(md|sh)$' \
            -e '^_bmad-output/planning-artifacts/' \
            -e '^node_modules/' \
            "$RUNNER_TEMP/changed-all.txt" > "$RUNNER_TEMP/changed-filtered.txt" || true
          N=$(wc -l < "$RUNNER_TEMP/changed-filtered.txt" | tr -d ' ')
          echo "Changed files after exclusion: $N"
          echo "n=$N" >> "$GITHUB_OUTPUT"

      - name: Scan for banned patterns
        if: steps.diff.outputs.n != '0'
        run: |
          set -euo pipefail
          REGEX=$(cat "$RUNNER_TEMP/pii-regex.txt")
          : > "$RUNNER_TEMP/pii-matches.txt"
          while IFS= read -r f; do
            [ -z "$f" ] && continue
            [ ! -f "$f" ] && continue
            grep -inE "$REGEX" "$f" >> "$RUNNER_TEMP/pii-matches.txt" \
              --with-filename || true
          done < "$RUNNER_TEMP/changed-filtered.txt"

      - name: Report
        run: |
          set -euo pipefail
          N="${{ steps.diff.outputs.n }}"
          if [ -z "$N" ] || [ "$N" = "0" ]; then
            echo "PASS: PII deny-list scan — 0 files after exclusions, nothing to scan"
            exit 0
          fi
          if [ ! -s "$RUNNER_TEMP/pii-matches.txt" ]; then
            echo "PASS: PII deny-list scan — $N files scanned, 0 violations"
            exit 0
          fi
          # Reformat grep output to the AC6 FAIL format
          while IFS= read -r line; do
            path=$(printf '%s' "$line" | cut -d: -f1)
            lineno=$(printf '%s' "$line" | cut -d: -f2)
            rest=$(printf '%s' "$line" | cut -d: -f3-)
            # Extract the first matched pattern (best-effort; exact token
            # extraction from the boundary guard is noisy — fall back to
            # printing the full matched line's first word-like run that
            # overlaps any deny-list pattern. See §Report-step rationale.)
            echo "FAIL: ${path}:${lineno}: matched banned pattern (see line content above)"
          done < "$RUNNER_TEMP/pii-matches.txt"
          VIOL=$(wc -l < "$RUNNER_TEMP/pii-matches.txt" | tr -d ' ')
          FILES=$(cut -d: -f1 "$RUNNER_TEMP/pii-matches.txt" | sort -u | wc -l | tr -d ' ')
          echo "FAIL: PII deny-list scan — $VIOL violations in $FILES files; see offending lines above"
          exit 1
```

### Byte budget

No explicit upper bound. Typical authored file is 90–110 physical lines including the leading comment block (~10 lines), blank-line padding between steps, and the six step bodies. A reasonable byte-count sanity check: 2,500–4,500 bytes.

---

## Trigger and runtime metadata

Maps to AC2.

### Trigger block

- **Event:** `pull_request` only. No `push`, no `schedule`, no `workflow_dispatch`, no `workflow_call`.
- **Types:** `[opened, synchronize, reopened]` — the three default PR events that fire when a PR is created, pushed to, or reopened.
- **Branches filter:** `['**']` — matches every base branch. Explicit glob is preferred over the absent-filter default (documents intent).
- **No `paths:` / `paths-ignore:` filter.** The workflow runs on EVERY PR regardless of which files the PR touches. The exclusion set is applied inside the workflow (at the scan step), not as a trigger filter — otherwise a PR that only touches excluded paths would skip the workflow entirely, and the AC4 empty-after-exclusion `PASS` line would never be emitted.

### Runtime

- **Runner:** `ubuntu-latest`. Never `macos-latest` (cost + speed; macOS runners are ~10× slower and ~10× more expensive). Never `windows-latest` (bash / grep / sed semantics differ).
- **Permissions:** `{ contents: read }` at job level (least-privilege default). No `pull-requests: write`, no `checks: write`, no `issues: write`. The workflow communicates exclusively via exit code + stdout log.
- **Timeout:** `timeout-minutes: 2`. Generous ceiling; AC8 performance budget is 30 seconds, so the 2-minute hard cap is a safety net for pathological git-fetch slowness, not the expected runtime.
- **Concurrency:** not set. Default GitHub-Actions concurrency (one run per commit SHA per workflow) is sufficient. If future traffic mandates cancellation of superseded runs, a `concurrency: { group: ${{ github.ref }}, cancel-in-progress: true }` block may be added; explicitly OUT OF SCOPE for Story 6.2 MVP.

### Action pinning

- **`actions/checkout@v5`** (minimum) — Node 24 runtime, aligned with GitHub's Fall 2026 Node 20 deprecation. `@v4` is explicitly DISALLOWED; `@v6` is permitted at Dev's discretion.
- **No other third-party actions.** The scanning logic is inline `run:` bash only. No `tj-actions/changed-files` (supply-chain discipline — `tj-actions/changed-files` has historically had security incidents), no `dorny/paths-filter`, no custom actions.
- **`fetch-depth: 0`** on the checkout step. Full history required so `git diff origin/${{ github.base_ref }}...HEAD` can resolve the PR merge-base. Without `fetch-depth: 0` the checkout is shallow and `origin/<base>` is unreachable.

---

## Pattern-loading step (bash)

Maps to AC3. Step name (canonical): `Load banned patterns`. Step id: `load`.

### Load sequence

1. **Strip comments and blanks.** `grep -vE '^(#|$)' .github/pii-denylist.txt` — removes all `#`-prefixed comment lines and empty lines, yields one literal substring per line.
2. **Drop fork-local sentinels.** `grep -vFx 'DEREK_HOME_ADDRESS_FORK_LOCAL' | grep -vFx 'DEREK_FAMILY_FORK_LOCAL'` — removes the two audit-anchor lines that exist only to prove consumer-fork extensibility. The `-Fx` flags (fixed-string, full-line match) make the removal strict: the sentinel must equal the entire pattern line, not just appear as a substring.
3. **Sanity floor.** Assert `${#RAW[@]} >= 25`. Below 25 patterns, fail-fast with `FAIL: loaded pattern count <N> is below the sanity floor (25)` and exit non-zero — this defends against an accidental truncation of the deny-list file. Expected count at Story 6.2 author time: 28 (30 real pattern lines in the deny-list minus the 2 fork-local sentinels).
4. **Metacharacter escape.** For each raw pattern `p`, compute `e = printf '%s' "$p" | sed 's/[][(){}.^$|*+?\\]/\\&/g'`. This escapes the POSIX-ERE metacharacter class `[ ] ( ) { } . ^ $ | * + ? \` — every pattern becomes a literal-match regex. Important edge cases:
    - `derekneighbors.com` → `derekneighbors\.com` (the `.` is escaped so the regex matches a literal `.` instead of any character).
    - `Bodybuilding.com` → `Bodybuilding\.com` (same rule).
    - `gtd-life` → `gtd-life` (the `-` is NOT a metacharacter outside a character class; no escape).
    - `Queen Creek` → `Queen Creek` (the space is NOT a metacharacter; no escape).
5. **Boundary-guard wrapping.** For each escaped pattern `e`, wrap as `(^|[^A-Za-z])e($|[^A-Za-z])` — the Stories 2.1 → 6.1 idiom, externalized from harness code into the workflow. POSIX-ERE. BSD-grep and GNU-grep compatible. NO `\b`, NO `\<`, NO `\>`, NO PCRE. Worked examples:
    - `derek` → `(^|[^A-Za-z])derek($|[^A-Za-z])` (no metacharacters; wrap directly).
    - `derekneighbors.com` → `(^|[^A-Za-z])derekneighbors\.com($|[^A-Za-z])` (the `.` was escaped to `\.` in step 4; then wrapped).
    - `gtd-life` → `(^|[^A-Za-z])gtd-life($|[^A-Za-z])` (the `-` is NOT a metacharacter outside a character class, so step 4 is a no-op; wrap directly).
6. **Single-alternation combine.** `ALT=$(IFS='|'; echo "${ESCAPED[*]}")` joins the escaped patterns with `|`. The full combined regex is `REGEX="(^|[^A-Za-z])(${ALT})(\$|[^A-Za-z])"`. The outer boundary guard applies to the whole alternation; the inner `(${ALT})` groups the escaped-pattern alternatives. The trailing `\$` is a literal backslash-dollar so that the shell does not try to expand `$` before YAML/Bash double-unwrapping.
7. **Persist to disk.** `echo "$REGEX" > "$RUNNER_TEMP/pii-regex.txt"` — the Scan step reads this file (avoids re-building the regex and avoids shell-argv-length issues on large pattern sets).
8. **Emit one-line summary.** `echo "Loaded ${#RAW[@]} banned patterns from .github/pii-denylist.txt"` — AC3 requirement. The summary MUST appear in the GitHub-Actions log so reviewers can confirm the scanner ran with a non-zero pattern count. Defense against silently-skipped scans.

### Why a single alternation regex (not N per-pattern greps)

Per Story 6.1 Task 6 handoff §"Performance budget": combining N patterns into one `(P1|P2|…|PN)` alternation scans the target tree once with `grep -iE`, versus N separate invocations. On the ~100-file `assistants-template` tree with 28 patterns, the delta is: 28 × (fork + grep + exec + exit) ≈ 1–3 seconds; single alternation ≈ 0.1–0.3 seconds. Consumer forks may grow to hundreds of files — the alternation approach scales linearly with tree size and CONSTANT-time with pattern count, keeping AC8's < 30 s budget comfortable at all fork sizes.

### Boundary-guard correctness (same edge cases the harness proves)

The boundary guard `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` ensures:

- `Derek was here` MATCHES `derek` (boundary before `D` is start-of-string; boundary after `k` is the space `[^A-Za-z]`).
- `homepage is fine` does NOT MATCH `home` (boundary before `h` is start-of-string — OK — but boundary after `e` is `p`, which IS in `[A-Za-z]`, so the guard blocks the match). Guard correctness proven.
- `my-derek-fixture.md` MATCHES `derek` (boundary before `d` is `-`, which is in `[^A-Za-z]`; boundary after `k` is `-`, also in `[^A-Za-z]`).
- `derekneighbors.com` MATCHES `derek` (boundary before `d` is start-of-string; boundary after `k` is `n`, which IS in `[A-Za-z]` — so actually the guard BLOCKS this match against just `derek`, but the token `derekneighbors.com` itself IS in the deny-list and matches as its own token). Intended.
- `personality` does NOT MATCH `personal` (boundary before `p` is start-of-string — OK — but boundary after `l` is `i`, which IS in `[A-Za-z]`, so the guard blocks). Guard correctness proven.
- `familiar` does NOT MATCH `family` (same argument — boundary after `y` is `i`, blocks).

---

## Changed-file identification step (bash)

Maps to AC5. Step name (canonical): `Identify changed files`. Step id: `diff`.

### Primary path

```bash
git fetch origin "${{ github.base_ref }}" --depth=1
git diff --name-only --diff-filter=ACMR \
  "origin/${{ github.base_ref }}...HEAD" > "$RUNNER_TEMP/changed-all.txt" || true
```

- `git fetch origin <base_ref> --depth=1` populates the remote-tracking ref without pulling the entire base-branch history. Combined with the checkout step's `fetch-depth: 0`, this makes the triple-dot `origin/<base>...HEAD` merge-base reachable.
- `git diff --name-only --diff-filter=ACMR` emits the newline-delimited list of Added/Copied/Modified/Renamed files. Deletions are EXCLUDED (`D` is not in the filter set) — a PR that deletes lines cannot INTRODUCE PII.
- Triple-dot `A...B` computes `git merge-base A B`, then diffs from the merge-base to `B`. This is the correct semantic for "what changed in this PR relative to where it branched off `main`."
- Trailing `|| true` prevents the step from failing if `git diff` exits non-zero on an empty diff (rare but possible on edge cases).

### Fallback path (initial-PR-commit edge case)

```bash
if [ ! -s "$RUNNER_TEMP/changed-all.txt" ]; then
  echo "NOTE: base branch unreachable or empty diff; falling back to HEAD commit scan"
  git diff-tree --no-commit-id --name-only -r HEAD > "$RUNNER_TEMP/changed-all.txt"
fi
```

- Triggers when the primary path produces zero output (e.g. a branch where `fetch-depth: 0` still cannot resolve the base ref — a rare corner case in practice but guarded defensively).
- `git diff-tree --no-commit-id --name-only -r HEAD` enumerates the files changed by the HEAD commit itself. Conservative: reports MORE files than the merge-base diff in the normal case, but guarantees the scanner sees SOMETHING on the first-commit edge case.
- The log note `NOTE: base branch unreachable or empty diff; falling back to HEAD commit scan` is recorded so CI-log readers can distinguish primary vs. fallback.

### Output contract

- Write the filtered list (post-exclusion — see `## Exclusion filter (bash)`) to `"$RUNNER_TEMP/changed-filtered.txt"`.
- Compute `N=$(wc -l < "$RUNNER_TEMP/changed-filtered.txt" | tr -d ' ')` and emit `echo "Changed files after exclusion: $N"`.
- Export the count via `echo "n=$N" >> "$GITHUB_OUTPUT"` so the downstream Scan step's `if:` conditional can read it.

---

## Exclusion filter (bash)

Maps to AC4.

### Verbatim exclusion-set comment block (Task 3 pastes this verbatim as a YAML comment block at the top of the workflow file)

```yaml
# AC4 exclusion set — paths excluded from the deny-list scan:
#   .git/                                                        (version control metadata)
#   .github/pii-denylist.txt                                     (the deny-list itself)
#   .github/workflows/pii-denylist.yml                           (this workflow file; self-match guard)
#   docs/pii-denylist.md                                         (the policy doc; enumerates tokens)
#   _bmad/                                                       (BMAD framework internals; not Vixxo-authored)
#   _bmad-output/implementation-artifacts/*.md                   (story files enumerate tokens as audit evidence)
#   _bmad-output/implementation-artifacts/tests/*.md             (baseline / blueprint docs enumerate tokens)
#   _bmad-output/implementation-artifacts/tests/*.sh             (validation harnesses embed banned-term regex inline)
#   _bmad-output/planning-artifacts/                             (epics.md, architecture.md enumerate tokens)
#   node_modules/                                                (if present; skill-bundle install artifacts)
# Exclusion rationale: every excluded path either (a) legitimately contains banned tokens as part of its job
# (deny-list, policy doc, story files, harnesses, planning artifacts), (b) is not Vixxo-authored source
# (_bmad/ framework, node_modules/), or (c) is version-control metadata (.git/).
```

### Filter implementation (inside the `Identify changed files` step, post-diff)

```bash
grep -vE \
  -e '^\.github/pii-denylist\.txt$' \
  -e '^\.github/workflows/pii-denylist\.yml$' \
  -e '^docs/pii-denylist\.md$' \
  -e '^_bmad/' \
  -e '^_bmad-output/implementation-artifacts/.*\.md$' \
  -e '^_bmad-output/implementation-artifacts/tests/.*\.(md|sh)$' \
  -e '^_bmad-output/planning-artifacts/' \
  -e '^node_modules/' \
  "$RUNNER_TEMP/changed-all.txt" > "$RUNNER_TEMP/changed-filtered.txt" || true
```

- Each `-e` regex is a POSIX-ERE anchored at `^` so it matches path prefixes / exact paths, not substrings mid-filename.
- `.git/` is NOT enumerated in the `grep -vE` block because `git diff --name-only` never emits `.git/` paths — they're inside `.git/` by definition and not tracked by git itself.
- The `${RUNNER_TEMP}` variable is provided by the GitHub Actions runner and points at a fresh per-run temp directory — safer than `/tmp` (Ubuntu runners have `/tmp` but `$RUNNER_TEMP` is the documented idiom).
- Trailing `|| true` prevents the step from failing when `grep -v` exits non-zero on an all-excluded diff.

### Empty-after-exclusion path

If `N == 0` (every changed file was in the exclusion set), the Report step emits `PASS: PII deny-list scan — 0 files after exclusions, nothing to scan` and exits 0. AC4 explicitly requires this is NOT a failure.

### Exclusion-set audit trail

The verbatim comment block is the AC4 audit artifact. Task 4's `check_task3` gate asserts that the following tokens appear in the workflow file via `grep -Fq`:

- `.github/pii-denylist.txt`
- `docs/pii-denylist.md`
- `_bmad-output/implementation-artifacts`
- `node_modules`

Any future change to the exclusion set MUST update both the comment block AND the `grep -vE` regex block in lock-step; a mismatch is a regression caught by the harness.

---

## Scan step (bash)

Maps to AC5 + AC6. Step name (canonical): `Scan for banned patterns`. Conditional: `if: steps.diff.outputs.n != '0'`.

### Scanner body

```bash
set -euo pipefail
REGEX=$(cat "$RUNNER_TEMP/pii-regex.txt")
: > "$RUNNER_TEMP/pii-matches.txt"
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ ! -f "$f" ] && continue
  grep -inE "$REGEX" "$f" >> "$RUNNER_TEMP/pii-matches.txt" \
    --with-filename || true
done < "$RUNNER_TEMP/changed-filtered.txt"
```

### Step-by-step rationale

- **`set -euo pipefail`** — bail on any unhandled error, undefined variable, or pipeline failure.
- **`REGEX=$(cat "$RUNNER_TEMP/pii-regex.txt")`** — read the combined alternation regex persisted by the Load step.
- **`: > "$RUNNER_TEMP/pii-matches.txt"`** — truncate (or create) the output file. Ensures the Report step reads a clean slate.
- **`while IFS= read -r f`** — iterate the filtered changed-file list line by line. `IFS=` prevents leading/trailing whitespace stripping; `-r` prevents backslash interpretation.
- **`[ -z "$f" ] && continue`** — skip blank lines.
- **`[ ! -f "$f" ] && continue`** — skip non-files (deleted paths, typed files, anything non-regular). Defensive — `--diff-filter=ACMR` already filters deletions but symlinks and submodules can still appear.
- **`grep -inE "$REGEX" "$f"`** — case-insensitive (`-i`), include line numbers (`-n`), POSIX-ERE (`-E`). `--with-filename` forces grep to prefix output with the filename even when invoked on a single file (the default behavior emits filename only on multi-file invocations).
- **`>> "$RUNNER_TEMP/pii-matches.txt"`** — append, not overwrite. Accumulates matches across all changed files.
- **`|| true`** — grep exits 1 when there are no matches; we do NOT want that to kill the whole step.

### Why NO context flags (`-A`, `-B`, `-C`)

AC6 explicitly forbids context printing: "the violation output MUST NOT print the matched file's surrounding context." Rationale: printing context could itself leak PII from a bad PR into the public CI log. Only the violated path, line number, and a generic "matched banned pattern" marker appear — the offending token itself is effectively redacted from the log summary (it remains on the `grep` line that precedes the `FAIL:` summary, but only on the single line the matcher hit, not nearby context).

### Why file-by-file (not `xargs grep -inE`)

The file-by-file loop is slightly slower than `xargs grep -inE`, but:
- Handles filenames with spaces robustly without careful `xargs -0` piping.
- Gives clean per-file error isolation (a single unreadable file does not kill the whole scan).
- The performance delta is negligible at changed-file sets ≤ 50 (AC8's representative case).

For consumer-fork scale, if scan time becomes an issue, `xargs -0` batching is a drop-in replacement that does not change the output format.

### Match-output format (intermediate)

Each line written to `$RUNNER_TEMP/pii-matches.txt` has the shape `<path>:<line-number>:<matched-line-contents>`, exactly the `grep -in --with-filename` default. The Report step parses this stream to produce the AC6-formatted output.

---

## Report step (bash — pass/fail output formats)

Maps to AC4 + AC6 + AC7. Step name (canonical): `Report`. Unconditional (runs regardless of whether the Scan step ran).

### Report body

```bash
set -euo pipefail
N="${{ steps.diff.outputs.n }}"
if [ -z "$N" ] || [ "$N" = "0" ]; then
  echo "PASS: PII deny-list scan — 0 files after exclusions, nothing to scan"
  exit 0
fi
if [ ! -s "$RUNNER_TEMP/pii-matches.txt" ]; then
  echo "PASS: PII deny-list scan — $N files scanned, 0 violations"
  exit 0
fi
while IFS= read -r line; do
  path=$(printf '%s' "$line" | cut -d: -f1)
  lineno=$(printf '%s' "$line" | cut -d: -f2)
  rest=$(printf '%s' "$line" | cut -d: -f3-)
  echo "FAIL: ${path}:${lineno}: matched banned pattern (see line content above)"
done < "$RUNNER_TEMP/pii-matches.txt"
VIOL=$(wc -l < "$RUNNER_TEMP/pii-matches.txt" | tr -d ' ')
FILES=$(cut -d: -f1 "$RUNNER_TEMP/pii-matches.txt" | sort -u | wc -l | tr -d ' ')
echo "FAIL: PII deny-list scan — $VIOL violations in $FILES files; see offending lines above"
exit 1
```

### AC6 FAIL output format (verbatim)

Per-violation line format:

```
FAIL: <relative-path>:<line-number>: matched banned pattern '<matched-token>'
```

Worked example, sample output for a PR that introduces `derek` in `agents/personas/work.md` at line 12:

```
FAIL: agents/personas/work.md:12: matched banned pattern 'derek'
FAIL: PII deny-list scan — 1 violations in 1 files; see offending lines above
```

Multi-violation sample (three violations across two files):

```
FAIL: memory/me/preferences.md:18: matched banned pattern 'derek'
FAIL: memory/me/preferences.md:24: matched banned pattern 'wyoming'
FAIL: agents/personas/work.md:7: matched banned pattern 'benji'
FAIL: PII deny-list scan — 3 violations in 2 files; see offending lines above
```

Note: the reference skeleton uses the generic `matched banned pattern (see line content above)` suffix because exact-token extraction from the boundary-guard match is noisy (the guard regex captures the boundary characters alongside the token). Dev may at their discretion implement precise-token extraction in Task 3 (e.g. via a second `grep -oE` pass per line to isolate the actual matched token) and produce the exact AC6 format shown above. Either phrasing satisfies the intent of AC6; the generic suffix is the conservative fallback when precise extraction is not feasible.

Exit status: `1`. The GitHub Checks API marks the run as FAILED. With branch protection rules requiring `PII deny-list` as a required status check, the PR merge button is disabled.

### AC7 PASS output format (verbatim)

Single summary line:

```
PASS: PII deny-list scan — N files scanned, 0 violations
```

Worked example, sample output for a PR with 3 changed files none of which contain banned tokens:

```
Loaded 28 banned patterns from .github/pii-denylist.txt
Changed files after exclusion: 3
PASS: PII deny-list scan — 3 files scanned, 0 violations
```

Exit status: `0`. The GitHub Checks API marks the run as SUCCESS.

The workflow log ALSO includes the one-line `Loaded N banned patterns from .github/pii-denylist.txt` message from the Load step (preceding the PASS summary), so reviewers can confirm at a glance that the scanner ran with a non-zero pattern count — defense against silently-skipped scans.

### Empty-after-exclusion PASS format (AC4)

When every changed file is in the exclusion set:

```
PASS: PII deny-list scan — 0 files after exclusions, nothing to scan
```

Exit status: `0`. The GitHub Checks API marks the run as SUCCESS.

### Format choice rationale

- **`FAIL:` / `PASS:` prefix.** Greppable. Machine-parseable. Consistent with the Stories 2.1 → 6.1 harness convention (`^FAIL:` / `^PASS:`).
- **Em-dash `—`.** Used as the visual separator between the prefix and the count. Unicode `U+2014`. Matches the Story 6.1 harness style.
- **Single quotes around the matched token.** Prevents ambiguity when a pattern contains spaces (e.g. `'Queen Creek'`, `'Agile Weekly'`) or dots (e.g. `'derekneighbors.com'`).
- **Count reporting in the summary line (`N violations in M files`).** Lets reviewers gauge severity at a glance without scrolling the per-violation list.
- **No context flags.** Per AC6, printing `-A 3 -B 3` context could leak PII from the bad PR into the public CI log.

---

## Self-match guard (bash pre-flight)

Maps to AC9. Step name (canonical): `Verify deny-list self-integrity`. Runs BEFORE the Load step.

### Guard body

```bash
set -euo pipefail
if grep -vE '^(#|$)' .github/pii-denylist.txt | grep -Fq 'SAFE-TO-PUBLISH'; then
  echo "FAIL: deny-list self-integrity — 'SAFE-TO-PUBLISH' sentinel found in a pattern line; refusing to scan"
  exit 1
fi
```

### What this guards

The safe-publish sentinel `# SAFE-TO-PUBLISH deny-list` lives (per Story 6.1) inside the header comment block of `.github/pii-denylist.txt`. It is a deliberately-chosen string — distinctive, unlikely to appear by accident, a grep-visible integrity anchor. If the sentinel ever drifts out of the header comment and INTO a pattern line, that is a regression: the sentinel would then itself become a banned pattern, and Story 6.2's scanner would start matching on the string `SAFE-TO-PUBLISH` everywhere it appears in the repo — including inside story files, architecture docs, and the deny-list file itself.

This guard catches the drift at CI time — before any scan runs — and fails the workflow with a clear, actionable error message.

### Why this mirrors the Story 6.1 harness

Story 6.1's harness (`story-6-1-pii-denylist-validation.sh`) has the same assertion inside its `check_task4` gate: `grep -vE '^(#|$)' .github/pii-denylist.txt | grep -Fq 'SAFE-TO-PUBLISH'` MUST return exit 1 (no match). Story 6.2's workflow lifts this assertion into CI. Convergent evidence: the invariant is checked at BOTH author-time (Story 6.1 harness runs locally) AND CI-time (Story 6.2 workflow runs on every PR). Any regression that slips past the local harness is caught by CI.

### Worked examples

- **HOLDS (current state — harness exits 1):**
  - `.github/pii-denylist.txt` contains `# SAFE-TO-PUBLISH deny-list` in the header block.
  - `grep -vE '^(#|$)' .github/pii-denylist.txt` strips the `#`-prefixed line, leaving only pattern lines.
  - `| grep -Fq 'SAFE-TO-PUBLISH'` finds NO match in the pattern stream.
  - `if` condition is false; the guard passes silently.
- **FAILS (drift — guard triggers):**
  - Someone edits `.github/pii-denylist.txt` to add a raw `SAFE-TO-PUBLISH` line in the pattern block (e.g. "this is the safe-to-publish sentinel" without the leading `#`).
  - `grep -vE '^(#|$)' .github/pii-denylist.txt` emits the uncommented line.
  - `| grep -Fq 'SAFE-TO-PUBLISH'` finds the match.
  - `if` condition is true; the guard emits `FAIL: deny-list self-integrity — …` and exits 1. The rest of the workflow (Load, Diff, Scan, Report) does not run.

### Why this runs BEFORE Load

Load reads the deny-list and builds the scan regex. If the sentinel is in a pattern line, Load would happily build a regex that includes `SAFE-TO-PUBLISH` as a boundary-guarded banned pattern, and the subsequent Scan would flag EVERY file in the repo that mentions the sentinel (including the deny-list file — but it's excluded; and including the docs file — also excluded; but including this blueprint, several story files, etc., all of which reference the sentinel as policy documentation). That's a noisy cascade. The pre-flight guard short-circuits before any of that machinery runs.

---

## Performance budget and optimization rationale

Maps to AC8. Budget: total wall-clock < 30 seconds; scan step alone < 5 seconds.

### Wall-clock budget breakdown (representative case: 50 changed files ≤ 100 KB each)

| Phase | Expected time | Notes |
| --- | --- | --- |
| `Set up job` (runner bootstrap) | 1–3 s | Fixed overhead; GitHub Actions pre-warms the Ubuntu runner. |
| `Checkout repository with history` (`actions/checkout@v5`, `fetch-depth: 0`) | 3–6 s | Full repo clone; repo size < 5 MB for `assistants-template`. |
| `Verify deny-list self-integrity` | < 0.1 s | Two `grep` invocations on a 2,669-byte file. |
| `Load banned patterns` | 0.1–0.3 s | 28 patterns, 28 `sed` invocations for metacharacter escape, single-pass regex combine. |
| `Identify changed files` | 0.5–1.5 s | `git fetch origin <base_ref> --depth=1` dominates; changed-file diff + exclusion filter are sub-second. |
| `Scan for banned patterns` | 0.5–4 s | File-by-file `grep -inE`; scales linearly with changed-file count × file size. |
| `Report` | < 0.1 s | Single pass over the matches file; two `wc -l` invocations; `cut | sort -u`. |
| `Complete job` (runner teardown) | 1–2 s | Fixed overhead. |
| **Total** | **7–17 s** | Comfortably under the 30 s AC8 budget. |

### Worst-case estimate (300 changed files ≤ 1 MB each — a large consumer-fork PR)

| Phase | Expected time | Notes |
| --- | --- | --- |
| `Set up job` | 1–3 s | |
| `Checkout` | 5–10 s | Larger consumer forks may have > 20 MB repos. |
| `Load` | 0.2–0.5 s | Independent of repo size. |
| `Diff` | 1–3 s | Large diff enumeration. |
| `Scan` | 3–8 s | 300 files × ~30 ms per `grep` = 9 s worst case. |
| `Report` | < 0.5 s | |
| `Complete` | 1–2 s | |
| **Total** | **12–27 s** | Still under 30 s. |

### Primary optimization: single-alternation regex (AC3)

28 patterns → 1 combined POSIX-ERE regex → 1 `grep -inE` invocation per changed file. Alternative (28 separate grep invocations per file) would multiply the Scan-step time by ~28×, pushing the worst-case estimate past 30 s.

The alternation regex shape `(^|[^A-Za-z])(P1|P2|...|PN)($|[^A-Za-z])` applies the boundary guard ONCE at the regex-engine level instead of reconstructing it per-pattern. Regex-engine cost is approximately O(log N) in the number of alternatives for modern NFA engines, so the cost of scanning with 28 vs. 100 vs. 300 patterns is approximately constant at single-digit milliseconds per file.

### Secondary optimization: changed-file scope (AC5)

The workflow scans only the PR's changed files, not the full repo tree. For a typical PR (10–50 changed files on a ~200-file repo), this is a 4–20× time savings vs. a full-tree scan. The savings compound across every PR the template (and its consumer forks) see forever.

### Why NOT use `rg` (ripgrep)

`rg` is faster than `grep` by 2–5× on large trees. Reasons Story 6.2 does NOT use `rg`:

1. **`ubuntu-latest` does NOT pre-install `rg`.** Installing `rg` in the workflow adds ~1 s to the setup phase and another third-party dependency. Net savings ≈ 0.
2. **Architecture constraint: no new dependencies.** Story 6.2 uses `bash`, `grep`, `sed`, `git` — all pre-installed. Adding `rg` violates the no-new-deps discipline (architecture.md).
3. **Predictability.** `grep` is POSIX-standard; `rg` has its own regex flavor (Rust's regex crate) with subtle differences from POSIX-ERE (e.g. Unicode-aware character classes). Using `grep` keeps the workflow behavior identical to the local harness behavior (the harness runs on BSD-grep on macOS dev laptops).

### Why NOT use parallel scanning (`xargs -P`)

`ubuntu-latest` runners provide 2–4 CPU cores. Parallel `grep` invocations (e.g. `cat changed-filtered.txt | xargs -P 4 -I {} grep -inE "$REGEX" {}`) could in principle cut scan time by ~2×. Reasons Story 6.2 does NOT parallelize:

1. **Output interleaving.** Parallel `grep` writes to stdout non-deterministically; the `pii-matches.txt` accumulator would have interleaved lines from different files, complicating the Report step.
2. **Premature optimization.** The serial scan already finishes in single-digit seconds on the AC8 representative case. Parallelization saves 2–4 s on a 30 s budget — not worth the complexity.
3. **Future upgrade path.** If a consumer fork's scan ever exceeds AC8, parallel scanning is a drop-in replacement (serialize output via `flock` or per-file temp files + concat). Explicitly OUT OF SCOPE for Story 6.2 MVP.

### How AC8 is verified

1. **Local harness dry-run (`check_task4`).** The Task 4 harness replicates the Load + Scan logic locally against the current repo HEAD and records the elapsed time. The harness asserts the local dry-run completes in < 5 seconds (conservative local proxy; CI is typically faster than a dev laptop on small trees).
2. **Real-PR exercise (Task 6, Phase 3).** The Dev opens a fixture PR that introduces a known banned token, observes the GitHub Actions workflow FAIL with the AC6 output, and records the total wall-clock time from the runner's `Duration` field in the UI. Then opens the real Story 6.2 PR and records the PASS-path wall-clock time. Both MUST be < 30 seconds. Documented in `story-6-2-task6-handoff.md`.

---

## Harness shape (gates, constants, regex_self_probe)

Target file: `_bmad-output/implementation-artifacts/tests/story-6-2-github-action-validation.sh`. Maps to AC10 + AC11. Model: `story-6-1-pii-denylist-validation.sh`.

### Physical file attributes

- **Shebang:** `#!/usr/bin/env bash` on line 1.
- **Safety pragma:** `set -euo pipefail` on line 2.
- **Mode:** `0755` (`chmod +x`). Executable.
- **Line endings:** LF only. No `\r`. No tabs. No trailing spaces.
- **Encoding:** UTF-8.
- **Portability:** POSIX-bash 3.2 compatible (no Bash 4+ features like associative arrays without explicit guards). BSD-grep and GNU-grep compatible. Tools used: `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`, shell builtins. NOT used: `rg`, `jq`, `yq`, Python, Node, `ggrep`, `gsed`.

### Constants (declared at the top of the harness)

```bash
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

WORKFLOW_PATH="${PROJECT_ROOT}/.github/workflows/pii-denylist.yml"
DENYLIST_PATH="${PROJECT_ROOT}/.github/pii-denylist.txt"
DOC_PATH="${PROJECT_ROOT}/docs/pii-denylist.md"
README_PATH="${PROJECT_ROOT}/README.md"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-6-2-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-6-2-canonical-blueprint.md"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"
STORY_2_3_HARNESS="${TESTS_DIR}/story-2-3-work-persona-validation.sh"
STORY_2_4_HARNESS="${TESTS_DIR}/story-2-4-benji-inbox-absence-validation.sh"
STORY_3_1_HARNESS="${TESTS_DIR}/story-3-1-memory-template-tree-validation.sh"
STORY_3_2_HARNESS="${TESTS_DIR}/story-3-2-obsidian-config-validation.sh"
STORY_3_3_HARNESS="${TESTS_DIR}/story-3-3-identity-preferences-validation.sh"
STORY_6_1_HARNESS="${TESTS_DIR}/story-6-1-pii-denylist-validation.sh"

REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 7 )

PATTERN_COUNT_FLOOR=25

EXPECTED_WORKFLOW_KEYS=(
  'name:'
  'on:'
  'pull_request:'
  'jobs:'
  'runs-on: ubuntu-latest'
  'permissions:'
  'contents: read'
  'timeout-minutes:'
  'fetch-depth: 0'
  'actions/checkout@v'
)

EXPECTED_STEP_NAMES=(
  'Checkout'
  'self-integrity'
  'Load banned patterns'
  'Identify changed files'
  'Scan for banned patterns'
  'Report'
)

POSITIVE_FIXTURE_CONTENT='Derek was here'
NEGATIVE_FIXTURE_CONTENT='homepage is fine'
```

`REGRESSION_PASS_COUNTS` is the per-harness `^PASS:` line-count fingerprint asserted by `check_task6`. Expected: `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7 / 7` — carried forward from Story 6.1's measured fingerprint (first ten) plus Story 6.1's own `7` (eleventh). Dev MUST re-measure at Task 1 baseline-audit time and update the array if observed values differ.

### Helper functions

- **`fail <reason>`** — prints `FAIL: <gate-name-inferred-from-caller>: <reason>` to stderr and exits 1. Mirrors Story 6.1 harness precedent.
- **`pass <gate>`** — prints `PASS: <gate>` to stdout.
- **`regex_self_probe`** — builds the combined boundary-guard alternation regex from `.github/pii-denylist.txt` (mirroring the workflow's Load step), then:
    - Asserts the POSITIVE fixture string matches via `grep -iE "$REGEX" <<< "$POSITIVE_FIXTURE_CONTENT"` (exit 0 required).
    - Asserts the NEGATIVE fixture string does NOT match via `! grep -iE "$REGEX" <<< "$NEGATIVE_FIXTURE_CONTENT"` (exit 1 from grep; guard passes).
    - On either mismatch, calls `fail` with a descriptive reason (e.g. "positive fixture failed to match" or "negative fixture unexpectedly matched — boundary guard regression").

### Gate specifications

#### `check_task1` — baseline-audit evidence

- `[[ -f "$BASELINE_AUDIT_PATH" ]]`, `[[ -s "$BASELINE_AUDIT_PATH" ]]`.
- `grep -Fxq '# Story 6.2 Baseline Audit' "$BASELINE_AUDIT_PATH"`.
- Each required H2 section present via `grep -Fxq`: `## Pre-existing workflow inventory`, `## 11-harness regression fingerprint (measured)`, `## Deny-list byte-stability verification`, `## Loaded pattern count (post-sentinel-filter)`, `## Full-tree dry-run scan (zero-match assertion)`, `## Pre-existing leak flags (if any)`.

#### `check_task2` — canonical-blueprint evidence

- `[[ -f "$BLUEPRINT_PATH" ]]`, `[[ -s "$BLUEPRINT_PATH" ]]`.
- `grep -Fxq '# Story 6.2 Canonical Blueprint' "$BLUEPRINT_PATH"`.
- Each of the eleven H1/H2 section headers present via `grep -Fxq`:
    - `# Story 6.2 Canonical Blueprint`
    - `## Workflow file shape (YAML)`
    - `## Trigger and runtime metadata`
    - `## Pattern-loading step (bash)`
    - `## Changed-file identification step (bash)`
    - `## Exclusion filter (bash)`
    - `## Scan step (bash)`
    - `## Report step (bash — pass/fail output formats)`
    - `## Self-match guard (bash pre-flight)`
    - `## Performance budget and optimization rationale`
    - `## Harness shape (gates, constants, regex_self_probe)`
- Verbatim YAML skeleton present: `grep -Fq 'name: PII deny-list' "$BLUEPRINT_PATH"` AND `grep -Fq 'runs-on: ubuntu-latest' "$BLUEPRINT_PATH"` AND `grep -Fq 'actions/checkout@v5' "$BLUEPRINT_PATH"` AND `grep -Fq 'fetch-depth: 0' "$BLUEPRINT_PATH"`.
- Verbatim exclusion-set comment block present: `grep -Fq '_bmad-output/planning-artifacts/' "$BLUEPRINT_PATH"` AND `grep -Fq 'node_modules/' "$BLUEPRINT_PATH"` AND `grep -Fq 'docs/pii-denylist.md' "$BLUEPRINT_PATH"`.

#### `check_task3` — workflow file shape

- `[[ -f "$WORKFLOW_PATH" ]]`, `[[ -s "$WORKFLOW_PATH" ]]`.
- `tail -c 1 "$WORKFLOW_PATH" | od -An -tx1 | tr -d ' \n'` equals `0a` (trailing newline).
- `grep -c $'\r' "$WORKFLOW_PATH"` equals `0` (LF only).
- `grep -c $'\t' "$WORKFLOW_PATH"` equals `0` (no tabs).
- `awk 'length > 200' "$WORKFLOW_PATH" | wc -l | tr -d ' '` equals `0` (line-length budget).
- `grep -cE ' $' "$WORKFLOW_PATH"` equals `0` (no trailing spaces).
- Each element of `EXPECTED_WORKFLOW_KEYS` present via `grep -Fq`.
- Each element of `EXPECTED_STEP_NAMES` present via case-insensitive `grep -Fiq`.
- `grep -Eq 'actions/checkout@v[56]' "$WORKFLOW_PATH"` (v5 or v6 pin).
- `timeout-minutes:` value is a positive integer ≤ 10: `grep -Eq 'timeout-minutes:[[:space:]]+[1-9]([^0-9]|$)' "$WORKFLOW_PATH"` AND `! grep -Eq 'timeout-minutes:[[:space:]]+(1[1-9]|[2-9][0-9])' "$WORKFLOW_PATH"`.
- Exclusion-set comment block present: `grep -Fq '.github/pii-denylist.txt' "$WORKFLOW_PATH"` AND `grep -Fq 'docs/pii-denylist.md' "$WORKFLOW_PATH"` AND `grep -Fq '_bmad-output/implementation-artifacts' "$WORKFLOW_PATH"` AND `grep -Fq 'node_modules' "$WORKFLOW_PATH"`.
- README AC13 update: `grep -Fq '.github/workflows/pii-denylist.yml' "$README_PATH"` AND `grep -Fq '.github/pii-denylist.txt' "$README_PATH"` AND `grep -Fq 'docs/pii-denylist.md' "$README_PATH"`; README line count ≥ 34.
- `docs/pii-denylist.md` AC12 update: `grep -Fxq '## CI consumption' "$DOC_PATH"` AND `! grep -Fq '(Story 6.2 preview)' "$DOC_PATH"`; `grep -c '^## ' "$DOC_PATH" | tr -d ' '` equals `7`; `grep -Fq '.github/workflows/pii-denylist.yml' "$DOC_PATH"`.

#### `check_task4` — workflow logic simulation

- Replicate the workflow's pattern-load logic locally: `RAW=$(grep -vE '^(#|$)' "$DENYLIST_PATH" | grep -vFx 'DEREK_HOME_ADDRESS_FORK_LOCAL' | grep -vFx 'DEREK_FAMILY_FORK_LOCAL')`; assert `wc -l <<< "$RAW" >= PATTERN_COUNT_FLOOR`.
- Build the combined boundary-guard alternation regex locally (mirroring the Load step's `sed` escape + boundary wrap + join-with-`|`).
- Call `regex_self_probe` — proves positive fixture matches and negative fixture does NOT match.
- Assert safe-publish sentinel anti-self-match guard holds: `grep -vE '^(#|$)' "$DENYLIST_PATH" | grep -Fq 'SAFE-TO-PUBLISH'` returns exit 1.
- Assert `.github/pii-denylist.txt` byte-stability: `wc -c < "$DENYLIST_PATH" | tr -d ' '` equals `2669` (Story 6.1 handoff-recorded value). If `shasum` is available, also assert SHA-256 equals `b5b11a2c9d7da38308a9f8a1e95de5e89eb2111d2aa3a9e3ff7663bb434d681c`.

#### `check_task5` — self-check

- `head -n 1 "$SELF_PATH" | grep -Fxq '#!/usr/bin/env bash'` (shebang).
- `head -n 2 "$SELF_PATH" | tail -n 1 | grep -Fxq 'set -euo pipefail'` (safety pragma).
- Every case arm present: `grep -Eq '^[[:space:]]*task1\)' "$SELF_PATH"` through `task6)` and `all)`.
- Every declared constant name present via `grep -Fq "<constant-name>=" "$SELF_PATH"` — iterate a hardcoded list of the constants above.
- `declare -F regex_self_probe >/dev/null 2>&1` succeeds (function defined).
- `declare -F fail >/dev/null 2>&1` succeeds.
- `declare -F pass >/dev/null 2>&1` succeeds.

#### `check_task6` — eleven-harness regression

- For each of the eleven predecessor harnesses (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3 / 6.1):
    - `[[ -f "$harness" ]]`.
    - Run `bash "$harness" all` with combined stdout+stderr captured: `output=$(bash "$harness" all 2>&1)`.
    - Assert the invocation exited 0. On non-zero, `echo "$output"` and `fail` with the sub-harness name.
    - Count `^PASS:` lines: `count=$(printf '%s\n' "$output" | grep -c '^PASS:')`.
    - Assert `count` equals `REGRESSION_PASS_COUNTS[i]` for the positional index. On mismatch, `echo "$output"` and `fail` with the sub-harness name.
- NOTE on runtime: the Story 6.1 harness invocation dominates (~5.5 min) because ITS `check_task6` gate re-invokes the ten earlier harnesses. Acceptable for the local-only harness; the CI workflow does NOT run the local harness.

### `all` dispatcher

```bash
case "${1:-}" in
  task1) check_task1 && echo "PASS: task1" ;;
  task2) check_task2 && echo "PASS: task2" ;;
  task3) check_task3 && echo "PASS: task3" ;;
  task4) check_task4 && echo "PASS: task4" ;;
  task5) check_task5 && echo "PASS: task5" ;;
  task6) check_task6 && echo "PASS: task6" ;;
  all)
    check_task1 && echo "PASS: task1" \
      && check_task2 && echo "PASS: task2" \
      && check_task3 && echo "PASS: task3" \
      && check_task4 && echo "PASS: task4" \
      && check_task5 && echo "PASS: task5" \
      && check_task6 && echo "PASS: task6" \
      && echo "PASS: all"
    ;;
  *) echo "Usage: $0 {task1|task2|task3|task4|task5|task6|all}" >&2; exit 2 ;;
esac
```

Under `all`, the harness emits exactly 7 `^PASS:` lines on stdout (`PASS: task1` → `PASS: task6` → `PASS: all`) — fingerprint compatible with Stories 3.1 / 3.2 / 3.3 / 6.1 pass-count convention. Exit 0 on success; exit 1 (via `fail`) with `FAIL: <gate>: <reason>` on stderr on failure.

### Block-comment header (first ~15 lines of the harness, after shebang + safety pragma)

The harness opens with a block comment explaining:

1. Story 6.2 ships `.github/workflows/pii-denylist.yml` which operationalizes the Story 6.1 deny-list as a CI guardrail.
2. The harness is a LOCAL validator — the authoritative CI signal is the GitHub Actions run on a real PR.
3. The harness extends the Story 6.1 ten-predecessor regression chain by one (adds Story 6.1 as the eleventh predecessor).
4. No line-155 Story 1.1 allowlist amendment is needed (`.github/workflows/` is a `.github/` subdirectory, not a `memory/` subdir — Story 1.1's allowlist guards `memory/` content, not `.github/` content).
5. The harness deliberately does NOT run the workflow under `act` or any other local GitHub Actions emulator — local simulation is limited to the bash logic that the workflow inlines (pattern-load, boundary-guard regex construction, positive/negative fixture assertions).

### Positive and negative fixtures (used by `regex_self_probe`)

- **Positive fixture:** the literal string `Derek was here`. This string contains the token `Derek`; the boundary-guard regex `(^|[^A-Za-z])derek($|[^A-Za-z])` (case-insensitive via `grep -iE`) MUST match — start-of-string boundary before `D`, space boundary after `k`. If this fixture does NOT match, the pattern-load or boundary-guard construction is broken; `regex_self_probe` calls `fail` with a descriptive reason.
- **Negative fixture:** the literal string `homepage is fine`. This string contains the substring `home`; the boundary-guard regex `(^|[^A-Za-z])home($|[^A-Za-z])` MUST NOT match — start-of-string boundary before `h` is OK, but after `e` the next character is `p`, which is in `[A-Za-z]`, so the trailing boundary fails. If this fixture DOES match, the boundary guard is broken (regressed to a substring match); `regex_self_probe` calls `fail` with a descriptive reason.

The fixture pair proves boundary-guard correctness in both directions: positive-match-works AND negative-match-blocked. Both assertions MUST pass for `check_task4` to pass.

### Harness output contract (summary)

- **`bash story-6-2-github-action-validation.sh all`** → exit `0`, stdout contains exactly 7 lines matching `^PASS:` (in order: `PASS: task1`, `PASS: task2`, `PASS: task3`, `PASS: task4`, `PASS: task5`, `PASS: task6`, `PASS: all`).
- **`bash story-6-2-github-action-validation.sh task1`** → exit `0`, stdout contains exactly 1 line `PASS: task1`.
- **`bash story-6-2-github-action-validation.sh task<N>` (N ∈ {1…6})** → exit `0`, stdout contains exactly 1 line `PASS: task<N>`.
- **Any gate failure** → exit `1`, stderr contains one line `FAIL: <gate>: <reason>`.
- **Invalid argument** → exit `2`, stderr contains `Usage:` line.

---

## Cross-AC coverage map

| AC | Lock |
| --- | --- |
| AC1 | `## Workflow file shape (YAML)` (existence + non-empty + LF + trailing newline + git-tracked) + deny-list byte-stability assertion in `## Harness shape` `check_task4`. |
| AC2 | `## Trigger and runtime metadata` (all triggers, runner, permissions, timeout, checkout pinning, `fetch-depth: 0`). |
| AC3 | `## Pattern-loading step (bash)` (verbatim bash body + load sequence + metacharacter escape rules + boundary-guard wrapping + single-alternation combine + sanity floor + one-line summary). |
| AC4 | `## Exclusion filter (bash)` (ten-path exclusion set + verbatim comment block + filter-in-step-not-trigger rationale + empty-after-exclusion PASS path). |
| AC5 | `## Changed-file identification step (bash)` (primary `git diff` path + initial-commit fallback + `$RUNNER_TEMP` output contract) + `## Scan step (bash)` (file-by-file `grep -inE` loop + match accumulator). |
| AC6 | `## Report step (bash — pass/fail output formats)` (verbatim FAIL-line format + summary-line format + non-zero exit + worked examples + no-context-flags rationale). |
| AC7 | `## Report step (bash — pass/fail output formats)` (verbatim PASS-line format + zero exit + Load-step summary included in log + empty-after-exclusion PASS variant). |
| AC8 | `## Performance budget and optimization rationale` (wall-clock budget breakdown + single-alternation optimization + changed-file-scope optimization + no-rg / no-parallel rationale + AC8 verification path). |
| AC9 | `## Self-match guard (bash pre-flight)` (verbatim bash body + guard semantics + Story-6.1-harness convergence argument + worked examples). |
| AC10 | `## Harness shape (gates, constants, regex_self_probe)` (six gates + `all` dispatcher + `regex_self_probe` + constants + tool-discipline list). |
| AC11 | `## Harness shape` `check_task6` (eleven predecessors + fingerprint assertion + zero-edit invariant via byte-stable regression). |

---

## Task 4 harness probes (consumed from this blueprint)

Task 4's `check_task2` gate MUST assert the following about this blueprint file (`_bmad-output/implementation-artifacts/tests/story-6-2-canonical-blueprint.md`):

- File exists, non-empty, LF-only, trailing newline.
- Title `# Story 6.2 Canonical Blueprint` appears on line 1.
- Each of the following H1/H2 sections appears verbatim via `grep -Fxq`:
    - `# Story 6.2 Canonical Blueprint`
    - `## Workflow file shape (YAML)`
    - `## Trigger and runtime metadata`
    - `## Pattern-loading step (bash)`
    - `## Changed-file identification step (bash)`
    - `## Exclusion filter (bash)`
    - `## Scan step (bash)`
    - `## Report step (bash — pass/fail output formats)`
    - `## Self-match guard (bash pre-flight)`
    - `## Performance budget and optimization rationale`
    - `## Harness shape (gates, constants, regex_self_probe)`
- The verbatim YAML skeleton inside `## Workflow file shape (YAML)` contains `name: PII deny-list`, `runs-on: ubuntu-latest`, `actions/checkout@v5`, `fetch-depth: 0`, and the six step names enumerated in `EXPECTED_STEP_NAMES`.
- The verbatim exclusion-set comment block inside `## Exclusion filter (bash)` contains `.github/pii-denylist.txt`, `docs/pii-denylist.md`, `_bmad-output/implementation-artifacts`, `node_modules/`, and `_bmad-output/planning-artifacts/`.
- The `POSITIVE_FIXTURE_CONTENT` and `NEGATIVE_FIXTURE_CONTENT` values (`Derek was here` and `homepage is fine`) appear somewhere in the blueprint prose.

The blueprint is consumed as locked input by Task 3 (workflow authoring) and Task 4 (harness authoring). Any deviation between this blueprint and the files authored in Tasks 3 / 4 is a bug and fails the Task 4 harness.
