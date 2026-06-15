#!/usr/bin/env bash
set -euo pipefail

# Story 4.3 — Write `.env.example` — deterministic validation harness.
#
# Scope:
#   - Story 4.3 creates `.env.example` at the repo root: a shell-env
#     template documenting every credential the five active MCPs
#     (linear, github, microsoft-365, salesforce, gong) and eleven
#     placeholder MCPs (freshdesk, dynamics, vixxonow, vixxolink,
#     gateway, zoominfo, hubspot, aws-connect, chatfpt, elastic,
#     introspection) can consume. Sixteen per-MCP `# --- <key> ---`
#     divider sections in canonical order (five active first, then
#     eleven placeholder) plus a five-line header banner, two banner
#     dividers (ACTIVE + PLACEHOLDER), and a `# Why: …` shell-comment
#     terminator.
#   - `.cursor/mcp.json` + `.cursor/mcp.README.md` +
#     `.cursor/mcp.placeholders.md` + `.gitignore` remain byte-stable
#     during Story 4.3 — SHA-256 fingerprint assertions at `task7`.
#   - Regression chain extends Story 4.2's eleven-harness chain by one
#     (adds Story 4.2 as the twelfth predecessor). Empirical `^PASS:`
#     line-count vector `( 1 1 1 1 10 7 7 7 7 7 10 10 )`.
#   - Banned-term regex + Derek fixed-string probes + path-reference
#     probes + eleven-pattern secret catalog + five placeholder-form
#     probes + `${VAR}`/`$VAR` shell-expansion probe inherited verbatim
#     from Stories 4.1 / 4.2. Story 4.3 ADDS one new probe family:
#     empty-RHS env-var declarations (`^[A-Z][A-Z0-9_]*=$` for bare,
#     `^# [A-Z][A-Z0-9_]*=$` for commented).
#   - Honors `BMAD_REGRESSION_DEPTH` guard (Story 4.2 F6 inheritance):
#     nested `check_task9` invocations short-circuit.
#   - Honors `EXPECTED_PREDECESSOR_SHA256` pre-check (Story 4.2 F5
#     inheritance): byte-stability drift of any predecessor harness
#     fails the gate BEFORE invocation.
#   - Shell-comment terminator (`# Why: …`) rather than HTML-comment
#     form — deliberate deviation per AC1 because `.env.example` is a
#     shell-env file and `<!-- … -->` would be treated as a literal
#     token by any shell-env parser.
#
# Banned-term allowlist (inherited verbatim from Story 4.1 F1):
#   The banned-term regex contains the token `personal`. `.env.example`
#   references `GITHUB_PERSONAL_ACCESS_TOKEN` directly (bare declaration
#   under the `github` active section), which would case-insensitively
#   match. `sanitize_for_banned_scan()` pre-filter substitutes
#   `GITHUB_PERSONAL_ACCESS_TOKEN` → `__GH_PAT_NAME__` before scanning
#   so the invariant holds. This pre-filter is LOAD-BEARING for
#   Story 4.3 (unlike Stories 4.1 / 4.2 where it was defensive-only).
#
# Gates:
#   task1  baseline-audit artifact present + structured
#   task2  canonical-blueprint artifact present + structured
#   task3  .env.example shape: exists at repo root, non-empty, LF-only,
#          trailing newline, first five lines match the locked header
#          banner, `# Why: …` terminator on last non-blank line, exactly
#          16 `# --- <key> ---` dividers in canonical order, exactly 2
#          banner dividers in canonical position, zero trailing-ws lines
#   task4  per-section metadata presence: each of the 16 sections has
#          the five required `# <Field>:` lines in order;
#          `^# status: active$` count = 3 (github, microsoft-365, gong);
#          `^# status: active-no-env$` count = 2 (linear, salesforce);
#          `^# status: placeholder$` count = 11; total `^# status:` = 16
#   task5  env-var declaration shape: `^[A-Z][A-Z0-9_]*=$` count = 3;
#          `^# [A-Z][A-Z0-9_]*=$` count = 20; bare-var set equals
#          EXPECTED_BARE_VARS; commented-var set equals
#          EXPECTED_COMMENTED_VARS; every bare `VAR=` lives under an
#          `# status: active` section; every commented `# VAR=` lives
#          under `# status: active` or `# status: placeholder`;
#          zero `${VAR}`/`$VAR` expansion tokens in the file
#   task6  secret-shape + banned-term + Derek + path + placeholder-form
#          + shell-expansion scans per AC6/AC9: all probes return zero
#          matches against sanitize_for_banned_scan() view
#   task7  byte-stability invariance per AC8: .cursor/mcp.json +
#          .cursor/mcp.README.md + .cursor/mcp.placeholders.md +
#          .gitignore SHA-256 anchors hold;
#          `git check-ignore .env.example` exits 1 (not ignored);
#          `git check-ignore -v .env` exits 0 and prints .gitignore
#          pattern reference
#   task8  self-check: shebang line 1, `set -euo pipefail`, every case
#          arm present (task1..task9, all), every declared constant
#          referenced, helper functions defined
#   task9  regression: twelve predecessor harnesses run in `all` mode
#          with BMAD_REGRESSION_DEPTH=1 exported; each exits 0 with
#          PASS: all; per-harness `^PASS:` line-count matches
#          EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 );
#          SHA-256 pre-check against EXPECTED_PREDECESSOR_SHA256
#   all    runs task1 -> task9 sequentially; exits 0 with exactly 10
#          `^PASS:` lines on success
#
# Tooling: POSIX-bash-3.2 compatible (no associative arrays, no
# namerefs). Uses bash, grep, awk, sed, find, tr, wc, head, tail, od,
# cut, sort, shasum -a 256 (falls back to sha256sum / openssl dgst
# -sha256), and shell built-ins. BSD-grep and GNU-grep compatible.
# Intentionally does NOT use rg, jq, yq, node, python3 (Story 4.3
# itself parses no JSON; Story 4.1 / 4.2 regression uses python3 via
# their own harnesses).

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
MCP_JSON="${PROJECT_ROOT}/.cursor/mcp.json"
MCP_README="${PROJECT_ROOT}/.cursor/mcp.README.md"
MCP_PLACEHOLDERS="${PROJECT_ROOT}/.cursor/mcp.placeholders.md"
GITIGNORE_PATH="${PROJECT_ROOT}/.gitignore"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-4-3-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-4-3-canonical-blueprint.md"

