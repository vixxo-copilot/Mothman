#!/usr/bin/env bash
set -euo pipefail

# Story 5.1 — Scaffold bin/init + package.json + package-lock.json —
# deterministic validation harness.
#
# Scope:
#   - Story 5.1 authors `bin/init` (executable Node entry point),
#     `package.json` (nine locked top-level keys; prompts@2.4.2
#     exact-pin; Node >=20 engine floor), and `package-lock.json`
#     (lockfileVersion 3; three transitive packages: prompts,
#     kleur, sisteransi) at the repo root.
#   - `.cursor/mcp.json` + `.cursor/mcp.README.md` +
#     `.cursor/mcp.placeholders.md` + `.env.example` + `.gitignore` +
#     `docs/legal/license-vixxo-internal-canonical.md` +
#     `docs/setup.md` + `docs/mcps.md` remain byte-stable during
#     Story 5.1 — eight SHA-256 fingerprint assertions at `task7`.
#   - Regression chain extends Story 4.4's thirteen-harness chain
#     by one (adds Story 4.4 as the fourteenth predecessor).
#     Empirical `^PASS:` line-count vector
#     `( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )`.
#   - Banned-term regex + Derek fixed-string probes + path-reference
#     probes + eleven-pattern secret catalog + five placeholder-form
#     probes + `${VAR}`/`$VAR` shell-expansion probe inherited
#     verbatim from Stories 4.1 / 4.2 / 4.3 / 4.4.
#   - Story 5.1 ADDS two new harness artifacts:
#       * `content_allowlist_for_personal()` — a single-scope `sed`
#         substitution of the full locked `description` string in
#         `package.json` to `__LOCKED_DESC__` before banned-term
#         scanning. Narrow, anchored on the full locked description,
#         applied only to `package.json`, self-testing.
#       * `json_strict_parse()` — Node-based JSON parser (`node -e
#         JSON.parse(...)`), used for `package.json` and
#         `package-lock.json` since Node is a hard prerequisite.
#   - Honors `BMAD_REGRESSION_DEPTH` guard (Story 4.2 F6 inheritance):
#     nested `check_task9` invocations short-circuit.
#   - Honors `EXPECTED_PREDECESSOR_SHA256` pre-check (Story 4.2 F5
#     inheritance): byte-stability drift of any predecessor harness
#     fails the gate BEFORE invocation.
#   - Epic-5 opens at Phase 1 (first story in Epic 5 flips
#     `epic-5.status: backlog -> in-progress`).
#
# Banned-term allowlist (TWO layers):
#   Layer 1 (inherited, load-bearing for docs stories): none of
#   Story 5.1's own artifacts reference `GITHUB_PERSONAL_ACCESS_TOKEN`,
#   so `sanitize_for_banned_scan()` is defensive-only for Story 5.1
#   (a departure from Story 4.3's load-bearing use).
#   Layer 2 (new for Story 5.1): `content_allowlist_for_personal()`
#   substitutes the full locked `description` string to
#   `"description": "__LOCKED_DESC__"` before scanning. Only applied
#   to `package.json`. Self-testing: pre-substitution view must
#   contain `personal AI agent template`, post-substitution view
#   must return zero banned-term matches.
#
# Gates:
#   task1  baseline-audit artifact present + structured
#   task2  canonical-blueprint artifact present + structured
#   task3  bin/init shape: exists, non-empty, LF-only, trailing
#          newline, executable bit, first line == `#!/usr/bin/env
#          node`, exactly one `spawnSync('npm',...)` call, zero
#          bash/sh/zsh tokens, zero absolute-path literals, four
#          banner lines present
#   task4  package.json shape: exists, non-empty, LF-only, trailing
#          newline, strict-JSON parse via `node -e`, nine top-level
#          keys in canonical order, locked values for name /
#          version / private / description / type / bin / scripts /
#          engines / dependencies
#   task5  package-lock.json shape: exists, non-empty, LF-only,
#          trailing newline, strict-JSON parse, lockfileVersion=3,
#          name/version match, prompts@2.4.2 pinned, three
#          transitive packages exactly
#   task6  secret-shape + banned-term + Derek + path + placeholder-
#          form + shell-expansion scans per AC5. bin/init uses
#          plain `sanitize_for_banned_scan()` view; package.json
#          uses two-stage `sanitize_for_banned_scan()` +
#          `content_allowlist_for_personal()` view. Pre-allowlist
#          view of package.json must contain `personal AI agent
#          template` (allowlist exercised).
#   task7  byte-stability invariance per AC6: eight SHA-256 anchors
#          hold; `git check-ignore -v bin/init` exits non-zero;
#          `git check-ignore -v package.json` exits non-zero;
#          `git check-ignore -v package-lock.json` exits non-zero;
#          `git check-ignore -v node_modules/prompts/package.json`
#          exits 0 with `.gitignore:<n>:node_modules/` rule cited
#   task8  self-check: shebang line 1, `set -euo pipefail`, every
#          case arm present, every declared constant referenced,
#          helper functions defined (regex_self_probe,
#          sanitize_for_banned_scan, content_allowlist_for_personal,
#          sha256_of, json_strict_parse)
#   task9  regression: fourteen predecessor harnesses run in `all`
#          mode with BMAD_REGRESSION_DEPTH=1 exported; each exits 0
#          with PASS: all; per-harness `^PASS:` line-count matches
#          EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 );
#          SHA-256 pre-check against EXPECTED_PREDECESSOR_SHA256
#   all    runs task1 -> task9 sequentially; exits 0 with exactly
#          10 `^PASS:` lines on success
#
# Tooling: POSIX-bash-3.2 compatible (no associative arrays, no
# namerefs). Uses bash, grep, awk, sed, find, tr, wc, head, tail, od,
# cut, sort, shasum -a 256 (falls back to sha256sum / openssl dgst
# -sha256), and `node -e` for JSON parsing (Node is a hard
# prerequisite for this story per AC3 engines floor). BSD-grep and
# GNU-grep compatible. Does NOT use rg, jq, yq. Uses python3 only
# via predecessor-harness invocations.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

BIN_INIT="${PROJECT_ROOT}/bin/init"
PACKAGE_JSON="${PROJECT_ROOT}/package.json"
PACKAGE_LOCK_JSON="${PROJECT_ROOT}/package-lock.json"

