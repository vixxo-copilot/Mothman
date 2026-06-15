#!/usr/bin/env bash
set -euo pipefail

# Story 4.1 — Write `.cursor/mcp.json` with active Vixxo MCPs —
# deterministic validation harness.
#
# Scope:
#   - Story 4.1 creates `.cursor/mcp.json` (strict JSON, five active MCPs —
#     linear, github, microsoft-365, salesforce, gong — in canonical order,
#     zero `env` blocks, zero `${VAR}` tokens) and a companion
#     `.cursor/mcp.README.md` documenting each server. Strict JSON forbids
#     comments so documentation lives in the README; `env` blocks are
#     intentionally absent because Cursor's 2026 parser does NOT expand
#     `${VAR}` inside them (forum 79296 / 79639).
#   - Regression chain extends Story 3.3's nine-harness chain by one
#     (adds Story 3.3 as the tenth predecessor) — ten prior harnesses
#     total (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 /
#     3.2 / 3.3). Empirical `^PASS:` line-count vector:
#     ( 1 1 1 1 10 7 7 7 7 7 ) — captured 2026-04-21.
#   - Story 4.2 placeholder convention locked in the blueprint + README:
#     placeholders live in `.cursor/mcp.placeholders.md` (separate markdown
#     companion), NOT as commented-out JSON inside `.cursor/mcp.json`.
#
# Banned-term allowlist (F1 codification, Story 4.1):
#   The AC7 boundary-guarded banned-term regex contains the token
#   `personal`. GitHub's canonical env var name `GITHUB_PERSONAL_ACCESS_TOKEN`
#   appears literally in both files (required by AC3 for the github Docker
#   `-e NAME` bare-form). The harness therefore runs the banned-term regex
#   against a pre-filtered view of each file that replaces
#   `GITHUB_PERSONAL_ACCESS_TOKEN` with the neutral token `__GH_PAT_NAME__`
#   before scanning. The canonical env-var name is the only legitimate
#   `PERSONAL` collision; all other `personal` hits remain caught.
#
# Gates:
#   task1  baseline-audit artifact present + structured
#   task2  canonical-blueprint artifact present + structured
#   task3  .cursor/mcp.json shape: exists, non-empty, LF-only, trailing
#          newline, parses via python3 -m json.tool, single top-level key
#          `mcpServers`, exactly five server keys in canonical order,
#          each value is an object, each value's key set is a subset of
#          {command, args, env, url, headers}, zero env blocks, zero
#          ${VAR} / $VAR substrings, no JS-style comments, no trailing
#          commas.
#   task4  per-server shape locks: Linear URL literal; GitHub docker args
#          six-element literal; M365 npx args two-element literal;
#          Salesforce npx args seven-element literal (includes --orgs
#          DEFAULT_TARGET_ORG --toolsets orgs,metadata,data,users); Gong
#          npx args two-element literal.
#   task5  secret-shape + deny-list scan: eleven secret-pattern regexes
#          against both files; zero password=/token=/secret=/api_key=
#          literals; zero ${VAR} / $VAR substrings; zero deny-list
#          server keys under `mcpServers`.
#   task6  README shape: exists, frontmatter first three bytes `---`,
#          frontmatter key order (type, scope, created, updated, tags),
#          body heading order (H1 then five H2s then env-handling H2
#          then forward-references H2), five required `**Field:**` lines
#          per server H2 section, banned-term regex + Derek fixed-string
#          probes yield zero matches (with GH PAT-name allowlist pre-filter),
#          `{{...}}` / angle / percent / dollar-brace placeholder probes
#          yield zero matches, `<!-- Why: ... -->` terminator on last
#          non-blank line.
#   task7  gitignore behavior: git check-ignore -v returns non-zero for
#          both files; .gitignore byte-stable (SHA-256 matches Story 1.1
#          F1-patch handoff fingerprint).
#   task8  self-check: shebang on line 1, `set -euo pipefail`, every case
#          arm present (task1..task9, all), every declared constant
#          referenced, regex_self_probe function exists via `declare -F`.
#   task9  regression: ten predecessor harnesses run in `all` mode; each
#          exits 0; each emits the expected `^PASS:` line-count vector.
#   all    runs task1 -> task9 sequentially; exits 0 with exactly 10
#          `^PASS:` lines on success.
#
# Tooling: POSIX-bash-3.2 compatible (no associative arrays, no namerefs).
# Uses bash, grep, awk, sed, find, tr, wc, head, tail, od, cut, sort,
# python3 -m json.tool, and shell built-ins. BSD-grep and GNU-grep
# compatible. Intentionally does NOT use rg, jq, yq, node — keyset /
# value assertions use `python3 -c '...'` one-liners.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

