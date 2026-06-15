#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
GETTING_STARTED_PATH="${PROJECT_ROOT}/GETTING_STARTED.md"
BASELINE_AUDIT_PATH="${TESTS_DIR}/story-7-1-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-7-1-canonical-blueprint.md"
SELF_PATH="${BASH_SOURCE[0]}"

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

require_contains() {
  local needle="$1"
  local path="$2"
  local gate="$3"
  grep -Fq "${needle}" "${path}" || fail "${gate}: missing required content '${needle}' in ${path}"
}

require_markdown_link_once() {
  local link_path="$1"
  local gate="$2"
  local escaped
  escaped="$(printf '%s' "${link_path}" | sed 's/\./\\./g')"
  local count
  count="$(grep -Ec "\\[[^]]+\\]\\(${escaped}\\)" "${GETTING_STARTED_PATH}")"
  [[ "${count}" == '1' ]] || fail "${gate}: markdown link '${link_path}' must appear exactly once (found ${count})"
}

check_h2_order() {
  local gate="$1"
  local current=0
  local heading
  for heading in \
    '## 15-minute quick path' \
    '## Prerequisites and environment checks' \
    '## Clone, bootstrap, and first-run setup' \
    '## Verify active MCPs (five-server checklist)' \
    '## Run first meeting prep' \
    '## Troubleshooting and escalation'; do
    local line
    line="$(grep -n "^${heading}$" "${GETTING_STARTED_PATH}" | cut -d: -f1)"
    [[ -n "${line}" ]] || fail "${gate}: missing heading '${heading}'"
    [[ "${line}" -gt "${current}" ]] || fail "${gate}: heading order invalid at '${heading}'"
    current="${line}"
  done
}

check_task1() {
  local gate="task1"
  require_file_exists "${GETTING_STARTED_PATH}" "${gate}"
  require_file_nonempty "${GETTING_STARTED_PATH}" "${gate}"
  check_h2_order "${gate}"

  local required_section
  for required_section in \
    '# GETTING_STARTED (Vixxo Internal Cohort)' \
    'Vixxo internal cohort onboarding' \
    'Target time: under 15 minutes for a clean workstation.' \
    'Expected wizard prompts and outcomes:' \
    'Interpretation:' \
    'Realistic first scenario:' \
    'Guardrails:' \
    'Escalation path now:' \
    'Forward references for cohort workflows:'; do
    require_contains "${required_section}" "${GETTING_STARTED_PATH}" "${gate}"
  done
}

check_task2() {
  local gate="task2"
  require_file_exists "${GETTING_STARTED_PATH}" "${gate}"
  require_file_nonempty "${GETTING_STARTED_PATH}" "${gate}"

  local cmd
  for cmd in \
    'git --version' \
    'node --version' \
    'npm --version' \
    'npx --version' \
    'docker --version' \
    'sf --version' \
    'git clone YOUR-REPO-URL assistants-template' \
    'cd assistants-template' \
    './bin/init' \
    'npx skills add vixxo-copilot/agent-skills'; do
    require_contains "${cmd}" "${GETTING_STARTED_PATH}" "${gate}"
  done

  local outcome
  for outcome in \
    'memory/me/identity.md' \
    'agents/personas/work.md' \
    '.env.example' \
    'PASS means the server initialized correctly' \
    'FAIL means setup or auth is incomplete' \
    'meeting-prep' \
    '/meeting-prep' \
    'memory/meetings/' \
    'prep.md' \
    'meeting.md'; do
    require_contains "${outcome}" "${GETTING_STARTED_PATH}" "${gate}"
  done

  local mcp_key
  for mcp_key in linear github microsoft-365 salesforce gong; do
    require_contains "${mcp_key}" "${GETTING_STARTED_PATH}" "${gate}"
  done
}

check_task3() {
  local gate="task3"
  require_file_exists "${GETTING_STARTED_PATH}" "${gate}"
  require_file_nonempty "${GETTING_STARTED_PATH}" "${gate}"

  local required_link
  for required_link in \
    'README.md' \
    'docs/setup.md' \
    'docs/mcps.md' \
    '.cursor/mcp.README.md' \
    'bin/init'; do
    require_markdown_link_once "${required_link}" "${gate}"
  done

  if grep -Eq '\[[^]]+\]\((/Users/|/home/|file://)' "${GETTING_STARTED_PATH}"; then
    fail "${gate}: markdown link uses local absolute filesystem path"
  fi

  if grep -Fq '/Users/' "${GETTING_STARTED_PATH}" || grep -Fq '/home/' "${GETTING_STARTED_PATH}"; then
    fail "${gate}: document contains local absolute path literal"
  fi
}

check_task4() {
  local gate="task4"
  require_file_exists "${GETTING_STARTED_PATH}" "${gate}"
  require_file_nonempty "${GETTING_STARTED_PATH}" "${gate}"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"
  require_file_exists "${SELF_PATH}" "${gate}"
  require_file_nonempty "${SELF_PATH}" "${gate}"

  local line1 line2
  line1="$(sed -n '1p' "${SELF_PATH}")"
  line2="$(sed -n '2p' "${SELF_PATH}")"
  [[ "${line1}" == '#!/usr/bin/env bash' ]] || fail "${gate}: harness missing bash shebang on line 1"
  [[ "${line2}" == 'set -euo pipefail' ]] || fail "${gate}: harness missing strict mode on line 2"

  local case_arm
  for case_arm in 'task1)' 'task2)' 'task3)' 'task4)' 'all)'; do
    require_contains "${case_arm}" "${SELF_PATH}" "${gate}"
  done

  local banned_regex
  banned_regex='(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})'
  if grep -nE "${banned_regex}" "${GETTING_STARTED_PATH}" >/dev/null 2>&1; then
    grep -nE "${banned_regex}" "${GETTING_STARTED_PATH}" >&2 || true
    fail "${gate}: GETTING_STARTED.md contains secret-shaped token"
  fi
  if grep -nEi '(^|[^A-Za-z])(derekneighbors\.com|@gmail\.com|personal[^A-Za-z]+email)($|[^A-Za-z])' "${GETTING_STARTED_PATH}" >/dev/null 2>&1; then
    grep -nEi '(^|[^A-Za-z])(derekneighbors\.com|@gmail\.com|personal[^A-Za-z]+email)($|[^A-Za-z])' "${GETTING_STARTED_PATH}" >&2 || true
    fail "${gate}: GETTING_STARTED.md contains forbidden personal-content token"
  fi
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task1)
      check_task1
      echo "PASS: task1"
      ;;
    task2)
      check_task2
      echo "PASS: task2"
      ;;
    task3)
      check_task3
      echo "PASS: task3"
      ;;
    task4)
      check_task4
      echo "PASS: task4"
      ;;
    all)
      check_task1
      echo "PASS: task1"
      check_task2
      echo "PASS: task2"
      check_task3
      echo "PASS: task3"
      check_task4
      echo "PASS: task4"
      echo "PASS: all"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac
}

main "$@"
