#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ARTIFACT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-3-triage-policy.md"
SEED_SOURCE_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-handoff.md"

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

check_forbidden_patterns() {
  local gate="$1"
  local pattern
  for pattern in '/Users/' '/home/' 'file://' 'ghp_' 'AKIA' 'AIza' '-----BEGIN'; do
    if grep -Fq -- "${pattern}" "${ARTIFACT_PATH}"; then
      fail "${gate}: contains forbidden pattern '${pattern}'"
    fi
  done
}

check_task2() {
  local gate="task2"
  require_file_exists "${SEED_SOURCE_PATH}" "${gate}"
  require_file_exists "${ARTIFACT_PATH}" "${gate}"
  require_file_nonempty "${ARTIFACT_PATH}" "${gate}"

  require_contains '# Story 7.3 Triage Policy and Routing Matrix' "${gate}"
  require_contains 'Route decision matrix' "${gate}"
  require_contains 'Story 7.2 seed-case routing map' "${gate}"
  require_contains 'Triage tags and minimum intake metadata' "${gate}"
  require_contains 'Guardrails and work-only scope (AC6)' "${gate}"

  require_contains '| Route destination | Use when | Owner default | SLA expectation | Required handoff metadata |' "${gate}"
  local route_name
  for route_name in '`channel FAQ/discussion`' '`template PR`' '`agent-skills PR`'; do
    require_contains "${route_name}" "${gate}"
  done

  local seed_id
  for seed_id in Q-001 Q-002 Q-003 B-001 B-002 B-003 A-001 A-002 A-003; do
    require_contains "\`${seed_id}\`" "${gate}"
  done

  local metadata_field
  for metadata_field in \
    '`item-id`' \
    '`source-thread-link`' \
    '`summary`' \
    '`route-decision`' \
    '`owner`' \
    '`due-date`' \
    '`sla-target`' \
    '`acceptance-signal`'; do
    require_contains "${metadata_field}" "${gate}"
  done

  local triage_tag
  for triage_tag in \
    '`triage/question`' \
    '`triage/blocker`' \
    '`triage/skill-idea`' \
    '`route/faq`' \
    '`route/template-pr`' \
    '`route/agent-skills-pr`'; do
    require_contains "${triage_tag}" "${gate}"
  done

  check_forbidden_patterns "${gate}"
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task2)
      check_task2
      ;;
    all)
      check_task2
      echo "PASS: task2"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac

  echo "PASS: ${mode}"
}

main "$@"