MCP_JSON="${PROJECT_ROOT}/.cursor/mcp.json"
MCP_README="${PROJECT_ROOT}/.cursor/mcp.README.md"
GITIGNORE_PATH="${PROJECT_ROOT}/.gitignore"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-4-1-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-4-1-canonical-blueprint.md"

# Story 1.1 F1-patch .gitignore fingerprint — invariant for Story 4.1.
GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"

# Canonical server keys in file order (AC2).
EXPECTED_SERVER_KEYS=( linear github microsoft-365 salesforce gong )

# AC2 deny-list — Story 4.2 placeholders + speculative accidental keys
# that must NOT appear under `mcpServers`.
DENY_LIST_SERVER_KEYS=(
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
  agent-skills
  slack
  notion
  gmail
  google-calendar
  obsidian
  linkedin
)

# Per-server shape literal locks (AC3 / AC4 blueprint) — each element is
# a canonical literal substring that MUST appear verbatim in the JSON
# (validated positionally via python3 assertions). Separate arrays to
# preserve POSIX-bash 3.2 compatibility.
LINEAR_URL_LITERAL="https://mcp.linear.app/mcp"
GITHUB_COMMAND_LITERAL="docker"
GITHUB_ARGS=( run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server )
M365_COMMAND_LITERAL="npx"
M365_ARGS=( -y '@softeria/ms-365-mcp-server@latest' )
SALESFORCE_COMMAND_LITERAL="npx"
SALESFORCE_ARGS=( -y '@salesforce/mcp@latest' --orgs DEFAULT_TARGET_ORG --toolsets 'orgs,metadata,data,users' )
GONG_COMMAND_LITERAL="npx"
GONG_ARGS=( -y 'github:kenazk/gong-mcp' )

# Eleven secret-pattern regexes (AC4). Case-sensitive. Applied to both
# MCP_JSON and MCP_README. Zero matches expected per pattern per file.
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

# Literal key=value substrings banned from either file (AC4 defense-in-depth).
SECRET_EQUALS_LITERALS=( 'password=' 'token=' 'secret=' 'api_key=' )

# 17-token boundary-guarded banned-term regex (inherited verbatim from
# Stories 3.1 / 3.2 / 3.3 Phase-4 lock). Case-insensitive via `grep -iE`.
# Zero new tokens; zero tokens removed.
BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'

# Twelve Derek defense-in-depth fixed-string probes (AC7). Applied to
# both files. Zero hits expected.
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

# F1 codification — the GitHub canonical env-var name contains the
# `personal` banned-term token as a substring (`_PERSONAL_`). It is the
# only legitimate collision in Story 4.1 content. The banned-term scan
# pre-filters this literal before applying the regex. Any other use of
# `personal` / `PERSONAL` remains caught.
GH_PAT_ENV_NAME="GITHUB_PERSONAL_ACCESS_TOKEN"
GH_PAT_ALLOWLIST_PLACEHOLDER="__GH_PAT_NAME__"

# Ten predecessor harnesses (AC10).
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

# Empirical `^PASS:` line-count fingerprint per predecessor harness in
# `all` mode, measured 2026-04-21. Positional parallel to the ten
# STORY_*_HARNESS constants above.
EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )

# SHA-256 byte-stability fingerprint per predecessor harness (AC10
# F3 review fix, 2026-04-21). Positional parallel to the ten
# STORY_*_HARNESS constants above. `check_task9` verifies each harness's
# on-disk SHA-256 against this constant before invocation; any drift
# triggers a hard fail. Refresh these values only when a story legitimately
# extends a predecessor harness (F1-codified integration fix) and
# re-records the new SHA here.
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

