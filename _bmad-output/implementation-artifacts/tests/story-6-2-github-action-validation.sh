#!/usr/bin/env bash
set -euo pipefail

# Story 6.2 — GitHub Action blocks PRs violating the PII deny-list —
# deterministic local validation harness.
#
# Scope:
#   - Story 6.2 ships .github/workflows/pii-denylist.yml which
#     operationalizes the Story 6.1 deny-list as a CI guardrail. The
#     workflow runs on every pull_request event, loads the banned-term
#     vocabulary from .github/pii-denylist.txt, wraps each pattern in
#     the POSIX-ERE boundary guard `(^|[^A-Za-z])TOKEN($|[^A-Za-z])`,
#     and fails the PR on any match in a non-excluded changed file.
#   - This harness is a LOCAL validator — the authoritative CI signal
#     is the GitHub Actions run on a real PR. The harness verifies the
#     Story 6.2 evidence tree, the workflow file shape, the workflow's
#     inlined bash logic (via local simulation of pattern-load and
#     boundary-guard correctness), the harness-self-integrity, and the
#     eleven-predecessor regression chain.
#   - The regression chain extends Story 6.1's ten-predecessor chain by
#     one (adds Story 6.1 as the eleventh predecessor) — eleven prior
#     harnesses total in the order
#     1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3 / 6.1
#     with per-harness ^PASS: line-count fingerprint
#     ( 1 1 1 1 10 7 7 7 7 7 7 ) measured 2026-04-21.
#   - No Story 1.1 line-155 allowlist amendment is required: the new
#     workflow lives under .github/workflows/, a `.github/` subdirectory,
#     not a `memory/` subdirectory — Story 1.1's allowlist guards
#     `memory/` content only. Story 6.2 is purely additive.
#   - The harness deliberately does NOT run the workflow under `act` or
#     any other local GitHub Actions emulator — local simulation is
#     limited to the bash logic that the workflow inlines
#     (pattern-load, metacharacter escape, boundary-guard alternation,
#     positive/negative fixture assertions).
#
# Gates:
#   task1  baseline-audit evidence present and structured
#          (story-6-2-baseline-audit.md)
#   task2  canonical-blueprint evidence present and structured
#          (story-6-2-canonical-blueprint.md)
#   task3  workflow file shape: existence, non-empty, LF-only, trailing
#          newline, no CR, no tabs, no trailing spaces, line-length
#          <= 200 bytes, expected top-level keys, expected step names,
#          actions/checkout@v5 or @v6, timeout-minutes positive integer
#          <= 10, exclusion-set comment block + grep -vE regex block
#          both include the NEW expanded exclusions
#          (.cursor/skills/, .claude/skills/, .cursor/rules/,
#          _bmad-output/implementation-artifacts/*.yaml), README AC13
#          update holds, docs/pii-denylist.md AC12 update holds.
#   task4  workflow logic simulation: replay pattern-load locally,
#          assert count >= PATTERN_COUNT_FLOOR (25), exercise
#          regex_self_probe (positive + negative fixtures), assert the
#          SAFE-TO-PUBLISH anti-self-match guard holds, assert
#          .github/pii-denylist.txt byte-count = 2669 and SHA-256 match.
#   task5  self-check: shebang, set -euo pipefail, every case arm,
#          every declared constant, regex_self_probe via `declare -F`.
#   task6  regression: iterate the eleven predecessor harnesses in
#          `all` mode, require exit 0, assert per-harness ^PASS:
#          line-count matches REGRESSION_PASS_COUNTS positional entry.
#   all    runs every gate in order — exits 0 with exactly 7 ^PASS:
#          lines.
#
# Invocation:
#   bash _bmad-output/implementation-artifacts/tests/story-6-2-github-action-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no mapfile, no associative
# arrays, no namerefs). Uses only bash, grep, find, awk, sed, wc,
# head, tail, tr, sort, cut, od, and shell built-ins. BSD-grep AND
# GNU-grep compatible. No rg, jq, yq, node, or Python.

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

# Per-harness ^PASS: line-count fingerprint for the eleven predecessors
# (positional parallel to the harness invocation order in check_task6).
# Measured 2026-04-21 per story-6-2-baseline-audit.md.
REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 7 )