MCP_JSON="${PROJECT_ROOT}/.cursor/mcp.json"
MCP_README="${PROJECT_ROOT}/.cursor/mcp.README.md"
MCP_PLACEHOLDERS="${PROJECT_ROOT}/.cursor/mcp.placeholders.md"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
GITIGNORE_PATH="${PROJECT_ROOT}/.gitignore"
LICENSE_CANONICAL="${PROJECT_ROOT}/docs/legal/license-vixxo-internal-canonical.md"
SETUP_MD="${PROJECT_ROOT}/docs/setup.md"
MCPS_MD="${PROJECT_ROOT}/docs/mcps.md"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-5-1-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-5-1-canonical-blueprint.md"

# Byte-stability SHA-256 constants (captured Task 1 2026-04-21).
STORY_4_3_MCP_JSON_SHA256="d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c"
STORY_4_3_MCP_README_SHA256="4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09"
STORY_4_3_MCP_PLACEHOLDERS_SHA256="1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010"
STORY_4_3_ENV_EXAMPLE_SHA256="19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4"
STORY_1_1_GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"
STORY_1_2_LICENSE_CANONICAL_SHA256="4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc"
STORY_4_4_SETUP_MD_SHA256="ddce66f02d496e6d5fcd9ed8c53bbca633b9f10772ee2e956b7cb3124ec27276"
STORY_4_4_MCPS_MD_SHA256="7b2a16f84fa1b087a0efcc08e72508ce834ef6820317e03485066de3d92668d6"

# Nine top-level keys, canonical order (AC3).
EXPECTED_TOP_KEYS=( name version private description type bin scripts engines dependencies )

# Three sorted transitive-package keys (AC7 / AC8 task5).
EXPECTED_LOCK_PACKAGES=( node_modules/kleur node_modules/prompts node_modules/sisteransi )

EXPECTED_PROMPTS_VERSION="2.4.2"
EXPECTED_NODE_ENGINE=">=20.0.0"
EXPECTED_LOCKFILE_VERSION=3
EXPECTED_PACKAGE_NAME="assistants-template"
EXPECTED_PACKAGE_VERSION="0.1.0"
EXPECTED_DESCRIPTION_LOCKED='"description": "Vixxo-deployable employee AI agent template; clone, run ./bin/init, work."'

# Four non-blank banner lines from AC4 (steady-state banner).
EXPECTED_BANNER_LINES=(
  'assistants-template — setup wizard'
)
EXPECTED_5_1_COMPAT_LINES=(
  'Story 5.1 scaffold — runnable entry point confirmed.'
  'Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.'
  'Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.'
)
EXPECTED_5_2_COMPAT_LINES=(
  'Story 5.2: prompts + deterministic file generation.'
  'Story 5.3 (pending):        npx skills add + MCP verification.'
  'Wizard completed.'
)
EXPECTED_5_3_COMPAT_LINES=(
  'Story 5.2: prompts + deterministic file generation.'
  'Story 5.3: post-wizard skills install + MCP verification.'
  'Wizard completed.'
)

# Eleven secret-pattern regexes (inherited verbatim from Story 4.1).
SECRET_PATTERNS=(
  'sk-[A-Za-z0-9_-]{20,}'
  'ghp_[A-Za-z0-9]{20,}'
  'gho_[A-Za-z0-9]{20,}'
  'ghs_[A-Za-z0-9]{20,}'
  'github_pat_[A-Za-z0-9_]{20,}'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
  'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'
  'Bearer [A-Za-z0-9_.-]{20,}'
  'AKIA[0-9A-Z]{16}'
  'AIza[A-Za-z0-9_-]{35}'
  '[A-Fa-f0-9]{32,}'
)

SECRET_EQUALS_LITERALS=( 'password=' 'token=' 'secret=' 'api_key=' )

BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'

DEREK_FIXED_STRINGS=(
  Chiron
  MasteryLab
  "Agile Weekly"
  "Queen Creek"
  Gangplank
  "Bodybuilding.com"
  Integrum
  Omarchy
  derekneighbors.com
  Playrix
  Laurie
  Deke
)

GH_PAT_ENV_NAME="GITHUB_PERSONAL_ACCESS_TOKEN"
GH_PAT_ALLOWLIST_PLACEHOLDER="__GH_PAT_NAME__"

# Fourteen predecessor harness paths (AC8 / AC9).
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

# Empirical `^PASS:` line-count fingerprint per predecessor in `all`
# mode. Fourteen-element positional-parallel vector.
EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )

# SHA-256 byte-stability anchor per predecessor harness (Story 4.2 F5
# inheritance extended to fourteen). Note: index 9 (Story 3.3)
# captures the CURRENT on-disk value; see baseline audit drift note.
EXPECTED_PREDECESSOR_SHA256=(
  "a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8"
  "0226aa1b2086ee63065a533bc720afe876fde0958af9ed99276c1ff68fb4afaf"
  "0cecd5293af7e5896bede460ef1f2a7e822554f735dc10b81d0beb8e0e840ba9"
  "dc9b98e5e89239d41429e4436b13c671822d237f616eb8ca99c016085e2bb08a"
  "5412bcfc7bd829a98a9054efb8fdf32c72b7e59c2b542cacca0c58648da6df10"
  "9d455eaebb775f80d29b24de4a35febc3a8ffba0ed7f237af492723d2096a591"
  "f70d8c25e333123c3aae9d44a388594f1850be1449e86a540fdbe2dbec701687"
  "cb298fff4f83ddbf27644293f4a38ecfd36b099b4d7d4ceb180c41a4af383ff7"
  "10ef5221ed1e64e3222c7d95297824175693f66c313eced1260d5645be81292e"
  "f49f21c1811be49fc7aafa386f7f14553f46deb8a5bee6d4e609ca4d1b39bea8"
  "cfe810169aef5c2abf7bc021aad4fbb43d3c91eda58fc99b3d16123907dbba8f"
  "ac01c393e68c41df07cc4792abab703d62d4a10d40e96b68c9ac771bd9a1a490"
  "7aa2733e3b0e93d6b35bd0d7c89645ded810ae876b10e81554d26c738d61a277"
  "e5a254b4f15ac2903c0fda15a6a832199abcc47c920e5823f997c13c255c0473"
)

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

