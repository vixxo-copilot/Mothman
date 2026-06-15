#!/usr/bin/env bash
set -euo pipefail

# Story 4.2 — Add commented-out placeholders for pending MCPs —
# deterministic validation harness.
#
# Scope:
#   - Story 4.2 creates `.cursor/mcp.placeholders.md`, the Story 4.1-locked
#     pending-MCP companion file for `.cursor/mcp.json`. Strict JSON
#     forbids `//` and `/* */` comments; Cursor's 2026 parser silently
#     rejects any `.cursor/mcp.json` that attempts them. The placeholders
#     therefore live as fenced `json` blocks inside a markdown companion
#     with `// TODO:` markdown lines OUTSIDE the fences.
#   - Eleven pending MCPs in canonical order: Freshdesk, Dynamics,
#     VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect,
#     ChatFPT, Elastic, agent-skills Introspection MCP (server key
#     `introspection`).
#   - `.cursor/mcp.json` and `.cursor/mcp.README.md` remain byte-stable
#     during Story 4.2 — SHA-256 fingerprints asserted (see AC6). The
#     `.gitignore` fingerprint continues to match the Story 1.1 F1-patch
#     handoff value.
#   - Regression chain extends Story 4.1's ten-harness chain by one
#     (adds Story 4.1 as the eleventh predecessor). Empirical
#     `^PASS:` line-count vector captured 2026-04-21:
#     ( 1 1 1 1 10 7 7 7 7 7 10 ) — matches the story's expected vector.
#
# Banned-term allowlist (inherited verbatim from Story 4.1 F1):
#   The AC7 boundary-guarded banned-term regex contains the token
#   `personal`. The GitHub canonical env-var name
#   `GITHUB_PERSONAL_ACCESS_TOKEN` is NOT expected in
#   `.cursor/mcp.placeholders.md` (GitHub is an active MCP; its env-var
#   documentation lives in `.cursor/mcp.README.md`). The pre-filter is
#   carried forward defensively for uniformity across the harness family.
#
# Gates:
#   task1  baseline-audit artifact present + structured
#   task2  canonical-blueprint artifact present + structured
#   task3  .cursor/mcp.placeholders.md shape: exists, non-empty, LF-only,
#          trailing newline, frontmatter first three bytes `---`,
#          frontmatter keys in canonical order (type, scope, created,
#          updated, tags), H1 present, preamble paragraph present,
#          exactly thirteen H2 sections in canonical order,
#          `<!-- Why: ... -->` terminator on last non-blank line
#   task4  per-entry field presence: eleven `**Status:** placeholder —
#          not wired` lines, eleven `// TODO: wiring; see ` lines,
#          eleven ` ```json ` opening fences, each pending-MCP H2 has
#          its four required `**Field:**` markers
#   task5  per-entry JSON validity: awk-extract each of the eleven
#          fenced json blocks, python3 -m json.tool each (exit 0 x 11),
#          assert top-level key matches the corresponding
#          EXPECTED_PLACEHOLDER_KEYS entry, assert nested value is an
#          object with key set subset of {command, args, url, headers}
#          (zero `env` blocks); assert zero ${VAR}/$VAR tokens in the
#          whole file
#   task6  secret-shape + banned-term scan per AC7: eleven secret-pattern
#          regexes on sanitized view of the file (zero matches);
#          banned-term regex zero matches; twelve Derek fixed-string
#          probes zero matches; three path-reference probes zero matches;
#          five placeholder-form probes zero matches; four
#          password=/token=/secret=/api_key= literal probes zero matches
#   task7  byte-stability invariance per AC6: .cursor/mcp.json SHA-256
#          matches STORY_4_1_MCP_JSON_SHA256, .cursor/mcp.README.md
#          SHA-256 matches STORY_4_1_MCP_README_SHA256, .gitignore SHA-256
#          matches STORY_1_1_GITIGNORE_SHA256; git check-ignore -v on the
#          placeholders file exits non-zero
#   task8  self-check: shebang line 1, `set -euo pipefail`, every case
#          arm present (task1..task9, all), every declared constant
#          referenced, helper functions defined
#   task9  regression: eleven predecessor harnesses run in `all` mode;
#          each exits 0; each emits the expected `^PASS:` line-count
#          vector `( 1 1 1 1 10 7 7 7 7 7 10 )`
#   all    runs task1 -> task9 sequentially; exits 0 with exactly 10
#          `^PASS:` lines on success
#
# Tooling: POSIX-bash-3.2 compatible (no associative arrays, no namerefs).
# Uses bash, grep, awk, sed, find, tr, wc, head, tail, od, cut, sort,
# python3 -m json.tool, and shell built-ins. BSD-grep and GNU-grep
# compatible. Intentionally does NOT use rg, jq, yq, node.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

