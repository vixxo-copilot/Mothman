#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RUNBOOK_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-runbook.md"
ROUTING_MAP_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-cohort-logistics-routing-map.md"
ROUTING_MAP_DIR="$(dirname "${ROUTING_MAP_PATH}")"
COHORT_ARTIFACT_PATH="${PROJECT_ROOT}/docs/cohort/7-2-kickoff-artifacts.md"
HANDOFF_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-handoff.md"
CURSOR_RULES_PATH="${PROJECT_ROOT}/.cursorrules"
AGENTS_PATH="${PROJECT_ROOT}/AGENTS.md"
CLAUDE_PATH="${PROJECT_ROOT}/CLAUDE.md"
SPRINT_STATUS_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/sprint-status.yaml"

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

verify_markdown_links_resolve() {
  local path="$1"
  local base_dir="$2"
  local gate="$3"
  local link target resolved
  while IFS= read -r link; do
    target="$(printf '%s\n' "${link}" | sed -E 's/.*\(([^)]+)\).*/\1/')"
    case "${target}" in
      http://*|https://*|mailto:*|\#*)
        continue
        ;;
      /*)
        fail "${gate}: absolute markdown link is not allowed: ${target}"
        ;;
      *)
        resolved="$(cd "${base_dir}" && realpath "${target}" 2>/dev/null || true)"
        [[ -n "${resolved}" && -e "${resolved}" ]] \
          || fail "${gate}: markdown link target does not exist: ${target}"
        ;;
    esac
  done < <(grep -oE '\[[^]]+\]\([^)]+\)' "${path}" || true)
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

check_task1() {
  local gate="task1"
  require_file_exists "${RUNBOOK_PATH}" "${gate}"
  require_file_nonempty "${RUNBOOK_PATH}" "${gate}"

  local required
  for required in \
    '## Objective' \
    '## Kickoff Invite Contract (Metadata + Payload)' \
    'Duration: `30 minutes`' \
    'Invite purpose:' \
    'Expected outcomes:' \
    'Prerequisites:' \
    '## 30-minute Timeboxed Agenda' \
    'Demo segment' \
    'Live setup segment' \
    'Q&A segment' \
    'Total scheduled duration is exactly 30 minutes.' \
    '## Pre-flight Checks'; do
    require_contains "${required}" "${RUNBOOK_PATH}" "${gate}"
  done

  local required_link
  for required_link in \
    'GETTING_STARTED.md' \
    'docs/setup.md' \
    'docs/mcps.md'; do
    require_contains "${required_link}" "${RUNBOOK_PATH}" "${gate}"
  done
}

check_task2() {
  local gate="task2"
  require_file_exists "${ROUTING_MAP_PATH}" "${gate}"
  require_file_nonempty "${ROUTING_MAP_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.2 Cohort Logistics and Routing Map' \
    '## Participant matrix (roles and attendance expectations)' \
    '## Kickoff invite payload text' \
    '## Post-kickoff routing map (Story 7.3 handoff inputs)' \
    '## Attendee question and blocker intake contract' \
    '[`GETTING_STARTED.md`](../../../GETTING_STARTED.md)' \
    '[`docs/setup.md`](../../../docs/setup.md)' \
    '[`docs/mcps.md`](../../../docs/mcps.md)'; do
    require_contains "${required}" "${ROUTING_MAP_PATH}" "${gate}"
  done

  verify_markdown_links_resolve "${ROUTING_MAP_PATH}" "${ROUTING_MAP_DIR}" "${gate}"
}

check_task3() {
  local gate="task3"
  require_file_exists "${COHORT_ARTIFACT_PATH}" "${gate}"
  require_file_nonempty "${COHORT_ARTIFACT_PATH}" "${gate}"

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
    '## Kickoff notes template (AC4)'; do
    require_contains "${required}" "${COHORT_ARTIFACT_PATH}" "${gate}"
  done
}

check_task4() {
  local gate="task4"

  require_file_exists "${CURSOR_RULES_PATH}" "${gate}"
  require_file_exists "${AGENTS_PATH}" "${gate}"
  require_file_exists "${CLAUDE_PATH}" "${gate}"

  local path
  for path in \
    "${RUNBOOK_PATH}" \
    "${ROUTING_MAP_PATH}" \
    "${COHORT_ARTIFACT_PATH}" \
    "${HANDOFF_PATH}"; do
    require_file_exists "${path}" "${gate}"
    require_file_nonempty "${path}" "${gate}"
    forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${path}" "${gate}"
    forbid_non_work_emails "${path}" "${gate}"
    forbid_regex '(/Users/|/home/|file://)' "${path}" "${gate}"
  done
}

check_task5() {
  local gate="task5"

  local evidence_path
  for evidence_path in \
    "${RUNBOOK_PATH}" \
    "${COHORT_ARTIFACT_PATH}" \
    "${HANDOFF_PATH}"; do
    require_file_exists "${evidence_path}" "${gate}"
    require_file_nonempty "${evidence_path}" "${gate}"
  done

  require_file_exists "${SPRINT_STATUS_PATH}" "${gate}"
  require_contains 'epic-7:' "${SPRINT_STATUS_PATH}" "${gate}"
  require_contains '7-2-30-minute-kickoff-with-ai-cohort:' "${SPRINT_STATUS_PATH}" "${gate}"
  grep -A2 '7-2-30-minute-kickoff-with-ai-cohort:' "${SPRINT_STATUS_PATH}" | grep -Eq 'status: (ready-for-dev|review|done)' \
    || fail "${gate}: Story 7.2 sprint status not in expected lifecycle state (ready-for-dev|review|done)"
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
    task5)
      check_task5
      echo "PASS: task5"
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
      check_task5
      echo "PASS: task5"
      echo "PASS: all"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac
}

main "$@"