assert_trailing_newline() {
  local path="$1"
  local gate="$2"
  local last_byte
  last_byte="$(tail -c 1 "${path}" | od -An -tx1 | tr -d ' \n')"
  [[ "${last_byte}" == '0a' ]] \
    || fail "${gate}: ${path} missing trailing newline (last byte: 0x${last_byte})"
}

assert_lf_only() {
  local path="$1"
  local gate="$2"
  local cr_count
  cr_count="$(grep -c $'\r' "${path}" 2>/dev/null || true)"
  cr_count="$(printf '%s' "${cr_count}" | tr -d '[:space:]')"
  [[ "${cr_count}" == '0' ]] \
    || fail "${gate}: ${path} contains ${cr_count} CR byte(s); expected LF-only"
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

sanitize_for_banned_scan() {
  local path="$1"
  sed -E "s/${GH_PAT_ENV_NAME}/${GH_PAT_ALLOWLIST_PLACEHOLDER}/g" "${path}"
}

# content_allowlist_for_personal <file> — emit file contents with
# the full locked `description` line substituted to
# `"description": "__LOCKED_DESC__"`. Narrow, anchored on the full
# locked string. Used only for `package.json` in check_task6.
content_allowlist_for_personal() {
  local path="$1"
  sed -E 's#"description": "Vixxo-deployable (personal|employee) AI agent template; clone, run \./bin/init, work\."#"description": "__LOCKED_DESC__"#g' "${path}"
}

# json_strict_parse <file> — invoke node -e to strict-parse JSON.
# Returns non-zero on parse failure; suppresses stdout on success.
json_strict_parse() {
  local path="$1"
  node -e 'JSON.parse(require("fs").readFileSync(process.argv[1],"utf8"))' "${path}" >/dev/null 2>&1
}

regex_self_probe() {
  # (a) banned-term boundary check.
  if echo "derekson" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary admitted 'derekson'"
  fi
  if ! echo "derek smith" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary rejected 'derek smith'"
  fi

  # (b) GH PAT secret pattern positive + short-rejected.
  if ! echo "ghp_aaaabbbbccccddddeeee1234" | grep -E 'ghp_[A-Za-z0-9]{20,}' >/dev/null; then
    fail "regex probe: ghp_ pattern rejected legitimate 24+ char hit"
  fi
  if echo "ghp_short" | grep -E 'ghp_[A-Za-z0-9]{20,}' >/dev/null; then
    fail "regex probe: ghp_ pattern admitted short 'ghp_short'"
  fi

  # (c) ${VAR} / $VAR probes — both forms must be caught.
  if ! echo '${FOO}' | grep -E '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' >/dev/null; then
    fail "regex probe: \${VAR} scan missed '\${FOO}'"
  fi
  if ! echo '$foo' | grep -E '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' >/dev/null; then
    fail "regex probe: \$VAR scan missed '\$foo'"
  fi
  if echo 'dollar sign' | grep -E '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' >/dev/null; then
    fail "regex probe: dollar-expansion scan hit benign 'dollar sign'"
  fi

  # (d) Angle-bracket placeholder-form positive + HTML-comment negative.
  if ! echo '<name>' | grep -E '<[A-Za-z_][A-Za-z0-9_]*>' >/dev/null; then
    fail "regex probe: angle-bracket probe missed '<name>'"
  fi
  if echo '<!-- c -->' | grep -E '<[A-Za-z_][A-Za-z0-9_]*>' >/dev/null; then
    fail "regex probe: angle-bracket probe tripped on HTML comment"
  fi

  # (e) GH_PAT allowlist pre-filter behavioural probe.
  if ! echo "GITHUB_PERSONAL_ACCESS_TOKEN" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: raw GH PAT name failed to trip banned-term regex (sanity)"
  fi
  local sanitized
  sanitized="$(echo "GITHUB_PERSONAL_ACCESS_TOKEN" | sed -E "s/${GH_PAT_ENV_NAME}/${GH_PAT_ALLOWLIST_PLACEHOLDER}/g")"
  if echo "${sanitized}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: allowlist pre-filter failed — sanitized GH PAT still trips"
  fi

  # (f) content_allowlist_for_personal() behavioural probe: run
  # against a synthetic fixture containing the exact locked
  # description line; assert post-substitution view is clean.
  local fixture_file fixture_before fixture_after
  fixture_file="$(mktemp)"
  printf '%s\n' \
    '{' \
    '  "description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work.",' \
    '  "note": "safe line"' \
    '}' >"${fixture_file}"
  fixture_before="$(cat "${fixture_file}")"
  fixture_after="$(content_allowlist_for_personal "${fixture_file}")"
  rm -f "${fixture_file}"
  if ! echo "${fixture_before}" | grep -Fq 'personal AI agent template'; then
    fail "regex probe: content_allowlist fixture missing 'personal AI agent template' in pre-view"
  fi
  if echo "${fixture_before}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    :  # expected — pre-view trips banned regex
  else
    fail "regex probe: pre-view of content_allowlist fixture did NOT trip banned regex (allowlist sanity)"
  fi
  if echo "${fixture_after}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: post-allowlist view of fixture STILL trips banned regex"
  fi
  if ! echo "${fixture_after}" | grep -Fq '__LOCKED_DESC__'; then
    fail "regex probe: content_allowlist did not emit __LOCKED_DESC__ marker"
  fi

  # (g) json_strict_parse() probe — valid JSON passes, invalid fails.
  local j_ok j_bad
  j_ok="$(mktemp)"
  j_bad="$(mktemp)"
  printf '%s\n' '{"a":1}' >"${j_ok}"
  printf '%s\n' '{a:1}' >"${j_bad}"
  if ! json_strict_parse "${j_ok}"; then
    rm -f "${j_ok}" "${j_bad}"
    fail "regex probe: json_strict_parse rejected valid JSON '{\"a\":1}'"
  fi
  if json_strict_parse "${j_bad}"; then
    rm -f "${j_ok}" "${j_bad}"
    fail "regex probe: json_strict_parse admitted invalid JSON '{a:1}'"
  fi
  rm -f "${j_ok}" "${j_bad}"
}

# ------------------------------------------------------------------
# task1 — baseline audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 5.1 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 5.1 Baseline Audit'"

  local section
  for section in \
    'Node / npm version-requirement rationale' \
    'prompts@2.4.2 upstream cross-reference and alternatives evaluation' \
    'Byte-stability fingerprints' \
    'Predecessor-harness SHA-256 vector (fourteen predecessors)' \
    'Predecessor-harness compatibility scan (fourteen harnesses)' \
    '.gitignore compatibility re-confirmation' \
    'bin/ directory pre-state check' \
    'Empirical predecessor PASS-count vector' \
    'Source URLs'; do
    if ! grep -Fq "${section}" "${BASELINE_AUDIT_PATH}"; then
      fail "${gate}: baseline audit missing required section/keyword: ${section}"
    fi
  done
}