PLACEHOLDERS_FILE="${PROJECT_ROOT}/.cursor/mcp.placeholders.md"
MCP_JSON="${PROJECT_ROOT}/.cursor/mcp.json"
MCP_README="${PROJECT_ROOT}/.cursor/mcp.README.md"
GITIGNORE_PATH="${PROJECT_ROOT}/.gitignore"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-4-2-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-4-2-canonical-blueprint.md"

# Byte-stability SHA-256 constants (captured Task 1 2026-04-21 from
# on-disk Story 4.1 artifacts; see story-4-2-baseline-audit.md
# `## Byte-stability fingerprints` section for the discrepancy note vs.
# the Story 4.1 handoff).
STORY_4_1_MCP_JSON_SHA256="d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c"
STORY_4_1_MCP_README_SHA256="4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09"
STORY_1_1_GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"

# Eleven pending-MCP server keys, canonical order (AC2 + AC3 lock;
# matches the Story 4.1 DENY_LIST_SERVER_KEYS subset).
EXPECTED_PLACEHOLDER_KEYS=(
  freshdesk
  dynamics
  vixxonow
  vixxolink
  gateway
  zoominfo
  hubspot
  aws-connect
  chatfpt
  elastic
  introspection
)

# Thirteen H2 headings in canonical order (AC2 lock: eleven pending MCPs
# + Conventions + Forward References).
EXPECTED_H2_HEADINGS=(
  "## Freshdesk"
  "## Dynamics"
  "## VixxoNow"
  "## VixxoLink"
  "## Gateway"
  "## ZoomInfo"
  "## HubSpot"
  "## AWS Connect"
  "## ChatFPT"
  "## Elastic"
  "## agent-skills Introspection MCP"
  "## Conventions"
  "## Forward References"
)

# Eleven secret-pattern regexes (inherited verbatim from Story 4.1 AC4).
# Case-sensitive. Applied to the placeholders file (sanitized view for
# uniformity; GH_PAT pre-filter is a no-op on this file in practice).
# Zero matches expected per pattern.
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

# Literal key=value substrings banned (defense-in-depth).
SECRET_EQUALS_LITERALS=( 'password=' 'token=' 'secret=' 'api_key=' )

# Seventeen-token boundary-guarded banned-term regex (inherited verbatim
# from Stories 3.1 / 3.2 / 3.3 / 4.1). Case-insensitive via `grep -iE`.
BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'

# Twelve Derek defense-in-depth fixed-string probes (AC7 inherited).
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

# GH PAT allowlist (inherited verbatim from Story 4.1 F1). No-op on
# `.cursor/mcp.placeholders.md` in practice; carried forward for harness
# family uniformity so the sanitizer code path is exercised.
GH_PAT_ENV_NAME="GITHUB_PERSONAL_ACCESS_TOKEN"
GH_PAT_ALLOWLIST_PLACEHOLDER="__GH_PAT_NAME__"

# Eleven predecessor harness paths (AC9). Story 4.1 is the eleventh.
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

# Empirical `^PASS:` line-count fingerprint per predecessor harness in
# `all` mode, measured 2026-04-21 in this worktree. Positional parallel
# to the eleven STORY_*_HARNESS constants above. Matches the story's
# expected vector exactly (see story-4-2-baseline-audit.md).
EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 )

# SHA-256 byte-stability anchor per predecessor harness (Story 4.2
# review-fix F5: port forward Story 4.1's EXPECTED_PREDECESSOR_SHA256
# pattern). Positional parallel to STORY_*_HARNESS / EXPECTED_PASS_COUNTS.
# check_task9 verifies each value BEFORE invocation; drift = silent
# regression, fail the gate.
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
  "77a5376887f03909223074b2f21e1306f689a9238d6da0cf191aa79a0427b427"
  "cfe810169aef5c2abf7bc021aad4fbb43d3c91eda58fc99b3d16123907dbba8f"
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

# Compute SHA-256 of a file on stdout. Portable across macOS (BSD
# `shasum -a 256`), Linux (`sha256sum`), and OpenSSL fallback. Prints a
# 64-char lowercase hex digest with NO trailing whitespace. Returns 1 if
# no SHA-256 utility is available.
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

