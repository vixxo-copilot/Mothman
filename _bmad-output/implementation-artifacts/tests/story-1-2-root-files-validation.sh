#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STORY_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/1-2-write-generic-readme-license-gitignore.md"
BASELINE_AUDIT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-1-2-baseline-audit.md"
TASK5_REPORT_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests/story-1-2-task5-validation.md"
SETUP_DOC_PATH="${PROJECT_ROOT}/docs/setup.md"
CANONICAL_LICENSE_PATH="${PROJECT_ROOT}/docs/legal/license-vixxo-internal-canonical.md"

REQUIRED_GITIGNORE_ENTRIES=(
  "node_modules/"
  ".env"
  ".env.*"
  "!.env.example"
  "*.log"
  "tmp/"
)

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_file_exists() {
  local path="$1"
  [[ -f "${path}" ]] || fail "Missing file: ${path}"
}

require_gitignore_entry() {
  local entry="$1"
  if ! grep -F -xq "${entry}" "${PROJECT_ROOT}/.gitignore"; then
    fail "Missing .gitignore entry: ${entry}"
  fi
}

require_clean_terms() {
  local file="$1"
  if grep -Eiq "(Derek|RevivaGo|blog|gtd-life)" "${file}"; then
    fail "Detected banned legacy terms in ${file}"
  fi
}

line_number_for_exact() {
  local entry="$1"
  grep -n -F -x "${entry}" "${PROJECT_ROOT}/.gitignore" | cut -d: -f1 | head -n 1
}

check_task1() {
  require_file_exists "${BASELINE_AUDIT_PATH}"
  grep -Fq "README.md: missing" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing README state"
  grep -Fq "LICENSE: missing" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing LICENSE state"
  grep -Fq ".gitignore required patterns: pass" "${BASELINE_AUDIT_PATH}" || fail "Baseline audit missing .gitignore guardrail result"
}

check_task2() {
  local readme_path="${PROJECT_ROOT}/README.md"
  require_file_exists "${readme_path}"
  require_file_exists "${SETUP_DOC_PATH}"
  grep -Fq "# assistants-template" "${readme_path}" || fail "README missing title"
  grep -Fq "Vixxo work assistant starter repository" "${readme_path}" || fail "README missing purpose statement"
  grep -Fq "## Quickstart" "${readme_path}" || fail "README missing quickstart section"
  grep -Eq '\b(git|node|npx)\b' "${readme_path}" || fail "README missing required prerequisite tools"
  grep -Fq "docs/setup.md" "${readme_path}" || fail "README missing setup docs link"
  grep -Fq "npx skills add vixxo-copilot/agent-skills" "${readme_path}" || fail "README missing skills registry install command"
  grep -Fq "## Help" "${readme_path}" || fail "README missing help section"
  require_clean_terms "${readme_path}"
}

check_task3() {
  local license_path="${PROJECT_ROOT}/LICENSE"
  require_file_exists "${license_path}"
  require_file_exists "${CANONICAL_LICENSE_PATH}"
  grep -Fq "Vixxo Internal License" "${license_path}" || fail "LICENSE missing internal license heading"
  grep -Fq "All Rights Reserved." "${license_path}" || fail "LICENSE missing rights reservation"
  grep -Fq "internal business use" "${license_path}" || fail "LICENSE missing internal-use restriction"
  grep -Fq "canonical source text for the repository root \`LICENSE\` file" "${CANONICAL_LICENSE_PATH}" || fail "Canonical license source missing guidance header"
  grep -Fq "Vixxo Internal License" "${CANONICAL_LICENSE_PATH}" || fail "Canonical license source missing license heading"
  diff -u <(tail -n +6 "${CANONICAL_LICENSE_PATH}") "${license_path}" >/dev/null || fail "LICENSE does not match canonical source text"
  require_clean_terms "${license_path}"
}

