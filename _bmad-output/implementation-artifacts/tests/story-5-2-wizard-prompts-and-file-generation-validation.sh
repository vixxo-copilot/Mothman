#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

BIN_INIT="${PROJECT_ROOT}/bin/init"
IDENTITY_MD="${PROJECT_ROOT}/memory/me/identity.md"
WORK_PERSONA_MD="${PROJECT_ROOT}/agents/personas/work.md"
ENV_PATH="${PROJECT_ROOT}/.env"
ENV_EXAMPLE_PATH="${PROJECT_ROOT}/.env.example"
TMP_ROOT="${PROJECT_ROOT}/tmp/story-5-2-harness"
FIXTURE_ENV_VAR="BMAD_STORY_5_2_FIXTURE_PATH"
STORY_5_3_FIXTURE_ENV_VAR="BMAD_STORY_5_3_FIXTURE_PATH"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-5-2-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-5-2-canonical-blueprint.md"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"
STORY_2_4_HARNESS="${TESTS_DIR}/story-2-4-benji-inbox-absence-validation.sh"
STORY_3_1_HARNESS="${TESTS_DIR}/story-3-1-memory-template-tree-validation.sh"
STORY_3_2_HARNESS="${TESTS_DIR}/story-3-2-obsidian-config-validation.sh"
STORY_4_1_HARNESS="${TESTS_DIR}/story-4-1-mcp-json-validation.sh"
STORY_4_2_HARNESS="${TESTS_DIR}/story-4-2-mcp-placeholders-validation.sh"
STORY_4_3_HARNESS="${TESTS_DIR}/story-4-3-env-example-validation.sh"
STORY_4_4_HARNESS="${TESTS_DIR}/story-4-4-setup-and-mcps-docs-validation.sh"

EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 10 10 10 10 )

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

sha256_of() {
  local path="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${path}" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${path}" | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "${path}" | awk '{print $NF}'
  else
    return 1
  fi
}

assert_lf_only() {
  local path="$1"
  local gate="$2"
  local cr_count
  cr_count="$(grep -c $'\r' "${path}" 2>/dev/null || true)"
  cr_count="$(printf '%s' "${cr_count}" | tr -d '[:space:]')"
  [[ "${cr_count}" == '0' ]] || fail "${gate}: ${path} contains CR bytes"
}

write_fixture() {
  local fixture_path="$1"
  local payload="$2"
  mkdir -p "$(dirname "${fixture_path}")"
  printf '%s\n' "${payload}" >"${fixture_path}"
}

write_story53_pass_fixture() {
  local fixture_path="$1"
  mkdir -p "$(dirname "${fixture_path}")"
  node - "${PROJECT_ROOT}" "${fixture_path}" <<'NODE'
const fs = require('node:fs');
const path = require('node:path');
const repoRoot = process.argv[2];
const fixturePath = process.argv[3];
const mcpConfig = JSON.parse(fs.readFileSync(path.join(repoRoot, '.cursor', 'mcp.json'), 'utf8'));
const payload = {
  skillsInstall: { status: 'PASS', reason: 'Story 5.2 harness compatibility fixture' },
  mcpResults: {}
};
for (const key of Object.keys(mcpConfig.mcpServers || {})) {
  payload.mcpResults[key] = { status: 'PASS', reason: 'Story 5.2 harness compatibility fixture pass for ' + key };
}
fs.writeFileSync(fixturePath, JSON.stringify(payload), 'utf8');
NODE
}

