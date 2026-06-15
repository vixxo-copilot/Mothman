#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STORY_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/1-3-write-generic-agents-claude-cursorrules.md"
BASELINE_AUDIT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-1-3-baseline-audit.md"
BLUEPRINT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-1-3-canonical-blueprint.md"
TASK6_REPORT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-1-3-task6-validation.md"
TASK7_REPORT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-1-3-task7-handoff.md"

AGENTS_PATH="${PROJECT_ROOT}/AGENTS.md"
CLAUDE_PATH="${PROJECT_ROOT}/CLAUDE.md"
CURSOR_RULES_PATH="${PROJECT_ROOT}/.cursorrules"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_file_exists() {
  local path="$1"
  [[ -f "${path}" ]] || fail "Missing file: ${path}"
}

require_clean_terms() {
  local file="$1"
  if grep -Eiq "(personal|RevivaGo|Derek|gtd-life)" "${file}"; then
    fail "Detected banned terms in ${file}"
  fi
}

require_placeholders() {
  local file="$1"
  grep -Fq "{{employee_name}}" "${file}" || fail "Missing {{employee_name}} in ${file}"
  grep -Fq "{{employee_role}}" "${file}" || fail "Missing {{employee_role}} in ${file}"
}

check_task1() {
  require_file_exists "${BASELINE_AUDIT_PATH}"
  grep -Fq "AGENTS.md: missing" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing AGENTS.md state"
  grep -Fq "CLAUDE.md: missing" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing CLAUDE.md state"
  grep -Fq ".cursorrules: missing" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing .cursorrules state"
  grep -Fq "Scope guard: root files only (AGENTS.md, CLAUDE.md, .cursorrules)" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing scope guard"
  grep -Fq "Epic 2 .cursor/rules pre-implementation: prohibited in Story 1.3" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing Epic 2 boundary"
  grep -Fq "Banned terms: personal, RevivaGo, Derek, gtd-life" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing banned terms list"
}

check_task2() {
  require_file_exists "${BLUEPRINT_PATH}"
  grep -Fq "## Identity" "${BLUEPRINT_PATH}" || fail "Blueprint missing Identity section"
  grep -Fq "## Scope" "${BLUEPRINT_PATH}" || fail "Blueprint missing Scope section"
  grep -Fq "## Tone" "${BLUEPRINT_PATH}" || fail "Blueprint missing Tone section"
  grep -Fq "## Operating Constraints" "${BLUEPRINT_PATH}" || fail "Blueprint missing Operating Constraints section"
  grep -Fq "## Handoff Expectations" "${BLUEPRINT_PATH}" || fail "Blueprint missing Handoff Expectations section"
  require_placeholders "${BLUEPRINT_PATH}"
  require_clean_terms "${BLUEPRINT_PATH}"
}

check_task3() {
  check_task2
  require_file_exists "${AGENTS_PATH}"
  diff -u "${BLUEPRINT_PATH}" "${AGENTS_PATH}" >/dev/null || fail "AGENTS.md does not match canonical blueprint"
  require_clean_terms "${AGENTS_PATH}"
}

check_task4() {
  check_task3
  require_file_exists "${CLAUDE_PATH}"
  diff -u "${AGENTS_PATH}" "${CLAUDE_PATH}" >/dev/null || fail "AGENTS.md and CLAUDE.md are not mirrored"
  require_placeholders "${CLAUDE_PATH}"
  require_clean_terms "${CLAUDE_PATH}"
}

check_task5() {
  require_file_exists "${CURSOR_RULES_PATH}"
  grep -Eiq "outbound" "${CURSOR_RULES_PATH}" || fail ".cursorrules missing outbound messaging guardrail topic"
  grep -Eiq "messag" "${CURSOR_RULES_PATH}" || fail ".cursorrules missing messaging guardrail wording"
  grep -Eiq "memory" "${CURSOR_RULES_PATH}" || fail ".cursorrules missing memory guardrail topic"
  require_placeholders "${CURSOR_RULES_PATH}"
  require_clean_terms "${CURSOR_RULES_PATH}"
}