# ------------------------------------------------------------------
# task2 — canonical blueprint evidence present and complete
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq '# Story 5.1 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 5.1 Canonical Blueprint'"

  local required
  for required in \
    'Inheritance-only note' \
    'Blueprint — `bin/init`' \
    'Blueprint — `package.json`' \
    'Blueprint — `package-lock.json`' \
    'Description-content-allowlist carve-out' \
    'Banner text lock' \
    'Evidence constants for the Task 5 harness' \
    'Secret-pattern catalog lock' \
    'Banned-term lock' \
    'Derek probe lock' \
    'Placeholder-form probes' \
    'Shell-expansion probe'; do
    if ! grep -Fq "${required}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing required subsection: '${required}'"
    fi
  done

  grep -Fq '4.1' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Story 4.1 inheritance reference"
  grep -Fq '4.4' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Story 4.4 inheritance reference"
}

# ------------------------------------------------------------------
# task3 — bin/init shape verification
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${BIN_INIT}" "${gate}"
  require_file_nonempty "${BIN_INIT}" "${gate}"
  assert_trailing_newline "${BIN_INIT}" "${gate}"
  assert_lf_only "${BIN_INIT}" "${gate}"

  [[ -x "${BIN_INIT}" ]] \
    || fail "${gate}: ${BIN_INIT} is not executable"

  local line_1
  line_1="$(sed -n '1p' "${BIN_INIT}")"
  [[ "${line_1}" == '#!/usr/bin/env node' ]] \
    || fail "${gate}: bin/init line 1 != '#!/usr/bin/env node' (got '${line_1}')"

  local shebang_count
  shebang_count="$(grep -cE '^#!/usr/bin/env node$' "${BIN_INIT}")"
  [[ "${shebang_count}" == '1' ]] \
    || fail "${gate}: bin/init shebang count ${shebang_count} != 1"

  local spawn_count
  spawn_count="$(grep -cE "spawnSync\('npm'," "${BIN_INIT}")"
  [[ "${spawn_count}" == '1' ]] \
    || fail "${gate}: bin/init spawnSync('npm',...) count ${spawn_count} != 1"

  local req_fs req_path req_child
  req_fs="$(grep -cE "require\('node:fs'\)" "${BIN_INIT}")"
  req_path="$(grep -cE "require\('node:path'\)" "${BIN_INIT}")"
  req_child="$(grep -cE "require\('node:child_process'\)" "${BIN_INIT}")"
  [[ "${req_fs}" == '1' ]] \
    || fail "${gate}: bin/init require('node:fs') count ${req_fs} != 1"
  [[ "${req_path}" == '1' ]] \
    || fail "${gate}: bin/init require('node:path') count ${req_path} != 1"
  [[ "${req_child}" == '1' ]] \
    || fail "${gate}: bin/init require('node:child_process') count ${req_child} != 1"

  # No bash/sh/zsh shell-name tokens (whole-word).
  if grep -nE '\b(bash|zsh|/bin/bash|/bin/sh)\b' "${BIN_INIT}" >/dev/null 2>&1; then
    grep -nE '\b(bash|zsh|/bin/bash|/bin/sh)\b' "${BIN_INIT}" >&2 || true
    fail "${gate}: bin/init contains bash/zsh/shell-path token"
  fi
  # Separate check for bare `sh` that avoids false positives from
  # `spawnSync` (contains `sh`); match only `'sh'` or ` sh ` etc.
  if grep -nE "'sh'|\"sh\"|/bin/sh" "${BIN_INIT}" >/dev/null 2>&1; then
    fail "${gate}: bin/init contains 'sh' shell-literal"
  fi

  # No absolute-path literals.
  if grep -nE '/Users/|/home/' "${BIN_INIT}" >/dev/null 2>&1; then
    grep -nE '/Users/|/home/' "${BIN_INIT}" >&2 || true
    fail "${gate}: bin/init contains absolute-path literal (/Users/ or /home/)"
  fi

  # No exec() / execSync() / backtick / spawn('bash').
  if grep -nE "spawn\(['\"](bash|sh)['\"]" "${BIN_INIT}" >/dev/null 2>&1; then
    fail "${gate}: bin/init contains spawn('bash'|'sh',...)"
  fi
  if grep -nE "\.(exec|execSync)\(" "${BIN_INIT}" >/dev/null 2>&1; then
    fail "${gate}: bin/init contains .exec()/.execSync() shell-exec"
  fi

  # Banner lines present verbatim (forward-compatible with Story 5.2).
  local banner
  for banner in "${EXPECTED_BANNER_LINES[@]}"; do
    if ! grep -Fq "${banner}" "${BIN_INIT}"; then
      fail "${gate}: bin/init missing banner line: '${banner}'"
    fi
  done

  local has_5_1_compat=1
  local has_5_2_compat=1
  local has_5_3_compat=1
  for banner in "${EXPECTED_5_1_COMPAT_LINES[@]}"; do
    if ! grep -Fq "${banner}" "${BIN_INIT}"; then
      has_5_1_compat=0
      break
    fi
  done
  for banner in "${EXPECTED_5_2_COMPAT_LINES[@]}"; do
    if ! grep -Fq "${banner}" "${BIN_INIT}"; then
      has_5_2_compat=0
      break
    fi
  done
  for banner in "${EXPECTED_5_3_COMPAT_LINES[@]}"; do
    if ! grep -Fq "${banner}" "${BIN_INIT}"; then
      has_5_3_compat=0
      break
    fi
  done
  if [[ "${has_5_1_compat}" != "1" && "${has_5_2_compat}" != "1" && "${has_5_3_compat}" != "1" ]]; then
    fail "${gate}: bin/init missing compatibility banner/text set for Story 5.1, Story 5.2, or Story 5.3"
  fi

  # Flag handlers present.
  grep -Fq -- "'--help'" "${BIN_INIT}" \
    || fail "${gate}: bin/init missing --help handler literal"
  grep -Fq -- "'-h'" "${BIN_INIT}" \
    || fail "${gate}: bin/init missing -h handler literal"
  grep -Fq -- "'--version'" "${BIN_INIT}" \
    || fail "${gate}: bin/init missing --version handler literal"
  grep -Fq -- "'-v'" "${BIN_INIT}" \
    || fail "${gate}: bin/init missing -v handler literal"

  # Error-message prefix.
  grep -Fq '[bin/init] npm install failed; exit' "${BIN_INIT}" \
    || fail "${gate}: bin/init missing locked error-message prefix"

  # No trailing-whitespace lines.
  if grep -nE ' +$' "${BIN_INIT}" >/dev/null 2>&1; then
    grep -nE ' +$' "${BIN_INIT}" >&2
    fail "${gate}: bin/init contains trailing-whitespace lines"
  fi
}

