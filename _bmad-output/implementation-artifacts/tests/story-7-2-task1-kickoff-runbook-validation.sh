#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RUNBOOK_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-runbook.md"

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

check_task1() {
  local gate="task1"
  require_file_exists "${RUNBOOK_PATH}" "${gate}"
  require_file_nonempty "${RUNBOOK_PATH}" "${gate}"

  local required
  for required in \
    '## Objective' \
    '## Audience' \
    '## Meeting Success Criteria' \
    '## Kickoff Invite Contract (Metadata + Payload)' \
    'Meeting title:' \
    'Duration: `30 minutes`' \
    'Invite purpose:' \
    'Expected outcomes:' \
    'Prerequisites:' \
    'GETTING_STARTED.md' \
    'docs/setup.md' \
    'docs/mcps.md' \
    '## 30-minute Timeboxed Agenda' \
    'Demo segment' \
    'Live setup segment' \
    'Q&A segment' \
    'Total scheduled duration is exactly 30 minutes.' \
    '## Pre-flight Checks' \
    '## Guardrails (AC6)' \
    'No secrets' \
    'No personal email addresses'; do
    require_contains "${required}" "${RUNBOOK_PATH}" "${gate}"
  done

  forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${RUNBOOK_PATH}" "${gate}"
  forbid_non_work_emails "${RUNBOOK_PATH}" "${gate}"
  forbid_regex '\[[^]]+\]\((/Users/|/home/|file://)' "${RUNBOOK_PATH}" "${gate}"
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task1)
      check_task1
      echo "PASS: task1"
      ;;
    all)
      check_task1
      echo "PASS: task1"
      echo "PASS: all"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac
}

main "$@"
