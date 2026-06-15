#!/usr/bin/env bash
set -euo pipefail

# Story 6.1 — Write shared PII deny-list config — deterministic validation
# harness.
#
# Scope:
#   - Story 6.1 externalizes the 17-token Story-3.x banned-term lock into
#     a publishable, human-editable single source of truth at
#     .github/pii-denylist.txt. The file is consumed by Story 6.2's
#     GitHub Action (future) as the CI guardrail that blocks PRs which
#     introduce Derek-PII patterns into shipped template content.
#   - File format is a superset of the Pi-hole one-pattern-per-line
#     convention: lines are either (a) a `#`-comment, (b) blank, or
#     (c) a literal-substring pattern token (no leading/trailing
#     whitespace, ≤ 200 bytes). Category-section headers use the exact
#     syntax `# === CATEGORY: <name> ===` so `grep -E` can enumerate
#     them. Story 6.2's workflow wraps each pattern line in a POSIX-ERE
#     boundary-guard regex (^|[^A-Za-z])TOKEN($|[^A-Za-z]) at scan time;
#     Story 6.1's file does NOT pre-escape regex metacharacters.
#   - The regression chain extends Story 3.3's nine-harness chain by one
#     (adds Story 3.3 as the tenth predecessor) — ten prior harnesses
#     total (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2
#     / 3.3). Expected per-harness ^PASS: line-count fingerprint
#     `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7` (measured 2026-04-21).
#   - No Story 1.1 line-155 allowlist amendment is required: `.github/`
#     is a top-level directory outside the `memory/`-subdirectory
#     allowlist scope. Story 6.1 is purely additive — no predecessor
#     harness is edited.
#
# Gates:
#   task1  baseline-audit evidence present and structured
#          (story-6-1-baseline-audit.md)
#   task2  canonical-blueprint evidence present and structured
#          (story-6-1-canonical-blueprint.md)
#   task3  deny-list file shape: existence, non-empty, LF-only, trailing
#          newline, line-length ≤ 200 bytes, no tabs, no trailing
#          spaces; header comment block with five labeled sections per
#          AC6; safe-to-publish sentinel per AC5; six category headers
#          in canonical order per AC3; per-category required tokens;
#          docs/pii-denylist.md present with seven H2 sections per AC9;
#          README.md references both paths per AC10.
#   task4  content scrub per AC5: zero street addresses, zero five-digit
#          zips, zero phone numbers, zero '@' characters; positive
#          coverage of 17 Story-3.x canonical tokens and 12 defence-in-
#          depth fixed-string tokens; anti-self-match guard on the
#          safe-to-publish sentinel.
#   task5  self-check: shebang, set -euo pipefail, all case arms, all
#          declared constants, regex_self_probe via `declare -F`.
#   task6  regression: ten predecessor harnesses invoked in `all` mode;
#          each must exit zero with the expected ^PASS: line-count
#          fingerprint (REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )).
#   all    runs every gate in order — exits 0 with exactly 7 ^PASS: lines.
#
# Invocation:
#   bash _bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays, no
# namerefs). Uses only bash, grep, find, awk, sed, wc, head, tail, tr,
# sort, cut, od, and shell built-ins. BSD-grep AND GNU-grep compatible.
# No rg, jq, yq, node, or Python.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

DENYLIST_PATH="${PROJECT_ROOT}/.github/pii-denylist.txt"
DOC_PATH="${PROJECT_ROOT}/docs/pii-denylist.md"
README_PATH="${PROJECT_ROOT}/README.md"
README_MIN_LINES=34

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-6-1-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-6-1-canonical-blueprint.md"

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

# 17-token Story-3.x canonical banned-term lock (case-folded). Positive
# coverage check in check_task4 asserts each token resolves to at least
# one pattern-line hit via case-insensitive fixed-string match.
CANONICAL_17_TOKENS=(
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
)

# Twelve Story-3.3 Derek-specific defence-in-depth fixed-string tokens.
# Each must match via `grep -Fq` somewhere in the deny-list. Preserves
# exact spelling / case — these are the AC4 second-bullet set.
DEFENSE_IN_DEPTH_TOKENS=(
  Chiron
  MasteryLab
  "Agile Weekly"
  Gangplank
  Integrum
  Omarchy
  Playrix
  derekneighbors.com
  "Queen Creek"
  Deke
  Laurie
  Bobby
)

