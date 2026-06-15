#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HANDOFF_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-handoff.md"

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

forbid_regex() {
  local regex="$1"
  local path="$2"
  local gate="$3"
  if grep -nE "${regex}" "${path}" >/dev/null 2>&1; then
    grep -nE "${regex}" "${path}" >&2 || true
    fail "${gate}: forbidden pattern matched /${regex}/ in ${path}"
  fi
}

forbid_non_work_emails() {
  local path="$1"
  local gate="$2"
  local match
  while IFS= read -r match; do
    [[ -z "${match}" ]] && continue
    if ! printf '%s\n' "${match}" | grep -Eq '@vixxo\.com([[:punct:]]|$)'; then
      printf '%s\n' "${match}" >&2
      fail "${gate}: non-work email detected in ${path}"
    fi
  done < <(grep -nE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "${path}" || true)
}

check_task4() {
  local gate="task4"
  require_file_exists "${HANDOFF_PATH}" "${gate}"
  require_file_nonempty "${HANDOFF_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.2 Kickoff Handoff for Story 7.3' \
    '## Kickoff outcome capture (AC4)' \
    '## Routed question and blocker matrix (AC5)' \
    '| Item ID | Type | Captured detail | Route destination | Owner | Due date | Expected SLA |' \
    '`template PR`' \
    '`agent-skills PR`' \
    '`Story 7.3 channel FAQ/discussion`' \
    '## Story 7.3 seed content for `#personal-agents` operations (AC5)' \
    'FAQ seed entries' \
    'Open discussion seed prompts' \
    'Escalation starter queue' \
    '## Guardrails check (AC6)' \
    'No secrets' \
    'No personal email addresses'; do
    require_contains "${required}" "${HANDOFF_PATH}" "${gate}"
  done

  forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${HANDOFF_PATH}" "${gate}"
  forbid_non_work_emails "${HANDOFF_PATH}" "${gate}"
  forbid_regex '\[[^]]+\]\((/Users/|/home/|file://)' "${HANDOFF_PATH}" "${gate}"
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
