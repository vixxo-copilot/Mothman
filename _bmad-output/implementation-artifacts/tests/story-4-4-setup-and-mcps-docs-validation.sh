#!/usr/bin/env bash
set -euo pipefail

# Story 4.4 — Rewrite docs/setup.md + create docs/mcps.md — deterministic
# validation harness.
#
# Scope:
#   - Story 4.4 rewrites `docs/setup.md` (Story 1.2 stub replaced) and
#     creates `docs/mcps.md` (green-field) as the Epic 4 onboarding +
#     MCP-catalog surfaces. Seven H2 sections in setup.md; five H2
#     sections in mcps.md; sixteen-row canonical catalog table under
#     `## Catalog at a glance`. HTML-comment terminator on both docs
#     (markdown-idiomatic; reverts the Story 4.3 shell-comment form).
#   - `.cursor/mcp.json` + `.cursor/mcp.README.md` +
#     `.cursor/mcp.placeholders.md` + `.env.example` + `.gitignore` +
#     `docs/legal/license-vixxo-internal-canonical.md` remain byte-stable
#     during Story 4.4 — six SHA-256 fingerprint assertions at `task7`.
#   - Regression chain extends Story 4.3's twelve-harness chain by one
#     (adds Story 4.3 as the thirteenth predecessor). Empirical `^PASS:`
#     line-count vector `( 1 1 1 1 10 7 7 7 7 7 10 10 10 )`.
#   - Banned-term regex + Derek fixed-string probes + path-reference
#     probes + eleven-pattern secret catalog + five placeholder-form
#     probes + `${VAR}`/`$VAR` shell-expansion probe inherited verbatim
#     from Stories 4.1 / 4.2 / 4.3. Story 4.4 ADDS one new helper:
#     `extract_table_column` for GFM table column extraction.
#   - Honors `BMAD_REGRESSION_DEPTH` guard (Story 4.2 F6 inheritance):
#     nested `check_task9` invocations short-circuit.
#   - Honors `EXPECTED_PREDECESSOR_SHA256` pre-check (Story 4.2 F5
#     inheritance): byte-stability drift of any predecessor harness
#     fails the gate BEFORE invocation.
#   - HTML-comment terminator (`<!-- Why: … -->`) on both docs — the
#     idiomatic markdown metadata footer; diverges from Story 4.3's
#     shell-comment `.env.example` terminator because both Story 4.4
#     artifacts are `.md` files.
#   - Epic-4 closure: at Phase 3 review approval, Story 4.4 flips
#     `epic-4.status: in-progress → done`. Story 4.4 is the last story
#     in Epic 4.
#
# Banned-term allowlist (inherited verbatim from Story 4.1 F1):
#   The banned-term regex contains the token `personal`. Both
#   `docs/setup.md` and `docs/mcps.md` reference
#   `GITHUB_PERSONAL_ACCESS_TOKEN` in prose and in the catalog table,
#   which would case-insensitively match. `sanitize_for_banned_scan()`
#   pre-filter substitutes `GITHUB_PERSONAL_ACCESS_TOKEN` →
#   `__GH_PAT_NAME__` before scanning so the invariant holds. This
#   pre-filter is LOAD-BEARING for Story 4.4.
#
# Gates:
#   task1  baseline-audit artifact present + structured
#   task2  canonical-blueprint artifact present + structured
#   task3  docs/setup.md shape: exists, non-empty, LF-only, trailing
#          newline, first seven lines match the locked YAML frontmatter,
#          line 9 equals `# assistants-template — setup and onboarding`,
#          last non-blank line equals EXPECTED_SETUP_TERMINATOR, seven
#          H2 headings in canonical order, `npx skills add
#          vixxo-copilot/agent-skills` present, `./bin/init` present,
#          zero trailing-whitespace lines
#   task4  docs/mcps.md shape: exists, non-empty, LF-only, trailing
#          newline, first seven lines match the locked YAML frontmatter,
#          line 9 equals `# assistants-template — MCP catalog`, last
#          non-blank line equals EXPECTED_MCPS_TERMINATOR, five H2
#          headings in canonical order, catalog-table header row +
#          separator present, exactly 18 pipe-prefixed lines total,
#          sixteen server-key data rows in canonical positional order
#   task5  cross-doc consistency: extract the Status + Transport
#          columns from docs/mcps.md and assert positional equality with
#          EXPECTED_STATUS_VALUES / EXPECTED_TRANSPORT_VALUES; assert
#          `.env.example` bare-var tokens (GITHUB_PERSONAL_ACCESS_TOKEN,
#          GONG_ACCESS_KEY, GONG_ACCESS_KEY_SECRET) each appear in BOTH
#          docs; assert `vixxo-copilot/agent-skills` appears in BOTH
#          docs; assert every HTTPS-URL `# Wiring link:` from
#          `.env.example` appears in docs/mcps.md
#   task6  secret-shape + banned-term + Derek + path + placeholder-form
#          + shell-expansion scans per AC7: all probes return zero
#          matches against the sanitize_for_banned_scan()-filtered
#          concatenation of both docs
#   task7  byte-stability invariance per AC8: six SHA-256 anchors hold
#          (.cursor/mcp.json + .cursor/mcp.README.md +
#          .cursor/mcp.placeholders.md + .env.example + .gitignore +
#          docs/legal/license-vixxo-internal-canonical.md);
#          `git check-ignore .env.example` exits 1 (not ignored);
#          `git check-ignore -v .env` exits 0 with `.env` rule cited
#   task8  self-check: shebang line 1, `set -euo pipefail`, every case
#          arm present (task1..task9, all), every declared constant
#          referenced, helper functions defined (regex_self_probe,
#          sanitize_for_banned_scan, sha256_of, extract_table_column)
#   task9  regression: thirteen predecessor harnesses run in `all` mode
#          with BMAD_REGRESSION_DEPTH=1 exported; each exits 0 with
#          PASS: all; per-harness `^PASS:` line-count matches
#          EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 );
#          SHA-256 pre-check against EXPECTED_PREDECESSOR_SHA256
#   all    runs task1 -> task9 sequentially; exits 0 with exactly 10
#          `^PASS:` lines on success
#
# Tooling: POSIX-bash-3.2 compatible (no associative arrays, no
# namerefs). Uses bash, grep, awk, sed, find, tr, wc, head, tail, od,
# cut, sort, shasum -a 256 (falls back to sha256sum / openssl dgst
# -sha256), and shell built-ins. BSD-grep and GNU-grep compatible.
# Intentionally does NOT use rg, jq, yq, node, python3 (Story 4.4
# itself parses no JSON; Story 4.1 / 4.2 regression uses python3 via
# their own harnesses).

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