# Sanitize a file's contents by replacing the GitHub canonical PAT env
# var name with a neutral token, so the banned-term regex can scan the
# residue without colliding on `_PERSONAL_`. All other content passes
# through untouched. Emits sanitized content to stdout.
sanitize_for_banned_scan() {
  local path="$1"
  sed -E "s/${GH_PAT_ENV_NAME}/${GH_PAT_ALLOWLIST_PLACEHOLDER}/g" "${path}"
}

# Compute SHA-256 of a file on stdout (portable across macOS BSD /
# Linux GNU / environments with shasum or openssl). Prints the 64-char
# lowercase hex digest with NO trailing whitespace. Returns 1 if no
# SHA-256 utility is available.
compute_sha256() {
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

  # (d) GH_PAT allowlist pre-filter behavioural probe: raw string trips
  #     banned-term regex; sanitized string does not.
  if ! echo "GITHUB_PERSONAL_ACCESS_TOKEN" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term regex failed to trip on raw GITHUB_PERSONAL_ACCESS_TOKEN (sanity check)"
  fi
  local sanitized
  sanitized="$(echo "GITHUB_PERSONAL_ACCESS_TOKEN" | sed -E "s/${GH_PAT_ENV_NAME}/${GH_PAT_ALLOWLIST_PLACEHOLDER}/g")"
  if echo "${sanitized}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: allowlist pre-filter failed — sanitized GH PAT still trips banned-term regex"
  fi

  # (e) SHA-256 utility probe (F3 review fix): compute a SHA for a tiny
  #     fixture, confirm the value is 64 lowercase hex chars and matches
  #     a precomputed expected; corrupt the fixture and assert the SHA
  #     changes. Guarantees check_task9's byte-stability check has a
  #     working digest backend.
  local tmp_sha_dir tmp_sha_file sha_got sha_expected sha_corrupted
  tmp_sha_dir="$(mktemp -d 2>/dev/null || mktemp -d -t sha-probe)"
  tmp_sha_file="${tmp_sha_dir}/probe.txt"
  printf 'abc' >"${tmp_sha_file}"
  sha_expected="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
  if ! sha_got="$(compute_sha256 "${tmp_sha_file}")"; then
    rm -rf "${tmp_sha_dir}"
    fail "regex probe: SHA-256 utility unavailable (shasum / sha256sum / openssl required for check_task9 byte-stability)"
  fi
  if [[ "${sha_got}" != "${sha_expected}" ]]; then
    rm -rf "${tmp_sha_dir}"
    fail "regex probe: SHA-256 utility produced ${sha_got} for 'abc', expected ${sha_expected}"
  fi
  printf 'abd' >"${tmp_sha_file}"
  sha_corrupted="$(compute_sha256 "${tmp_sha_file}")"
  rm -rf "${tmp_sha_dir}"
  if [[ "${sha_corrupted}" == "${sha_expected}" ]]; then
    fail "regex probe: SHA-256 did not change after fixture corruption (digest backend broken)"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 4.1 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 4.1 Baseline Audit'"

  local section
  for section in \
    'Cursor mcp.json 2026 schema' \
    'Per-server canonical config' \
    'Env-var handling decision' \
    'Secret-pattern regex set' \
    'Gitignore invariance' \
    'Predecessor-harness compatibility scan' \
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

  grep -Fq '# Story 4.1 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 4.1 Canonical Blueprint'"

  local server
  for server in linear github microsoft-365 salesforce gong; do
    if ! grep -Fq "Blueprint — \`${server}\`" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing per-server section for '${server}'"
    fi
  done

  local required
  for required in \
    'Env Variable Handling Convention' \
    'Forward References' \
    'Story 4.2 Placeholder Convention' \
    'Banned-term lock' \
    'Secret-pattern catalog lock' \
    'Forbidden-form lock'; do
    if ! grep -Fq "${required}" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing required subsection: '${required}'"
    fi
  done
}

