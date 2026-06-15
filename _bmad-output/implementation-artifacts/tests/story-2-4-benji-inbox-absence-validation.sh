#!/usr/bin/env bash
set -euo pipefail

# Story 2.4 — Confirm benji-inbox-default.mdc is NOT ported — deterministic
# validation harness.
#
# Scope distinction (complementary, not duplicative):
#   - Story 2.3 owns CONTENT-level scrub of agents/personas/work.md via the
#     boundary-guarded regex (^|[^A-Za-z])benji($|[^A-Za-z]).
#   - Story 2.4 (this harness) owns FILE-LEVEL absence assertion of
#     .cursor/rules/benji-inbox-default.mdc and any benji*-shaped rule file.
#   - The two scans are complementary — neither supersedes the other.
#
# This harness is additive over the Story 2.3 regression chain: it invokes
# Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 harnesses under task6 without
# editing any of them.
#
# Gates:
#   task1  baseline-absence-audit evidence (_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md)
#   task2  file-absence assertions: banned rule file absent, no benji-prefixed basename under .cursor/rules/, repo-wide benji*.mdc scan empty outside evidence paths
#   task3  rule-pack integrity: five Story 2.1/2.2 .mdc files + agents/personas/work.md exist and are non-empty; agent-identity.mdc still references the persona
#   task4  content-scrub parity probe: regex_self_probe for the benji boundary guard (benjiman rejected, "benji inbox" accepted)
#   task5  self-check: harness well-formed (shebang, set -euo pipefail, case branches, constants, regex_self_probe function)
#   task6  regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 harnesses (bash <harness> all must exit 0)
#   all    runs every gate in order
#
# Invocation: bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays). Uses only bash,
# grep, awk, sed, find, and shell built-ins. NOTE: ripgrep (rg) is
# intentionally not used — the scans are BSD-grep and GNU-grep compatible.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

STORY_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/2-4-confirm-benji-inbox-default-not-ported.md"
BASELINE_AUDIT_PATH="${TESTS_DIR}/story-2-4-baseline-absence-audit.md"

RULES_DIR="${PROJECT_ROOT}/.cursor/rules"
BANNED_RULE_PATH="${RULES_DIR}/benji-inbox-default.mdc"

# POSIX-ERE basename prefix match, case-explicit via bracket enumeration so
# `shopt -s nocaseglob` is not required (no global shell state mutation).
BENJI_BASENAME_PATTERN='^[Bb][Ee][Nn][Jj][Ii]'

# Content-scrub parity probe regex (reused from Story 2.2 / 2.3 harnesses).
# NOT used for a duplicate content scan of any file — used only by
# regex_self_probe against synthetic input to guard against a mis-parsing
# host grep before any other Story 2.4 gate runs.
BENJI_BOUNDARY_REGEX='(^|[^A-Za-z])benji($|[^A-Za-z])'

PERSONA_PATH="${PROJECT_ROOT}/agents/personas/work.md"
AGENT_IDENTITY_PATH="${RULES_DIR}/agent-identity.mdc"

# Rule-pack integrity list — five rule files that MUST exist and be
# non-empty per AC5 task3 (zero-edit verification that Story 2.4 did not
# accidentally remove the allowed pack while installing the absence
# assertion).
EXPECTED_RULE_FILES="\
agent-identity.mdc
outbound-messaging-guardrail.mdc
memory-vault-protection.mdc
teams-dm-formatting.mdc
email-triage-thread-defaults.mdc"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"
STORY_2_3_HARNESS="${TESTS_DIR}/story-2-3-work-persona-validation.sh"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_file_exists() {
  local path="$1"
  local gate="$2"
  [[ -f "${path}" ]] || fail "${gate}: missing file ${path}"
}