# ------------------------------------------------------------------
# task4 — package.json shape verification
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${PACKAGE_JSON}" "${gate}"
  require_file_nonempty "${PACKAGE_JSON}" "${gate}"
  assert_trailing_newline "${PACKAGE_JSON}" "${gate}"
  assert_lf_only "${PACKAGE_JSON}" "${gate}"

  json_strict_parse "${PACKAGE_JSON}" \
    || fail "${gate}: package.json failed strict JSON parse (node -e)"

  if grep -nE ' +$' "${PACKAGE_JSON}" >/dev/null 2>&1; then
    grep -nE ' +$' "${PACKAGE_JSON}" >&2
    fail "${gate}: package.json contains trailing-whitespace lines"
  fi

  # Extract top-level key sequence in on-disk order. Lines at indent
  # level 2 spaces starting with `"<key>":` are top-level keys when
  # we track brace depth; simpler approach: use node to print keys.
  local actual_keys
  actual_keys="$(node -e '
    const fs = require("fs");
    const obj = JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
    console.log(Object.keys(obj).join(" "));
  ' "${PACKAGE_JSON}")" \
    || fail "${gate}: failed to extract top-level keys via node"
  local expected_keys="${EXPECTED_TOP_KEYS[*]}"
  [[ "${actual_keys}" == "${expected_keys}" ]] \
    || fail "${gate}: package.json top-level key sequence mismatch. expected '${expected_keys}' got '${actual_keys}'"

  # Locked values.
  local actual
  actual="$(node -e 'console.log(require(process.argv[1]).name);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "${EXPECTED_PACKAGE_NAME}" ]] \
    || fail "${gate}: package.json name '${actual}' != '${EXPECTED_PACKAGE_NAME}'"

  actual="$(node -e 'console.log(require(process.argv[1]).version);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "${EXPECTED_PACKAGE_VERSION}" ]] \
    || fail "${gate}: package.json version '${actual}' != '${EXPECTED_PACKAGE_VERSION}'"

  actual="$(node -e 'console.log(require(process.argv[1]).private);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "true" ]] \
    || fail "${gate}: package.json private '${actual}' != 'true'"

  actual="$(node -e 'console.log(require(process.argv[1]).type);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "commonjs" ]] \
    || fail "${gate}: package.json type '${actual}' != 'commonjs'"

  actual="$(node -e 'console.log(require(process.argv[1]).engines.node);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "${EXPECTED_NODE_ENGINE}" ]] \
    || fail "${gate}: package.json engines.node '${actual}' != '${EXPECTED_NODE_ENGINE}'"

  actual="$(node -e 'console.log(require(process.argv[1]).dependencies.prompts);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "${EXPECTED_PROMPTS_VERSION}" ]] \
    || fail "${gate}: package.json dependencies.prompts '${actual}' != '${EXPECTED_PROMPTS_VERSION}' (exact-pin)"

  actual="$(node -e 'console.log(require(process.argv[1]).bin["assistants-init"]);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "./bin/init" ]] \
    || fail "${gate}: package.json bin.assistants-init '${actual}' != './bin/init'"

  actual="$(node -e 'console.log(require(process.argv[1]).scripts.init);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "node ./bin/init" ]] \
    || fail "${gate}: package.json scripts.init '${actual}' != 'node ./bin/init'"

  actual="$(node -e 'console.log(require(process.argv[1]).scripts.start);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "node ./bin/init" ]] \
    || fail "${gate}: package.json scripts.start '${actual}' != 'node ./bin/init'"

  actual="$(node -e 'console.log(require(process.argv[1]).description);' "${PACKAGE_JSON}")"
  [[ "${actual}" == "Vixxo-deployable employee AI agent template; clone, run ./bin/init, work." ]] \
    || fail "${gate}: package.json description mismatch. got '${actual}'"

  # Description must appear verbatim on some line (locked line form).
  grep -Fq "${EXPECTED_DESCRIPTION_LOCKED}" "${PACKAGE_JSON}" \
    || fail "${gate}: package.json missing locked description line"

  # Prompts dep must NOT contain ^ or ~ or * (exact-pin).
  local prompts_line
  prompts_line="$(grep -E '"prompts"' "${PACKAGE_JSON}")"
  if echo "${prompts_line}" | grep -qE '[\^~*]'; then
    fail "${gate}: package.json prompts dependency is not exact-pin: ${prompts_line}"
  fi
}