SETUP_MD="${PROJECT_ROOT}/docs/setup.md"
MCPS_MD="${PROJECT_ROOT}/docs/mcps.md"
MCP_JSON="${PROJECT_ROOT}/.cursor/mcp.json"
MCP_README="${PROJECT_ROOT}/.cursor/mcp.README.md"
MCP_PLACEHOLDERS="${PROJECT_ROOT}/.cursor/mcp.placeholders.md"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
GITIGNORE_PATH="${PROJECT_ROOT}/.gitignore"
LICENSE_CANONICAL="${PROJECT_ROOT}/docs/legal/license-vixxo-internal-canonical.md"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-4-4-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-4-4-canonical-blueprint.md"

# Byte-stability SHA-256 constants (captured Task 1 2026-04-21).
STORY_4_3_MCP_JSON_SHA256="d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c"
STORY_4_3_MCP_README_SHA256="4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09"
STORY_4_3_MCP_PLACEHOLDERS_SHA256="1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010"
STORY_4_3_ENV_EXAMPLE_SHA256="19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4"
STORY_1_1_GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"
STORY_1_2_LICENSE_CANONICAL_SHA256="4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc"

# Sixteen per-MCP server keys, canonical order (identical to Story 4.3).
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

# Seven H2 section names for docs/setup.md (canonical order, AC1).
EXPECTED_SETUP_H2=(
  "Prerequisites"
  "Clone and install"
  "Configure credentials (\`.env\`)"
  "Configure active MCPs"
  "Review placeholder MCPs"
  "Run the setup smoke test"
  "Troubleshooting and next steps"
)

# Five H2 section names for docs/mcps.md (canonical order, AC3).
EXPECTED_MCPS_H2=(
  "Catalog at a glance"
  "Active MCPs"
  "Placeholder MCPs"
  "Credential surface"
  "Flipping a placeholder to active"
)

# Sixteen positional-parallel Status / Transport values (AC4 locks).
EXPECTED_STATUS_VALUES=(
  active-no-env
  active
  active
  active-no-env
  active
  placeholder
  placeholder
  placeholder
  placeholder
  placeholder
  placeholder
  placeholder
  placeholder
  placeholder
  placeholder
  placeholder
)

EXPECTED_TRANSPORT_VALUES=(
  "remote URL (HTTP)"
  "local stdio (docker)"
  "local stdio (npx)"
  "local stdio (npx)"
  "local stdio (npx)"
  "local stdio (intended)"
  "local stdio (intended)"
  "remote URL (HTTP)"
  "remote URL (HTTP)"
  "remote URL (HTTP)"
  "local stdio (intended)"
  "remote URL (HTTP)"
  "local stdio (intended)"
  "remote URL (HTTP)"
  "local stdio (intended)"
  "local stdio (intended)"
)