# Fail fast if the host grep mis-parses the POSIX-ERE boundary pattern for
# `benji`. Exercises both a positive case (expected to match) and a negative
# case (expected to NOT match). Guards against a mis-parsing host grep (e.g.
# a BusyBox grep lacking -E, or an environment where $LANG causes bracket
# expressions to misbehave) before any other gate depends on the pattern.
regex_self_probe() {
  # Negative case: `benjiman` must NOT match (boundary guard rejects
  # embedded letters after `benji`).
  if echo "benjiman" | grep -iE "${BENJI_BOUNDARY_REGEX}" >/dev/null; then
    fail "regex probe: benji boundary match admitted 'benjiman' (grep too permissive)"
  fi

  # Positive case: `benji inbox` must match (space after `benji` is a
  # non-letter boundary, the expected shape in a gtd-life content leak).
  if ! echo "benji inbox" | grep -iE "${BENJI_BOUNDARY_REGEX}" >/dev/null; then
    fail "regex probe: benji boundary match rejected legitimate hit 'benji inbox' (grep too strict)"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline-absence-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq "Story 2.4 Baseline Absence Audit" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title 'Story 2.4 Baseline Absence Audit'"

  local section
  for section in \
    "Current .cursor/rules/ inventory" \
    "gtd-life source" \
    "Absence-assertion scope" \
    "Complement to Story 2.3 content scrub" \
    "Banned-filename pattern lock"; do
    if ! grep -Fiq "${section}" "${BASELINE_AUDIT_PATH}"; then
      fail "${gate}: baseline audit missing required section/keyword: ${section}"
    fi
  done

  # Source-of-record reference must be documented.
  grep -Fq "benji-inbox-default.mdc" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing reference to banned filename"

  # Complement-to-Story-2.3 assertion must be explicit.
  grep -Fq "Story 2.3" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Story 2.3 complement note"
}