# Sanitize a file's contents by replacing the GitHub canonical PAT env
# var name with a neutral token (Story 4.1 F1 codification; carried
# forward). Emits sanitized content to stdout.
sanitize_for_banned_scan() {
  local path="$1"
  sed -E "s/${GH_PAT_ENV_NAME}/${GH_PAT_ALLOWLIST_PLACEHOLDER}/g" "${path}"
}

# Awk-extract each fenced ` ```json ` block in the placeholders file
# into a temp file. Prints the temp-file paths, one per line, on stdout.
# Caller is responsible for `rm -f` when done. Produces exactly eleven
# temp files when the file is well-formed.
extract_fenced_json_blocks() {
  local src="$1"
  local out_dir
  out_dir="$(mktemp -d 2>/dev/null || mktemp -d -t story42)"
  awk -v outdir="${out_dir}" '
    BEGIN { in_block = 0; idx = 0; path = "" }
    /^```json$/ { in_block = 1; idx += 1; path = sprintf("%s/block-%02d.json", outdir, idx); next }
    /^```$/ && in_block == 1 { in_block = 0; next }
    in_block == 1 { print $0 > path }
  ' "${src}"
  # Emit sorted list of extracted files so the caller sees them in
  # block-order (block-01 ... block-11).
  ls "${out_dir}"/block-*.json 2>/dev/null | sort
}

regex_self_probe() {
  # (a) banned-term boundary check — positive for `derek`, rejected for `derekson`.
  if echo "derekson" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary admitted 'derekson' (grep too permissive)"
  fi
  if ! echo "derek smith" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary rejected legitimate hit 'derek smith'"
  fi

  # (b) GitHub PAT secret pattern — positive for synthetic hit, short-rejected.
  if ! echo "ghp_aaaabbbbccccddddeeee1234" | grep -E 'ghp_[A-Za-z0-9]{20,}' >/dev/null; then
    fail "regex probe: ghp_ pattern rejected legitimate 24+ char hit"
  fi
  if echo "ghp_short" | grep -E 'ghp_[A-Za-z0-9]{20,}' >/dev/null; then
    fail "regex probe: ghp_ pattern admitted short 'ghp_short'"
  fi

  # (c) ${VAR} / $VAR probes — both forms must be caught; literal 'dollar sign' must not.
  if ! echo '${FOO}' | grep -E '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' >/dev/null; then
    fail "regex probe: \${VAR} scan missed '\${FOO}'"
  fi
  if ! echo '$foo' | grep -E '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' >/dev/null; then
    fail "regex probe: \$VAR scan missed '\$foo'"
  fi
  if echo 'dollar sign' | grep -E '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' >/dev/null; then
    fail "regex probe: dollar-expansion scan hit benign 'dollar sign'"
  fi

  # (d) Angle-bracket placeholder-form — positive for `<name>`,
  #     rejected for HTML comments and bracketed URLs.
  if ! echo '<name>' | grep -E '<[A-Za-z_][A-Za-z0-9_]*>' >/dev/null; then
    fail "regex probe: angle-bracket probe missed literal '<name>'"
  fi
  if echo '<!-- comment -->' | grep -E '<[A-Za-z_][A-Za-z0-9_]*>' >/dev/null; then
    fail "regex probe: angle-bracket probe tripped on HTML comment '<!-- comment -->'"
  fi
  if echo '<https://example>' | grep -E '<[A-Za-z_][A-Za-z0-9_]*>' >/dev/null; then
    fail "regex probe: angle-bracket probe tripped on bracketed URL '<https://example>'"
  fi

  # (e) GH_PAT allowlist pre-filter behavioural probe (inherited Story 4.1):
  #     raw GITHUB_PERSONAL_ACCESS_TOKEN trips banned-term regex;
  #     sanitized string does not.
  if ! echo "GITHUB_PERSONAL_ACCESS_TOKEN" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term regex failed to trip on raw GH PAT name (sanity check)"
  fi
  local sanitized
  sanitized="$(echo "GITHUB_PERSONAL_ACCESS_TOKEN" | sed -E "s/${GH_PAT_ENV_NAME}/${GH_PAT_ALLOWLIST_PLACEHOLDER}/g")"
  if echo "${sanitized}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: allowlist pre-filter failed — sanitized GH PAT still trips banned-term regex"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 4.2 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 4.2 Baseline Audit'"

  local section
  for section in \
    'Placeholder convention re-confirmation' \
    'Per-server research' \
    'Deny-list cross-reference with Story 4.1' \
    'Byte-stability fingerprints' \
    'Predecessor-harness compatibility scan' \
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

  grep -Fq '# Story 4.2 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 4.2 Canonical Blueprint'"

  local server
  for server in Freshdesk Dynamics VixxoNow VixxoLink Gateway ZoomInfo HubSpot 'AWS Connect' ChatFPT Elastic 'agent-skills Introspection MCP'; do
    if ! grep -Fq "### ${server}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing per-server subsection for '${server}'"
    fi
  done

  local required
  for required in \
    'Frontmatter lock' \
    'Body section order lock' \
    'Per-server H2 template lock' \
    'Per-server content locks' \
    'Conventions body lock' \
    'Forward References body lock' \
    'Banned-term lock (inherited verbatim)' \
    'Secret-pattern catalog lock (inherited verbatim)' \
    'Placeholder-form probes (inherited verbatim)' \
    'Deny-list cross-reference (Story 4.1)' \
    'Evidence constants for Task 5 harness' \
    'Inheritance-only note'; do
    if ! grep -Fq "${required}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing required subsection: '${required}'"
    fi
  done
}

