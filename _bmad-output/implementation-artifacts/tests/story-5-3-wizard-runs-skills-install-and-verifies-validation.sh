#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"

BIN_INIT="${PROJECT_ROOT}/bin/init"
IDENTITY_MD="${PROJECT_ROOT}/memory/me/identity.md"
WORK_PERSONA_MD="${PROJECT_ROOT}/agents/personas/work.md"
ENV_PATH="${PROJECT_ROOT}/.env"
TMP_ROOT="${PROJECT_ROOT}/tmp/story-5-3-harness"
STORY_5_2_FIXTURE_ENV_VAR="BMAD_STORY_5_2_FIXTURE_PATH"
STORY_5_3_FIXTURE_ENV_VAR="BMAD_STORY_5_3_FIXTURE_PATH"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-5-3-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-5-3-canonical-blueprint.md"
STORY_5_2_HARNESS="${TESTS_DIR}/story-5-2-wizard-prompts-and-file-generation-validation.sh"
STORY_5_1_HARNESS="${TESTS_DIR}/story-5-1-bin-init-validation.sh"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"
STORY_2_3_HARNESS="${TESTS_DIR}/story-2-3-work-persona-validation.sh"
STORY_2_4_HARNESS="${TESTS_DIR}/story-2-4-benji-inbox-absence-validation.sh"
STORY_3_1_HARNESS="${TESTS_DIR}/story-3-1-memory-template-tree-validation.sh"
STORY_3_2_HARNESS="${TESTS_DIR}/story-3-2-obsidian-config-validation.sh"
STORY_3_3_HARNESS="${TESTS_DIR}/story-3-3-identity-preferences-validation.sh"
STORY_4_1_HARNESS="${TESTS_DIR}/story-4-1-mcp-json-validation.sh"
STORY_4_2_HARNESS="${TESTS_DIR}/story-4-2-mcp-placeholders-validation.sh"
STORY_4_3_HARNESS="${TESTS_DIR}/story-4-3-env-example-validation.sh"
STORY_4_4_HARNESS="${TESTS_DIR}/story-4-4-setup-and-mcps-docs-validation.sh"

EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )

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

assert_lf_only() {
  local path="$1"
  local gate="$2"
  local cr_count
  cr_count="$(grep -c $'\r' "${path}" 2>/dev/null || true)"
  cr_count="$(printf '%s' "${cr_count}" | tr -d '[:space:]')"
  [[ "${cr_count}" == '0' ]] || fail "${gate}: ${path} contains CR bytes"
}

create_guarded_snapshot() {
  local guard_dir="$1"
  mkdir -p "${guard_dir}"
  cp "${IDENTITY_MD}" "${guard_dir}/identity.md"
  cp "${WORK_PERSONA_MD}" "${guard_dir}/work.md"
  if [[ -f "${ENV_PATH}" ]]; then
    cp "${ENV_PATH}" "${guard_dir}/env"
    printf '%s\n' 'present' >"${guard_dir}/env-state.txt"
  else
    printf '%s\n' 'missing' >"${guard_dir}/env-state.txt"
  fi
}

restore_guarded_files() {
  local guard_dir="$1"
  cp "${guard_dir}/identity.md" "${IDENTITY_MD}"
  cp "${guard_dir}/work.md" "${WORK_PERSONA_MD}"
  if grep -Fxq 'present' "${guard_dir}/env-state.txt"; then
    cp "${guard_dir}/env" "${ENV_PATH}"
  else
    rm -f "${ENV_PATH}"
  fi
}

write_story52_fixture() {
  local fixture_path="$1"
  mkdir -p "$(dirname "${fixture_path}")"
  printf '%s\n' '{"responses":["Jordan Miles","jordan@vixxo.com","Product Manager",["linear","github"]]}' >"${fixture_path}"
}

write_story53_fixture() {
  local fixture_path="$1"
  local skills_status="$2"
  local failing_key="${3:-}"
  mkdir -p "$(dirname "${fixture_path}")"
  node - "${PROJECT_ROOT}" "${fixture_path}" "${skills_status}" "${failing_key}" <<'NODE'
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = process.argv[2];
const fixturePath = process.argv[3];
const skillsStatus = process.argv[4];
const failingKey = process.argv[5] || '';
const mcpConfigPath = path.join(repoRoot, '.cursor', 'mcp.json');
const mcpConfig = JSON.parse(fs.readFileSync(mcpConfigPath, 'utf8'));
const keys = Object.keys(mcpConfig.mcpServers || {});
const payload = {
  skillsInstall: {
    status: skillsStatus,
    reason: skillsStatus === 'PASS' ? 'fixture skills pass' : 'fixture skills fail'
  },
  mcpResults: {}
};
for (const key of keys) {
  const isFail = key === failingKey;
  payload.mcpResults[key] = {
    status: isFail ? 'FAIL' : 'PASS',
    reason: isFail ? 'fixture fail for ' + key : 'fixture pass for ' + key
  };
}
fs.writeFileSync(fixturePath, JSON.stringify(payload), 'utf8');
NODE
}