# Byte-stability SHA-256 constants (captured Task 1 2026-04-21 from
# on-disk Story 4.1 / 4.2 artifacts).
STORY_4_2_MCP_JSON_SHA256="d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c"
STORY_4_2_MCP_README_SHA256="4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09"
STORY_4_2_MCP_PLACEHOLDERS_SHA256="1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010"
STORY_1_1_GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"

# Sixteen per-MCP server keys, canonical order (AC2 lock). Five active
# first (mcp.json order), then eleven placeholder (mcp.placeholders.md
# order).
EXPECTED_SECTION_KEYS=(
  linear
  github
  microsoft-365
  salesforce
  gong
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

# Three bare `VAR=` tokens (AC4 lock; SCREAMING_SNAKE_CASE + empty RHS).
EXPECTED_BARE_VARS=(
  GITHUB_PERSONAL_ACCESS_TOKEN
  GONG_ACCESS_KEY
  GONG_ACCESS_KEY_SECRET
)

# Twenty commented `# VAR=` tokens (AC4 + AC5 union: two under
# microsoft-365 optional + eighteen across eleven placeholder sections).
EXPECTED_COMMENTED_VARS=(
  MS365_MCP_CLIENT_ID
  MS365_MCP_TENANT_ID
  FRESHDESK_API_KEY
  FRESHDESK_DOMAIN
  DYNAMICS_CLIENT_ID
  DYNAMICS_CLIENT_SECRET
  DYNAMICS_TENANT_ID
  VIXXONOW_API_TOKEN
  VIXXOLINK_API_TOKEN
  GATEWAY_API_TOKEN
  ZOOMINFO_USERNAME
  ZOOMINFO_PASSWORD
  HUBSPOT_ACCESS_TOKEN
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_REGION
  AWS_CONNECT_INSTANCE_ID
  CHATFPT_API_TOKEN
  ELASTIC_URL
  ELASTIC_API_KEY
)

# Five-line header banner lock (AC1). Positional: lines 1..5 of the file.
EXPECTED_HEADER_LINE_1="# .env.example — credential template for assistants-template"
EXPECTED_HEADER_LINE_2="# Copy this file to \`.env\` and fill in values for the MCPs you use."
EXPECTED_HEADER_LINE_3="# \`.env\` is gitignored (see \`.gitignore\`). \`.env.example\` is tracked (allowlist: \`!.env.example\`)."
EXPECTED_HEADER_LINE_4="# NEVER commit \`.env.example\` with real values — every RHS below is intentionally blank or commented."
EXPECTED_HEADER_LINE_5="# Sections are ordered: ACTIVE MCPs first (mcp.json order), then PLACEHOLDER MCPs (mcp.placeholders.md order)."

# Two banner divider locks (AC2).
EXPECTED_BANNER_ACTIVE="# === ACTIVE MCPs (wired in .cursor/mcp.json — see .cursor/mcp.README.md) ==="
EXPECTED_BANNER_PLACEHOLDER="# === PLACEHOLDER MCPs (not wired — see .cursor/mcp.placeholders.md) ==="

# Eleven secret-pattern regexes (inherited verbatim from Story 4.1 AC4).
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

# Four lowercase `…=` literal probes (case-sensitive grep -F).
SECRET_EQUALS_LITERALS=( 'password=' 'token=' 'secret=' 'api_key=' )

# Seventeen-token boundary-guarded banned-term regex (inherited verbatim
# from Stories 3.1 / 3.2 / 3.3 / 4.1 / 4.2). Case-insensitive via
# `grep -iE`.
BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'

# Twelve Derek defense-in-depth fixed-string probes (inherited verbatim).
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

# GitHub PAT allowlist pre-filter (inherited verbatim from Story 4.1 F1).
# LOAD-BEARING for Story 4.3 because `.env.example` references
# GITHUB_PERSONAL_ACCESS_TOKEN directly.
GH_PAT_ENV_NAME="GITHUB_PERSONAL_ACCESS_TOKEN"
GH_PAT_ALLOWLIST_PLACEHOLDER="__GH_PAT_NAME__"

# Twelve predecessor harness paths (AC11). Story 4.2 is the twelfth.
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

# Empirical `^PASS:` line-count fingerprint per predecessor in `all`
# mode (twelve-element positional-parallel vector).
EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 )

