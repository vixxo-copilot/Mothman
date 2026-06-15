#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ARTIFACT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-3-weekly-sweep-log.md"

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
  local gate="$2"
  grep -Fq -- "${needle}" "${ARTIFACT_PATH}" || fail "${gate}: missing '${needle}'"
}

forbid_regex() {
  local regex="$1"
  local gate="$2"
  if grep -nE "${regex}" "${ARTIFACT_PATH}" >/dev/null 2>&1; then
    grep -nE "${regex}" "${ARTIFACT_PATH}" >&2 || true
    fail "${gate}: forbidden pattern matched /${regex}/ in ${ARTIFACT_PATH}"
  fi
}

check_week_pr_output() {
  local week_heading="$1"
  local gate="$2"
  local week_block
  week_block="$(awk -v heading="${week_heading}" '
    BEGIN { in_block=0 }
    $0 == heading { in_block=1; next }
    /^## Week [0-9]+ sweep/ && in_block { exit }
    in_block { print }
  ' "${ARTIFACT_PATH}")"

  [[ -n "${week_block}" ]] || fail "${gate}: missing week block '${week_heading}'"
  printf '%s\n' "${week_block}" | grep -Eq 'https://github.com/vixxo-copilot/(assistants-template|agent-skills)/pull/[0-9]+' \
    || fail "${gate}: ${week_heading} must include at least one PR URL"
}

check_task4() {
  local gate="task4"
  require_file_exists "${ARTIFACT_PATH}" "${gate}"
  require_file_nonempty "${ARTIFACT_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.3 Weekly Sweep Log' \
    '## Weekly sweep operating contract' \
    'Cadence:' \
    'Sweep owner:' \
    'Closure protocol:' \
    'Escalation trigger:' \
    'Fallback owner:' \
    '## Week 1 sweep' \
    '## Week 2 sweep' \
    '| Item ID | Source thread | Route destination | Owner | Due date | PR URL | Status |' \
    '### Week 1 escalated blockers' \
    '### Week 2 escalated blockers' \
    '| Blocker ID | Escalation reason | Escalated to | Escalation due date | Status |'; do
    require_contains "${required}" "${gate}"
  done

  check_week_pr_output '## Week 1 sweep' "${gate}"
  check_week_pr_output '## Week 2 sweep' "${gate}"

  require_contains 'unresolved blocker past SLA' "${gate}"
  require_contains 'Escalation due date' "${gate}"

  forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${gate}"
  forbid_regex '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "${gate}"
  forbid_regex '\[[^]]+\]\((/Users/|/home/|file://)' "${gate}"
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task4)
      check_task4
      echo "PASS: task4"
      ;;
    all)
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
