#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
GETTING_STARTED_PATH="${PROJECT_ROOT}/GETTING_STARTED.md"

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
  grep -Fq "${needle}" "${GETTING_STARTED_PATH}" || fail "${gate}: missing required content '${needle}'"
}

require_markdown_link_once() {
  local link_path="$1"
  local gate="$2"
  local count
  count="$(grep -Ec "\\[[^]]+\\]\\(${link_path//./\\.}\\)" "${GETTING_STARTED_PATH}")"
  [[ "${count}" -eq 1 ]] || fail "${gate}: link '${link_path}' must appear exactly once as markdown link (found ${count})"
}

check_h2_order() {
  local gate="$1"
  local current=0
  local heading
  for heading in \
    '## 15-minute quick path' \
    '## Prerequisites and environment checks' \
    '## Clone, bootstrap, and first-run setup' \
    '## Verify active MCPs (five-server checklist)' \
    '## Run first meeting prep' \
    '## Troubleshooting and escalation'; do
    local line
    line="$(grep -n "^${heading}$" "${GETTING_STARTED_PATH}" | cut -d: -f1)"
    [[ -n "${line}" ]] || fail "${gate}: missing heading '${heading}'"
    [[ "${line}" -gt "${current}" ]] || fail "${gate}: heading order is invalid at '${heading}'"
    current="${line}"
  done
}

check_task3() {
  local gate="task3"
  require_file_exists "${GETTING_STARTED_PATH}" "${gate}"
  require_file_nonempty "${GETTING_STARTED_PATH}" "${gate}"

  check_h2_order "${gate}"

  require_contains 'Vixxo internal cohort onboarding' "${gate}"
  require_contains '15-minute quick path' "${gate}"

  local prereq_cmd
  for prereq_cmd in \
    'git --version' \
    'node --version' \
    'npm --version' \
    'npx --version' \
    'docker --version' \
    'sf --version'; do
    require_contains "${prereq_cmd}" "${gate}"
  done

  require_contains 'Node 24 LTS' "${gate}"
  require_contains 'Node 22 LTS' "${gate}"
  require_contains 'EOL' "${gate}"

  require_contains 'git clone YOUR-REPO-URL assistants-template' "${gate}"
  require_contains 'cd assistants-template' "${gate}"
  require_contains './bin/init' "${gate}"
  require_contains 'memory/me/identity.md' "${gate}"
  require_contains 'agents/personas/work.md' "${gate}"
  require_contains '.env' "${gate}"
  require_contains 'npx skills add vixxo-copilot/agent-skills' "${gate}"

  local mcp_key
  for mcp_key in linear github microsoft-365 salesforce gong; do
    require_contains "${mcp_key}" "${gate}"
  done
  require_contains 'PASS means the server initialized correctly' "${gate}"
  require_contains 'FAIL means setup or auth is incomplete' "${gate}"
  require_contains 'docs/setup.md' "${gate}"
  require_contains 'docs/mcps.md' "${gate}"
  require_contains '.cursor/mcp.README.md' "${gate}"

  require_contains 'meeting-prep' "${gate}"
  require_contains '/meeting-prep' "${gate}"
  require_contains 'memory/meetings/' "${gate}"
  require_contains 'prep.md' "${gate}"
  require_contains 'meeting.md' "${gate}"
  require_contains 'first weekly Vixxo cohort kickoff with platform maintainers' "${gate}"

  require_contains '.env only' "${gate}"
  require_contains 'work-only' "${gate}"
  require_contains 'personal data' "${gate}"
  require_contains 'internal tracker ticket' "${gate}"
  require_contains 'Vixxo AI support channel' "${gate}"
  require_contains 'Story 7.2' "${gate}"
  require_contains 'Story 7.3' "${gate}"

  local required_link
  for required_link in \
    'README.md' \
    'docs/setup.md' \
    'docs/mcps.md' \
    '.cursor/mcp.README.md' \
    'bin/init'; do
    require_markdown_link_once "${required_link}" "${gate}"
  done

  if grep -Fq '/Users/' "${GETTING_STARTED_PATH}"; then
    fail "${gate}: document contains local absolute path (/Users/)"
  fi
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task3)
      check_task3
      ;;
    all)
      check_task3
      echo "PASS: task3"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac

  echo "PASS: ${mode}"
}

main "$@"