# SHA-256 byte-stability anchor per predecessor harness (Story 4.2 F5
# inheritance extended to twelve). Positional parallel to
# STORY_*_HARNESS / EXPECTED_PASS_COUNTS. check_task9 verifies each
# value BEFORE invocation; drift = silent regression, fail the gate.
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
  "ac01c393e68c41df07cc4792abab703d62d4a10d40e96b68c9ac771bd9a1a490"
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

# count_section_declarations <key> — emit two counts on stdout
# separated by whitespace: bare_var_count commented_var_count for the
# section between `# --- <key> ---` and the next `# --- ` divider (or
# EOF / terminator / banner divider).
count_section_declarations() {
  local key="$1"
  awk -v k="# --- ${key} ---" '
    $0 == k { inb = 1; next }
    inb == 1 && /^# --- / { inb = 0 }
    inb == 1 && /^# === / { inb = 0 }
    inb == 1 {
      if ($0 ~ /^[A-Z][A-Z0-9_]*=$/) bare++
      else if ($0 ~ /^# [A-Z][A-Z0-9_]*=$/) cmt++
    }
    END { printf "%d %d\n", bare+0, cmt+0 }
  ' "${ENV_EXAMPLE}"
}

# section_status_for <key> — emit the `# status: <value>` value for
# the given section key; empty string if section absent or no status
# line.
section_status_for() {
  local key="$1"
  awk -v k="# --- ${key} ---" '
    $0 == k { inb = 1; next }
    inb == 1 && /^# --- / { inb = 0 }
    inb == 1 && /^# === / { inb = 0 }
    inb == 1 && /^# status: / { sub(/^# status: /, ""); print; exit }
  ' "${ENV_EXAMPLE}"
}

# section_containing_line <line_number> — emit the section-key in whose
# body the given line number falls, or empty string if outside any
# section.
section_containing_line() {
  local lineno="$1"
  awk -v ln="${lineno}" '
    /^# --- [a-z][a-z0-9-]* ---$/ {
      match($0, /# --- [a-z][a-z0-9-]* ---/)
      cur = substr($0, 7, RLENGTH - 10)
    }
    NR == ln { print cur; exit }
  ' "${ENV_EXAMPLE}"
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

  # (f) Empty-RHS env-var declaration probes (Story 4.3 addition).
  if ! echo 'FOO=' | grep -E '^[A-Z][A-Z0-9_]*=$' >/dev/null; then
    fail "regex probe: bare VAR= positive probe missed 'FOO='"
  fi
  if echo 'FOO=bar' | grep -E '^[A-Z][A-Z0-9_]*=$' >/dev/null; then
    fail "regex probe: bare VAR= probe admitted non-empty 'FOO=bar'"
  fi
  if ! echo '# FOO=' | grep -E '^# [A-Z][A-Z0-9_]*=$' >/dev/null; then
    fail "regex probe: commented # VAR= positive probe missed '# FOO='"
  fi
  if echo '# FOO=bar' | grep -E '^# [A-Z][A-Z0-9_]*=$' >/dev/null; then
    fail "regex probe: commented # VAR= probe admitted non-empty '# FOO=bar'"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 4.3 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 4.3 Baseline Audit'"

  local section
  for section in \
    'Env-var source-of-truth cross-reference with Story 4.1 mcp.README.md' \
    'Placeholder env-var TBD locks' \
    '.gitignore allowlist re-confirmation' \
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

  grep -Fq '# Story 4.3 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 4.3 Canonical Blueprint'"

  local server
  for server in linear github microsoft-365 salesforce gong \
                freshdesk dynamics vixxonow vixxolink gateway zoominfo \
                hubspot aws-connect chatfpt elastic introspection; do
    if ! grep -Fq "### ${server}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing per-server subsection for '${server}'"
    fi
  done

  local required
  for required in \
    'Header banner lock' \
    'Terminator lock' \
    'Active/placeholder banner-divider locks' \
    'Body section order lock' \
    'Per-section template lock' \
    'Env-var declaration lock' \
    'Per-server content locks — ACTIVE' \
    'Per-server content locks — PLACEHOLDER' \
    'Banned-term lock (inherited verbatim)' \
    'Secret-pattern catalog lock (inherited verbatim)' \
    'Placeholder-form probes (inherited verbatim)' \
    'Inheritance-only note' \
    'Evidence constants for Task 5 harness'; do
    if ! grep -Fq "${required}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing required subsection: '${required}'"
    fi
  done
}

# ------------------------------------------------------------------
# task3 — .env.example shape verification
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${ENV_EXAMPLE}" "${gate}"
  require_file_nonempty "${ENV_EXAMPLE}" "${gate}"
  assert_trailing_newline "${ENV_EXAMPLE}" "${gate}"
  assert_lf_only "${ENV_EXAMPLE}" "${gate}"

  # No trailing whitespace on any line.
  if grep -nE ' +$' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    grep -nE ' +$' "${ENV_EXAMPLE}" >&2
    fail "${gate}: ${ENV_EXAMPLE} contains trailing-whitespace lines"
  fi

  # Header banner — lines 1..5 verbatim.
  local line_1 line_2 line_3 line_4 line_5
  line_1="$(sed -n '1p' "${ENV_EXAMPLE}")"
  line_2="$(sed -n '2p' "${ENV_EXAMPLE}")"
  line_3="$(sed -n '3p' "${ENV_EXAMPLE}")"
  line_4="$(sed -n '4p' "${ENV_EXAMPLE}")"
  line_5="$(sed -n '5p' "${ENV_EXAMPLE}")"
  [[ "${line_1}" == "${EXPECTED_HEADER_LINE_1}" ]] \
    || fail "${gate}: header line 1 mismatch: got '${line_1}'"
  [[ "${line_2}" == "${EXPECTED_HEADER_LINE_2}" ]] \
    || fail "${gate}: header line 2 mismatch: got '${line_2}'"
  [[ "${line_3}" == "${EXPECTED_HEADER_LINE_3}" ]] \
    || fail "${gate}: header line 3 mismatch: got '${line_3}'"
  [[ "${line_4}" == "${EXPECTED_HEADER_LINE_4}" ]] \
    || fail "${gate}: header line 4 mismatch: got '${line_4}'"
  [[ "${line_5}" == "${EXPECTED_HEADER_LINE_5}" ]] \
    || fail "${gate}: header line 5 mismatch: got '${line_5}'"

  # Terminator — last non-blank line matches `^# Why: .*$`.
  local last_nb
  last_nb="$(awk 'NF' "${ENV_EXAMPLE}" | tail -n 1)"
  case "${last_nb}" in
    '# Why: '*) ;;
    *) fail "${gate}: last non-blank line is not '# Why: …' terminator (got: ${last_nb})" ;;
  esac

  # Exactly 16 per-MCP divider lines, canonical order.
  local divider_count
  divider_count="$(grep -cE '^# --- [a-z][a-z0-9-]* ---$' "${ENV_EXAMPLE}")"
  [[ "${divider_count}" == '16' ]] \
    || fail "${gate}: divider count ${divider_count} != 16"

  local key prev_line=0 kline
  for key in "${EXPECTED_SECTION_KEYS[@]}"; do
    kline="$(grep -Fxn "# --- ${key} ---" "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
    [[ -n "${kline}" ]] \
      || fail "${gate}: missing divider '# --- ${key} ---'"
    (( kline > prev_line )) \
      || fail "${gate}: divider '# --- ${key} ---' (line ${kline}) not after prior (line ${prev_line})"
    prev_line="${kline}"
  done

  # Exactly 2 banner dividers, canonical position.
  local banner_count
  banner_count="$(grep -cE '^# === ' "${ENV_EXAMPLE}")"
  [[ "${banner_count}" == '2' ]] \
    || fail "${gate}: banner divider count ${banner_count} != 2"

  grep -Fxq "${EXPECTED_BANNER_ACTIVE}" "${ENV_EXAMPLE}" \
    || fail "${gate}: missing ACTIVE banner divider"
  grep -Fxq "${EXPECTED_BANNER_PLACEHOLDER}" "${ENV_EXAMPLE}" \
    || fail "${gate}: missing PLACEHOLDER banner divider"

  # ACTIVE banner appears BEFORE linear divider; PLACEHOLDER banner
  # appears AFTER gong section and BEFORE freshdesk divider.
  local active_banner_line placeholder_banner_line linear_line gong_line freshdesk_line
  active_banner_line="$(grep -Fxn "${EXPECTED_BANNER_ACTIVE}" "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
  placeholder_banner_line="$(grep -Fxn "${EXPECTED_BANNER_PLACEHOLDER}" "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
  linear_line="$(grep -Fxn '# --- linear ---' "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
  gong_line="$(grep -Fxn '# --- gong ---' "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
  freshdesk_line="$(grep -Fxn '# --- freshdesk ---' "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
  (( active_banner_line < linear_line )) \
    || fail "${gate}: ACTIVE banner (line ${active_banner_line}) not before linear divider (line ${linear_line})"
  (( placeholder_banner_line > gong_line )) \
    || fail "${gate}: PLACEHOLDER banner (line ${placeholder_banner_line}) not after gong divider (line ${gong_line})"
  (( placeholder_banner_line < freshdesk_line )) \
    || fail "${gate}: PLACEHOLDER banner (line ${placeholder_banner_line}) not before freshdesk divider (line ${freshdesk_line})"
}