# ------------------------------------------------------------------
# task3 — .cursor/mcp.placeholders.md shape verification
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${PLACEHOLDERS_FILE}" "${gate}"
  require_file_nonempty "${PLACEHOLDERS_FILE}" "${gate}"
  assert_trailing_newline "${PLACEHOLDERS_FILE}" "${gate}"
  assert_lf_only "${PLACEHOLDERS_FILE}" "${gate}"

  # Frontmatter first three bytes.
  local first3
  first3="$(head -c 3 "${PLACEHOLDERS_FILE}")"
  [[ "${first3}" == '---' ]] \
    || fail "${gate}: ${PLACEHOLDERS_FILE} first 3 bytes are '${first3}', expected '---'"

  # Frontmatter key order between the two `---` delimiters.
  local fm_keys expected_fm_keys
  fm_keys="$(awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}' "${PLACEHOLDERS_FILE}" \
    | grep -oE '^[a-zA-Z_][a-zA-Z0-9_]*:' \
    | sed 's/:$//' | tr '\n' ' ')"
  expected_fm_keys="type scope created updated tags "
  [[ "${fm_keys}" == "${expected_fm_keys}" ]] \
    || fail "${gate}: ${PLACEHOLDERS_FILE} frontmatter key order is '${fm_keys}', expected '${expected_fm_keys}'"

  # Frontmatter literal values.
  local fm_body
  fm_body="$(awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}' "${PLACEHOLDERS_FILE}")"
  printf '%s\n' "${fm_body}" | grep -Fxq 'type: mcp-placeholders' \
    || fail "${gate}: ${PLACEHOLDERS_FILE} frontmatter missing 'type: mcp-placeholders'"
  printf '%s\n' "${fm_body}" | grep -Fxq 'scope: work' \
    || fail "${gate}: ${PLACEHOLDERS_FILE} frontmatter missing 'scope: work'"
  printf '%s\n' "${fm_body}" | grep -Fxq 'created: 2026-04-21' \
    || fail "${gate}: ${PLACEHOLDERS_FILE} frontmatter missing 'created: 2026-04-21'"
  printf '%s\n' "${fm_body}" | grep -Fxq 'updated: 2026-04-21' \
    || fail "${gate}: ${PLACEHOLDERS_FILE} frontmatter missing 'updated: 2026-04-21'"
  printf '%s\n' "${fm_body}" | grep -Fxq 'tags: [mcp, work, placeholder]' \
    || fail "${gate}: ${PLACEHOLDERS_FILE} frontmatter missing 'tags: [mcp, work, placeholder]'"

  # H1 present.
  grep -Fxq '# Pending MCPs (.cursor/mcp.placeholders.md)' "${PLACEHOLDERS_FILE}" \
    || fail "${gate}: ${PLACEHOLDERS_FILE} missing H1 '# Pending MCPs (.cursor/mcp.placeholders.md)'"

  # Preamble paragraph present — `Story 4.2 placeholder companion` phrase.
  grep -Fq 'Story 4.2 placeholder companion for `.cursor/mcp.json`' "${PLACEHOLDERS_FILE}" \
    || fail "${gate}: ${PLACEHOLDERS_FILE} missing preamble phrase"

  # Exactly thirteen H2 headings in canonical order.
  local h2_count
  h2_count="$(grep -c '^## ' "${PLACEHOLDERS_FILE}")"
  [[ "${h2_count}" == '13' ]] \
    || fail "${gate}: ${PLACEHOLDERS_FILE} has ${h2_count} H2 headings, expected 13"

  local heading prev_line=0 hline
  for heading in "${EXPECTED_H2_HEADINGS[@]}"; do
    hline="$(grep -Fxn "${heading}" "${PLACEHOLDERS_FILE}" | head -n 1 | cut -d: -f1)"
    [[ -n "${hline}" ]] \
      || fail "${gate}: ${PLACEHOLDERS_FILE} missing H2 heading: '${heading}'"
    (( hline > prev_line )) \
      || fail "${gate}: ${PLACEHOLDERS_FILE} heading '${heading}' (line ${hline}) not after prior heading (line ${prev_line})"
    prev_line="${hline}"
  done

  # `<!-- Why: ... -->` terminator on last non-blank line.
  local last_nb
  last_nb="$(awk 'NF' "${PLACEHOLDERS_FILE}" | tail -n 1)"
  case "${last_nb}" in
    '<!-- Why: '*'-->') ;;
    *) fail "${gate}: ${PLACEHOLDERS_FILE} last non-blank line is not the '<!-- Why: ... -->' terminator (got: ${last_nb})" ;;
  esac
}