# Catalog-table header + separator locks (AC4).
EXPECTED_TABLE_HEADER="| Server key | Status | Transport | Env vars | Wiring reference |"
EXPECTED_TABLE_SEPARATOR="| --- | --- | --- | --- | --- |"

# HTML-comment terminator locks (full-prose equality, AC1 / AC3).
EXPECTED_SETUP_TERMINATOR="<!-- Why: canonical self-serve onboarding checklist from clone through smoke-test per Epic 4 Story 4.4 AC1; cross-links .env.example (Story 4.3), .cursor/mcp.README.md (Story 4.1), .cursor/mcp.placeholders.md (Story 4.2), and docs/mcps.md (Story 4.4). -->"
EXPECTED_MCPS_TERMINATOR="<!-- Why: canonical catalog of every MCP the assistants-template ships (five active + eleven placeholder) per Epic 4 Story 4.4 AC3; cross-links .cursor/mcp.README.md (Story 4.1), .cursor/mcp.placeholders.md (Story 4.2), .env.example (Story 4.3), and docs/setup.md (Story 4.4). -->"

# Three bare env vars that must appear in BOTH docs (AC5 consistency).
EXPECTED_BARE_VARS=(
  GITHUB_PERSONAL_ACCESS_TOKEN
  GONG_ACCESS_KEY
  GONG_ACCESS_KEY_SECRET
)

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

# Thirteen predecessor harness paths (AC11). Story 4.3 is the thirteenth.
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

# Empirical `^PASS:` line-count fingerprint per predecessor in `all` mode.
# Thirteen-element positional-parallel vector.
EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 )

# SHA-256 byte-stability anchor per predecessor harness (Story 4.2 F5
# inheritance extended to thirteen).
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
  "7aa2733e3b0e93d6b35bd0d7c89645ded810ae876b10e81554d26c738d61a277"
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

# extract_table_column <file> <column_index> — scan `file` for the
# first line starting with `|`, treat it as the header row, skip the
# separator row, then emit each subsequent data row's `column_index`
# cell value (1-based). Terminates at the first blank line or first
# non-`|`-prefixed line after the table begins. Trims leading/trailing
# whitespace from each emitted cell.
extract_table_column() {
  local file="$1"
  local col="$2"
  awk -v c="${col}" '
    BEGIN { in_table = 0; row = 0 }
    /^\|/ {
      in_table = 1
      row++
      if (row <= 2) next
      # GFM rows start and end with a pipe — the number of fields
      # reported by awk -F"|" is cells + 2 (leading + trailing empty).
      n = split($0, parts, "|")
      idx = c + 1
      if (idx < 1 || idx > n) next
      cell = parts[idx]
      sub(/^[[:space:]]+/, "", cell)
      sub(/[[:space:]]+$/, "", cell)
      print cell
      next
    }
    in_table == 1 && !/^\|/ { exit }
  ' "${file}"
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

  # (f) extract_table_column fixture probe — two-row / three-column
  # locked fixture; assert cell values preserved.
  local fixture_file fixture_col2 fixture_col3
  fixture_file="$(mktemp)"
  printf '%s\n' \
    '| H1 | H2 | H3 |' \
    '| --- | --- | --- |' \
    '| alpha | beta | gamma |' \
    '| delta | epsilon | zeta |' \
    '' \
    'not a row' >"${fixture_file}"
  fixture_col2="$(extract_table_column "${fixture_file}" 2 | tr '\n' ',' | sed 's/,$//')"
  fixture_col3="$(extract_table_column "${fixture_file}" 3 | tr '\n' ',' | sed 's/,$//')"
  rm -f "${fixture_file}"
  [[ "${fixture_col2}" == "beta,epsilon" ]] \
    || fail "regex probe: extract_table_column col=2 fixture mismatch: got '${fixture_col2}'"
  [[ "${fixture_col3}" == "gamma,zeta" ]] \
    || fail "regex probe: extract_table_column col=3 fixture mismatch: got '${fixture_col3}'"
}

