#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ARTIFACT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-3-channel-charter.md"

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
  require_file_exists "${ARTIFACT_PATH}" "${gate}"
  require_file_nonempty "${ARTIFACT_PATH}" "${gate}"

  local required
  for required in \
    '## Canonical Channel Metadata' \
    'Channel name: `#personal-agents`' \
    'Owning team:' \
    'Default owners:' \
    'Moderation expectations:' \
    '## Channel Description Contract' \
    '[`assistants-template`](../../../README.md)' \
    '[`agent-skills`](https://github.com/vixxo-copilot/agent-skills)' \
    'work-only collaboration surface' \
    '## Pinned Content Contract' \
    '[`GETTING_STARTED.md`](../../../GETTING_STARTED.md)' \
    '[`docs/setup.md`](../../../docs/setup.md)' \
    '[`docs/mcps.md`](../../../docs/mcps.md)' \
    '[`Story 7.2 kickoff handoff`](story-7-2-kickoff-handoff.md)' \
    'Starter FAQ seed (from Story 7.2)' \
    'Who updates pinned content:' \
    'Update cadence:' \
    '## Guardrails (AC6)' \
    'No secrets, tokens, or personal email addresses.' \
    'No local absolute paths'; do
    require_contains "${required}" "${ARTIFACT_PATH}" "${gate}"
  done

  forbid_regex '(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_-]{35}|Bearer [A-Za-z0-9_.-]{20,})' "${ARTIFACT_PATH}" "${gate}"
  forbid_non_work_emails "${ARTIFACT_PATH}" "${gate}"
  forbid_regex '\[[^]]+\]\((/Users/|/home/|file://)' "${ARTIFACT_PATH}" "${gate}"
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