# ------------------------------------------------------------------
# task4 — per-entry field presence + counts
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${PLACEHOLDERS_FILE}" "${gate}"

  # Status literal lines — exactly eleven.
  local status_count
  status_count="$(grep -c '^\*\*Status:\*\* placeholder — not wired$' "${PLACEHOLDERS_FILE}")"
  [[ "${status_count}" == '11' ]] \
    || fail "${gate}: '**Status:** placeholder — not wired' count is ${status_count}, expected 11"

  # `// TODO: wiring; see ` prefix — exactly eleven.
  local todo_count
  todo_count="$(grep -c '^// TODO: wiring; see ' "${PLACEHOLDERS_FILE}")"
  [[ "${todo_count}" == '11' ]] \
    || fail "${gate}: '^// TODO: wiring; see ' prefix count is ${todo_count}, expected 11"

  # Fenced `json` opener fences — exactly eleven.
  local fence_count
  fence_count="$(grep -c '^```json$' "${PLACEHOLDERS_FILE}")"
  [[ "${fence_count}" == '11' ]] \
    || fail "${gate}: '^\`\`\`json\$' opener count is ${fence_count}, expected 11"

  # For each pending-MCP H2, the four required `**Field:**` markers
  # must appear between that H2 and the next H2.
  local h2 start_line end_line section_body marker
  local markers=(
    '**Purpose:**'
    '**Status:**'
    '**Intended transport:**'
    '**Wiring reference:**'
  )
  local pending_h2s=(
    '## Freshdesk'
    '## Dynamics'
    '## VixxoNow'
    '## VixxoLink'
    '## Gateway'
    '## ZoomInfo'
    '## HubSpot'
    '## AWS Connect'
    '## ChatFPT'
    '## Elastic'
    '## agent-skills Introspection MCP'
  )
  for h2 in "${pending_h2s[@]}"; do
    start_line="$(grep -Fxn "${h2}" "${PLACEHOLDERS_FILE}" | head -n 1 | cut -d: -f1)"
    [[ -n "${start_line}" ]] \
      || fail "${gate}: ${PLACEHOLDERS_FILE} missing H2 '${h2}'"
    end_line="$(awk -v s="${start_line}" 'NR>s && /^## /{print NR; exit}' "${PLACEHOLDERS_FILE}")"
    [[ -n "${end_line}" ]] || end_line="$(wc -l <"${PLACEHOLDERS_FILE}" | tr -d '[:space:]')"
    section_body="$(awk -v s="${start_line}" -v e="${end_line}" 'NR>=s && NR<e' "${PLACEHOLDERS_FILE}")"
    for marker in "${markers[@]}"; do
      if ! printf '%s\n' "${section_body}" | grep -Fq "${marker}"; then
        fail "${gate}: ${PLACEHOLDERS_FILE} section '${h2}' missing required field marker '${marker}'"
      fi
    done
    # Fenced json block must appear inside the section.
    if ! printf '%s\n' "${section_body}" | grep -Fxq '```json'; then
      fail "${gate}: ${PLACEHOLDERS_FILE} section '${h2}' missing fenced \`\`\`json block"
    fi
    # TODO line must appear inside the section.
    if ! printf '%s\n' "${section_body}" | grep -q '^// TODO: wiring; see '; then
      fail "${gate}: ${PLACEHOLDERS_FILE} section '${h2}' missing // TODO: wiring line"
    fi
  done
}