# Sanity floor for the loaded pattern count after stripping comments,
# blanks, and the two fork-local sentinels. Story 6.2 AC3 codifies
# floor >= 25; observed count at author time is 30.
PATTERN_COUNT_FLOOR=25

# Deny-list byte-stability invariants (Story 6.1 handoff-recorded).
DENYLIST_EXPECTED_BYTES=2669
DENYLIST_EXPECTED_SHA256='b5b11a2c9d7da38308a9f8a1e95de5e89eb2111d2aa3a9e3ff7663bb434d681c'

# AC10 README floor carried forward from Story 6.1.
README_MIN_LINES=34

# Workflow line-length budget per Story 6.2 canonical blueprint.
WORKFLOW_MAX_LINE_BYTES=200

# Substrings that MUST appear on at least one line of the workflow
# file. `grep -Fq` substring match; exact wording inside the line is
# at Dev's discretion.
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

# Substrings that MUST appear on at least one line of the workflow
# file (case-insensitive match via `grep -Fiq`). Exact wording at
# Dev's discretion.
EXPECTED_STEP_NAMES=(
  'Checkout'
  'self-integrity'
  'Load banned patterns'
  'Identify changed files'
  'Scan for banned patterns'
  'Report'
)

# New expanded exclusion substrings added in Task 3. Each MUST appear
# in BOTH the workflow's opening YAML comment block AND inside the
# `grep -vE -e` filter block. check_task3 asserts both presences.
EXPANDED_EXCLUSION_TOKENS=(
  '.cursor/skills/'
  '.claude/skills/'
  '.cursor/rules/'
)

# Baseline-audit required H2 section headings (per Task 1 spec).
BASELINE_AUDIT_H2_SECTIONS=(
  '## Pre-existing workflow inventory'
  '## 11-harness regression fingerprint (measured)'
  '## Deny-list byte-stability verification'
  '## Loaded pattern count (post-sentinel-filter)'
  '## Full-tree dry-run scan (zero-match assertion)'
  '## Pre-existing leak flags (if any)'
)

# Canonical blueprint required H2 section headings (per Task 2 spec).
BLUEPRINT_H2_SECTIONS=(
  '## Workflow file shape (YAML)'
  '## Trigger and runtime metadata'
  '## Pattern-loading step (bash)'
  '## Changed-file identification step (bash)'
  '## Exclusion filter (bash)'
  '## Scan step (bash)'
  '## Report step (bash — pass/fail output formats)'
  '## Self-match guard (bash pre-flight)'
  '## Performance budget and optimization rationale'
  '## Harness shape (gates, constants, regex_self_probe)'
)

# Positive / negative fixtures consumed by regex_self_probe().
# Positive:  the literal string 'Derek was here' MUST match the
#            combined boundary-guard alternation regex (start-of-
#            string boundary before 'D', space boundary after 'k').
# Negative:  the literal string 'homepage is fine' MUST NOT match the
#            combined regex (boundary guard blocks 'home' -> 'homep...'
#            because 'p' is in [A-Za-z]). Proves boundary-guard
#            correctness in both directions.
POSITIVE_FIXTURE_CONTENT='Derek was here'
NEGATIVE_FIXTURE_CONTENT='homepage is fine'
# Metacharacter escaping fixtures (F6 fix): ensure the `sed` metachar
# escape in build_combined_regex actually escapes `.` in the pattern
# `derekneighbors.com`. If the escape breaks, the unescaped `.` would
# match any char, so a variant with `X` in place of `.` would match —
# the negative fixture below must NOT match when escaping is intact.
METACHAR_POSITIVE_FIXTURE_CONTENT='visit derekneighbors.com today'
METACHAR_NEGATIVE_FIXTURE_CONTENT='visit derekneighborsXcom today'

# Canonical H2 section list for docs/pii-denylist.md (F8 fix): AC12
# preserves exactly these 7 H2 headings in this order. check_task3
# iterates this list via `grep -Fxq` to catch rename or reorder
# regressions that a bare count-of-7 would miss.
DOC_H2_SECTIONS=(
  '## Purpose'
  '## File location and format'
  '## Categories'
  '## CI consumption'
  '## How to extend'
  '## Relationship to the mirrored `agent-skills` repo'
  '## What does NOT belong in this file'
)

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_file_exists() {
  local path="$1"
  local gate="$2"
  [[ -f "${path}" ]] || fail "${gate}: missing file ${path}"
}