# Six canonical category names in canonical order per AC3.
EXPECTED_CATEGORIES=(
  Names
  "Home Address"
  Family
  Businesses
  "Blog & Public Content"
  "Personal Scope Words"
)

# Five labeled-section comment-line prefixes that MUST appear in the
# header comment block per AC6. check_task3 asserts each via `grep -Fq`.
HEADER_LABELS=(
  '# Purpose:'
  '# CI contract:'
  '# How to extend:'
  '# Mirror:'
  '# Safe-to-publish policy:'
)

# Sentinel comment line that confirms the "no raw PII in this file"
# self-documenting policy per AC5.
SAFE_PUBLISH_SENTINEL='# SAFE-TO-PUBLISH deny-list'

# Per-harness ^PASS: line-count fingerprint for the ten predecessors.
# Positional parallel to the STORY_*_HARNESS list invoked in task6.
# Measured 2026-04-21 per story-6-1-baseline-audit.md.
REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )

# AC2 per-line byte budget.
MAX_LINE_BYTES=200

# Seven H2 section headings required by AC9 for docs/pii-denylist.md,
# in canonical order per the Story 6.1 blueprint.
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

# Emit the stripped pattern-lines stream (comments + blanks removed).
# Guarded with `|| true` so pipefail does not trip if zero pattern lines.
strip_patterns() {
  grep -vE '^(#|$)' "${DENYLIST_PATH}" || true
}

# Case-insensitive fixed-string membership for the canonical-17 list.
is_canonical_17_token() {
  local needle="$1"
  local lower
  lower="$(printf '%s' "${needle}" | tr '[:upper:]' '[:lower:]')"
  local t
  for t in "${CANONICAL_17_TOKENS[@]}"; do
    if [[ "${t}" == "${lower}" ]]; then
      return 0
    fi
  done
  return 1
}

# Fail fast if the host grep mis-parses any regex used downstream.
# Exercises:
#   - the AC5 street-address regex (positive + negative cases)
#   - the AC5 zip regex (positive + negative cases)
#   - the canonical-17 case-fold membership lookup (upper-case input
#     resolves to the lower-case list entry; a non-member is rejected)
regex_self_probe() {
  local street_re='^[0-9]+ [A-Za-z]+ (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Dr|Drive|Ct|Court|Pl|Place)$'
  if ! echo "123 Main St" | grep -Eq "${street_re}"; then
    fail "regex probe: AC5 street-address regex rejected positive case '123 Main St' (grep too strict)"
  fi
  if echo "# marker: street address (number + street name)" | grep -Eq "${street_re}"; then
    fail "regex probe: AC5 street-address regex admitted marker-comment negative case (grep too permissive)"
  fi

  local zip_re='^[0-9]{5}(-[0-9]{4})?$'
  if ! echo "85298" | grep -Eq "${zip_re}"; then
    fail "regex probe: AC5 zip regex rejected positive case '85298' (grep too strict)"
  fi
  if ! echo "85298-1234" | grep -Eq "${zip_re}"; then
    fail "regex probe: AC5 zip regex rejected positive case '85298-1234' (grep too strict for ZIP+4)"
  fi
  if echo "Derek" | grep -Eq "${zip_re}"; then
    fail "regex probe: AC5 zip regex admitted negative case 'Derek' (grep too permissive)"
  fi

  if ! is_canonical_17_token DEREK; then
    fail "regex probe: canonical-17 case-fold membership rejected upper-case 'DEREK'"
  fi
  if is_canonical_17_token Vixxo; then
    fail "regex probe: canonical-17 case-fold membership admitted non-member 'Vixxo'"
  fi
}

# Extract the body of a named category section — the lines strictly
# between `# === CATEGORY: <name> ===` and the next category header or
# end-of-file. Used by check_task3 for per-category token-presence
# assertions.
extract_category_section() {
  local name="$1"
  awk -v want="${name}" '
    BEGIN { in_sec = 0 }
    $0 == "# === CATEGORY: " want " ===" { in_sec = 1; next }
    in_sec && /^# === CATEGORY: / { exit }
    in_sec { print }
  ' "${DENYLIST_PATH}"
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 6.1 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 6.1 Baseline Audit'"

  local section
  for section in \
    'Per-harness token inventory' \
    'Union-set (deduplicated, case-folded)' \
    'Token → category classification' \
    'Safe-to-publish vs fork-local-only partition' \
    'Pre-existing leak flags' \
    'Measured `^PASS:` line-count fingerprint'; do
    if ! grep -Fq "${section}" "${BASELINE_AUDIT_PATH}"; then
      fail "${gate}: baseline audit missing required section: ${section}"
    fi
  done
}

