#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BLUEPRINT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-1-canonical-blueprint.md"

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

line_of() {
  local needle="$1"
  local path="$2"
  local line
  line="$(grep -nF "${needle}" "${path}" | awk -F: 'NR==1 {print $1}')"
  [[ -n "${line}" ]] || return 1
  printf '%s\n' "${line}"
}

check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq '# Story 7.1 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: missing title '# Story 7.1 Canonical Blueprint'"

  local section
  for section in \
    'Section order lock — `GETTING_STARTED.md`' \
    'Command snippets and expected outcomes lock' \
    'MCP verification contract (five active servers)' \
    'Meeting-prep invocation and artifact contract' \
    'Link contract (canonical and non-redundant)' \
    'Content contract summary (AC mapping for Task 2)'; do
    grep -Fq "${section}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: missing required section '${section}'"
  done

  local h2_1 h2_2 h2_3 h2_4 h2_5 h2_6
  h2_1="$(line_of '## 15-minute quick path' "${BLUEPRINT_PATH}")" \
    || fail "${gate}: missing section lock '## 15-minute quick path'"
  h2_2="$(line_of '## Prerequisites and environment checks' "${BLUEPRINT_PATH}")" \
    || fail "${gate}: missing section lock '## Prerequisites and environment checks'"
  h2_3="$(line_of '## Clone, bootstrap, and first-run setup' "${BLUEPRINT_PATH}")" \
    || fail "${gate}: missing section lock '## Clone, bootstrap, and first-run setup'"
  h2_4="$(line_of '## Verify active MCPs (five-server checklist)' "${BLUEPRINT_PATH}")" \
    || fail "${gate}: missing section lock '## Verify active MCPs (five-server checklist)'"
  h2_5="$(line_of '## Run first meeting prep' "${BLUEPRINT_PATH}")" \
    || fail "${gate}: missing section lock '## Run first meeting prep'"
  h2_6="$(line_of '## Troubleshooting and escalation' "${BLUEPRINT_PATH}")" \
    || fail "${gate}: missing section lock '## Troubleshooting and escalation'"

  [[ "${h2_1}" -lt "${h2_2}" && "${h2_2}" -lt "${h2_3}" && "${h2_3}" -lt "${h2_4}" && "${h2_4}" -lt "${h2_5}" && "${h2_5}" -lt "${h2_6}" ]] \
    || fail "${gate}: section-order lock is not strictly increasing"

  local command_snippet
  for command_snippet in \
    'git --version' \
    'node --version' \
    'npm --version' \
    'npx --version' \
    'docker --version' \
    'sf --version' \
    'git clone YOUR-REPO-URL assistants-template' \
    'cd assistants-template' \
    './bin/init' \
    'npx skills add vixxo-copilot/agent-skills'; do
    grep -Fq "${command_snippet}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: missing command lock '${command_snippet}'"
  done

  local outcome
  for outcome in \
    'memory/me/identity.md created or updated' \
    'agents/personas/work.md created or updated' \
    '.env created from .env.example (or left untouched if already present)' \
    'Post-wizard summary includes PASS/FAIL status per active MCP' \
    'meeting-prep output folder exists under memory/meetings/' \
    'prep.md and meeting.md exist for the target meeting'; do
    grep -Fq "${outcome}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: missing expected-outcome lock '${outcome}'"
  done

  local mcp_key
  for mcp_key in linear github microsoft-365 salesforce gong; do
    grep -Fq "${mcp_key}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: missing MCP contract key '${mcp_key}'"
  done

  local link_path
  for link_path in \
    '[`README.md`](README.md)' \
    '[`docs/setup.md`](docs/setup.md)' \
    '[`docs/mcps.md`](docs/mcps.md)' \
    '[`.cursor/mcp.README.md`](.cursor/mcp.README.md)' \
    '[`bin/init`](bin/init)'; do
    grep -Fq "${link_path}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: missing required link contract entry '${link_path}'"
  done

  if grep -Fq '/Users/' "${BLUEPRINT_PATH}"; then
    fail "${gate}: blueprint contains forbidden local absolute path '/Users/'"
  fi
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
