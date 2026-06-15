#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STORY_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/1-1-scaffold-directory-structure-and-root-files.md"
PROBE_FILES=()

REQUIRED_DIRS=(
  ".cursor/rules"
  "agents/personas"
  "bin"
  "docs"
  "memory"
  "scripts"
)

EMPTY_REQUIRED_DIRS=(
  ".cursor/rules"
  "agents/personas"
  "bin"
  "docs"
  "memory"
  "scripts"
)

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

cleanup_probe_files() {
  local probe
  for probe in "${PROBE_FILES[@]+"${PROBE_FILES[@]}"}"; do
    rm -f "${probe}" 2>/dev/null || true
  done
  if [[ -d "${PROJECT_ROOT}/tmp" ]] && [[ -z "$(ls -A "${PROJECT_ROOT}/tmp" 2>/dev/null)" ]]; then
    rmdir "${PROJECT_ROOT}/tmp" 2>/dev/null || true
  fi
}

trap cleanup_probe_files EXIT

require_dir_exists() {
  local dir="$1"
  if [[ ! -d "${PROJECT_ROOT}/${dir}" ]]; then
    fail "Missing directory: ${dir}"
  fi
}

require_gitkeep_exists() {
  local dir="$1"
  if [[ ! -f "${PROJECT_ROOT}/${dir}/.gitkeep" ]]; then
    fail "Missing .gitkeep in ${dir}"
  fi
}

dir_has_intentional_non_gitkeep_content() {
  local dir="$1"
  local non_gitkeep_entries
  non_gitkeep_entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^\.gitkeep$' || true)"
  [[ -n "${non_gitkeep_entries}" ]]
}

require_gitignore_entry() {
  local entry="$1"
  if [[ ! -f "${PROJECT_ROOT}/.gitignore" ]]; then
    fail "Missing root .gitignore"
  fi
  if ! grep -F -xq "${entry}" "${PROJECT_ROOT}/.gitignore"; then
    fail "Missing .gitignore entry: ${entry}"
  fi
}

check_task1() {
  [[ -f "${STORY_PATH}" ]] || fail "Missing story file: ${STORY_PATH}"
  [[ "${#REQUIRED_DIRS[@]}" -eq 6 ]] || fail "Unexpected REQUIRED_DIRS count"
  [[ "${REQUIRED_DIRS[*]}" == *".cursor/rules"* ]] || fail "Required scaffold list missing .cursor/rules"
  [[ "${REQUIRED_DIRS[*]}" == *"agents/personas"* ]] || fail "Required scaffold list missing agents/personas"
  [[ "${REQUIRED_DIRS[*]}" == *"bin"* ]] || fail "Required scaffold list missing bin"
  [[ "${REQUIRED_DIRS[*]}" == *"docs"* ]] || fail "Required scaffold list missing docs"
  [[ "${REQUIRED_DIRS[*]}" == *"memory"* ]] || fail "Required scaffold list missing memory"
  [[ "${REQUIRED_DIRS[*]}" == *"scripts"* ]] || fail "Required scaffold list missing scripts"
}

check_task2() {
  for dir in "${REQUIRED_DIRS[@]}"; do
    require_dir_exists "$dir"
  done
}

check_task3() {
  for dir in "${EMPTY_REQUIRED_DIRS[@]}"; do
    if ! dir_has_intentional_non_gitkeep_content "$dir"; then
      require_gitkeep_exists "$dir"
    fi
  done
}

check_task4() {
  require_gitignore_entry "node_modules/"
  require_gitignore_entry ".env"
  require_gitignore_entry ".env.*"
  require_gitignore_entry "*.log"
  require_gitignore_entry "tmp/"
}

check_task5() {
  local tmp_probe
  local log_probe
  local env_probe

  check_task2
  check_task3
  check_task4

  tmp_probe="${PROJECT_ROOT}/tmp/story-1-1-ignore-check"
  log_probe="${PROJECT_ROOT}/story-1-1.log"
  env_probe="${PROJECT_ROOT}/.env.test"
  PROBE_FILES=("${tmp_probe}" "${log_probe}" "${env_probe}")

  mkdir -p "${PROJECT_ROOT}/tmp"
  touch "${tmp_probe}" "${log_probe}" "${env_probe}"

  git -C "${PROJECT_ROOT}" check-ignore -v tmp/story-1-1-ignore-check >/dev/null || fail "tmp/ ignore check failed"
  git -C "${PROJECT_ROOT}" check-ignore -v story-1-1.log >/dev/null || fail "*.log ignore check failed"
  git -C "${PROJECT_ROOT}" check-ignore -v .env.test >/dev/null || fail ".env.* ignore check failed"
}

check_task6() {
  local dir
  local entries

  # Scaffold-invariant check. The scaffold's guarantee is that every required
  # directory exists and that each directory's `.gitkeep` sentinel either
  # remains present OR has been superseded by intentional, extension-appropriate
  # content for that surface. Downstream stories add rule files, personas,
  # binaries, memory files, and scripts — we allowlist by extension/filename
  # convention here so each new story does not have to edit this harness.
  #
  # Allowed content per directory (alongside optional .gitkeep):
  #   .cursor/rules   -> any *.mdc file
  #   agents/personas -> any *.md file
  #   bin             -> any executable (no extension filter — bin files vary)
  #   memory          -> any *.md file (memory notes)
  #   scripts         -> any *.sh / *.py / *.js / *.ts file
  for dir in ".cursor/rules" "agents/personas" "bin" "memory" "scripts"; do
    case "${dir}" in
      ".cursor/rules")
        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.mdc)$' || true)"
        ;;
      "agents/personas")
        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.md)$' || true)"
        ;;
      "memory")
        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.md|me|mcp|obsidian|\.obsidian|meetings|people|decisions|reference|inbox|appreciations)$' || true)"
        ;;
      "scripts")
        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|.+\.(sh|py|js|ts|mjs|cjs))$' || true)"
        ;;
      "bin")
        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep|[A-Za-z0-9._-]+)$' || true)"
        ;;
      *)
        entries="$(ls -A "${PROJECT_ROOT}/${dir}" | grep -Ev '^(\.gitkeep)?$' || true)"
        ;;
    esac
    if [[ -n "${entries}" ]]; then
      fail "Unexpected non-scaffold content in ${dir}: ${entries}"
    fi
  done

  if grep -Eiq "(personal|private|home address|ssn|social security)" \
    "${PROJECT_ROOT}/.gitignore" \
    "${PROJECT_ROOT}/.cursor/rules/.gitkeep" \
    "${PROJECT_ROOT}/agents/personas/.gitkeep" \
    "${PROJECT_ROOT}/bin/.gitkeep" \
    "${PROJECT_ROOT}/docs/.gitkeep" \
    "${PROJECT_ROOT}/memory/.gitkeep" \
    "${PROJECT_ROOT}/scripts/.gitkeep"; then
    fail "Detected personal-context terms in scaffold files"
  fi
}

mode="${1:-all}"
case "$mode" in
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