restore_guarded_files() {
  local guard_dir="$1"
  local env_state_file="${guard_dir}/env-state.txt"

  cp "${guard_dir}/identity.md" "${IDENTITY_MD}"
  cp "${guard_dir}/work.md" "${WORK_PERSONA_MD}"

  if [[ -f "${env_state_file}" ]] && grep -Fxq 'present' "${env_state_file}"; then
    cp "${guard_dir}/env" "${ENV_PATH}"
  else
    rm -f "${ENV_PATH}"
  fi
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

run_init_with_fixture() {
  local fixture_path="$1"
  local output_path="$2"
  local story53_fixture_path="${TMP_ROOT}/story-5-2-story-5-3-compat.json"
  local exit_code=0

  write_story53_pass_fixture "${story53_fixture_path}"
  set +e
  (
    cd "${PROJECT_ROOT}" && \
      env \
        "${FIXTURE_ENV_VAR}=${fixture_path}" \
        "${STORY_5_3_FIXTURE_ENV_VAR}=${story53_fixture_path}" \
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
  grep -Fq '# Story 5.2 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline title mismatch"
  grep -Fq 'Pre-change SHA-256 fingerprints' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline missing fingerprint section"
  grep -Fq 'Deterministic mapping policy lock' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline missing mapping policy section"
}

check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"
  grep -Fq '# Story 5.2 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint title mismatch"
  grep -Fq 'Prompt schema lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing prompt schema lock"
  grep -Fq 'Deterministic non-interactive mode lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing fixture-mode lock"
}

check_task3() {
  local gate="task3"
  require_file_exists "${BIN_INIT}" "${gate}"
  require_file_nonempty "${BIN_INIT}" "${gate}"
  assert_lf_only "${BIN_INIT}" "${gate}"

  grep -Fq "const FIXTURE_ENV_VAR = 'BMAD_STORY_5_2_FIXTURE_PATH';" "${BIN_INIT}" \
    || fail "${gate}: fixture env var missing"
  grep -Fq 'function promptSchema' "${BIN_INIT}" \
    || fail "${gate}: prompt schema function missing"
  grep -Fq 'function collectWizardAnswers' "${BIN_INIT}" \
    || fail "${gate}: prompt orchestration missing"
  grep -Fq 'type: '\''multiselect'\''' "${BIN_INIT}" \
    || fail "${gate}: multiselect prompt missing"
  grep -Fq 'onCancel' "${BIN_INIT}" \
    || fail "${gate}: onCancel handling missing"

  local out
  out="$(cd "${PROJECT_ROOT}" && ./bin/init --help 2>&1)"
  echo "${out}" | grep -Fq 'Usage: ./bin/init' \
    || fail "${gate}: --help output missing usage"
  out="$(cd "${PROJECT_ROOT}" && ./bin/init --version 2>&1)"
  echo "${out}" | grep -Fq 'assistants-template init' \
    || fail "${gate}: --version output missing version banner"
}

check_task4() {
  local gate="task4"
  local guard_dir="${TMP_ROOT}/task4-guard"
  local fixture_path="${TMP_ROOT}/task4-cancel.json"
  local output_path="${TMP_ROOT}/task4-cancel.out"

  mkdir -p "${TMP_ROOT}"
  create_guarded_snapshot "${guard_dir}"

  local identity_sha_before work_sha_before env_sha_before="missing"
  identity_sha_before="$(sha256_of "${IDENTITY_MD}")" || fail "${gate}: cannot hash identity"
  work_sha_before="$(sha256_of "${WORK_PERSONA_MD}")" || fail "${gate}: cannot hash work persona"
  if [[ -f "${ENV_PATH}" ]]; then
    env_sha_before="$(sha256_of "${ENV_PATH}")" || fail "${gate}: cannot hash .env"
  fi

  write_fixture "${fixture_path}" '{"responses":["Casey User","casey@vixxo.com",{"type":"error","message":"stop"}]}'
  if run_init_with_fixture "${fixture_path}" "${output_path}"; then
    restore_guarded_files "${guard_dir}"
    fail "${gate}: cancellation fixture returned exit 0"
  fi

  grep -Fq 'setup cancelled' "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: missing cancellation guidance output"; }

  local identity_sha_after work_sha_after env_sha_after="missing"
  identity_sha_after="$(sha256_of "${IDENTITY_MD}")" || { restore_guarded_files "${guard_dir}"; fail "${gate}: cannot hash identity after cancel"; }
  work_sha_after="$(sha256_of "${WORK_PERSONA_MD}")" || { restore_guarded_files "${guard_dir}"; fail "${gate}: cannot hash work persona after cancel"; }
  if [[ -f "${ENV_PATH}" ]]; then
    env_sha_after="$(sha256_of "${ENV_PATH}")" || { restore_guarded_files "${guard_dir}"; fail "${gate}: cannot hash .env after cancel"; }
  fi

  [[ "${identity_sha_before}" == "${identity_sha_after}" ]] \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: identity changed on cancel"; }
  [[ "${work_sha_before}" == "${work_sha_after}" ]] \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: work persona changed on cancel"; }
  [[ "${env_sha_before}" == "${env_sha_after}" ]] \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: .env changed on cancel"; }

  restore_guarded_files "${guard_dir}"
}