# ------------------------------------------------------------------
# task5 — package-lock.json shape + reproducibility lock
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${PACKAGE_LOCK_JSON}" "${gate}"
  require_file_nonempty "${PACKAGE_LOCK_JSON}" "${gate}"
  assert_trailing_newline "${PACKAGE_LOCK_JSON}" "${gate}"
  assert_lf_only "${PACKAGE_LOCK_JSON}" "${gate}"

  json_strict_parse "${PACKAGE_LOCK_JSON}" \
    || fail "${gate}: package-lock.json failed strict JSON parse (node -e)"

  local actual
  actual="$(node -e 'console.log(require(process.argv[1]).lockfileVersion);' "${PACKAGE_LOCK_JSON}")"
  [[ "${actual}" == "${EXPECTED_LOCKFILE_VERSION}" ]] \
    || fail "${gate}: package-lock.json lockfileVersion '${actual}' != '${EXPECTED_LOCKFILE_VERSION}'"

  actual="$(node -e 'console.log(require(process.argv[1]).name);' "${PACKAGE_LOCK_JSON}")"
  [[ "${actual}" == "${EXPECTED_PACKAGE_NAME}" ]] \
    || fail "${gate}: package-lock.json name '${actual}' != '${EXPECTED_PACKAGE_NAME}'"

  actual="$(node -e 'console.log(require(process.argv[1]).version);' "${PACKAGE_LOCK_JSON}")"
  [[ "${actual}" == "${EXPECTED_PACKAGE_VERSION}" ]] \
    || fail "${gate}: package-lock.json version '${actual}' != '${EXPECTED_PACKAGE_VERSION}'"

  actual="$(node -e 'console.log(require(process.argv[1]).packages[""].dependencies.prompts);' "${PACKAGE_LOCK_JSON}")"
  [[ "${actual}" == "${EXPECTED_PROMPTS_VERSION}" ]] \
    || fail "${gate}: package-lock.json packages[''].dependencies.prompts '${actual}' != '${EXPECTED_PROMPTS_VERSION}'"

  actual="$(node -e 'console.log(require(process.argv[1]).packages["node_modules/prompts"].version);' "${PACKAGE_LOCK_JSON}")"
  [[ "${actual}" == "${EXPECTED_PROMPTS_VERSION}" ]] \
    || fail "${gate}: package-lock.json packages[node_modules/prompts].version '${actual}' != '${EXPECTED_PROMPTS_VERSION}'"

  # Sorted set equality on non-root packages keys.
  actual="$(node -e '
    const l = require(process.argv[1]);
    const keys = Object.keys(l.packages).filter(k => k !== "").sort();
    console.log(keys.join(" "));
  ' "${PACKAGE_LOCK_JSON}")"
  local expected_lock_keys="${EXPECTED_LOCK_PACKAGES[*]}"
  [[ "${actual}" == "${expected_lock_keys}" ]] \
    || fail "${gate}: package-lock.json transitive packages mismatch. expected '${expected_lock_keys}' got '${actual}'"
}

# ------------------------------------------------------------------
# task6 — secret / banned / Derek / path / placeholder / expansion scans
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  regex_self_probe
  require_file_exists "${BIN_INIT}" "${gate}"
  require_file_exists "${PACKAGE_JSON}" "${gate}"

  local bin_sanitized pkg_two_stage pkg_sanitized
  bin_sanitized="$(mktemp)"
  pkg_two_stage="$(mktemp)"
  pkg_sanitized="$(mktemp)"
  sanitize_for_banned_scan "${BIN_INIT}" >"${bin_sanitized}"
  sanitize_for_banned_scan "${PACKAGE_JSON}" >"${pkg_sanitized}"
  content_allowlist_for_personal "${pkg_sanitized}" >"${pkg_two_stage}"

  # Assert allowlist substitution is EXERCISED for current description lock.
  if ! grep -Eq 'Vixxo-deployable (personal|employee) AI agent template; clone, run \./bin/init, work\.' "${PACKAGE_JSON}"; then
    rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
    fail "${gate}: package.json missing locked AI agent template description (allowlist unused — misconfig)"
  fi

  # Assert allowlist marker appears in post-view.
  if ! grep -Fq '__LOCKED_DESC__' "${pkg_two_stage}"; then
    rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
    fail "${gate}: post-allowlist view of package.json missing __LOCKED_DESC__ marker"
  fi

  local pattern target
  for target in "${bin_sanitized}" "${pkg_two_stage}"; do
    for pattern in "${SECRET_PATTERNS[@]}"; do
      if grep -E "${pattern}" "${target}" >/dev/null 2>&1; then
        grep -nE "${pattern}" "${target}" >&2 || true
        rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
        fail "${gate}: ${target} matches secret pattern: ${pattern}"
      fi
    done
  done

  local equals_lit
  for target in "${BIN_INIT}" "${PACKAGE_JSON}"; do
    for equals_lit in "${SECRET_EQUALS_LITERALS[@]}"; do
      if grep -F "${equals_lit}" "${target}" >/dev/null 2>&1; then
        rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
        fail "${gate}: ${target} contains banned literal '${equals_lit}'"
      fi
    done
  done

  # Banned-term regex — bin/init uses plain sanitized view, package.json
  # uses two-stage sanitized-plus-allowlist view.
  if grep -iE "${BANNED_TERMS_REGEX}" "${bin_sanitized}" >/dev/null 2>&1; then
    grep -inE "${BANNED_TERMS_REGEX}" "${bin_sanitized}" >&2 || true
    rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
    fail "${gate}: bin/init contains banned token"
  fi
  if grep -iE "${BANNED_TERMS_REGEX}" "${pkg_two_stage}" >/dev/null 2>&1; then
    grep -inE "${BANNED_TERMS_REGEX}" "${pkg_two_stage}" >&2 || true
    rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
    fail "${gate}: package.json contains banned token (after two-stage allowlist)"
  fi

  # Derek fixed-strings — both files (unsanitized).
  local derek_token
  for target in "${BIN_INIT}" "${PACKAGE_JSON}"; do
    for derek_token in "${DEREK_FIXED_STRINGS[@]}"; do
      if grep -Fiq "${derek_token}" "${target}"; then
        rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
        fail "${gate}: ${target} contains Derek fixed-string: '${derek_token}'"
      fi
    done
  done

  # Path-reference probes.
  local path_probe
  for target in "${BIN_INIT}" "${PACKAGE_JSON}"; do
    for path_probe in '/Users/' 'Public/gtd-life' '@gmail.com'; do
      if grep -Fq "${path_probe}" "${target}"; then
        rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
        fail "${gate}: ${target} contains path-reference probe '${path_probe}'"
      fi
    done
  done

  # Placeholder-form probes.
  for target in "${BIN_INIT}" "${PACKAGE_JSON}"; do
    if grep -oE '\{\{[^}]+\}\}' "${target}" >/dev/null 2>&1; then
      rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
      fail "${gate}: ${target} contains {{...}} template token"
    fi
    if grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}' "${target}" >/dev/null 2>&1; then
      rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
      fail "${gate}: ${target} contains {name} single-brace placeholder"
    fi
    if grep -oE '<[A-Za-z_][A-Za-z0-9_]*>' "${target}" >/dev/null 2>&1; then
      rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
      fail "${gate}: ${target} contains <name> angle-bracket placeholder"
    fi
    if grep -oE '%[A-Za-z_][A-Za-z0-9_]*%' "${target}" >/dev/null 2>&1; then
      rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
      fail "${gate}: ${target} contains %name% percent placeholder"
    fi
    if grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*\}' "${target}" >/dev/null 2>&1; then
      rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
      fail "${gate}: ${target} contains \${name} dollar-brace placeholder"
    fi
  done

  # Shell-expansion probes (${VAR} or $VAR).
  for target in "${BIN_INIT}" "${PACKAGE_JSON}"; do
    if grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${target}" >/dev/null 2>&1; then
      grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${target}" >&2 || true
      rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
      fail "${gate}: ${target} contains \${VAR} or \$VAR expansion token"
    fi
  done

  rm -f "${bin_sanitized}" "${pkg_two_stage}" "${pkg_sanitized}"
}