# ------------------------------------------------------------------
# task3 — .cursor/mcp.json shape verification
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${MCP_JSON}" "${gate}"
  require_file_nonempty "${MCP_JSON}" "${gate}"
  assert_trailing_newline "${MCP_JSON}" "${gate}"
  assert_lf_only "${MCP_JSON}" "${gate}"

  # Strict-JSON parse (Python). Node assertion deferred to task-handoff
  # evidence block — python3 is the harness's declared parser.
  if ! python3 -m json.tool "${MCP_JSON}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_JSON} fails python3 -m json.tool strict-JSON parse"
  fi

  # No JS-style comments; no trailing commas.
  if grep -nE '^[[:space:]]*//|/\*|\*/' "${MCP_JSON}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_JSON} contains JS-style comment syntax"
  fi
  if grep -nE ',[[:space:]]*[}\]]' "${MCP_JSON}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_JSON} contains trailing commas"
  fi

  # Single top-level key `mcpServers` mapping to an object; exactly five
  # server keys in canonical order; each value is an object; each value's
  # key set is a subset of {command, args, env, url, headers}; zero env
  # blocks; zero ${VAR} / $VAR tokens.
  local expected_order
  expected_order="$(printf '%s\n' "${EXPECTED_SERVER_KEYS[@]}")"
  if ! python3 - "${MCP_JSON}" "${expected_order}" <<'PY' >/dev/null
import json, sys
path, expected_block = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as fh:
    d = json.load(fh)
assert isinstance(d, dict), f"root must be object, got {type(d).__name__}"
assert list(d.keys()) == ["mcpServers"], f"top-level keys must be ['mcpServers'], got {list(d.keys())}"
servers = d["mcpServers"]
assert isinstance(servers, dict), "mcpServers must be an object"
expected_keys = [k for k in expected_block.splitlines() if k]
actual_keys = list(servers.keys())
assert actual_keys == expected_keys, f"server keys {actual_keys} != canonical {expected_keys}"
allowed = {"command", "args", "env", "url", "headers"}
for k, v in servers.items():
    assert isinstance(v, dict), f"{k} value must be object"
    assert "env" not in v, f"{k} contains forbidden env block"
    unknown = set(v.keys()) - allowed
    assert not unknown, f"{k} has unknown keys {unknown}"
    if "command" in v:
        assert "url" not in v, f"{k} mixes command+url"
        assert isinstance(v.get("command"), str), f"{k}.command must be string"
        assert isinstance(v.get("args"), list), f"{k}.args must be array"
        for i, a in enumerate(v["args"]):
            assert isinstance(a, str), f"{k}.args[{i}] must be string"
    elif "url" in v:
        assert isinstance(v.get("url"), str), f"{k}.url must be string"
    else:
        raise AssertionError(f"{k} has neither command nor url")
PY
  then
    fail "${gate}: JSON structural assertions failed for ${MCP_JSON}"
  fi

  # ${VAR} / $VAR substring scan.
  if grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${MCP_JSON}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_JSON} contains \${VAR} or \$VAR expansion token (Cursor does not expand)"
  fi
}

# ------------------------------------------------------------------
# task4 — per-server shape literal locks
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${MCP_JSON}" "${gate}"

  # Pass the expected server arg literals to Python via env-like positional
  # args; Python loads the JSON and asserts deep equality.
  local linear_url github_cmd github_args m365_cmd m365_args sf_cmd sf_args gong_cmd gong_args
  linear_url="${LINEAR_URL_LITERAL}"
  github_cmd="${GITHUB_COMMAND_LITERAL}"
  github_args="$(printf '%s\n' "${GITHUB_ARGS[@]}")"
  m365_cmd="${M365_COMMAND_LITERAL}"
  m365_args="$(printf '%s\n' "${M365_ARGS[@]}")"
  sf_cmd="${SALESFORCE_COMMAND_LITERAL}"
  sf_args="$(printf '%s\n' "${SALESFORCE_ARGS[@]}")"
  gong_cmd="${GONG_COMMAND_LITERAL}"
  gong_args="$(printf '%s\n' "${GONG_ARGS[@]}")"

  if ! python3 - "${MCP_JSON}" \
      "${linear_url}" \
      "${github_cmd}" "${github_args}" \
      "${m365_cmd}" "${m365_args}" \
      "${sf_cmd}" "${sf_args}" \
      "${gong_cmd}" "${gong_args}" <<'PY' >/dev/null