check_task5() {
  local gate="task5"
  local out
  out="$(cd "${PROJECT_ROOT}" && node - <<'NODE'
const assert = require('node:assert/strict');
const init = require('./bin/init');

const answers = {
  employeeName: '  Riley   Gray ',
  employeeEmail: '  RILEY.GRAY@VIXXO.COM ',
  employeeRole: 'Senior QA Engineer',
  optionalMcps: ['github', 'linear', 'linear']
};
const canonical = ['linear', 'github', 'gong'];
const normalized = init.normalizeWizardAnswers(answers, canonical);
assert.equal(normalized.department, 'Engineering');
assert.equal(normalized.manager, 'Engineering Manager (TBD)');
assert.deepEqual(normalized.optionalMcps, ['linear', 'github']);

const identityA = init.renderIdentityMarkdown(normalized);
const identityB = init.renderIdentityMarkdown(normalized);
assert.equal(identityA, identityB);
assert.ok(identityA.endsWith('\n'));
assert.match(identityA, /## Optional MCPs/);

const personaA = init.renderWorkPersonaMarkdown(normalized);
const personaB = init.renderWorkPersonaMarkdown(normalized);
assert.equal(personaA, personaB);
assert.ok(personaA.endsWith('\n'));

assert.throws(() => init.assertPathInsideRepo('../escape.md'));
console.log('NODE_OK');
NODE
)"
  echo "${out}" | grep -Fq 'NODE_OK' \
    || fail "${gate}: deterministic renderer/path guard assertions failed"
}

check_task6() {
  local gate="task6"
  local guard_dir="${TMP_ROOT}/task6-guard"
  local fixture_create="${TMP_ROOT}/task6-create.json"
  local fixture_keep="${TMP_ROOT}/task6-keep.json"
  local fixture_overwrite="${TMP_ROOT}/task6-overwrite.json"
  local output_path="${TMP_ROOT}/task6.out"

  mkdir -p "${TMP_ROOT}"
  create_guarded_snapshot "${guard_dir}"

  rm -f "${ENV_PATH}"
  write_fixture "${fixture_create}" '{"responses":["Morgan Lee","morgan@vixxo.com","Operations Lead",["linear"]]}'
  run_init_with_fixture "${fixture_create}" "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: missing-.env fixture run failed"; }
  [[ -f "${ENV_PATH}" ]] || { restore_guarded_files "${guard_dir}"; fail "${gate}: .env was not created"; }
  local env_sha env_example_sha
  env_sha="$(sha256_of "${ENV_PATH}")" || { restore_guarded_files "${guard_dir}"; fail "${gate}: cannot hash .env"; }
  env_example_sha="$(sha256_of "${ENV_EXAMPLE_PATH}")" || { restore_guarded_files "${guard_dir}"; fail "${gate}: cannot hash .env.example"; }
  [[ "${env_sha}" == "${env_example_sha}" ]] \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: created .env differs from .env.example"; }

  printf '%s\n' '# keep-me' >"${ENV_PATH}"
  write_fixture "${fixture_keep}" '{"responses":["Morgan Lee","morgan@vixxo.com","Operations Lead",["linear"],false]}'
  run_init_with_fixture "${fixture_keep}" "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: existing-.env keep fixture run failed"; }
  grep -Fq '# keep-me' "${ENV_PATH}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: .env was overwritten despite false confirm"; }

  write_fixture "${fixture_overwrite}" '{"responses":["Morgan Lee","morgan@vixxo.com","Operations Lead",["linear"],true]}'
  run_init_with_fixture "${fixture_overwrite}" "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: existing-.env overwrite fixture run failed"; }
  env_sha="$(sha256_of "${ENV_PATH}")" || { restore_guarded_files "${guard_dir}"; fail "${gate}: cannot hash overwritten .env"; }
  [[ "${env_sha}" == "${env_example_sha}" ]] \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: .env overwrite did not match .env.example"; }

  restore_guarded_files "${guard_dir}"
}