# ------------------------------------------------------------------
# task2 — canonical-blueprint evidence present and complete
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq '# Story 6.1 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 6.1 Canonical Blueprint'"

  local section
  for section in \
    '## Deny-list file shape' \
    '## Header comment block (exact labeled sections)' \
    '## Category section format and ordering' \
    '## Per-category token inventory' \
    '## Safe-to-publish policy restatement' \
    '## CI consumption contract (forward reference to Story 6.2)' \
    '## Negative-scan patterns (AC5 content-scrub probes)' \
    '## Doc file shape (docs/pii-denylist.md H2 sections)'; do
    if ! grep -Fq "${section}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing required H2 section: ${section}"
    fi
  done

  local label
  for label in "${HEADER_LABELS[@]}"; do
    if ! grep -Fq "${label}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing header-label reference: ${label}"
    fi
  done
  if ! grep -Fq "${SAFE_PUBLISH_SENTINEL}" "${BLUEPRINT_PATH}"; then
    fail "${gate}: blueprint missing safe-to-publish sentinel: ${SAFE_PUBLISH_SENTINEL}"
  fi

  local cat
  for cat in "${EXPECTED_CATEGORIES[@]}"; do
    if ! grep -Fq "# === CATEGORY: ${cat} ===" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing category template: # === CATEGORY: ${cat} ==="
    fi
  done
}