# ------------------------------------------------------------------
# task4 — per-section metadata presence
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${ENV_EXAMPLE}" "${gate}"

  local key section_body
  local expected_fields=( '# status:' '# Purpose:' '# Transport:' '# Auth:' '# Wiring link:' )
  for key in "${EXPECTED_SECTION_KEYS[@]}"; do
    # Extract the six lines following the divider and verify metadata order.
    section_body="$(awk -v k="# --- ${key} ---" '
      $0 == k { inb = 1; lc = 0; next }
      inb == 1 && /^# --- / { inb = 0 }
      inb == 1 && /^# === / { inb = 0 }
      inb == 1 { print }
    ' "${ENV_EXAMPLE}")"

    local idx=0 field expected got
    for field in "${expected_fields[@]}"; do
      idx=$(( idx + 1 ))
      got="$(printf '%s\n' "${section_body}" | sed -n "${idx}p")"
      case "${got}" in
        "${field}"*) ;;
        *) fail "${gate}: section '${key}' metadata line ${idx} does not start with '${field}' (got: '${got}')" ;;
      esac
    done
  done

  # Status-line counts.
  local active_count no_env_count ph_count total_count
  active_count="$(grep -c '^# status: active$' "${ENV_EXAMPLE}")"
  no_env_count="$(grep -c '^# status: active-no-env$' "${ENV_EXAMPLE}")"
  ph_count="$(grep -c '^# status: placeholder$' "${ENV_EXAMPLE}")"
  total_count="$(grep -c '^# status: ' "${ENV_EXAMPLE}")"
  [[ "${active_count}" == '3' ]] \
    || fail "${gate}: '# status: active' count ${active_count} != 3"
  [[ "${no_env_count}" == '2' ]] \
    || fail "${gate}: '# status: active-no-env' count ${no_env_count} != 2"
  [[ "${ph_count}" == '11' ]] \
    || fail "${gate}: '# status: placeholder' count ${ph_count} != 11"
  [[ "${total_count}" == '16' ]] \
    || fail "${gate}: '# status:' total count ${total_count} != 16"
}

