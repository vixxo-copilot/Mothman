#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COHORT_DIR="${PROJECT_ROOT}/docs/cohort"
ARTIFACT_PATH="${COHORT_DIR}/7-2-kickoff-artifacts.md"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_dir_exists() {
  local path="$1"
  local gate="$2"
  [[ -d "${path}" ]] || fail "${gate}: missing directory ${path}"
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

check_task3() {
  local gate="task3"
  require_dir_exists "${COHORT_DIR}" "${gate}"
  require_file_exists "${ARTIFACT_PATH}" "${gate}"
  require_file_nonempty "${ARTIFACT_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.2 Kickoff Artifacts' \
    'Date:' \
    'Facilitator:' \
    'Artifact owner:' \
    '## Kickoff collateral index (AC3)' \
    'Deck link:' \
    'Loom link:' \
    'How to reuse for future cohorts:' \
    '## Kickoff notes template (AC4)' \
    'Attendance' \
    'Key Q&A' \
    'Blockers' \
    'Action items' \
    '| Action ID | Action item | Owner | Due date | Status |' \
    '## Guardrails check (AC6)' \
    'No secrets' \
    'No personal email addresses'; do
    require_contains "${required}" "${ARTIFACT_PATH}" "${gate}"
  done

  forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${ARTIFACT_PATH}" "${gate}"
  forbid_non_work_emails "${ARTIFACT_PATH}" "${gate}"
  forbid_regex '\[[^]]+\]\((/Users/|/home/|file://)' "${ARTIFACT_PATH}" "${gate}"
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
