#!/usr/bin/env bash
set -euo pipefail

# Story 2.1 — Port agent-identity rule (generic) — deterministic validation harness.
#
# Gates:
#   task1  baseline-audit-evidence (_bmad-output/implementation-artifacts/tests/story-2-1-baseline-audit.md)
#   task2  canonical-blueprint-evidence (_bmad-output/implementation-artifacts/tests/story-2-1-canonical-blueprint.md)
#   task3  rule file exists, frontmatter shape, required section headers, AC2 tokens
#   task4  banned-term scrub (case-insensitive) + placeholder presence + placeholder parity
#   task5  self-check (harness well-formed and owns a complete gate set)
#   task6  regression against Story 1.1 / 1.2 / 1.3 validation harnesses
#   all    runs every gate in order
#
# Invocation: bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays). Uses only bash, grep, awk, sed.
# NOTE: ripgrep (rg) is intentionally not used — `grep -i -E` is the portable scanner here.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

STORY_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/2-1-port-agent-identity-rule-generic.md"
BASELINE_AUDIT_PATH="${TESTS_DIR}/story-2-1-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-2-1-canonical-blueprint.md"
RULE_PATH="${PROJECT_ROOT}/.cursor/rules/agent-identity.mdc"

AGENTS_PATH="${PROJECT_ROOT}/AGENTS.md"
CLAUDE_PATH="${PROJECT_ROOT}/CLAUDE.md"
CURSOR_RULES_PATH="${PROJECT_ROOT}/.cursorrules"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"

# Required section headers for the ported rule (locked by Task 2 blueprint).
REQUIRED_HEADERS="\
# Agent Identity
## Scope
## Who the Employee Is
## Communication Style
## This Workspace
## Available Tools (overview)
## Work Persona
## Email and Calendar Routing
## Related Rule Files
## Key References"

# Case-insensitive banned-term regex (alternation). Word-boundary guards for
# short substrings that could false-positive on legitimate English (ASU, blog,
# deke, arete, eudaimonia) use POSIX-ERE non-letter boundaries instead of GNU
# `\b`, so the scan behaves identically under macOS BSD grep, GNU grep, and
# busybox/Alpine grep. A fail-fast probe below rejects any host whose grep
# interprets these patterns incorrectly.
BANNED_TERMS_REGEX='derek|(^|[^A-Za-z])deke($|[^A-Za-z])|neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|(^|[^A-Za-z])ASU($|[^A-Za-z])|gtd-life|(^|[^A-Za-z])arete($|[^A-Za-z])|(^|[^A-Za-z])eudaimonia($|[^A-Za-z])|(^|[^A-Za-z])blog($|[^A-Za-z])|gmail|google calendar|google workspace|personal email'

# Story 2.2 deferred-content regex. Outlook Comment workflow, Graph API payloads,
# Teams HTML formatting, and fenced JSON blocks must live in sibling rule files
# added by Story 2.2 — never inlined in the identity rule (AC6).
DEFERRED_CONTENT_REGEX='outlook|graph\.microsoft\.com|"contentType"|"contenttype"|"Comment"|"comment"'

# AC5 required reference paths — the rule must point at these and NOT at
# legacy multi-persona files.
AC5_REQUIRED_REFS='agents/personas/work.md|memory/me/identity.md|memory/me/preferences.md'
AC5_FORBIDDEN_REFS='vixxo-cto\.md|revivago-ceo\.md|personal\.md'

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_file_exists() {
  local path="$1"
  local gate="$2"
  [[ -f "${path}" ]] || fail "${gate}: missing file ${path}"
}

# Fail fast if the host grep mis-parses the POSIX-ERE patterns above. This
# guards against silent fail-open on exotic hosts where `(^|[^A-Za-z])` is
# interpreted incorrectly.
regex_self_probe() {
  echo "XASUX" | grep -iE '(^|[^A-Za-z])ASU($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: ASU boundary match admitted embedded 'XASUX' (grep too permissive)"
  echo "ASU test" | grep -iE '(^|[^A-Za-z])ASU($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: ASU boundary match rejected legitimate hit 'ASU test' (grep too strict)"
  echo "blogger" | grep -iE '(^|[^A-Za-z])blog($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: blog boundary match admitted 'blogger' (grep too permissive)"
  echo "my blog" | grep -iE '(^|[^A-Za-z])blog($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: blog boundary match rejected legitimate hit 'my blog' (grep too strict)"
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq "Story 2.1 Baseline Audit" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title"
  grep -Fq "Source rule" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Source rule section"
  grep -Fq "Target path" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Target path section"
  grep -Fq "Banned-term set" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Banned-term set section"

  local term
  for term in Derek Deke Neighbors Chiron RevivaGo derekneighbors.com \
              "Agile Weekly" MasteryLab Bodybuilding.com Gangplank ASU \
              gtd-life arete eudaimonia blog Gmail "Google Calendar" \
              "Google Workspace" "personal email"; do
    grep -Fq "${term}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing banned term entry: ${term}"
  done

  grep -Fq "Vixxo employee" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing required AC2 token: Vixxo employee"
  grep -Fq "work context only" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing required AC2 token: work context only"
}