# ------------------------------------------------------------------
# task5 — env-var declaration shape + set-equality + section-location
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${ENV_EXAMPLE}" "${gate}"

  # Shape counts.
  local bare_count cmt_count
  bare_count="$(grep -cE '^[A-Z][A-Z0-9_]*=$' "${ENV_EXAMPLE}")"
  cmt_count="$(grep -cE '^# [A-Z][A-Z0-9_]*=$' "${ENV_EXAMPLE}")"
  [[ "${bare_count}" == '3' ]] \
    || fail "${gate}: bare VAR= count ${bare_count} != 3"
  [[ "${cmt_count}" == '20' ]] \
    || fail "${gate}: commented # VAR= count ${cmt_count} != 20"

  # Extracted LHS token set equality (bare).
  local actual_bare sorted_actual_bare sorted_expected_bare
  actual_bare="$(grep -oE '^[A-Z][A-Z0-9_]*=' "${ENV_EXAMPLE}" | sed 's/=$//' | sort)"
  sorted_expected_bare="$(printf '%s\n' "${EXPECTED_BARE_VARS[@]}" | sort)"
  [[ "${actual_bare}" == "${sorted_expected_bare}" ]] \
    || fail "${gate}: bare VAR set mismatch. got: ${actual_bare//$'\n'/,} expected: ${sorted_expected_bare//$'\n'/,}"

  # Extracted LHS token set equality (commented).
  local actual_cmt sorted_expected_cmt
  actual_cmt="$(grep -oE '^# [A-Z][A-Z0-9_]*=' "${ENV_EXAMPLE}" | sed 's/^# //; s/=$//' | sort)"
  sorted_expected_cmt="$(printf '%s\n' "${EXPECTED_COMMENTED_VARS[@]}" | sort)"
  [[ "${actual_cmt}" == "${sorted_expected_cmt}" ]] \
    || fail "${gate}: commented # VAR set mismatch. got: ${actual_cmt//$'\n'/,} expected: ${sorted_expected_cmt//$'\n'/,}"

  # Every bare `VAR=` line lives under an `# status: active` section.
  local var line_no status
  for var in "${EXPECTED_BARE_VARS[@]}"; do
    line_no="$(grep -nE "^${var}=$" "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
    [[ -n "${line_no}" ]] \
      || fail "${gate}: bare var '${var}=' not found in file"
    local key
    key="$(section_containing_line "${line_no}")"
    [[ -n "${key}" ]] \
      || fail "${gate}: bare var '${var}=' (line ${line_no}) not inside any section"
    status="$(section_status_for "${key}")"
    [[ "${status}" == 'active' ]] \
      || fail "${gate}: bare var '${var}=' lives under '${key}' with status '${status}', expected 'active'"
  done

  # Every commented `# VAR=` line lives under `active` or `placeholder`
  # (never `active-no-env`).
  for var in "${EXPECTED_COMMENTED_VARS[@]}"; do
    line_no="$(grep -nE "^# ${var}=$" "${ENV_EXAMPLE}" | head -n 1 | cut -d: -f1)"
    [[ -n "${line_no}" ]] \
      || fail "${gate}: commented var '# ${var}=' not found in file"
    local key2
    key2="$(section_containing_line "${line_no}")"
    [[ -n "${key2}" ]] \
      || fail "${gate}: commented var '# ${var}=' (line ${line_no}) not inside any section"
    local status2
    status2="$(section_status_for "${key2}")"
    case "${status2}" in
      active|placeholder) ;;
      *) fail "${gate}: commented var '# ${var}=' lives under '${key2}' with status '${status2}', expected active|placeholder" ;;
    esac
  done

  # ${VAR} / $VAR absence in the whole file.
  if grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${ENV_EXAMPLE}" >&2
    fail "${gate}: ${ENV_EXAMPLE} contains \${VAR} or \$VAR expansion token"
  fi

  # Defense-in-depth: any `=<non-whitespace>` after SCREAMING_SNAKE_CASE
  # LHS fails.
  if grep -nE '^(# )?[A-Z][A-Z0-9_]*=[^[:space:]]' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    grep -nE '^(# )?[A-Z][A-Z0-9_]*=[^[:space:]]' "${ENV_EXAMPLE}" >&2
    fail "${gate}: ${ENV_EXAMPLE} contains non-empty-RHS SCREAMING_SNAKE_CASE declaration"
  fi
}