# ------------------------------------------------------------------
# task1 — baseline audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 4.4 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 4.4 Baseline Audit'"

  local section
  for section in \
    'Per-MCP cross-reference with .cursor/mcp.README.md' \
    'Byte-stability fingerprints' \
    'Predecessor-harness compatibility scan (thirteen harnesses)' \
    'Empirical predecessor PASS-count vector' \
    'docs/setup.md rewrite-delta audit' \
    'Placeholder-MCP wiring-link audit' \
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

  grep -Fq '# Story 4.4 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 4.4 Canonical Blueprint'"

  local required
  for required in \
    'Frontmatter lock — docs/setup.md' \
    'Frontmatter lock — docs/mcps.md' \
    'H1 lock — docs/setup.md' \
    'H1 lock — docs/mcps.md' \
    'H2 sequence lock — docs/setup.md' \
    'H2 sequence lock — docs/mcps.md' \
    'Terminator lock — docs/setup.md' \
    'Terminator lock — docs/mcps.md' \
    'Catalog-table header + separator lock' \
    'Catalog-table data-row lock' \
    'Skills-registry-reference lock' \
    'Banned-term lock (inherited verbatim from Story 4.3)' \
    'Secret-pattern catalog lock' \
    'Placeholder-form probes (inherited verbatim)' \
    'Inheritance-only note' \
    'Evidence constants for Task 5 harness'; do
    if ! grep -Fq "${required}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing required subsection: '${required}'"
    fi
  done

  local server
  for server in linear github microsoft-365 salesforce gong \
                freshdesk dynamics vixxonow vixxolink gateway zoominfo \
                hubspot aws-connect chatfpt elastic introspection; do
    if ! grep -Fq "### ${server}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing per-server data-row lock for '${server}'"
    fi
  done
}

# ------------------------------------------------------------------
# task3 — docs/setup.md shape verification
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${SETUP_MD}" "${gate}"
  require_file_nonempty "${SETUP_MD}" "${gate}"
  assert_trailing_newline "${SETUP_MD}" "${gate}"
  assert_lf_only "${SETUP_MD}" "${gate}"

  if grep -nE ' +$' "${SETUP_MD}" >/dev/null 2>&1; then
    grep -nE ' +$' "${SETUP_MD}" >&2
    fail "${gate}: ${SETUP_MD} contains trailing-whitespace lines"
  fi

  # Frontmatter — first seven lines verbatim.
  local line_1 line_2 line_3 line_4 line_5 line_6 line_7 line_9
  line_1="$(sed -n '1p' "${SETUP_MD}")"
  line_2="$(sed -n '2p' "${SETUP_MD}")"
  line_3="$(sed -n '3p' "${SETUP_MD}")"
  line_4="$(sed -n '4p' "${SETUP_MD}")"
  line_5="$(sed -n '5p' "${SETUP_MD}")"
  line_6="$(sed -n '6p' "${SETUP_MD}")"
  line_7="$(sed -n '7p' "${SETUP_MD}")"
  line_9="$(sed -n '9p' "${SETUP_MD}")"
  [[ "${line_1}" == '---' ]] \
    || fail "${gate}: setup.md line 1 != '---' (got '${line_1}')"
  [[ "${line_2}" == 'type: setup-guide' ]] \
    || fail "${gate}: setup.md line 2 mismatch (got '${line_2}')"
  [[ "${line_3}" == 'scope: work' ]] \
    || fail "${gate}: setup.md line 3 mismatch (got '${line_3}')"
  [[ "${line_4}" == 'created: 2026-04-21' ]] \
    || fail "${gate}: setup.md line 4 mismatch (got '${line_4}')"
  [[ "${line_5}" == 'updated: 2026-04-21' ]] \
    || fail "${gate}: setup.md line 5 mismatch (got '${line_5}')"
  [[ "${line_6}" == 'tags: [setup, onboarding, work]' ]] \
    || fail "${gate}: setup.md line 6 mismatch (got '${line_6}')"
  [[ "${line_7}" == '---' ]] \
    || fail "${gate}: setup.md line 7 != '---' (got '${line_7}')"
  [[ "${line_9}" == '# assistants-template — setup and onboarding' ]] \
    || fail "${gate}: setup.md line 9 H1 mismatch (got '${line_9}')"

  # Terminator — last non-blank line equals EXPECTED_SETUP_TERMINATOR.
  local last_nb
  last_nb="$(awk 'NF' "${SETUP_MD}" | tail -n 1)"
  [[ "${last_nb}" == "${EXPECTED_SETUP_TERMINATOR}" ]] \
    || fail "${gate}: setup.md terminator mismatch. got '${last_nb}'"

  # Seven H2 headings in canonical positional order.
  local heading prev_line=0 kline
  for heading in "${EXPECTED_SETUP_H2[@]}"; do
    kline="$(grep -Fxn "## ${heading}" "${SETUP_MD}" | head -n 1 | cut -d: -f1)"
    [[ -n "${kline}" ]] \
      || fail "${gate}: setup.md missing H2 '## ${heading}'"
    (( kline > prev_line )) \
      || fail "${gate}: setup.md H2 '## ${heading}' (line ${kline}) not after prior (line ${prev_line})"
    # Ensure no duplicate.
    local hit_count
    hit_count="$(grep -Fxc "## ${heading}" "${SETUP_MD}")"
    [[ "${hit_count}" == '1' ]] \
      || fail "${gate}: setup.md H2 '## ${heading}' appears ${hit_count} times (expected 1)"
    prev_line="${kline}"
  done

  # Total H2 count equals 7 (no extras).
  local total_h2
  total_h2="$(grep -c '^## ' "${SETUP_MD}")"
  [[ "${total_h2}" == '7' ]] \
    || fail "${gate}: setup.md total H2 count ${total_h2} != 7"

  # Skills-registry references.
  grep -Fq 'npx skills add vixxo-copilot/agent-skills' "${SETUP_MD}" \
    || fail "${gate}: setup.md missing 'npx skills add vixxo-copilot/agent-skills'"
  grep -Fq './bin/init' "${SETUP_MD}" \
    || fail "${gate}: setup.md missing './bin/init' forward reference"
}