import json, sys
path = sys.argv[1]
linear_url = sys.argv[2]
github_cmd, github_args_block = sys.argv[3], sys.argv[4]
m365_cmd, m365_args_block = sys.argv[5], sys.argv[6]
sf_cmd, sf_args_block = sys.argv[7], sys.argv[8]
gong_cmd, gong_args_block = sys.argv[9], sys.argv[10]
def split(b): return [l for l in b.splitlines() if l != ""] if b else []
with open(path, 'r', encoding='utf-8') as fh:
    d = json.load(fh)
s = d["mcpServers"]
# Linear
assert s["linear"] == {"url": linear_url}, f"linear shape != {{'url': {linear_url!r}}} (got {s['linear']})"
# GitHub
assert s["github"].get("command") == github_cmd, f"github.command != {github_cmd!r}"
expected_gh_args = split(github_args_block)
assert s["github"].get("args") == expected_gh_args, f"github.args != {expected_gh_args} (got {s['github'].get('args')})"
# Microsoft 365
assert s["microsoft-365"].get("command") == m365_cmd
expected_m365_args = split(m365_args_block)
assert s["microsoft-365"].get("args") == expected_m365_args, f"microsoft-365.args != {expected_m365_args} (got {s['microsoft-365'].get('args')})"
# Salesforce
assert s["salesforce"].get("command") == sf_cmd
expected_sf_args = split(sf_args_block)
assert s["salesforce"].get("args") == expected_sf_args, f"salesforce.args != {expected_sf_args} (got {s['salesforce'].get('args')})"
# Gong
assert s["gong"].get("command") == gong_cmd
expected_gong_args = split(gong_args_block)
assert s["gong"].get("args") == expected_gong_args, f"gong.args != {expected_gong_args} (got {s['gong'].get('args')})"
PY
  then
    fail "${gate}: per-server literal locks failed for ${MCP_JSON}"
  fi
}

# ------------------------------------------------------------------
# task5 — secret-shape scan + deny-list scan
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${MCP_JSON}" "${gate}"
  require_file_exists "${MCP_README}" "${gate}"

  # AC4 scope: the eleven secret-pattern regexes and the four
  # password=/token=/secret=/api_key= literal-substring probes apply to
  # `.cursor/mcp.json` ONLY. The README legitimately documents secret
  # pattern examples (e.g. `ghp_` prefix, `Bearer <token>` shape), which
  # would false-positive the scanner. Banned-term + Derek fixed-string
  # scans in task6 still cover both files.
  local pattern
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -E "${pattern}" "${MCP_JSON}" >/dev/null 2>&1; then
      grep -nE "${pattern}" "${MCP_JSON}" >&2 || true
      fail "${gate}: ${MCP_JSON} matches secret pattern: ${pattern}"
    fi
  done
  local equals_lit
  for equals_lit in "${SECRET_EQUALS_LITERALS[@]}"; do
    if grep -F "${equals_lit}" "${MCP_JSON}" >/dev/null 2>&1; then
      fail "${gate}: ${MCP_JSON} contains banned literal substring '${equals_lit}'"
    fi
  done
  # ${VAR} / $VAR expansion tokens are banned in the JSON file only; the
  # README legitimately documents the non-expansion pitfall.
  if grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' "${MCP_JSON}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_JSON} contains \${VAR} / \$VAR expansion token (not permitted in JSON)"
  fi

  # Deny-list scan — no pending/placeholder server keys under mcpServers.
  local deny_block
  deny_block="$(printf '%s\n' "${DENY_LIST_SERVER_KEYS[@]}")"
  if ! python3 - "${MCP_JSON}" "${deny_block}" <<'PY' >/dev/null
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    d = json.load(fh)
deny = {k for k in sys.argv[2].splitlines() if k}
present = set(d["mcpServers"].keys()) & deny
assert not present, f"deny-listed server keys present: {sorted(present)}"
PY
  then
    fail "${gate}: deny-list server key check failed"
  fi
}