# ------------------------------------------------------------------
# task6 — secret / banned / Derek / path / placeholder / expansion scans
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  regex_self_probe
  require_file_exists "${ENV_EXAMPLE}" "${gate}"

  local sanitized
  sanitized="$(sanitize_for_banned_scan "${ENV_EXAMPLE}")"

  local pattern
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if printf '%s\n' "${sanitized}" | grep -E "${pattern}" >/dev/null 2>&1; then
      printf '%s\n' "${sanitized}" | grep -nE "${pattern}" >&2 || true
      fail "${gate}: ${ENV_EXAMPLE} matches secret pattern: ${pattern}"
    fi
  done

  local equals_lit
  for equals_lit in "${SECRET_EQUALS_LITERALS[@]}"; do
    if grep -F "${equals_lit}" "${ENV_EXAMPLE}" >/dev/null 2>&1; then
      fail "${gate}: ${ENV_EXAMPLE} contains banned literal '${equals_lit}'"
    fi
  done

  if printf '%s\n' "${sanitized}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null 2>&1; then
    printf '%s\n' "${sanitized}" | grep -inE "${BANNED_TERMS_REGEX}" >&2 || true
    fail "${gate}: ${ENV_EXAMPLE} contains banned token (after GH PAT allowlist pre-filter)"
  fi

  local derek_token
  for derek_token in "${DEREK_FIXED_STRINGS[@]}"; do
    if grep -Fiq "${derek_token}" "${ENV_EXAMPLE}"; then
      fail "${gate}: ${ENV_EXAMPLE} contains Derek fixed-string: '${derek_token}'"
    fi
  done

  if grep -Fq '/Users/' "${ENV_EXAMPLE}"; then
    fail "${gate}: ${ENV_EXAMPLE} contains absolute-path fragment '/Users/'"
  fi
  if grep -Fq 'Public/gtd-life' "${ENV_EXAMPLE}"; then
    fail "${gate}: ${ENV_EXAMPLE} contains source-repo fragment 'Public/gtd-life'"
  fi
  if grep -Fq '@gmail.com' "${ENV_EXAMPLE}"; then
    fail "${gate}: ${ENV_EXAMPLE} contains personal-mailbox domain '@gmail.com'"
  fi

  if grep -oE '\{\{[^}]+\}\}' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    fail "${gate}: ${ENV_EXAMPLE} contains forbidden {{...}} template token"
  fi
  if grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    fail "${gate}: ${ENV_EXAMPLE} contains forbidden {name} single-brace placeholder"
  fi
  if grep -oE '<[A-Za-z_][A-Za-z0-9_]*>' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    fail "${gate}: ${ENV_EXAMPLE} contains forbidden <name> angle-bracket placeholder"
  fi
  if grep -oE '%[A-Za-z_][A-Za-z0-9_]*%' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    fail "${gate}: ${ENV_EXAMPLE} contains forbidden %name% percent placeholder"
  fi
  if grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*\}' "${ENV_EXAMPLE}" >/dev/null 2>&1; then
    fail "${gate}: ${ENV_EXAMPLE} contains forbidden \${name} dollar-brace placeholder"
  fi
}