# ------------------------------------------------------------------
# task4 — docs/mcps.md shape verification
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${MCPS_MD}" "${gate}"
  require_file_nonempty "${MCPS_MD}" "${gate}"
  assert_trailing_newline "${MCPS_MD}" "${gate}"
  assert_lf_only "${MCPS_MD}" "${gate}"

  if grep -nE ' +$' "${MCPS_MD}" >/dev/null 2>&1; then
    grep -nE ' +$' "${MCPS_MD}" >&2
    fail "${gate}: ${MCPS_MD} contains trailing-whitespace lines"
  fi

  local line_1 line_2 line_3 line_4 line_5 line_6 line_7 line_9
  line_1="$(sed -n '1p' "${MCPS_MD}")"
  line_2="$(sed -n '2p' "${MCPS_MD}")"
  line_3="$(sed -n '3p' "${MCPS_MD}")"
  line_4="$(sed -n '4p' "${MCPS_MD}")"
  line_5="$(sed -n '5p' "${MCPS_MD}")"
  line_6="$(sed -n '6p' "${MCPS_MD}")"
  line_7="$(sed -n '7p' "${MCPS_MD}")"
  line_9="$(sed -n '9p' "${MCPS_MD}")"
  [[ "${line_1}" == '---' ]] \
    || fail "${gate}: mcps.md line 1 != '---' (got '${line_1}')"
  [[ "${line_2}" == 'type: mcp-catalog' ]] \
    || fail "${gate}: mcps.md line 2 mismatch (got '${line_2}')"
  [[ "${line_3}" == 'scope: work' ]] \
    || fail "${gate}: mcps.md line 3 mismatch (got '${line_3}')"
  [[ "${line_4}" == 'created: 2026-04-21' ]] \
    || fail "${gate}: mcps.md line 4 mismatch (got '${line_4}')"
  [[ "${line_5}" == 'updated: 2026-04-21' ]] \
    || fail "${gate}: mcps.md line 5 mismatch (got '${line_5}')"
  [[ "${line_6}" == 'tags: [mcp, catalog, work]' ]] \
    || fail "${gate}: mcps.md line 6 mismatch (got '${line_6}')"
  [[ "${line_7}" == '---' ]] \
    || fail "${gate}: mcps.md line 7 != '---' (got '${line_7}')"
  [[ "${line_9}" == '# assistants-template — MCP catalog' ]] \
    || fail "${gate}: mcps.md line 9 H1 mismatch (got '${line_9}')"

  local last_nb
  last_nb="$(awk 'NF' "${MCPS_MD}" | tail -n 1)"
  [[ "${last_nb}" == "${EXPECTED_MCPS_TERMINATOR}" ]] \
    || fail "${gate}: mcps.md terminator mismatch. got '${last_nb}'"

  # Five H2 headings in canonical positional order.
  local heading prev_line=0 kline hit_count
  for heading in "${EXPECTED_MCPS_H2[@]}"; do
    kline="$(grep -Fxn "## ${heading}" "${MCPS_MD}" | head -n 1 | cut -d: -f1)"
    [[ -n "${kline}" ]] \
      || fail "${gate}: mcps.md missing H2 '## ${heading}'"
    (( kline > prev_line )) \
      || fail "${gate}: mcps.md H2 '## ${heading}' (line ${kline}) not after prior (line ${prev_line})"
    hit_count="$(grep -Fxc "## ${heading}" "${MCPS_MD}")"
    [[ "${hit_count}" == '1' ]] \
      || fail "${gate}: mcps.md H2 '## ${heading}' appears ${hit_count} times (expected 1)"
    prev_line="${kline}"
  done

  local total_h2
  total_h2="$(grep -c '^## ' "${MCPS_MD}")"
  [[ "${total_h2}" == '5' ]] \
    || fail "${gate}: mcps.md total H2 count ${total_h2} != 5"

  # Catalog-table header + separator present.
  grep -Fxq "${EXPECTED_TABLE_HEADER}" "${MCPS_MD}" \
    || fail "${gate}: mcps.md missing catalog-table header row"
  grep -Fxq "${EXPECTED_TABLE_SEPARATOR}" "${MCPS_MD}" \
    || fail "${gate}: mcps.md missing catalog-table separator row"

  # Exactly 18 pipe-prefixed lines (1 header + 1 separator + 16 rows).
  local pipe_count
  pipe_count="$(grep -cE '^\|' "${MCPS_MD}")"
  [[ "${pipe_count}" == '18' ]] \
    || fail "${gate}: mcps.md pipe-prefixed line count ${pipe_count} != 18"

  # Sixteen server-key data rows in canonical positional order.
  local key prev_row=0 row_line
  for key in "${EXPECTED_SECTION_KEYS[@]}"; do
    row_line="$(grep -nE "^\| ${key} \| " "${MCPS_MD}" | head -n 1 | cut -d: -f1)"
    [[ -n "${row_line}" ]] \
      || fail "${gate}: mcps.md missing catalog-table data row for '${key}'"
    (( row_line > prev_row )) \
      || fail "${gate}: mcps.md row '${key}' (line ${row_line}) not after prior (line ${prev_row})"
    prev_row="${row_line}"
  done
}

