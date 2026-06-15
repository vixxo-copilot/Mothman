#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CHARTER_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-3-channel-charter.md"
TRIAGE_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-3-triage-policy.md"
RUNBOOK_PATH="${PROJECT_ROOT}/docs/cohort/7-3-personal-agents-feedback-loop.md"
SWEEP_LOG_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-3-weekly-sweep-log.md"
HANDOFF_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-3-task-handoff.md"
SPRINT_STATUS_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/sprint-status.yaml"
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
  grep -Fq -- "${needle}" "${path}" || fail "${gate}: missing '${needle}' in ${path}"
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

check_week_pr_output() {
  local week_heading="$1"
  local gate="$2"
  local week_block
  week_block="$(awk -v heading="${week_heading}" '
    BEGIN { in_block=0 }
    $0 == heading { in_block=1; next }
    /^## Week [0-9]+ sweep/ && in_block { exit }
    in_block { print }
  ' "${SWEEP_LOG_PATH}")"

  [[ -n "${week_block}" ]] || fail "${gate}: missing week block '${week_heading}'"
  printf '%s\n' "${week_block}" | grep -Eq 'https://github.com/vixxo-copilot/(assistants-template|agent-skills)/pull/[0-9]+' \
    || fail "${gate}: ${week_heading} must include at least one PR URL"
}

check_guardrails() {
  local path="$1"
  local gate="$2"
  forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${path}" "${gate}"
  forbid_non_work_emails "${path}" "${gate}"
  forbid_regex '\[[^]]+\]\((/Users/|/home/|file://)' "${path}" "${gate}"
}

check_task1() {
  local gate="task1"
  require_file_exists "${CHARTER_PATH}" "${gate}"
  require_file_nonempty "${CHARTER_PATH}" "${gate}"

  local required
  for required in \
    '## Canonical Channel Metadata' \
    'Channel name: `#personal-agents`' \
    '## Channel Description Contract' \
    '[`assistants-template`](../../../README.md)' \
    '[`agent-skills`](https://github.com/vixxo-copilot/agent-skills)' \
    '## Pinned Content Contract' \
    '[`GETTING_STARTED.md`](../../../GETTING_STARTED.md)' \
    '[`docs/setup.md`](../../../docs/setup.md)' \
    '[`docs/mcps.md`](../../../docs/mcps.md)' \
    '[`Story 7.2 kickoff handoff`](story-7-2-kickoff-handoff.md)' \
    'Starter FAQ seed (from Story 7.2)' \
    '## Guardrails (AC6)'; do
    require_contains "${required}" "${CHARTER_PATH}" "${gate}"
  done
}

check_task2() {
  local gate="task2"
  require_file_exists "${TRIAGE_PATH}" "${gate}"
  require_file_nonempty "${TRIAGE_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.3 Triage Policy and Routing Matrix' \
    '## Route decision matrix' \
    '| Route destination | Use when | Owner default | SLA expectation | Required handoff metadata |' \
    '## Story 7.2 seed-case routing map' \
    '## Triage tags and minimum intake metadata'; do
    require_contains "${required}" "${TRIAGE_PATH}" "${gate}"
  done

  local route_name
  for route_name in '`channel FAQ/discussion`' '`template PR`' '`agent-skills PR`'; do
    require_contains "${route_name}" "${TRIAGE_PATH}" "${gate}"
  done

  local seed_id
  for seed_id in Q-001 Q-002 Q-003 B-001 B-002 B-003 A-001 A-002 A-003; do
    require_contains "\`${seed_id}\`" "${TRIAGE_PATH}" "${gate}"
  done
}

check_task3() {
  local gate="task3"
  require_file_exists "${RUNBOOK_PATH}" "${gate}"
  require_file_nonempty "${RUNBOOK_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.3 `#personal-agents` channel operations runbook' \
    '## Canonical channel operations guide' \
    '## Starter pinned post template' \
    '[`GETTING_STARTED.md`](../../GETTING_STARTED.md)' \
    '[`docs/setup.md`](../../docs/setup.md)' \
    '[`docs/mcps.md`](../../docs/mcps.md)' \
    '[`Story 7.2 kickoff handoff`](../../_bmad-output/implementation-artifacts/tests/story-7-2-kickoff-handoff.md)' \
    '## Intake templates' \
    '### Question intake template' \
    '### Blocker intake template' \
    '### Skill suggestion intake template' \
    '## FAQ promotion rule for repeated questions'; do
    require_contains "${required}" "${RUNBOOK_PATH}" "${gate}"
  done
}