# ------------------------------------------------------------------
# task5 — per-entry JSON validity + keyset assertions + ${VAR} absence
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${PLACEHOLDERS_FILE}" "${gate}"

  local tmp_files
  tmp_files="$(extract_fenced_json_blocks "${PLACEHOLDERS_FILE}")"

  local file_count
  file_count="$(printf '%s\n' "${tmp_files}" | grep -c '\.json$' || true)"
  file_count="$(printf '%s' "${file_count}" | tr -d '[:space:]')"
  [[ "${file_count}" == '11' ]] \
    || fail "${gate}: extracted ${file_count} fenced json blocks, expected 11"

  # Individual python3 -m json.tool parse.
  local f
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    if ! python3 -m json.tool "${f}" >/dev/null 2>&1; then
      fail "${gate}: fenced json block ${f} fails python3 -m json.tool strict-JSON parse"
    fi
  done <<<"${tmp_files}"

  # Keyset + positional assertion.
  local keys_block files_block
  keys_block="$(printf '%s\n' "${EXPECTED_PLACEHOLDER_KEYS[@]}")"
  files_block="${tmp_files}"
  if ! python3 - "${keys_block}" "${files_block}" <<'PY' >/dev/null
import json, sys
keys = [k for k in sys.argv[1].splitlines() if k]
files = [f for f in sys.argv[2].splitlines() if f]
assert len(keys) == 11, f"expected 11 keys, got {len(keys)}"
assert len(files) == 11, f"expected 11 block files, got {len(files)}"
allowed = {"command", "args", "url", "headers"}
for i, (k, path) in enumerate(zip(keys, files)):
    with open(path, 'r', encoding='utf-8') as fh:
        d = json.load(fh)
    assert isinstance(d, dict), f"block {i} root not object"
    assert len(d) == 1, f"block {i} ({k}): {len(d)} top-level keys"
    got_key = list(d.keys())[0]
    assert got_key == k, f"block {i}: key {got_key!r} != expected {k!r}"
    v = d[got_key]
    assert isinstance(v, dict), f"{k}: value not object"
    assert "env" not in v, f"{k}: contains forbidden env block"
    unk = set(v.keys()) - allowed
    assert not unk, f"{k}: unknown keys {unk}"
    if "command" in v:
        assert isinstance(v["command"], str)
        assert isinstance(v.get("args"), list)
        for j, a in enumerate(v["args"]):
            assert isinstance(a, str), f"{k}.args[{j}] not string"
    elif "url" in v:
        assert isinstance(v["url"], str)
    else:
        raise AssertionError(f"{k} has neither command nor url")
PY
  then
    # Clean up before failing.
    local d
    while IFS= read -r d; do
      [[ -z "${d}" ]] && continue
      rm -f "${d}"
    done <<<"${tmp_files}"
    local parent_dir
    parent_dir="$(dirname "$(printf '%s' "${tmp_files}" | head -n 1)")"
    [[ -d "${parent_dir}" ]] && rmdir "${parent_dir}" 2>/dev/null || true
    fail "${gate}: per-entry JSON keyset / positional assertions failed"
  fi

  # Clean up temp files.
  local tmp_first tmp_dir
  tmp_first="$(printf '%s' "${tmp_files}" | head -n 1)"
  tmp_dir="$(dirname "${tmp_first}")"
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    rm -f "${f}"
  done <<<"${tmp_files}"
  [[ -d "${tmp_dir}" ]] && rmdir "${tmp_dir}" 2>/dev/null || true

  # ${VAR} / $VAR absence in the whole file.
  if grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${PLACEHOLDERS_FILE}" >/dev/null 2>&1; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains \${VAR} or \$VAR expansion token"
  fi
}