# ------------------------------------------------------------------
# task5 — cross-doc consistency
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${SETUP_MD}" "${gate}"
  require_file_exists "${MCPS_MD}" "${gate}"
  require_file_exists "${ENV_EXAMPLE}" "${gate}"

  # Status column (col=2) — positional parity with EXPECTED_STATUS_VALUES.
  local actual_status i expected got
  local -a status_lines
  while IFS= read -r line; do
    status_lines+=("${line}")
  done < <(extract_table_column "${MCPS_MD}" 2)
  [[ "${#status_lines[@]}" == '16' ]] \
    || fail "${gate}: extracted ${#status_lines[@]} Status cells, expected 16"
  for (( i=0; i<16; i++ )); do
    expected="${EXPECTED_STATUS_VALUES[$i]}"
    got="${status_lines[$i]}"
    [[ "${got}" == "${expected}" ]] \
      || fail "${gate}: Status col row $((i+1)) mismatch: got '${got}' expected '${expected}'"
  done

  # Transport column (col=3) — positional parity.
  local -a transport_lines
  while IFS= read -r line; do
    transport_lines+=("${line}")
  done < <(extract_table_column "${MCPS_MD}" 3)
  [[ "${#transport_lines[@]}" == '16' ]] \
    || fail "${gate}: extracted ${#transport_lines[@]} Transport cells, expected 16"
  for (( i=0; i<16; i++ )); do
    expected="${EXPECTED_TRANSPORT_VALUES[$i]}"
    got="${transport_lines[$i]}"
    [[ "${got}" == "${expected}" ]] \
      || fail "${gate}: Transport col row $((i+1)) mismatch: got '${got}' expected '${expected}'"
  done

  # Status-value counts — set-equality with .env.example.
  local active_count no_env_count ph_count
  active_count="$(printf '%s\n' "${status_lines[@]}" | grep -Fxc 'active' || true)"
  no_env_count="$(printf '%s\n' "${status_lines[@]}" | grep -Fxc 'active-no-env' || true)"
  ph_count="$(printf '%s\n' "${status_lines[@]}" | grep -Fxc 'placeholder' || true)"
  [[ "${active_count}" == '3' ]] \
    || fail "${gate}: 'active' status count ${active_count} != 3"
  [[ "${no_env_count}" == '2' ]] \
    || fail "${gate}: 'active-no-env' status count ${no_env_count} != 2"
  [[ "${ph_count}" == '11' ]] \
    || fail "${gate}: 'placeholder' status count ${ph_count} != 11"

  # Bare env vars present in BOTH docs.
  local var
  for var in "${EXPECTED_BARE_VARS[@]}"; do
    grep -Fq "${var}" "${SETUP_MD}" \
      || fail "${gate}: docs/setup.md missing bare var '${var}'"
    grep -Fq "${var}" "${MCPS_MD}" \
      || fail "${gate}: docs/mcps.md missing bare var '${var}'"
  done

  # Skills-registry handle present in BOTH docs.
  grep -Fq 'vixxo-copilot/agent-skills' "${SETUP_MD}" \
    || fail "${gate}: docs/setup.md missing 'vixxo-copilot/agent-skills' handle"
  grep -Fq 'vixxo-copilot/agent-skills' "${MCPS_MD}" \
    || fail "${gate}: docs/mcps.md missing 'vixxo-copilot/agent-skills' handle"

  # Introspection canonical form in mcps.md.
  grep -Fq 'github:vixxo-copilot/agent-skills' "${MCPS_MD}" \
    || fail "${gate}: docs/mcps.md missing 'github:vixxo-copilot/agent-skills' canonical form"

  # Every HTTPS-URL # Wiring link: in .env.example appears in mcps.md.
  local url
  while IFS= read -r url; do
    url="${url#\# Wiring link: }"
    [[ -n "${url}" ]] || continue
    grep -Fq "${url}" "${MCPS_MD}" \
      || fail "${gate}: docs/mcps.md missing .env.example wiring-link URL '${url}'"
  done < <(grep -E '^# Wiring link: https://' "${ENV_EXAMPLE}")
}