# ------------------------------------------------------------------
# task7 — byte-stability invariance per AC8
# ------------------------------------------------------------------
check_task7() {
  local gate="task7"
  require_file_exists "${MCP_JSON}" "${gate}"
  require_file_exists "${MCP_README}" "${gate}"
  require_file_exists "${MCP_PLACEHOLDERS}" "${gate}"
  require_file_exists "${GITIGNORE_PATH}" "${gate}"

  local got
  if ! got="$(sha256_of "${MCP_JSON}")"; then
    fail "${gate}: no SHA-256 utility available"
  fi
  [[ "${got}" == "${STORY_4_2_MCP_JSON_SHA256}" ]] \
    || fail "${gate}: ${MCP_JSON} SHA-256 ${got} != expected ${STORY_4_2_MCP_JSON_SHA256}"

  got="$(sha256_of "${MCP_README}")" \
    || fail "${gate}: SHA-256 of ${MCP_README} failed"
  [[ "${got}" == "${STORY_4_2_MCP_README_SHA256}" ]] \
    || fail "${gate}: ${MCP_README} SHA-256 ${got} != expected ${STORY_4_2_MCP_README_SHA256}"

  got="$(sha256_of "${MCP_PLACEHOLDERS}")" \
    || fail "${gate}: SHA-256 of ${MCP_PLACEHOLDERS} failed"
  [[ "${got}" == "${STORY_4_2_MCP_PLACEHOLDERS_SHA256}" ]] \
    || fail "${gate}: ${MCP_PLACEHOLDERS} SHA-256 ${got} != expected ${STORY_4_2_MCP_PLACEHOLDERS_SHA256}"

  got="$(sha256_of "${GITIGNORE_PATH}")" \
    || fail "${gate}: SHA-256 of ${GITIGNORE_PATH} failed"
  [[ "${got}" == "${STORY_1_1_GITIGNORE_SHA256}" ]] \
    || fail "${gate}: ${GITIGNORE_PATH} SHA-256 ${got} != expected ${STORY_1_1_GITIGNORE_SHA256}"

  # `.env.example` must NOT be gitignored. Semantically: use plain
  # `git check-ignore` (without -v) to get exit 1 on negation match —
  # on git 2.50 Apple Git-155, `-v` returns exit 0 with the `!pattern`
  # printed (documented in baseline audit § `.gitignore allowlist
  # re-confirmation`). The plain form is the authoritative semantic
  # test for "is this file ignored".
  if ( cd "${PROJECT_ROOT}" && git check-ignore .env.example >/dev/null 2>&1 ); then
    fail "${gate}: .env.example is gitignored (git check-ignore returned 0)"
  fi

  # `.env` itself must remain ignored; verify via -v so we can assert
  # the matching pattern is a `.env` rule.
  local env_out env_ec=0
  env_out="$( cd "${PROJECT_ROOT}" && git check-ignore -v .env 2>&1 )" || env_ec=$?
  [[ "${env_ec}" == '0' ]] \
    || fail "${gate}: git check-ignore -v .env exited ${env_ec}, expected 0 (ignored)"
  printf '%s\n' "${env_out}" | grep -qE '\.gitignore:[0-9]+:\.env[[:space:]]' \
    || fail "${gate}: git check-ignore -v .env did not print a .gitignore:N:.env rule (got: ${env_out})"
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
    'ENV_EXAMPLE=' \
    'MCP_JSON=' \
    'MCP_README=' \
    'MCP_PLACEHOLDERS=' \
    'GITIGNORE_PATH=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'STORY_4_2_MCP_JSON_SHA256=' \
    'STORY_4_2_MCP_README_SHA256=' \
    'STORY_4_2_MCP_PLACEHOLDERS_SHA256=' \
    'STORY_1_1_GITIGNORE_SHA256=' \
    'EXPECTED_SECTION_KEYS=' \
    'EXPECTED_BARE_VARS=' \
    'EXPECTED_COMMENTED_VARS=' \
    'EXPECTED_HEADER_LINE_1=' \
    'EXPECTED_HEADER_LINE_2=' \
    'EXPECTED_HEADER_LINE_3=' \
    'EXPECTED_HEADER_LINE_4=' \
    'EXPECTED_HEADER_LINE_5=' \
    'EXPECTED_BANNER_ACTIVE=' \
    'EXPECTED_BANNER_PLACEHOLDER=' \
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
    'EXPECTED_PASS_COUNTS=' \
    'EXPECTED_PREDECESSOR_SHA256='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function"
  declare -F sanitize_for_banned_scan >/dev/null 2>&1 \
    || fail "${gate}: harness missing sanitize_for_banned_scan function"
  declare -F sha256_of >/dev/null 2>&1 \
    || fail "${gate}: harness missing sha256_of function"
  declare -F count_section_declarations >/dev/null 2>&1 \
    || fail "${gate}: harness missing count_section_declarations function"
}