# ------------------------------------------------------------------
# task6 — secret-shape + banned-term + placeholder-form scans (AC7)
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  regex_self_probe
  require_file_exists "${PLACEHOLDERS_FILE}" "${gate}"

  # Secret patterns against sanitized view.
  local sanitized
  sanitized="$(sanitize_for_banned_scan "${PLACEHOLDERS_FILE}")"
  local pattern
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if printf '%s\n' "${sanitized}" | grep -E "${pattern}" >/dev/null 2>&1; then
      printf '%s\n' "${sanitized}" | grep -nE "${pattern}" >&2 || true
      fail "${gate}: ${PLACEHOLDERS_FILE} matches secret pattern: ${pattern}"
    fi
  done

  # password=/token=/secret=/api_key= literal substrings.
  local equals_lit
  for equals_lit in "${SECRET_EQUALS_LITERALS[@]}"; do
    if grep -F "${equals_lit}" "${PLACEHOLDERS_FILE}" >/dev/null 2>&1; then
      fail "${gate}: ${PLACEHOLDERS_FILE} contains banned literal substring '${equals_lit}'"
    fi
  done

  # Banned-term regex against sanitized view.
  if printf '%s\n' "${sanitized}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null 2>&1; then
    printf '%s\n' "${sanitized}" | grep -inE "${BANNED_TERMS_REGEX}" >&2 || true
    fail "${gate}: ${PLACEHOLDERS_FILE} contains banned token (after GH PAT allowlist pre-filter)"
  fi

  # Derek fixed-string probes.
  local derek_token
  for derek_token in "${DEREK_FIXED_STRINGS[@]}"; do
    if grep -Fiq "${derek_token}" "${PLACEHOLDERS_FILE}"; then
      fail "${gate}: ${PLACEHOLDERS_FILE} contains Derek fixed-string token: '${derek_token}'"
    fi
  done

  # Path-reference probes.
  if grep -Fq '/Users/' "${PLACEHOLDERS_FILE}"; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains absolute-path fragment '/Users/'"
  fi
  if grep -Fq 'Public/gtd-life' "${PLACEHOLDERS_FILE}"; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains source-repo fragment 'Public/gtd-life'"
  fi
  if grep -Fq '@gmail.com' "${PLACEHOLDERS_FILE}"; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains personal-mailbox domain '@gmail.com'"
  fi

  # Placeholder-form probes (inherited Story 4.1 forbidden-form lock).
  if grep -oE '\{\{[^}]+\}\}' "${PLACEHOLDERS_FILE}" >/dev/null 2>&1; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains forbidden {{...}} template token"
  fi
  if grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}' "${PLACEHOLDERS_FILE}" >/dev/null 2>&1; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains forbidden {name} single-brace placeholder"
  fi
  if grep -oE '<[A-Za-z_][A-Za-z0-9_]*>' "${PLACEHOLDERS_FILE}" >/dev/null 2>&1; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains forbidden <name> angle-bracket placeholder"
  fi
  if grep -oE '%[A-Za-z_][A-Za-z0-9_]*%' "${PLACEHOLDERS_FILE}" >/dev/null 2>&1; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains forbidden %name% percent placeholder"
  fi
  if grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*\}' "${PLACEHOLDERS_FILE}" >/dev/null 2>&1; then
    fail "${gate}: ${PLACEHOLDERS_FILE} contains forbidden \${name} dollar-brace placeholder"
  fi
}