require_file_nonempty() {
  local path="$1"
  local gate="$2"
  [[ -s "${path}" ]] || fail "${gate}: file is empty ${path}"
}

assert_trailing_newline() {
  local path="$1"
  local gate="$2"
  local last_byte
  last_byte="$(tail -c 1 "${path}" | od -An -tx1 | tr -d ' \n')"
  [[ "${last_byte}" == '0a' ]] \
    || fail "${gate}: ${path} missing trailing newline (last byte: 0x${last_byte})"
}

# Replay the workflow's pattern-load step locally: strip comments and
# blanks, drop the two fork-local sentinels, escape POSIX-ERE
# metacharacters per pattern, wrap each escaped pattern in the
# boundary guard `(^|[^A-Za-z])P($|[^A-Za-z])` via alternation combine,
# and echo the combined regex on stdout. Mirrors the Load step of
# .github/workflows/pii-denylist.yml verbatim in bash semantics.
build_combined_regex() {
  local raw p e escaped
  raw="$(grep -vE '^(#|$)' "${DENYLIST_PATH}" \
    | grep -vFx 'DEREK_HOME_ADDRESS_FORK_LOCAL' \
    | grep -vFx 'DEREK_FAMILY_FORK_LOCAL' || true)"
  escaped=""
  while IFS= read -r p; do
    [[ -z "${p}" ]] && continue
    e="$(printf '%s' "${p}" | sed 's/[][(){}.^$|*+?\\]/\\&/g')"
    if [[ -z "${escaped}" ]]; then
      escaped="${e}"
    else
      escaped="${escaped}|${e}"
    fi
  done <<EOF
${raw}
EOF
  printf '%s' '(^|[^A-Za-z])('"${escaped}"')($|[^A-Za-z])'
}

# Fail fast if the combined boundary-guard alternation regex mis-
# behaves on either fixture. Exercises:
#   - positive fixture: 'Derek was here' MUST match (start-of-string
#     boundary, space boundary after 'k').
#   - negative fixture: 'homepage is fine' MUST NOT match (boundary
#     guard blocks 'home' -> 'homepage' because 'p' is in [A-Za-z]).
# Either mismatch is a pattern-load / boundary-guard regression and
# calls fail with a descriptive reason.
regex_self_probe() {
  local regex
  regex="$(build_combined_regex)"
  if [[ -z "${regex}" ]]; then
    fail "regex probe: combined regex is empty — pattern load returned zero patterns"
  fi
  if ! printf '%s' "${POSITIVE_FIXTURE_CONTENT}" | grep -iqE "${regex}"; then
    fail "regex probe: positive fixture '${POSITIVE_FIXTURE_CONTENT}' did not match — pattern-load or boundary-guard regression"
  fi
  if printf '%s' "${NEGATIVE_FIXTURE_CONTENT}" | grep -iqE "${regex}"; then
    fail "regex probe: negative fixture '${NEGATIVE_FIXTURE_CONTENT}' unexpectedly matched — boundary-guard regression (guard must block 'homepage' against 'home')"
  fi
  # Metacharacter-escape fixtures (F6 fix) — verify the `sed` escape of
  # `.` in `derekneighbors.com` held. Positive must match, negative
  # (dot replaced with 'X') MUST NOT match.
  if ! printf '%s' "${METACHAR_POSITIVE_FIXTURE_CONTENT}" | grep -iqE "${regex}"; then
    fail "regex probe: metachar-positive fixture '${METACHAR_POSITIVE_FIXTURE_CONTENT}' did not match — metacharacter-escape regression"
  fi
  if printf '%s' "${METACHAR_NEGATIVE_FIXTURE_CONTENT}" | grep -iqE "${regex}"; then
    fail "regex probe: metachar-negative fixture '${METACHAR_NEGATIVE_FIXTURE_CONTENT}' unexpectedly matched — `.` escape dropped, unescaped dot matches any char"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and structured
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 6.2 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 6.2 Baseline Audit'"

  local section
  for section in "${BASELINE_AUDIT_H2_SECTIONS[@]}"; do
    if ! grep -Fq "${section}" "${BASELINE_AUDIT_PATH}"; then
      fail "${gate}: baseline audit missing required H2 section: ${section}"
    fi
  done
}