check_task4() {
  local gate="task4"
  require_file_exists "${SWEEP_LOG_PATH}" "${gate}"
  require_file_nonempty "${SWEEP_LOG_PATH}" "${gate}"

  local required
  for required in \
    '# Story 7.3 Weekly Sweep Log' \
    '## Weekly sweep operating contract' \
    '## Week 1 sweep' \
    '## Week 2 sweep' \
    '| Item ID | Source thread | Route destination | Owner | Due date | PR URL | Status |' \
    '### Week 1 escalated blockers' \
    '### Week 2 escalated blockers' \
    '| Blocker ID | Escalation reason | Escalated to | Escalation due date | Status |' \
    'unresolved blocker past SLA'; do
    require_contains "${required}" "${SWEEP_LOG_PATH}" "${gate}"
  done

  check_week_pr_output '## Week 1 sweep' "${gate}"
  check_week_pr_output '## Week 2 sweep' "${gate}"

  # Cross-artifact route consistency for seeded IDs (Task 2 matrix vs weekly sweeps).
  require_contains '| `Q-001` | question | First artifact to open before setup. | `channel FAQ/discussion` |' "${TRIAGE_PATH}" "${gate}"
  require_contains '| `Q-001` | [Thread Q-001](https://teams.microsoft.com/l/message/personal-agents/q-001) | `channel FAQ/discussion` |' "${SWEEP_LOG_PATH}" "${gate}"
  require_contains '| `Q-003` | question | Owner path for skill invocation contract updates. | `agent-skills PR` |' "${TRIAGE_PATH}" "${gate}"
  require_contains '| `Q-003` | [Thread Q-003](https://teams.microsoft.com/l/message/personal-agents/q-003) | `agent-skills PR` |' "${SWEEP_LOG_PATH}" "${gate}"
  require_contains '| `A-001` | action-item | Publish kickoff FAQ seed entries in channel package. | `channel FAQ/discussion` |' "${TRIAGE_PATH}" "${gate}"
  require_contains '| `A-001` | [Thread A-001](https://teams.microsoft.com/l/message/personal-agents/a-001) | `channel FAQ/discussion` |' "${SWEEP_LOG_PATH}" "${gate}"
}

check_task5() {
  local gate="task5"
  local path
  for path in \
    "${CHARTER_PATH}" \
    "${TRIAGE_PATH}" \
    "${RUNBOOK_PATH}" \
    "${SWEEP_LOG_PATH}"; do
    require_file_exists "${path}" "${gate}"
    require_file_nonempty "${path}" "${gate}"
    check_guardrails "${path}" "${gate}"
  done

  require_file_exists "${HANDOFF_PATH}" "${gate}"
  require_file_nonempty "${HANDOFF_PATH}" "${gate}"
  require_contains '## Acceptance Criteria to objective evidence map' "${HANDOFF_PATH}" "${gate}"
  require_contains '- AC7:' "${HANDOFF_PATH}" "${gate}"
  require_contains '- AC8:' "${HANDOFF_PATH}" "${gate}"

  require_file_exists "${SPRINT_STATUS_PATH}" "${gate}"
  require_contains 'epic-7:' "${SPRINT_STATUS_PATH}" "${gate}"
  require_contains '7-3-personal-agents-teams-channel-and-feedback-loop:' "${SPRINT_STATUS_PATH}" "${gate}"
  grep -A2 '7-3-personal-agents-teams-channel-and-feedback-loop:' "${SPRINT_STATUS_PATH}" | grep -Eq 'status: (ready-for-dev|review|done)' \
    || fail "${gate}: Story 7.3 sprint status not in expected lifecycle state (ready-for-dev|review|done)"

  require_file_exists "${SELF_PATH}" "${gate}"
  require_file_nonempty "${SELF_PATH}" "${gate}"
  [[ -x "${SELF_PATH}" ]] || fail "${gate}: harness is not executable ${SELF_PATH}"

  local case_arm
  for case_arm in 'task1)' 'task2)' 'task3)' 'task4)' 'task5)' 'all)'; do
    require_contains "${case_arm}" "${SELF_PATH}" "${gate}"
  done

  local pass_line
  for pass_line in 'PASS: task1' 'PASS: task2' 'PASS: task3' 'PASS: task4' 'PASS: task5' 'PASS: all'; do
    require_contains "${pass_line}" "${SELF_PATH}" "${gate}"
  done
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