check_task6() {
  check_task4
  check_task5

  require_placeholders "${AGENTS_PATH}"
  require_placeholders "${CLAUDE_PATH}"
  require_placeholders "${CURSOR_RULES_PATH}"

  require_clean_terms "${AGENTS_PATH}"
  require_clean_terms "${CLAUDE_PATH}"
  require_clean_terms "${CURSOR_RULES_PATH}"

  require_file_exists "${TASK6_REPORT_PATH}"
  grep -Fq "AGENTS/CLAUDE mirror check: pass" "${TASK6_REPORT_PATH}" || fail "Task 6 report missing mirror check"
  grep -Fq "Placeholder coverage check: pass" "${TASK6_REPORT_PATH}" || fail "Task 6 report missing placeholder coverage check"
  grep -Fq ".cursorrules guardrail-topic check: pass" "${TASK6_REPORT_PATH}" || fail "Task 6 report missing guardrail-topic check"
  grep -Fq "Banned-term scan: pass" "${TASK6_REPORT_PATH}" || fail "Task 6 report missing banned-term scan"
}

check_task7() {
  check_task6
  require_file_exists "${TASK7_REPORT_PATH}"
  grep -Fq "story-1-1-scaffold-validation.sh all" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing story-1-1 command evidence"
  grep -Fq "story-1-2-root-files-validation.sh all" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing story-1-2 command evidence"
  grep -Fq "story-1-3-root-context-validation.sh all" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing story-1-3 command evidence"
  grep -Fq "Result: \`PASS: all\`" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing pass-result evidence"
  grep -Fq "AC1 -> AGENTS.md, CLAUDE.md" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing AC1 mapping"
  grep -Fq "AC2 -> .cursorrules" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing AC2 mapping"
  grep -Fq "AC3 -> AGENTS.md, CLAUDE.md, .cursorrules" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing AC3 mapping"
  grep -Fq "AC4 -> AGENTS.md, CLAUDE.md, .cursorrules" "${TASK7_REPORT_PATH}" || fail "Task 7 report missing AC4 mapping"

  if ! grep -Fq "Status: review" "${STORY_PATH}" && ! grep -Fq "Status: done" "${STORY_PATH}"; then
    fail "Story status is neither review nor done"
  fi
  grep -Fq -- "- [x] Task 1 - Baseline audit and scope guard setup (AC: 1, 2, 4)" "${STORY_PATH}" || fail "Task 1 not checked"
  grep -Fq -- "- [x] Task 2 - Define canonical shared instruction blueprint for mirrored root files (AC: 1, 3, 4)" "${STORY_PATH}" || fail "Task 2 not checked"
  grep -Fq -- "- [x] Task 3 - Author \`AGENTS.md\` from the canonical blueprint (AC: 1, 3, 4) **[Parallelizable]**" "${STORY_PATH}" || fail "Task 3 not checked"
  grep -Fq -- "- [x] Task 4 - Author \`CLAUDE.md\` as a mirrored counterpart (AC: 1, 3, 4) **[Parallelizable]**" "${STORY_PATH}" || fail "Task 4 not checked"
  grep -Fq -- "- [x] Task 5 - Author root \`.cursorrules\` guardrail summary (AC: 2, 3, 4) **[Parallelizable]**" "${STORY_PATH}" || fail "Task 5 not checked"
  grep -Fq -- "- [x] Task 6 - Deterministic validation checks for AC compliance (AC: 1, 2, 3, 4)" "${STORY_PATH}" || fail "Task 6 not checked"
  grep -Fq -- "- [x] Task 7 - Regression and handoff readiness package (AC: 1, 2, 3, 4)" "${STORY_PATH}" || fail "Task 7 not checked"
}

mode="${1:-all}"
case "${mode}" in
  task1) check_task1 ;;
  task2) check_task2 ;;
  task3) check_task3 ;;
  task4) check_task4 ;;
  task5) check_task5 ;;
  task6) check_task6 ;;
  task7) check_task7 ;;
  all)
    check_task1
    check_task2
    check_task3
    check_task4
    check_task5
    check_task6
    check_task7
    ;;
  *)
    fail "Unknown mode: ${mode}"
    ;;
esac

echo "PASS: ${mode}"