# ------------------------------------------------------------------
# task6 — secret / banned / Derek / path / placeholder / expansion scans
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  regex_self_probe
  require_file_exists "${SETUP_MD}" "${gate}"
  require_file_exists "${MCPS_MD}" "${gate}"

  local combined_file sanitized_file
  combined_file="$(mktemp)"
  sanitized_file="$(mktemp)"
  cat "${SETUP_MD}" "${MCPS_MD}" >"${combined_file}"
  sanitize_for_banned_scan "${combined_file}" >"${sanitized_file}"

  local pattern
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -E "${pattern}" "${sanitized_file}" >/dev/null 2>&1; then
      grep -nE "${pattern}" "${sanitized_file}" >&2 || true
      rm -f "${combined_file}" "${sanitized_file}"
      fail "${gate}: docs/setup.md+docs/mcps.md matches secret pattern: ${pattern}"
    fi
  done

  local equals_lit
  for equals_lit in "${SECRET_EQUALS_LITERALS[@]}"; do
    if grep -F "${equals_lit}" "${combined_file}" >/dev/null 2>&1; then
      rm -f "${combined_file}" "${sanitized_file}"
      fail "${gate}: docs contain banned literal '${equals_lit}'"
    fi
  done

  if grep -iE "${BANNED_TERMS_REGEX}" "${sanitized_file}" >/dev/null 2>&1; then
    grep -inE "${BANNED_TERMS_REGEX}" "${sanitized_file}" >&2 || true
    rm -f "${combined_file}" "${sanitized_file}"
    fail "${gate}: docs contain banned token (after GH PAT allowlist pre-filter)"
  fi

  local derek_token
  for derek_token in "${DEREK_FIXED_STRINGS[@]}"; do
    if grep -Fiq "${derek_token}" "${combined_file}"; then
      rm -f "${combined_file}" "${sanitized_file}"
      fail "${gate}: docs contain Derek fixed-string: '${derek_token}'"
    fi
  done

  local path_probe
  for path_probe in '/Users/' 'Public/gtd-life' '@gmail.com'; do
    if grep -Fq "${path_probe}" "${combined_file}"; then
      rm -f "${combined_file}" "${sanitized_file}"
      fail "${gate}: docs contain path-reference probe '${path_probe}'"
    fi
  done

  if grep -oE '\{\{[^}]+\}\}' "${combined_file}" >/dev/null 2>&1; then
    rm -f "${combined_file}" "${sanitized_file}"
    fail "${gate}: docs contain forbidden {{...}} template token"
  fi
  if grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}' "${combined_file}" >/dev/null 2>&1; then
    rm -f "${combined_file}" "${sanitized_file}"
    fail "${gate}: docs contain forbidden {name} single-brace placeholder"
  fi
  if grep -oE '<[A-Za-z_][A-Za-z0-9_]*>' "${combined_file}" >/dev/null 2>&1; then
    rm -f "${combined_file}" "${sanitized_file}"
    fail "${gate}: docs contain forbidden <name> angle-bracket placeholder"
  fi
  if grep -oE '%[A-Za-z_][A-Za-z0-9_]*%' "${combined_file}" >/dev/null 2>&1; then
    rm -f "${combined_file}" "${sanitized_file}"
    fail "${gate}: docs contain forbidden %name% percent placeholder"
  fi
  if grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*\}' "${combined_file}" >/dev/null 2>&1; then
    rm -f "${combined_file}" "${sanitized_file}"
    fail "${gate}: docs contain forbidden \${name} dollar-brace placeholder"
  fi

  if grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${combined_file}" >/dev/null 2>&1; then
    grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${combined_file}" >&2 || true
    rm -f "${combined_file}" "${sanitized_file}"
    fail "${gate}: docs contain \${VAR} or \$VAR expansion token"
  fi

  rm -f "${combined_file}" "${sanitized_file}"
}

