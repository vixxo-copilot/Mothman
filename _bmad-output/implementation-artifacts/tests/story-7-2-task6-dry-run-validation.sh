#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TASK_HANDOFF_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-task-handoff.md"

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
  grep -Fq -- "${needle}" "${path}" || fail "${gate}: missing required content '${needle}' in ${path}"
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

check_task6() {
  local gate="task6"
  require_file_exists "${TASK_HANDOFF_PATH}" "${gate}"
  require_file_nonempty "${TASK_HANDOFF_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.2 Task Handoff (Task 6)' \
    '## Task 6 execution evidence' \
    '### 1) Story 7.2 harness dry-run (`all`)' \
    'bash _bmad-output/implementation-artifacts/tests/story-7-2-kickoff-validation.sh all' \
    'PASS: task5' \
    'PASS: all' \
    '### 2) Story 7.1 reference regression check' \
    'bash _bmad-output/implementation-artifacts/tests/story-7-1-getting-started-validation.sh all' \
    'GETTING_STARTED.md' \
    'docs/setup.md' \
    'docs/mcps.md' \
    '### 3) Task 6 artifact existence gate (RED -> GREEN)' \
    'test -s _bmad-output/implementation-artifacts/tests/story-7-2-task-handoff.md' \
    '## Acceptance Criteria to objective evidence map' \
    '- AC4:' \
    '- AC5:' \
    '- AC7:'; do
    require_contains "${required}" "${TASK_HANDOFF_PATH}" "${gate}"
  done

  forbid_regex '(/Users/|/home/|file://)' "${TASK_HANDOFF_PATH}" "${gate}"
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task6)
      check_task6
      echo "PASS: task6"
      ;;
    all)
      check_task6
      echo "PASS: task6"
      echo "PASS: all"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac
}

main "$@"