# ------------------------------------------------------------------
# task2 — canonical blueprint evidence present and complete
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq "Canonical Blueprint" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Canonical Blueprint title"
  grep -Fq "Frontmatter (locked)" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Frontmatter (locked) section"
  grep -Fq "Section layout (locked order)" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Section layout (locked order) section"
  grep -Fq "Placeholder inventory" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Placeholder inventory section"

  local header
  while IFS= read -r header; do
    [[ -z "${header}" ]] && continue
    grep -Fq "${header}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing locked section header reference: ${header}"
  done <<EOF
${REQUIRED_HEADERS}
EOF

  local ph
  for ph in '{{employee_name}}' '{{employee_role}}' '{{employee_department}}' '{{employee_manager}}'; do
    grep -Fq "${ph}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing placeholder: ${ph}"
  done

  grep -Fq "Vixxo employee" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing AC2 token: Vixxo employee"
  grep -Fq "work context only" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing AC2 token: work context only"
  grep -Fq "alwaysApply: true" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing alwaysApply: true"
}

# ------------------------------------------------------------------
# task3 — rule file exists, frontmatter shape, section headers, AC2 tokens
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${RULE_PATH}" "${gate}"

  # Frontmatter block (opening + closing --- with keys in between).
  local fm_open_line fm_close_line
  fm_open_line="$(grep -n '^---$' "${RULE_PATH}" | head -n 1 | cut -d: -f1 || true)"
  fm_close_line="$(grep -n '^---$' "${RULE_PATH}" | sed -n '2p' | cut -d: -f1 || true)"
  [[ -n "${fm_open_line}" && -n "${fm_close_line}" ]] \
    || fail "${gate}: rule file missing YAML frontmatter delimiters"
  [[ "${fm_open_line}" -eq 1 ]] \
    || fail "${gate}: frontmatter must start on line 1 (found line ${fm_open_line})"
  (( fm_close_line > fm_open_line )) \
    || fail "${gate}: frontmatter block malformed (close <= open)"

  local frontmatter
  frontmatter="$(awk -v a="${fm_open_line}" -v b="${fm_close_line}" 'NR>a && NR<b' "${RULE_PATH}")"
  echo "${frontmatter}" | grep -Eq '^description:[[:space:]]*.+' \
    || fail "${gate}: frontmatter missing description key"
  echo "${frontmatter}" | grep -Eq '^alwaysApply:[[:space:]]*true[[:space:]]*$' \
    || fail "${gate}: frontmatter missing alwaysApply: true"
  # AC4: globs must be empty or omitted. If the key is present, its value must
  # be one of: empty, [], or "". Reject any value that looks like a file glob.
  if echo "${frontmatter}" | grep -Eq '^globs:'; then
    local globs_value
    globs_value="$(echo "${frontmatter}" | awk 'sub(/^globs:[[:space:]]*/,"") {print; exit}')"
    case "${globs_value}" in
      ""|"[]"|'""'|"''") : ;;
      *) fail "${gate}: globs must be empty/[]/\"\" (got: '${globs_value}')" ;;
    esac
  fi

  # Required section headers, exact-line match.
  local header
  while IFS= read -r header; do
    [[ -z "${header}" ]] && continue
    grep -Fxq "${header}" "${RULE_PATH}" \
      || fail "${gate}: rule missing required section header: ${header}"
  done <<EOF
${REQUIRED_HEADERS}
EOF

  # AC2 verbatim tokens.
  grep -Fq "Vixxo employee" "${RULE_PATH}" \
    || fail "${gate}: rule missing verbatim token: Vixxo employee"
  grep -Fq "work context only" "${RULE_PATH}" \
    || fail "${gate}: rule missing verbatim token: work context only"
}