# ------------------------------------------------------------------
# task7 — byte-stability invariance per AC8
# ------------------------------------------------------------------
check_task7() {
  local gate="task7"
  require_file_exists "${MCP_JSON}" "${gate}"
  require_file_exists "${MCP_README}" "${gate}"
  require_file_exists "${MCP_PLACEHOLDERS}" "${gate}"
  require_file_exists "${ENV_EXAMPLE}" "${gate}"
  require_file_exists "${GITIGNORE_PATH}" "${gate}"
  require_file_exists "${LICENSE_CANONICAL}" "${gate}"

  local got
  if ! got="$(sha256_of "${MCP_JSON}")"; then
    fail "${gate}: no SHA-256 utility available"
  fi
  [[ "${got}" == "${STORY_4_3_MCP_JSON_SHA256}" ]] \
    || fail "${gate}: ${MCP_JSON} SHA-256 ${got} != expected ${STORY_4_3_MCP_JSON_SHA256}"

  got="$(sha256_of "${MCP_README}")" \
    || fail "${gate}: SHA-256 of ${MCP_README} failed"
  [[ "${got}" == "${STORY_4_3_MCP_README_SHA256}" ]] \
    || fail "${gate}: ${MCP_README} SHA-256 ${got} != expected ${STORY_4_3_MCP_README_SHA256}"

  got="$(sha256_of "${MCP_PLACEHOLDERS}")" \
    || fail "${gate}: SHA-256 of ${MCP_PLACEHOLDERS} failed"
  [[ "${got}" == "${STORY_4_3_MCP_PLACEHOLDERS_SHA256}" ]] \
    || fail "${gate}: ${MCP_PLACEHOLDERS} SHA-256 ${got} != expected ${STORY_4_3_MCP_PLACEHOLDERS_SHA256}"

  got="$(sha256_of "${ENV_EXAMPLE}")" \
    || fail "${gate}: SHA-256 of ${ENV_EXAMPLE} failed"
  [[ "${got}" == "${STORY_4_3_ENV_EXAMPLE_SHA256}" ]] \
    || fail "${gate}: ${ENV_EXAMPLE} SHA-256 ${got} != expected ${STORY_4_3_ENV_EXAMPLE_SHA256}"

  got="$(sha256_of "${GITIGNORE_PATH}")" \
    || fail "${gate}: SHA-256 of ${GITIGNORE_PATH} failed"
  [[ "${got}" == "${STORY_1_1_GITIGNORE_SHA256}" ]] \
    || fail "${gate}: ${GITIGNORE_PATH} SHA-256 ${got} != expected ${STORY_1_1_GITIGNORE_SHA256}"

  got="$(sha256_of "${LICENSE_CANONICAL}")" \
    || fail "${gate}: SHA-256 of ${LICENSE_CANONICAL} failed"
  [[ "${got}" == "${STORY_1_2_LICENSE_CANONICAL_SHA256}" ]] \
    || fail "${gate}: ${LICENSE_CANONICAL} SHA-256 ${got} != expected ${STORY_1_2_LICENSE_CANONICAL_SHA256}"

  if ( cd "${PROJECT_ROOT}" && git check-ignore .env.example >/dev/null 2>&1 ); then
    fail "${gate}: .env.example is gitignored (git check-ignore returned 0)"
  fi

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
    'SETUP_MD=' \
    'MCPS_MD=' \
    'MCP_JSON=' \
    'MCP_README=' \
    'MCP_PLACEHOLDERS=' \
    'ENV_EXAMPLE=' \
    'GITIGNORE_PATH=' \
    'LICENSE_CANONICAL=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'STORY_4_3_MCP_JSON_SHA256=' \
    'STORY_4_3_MCP_README_SHA256=' \
    'STORY_4_3_MCP_PLACEHOLDERS_SHA256=' \
    'STORY_4_3_ENV_EXAMPLE_SHA256=' \
    'STORY_1_1_GITIGNORE_SHA256=' \
    'STORY_1_2_LICENSE_CANONICAL_SHA256=' \
    'EXPECTED_SECTION_KEYS=' \
    'EXPECTED_SETUP_H2=' \
    'EXPECTED_MCPS_H2=' \
    'EXPECTED_STATUS_VALUES=' \
    'EXPECTED_TRANSPORT_VALUES=' \
    'EXPECTED_TABLE_HEADER=' \
    'EXPECTED_TABLE_SEPARATOR=' \
    'EXPECTED_SETUP_TERMINATOR=' \
    'EXPECTED_MCPS_TERMINATOR=' \
    'EXPECTED_BARE_VARS=' \
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
  declare -F extract_table_column >/dev/null 2>&1 \
    || fail "${gate}: harness missing extract_table_column function"
}

# ------------------------------------------------------------------
# task9 — regression against thirteen predecessor harnesses
# ------------------------------------------------------------------
check_task9() {
  local gate="task9"

  # Story 4.2 F6: BMAD_REGRESSION_DEPTH guard. Short-circuit nested
  # invocations.
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

  echo "task9 OK: thirteen-predecessor byte-stability + regression verified (SHA-256 + ^PASS: fingerprint)" >&2
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