# ------------------------------------------------------------------
# task6 — .cursor/mcp.README.md shape verification
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  regex_self_probe

  require_file_exists "${MCP_README}" "${gate}"
  require_file_nonempty "${MCP_README}" "${gate}"
  assert_trailing_newline "${MCP_README}" "${gate}"
  assert_lf_only "${MCP_README}" "${gate}"

  # Frontmatter first three bytes.
  local first3
  first3="$(head -c 3 "${MCP_README}" | tr -d '[:space:]')"
  [[ "${first3}" == '---' ]] \
    || fail "${gate}: ${MCP_README} first 3 bytes are '${first3}', expected '---'"

  # Frontmatter key order.
  local fm_keys expected_fm_keys
  fm_keys="$(awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}' "${MCP_README}" \
    | grep -oE '^[a-zA-Z_][a-zA-Z0-9_]*:' \
    | sed 's/:$//' | tr '\n' ' ')"
  expected_fm_keys="type scope created updated tags "
  [[ "${fm_keys}" == "${expected_fm_keys}" ]] \
    || fail "${gate}: ${MCP_README} frontmatter key order is '${fm_keys}', expected '${expected_fm_keys}'"

  # Frontmatter literal values.
  local fm_body
  fm_body="$(awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}' "${MCP_README}")"
  printf '%s\n' "${fm_body}" | grep -Fxq 'type: mcp-readme' \
    || fail "${gate}: ${MCP_README} frontmatter missing 'type: mcp-readme'"
  printf '%s\n' "${fm_body}" | grep -Fxq 'scope: work' \
    || fail "${gate}: ${MCP_README} frontmatter missing 'scope: work'"
  printf '%s\n' "${fm_body}" | grep -Fxq 'tags: [mcp, work]' \
    || fail "${gate}: ${MCP_README} frontmatter missing 'tags: [mcp, work]'"

  # Body heading ordering (H1 + five H2s + env-handling H2 + forward-refs H2).
  local headings=(
    '# Active MCPs (.cursor/mcp.json)'
    '## Linear'
    '## GitHub'
    '## Microsoft 365'
    '## Salesforce'
    '## Gong'
    '## Env Variable Handling Convention'
    '## Forward References'
  )
  local heading prev_line=0 hline
  for heading in "${headings[@]}"; do
    hline="$(grep -Fxn "${heading}" "${MCP_README}" | head -n 1 | cut -d: -f1)"
    [[ -n "${hline}" ]] \
      || fail "${gate}: ${MCP_README} missing body heading: '${heading}'"
    (( hline > prev_line )) \
      || fail "${gate}: ${MCP_README} heading '${heading}' (line ${hline}) not after prior heading (line ${prev_line})"
    prev_line="${hline}"
  done

  # Per-server H2 section must contain the five required `**Field:**`
  # marker lines: Purpose, Transport, Auth, Required env vars, Wiring link.
  local server_h2 fields field
  local field_markers=(
    '**Purpose:**'
    '**Transport:**'
    '**Auth:**'
    '**Required env vars:**'
    '**Wiring link:**'
  )
  for server_h2 in '## Linear' '## GitHub' '## Microsoft 365' '## Salesforce' '## Gong'; do
    local start_line end_line
    start_line="$(grep -Fxn "${server_h2}" "${MCP_README}" | head -n 1 | cut -d: -f1)"
    # Next H2 after this one delimits the section body.
    end_line="$(awk -v s="${start_line}" 'NR>s && /^## /{print NR; exit}' "${MCP_README}")"
    [[ -n "${end_line}" ]] || end_line="$(wc -l <"${MCP_README}" | tr -d '[:space:]')"
    local section_body
    section_body="$(awk -v s="${start_line}" -v e="${end_line}" 'NR>=s && NR<e' "${MCP_README}")"
    for field in "${field_markers[@]}"; do
      if ! printf '%s\n' "${section_body}" | grep -Fq "${field}"; then
        fail "${gate}: ${MCP_README} section '${server_h2}' missing required field marker '${field}'"
      fi
    done
  done

  # Banned-term regex + Derek fixed-string probes on sanitized content.
  local sanitized
  sanitized="$(sanitize_for_banned_scan "${MCP_README}")"
  if printf '%s\n' "${sanitized}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null 2>&1; then
    printf '%s\n' "${sanitized}" | grep -inE "${BANNED_TERMS_REGEX}" >&2 || true
    fail "${gate}: ${MCP_README} contains banned token (after GH PAT allowlist pre-filter)"
  fi
  sanitized="$(sanitize_for_banned_scan "${MCP_JSON}")"
  if printf '%s\n' "${sanitized}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null 2>&1; then
    printf '%s\n' "${sanitized}" | grep -inE "${BANNED_TERMS_REGEX}" >&2 || true
    fail "${gate}: ${MCP_JSON} contains banned token (after GH PAT allowlist pre-filter)"
  fi

  local derek_token f
  for f in "${MCP_JSON}" "${MCP_README}"; do
    for derek_token in "${DEREK_FIXED_STRINGS[@]}"; do
      if grep -Fiq "${derek_token}" "${f}"; then
        fail "${gate}: ${f} contains Derek fixed-string token: '${derek_token}'"
      fi
    done
    if grep -Fq '/Users/' "${f}"; then
      fail "${gate}: ${f} contains absolute-path fragment '/Users/'"
    fi
    if grep -Fq 'Public/gtd-life' "${f}"; then
      fail "${gate}: ${f} contains source-repo fragment 'Public/gtd-life'"
    fi
    if grep -Fq '@gmail.com' "${f}"; then
      fail "${gate}: ${f} contains personal-mailbox domain '@gmail.com'"
    fi
  done

  # Placeholder-form probes against the README (AC7 — README is prose).
  if grep -oE '\{\{[^}]+\}\}' "${MCP_README}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_README} contains forbidden {{...}} template token"
  fi
  if grep -oE '<[A-Za-z_][A-Za-z0-9_]*>' "${MCP_README}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_README} contains forbidden <name> angle-bracket placeholder"
  fi
  if grep -oE '%[A-Za-z_][A-Za-z0-9_]*%' "${MCP_README}" >/dev/null 2>&1; then
    fail "${gate}: ${MCP_README} contains forbidden %name% percent placeholder"
  fi

  # `<!-- Why: ... -->` terminator on last non-blank line.
  local last_nb
  last_nb="$(awk 'NF' "${MCP_README}" | tail -n 1)"
  case "${last_nb}" in
    '<!-- Why: '*'-->') ;;
    *) fail "${gate}: ${MCP_README} last non-blank line is not the '<!-- Why: ... -->' terminator (got: ${last_nb})" ;;
  esac
}

