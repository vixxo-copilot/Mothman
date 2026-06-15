#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RUNBOOK_PATH="${PROJECT_ROOT}/docs/cohort/7-3-personal-agents-feedback-loop.md"

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
  grep -Fq -- "${needle}" "${path}" || fail "${gate}: missing '${needle}'"
}

forbid_regex() {
  local regex="$1"
  local path="$2"
  local gate="$3"
  if grep -nE "${regex}" "${path}" >/dev/null 2>&1; then
    grep -nE "${regex}" "${path}" >&2 || true
    fail "${gate}: forbidden pattern matched /${regex}/ in ${path}"
  fi
}

check_task3() {
  local gate="task3"
  require_file_exists "${RUNBOOK_PATH}" "${gate}"
  require_file_nonempty "${RUNBOOK_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.3 `#personal-agents` channel operations runbook' \
    '## Canonical channel operations guide' \
    'Channel: `#personal-agents`' \
    '## Starter pinned post template' \
    '[`GETTING_STARTED.md`](../../GETTING_STARTED.md)' \
    '[`docs/setup.md`](../../docs/setup.md)' \
    '[`docs/mcps.md`](../../docs/mcps.md)' \
    '[`Story 7.2 kickoff handoff`](../../_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-handoff.md)' \
    '## Intake templates' \
    '### Question intake template' \
    '### Blocker intake template' \
    '### Skill suggestion intake template' \
    '- Owner:' \
    '- Due date:' \
    '## FAQ promotion rule for repeated questions' \
    'Repeated >=3 times in one calendar week'; do
    require_contains "${required}" "${RUNBOOK_PATH}" "${gate}"
  done

  forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${RUNBOOK_PATH}" "${gate}"
  forbid_regex '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "${RUNBOOK_PATH}" "${gate}"
  forbid_regex '\[[^]]+\]\((/Users/|/home/|file://)' "${RUNBOOK_PATH}" "${gate}"
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task3)
      check_task3
      echo "PASS: task3"
      ;;
    all)
      check_task3
      echo "PASS: task3"
      echo "PASS: all"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac
}

main "$@"