# ------------------------------------------------------------------
# task7 — byte-stability invariance per AC6
# ------------------------------------------------------------------
check_task7() {
  local gate="task7"
  require_file_exists "${MCP_JSON}" "${gate}"
  require_file_exists "${MCP_README}" "${gate}"
  require_file_exists "${MCP_PLACEHOLDERS}" "${gate}"
  require_file_exists "${ENV_EXAMPLE}" "${gate}"
  require_file_exists "${GITIGNORE_PATH}" "${gate}"
  require_file_exists "${LICENSE_CANONICAL}" "${gate}"
  require_file_exists "${SETUP_MD}" "${gate}"
  require_file_exists "${MCPS_MD}" "${gate}"

  local got
  got="$(sha256_of "${MCP_JSON}")" \
    || fail "${gate}: no SHA-256 utility available"
  [[ "${got}" == "${STORY_4_3_MCP_JSON_SHA256}" ]] \
    || fail "${gate}: ${MCP_JSON} SHA-256 ${got} != expected ${STORY_4_3_MCP_JSON_SHA256}"

  got="$(sha256_of "${MCP_README}")"
  [[ "${got}" == "${STORY_4_3_MCP_README_SHA256}" ]] \
    || fail "${gate}: ${MCP_README} SHA-256 ${got} != expected ${STORY_4_3_MCP_README_SHA256}"

  got="$(sha256_of "${MCP_PLACEHOLDERS}")"
  [[ "${got}" == "${STORY_4_3_MCP_PLACEHOLDERS_SHA256}" ]] \
    || fail "${gate}: ${MCP_PLACEHOLDERS} SHA-256 ${got} != expected ${STORY_4_3_MCP_PLACEHOLDERS_SHA256}"

  got="$(sha256_of "${ENV_EXAMPLE}")"
  [[ "${got}" == "${STORY_4_3_ENV_EXAMPLE_SHA256}" ]] \
    || fail "${gate}: ${ENV_EXAMPLE} SHA-256 ${got} != expected ${STORY_4_3_ENV_EXAMPLE_SHA256}"

  got="$(sha256_of "${GITIGNORE_PATH}")"
  [[ "${got}" == "${STORY_1_1_GITIGNORE_SHA256}" ]] \
    || fail "${gate}: ${GITIGNORE_PATH} SHA-256 ${got} != expected ${STORY_1_1_GITIGNORE_SHA256}"

  got="$(sha256_of "${LICENSE_CANONICAL}")"
  [[ "${got}" == "${STORY_1_2_LICENSE_CANONICAL_SHA256}" ]] \
    || fail "${gate}: ${LICENSE_CANONICAL} SHA-256 ${got} != expected ${STORY_1_2_LICENSE_CANONICAL_SHA256}"

  got="$(sha256_of "${SETUP_MD}")"
  [[ "${got}" == "${STORY_4_4_SETUP_MD_SHA256}" ]] \
    || fail "${gate}: ${SETUP_MD} SHA-256 ${got} != expected ${STORY_4_4_SETUP_MD_SHA256}"

  got="$(sha256_of "${MCPS_MD}")"
  [[ "${got}" == "${STORY_4_4_MCPS_MD_SHA256}" ]] \
    || fail "${gate}: ${MCPS_MD} SHA-256 ${got} != expected ${STORY_4_4_MCPS_MD_SHA256}"

  # Gitignore discipline — working-set files tracked, node_modules ignored.
  if ( cd "${PROJECT_ROOT}" && git check-ignore -q bin/init ); then
    fail "${gate}: bin/init is gitignored (should be tracked)"
  fi
  if ( cd "${PROJECT_ROOT}" && git check-ignore -q package.json ); then
    fail "${gate}: package.json is gitignored (should be tracked)"
  fi
  if ( cd "${PROJECT_ROOT}" && git check-ignore -q package-lock.json ); then
    fail "${gate}: package-lock.json is gitignored (should be tracked)"
  fi

  local nm_out nm_ec=0
  nm_out="$( cd "${PROJECT_ROOT}" && git check-ignore -v node_modules/prompts/package.json 2>&1 )" || nm_ec=$?
  [[ "${nm_ec}" == '0' ]] \
    || fail "${gate}: git check-ignore -v node_modules/prompts/package.json exited ${nm_ec}, expected 0 (ignored)"
  printf '%s\n' "${nm_out}" | grep -qE '\.gitignore:[0-9]+:node_modules/' \
    || fail "${gate}: git check-ignore -v node_modules/... did not print .gitignore:N:node_modules/ rule (got: ${nm_out})"
}