# ------------------------------------------------------------------
# task7 — gitignore behavior + byte-stability
# ------------------------------------------------------------------
check_task7() {
  local gate="task7"
  require_file_exists "${GITIGNORE_PATH}" "${gate}"

  # `git check-ignore -v` must exit non-zero for both files (NOT ignored).
  ( cd "${PROJECT_ROOT}" && git check-ignore -v .cursor/mcp.json >/dev/null 2>&1 ) \
    && fail "${gate}: .cursor/mcp.json is gitignored (git check-ignore returned 0)"
  ( cd "${PROJECT_ROOT}" && git check-ignore -v .cursor/mcp.README.md >/dev/null 2>&1 ) \
    && fail "${gate}: .cursor/mcp.README.md is gitignored (git check-ignore returned 0)"

  # .gitignore byte-stable vs Story 1.1 F1-patch handoff fingerprint.
  local gi_sha=""
  if command -v shasum >/dev/null 2>&1; then
    gi_sha="$(shasum -a 256 "${GITIGNORE_PATH}" | awk '{print $1}')"
  elif command -v openssl >/dev/null 2>&1; then
    gi_sha="$(openssl dgst -sha256 "${GITIGNORE_PATH}" | awk '{print $NF}')"
  fi
  if [[ -n "${gi_sha}" ]]; then
    [[ "${gi_sha}" == "${GITIGNORE_SHA256}" ]] \
      || fail "${gate}: .gitignore SHA-256 ${gi_sha} != expected ${GITIGNORE_SHA256} (Story 1.1 F1-patch fingerprint drift)"
  else
    echo "${gate}: WARN: neither shasum nor openssl available; .gitignore SHA-256 not enforced" >&2
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
    'MCP_JSON=' \
    'MCP_README=' \
    'GITIGNORE_PATH=' \
    'GITIGNORE_SHA256=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'EXPECTED_SERVER_KEYS=' \
    'DENY_LIST_SERVER_KEYS=' \
    'LINEAR_URL_LITERAL=' \
    'GITHUB_COMMAND_LITERAL=' \
    'GITHUB_ARGS=' \
    'M365_COMMAND_LITERAL=' \
    'M365_ARGS=' \
    'SALESFORCE_COMMAND_LITERAL=' \
    'SALESFORCE_ARGS=' \
    'GONG_COMMAND_LITERAL=' \
    'GONG_ARGS=' \
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
    'EXPECTED_PASS_COUNTS=' \
    'EXPECTED_PREDECESSOR_SHA256='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"
  declare -F sanitize_for_banned_scan >/dev/null 2>&1 \
    || fail "${gate}: harness missing sanitize_for_banned_scan function definition"
  declare -F compute_sha256 >/dev/null 2>&1 \
    || fail "${gate}: harness missing compute_sha256 function definition"
}