# ------------------------------------------------------------------
# task2 — canonical-blueprint evidence present and structured
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq '# Story 6.2 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 6.2 Canonical Blueprint'"

  local section
  for section in "${BLUEPRINT_H2_SECTIONS[@]}"; do
    if ! grep -Fq "${section}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing required H2 section: ${section}"
    fi
  done
}

# ------------------------------------------------------------------
# task3 — workflow file shape + expanded exclusion set + doc/README
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"

  require_file_exists "${WORKFLOW_PATH}" "${gate}"
  require_file_nonempty "${WORKFLOW_PATH}" "${gate}"
  assert_trailing_newline "${WORKFLOW_PATH}" "${gate}"

  local cr_count
  cr_count="$(grep -c $'\r' "${WORKFLOW_PATH}" 2>/dev/null || true)"
  cr_count="$(printf '%s' "${cr_count}" | tr -d '[:space:]')"
  [[ "${cr_count}" == '0' ]] \
    || fail "${gate}: ${WORKFLOW_PATH} contains ${cr_count} CR byte(s) (CRLF line endings forbidden)"

  local tab_count
  tab_count="$(grep -c $'\t' "${WORKFLOW_PATH}" 2>/dev/null || true)"
  tab_count="$(printf '%s' "${tab_count}" | tr -d '[:space:]')"
  [[ "${tab_count}" == '0' ]] \
    || fail "${gate}: ${WORKFLOW_PATH} contains ${tab_count} tab character(s) (YAML forbids tabs)"

  local trailing_space_count
  trailing_space_count="$(grep -cE ' $' "${WORKFLOW_PATH}" 2>/dev/null || true)"
  trailing_space_count="$(printf '%s' "${trailing_space_count}" | tr -d '[:space:]')"
  [[ "${trailing_space_count}" == '0' ]] \
    || fail "${gate}: ${WORKFLOW_PATH} contains ${trailing_space_count} line(s) with trailing spaces"

  local long_lines
  long_lines="$(awk -v max="${WORKFLOW_MAX_LINE_BYTES}" 'length > max' "${WORKFLOW_PATH}" | wc -l | tr -d '[:space:]')"
  [[ "${long_lines}" == '0' ]] \
    || fail "${gate}: ${WORKFLOW_PATH} contains ${long_lines} line(s) exceeding ${WORKFLOW_MAX_LINE_BYTES} bytes"

  # AC2 — expected top-level keys / job-shape substrings present.
  local key
  for key in "${EXPECTED_WORKFLOW_KEYS[@]}"; do
    if ! grep -Fq "${key}" "${WORKFLOW_PATH}"; then
      fail "${gate}: ${WORKFLOW_PATH} missing expected key/substring: '${key}'"
    fi
  done

  # AC2 — expected step names present (case-insensitive substring).
  local step
  for step in "${EXPECTED_STEP_NAMES[@]}"; do
    if ! grep -Fiq "${step}" "${WORKFLOW_PATH}"; then
      fail "${gate}: ${WORKFLOW_PATH} missing expected step name (case-insensitive): '${step}'"
    fi
  done

  # AC2 — checkout action pinned to @v5 or @v6 (v4 disallowed).
  grep -Eq 'actions/checkout@v[56]' "${WORKFLOW_PATH}" \
    || fail "${gate}: ${WORKFLOW_PATH} missing 'actions/checkout@v5' or '@v6' pin"

  # AC2 — timeout-minutes is a positive integer between 1 and 10.
  # F10 fix: accept 10 (prior regex `[1-9]([^0-9]|$)` rejected `10`).
  grep -Eq 'timeout-minutes:[[:space:]]+([1-9]|10)([^0-9]|$)' "${WORKFLOW_PATH}" \
    || fail "${gate}: ${WORKFLOW_PATH} 'timeout-minutes:' must be a positive integer (1-10)"
  if grep -Eq 'timeout-minutes:[[:space:]]+(1[1-9]|[2-9][0-9]|[0-9]{3,})' "${WORKFLOW_PATH}"; then
    fail "${gate}: ${WORKFLOW_PATH} 'timeout-minutes:' exceeds ceiling of 10"
  fi

  # AC4 — original exclusion tokens present (anywhere in the file;
  # substring match). These appear in both the comment block and the
  # grep -vE regex block; count is not asserted here.
  local token
  for token in \
    '.github/pii-denylist.txt' \
    'docs/pii-denylist.md' \
    '_bmad-output/implementation-artifacts' \
    'node_modules'; do
    if ! grep -Fq "${token}" "${WORKFLOW_PATH}"; then
      fail "${gate}: ${WORKFLOW_PATH} exclusion-set comment block missing token: '${token}'"
    fi
  done

  # AC4 (Dev-expanded) — each of the three new directory exclusions
  # MUST appear at least TWICE: once in the YAML comment block AND
  # once inside the grep -vE -e regex block. Count-ge-2 catches the
  # drift where a maintainer updates one location but not the other.
  local expanded occ
  for expanded in "${EXPANDED_EXCLUSION_TOKENS[@]}"; do
    occ="$(grep -Fc "${expanded}" "${WORKFLOW_PATH}" 2>/dev/null || true)"
    occ="$(printf '%s' "${occ}" | tr -d '[:space:]')"
    if (( occ < 2 )); then
      fail "${gate}: expanded exclusion '${expanded}' must appear in BOTH the comment block AND the grep -vE regex block (found ${occ} occurrence(s))"
    fi
  done

  # AC4 (Dev-expanded) — sprint-status.yaml exclusion. The literal
  # comment-block form is `_bmad-output/implementation-artifacts/*.yaml`;
  # the grep -vE regex form is `_bmad-output/implementation-artifacts/.*\.yaml`.
  # Both MUST be present (comment-block audit trail + live regex).
  grep -Fq '_bmad-output/implementation-artifacts/*.yaml' "${WORKFLOW_PATH}" \
    || fail "${gate}: ${WORKFLOW_PATH} missing comment-block entry for '_bmad-output/implementation-artifacts/*.yaml' exclusion"
  grep -Fq '_bmad-output/implementation-artifacts/.*\.yaml' "${WORKFLOW_PATH}" \
    || fail "${gate}: ${WORKFLOW_PATH} missing grep -vE regex entry for '_bmad-output/implementation-artifacts/.*\\.yaml' exclusion"

  # AC13 — README updated to reference the workflow + deny-list + doc.
  require_file_exists "${README_PATH}" "${gate}"
  grep -Fq '.github/workflows/pii-denylist.yml' "${README_PATH}" \
    || fail "${gate}: ${README_PATH} missing reference to '.github/workflows/pii-denylist.yml' (AC13)"
  grep -Fq '.github/pii-denylist.txt' "${README_PATH}" \
    || fail "${gate}: ${README_PATH} missing reference to '.github/pii-denylist.txt' (AC13)"
  grep -Fq 'docs/pii-denylist.md' "${README_PATH}" \
    || fail "${gate}: ${README_PATH} missing reference to 'docs/pii-denylist.md' (AC13)"

  local readme_lines
  readme_lines="$(wc -l < "${README_PATH}" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "${readme_lines}" ]] \
    || fail "${gate}: failed to count lines in ${README_PATH}"
  if (( readme_lines < README_MIN_LINES )); then
    fail "${gate}: ${README_PATH} line count ${readme_lines} is below floor ${README_MIN_LINES} (AC13)"
  fi

  # AC12 — docs/pii-denylist.md has `## CI consumption` heading (no
  # preview suffix), workflow link, and preserved seven-H2 count.
  require_file_exists "${DOC_PATH}" "${gate}"
  grep -Fq '## CI consumption' "${DOC_PATH}" \
    || fail "${gate}: ${DOC_PATH} missing '## CI consumption' heading (AC12)"
  if grep -Fq 'Story 6.2 preview' "${DOC_PATH}"; then
    fail "${gate}: ${DOC_PATH} still contains 'Story 6.2 preview' suffix — AC12 rename not applied"
  fi
  grep -Fq '.github/workflows/pii-denylist.yml' "${DOC_PATH}" \
    || fail "${gate}: ${DOC_PATH} missing link to '.github/workflows/pii-denylist.yml' (AC12)"

  local doc_h2_count
  doc_h2_count="$(grep -c '^## ' "${DOC_PATH}" 2>/dev/null || true)"
  doc_h2_count="$(printf '%s' "${doc_h2_count}" | tr -d '[:space:]')"
  [[ "${doc_h2_count}" == '7' ]] \
    || fail "${gate}: ${DOC_PATH} has ${doc_h2_count} H2 sections, expected 7 (AC12 preserves count)"
  # F8 fix: assert each of the 7 canonical H2 headings exists verbatim.
  # A bare count-of-7 would miss a rename or reorder regression.
  local section
  for section in "${DOC_H2_SECTIONS[@]}"; do
    grep -Fxq "${section}" "${DOC_PATH}" \
      || fail "${gate}: ${DOC_PATH} missing canonical H2 section '${section}'"
  done
}