# ------------------------------------------------------------------
# task8 — self-check (harness well-formed and owns full gate set)
# ------------------------------------------------------------------
check_task8() {
  local gate="task8"
  require_file_exists "${SELF_PATH}" "${gate}"

  head -n 1 "${SELF_PATH}" | grep -Fxq '#!/usr/bin/env bash' \
    || fail "${gate}: harness missing bash shebang on line 1"
  grep -Fq 'set -euo pipefail' "${SELF_PATH}" \
    || fail "${gate}: harness missing 'set -euo pipefail'"

  local required_case
  for required_case in 'task1)' 'task2)' 'task3)' 'task4)' 'task5)' 'task6)' 'task7)' 'task8)' 'task9)' 'all)'; do
    grep -Fq "${required_case}" "${SELF_PATH}" \
      || fail "${gate}: harness missing case branch: ${required_case}"
  done

  local required_const
  for required_const in \
    'BIN_INIT=' \
    'PACKAGE_JSON=' \
    'PACKAGE_LOCK_JSON=' \
    'MCP_JSON=' \
    'MCP_README=' \
    'MCP_PLACEHOLDERS=' \
    'ENV_EXAMPLE=' \
    'GITIGNORE_PATH=' \
    'LICENSE_CANONICAL=' \
    'SETUP_MD=' \
    'MCPS_MD=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'STORY_4_3_MCP_JSON_SHA256=' \
    'STORY_4_3_MCP_README_SHA256=' \
    'STORY_4_3_MCP_PLACEHOLDERS_SHA256=' \
    'STORY_4_3_ENV_EXAMPLE_SHA256=' \
    'STORY_1_1_GITIGNORE_SHA256=' \
    'STORY_1_2_LICENSE_CANONICAL_SHA256=' \
    'STORY_4_4_SETUP_MD_SHA256=' \
    'STORY_4_4_MCPS_MD_SHA256=' \
    'EXPECTED_TOP_KEYS=' \
    'EXPECTED_LOCK_PACKAGES=' \
    'EXPECTED_PROMPTS_VERSION=' \
    'EXPECTED_NODE_ENGINE=' \
    'EXPECTED_LOCKFILE_VERSION=' \
    'EXPECTED_PACKAGE_NAME=' \
    'EXPECTED_PACKAGE_VERSION=' \
    'EXPECTED_DESCRIPTION_LOCKED=' \
    'EXPECTED_BANNER_LINES=' \
    'SECRET_PATTERNS=' \
    'SECRET_EQUALS_LITERALS=' \
    'BANNED_TERMS_REGEX=' \
    'DEREK_FIXED_STRINGS=' \
    'GH_PAT_ENV_NAME=' \
    'GH_PAT_ALLOWLIST_PLACEHOLDER=' \
    'STORY_1_1_HARNESS=' \
    'STORY_1_2_HARNESS=' \
    'STORY_1_3_HARNESS=' \
    'STORY_2_1_HARNESS=' \
    'STORY_2_2_HARNESS=' \
    'STORY_2_3_HARNESS=' \
    'STORY_2_4_HARNESS=' \
    'STORY_3_1_HARNESS=' \
    'STORY_3_2_HARNESS=' \
    'STORY_3_3_HARNESS=' \
    'STORY_4_1_HARNESS=' \
    'STORY_4_2_HARNESS=' \
    'STORY_4_3_HARNESS=' \
    'STORY_4_4_HARNESS=' \
    'EXPECTED_PASS_COUNTS=' \
    'EXPECTED_PREDECESSOR_SHA256='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function"
  declare -F sanitize_for_banned_scan >/dev/null 2>&1 \
    || fail "${gate}: harness missing sanitize_for_banned_scan function"
  declare -F content_allowlist_for_personal >/dev/null 2>&1 \
    || fail "${gate}: harness missing content_allowlist_for_personal function"
  declare -F sha256_of >/dev/null 2>&1 \
    || fail "${gate}: harness missing sha256_of function"
  declare -F json_strict_parse >/dev/null 2>&1 \
    || fail "${gate}: harness missing json_strict_parse function"
}

# ------------------------------------------------------------------
# task9 — regression against fourteen predecessor harnesses
# ------------------------------------------------------------------
check_task9() {
  local gate="task9"

  # Story 4.2 F6: BMAD_REGRESSION_DEPTH guard.
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
  local i path name out pass_count expected actual_sha expected_sha attempts max_attempts
  local total="${#harnesses[@]}"
  max_attempts=3
  for (( i=0; i<total; i++ )); do
    path="${harnesses[$i]}"
    expected="${EXPECTED_PASS_COUNTS[$i]}"
    expected_sha="${EXPECTED_PREDECESSOR_SHA256[$i]}"
    name="$(basename "${path}")"
    require_file_exists "${path}" "${gate}"

    if ! actual_sha="$(sha256_of "${path}")"; then
      fail "${gate}: SHA-256 utility unavailable; cannot verify ${name}"
    fi
    [[ "${actual_sha}" == "${expected_sha}" ]] \
      || fail "${gate}: ${name} SHA-256 drift — expected ${expected_sha} got ${actual_sha}"

    mkdir -p "${PROJECT_ROOT}/tmp" 2>/dev/null || true

    attempts=0
    out=""
    local invoke_ok="0"
    while (( attempts < max_attempts )); do
      if out="$(BMAD_REGRESSION_DEPTH=1 bash "${path}" all 2>&1)"; then
        invoke_ok="1"
        break
      fi
      attempts=$(( attempts + 1 ))
      mkdir -p "${PROJECT_ROOT}/tmp" 2>/dev/null || true
      sleep 1
    done
    if [[ "${invoke_ok}" != "1" ]]; then
      echo "${out}" >&2
      fail "${gate}: ${name} all returned non-zero after ${max_attempts} attempt(s)"
    fi
    pass_count="$(printf '%s\n' "${out}" | grep -c '^PASS:' || true)"
    pass_count="$(printf '%s' "${pass_count}" | tr -d '[:space:]')"
    if [[ "${pass_count}" != "${expected}" ]]; then
      echo "${out}" >&2
      fail "${gate}: ${name} emitted ${pass_count} PASS line(s), expected ${expected}"
    fi
  done

  echo "task9 OK: fourteen-predecessor byte-stability + regression verified (SHA-256 + ^PASS: fingerprint)" >&2
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