# ------------------------------------------------------------------
# task7 — byte-stability invariance per AC6
# ------------------------------------------------------------------
check_task7() {
  local gate="task7"
  require_file_exists "${MCP_JSON}" "${gate}"
  require_file_exists "${MCP_README}" "${gate}"
  require_file_exists "${GITIGNORE_PATH}" "${gate}"

  local got
  if ! got="$(sha256_of "${MCP_JSON}")"; then
    fail "${gate}: no SHA-256 utility available; cannot verify byte-stability"
  fi
  [[ "${got}" == "${STORY_4_1_MCP_JSON_SHA256}" ]] \
    || fail "${gate}: ${MCP_JSON} SHA-256 ${got} != expected ${STORY_4_1_MCP_JSON_SHA256}"

  got="$(sha256_of "${MCP_README}")" \
    || fail "${gate}: SHA-256 of ${MCP_README} failed"
  [[ "${got}" == "${STORY_4_1_MCP_README_SHA256}" ]] \
    || fail "${gate}: ${MCP_README} SHA-256 ${got} != expected ${STORY_4_1_MCP_README_SHA256}"

  got="$(sha256_of "${GITIGNORE_PATH}")" \
    || fail "${gate}: SHA-256 of ${GITIGNORE_PATH} failed"
  [[ "${got}" == "${STORY_1_1_GITIGNORE_SHA256}" ]] \
    || fail "${gate}: ${GITIGNORE_PATH} SHA-256 ${got} != expected ${STORY_1_1_GITIGNORE_SHA256}"

  # git check-ignore must exit non-zero for the placeholders file.
  if ( cd "${PROJECT_ROOT}" && git check-ignore -v .cursor/mcp.placeholders.md >/dev/null 2>&1 ); then
    fail "${gate}: .cursor/mcp.placeholders.md is gitignored (git check-ignore returned 0)"
  fi
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
    'PLACEHOLDERS_FILE=' \
    'MCP_JSON=' \
    'MCP_README=' \
    'GITIGNORE_PATH=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'STORY_4_1_MCP_JSON_SHA256=' \
    'STORY_4_1_MCP_README_SHA256=' \
    'STORY_1_1_GITIGNORE_SHA256=' \
    'EXPECTED_PLACEHOLDER_KEYS=' \
    'EXPECTED_H2_HEADINGS=' \
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
    'EXPECTED_PASS_COUNTS='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"
  declare -F sanitize_for_banned_scan >/dev/null 2>&1 \
    || fail "${gate}: harness missing sanitize_for_banned_scan function definition"
  declare -F sha256_of >/dev/null 2>&1 \
    || fail "${gate}: harness missing sha256_of function definition"
  declare -F extract_fenced_json_blocks >/dev/null 2>&1 \
    || fail "${gate}: harness missing extract_fenced_json_blocks function definition"
}

# ------------------------------------------------------------------
# task9 — regression against eleven predecessor harnesses
#
# Pattern inherited verbatim from the Story 4.1 harness check_task9:
# iterate the predecessor list, compute each path's SHA-256 via
# `sha256_of` as a sanity-probe (the sha256 subshell invocation also
# empirically resets enough bash file-buffer state to keep the long
# predecessor-of-predecessor chain from drifting on macOS bash 3.2.57),
# then invoke `bash "${path}" all` capturing combined stdout/stderr.
# On failure, echoes the captured output to stderr and fails with the
# predecessor's basename so the reader sees which sub-chain broke.
# ------------------------------------------------------------------
check_task9() {
  local gate="task9"

  # Review-fix F6 (BMAD_REGRESSION_DEPTH guard): if this harness is
  # being invoked as a predecessor by a newer story's task9 (and that
  # story set BMAD_REGRESSION_DEPTH=1 before calling us), skip the
  # full eleven-harness recursion to prevent O(N!) nested chains and
  # the macOS bash 3.2.57 tmp/ trap race those chains can trigger.
  # Outer-level regression still runs as normal; inner-level
  # Story 4.2 invocations short-circuit here.
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

    # Review-fix F5: byte-stability anchor. SHA-256 drift = silent
    # regression; reject immediately rather than invoke.
    if ! actual_sha="$(sha256_of "${path}")"; then
      fail "${gate}: SHA-256 utility unavailable; cannot verify ${name}"
    fi
    [[ "${actual_sha}" == "${expected_sha}" ]] \
      || fail "${gate}: ${name} SHA-256 drift — expected ${expected_sha} got ${actual_sha}"

    # Defensive: ensure the Story 1.1 tmp/ probe dir exists before
    # invocation. Older predecessors create it via `mkdir -p` but
    # the nested cleanup trap can race on bash 3.2.57; pre-creating
    # here is a no-op when it already exists and eliminates the
    # "touch: tmp/story-1-1-ignore-check: No such file or directory"
    # flake documented in Story 4.2 code review F1.
    mkdir -p "${PROJECT_ROOT}/tmp" 2>/dev/null || true

    # Review-fix F1/F6: invoke with BMAD_REGRESSION_DEPTH=1 so any
    # predecessor harness that honors the guard (Story 4.1 onward)
    # short-circuits its own task9 and we run the eleven-harness
    # regression flatly instead of recursively. Retry-once on
    # transient macOS bash 3.2.57 flake.
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

  echo "task9 OK: eleven-predecessor byte-stability + regression verified (SHA-256 + ^PASS: fingerprint)" >&2
}

# Dispatcher wrapped in `main()` so bash 3.2 parses the entire function
# body up-front; avoids a file-buffer corruption bug that can surface
# when `check_task9` spawns a long chain of predecessor-harness
# subshells (inherited pattern from Story 4.1 harness).
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