# ------------------------------------------------------------------
# task4 — workflow logic simulation (pattern load + fixtures +
# anti-self-match + deny-list byte stability)
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"

  require_file_exists "${DENYLIST_PATH}" "${gate}"

  # Replay the workflow's pattern-load step; count >= floor.
  local count
  count="$(grep -vE '^(#|$)' "${DENYLIST_PATH}" \
    | grep -vFx 'DEREK_HOME_ADDRESS_FORK_LOCAL' \
    | grep -vFx 'DEREK_FAMILY_FORK_LOCAL' \
    | wc -l | tr -d '[:space:]')"
  [[ -n "${count}" ]] || fail "${gate}: failed to count loaded pattern lines"
  if (( count < PATTERN_COUNT_FLOOR )); then
    fail "${gate}: loaded pattern count ${count} is below sanity floor ${PATTERN_COUNT_FLOOR}"
  fi

  # Build the combined boundary-guard alternation regex and exercise
  # positive + negative fixtures via regex_self_probe.
  regex_self_probe

  # Anti-self-match guard — the SAFE-TO-PUBLISH sentinel lives ONLY
  # in the header comment block, never in a stripped pattern line.
  # Mirrors the Story 6.1 harness check_task4 guard and the Story 6.2
  # AC9 workflow pre-flight.
  if grep -vE '^(#|$)' "${DENYLIST_PATH}" | grep -Fq 'SAFE-TO-PUBLISH'; then
    fail "${gate}: 'SAFE-TO-PUBLISH' sentinel leaked into a pattern line of ${DENYLIST_PATH} (anti-self-match guard)"
  fi

  # Deny-list byte-count invariant (Story 6.1 handoff value).
  local byte_count
  byte_count="$(wc -c < "${DENYLIST_PATH}" 2>/dev/null | tr -d '[:space:]')"
  [[ "${byte_count}" == "${DENYLIST_EXPECTED_BYTES}" ]] \
    || fail "${gate}: ${DENYLIST_PATH} byte count ${byte_count} != expected ${DENYLIST_EXPECTED_BYTES} (Story 6.1 drift)"

  # Deny-list SHA-256 invariant when shasum is available. macOS and
  # most Linux distros ship shasum; skip silently on exotic hosts.
  if command -v shasum >/dev/null 2>&1; then
    local observed_sha
    observed_sha="$(shasum -a 256 "${DENYLIST_PATH}" | awk '{print $1}')"
    [[ "${observed_sha}" == "${DENYLIST_EXPECTED_SHA256}" ]] \
      || fail "${gate}: ${DENYLIST_PATH} SHA-256 ${observed_sha} != expected ${DENYLIST_EXPECTED_SHA256} (Story 6.1 drift)"
  fi
}