run_init_with_fixtures() {
  local fixture_52="$1"
  local fixture_53="$2"
  local output_path="$3"
  local exit_code=0
  set +e
  (
    cd "${PROJECT_ROOT}" && \
      env \
        "${STORY_5_2_FIXTURE_ENV_VAR}=${fixture_52}" \
        "${STORY_5_3_FIXTURE_ENV_VAR}=${fixture_53}" \
        ./bin/init >"${output_path}" 2>&1
  )
  exit_code=$?
  set -e
  return "${exit_code}"
}

check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"
  grep -Fq '# Story 5.3 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline title mismatch"
  grep -Fq 'Pre-change SHA-256 fingerprints' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline missing fingerprint section"
  grep -Fq 'Deterministic Story 5.3 fixture payload schema' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline missing fixture schema section"
}

check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"
  grep -Fq '# Story 5.3 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint title mismatch"
  grep -Fq 'Post-wizard call-order lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing call-order lock"
  grep -Fq 'Summary and exit contract lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing summary/exit lock"
}

check_task3() {
  local gate="task3"
  require_file_exists "${BIN_INIT}" "${gate}"
  require_file_nonempty "${BIN_INIT}" "${gate}"
  assert_lf_only "${BIN_INIT}" "${gate}"

  grep -Fq "const STORY_5_3_FIXTURE_ENV_VAR = 'BMAD_STORY_5_3_FIXTURE_PATH';" "${BIN_INIT}" \
    || fail "${gate}: Story 5.3 fixture env var missing"
  grep -Fq "const SKILLS_INSTALL_ARGS = ['skills', 'add', 'vixxo-copilot/agent-skills'];" "${BIN_INIT}" \
    || fail "${gate}: skills install args wiring missing"
  grep -Fq 'function runPostWizardSetup' "${BIN_INIT}" \
    || fail "${gate}: post-wizard coordinator missing"
  grep -Fq 'return await runPostWizardSetup(env);' "${BIN_INIT}" \
    || fail "${gate}: main flow does not invoke post-wizard setup"

  local out
  out="$(cd "${PROJECT_ROOT}" && ./bin/init --help 2>&1)"
  echo "${out}" | grep -Fq 'Usage: ./bin/init' \
    || fail "${gate}: --help output missing usage"
  echo "${out}" | grep -Fq 'Story 5.3: post-wizard skills install + MCP verification.' \
    || fail "${gate}: --help output missing Story 5.3 help text"
  if echo "${out}" | grep -Fq '=== Story 5.3:'; then
    fail "${gate}: --help triggered post-wizard setup headings"
  fi
}

check_task4() {
  local gate="task4"
  local guard_dir="${TMP_ROOT}/task4-guard"
  local fixture_52="${TMP_ROOT}/task4-story52.json"
  local fixture_53="${TMP_ROOT}/task4-story53.json"
  local output_path="${TMP_ROOT}/task4.out"

  mkdir -p "${TMP_ROOT}"
  create_guarded_snapshot "${guard_dir}"
  rm -f "${ENV_PATH}"
  write_story52_fixture "${fixture_52}"
  write_story53_fixture "${fixture_53}" "PASS"

  run_init_with_fixtures "${fixture_52}" "${fixture_53}" "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: success fixture run failed"; }

  grep -Fq '=== Story 5.3: Skills install ===' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: missing skills heading"; }
  grep -Fq '=== Story 5.3: Active MCP verification ===' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: missing MCP heading"; }
  grep -Fq '=== Story 5.3: Summary ===' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: missing summary heading"; }
  grep -Fq -- '- Skills install status: PASS' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: summary missing skills PASS"; }
  grep -Eq -- '- MCP checks: PASS [0-9]+, FAIL 0' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: summary missing MCP pass/fail counts"; }

  local line_skills line_mcps line_summary
  line_skills="$(grep -n '=== Story 5.3: Skills install ===' "${output_path}" | awk -F: 'NR==1{print $1}')"
  line_mcps="$(grep -n '=== Story 5.3: Active MCP verification ===' "${output_path}" | awk -F: 'NR==1{print $1}')"
  line_summary="$(grep -n '=== Story 5.3: Summary ===' "${output_path}" | awk -F: 'NR==1{print $1}')"
  [[ -n "${line_skills}" && -n "${line_mcps}" && -n "${line_summary}" ]] \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: unable to compute heading order"; }
  [[ "${line_skills}" -lt "${line_mcps}" && "${line_mcps}" -lt "${line_summary}" ]] \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: heading order not deterministic"; }

  restore_guarded_files "${guard_dir}"
}