check_task7() {
  local gate="task7"
  grep -Fq "const FIXTURE_ENV_VAR = 'BMAD_STORY_5_2_FIXTURE_PATH';" "${BIN_INIT}" \
    || fail "${gate}: Story 5.2 fixture env var missing"
  grep -Fq 'function runWizard' "${BIN_INIT}" \
    || fail "${gate}: Story 5.2 runWizard function missing"
  grep -Fq 'setup cancelled. No files were changed; re-run ./bin/init to continue.' "${BIN_INIT}" \
    || fail "${gate}: Story 5.2 cancellation guidance changed unexpectedly"
  grep -Fq 'function runPostWizardSetup' "${BIN_INIT}" \
    || fail "${gate}: Story 5.3 post-wizard orchestration not wired"
  grep -Fq "const SKILLS_INSTALL_ARGS = ['skills', 'add', 'vixxo-copilot/agent-skills'];" "${BIN_INIT}" \
    || fail "${gate}: Story 5.3 skills-install command wiring missing from integrated flow"
}

check_task8() {
  local gate="task8"
  local guard_dir="${TMP_ROOT}/task8-guard"
  local fixture_path="${TMP_ROOT}/task8-success.json"
  local output_path="${TMP_ROOT}/task8-success.out"

  mkdir -p "${TMP_ROOT}"
  create_guarded_snapshot "${guard_dir}"

  write_fixture "${fixture_path}" '{"responses":["Jordan Miles","jordan@vixxo.com","Product Manager",["linear","github"],true]}'
  run_init_with_fixture "${fixture_path}" "${output_path}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: success fixture run failed"; }

  grep -Fq 'scope: work' "${IDENTITY_MD}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: identity scope missing"; }
  grep -Fq 'Jordan Miles' "${IDENTITY_MD}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: identity missing rendered name"; }
  grep -Fq 'jordan@vixxo.com' "${IDENTITY_MD}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: identity missing rendered email"; }
  grep -Fq '## Optional MCPs' "${IDENTITY_MD}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: identity missing optional MCP section"; }
  grep -Fq '{{employee_' "${IDENTITY_MD}" \
    && { restore_guarded_files "${guard_dir}"; fail "${gate}: identity still contains employee placeholders"; }

  grep -Fq 'scope: work' "${WORK_PERSONA_MD}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: work persona scope missing"; }
  grep -Fq 'Jordan Miles is Product Manager in Product' "${WORK_PERSONA_MD}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: work persona role sentence mismatch"; }
  grep -Fq '| **Linear** | Vixxo work task and project management |' "${WORK_PERSONA_MD}" \
    || { restore_guarded_files "${guard_dir}"; fail "${gate}: active MCP table discipline missing"; }
  grep -Fq '{{employee_' "${WORK_PERSONA_MD}" \
    && { restore_guarded_files "${guard_dir}"; fail "${gate}: work persona still contains employee placeholders"; }

  restore_guarded_files "${guard_dir}"
}

check_task9() {
  local gate="task9"
  local harnesses=(
    "${STORY_1_1_HARNESS}"
    "${STORY_1_2_HARNESS}"
    "${STORY_1_3_HARNESS}"
    "${STORY_2_1_HARNESS}"
    "${STORY_2_2_HARNESS}"
    "${STORY_2_4_HARNESS}"
    "${STORY_3_1_HARNESS}"
    "${STORY_3_2_HARNESS}"
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
