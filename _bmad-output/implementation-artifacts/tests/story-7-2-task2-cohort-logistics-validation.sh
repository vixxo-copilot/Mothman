#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ARTIFACT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-7-2-cohort-logistics-routing-map.md"
ARTIFACT_DIR="$(dirname "${ARTIFACT_PATH}")"

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

verify_markdown_links_resolve() {
  local path="$1"
  local gate="$2"
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
        resolved="$(cd "${ARTIFACT_DIR}" && realpath "${target}" 2>/dev/null || true)"
        [[ -n "${resolved}" && -e "${resolved}" ]] \
          || fail "${gate}: markdown link target does not exist: ${target}"
        ;;
    esac
  done < <(grep -oE '\[[^]]+\]\([^)]+\)' "${path}" || true)
}

check_task2() {
  local gate="task2"
  require_file_exists "${ARTIFACT_PATH}" "${gate}"
  require_file_nonempty "${ARTIFACT_PATH}" "${gate}"

  grep -Fq '# Story 7.2 Cohort Logistics and Routing Map' "${ARTIFACT_PATH}" \
    || fail "${gate}: missing title '# Story 7.2 Cohort Logistics and Routing Map'"

  local section
  for section in \
    'Participant matrix (roles and attendance expectations)' \
    'Kickoff invite payload text' \
    'Post-kickoff routing map (Story 7.3 handoff inputs)' \
    'Attendee question and blocker intake contract' \
    'AC coverage map (Task 2)'; do
    grep -Fq "${section}" "${ARTIFACT_PATH}" \
      || fail "${gate}: missing section '${section}'"
  done

  local participant_row
  for participant_row in \
    '| Required attendee |' \
    '| Optional attendee |' \
    '| Facilitator |' \
    '| Backup facilitator |' \
    '| Note-taker |'; do
    grep -Fq "${participant_row}" "${ARTIFACT_PATH}" \
      || fail "${gate}: missing participant matrix row '${participant_row}'"
  done

  local invite_field
  for invite_field in \
    'Purpose:' \
    'Expected outcomes:' \
    'Prerequisites:' \
    'Artifact links:' \
    'Follow-up expectations:' \
    '[`GETTING_STARTED.md`](../../../GETTING_STARTED.md)' \
    '[`docs/setup.md`](../../../docs/setup.md)' \
    '[`docs/mcps.md`](../../../docs/mcps.md)'; do
    grep -Fq "${invite_field}" "${ARTIFACT_PATH}" \
      || fail "${gate}: missing invite payload field '${invite_field}'"
  done

  verify_markdown_links_resolve "${ARTIFACT_PATH}" "${gate}"

  local route_name
  for route_name in "'template PR'" "'agent-skills PR'" "'Story 7.3 channel FAQ'"; do
    grep -Fq "${route_name}" "${ARTIFACT_PATH}" \
      || fail "${gate}: missing route '${route_name}'"
  done

  local notes_field
  for notes_field in \
    'Attendees present' \
    'Key Q&A' \
    'Blockers' \
    'Action item owner' \
    'Action item due date'; do
    grep -Fq "${notes_field}" "${ARTIFACT_PATH}" \
      || fail "${gate}: missing attendee intake field '${notes_field}'"
  done

  if grep -Fq '/Users/' "${ARTIFACT_PATH}"; then
    fail "${gate}: contains forbidden local absolute path '/Users/'"
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