# ------------------------------------------------------------------
# task5 — self-check: harness well-formed and owns the full gate set
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${SELF_PATH}" "${gate}"

  head -n 1 "${SELF_PATH}" | grep -Fxq '#!/usr/bin/env bash' \
    || fail "${gate}: harness missing bash shebang on line 1"
  head -n 2 "${SELF_PATH}" | tail -n 1 | grep -Fxq 'set -euo pipefail' \
    || fail "${gate}: harness missing 'set -euo pipefail' on line 2"

  local required_case
  for required_case in 'task1)' 'task2)' 'task3)' 'task4)' 'task5)' 'task6)' 'all)'; do
    grep -Fq "${required_case}" "${SELF_PATH}" \
      || fail "${gate}: harness missing case branch: ${required_case}"
  done

  local required_const
  for required_const in \
    'PROJECT_ROOT=' \
    'TESTS_DIR=' \
    'SELF_PATH=' \
    'WORKFLOW_PATH=' \
    'DENYLIST_PATH=' \
    'DOC_PATH=' \
    'README_PATH=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'STORY_1_1_HARNESS=' \
    'STORY_1_2_HARNESS=' \
    'STORY_1_3_HARNESS=' \
    'STORY_2_1_HARNESS=' \
    'STORY_2_2_HARNESS=' \
    'STORY_2_3_HARNESS=' \
    'STORY_2_4_HARNESS=' \
    'STORY_3_1_HARNESS=' \
    'STORY_3_2_HARNESS=' \
    'STORY_3_3_HARNESS=' \
    'STORY_6_1_HARNESS=' \
    'REGRESSION_PASS_COUNTS=' \
    'PATTERN_COUNT_FLOOR=' \
    'EXPECTED_WORKFLOW_KEYS=' \
    'EXPECTED_STEP_NAMES=' \
    'POSITIVE_FIXTURE_CONTENT=' \
    'NEGATIVE_FIXTURE_CONTENT=' \
    'METACHAR_POSITIVE_FIXTURE_CONTENT=' \
    'METACHAR_NEGATIVE_FIXTURE_CONTENT=' \
    'DOC_H2_SECTIONS=('; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"
  declare -F fail >/dev/null 2>&1 \
    || fail "${gate}: harness missing fail helper function definition"
  declare -F build_combined_regex >/dev/null 2>&1 \
    || fail "${gate}: harness missing build_combined_regex helper function definition"
}