check_task4() {
  local entry
  local line_env line_env_glob line_env_example

  for entry in "${REQUIRED_GITIGNORE_ENTRIES[@]}"; do
    require_gitignore_entry "${entry}"
  done

  line_env="$(line_number_for_exact ".env")"
  line_env_glob="$(line_number_for_exact ".env.*")"
  line_env_example="$(line_number_for_exact "!.env.example")"
  [[ -n "${line_env}" && -n "${line_env_glob}" && -n "${line_env_example}" ]] || fail "Unable to verify .env rule ordering"
  (( line_env < line_env_glob )) || fail ".env should appear before .env.*"
  (( line_env_glob < line_env_example )) || fail "!.env.example should appear after .env.*"

  git -C "${PROJECT_ROOT}" check-ignore .env.test >/dev/null || fail ".env.* ignore behavior failed"
  if git -C "${PROJECT_ROOT}" check-ignore .env.example >/dev/null; then
    fail ".env.example must remain tracked (not ignored)"
  fi
}

check_task5() {
  check_task2
  check_task3
  check_task4
  require_clean_terms "${PROJECT_ROOT}/README.md"
  require_clean_terms "${PROJECT_ROOT}/LICENSE"
  require_clean_terms "${PROJECT_ROOT}/.gitignore"
  require_file_exists "${TASK5_REPORT_PATH}"
  grep -Fq "README AC checks: pass" "${TASK5_REPORT_PATH}" || fail "Task 5 report missing README validation result"
  grep -Fq "LICENSE AC checks: pass" "${TASK5_REPORT_PATH}" || fail "Task 5 report missing LICENSE validation result"
  grep -Fq "Banned term scan: pass" "${TASK5_REPORT_PATH}" || fail "Task 5 report missing banned-term scan result"
  grep -Fq ".gitignore behavior checks: pass" "${TASK5_REPORT_PATH}" || fail "Task 5 report missing .gitignore behavior result"
}

check_task6() {
  grep -Fq "Status: done" "${STORY_PATH}" || fail "Story status is not done"
  grep -Fq -- "- [x] Task 1 - Validate baseline root-file state and guardrails before edits (AC: 1, 3)" "${STORY_PATH}" || fail "Task 1 not checked"
  grep -Fq -- "- [x] Task 2 - Draft and author \`README.md\` for under-15-minute onboarding (AC: 1, 3) **[Parallelizable]**" "${STORY_PATH}" || fail "Task 2 not checked"
  grep -Fq -- "- [x] Task 3 - Add canonical root \`LICENSE\` with Vixxo-internal licensing text (AC: 2, 3) **[Parallelizable]**" "${STORY_PATH}" || fail "Task 3 not checked"
  grep -Fq -- "- [x] Task 4 - Reconcile \`.gitignore\` with this story scope without regressing Story 1.1 (AC: 3) **[Parallelizable]**" "${STORY_PATH}" || fail "Task 4 not checked"
  grep -Fq -- "- [x] Task 5 - AC validation checks and anti-PII sweep (AC: 1, 2, 3)" "${STORY_PATH}" || fail "Task 5 not checked"
  grep -Fq -- "- [x] Task 6 - Final regression and handoff readiness package (AC: 1, 2, 3)" "${STORY_PATH}" || fail "Task 6 not checked"
  if ! grep -Fq "license source is now anchored to in-repo canonical text" "${STORY_PATH}" \
    && ! grep -Fq "Legal-source assumption:" "${STORY_PATH}"; then
    fail "Story completion notes missing legal-source provenance"
  fi
}

mode="${1:-all}"
case "${mode}" in
  task1) check_task1 ;;
  task2) check_task2 ;;
  task3) check_task3 ;;
  task4) check_task4 ;;
  task5) check_task5 ;;
  task6) check_task6 ;;
  all)
    check_task1
    check_task2
    check_task3
    check_task4
    check_task5
    check_task6
    ;;
  *)
    fail "Unknown mode: ${mode}"
    ;;
esac

echo "PASS: ${mode}"