# ------------------------------------------------------------------
# task9 — regression against twelve predecessor harnesses
# ------------------------------------------------------------------
check_task9() {
  local gate="task9"

  # Story 4.2 F6: BMAD_REGRESSION_DEPTH guard. Short-circuit nested
  # invocations (outer-level still runs full twelve-harness regression;
  # inner-level invocations from a future newer story short-circuit).
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

    # Story 4.2 F5 inheritance: SHA-256 pre-check.
    if ! actual_sha="$(sha256_of "${path}")"; then
      fail "${gate}: SHA-256 utility unavailable; cannot verify ${name}"
    fi
    [[ "${actual_sha}" == "${expected_sha}" ]] \
      || fail "${gate}: ${name} SHA-256 drift — expected ${expected_sha} got ${actual_sha}"

    # Defensive tmp/ pre-creation (Story 4.2 F1 inheritance).
    mkdir -p "${PROJECT_ROOT}/tmp" 2>/dev/null || true

    # Story 4.2 F1 inheritance: retry-up-to-3 on macOS bash 3.2.57
    # transient flake. Invoke with BMAD_REGRESSION_DEPTH=1 exported so
    # any predecessor that honors the guard (Stories 4.1 + 4.2)
    # short-circuits its own task9.
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

  echo "task9 OK: twelve-predecessor byte-stability + regression verified (SHA-256 + ^PASS: fingerprint)" >&2
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