# ------------------------------------------------------------------
# task6 — regression against eleven predecessor harnesses
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"

  local harness_paths=(
    "${STORY_1_1_HARNESS}"
    "${STORY_1_2_HARNESS}"
    "${STORY_1_3_HARNESS}"
    "${STORY_2_1_HARNESS}"
    "${STORY_2_2_HARNESS}"
    "${STORY_2_3_HARNESS}"
    "${STORY_2_4_HARNESS}"
    "${STORY_3_1_HARNESS}"
    "${STORY_3_2_HARNESS}"
    "${STORY_3_3_HARNESS}"
    "${STORY_6_1_HARNESS}"
  )
  local harness_names=(
    story-1-1-scaffold-validation.sh
    story-1-2-root-files-validation.sh
    story-1-3-root-context-validation.sh
    story-2-1-agent-identity-validation.sh
    story-2-2-guardrail-and-formatting-validation.sh
    story-2-3-work-persona-validation.sh
    story-2-4-benji-inbox-absence-validation.sh
    story-3-1-memory-template-tree-validation.sh
    story-3-2-obsidian-config-validation.sh
    story-3-3-identity-preferences-validation.sh
    story-6-1-pii-denylist-validation.sh
  )

  local total="${#harness_paths[@]}"
  if (( total != ${#REGRESSION_PASS_COUNTS[@]} )); then
    fail "${gate}: internal: REGRESSION_PASS_COUNTS cardinality ${#REGRESSION_PASS_COUNTS[@]} != harness count ${total}"
  fi

  local idx path name expected out pass_count
  for (( idx=0; idx<total; idx++ )); do
    path="${harness_paths[$idx]}"
    name="${harness_names[$idx]}"
    expected="${REGRESSION_PASS_COUNTS[$idx]}"
    require_file_exists "${path}" "${gate}"
    if ! out="$(bash "${path}" all 2>&1)"; then
      echo "${out}" >&2
      fail "${gate}: ${name} all returned non-zero"
    fi
    pass_count="$(printf '%s\n' "${out}" | grep -c '^PASS:' || true)"
    pass_count="$(printf '%s' "${pass_count}" | tr -d '[:space:]')"
    if [[ "${pass_count}" != "${expected}" ]]; then
      echo "${out}" >&2
      fail "${gate}: ${name} emitted ${pass_count} PASS line(s), expected ${expected}"
    fi
  done
}

mode="${1:-all}"
case "${mode}" in
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
  *)
    echo "Usage: $0 {task1|task2|task3|task4|task5|task6|all}" >&2
    exit 2
    ;;
esac