# ------------------------------------------------------------------
# task9 — regression against ten predecessor harnesses
# ------------------------------------------------------------------
check_task9() {
  local gate="task9"

  # Story 4.2 review-fix F6 (BMAD_REGRESSION_DEPTH guard; ported back
  # into Story 4.1 under its in-review status): if invoked as a
  # predecessor by a newer story's task9 (BMAD_REGRESSION_DEPTH set),
  # skip the ten-harness recursion. Outer-level invocations still
  # run the full chain; nested invocations short-circuit to avoid
  # the O(N!) regression tree + macOS bash 3.2.57 tmp/ trap race.
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
  )
  local i path name out pass_count expected expected_sha got_sha
  local total="${#harnesses[@]}"
  for (( i=0; i<total; i++ )); do
    path="${harnesses[$i]}"
    expected="${EXPECTED_PASS_COUNTS[$i]}"
    expected_sha="${EXPECTED_PREDECESSOR_SHA256[$i]}"
    name="$(basename "${path}")"
    require_file_exists "${path}" "${gate}"

    # F3 review fix — byte-stability gate. Compute each predecessor
    # harness's SHA-256 before invoking it; hard-fail on drift. This
    # codifies AC10's zero-predecessor-edit invariant in the harness
    # itself (previous harness versions checked only PASS counts).
    if ! got_sha="$(compute_sha256 "${path}")"; then
      fail "${gate}: SHA-256 utility unavailable; cannot verify ${name} byte-stability"
    fi
    if [[ "${got_sha}" != "${expected_sha}" ]]; then
      fail "${gate}: ${name} SHA-256 ${got_sha} != expected ${expected_sha} (predecessor harness byte drift)"
    fi

    if ! out="$(bash "${path}" all 2>&1)"; then
      echo "${out}" >&2
      fail "${gate}: ${name} all returned non-zero"
    fi
    pass_count="$(printf '%s\n' "${out}" | grep -c '^PASS:' || true)"
    pass_count="$(printf '%s' "${pass_count}" | tr -d '[:space:]')"
    if [[ "${pass_count}" != "${expected}" ]]; then
      echo "${out}" >&2
      fail "${gate}: ${name} emitted ${pass_count} PASS line(s), expected ${expected}"
    fi
  done
  # F3 review fix — positive-branch confirmation of predecessor
  # byte-stability gate. Emitted to stderr and uses the `task9 OK:`
  # prefix (not `^PASS:`) to preserve AC9's "exactly 10 `^PASS:` lines"
  # invariant on stdout OR combined streams.
  echo "task9 OK: predecessor byte-stability verified (SHA-256 matched for all 10 harnesses)" >&2
}

# Dispatcher wrapped in `main()` so bash 3.2 parses the entire function
# body up-front; avoids a file-buffer corruption bug that can surface when
# `check_task9` spawns a long chain of predecessor-harness subshells and
# bash resumes reading the script at a stale offset on return.
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