# ------------------------------------------------------------------
# task2 — file-absence assertions (AC1 primary + AC2 pattern-level + repo-wide)
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"

  # AC1 primary — banned rule path must not exist as a file, symlink, or
  # directory. `[[ ! -e ... ]]` covers all three forms.
  if [[ -e "${BANNED_RULE_PATH}" ]]; then
    fail "${gate}: banned rule file still present: ${BANNED_RULE_PATH}"
  fi

  # AC2 pattern-level — case-insensitive enumeration of `.cursor/rules/`.
  # Iterate every regular file (not extension-indexed globs, which are
  # case-sensitive under default bash) and reject any rule-shaped entry whose
  # lowercased basename contains `benji`. Catches `Benji-Inbox.MDC`,
  # `BENJI_TASKS.markdown`, `my-benji-inbox-default.md`, every case permutation.
  local entry base base_lc
  for entry in "${RULES_DIR}"/*; do
    [[ -f "${entry}" ]] || continue
    base="$(basename "${entry}")"
    base_lc="$(echo "${base}" | tr '[:upper:]' '[:lower:]')"
    case "${base_lc}" in
      *.mdc|*.md|*.markdown) ;;
      *) continue ;;
    esac
    case "${base_lc}" in
      *benji*)
        fail "${gate}: .cursor/rules/ contains benji-named rule file: ${entry}"
        ;;
    esac
    if [[ "${base_lc}" =~ ${BENJI_BASENAME_PATTERN} ]]; then
      fail "${gate}: .cursor/rules/ contains benji-prefixed rule file: ${entry}"
    fi
  done

  # Repository-wide scan — no benji*.mdc / .md / .markdown file may exist
  # anywhere in the repository outside the AC1-allowed exclusions
  # (`_bmad-output/` evidence/spec paths and `.git/` internals). Uses
  # `find -iname` for case-insensitive matching (review fix F1) and drops
  # the previously-undocumented `_bmad/` exclusion to realign with AC1
  # verbatim (review fix F3 — `_bmad/` currently contains no benji files).
  # `find -print | head -n1` is BSD + GNU compatible; avoids GNU-only `-printf`.
  local ext_repo found
  for ext_repo in mdc md markdown; do
    found="$(find "${PROJECT_ROOT}" -type f -iname "benji*.${ext_repo}" \
      -not -path "${PROJECT_ROOT}/_bmad-output/*" \
      -not -path "${PROJECT_ROOT}/.git/*" \
      -print 2>/dev/null | head -n 1 || true)"
    if [[ -n "${found}" ]]; then
      fail "${gate}: repository-wide scan found banned benji*.${ext_repo} file: ${found}"
    fi
  done
}

# ------------------------------------------------------------------
# task3 — rule-pack integrity (Story 2.1/2.2 rule pack + Story 2.3 persona present)
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"

  local rule rule_path
  while IFS= read -r rule; do
    [[ -z "${rule}" ]] && continue
    rule_path="${RULES_DIR}/${rule}"
    [[ -f "${rule_path}" ]] \
      || fail "${gate}: required rule file missing: ${rule_path}"
    [[ -s "${rule_path}" ]] \
      || fail "${gate}: required rule file is empty: ${rule_path}"
  done <<EOF
${EXPECTED_RULE_FILES}
EOF

  # Story 2.3 persona artifact present and non-empty.
  [[ -f "${PERSONA_PATH}" ]] \
    || fail "${gate}: Story 2.3 persona missing: ${PERSONA_PATH}"
  [[ -s "${PERSONA_PATH}" ]] \
    || fail "${gate}: Story 2.3 persona is empty: ${PERSONA_PATH}"

  # Zero-edit guard — identity rule still references the persona (Story 2.1 /
  # 2.3 pointer preserved).
  require_file_exists "${AGENT_IDENTITY_PATH}" "${gate}"
  grep -Fq 'agents/personas/work.md' "${AGENT_IDENTITY_PATH}" \
    || fail "${gate}: ${AGENT_IDENTITY_PATH} no longer references agents/personas/work.md"
}

# ------------------------------------------------------------------
# task4 — content-scrub parity probe (fail-fast host-grep sanity check)
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  # Intentionally NO content-level scan of agents/personas/work.md here —
  # that is Story 2.3's domain. Duplicating the scan would create coupling.
  # This gate proves only that the regex mechanism is working on the host.
  regex_self_probe
  # Belt-and-suspenders: the boundary-guard constant must still be defined
  # (review fix F6 — replaces the prior tautological `gate == 'task4'` check).
  [[ -n "${BENJI_BOUNDARY_REGEX:-}" ]] \
    || fail "${gate}: BENJI_BOUNDARY_REGEX constant is unset"
}

# ------------------------------------------------------------------
# task5 — self-check (harness well-formed and owns the full gate set)
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${SELF_PATH}" "${gate}"

  head -n 1 "${SELF_PATH}" | grep -Fxq '#!/usr/bin/env bash' \
    || fail "${gate}: harness missing bash shebang on line 1"
  grep -Fq 'set -euo pipefail' "${SELF_PATH}" \
    || fail "${gate}: harness missing 'set -euo pipefail'"

  local required_case
  for required_case in 'task1)' 'task2)' 'task3)' 'task4)' 'task5)' 'task6)' 'all)'; do
    grep -Fq "${required_case}" "${SELF_PATH}" \
      || fail "${gate}: harness missing case branch: ${required_case}"
  done

  local required_const
  for required_const in \
    'RULES_DIR=' \
    'BANNED_RULE_PATH=' \
    'BENJI_BASENAME_PATTERN=' \
    'BENJI_BOUNDARY_REGEX=' \
    'PERSONA_PATH=' \
    'AGENT_IDENTITY_PATH=' \
    'EXPECTED_RULE_FILES=' \
    'STORY_1_1_HARNESS=' \
    'STORY_1_2_HARNESS=' \
    'STORY_1_3_HARNESS=' \
    'STORY_2_1_HARNESS=' \
    'STORY_2_2_HARNESS=' \
    'STORY_2_3_HARNESS='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  # Prove the probe is a callable function (review fix F4 — the prior
  # `grep -Fq 'regex_self_probe'` form matched the string anywhere, including
  # comments or call sites, so a deleted function body would still pass).
  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"
}

# ------------------------------------------------------------------
# task6 — regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 harnesses
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  require_file_exists "${STORY_1_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_2_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_3_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_2_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_3_HARNESS}" "${gate}"

  local out
  # Story 2.2 Phase 4 F6 pattern — capture combined stdout/stderr and echo
  # on non-zero exit so a downstream regression surfaces the offending gate.
  if ! out="$(bash "${STORY_1_1_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-1-1-scaffold-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_1_2_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-1-2-root-files-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_1_3_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-1-3-root-context-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_2_1_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-2-1-agent-identity-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_2_2_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-2-2-guardrail-and-formatting-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_2_3_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-2-3-work-persona-validation.sh all returned non-zero"
  fi
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