# ------------------------------------------------------------------
# task4 — banned-term scrub + placeholder presence + root-file parity
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${RULE_PATH}" "${gate}"

  # Verify host grep honors the POSIX-ERE boundary patterns before trusting the
  # banned-term scan result. A mis-parsing grep would silently fail open here.
  regex_self_probe

  # Banned-term scan (AC3) — any case-insensitive hit is a FAIL.
  local hit
  hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${RULE_PATH}" || true)"
  if [[ -n "${hit}" ]]; then
    fail "${gate}: banned term(s) detected in ${RULE_PATH}: ${hit}"
  fi

  # Story 2.2 deferred-content scan (AC6) — identity rule must not inline
  # Outlook Comment workflow, Graph API payloads, Teams HTML, or fenced JSON.
  local deferred_hit
  deferred_hit="$(grep -n -i -E "${DEFERRED_CONTENT_REGEX}" "${RULE_PATH}" || true)"
  if [[ -n "${deferred_hit}" ]]; then
    fail "${gate}: Story 2.2 deferred content detected in ${RULE_PATH}: ${deferred_hit}"
  fi
  if grep -nE '^[[:space:]]*```json' "${RULE_PATH}" >/dev/null; then
    fail "${gate}: fenced JSON block detected in ${RULE_PATH} (inline payloads belong to Story 2.2)"
  fi
  if grep -nE '<(div|span|table|tr|td|p|strong|em|br|a)[[:space:]>]' "${RULE_PATH}" >/dev/null; then
    fail "${gate}: inline HTML element detected in ${RULE_PATH} (Teams HTML formatting belongs to Story 2.2)"
  fi

  # AC5 positive assertions: rule references the generic work persona and
  # memory paths, and does NOT reference legacy multi-persona files.
  local ref
  while IFS= read -r ref; do
    [[ -z "${ref}" ]] && continue
    grep -Fq "${ref}" "${RULE_PATH}" \
      || fail "${gate}: AC5 missing required reference: ${ref}"
  done <<EOF
agents/personas/work.md
memory/me/identity.md
memory/me/preferences.md
EOF
  if grep -i -E -q "${AC5_FORBIDDEN_REFS}" "${RULE_PATH}"; then
    fail "${gate}: AC5 legacy persona reference detected in ${RULE_PATH}"
  fi

  # Positive placeholder presence.
  grep -Fq '{{employee_name}}' "${RULE_PATH}" \
    || fail "${gate}: rule missing placeholder {{employee_name}}"
  grep -Fq '{{employee_role}}' "${RULE_PATH}" \
    || fail "${gate}: rule missing placeholder {{employee_role}}"

  # Root-file placeholder parity (AC7): Story 1.3 files must still use matching
  # placeholders and must not hard-code any banned identity/biography term.
  require_file_exists "${AGENTS_PATH}" "${gate}"
  require_file_exists "${CLAUDE_PATH}" "${gate}"
  require_file_exists "${CURSOR_RULES_PATH}" "${gate}"

  local root_file root_hit
  for root_file in "${AGENTS_PATH}" "${CLAUDE_PATH}" "${CURSOR_RULES_PATH}"; do
    grep -Fq '{{employee_name}}' "${root_file}" \
      || fail "${gate}: root file missing {{employee_name}}: ${root_file}"
    grep -Fq '{{employee_role}}' "${root_file}" \
      || fail "${gate}: root file missing {{employee_role}}: ${root_file}"
    root_hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${root_file}" || true)"
    if [[ -n "${root_hit}" ]]; then
      fail "${gate}: root file contains banned identity term: ${root_file}: ${root_hit}"
    fi
  done
}

# ------------------------------------------------------------------
# task5 — self-check: harness is well-formed and owns the full gate set
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

  grep -Fq 'BANNED_TERMS_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing banned-term regex definition"
  grep -Fq 'REQUIRED_HEADERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing required-headers definition"
}

# ------------------------------------------------------------------
# task6 — regression against Story 1.1 / 1.2 / 1.3 harnesses
# ------------------------------------------------------------------
# Story 1.1's task6 scaffold-content guard has been updated to allowlist
# `.cursor/rules/agent-identity.mdc` alongside `.gitkeep`, so Story 2.1's
# legitimate addition of that rule file no longer breaches the scaffold
# invariant. All three Story 1.x harnesses are therefore invoked with `all`
# and must return zero.
check_task6() {
  local gate="task6"
  require_file_exists "${STORY_1_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_2_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_3_HARNESS}" "${gate}"

  bash "${STORY_1_1_HARNESS}" all >/dev/null \
    || fail "${gate}: story-1-1-scaffold-validation.sh all returned non-zero"
  bash "${STORY_1_2_HARNESS}" all >/dev/null \
    || fail "${gate}: story-1-2-root-files-validation.sh all returned non-zero"
  bash "${STORY_1_3_HARNESS}" all >/dev/null \
    || fail "${gate}: story-1-3-root-context-validation.sh all returned non-zero"
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
    check_task2
    check_task3
    check_task4
    check_task5
    check_task6
    ;;
  *)
    fail "Unknown mode: ${mode}"
    ;;
esac

echo "PASS: ${mode}"
