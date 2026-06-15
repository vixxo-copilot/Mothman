#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BASELINE_AUDIT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-1-baseline-audit.md"

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

check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 7.1 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 7.1 Baseline Audit'"

  local section
  for section in \
    'Onboarding source inventory' \
    'Command inventory and verification surface' \
    'bin/init observed behavior snapshot' \
    'Setup-flow drift log (docs vs `bin/init`)' \
    'Source-of-truth mapping' \
    'Meeting template output expectations' \
    'AC coverage map (Task 1)' \
    'Source references'; do
    if ! grep -Fq "${section}" "${BASELINE_AUDIT_PATH}"; then
      fail "${gate}: baseline audit missing required section '${section}'"
    fi
  done

  local required_path
  for required_path in \
    'README.md' \
    'docs/setup.md' \
    'docs/mcps.md' \
    '.cursor/mcp.README.md' \
    'bin/init' \
    'memory/meetings/_template/prep.md' \
    'memory/meetings/_template/meeting.md'; do
    grep -Fq "${required_path}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing source path '${required_path}'"
  done

  local mcp_key
  for mcp_key in linear github microsoft-365 salesforce gong; do
    grep -Fq "${mcp_key}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing active MCP key '${mcp_key}'"
  done

  grep -Fq 'npx skills add vixxo-copilot/agent-skills' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing skills install command"

  if grep -Fq '/Users/' "${BASELINE_AUDIT_PATH}"; then
    fail "${gate}: baseline audit contains local absolute path (/Users/)"
  fi
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task1)
      check_task1
      ;;
    all)
      check_task1
      echo "PASS: task1"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac

  echo "PASS: ${mode}"
}

main "$@"