check_task5() {
  local gate="task5"
  local guard_dir="${TMP_ROOT}/task5-guard"
  local fixture_52="${TMP_ROOT}/task5-story52.json"
  local fixture_53="${TMP_ROOT}/task5-story53.json"
  local output_path="${TMP_ROOT}/task5.out"

  mkdir -p "${TMP_ROOT}"
  create_guarded_snapshot "${guard_dir}"
  rm -f "${ENV_PATH}"
  write_story52_fixture "${fixture_52}"
  write_story53_fixture "${fixture_53}" "FAIL" "github"

  if run_init_with_fixtures "${fixture_52}" "${fixture_53}" "${output_path}"; then
    restore_guarded_files "${guard_dir}"
    fail "${gate}: failure fixture run unexpectedly returned exit 0"
  fi

  grep -Fq '[FAIL] skills install - fixture skills fail' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: missing skills FAIL line"; }
  grep -Fq 'Re-run command: npx skills add vixxo-copilot/agent-skills' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: missing skills remediation command"; }
  grep -Eq -- '- MCP checks: PASS [0-9]+, FAIL [1-9][0-9]*' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: summary did not report MCP failure count"; }
  grep -Fq 'github:' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: failing MCP key not listed"; }

  restore_guarded_files "${guard_dir}"
}

check_task6() {
  local gate="task6"
  local guard_dir="${TMP_ROOT}/task6-guard"
  local fixture_52="${TMP_ROOT}/task6-story52.json"
  local fixture_53="${TMP_ROOT}/task6-story53-invalid.json"
  local output_path="${TMP_ROOT}/task6.out"

  mkdir -p "${TMP_ROOT}"
  create_guarded_snapshot "${guard_dir}"
  rm -f "${ENV_PATH}"
  write_story52_fixture "${fixture_52}"
  printf '%s\n' '{"skillsInstall":{"status":"PASS"}}' >"${fixture_53}"

  if run_init_with_fixtures "${fixture_52}" "${fixture_53}" "${output_path}"; then
    restore_guarded_files "${guard_dir}"
    fail "${gate}: invalid fixture payload unexpectedly returned exit 0"
  fi
  grep -Fq 'invalid Story 5.3 fixture payload' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: invalid fixture error text missing"; }

  restore_guarded_files "${guard_dir}"
}

check_task7() {
  local gate="task7"
  if ! out="$(cd "${PROJECT_ROOT}" && bash "${STORY_5_2_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: Story 5.2 harness failed"
  fi
  echo "${out}" | grep -Fq 'PASS: all' \
    || fail "${gate}: Story 5.2 harness did not report PASS: all"
}

check_task8() {
  local gate="task8"
  if ! out="$(cd "${PROJECT_ROOT}" && bash "${STORY_5_1_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: Story 5.1 harness failed"
  fi
  echo "${out}" | grep -Fq 'PASS: all' \
    || fail "${gate}: Story 5.1 harness did not report PASS: all"
}

check_task9() {
  local gate="task9"
  if [[ "${BMAD_REGRESSION_DEPTH:-0}" != "0" ]]; then
    echo "task9 SKIP: BMAD_REGRESSION_DEPTH=${BMAD_REGRESSION_DEPTH} (nested)" >&2
    return 0
  fi

  local harnesses=(
    "${STORY_1_1_HARNESS}"
    "${STORY_1_2_HARNESS}"
    "${STORY_1_3_HARNESS}"
    "${STORY_2_1_HARNESS}"
    "${STORY_2_2_HARNESS}"
    "${STORY_2_3_HARNESS}"
    "${STORY_2_4_HARNESS}"
    "${STORY_3_1_HARNESS}"
    "${STORY_3_2_HARNESS}"
    "${STORY_3_3_HARNESS}"
    "${STORY_4_1_HARNESS}"
    "${STORY_4_2_HARNESS}"
    "${STORY_4_3_HARNESS}"
    "${STORY_4_4_HARNESS}"
  )

  local i path out pass_count expected
  for (( i=0; i<${#harnesses[@]}; i++ )); do
    path="${harnesses[$i]}"
    expected="${EXPECTED_PASS_COUNTS[$i]}"
    require_file_exists "${path}" "${gate}"
    if ! out="$(cd "${PROJECT_ROOT}" && BMAD_REGRESSION_DEPTH=1 bash "${path}" all 2>&1)"; then
      echo "${out}" >&2
      fail "${gate}: predecessor harness failed: $(basename "${path}")"
    fi
    pass_count="$(printf '%s\n' "${out}" | grep -c '^PASS:' || true)"
    pass_count="$(printf '%s' "${pass_count}" | tr -d '[:space:]')"
    [[ "${pass_count}" == "${expected}" ]] \
      || fail "${gate}: $(basename "${path}") PASS count ${pass_count} != expected ${expected}"
  done
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    task1) check_task1 ;;
    task2) check_task2 ;;
    task3) check_task3 ;;
    task4) check_task4 ;;
    task5) check_task5 ;;
    task6) check_task6 ;;
    task7) check_task7 ;;
    task8) check_task8 ;;
    task9) check_task9 ;;
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
      check_task6
      echo "PASS: task6"
      check_task7
      echo "PASS: task7"
      check_task8
      echo "PASS: task8"
      check_task9
      echo "PASS: task9"
      ;;
    *)
      fail "Unknown mode: ${mode}"
      ;;
  esac

  echo "PASS: ${mode}"
}

main "$@"