# ------------------------------------------------------------------
# task3 — deny-list file shape + doc + README refs
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"

  require_file_exists "${DENYLIST_PATH}" "${gate}"
  require_file_nonempty "${DENYLIST_PATH}" "${gate}"
  assert_trailing_newline "${DENYLIST_PATH}" "${gate}"

  local cr_count
  cr_count="$(grep -c $'\r' "${DENYLIST_PATH}" 2>/dev/null || true)"
  cr_count="$(printf '%s' "${cr_count}" | tr -d '[:space:]')"
  [[ "${cr_count}" == '0' ]] \
    || fail "${gate}: ${DENYLIST_PATH} contains ${cr_count} CR byte(s) (CRLF line endings forbidden)"

  local long_lines
  long_lines="$(awk -v max="${MAX_LINE_BYTES}" 'length > max' "${DENYLIST_PATH}" | wc -l | tr -d '[:space:]')"
  [[ "${long_lines}" == '0' ]] \
    || fail "${gate}: ${DENYLIST_PATH} contains ${long_lines} line(s) exceeding ${MAX_LINE_BYTES} bytes"

  local tab_count
  tab_count="$(grep -c $'\t' "${DENYLIST_PATH}" 2>/dev/null || true)"
  tab_count="$(printf '%s' "${tab_count}" | tr -d '[:space:]')"
  [[ "${tab_count}" == '0' ]] \
    || fail "${gate}: ${DENYLIST_PATH} contains ${tab_count} tab character(s)"

  local trailing_space_count
  trailing_space_count="$(grep -cE ' $' "${DENYLIST_PATH}" 2>/dev/null || true)"
  trailing_space_count="$(printf '%s' "${trailing_space_count}" | tr -d '[:space:]')"
  [[ "${trailing_space_count}" == '0' ]] \
    || fail "${gate}: ${DENYLIST_PATH} contains ${trailing_space_count} line(s) with trailing spaces"

  # AC6 (Phase 4 F9 hardening) — each of the five labeled sections appears
  # at least once ANCHORED AT COLUMN 1 on its own comment line. Prevents
  # false positives from labels inlined in pattern lines or continuation
  # comments. Each label (e.g. `# Purpose:`) is escaped for ERE and matched
  # via `grep -qE '^<escaped_label>'`.
  local label escaped_label
  for label in "${HEADER_LABELS[@]}"; do
    # Escape ERE metacharacters in the label. Labels contain only `# `
    # plus ASCII word characters, spaces, and a trailing `:` — none are
    # ERE metacharacters, so a literal anchor works. Use `grep -F` on a
    # constructed "start-of-line + label" check via `awk` for portability.
    if ! awk -v lbl="${label}" 'index($0, lbl) == 1 { found=1; exit } END { exit !found }' "${DENYLIST_PATH}"; then
      fail "${gate}: ${DENYLIST_PATH} missing header label anchored at column 1: ${label}"
    fi
  done

  # AC5 (Phase 4 F9 hardening) — safe-to-publish sentinel present as its
  # own exact line (no surrounding text). Uses `grep -Fxq` for exact-line
  # match so a future pattern line containing the sentinel substring would
  # not satisfy the AC6 header requirement.
  grep -Fxq "${SAFE_PUBLISH_SENTINEL}" "${DENYLIST_PATH}" \
    || fail "${gate}: ${DENYLIST_PATH} missing safe-to-publish sentinel as exact line: ${SAFE_PUBLISH_SENTINEL}"

  # AC3 — exactly six `# === CATEGORY: ` headers.
  local cat_header_count
  cat_header_count="$(grep -c '^# === CATEGORY: ' "${DENYLIST_PATH}" 2>/dev/null || true)"
  cat_header_count="$(printf '%s' "${cat_header_count}" | tr -d '[:space:]')"
  [[ "${cat_header_count}" == '6' ]] \
    || fail "${gate}: ${DENYLIST_PATH} has ${cat_header_count} '# === CATEGORY: ' header(s), expected 6"

  # AC3 — every expected category header present.
  local cat
  for cat in "${EXPECTED_CATEGORIES[@]}"; do
    if ! grep -Fq "# === CATEGORY: ${cat} ===" "${DENYLIST_PATH}"; then
      fail "${gate}: ${DENYLIST_PATH} missing category header: # === CATEGORY: ${cat} ==="
    fi
  done

  # AC3 — category order matches EXPECTED_CATEGORIES verbatim.
  local actual_order
  actual_order="$(grep -E '^# === CATEGORY: ' "${DENYLIST_PATH}" \
    | sed -E 's/^# === CATEGORY: //; s/ ===$//')"
  local idx=0 actual_name expected_name
  while IFS= read -r actual_name; do
    [[ -z "${actual_name}" ]] && continue
    if (( idx >= ${#EXPECTED_CATEGORIES[@]} )); then
      fail "${gate}: ${DENYLIST_PATH} has extra category '${actual_name}' past canonical position ${idx}"
    fi
    expected_name="${EXPECTED_CATEGORIES[$idx]}"
    if [[ "${actual_name}" != "${expected_name}" ]]; then
      fail "${gate}: ${DENYLIST_PATH} category position ${idx} is '${actual_name}', expected '${expected_name}' (canonical order violated)"
    fi
    idx=$((idx + 1))
  done <<EOF
${actual_order}
EOF
  if (( idx != ${#EXPECTED_CATEGORIES[@]} )); then
    fail "${gate}: ${DENYLIST_PATH} has ${idx} category header(s), expected ${#EXPECTED_CATEGORIES[@]}"
  fi

  # AC3 — per-category required tokens present within their section.
  local section_body token_list token
  local names_required=( Derek Neighbors Deke Laurie Bobby )
  local home_required=( DEREK_HOME_ADDRESS_FORK_LOCAL )
  local family_required=( DEREK_FAMILY_FORK_LOCAL )
  local businesses_required=(
    "Agile Weekly"
    Benji
    Bodybuilding.com
    Chiron
    Flowtopic
    Gangplank
    Integrum
    MasteryLab
    Omarchy
    Playrix
    RevivaGo
  )
  local blog_required=( derekneighbors.com gtd-life gtdlife "Queen Creek" )
  local scope_required=( blog cheyenne daughter dog family home personal son wife wyoming )

  for token in "${names_required[@]}"; do
    section_body="$(extract_category_section "Names")"
    if ! printf '%s\n' "${section_body}" | grep -Fq "${token}"; then
      fail "${gate}: Names section missing required token: '${token}'"
    fi
  done
  for token in "${home_required[@]}"; do
    section_body="$(extract_category_section "Home Address")"
    if ! printf '%s\n' "${section_body}" | grep -Fq "${token}"; then
      fail "${gate}: Home Address section missing required token/sentinel: '${token}'"
    fi
  done
  for token in "${family_required[@]}"; do
    section_body="$(extract_category_section "Family")"
    if ! printf '%s\n' "${section_body}" | grep -Fq "${token}"; then
      fail "${gate}: Family section missing required token/sentinel: '${token}'"
    fi
  done
  for token in "${businesses_required[@]}"; do
    section_body="$(extract_category_section "Businesses")"
    if ! printf '%s\n' "${section_body}" | grep -Fq "${token}"; then
      fail "${gate}: Businesses section missing required token: '${token}'"
    fi
  done
  for token in "${blog_required[@]}"; do
    section_body="$(extract_category_section "Blog & Public Content")"
    if ! printf '%s\n' "${section_body}" | grep -Fq "${token}"; then
      fail "${gate}: Blog & Public Content section missing required token: '${token}'"
    fi
  done
  for token in "${scope_required[@]}"; do
    section_body="$(extract_category_section "Personal Scope Words")"
    if ! printf '%s\n' "${section_body}" | grep -Fq "${token}"; then
      fail "${gate}: Personal Scope Words section missing required token: '${token}'"
    fi
  done

  # AC10 — README references both paths.
  require_file_exists "${README_PATH}" "${gate}"
  grep -Fq '.github/pii-denylist.txt' "${README_PATH}" \
    || fail "${gate}: ${README_PATH} missing reference to '.github/pii-denylist.txt' (AC10)"
  grep -Fq 'docs/pii-denylist.md' "${README_PATH}" \
    || fail "${gate}: ${README_PATH} missing reference to 'docs/pii-denylist.md' (AC10)"

  # AC10 (Phase 4 F8 hardening) — enforce the "README grows, never shrinks"
  # invariant with a concrete line-count floor. Post-Story-6.1 state is
  # 34 lines (pre-Story-6.1 was 33; Task 5 added exactly one bullet under
  # `## Help`). Any future PR that removes README content while preserving
  # the two path substrings would otherwise escape detection by this gate.
  local readme_lines
  readme_lines="$(wc -l < "${README_PATH}" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "${readme_lines}" ]] \
    || fail "${gate}: failed to count lines in ${README_PATH}"
  if (( readme_lines < README_MIN_LINES )); then
    fail "${gate}: ${README_PATH} line count ${readme_lines} is below floor ${README_MIN_LINES} (AC10 'never shrinks' invariant)"
  fi

  # AC9 — doc file present with seven canonical H2 sections.
  require_file_exists "${DOC_PATH}" "${gate}"
  require_file_nonempty "${DOC_PATH}" "${gate}"
  assert_trailing_newline "${DOC_PATH}" "${gate}"

  local doc_cr
  doc_cr="$(grep -c $'\r' "${DOC_PATH}" 2>/dev/null || true)"
  doc_cr="$(printf '%s' "${doc_cr}" | tr -d '[:space:]')"
  [[ "${doc_cr}" == '0' ]] \
    || fail "${gate}: ${DOC_PATH} contains ${doc_cr} CR byte(s) (CRLF line endings forbidden)"

  local h2
  for h2 in "${DOC_H2_SECTIONS[@]}"; do
    if ! grep -Fxq "${h2}" "${DOC_PATH}"; then
      fail "${gate}: ${DOC_PATH} missing canonical H2 section: '${h2}'"
    fi
  done

  # AC9 — doc file itself contains ZERO '@' characters (safe-to-publish
  # invariant applied to the doc per blueprint ## Doc-file-itself
  # safe-to-publish invariant).
  if grep -Fq '@' "${DOC_PATH}"; then
    fail "${gate}: ${DOC_PATH} contains '@' character (AC9 safe-to-publish invariant violated)"
  fi
}

# ------------------------------------------------------------------
# task4 — content scrub (AC5) + positive-coverage assertions
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  regex_self_probe

  require_file_exists "${DENYLIST_PATH}" "${gate}"

  # AC5 probe 1 — street addresses. Applied to stripped pattern-lines.
  local stripped
  stripped="$(strip_patterns)"
  local street_re='^[0-9]+ [A-Za-z]+ (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Dr|Drive|Ct|Court|Pl|Place)$'
  local street_hit
  street_hit="$(printf '%s\n' "${stripped}" | grep -E "${street_re}" || true)"
  if [[ -n "${street_hit}" ]]; then
    echo "${street_hit}" >&2
    fail "${gate}: ${DENYLIST_PATH} contains street-address pattern line(s) — AC5 violated"
  fi

  # AC5 probe 2 — five-digit US ZIP codes (with optional ZIP+4). Applied
  # to stripped pattern-lines.
  local zip_re='^[0-9]{5}(-[0-9]{4})?$'
  local zip_hit
  zip_hit="$(printf '%s\n' "${stripped}" | grep -E "${zip_re}" || true)"
  if [[ -n "${zip_hit}" ]]; then
    echo "${zip_hit}" >&2
    fail "${gate}: ${DENYLIST_PATH} contains five-digit ZIP pattern line(s) — AC5 violated"
  fi

  # AC5 probe 3 — phone numbers. Applied to the whole file (phone number
  # in a comment would also be a PII leak).
  local phone_re='\+?[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}'
  local phone_hit
  phone_hit="$(grep -E "${phone_re}" "${DENYLIST_PATH}" || true)"
  if [[ -n "${phone_hit}" ]]; then
    echo "${phone_hit}" >&2
    fail "${gate}: ${DENYLIST_PATH} contains phone-number pattern — AC5 violated"
  fi

  # AC5 probe 4 — zero '@' characters anywhere in the file.
  if grep -Fq '@' "${DENYLIST_PATH}"; then
    fail "${gate}: ${DENYLIST_PATH} contains '@' character — AC5 violated (no email addresses allowed)"
  fi

  # AC4 — positive coverage of the 17 Story-3.x canonical tokens.
  local token
  for token in "${CANONICAL_17_TOKENS[@]}"; do
    if ! grep -Fiq "${token}" "${DENYLIST_PATH}"; then
      fail "${gate}: ${DENYLIST_PATH} missing case-folded canonical token coverage: '${token}'"
    fi
  done

  # AC4 — defence-in-depth fixed-string coverage (exact case / spelling).
  for token in "${DEFENSE_IN_DEPTH_TOKENS[@]}"; do
    if ! grep -Fq "${token}" "${DENYLIST_PATH}"; then
      fail "${gate}: ${DENYLIST_PATH} missing defence-in-depth fixed-string token: '${token}'"
    fi
  done

  # Anti-self-match guard — the safe-to-publish sentinel MUST live only
  # in the header comment block, never in a stripped pattern line (else
  # Story 6.2's scan would match against the deny-list itself).
  if printf '%s\n' "${stripped}" | grep -Fq 'SAFE-TO-PUBLISH'; then
    fail "${gate}: ${DENYLIST_PATH} safe-to-publish sentinel leaked into a pattern line (anti-self-match guard)"
  fi
}

# ------------------------------------------------------------------
# task5 — self-check (harness well-formed and owns the full gate set)
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
    'DENYLIST_PATH=' \
    'DOC_PATH=' \
    'README_PATH=' \
    'README_MIN_LINES=' \
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
    'CANONICAL_17_TOKENS=' \
    'DEFENSE_IN_DEPTH_TOKENS=' \
    'EXPECTED_CATEGORIES=' \
    'HEADER_LABELS=' \
    'SAFE_PUBLISH_SENTINEL=' \
    'REGRESSION_PASS_COUNTS=' \
    'MAX_LINE_BYTES=' \
    'DOC_H2_SECTIONS='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"
  declare -F fail >/dev/null 2>&1 \
    || fail "${gate}: harness missing fail helper function definition"
  declare -F is_canonical_17_token >/dev/null 2>&1 \
    || fail "${gate}: harness missing is_canonical_17_token helper function definition"
  declare -F extract_category_section >/dev/null 2>&1 \
    || fail "${gate}: harness missing extract_category_section helper function definition"
}

# ------------------------------------------------------------------
# task6 — regression against ten predecessor harnesses
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
  task1) check_task1 ;;
  task2) check_task2 ;;
  task3) check_task3 ;;
  task4) check_task4 ;;
  task5) check_task5 ;;
  task6) check_task6 ;;
  all)
    check_task1
    echo "PASS: task1"
    check_task2
    echo "PASS: task2"
    check_task3
    echo "PASS: task3"
    check_task4
    echo "PASS: task4"
    check_task5
    echo "PASS: task5"
    check_task6
    echo "PASS: task6"
    ;;
  *)
    fail "Unknown mode: ${mode}"
    ;;
esac

echo "PASS: ${mode}"
