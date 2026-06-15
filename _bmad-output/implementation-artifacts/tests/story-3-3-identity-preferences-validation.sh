#!/usr/bin/env bash
set -euo pipefail

# Story 3.3 — Seed empty identity + preferences files under `memory/me/` —
# deterministic validation harness.
#
# Scope:
#   - Story 3.3 creates two markdown scaffolds under memory/me/ with
#     scope: work frontmatter and five identity-placeholder tokens
#     ({{employee_name}}, {{employee_role}}, {{employee_department}},
#     {{employee_manager}}, {{employee_email}}) — REBUILT FROM SCAFFOLD,
#     NOT ported verbatim from the gtd-life source (distinct from
#     Story 3.2's verbatim-with-REPAIR port method). Two files:
#       memory/me/identity.md     (10-key frontmatter, 8-heading body)
#       memory/me/preferences.md  ( 5-key frontmatter, 6-heading body)
#   - The regression chain extends Story 3.2's eight-harness chain by
#     one (adds Story 3.2 as the ninth predecessor) — nine prior
#     harnesses total (Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 /
#     3.1 / 3.2).
#   - The Story 1.1 line-155 allowlist requires ZERO amendment —
#     Story 2.1 commit `0db273b` already admitted `me` as a legitimate
#     memory/ subdirectory slug. AC10 codifies this zero-edit invariant
#     (distinct from Stories 3.1 / 3.2 which each added one line).
#
# Gates:
#   task1  baseline-audit evidence present and structured (story-3-3-baseline-audit.md)
#   task2  canonical-blueprint evidence present and structured (story-3-3-canonical-blueprint.md)
#   task3  per-file shape: existence, non-empty, trailing newline, first-3-bytes `---`,
#          frontmatter key order per AC2/AC4, body headings per AC3/AC5, byte budget
#          [200, 2048], LF-only, directory count exactly 2, no subdirectories,
#          no sentinels, .gitkeep 0-byte invariance, Story 3.1 template byte-stability,
#          Story 3.2 .obsidian/ file existence (byte-stability owned by task6 regression)
#   task4  cross-file scrub: 17-token banned-term regex, 12-token Derek fixed-string
#          defence-in-depth, path-reference fixed-strings, placeholder allowlist
#          (identity.md: all 5 tokens allowlisted; preferences.md: zero {{...}} tokens),
#          forbidden-form probes (anchored single-brace, angle, percent, dollar-brace),
#          personal-in-tags backstop
#   task5  self-check: shebang, set -euo pipefail, every case arm, every declared
#          constant, regex_self_probe function definition via `declare -F`
#   task6  regression: nine prior harnesses invoked in `all` mode; each must exit
#          zero and emit the expected ^PASS: line-count fingerprint
#          (1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7)
#   all    runs every gate in order — exits 0 with exactly 7 ^PASS: lines on success
#
# Invocation: bash _bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays, no namerefs). Uses
# only bash, grep, awk, sed, find, tr, wc, head, tail, od, cut, sort, and shell
# built-ins. BSD-grep AND GNU-grep compatible. Intentionally does NOT use rg,
# jq, yq, node, or Python — frontmatter-key-order assertions use awk line-walks,
# not a YAML parser.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

MEMORY_DIR="${PROJECT_ROOT}/memory"
ME_DIR="${MEMORY_DIR}/me"
OBSIDIAN_DIR="${MEMORY_DIR}/.obsidian"

IDENTITY_MD="${ME_DIR}/identity.md"
PREFERENCES_MD="${ME_DIR}/preferences.md"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-3-3-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-3-3-canonical-blueprint.md"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"
STORY_2_3_HARNESS="${TESTS_DIR}/story-2-3-work-persona-validation.sh"
STORY_2_4_HARNESS="${TESTS_DIR}/story-2-4-benji-inbox-absence-validation.sh"
STORY_3_1_HARNESS="${TESTS_DIR}/story-3-1-memory-template-tree-validation.sh"
STORY_3_2_HARNESS="${TESTS_DIR}/story-3-2-obsidian-config-validation.sh"

# AC10 zero-edit invariant — positional fingerprint of the Story 1.1
# scaffold-validation harness. Captured 2026-04-20 via `wc -c` and
# `shasum -a 256`. Any drift means Story 3.3 (or a later story) edited
# the harness, violating AC10. check_task5 asserts both.
STORY_1_1_HARNESS_BYTES=6215
STORY_1_1_HARNESS_SHA256="a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8"

# POSIX-ERE composite boundary-guarded banned-term regex. Case-insensitive
# via `grep -iE`. 17 tokens — identical to the Story 3.1 Phase-4 F4 lock
# and Story 3.2. Zero new tokens added for Story 3.3; zero tokens removed.
BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'

# Story-3.3-specific Derek defence-in-depth fixed-string scans. These
# tokens appear verbatim in the gtd-life source me/*.md files and must
# not port through. Fixed-string scans (`grep -Fi`) — NOT added to the
# 17-token regex because some strings (e.g. `Integrum`, `Laurie`) could
# legitimately appear in unrelated future content; narrow-scope fixed-
# string enforcement limited to memory/me/*.md is appropriate.
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

# Five-item identity-placeholder allowlist (Story 2.1 / 2.3 vocabulary
# extended by {{employee_email}} for Story 3.3). Any {{...}} token in
# identity.md MUST be a member of this set. preferences.md MUST yield
# zero {{...}} tokens (prose-only, AC6 reinforcement).
IDENTITY_PLACEHOLDER_ALLOWLIST=(
  '{{employee_name}}'
  '{{employee_role}}'
  '{{employee_department}}'
  '{{employee_manager}}'
  '{{employee_email}}'
)

# Canonical frontmatter key order for identity.md (10 keys) and
# preferences.md (5 keys). Enforced by check_task3 via awk line-walk.
IDENTITY_FRONTMATTER_KEYS=(
  type
  scope
  name
  role
  department
  manager
  email
  created
  updated
  tags
)

PREFERENCES_FRONTMATTER_KEYS=(
  type
  scope
  created
  updated
  tags
)

# Body heading sequence (H1 + H2 list, in order).
IDENTITY_BODY_HEADINGS=(
  '# Identity'
  '## Name'
  '## Role'
  '## Department'
  '## Manager'
  '## Email'
  '## Work Scope'
  '## Key References'
)

PREFERENCES_BODY_HEADINGS=(
  '# Preferences'
  '## Communication Style'
  '## Tooling'
  '## Meeting Cadence'
  '## Working Hours'
  '## AI Assistant'
)

# AC8 byte-budget bounds.
MIN_BYTES=200
MAX_BYTES=2048

# Nine Story 3.1 template files asserted byte-stable per AC9. Paths
# are relative to MEMORY_DIR. Positional mapping to STORY_3_1_TEMPLATE_BYTES —
# copied verbatim from the Story 3.2 harness (same Task-6 fingerprint).
STORY_3_1_TEMPLATE_FILES=(
  meetings/_template/meeting.md
  meetings/_template/agenda.md
  meetings/_template/prep.md
  meetings/_template/transcript.md
  people/_template.md
  decisions/_template.md
  reference/_template.md
  inbox/_template.md
  appreciations/_template.md
)

STORY_3_1_TEMPLATE_BYTES=(
  828
  250
  513
  306
  561
  588
  506
  72
  211
)

# Seven Story 3.2 `.obsidian/` files asserted present + non-empty per
# AC9. Byte-level invariance is enforced by Story 3.2's own harness
# running in task6 regression (single source of truth — see AC9 +
# Story 3.2 F4 positional-fingerprint discipline).
STORY_3_2_OBSIDIAN_FILES=(
  app.json
  appearance.json
  community-plugins.json
  core-plugins.json
  daily-notes.json
  graph.json
  templates.json
)

# AC9 SHA-256 vector for the seven Story 3.2 .obsidian/ JSON files.
# Positional parallel to STORY_3_2_OBSIDIAN_FILES. Captured 2026-04-20
# via `shasum -a 256 memory/.obsidian/<file> | awk '{print $1}'`.
# Any drift means a Story-3.2 file was edited during Story 3.3
# execution (AC9 + AC12 invariance violated). check_task3 loops and
# asserts each file's SHA matches. If neither `shasum` nor `openssl`
# is available, fall back to byte-count only with a WARN.
STORY_3_2_OBSIDIAN_SHA256=(
  c39e6f3f3becf132433b3dc698eadcf0600a026e5ea73cb87676ad27b2c7a810
  ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356
  37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570
  ac8a3c03d04b14d992f568d7fab290b232f611c7844a3ccbcdb3f0e84b72f280
  f21e73a2012255ceda1ea9171cac89cb03c45301772dc2b4eedd357970f1eb78
  f75c7af68f6f1a17663d9c4f8359dca4567d91a6f59c48e03c5868b639d19424
  935f8fcefa2349412bd80c16f7235117fd462a2fb962d80abcf7d8cfb01c27e8
)

# AC12 broader byte-stability — positional-fingerprint arrays for the
# scaffold files Story 3.3 must NOT touch. Story 2.1 agent-identity rule,
# the four Story 2.2 rule files, Story 2.3 work persona, the three root
# context files, README, LICENSE, .gitignore. Parallel arrays (POSIX
# bash 3.2 has no associative arrays). Paths are relative to PROJECT_ROOT.
# Byte counts captured 2026-04-20 via `wc -c`. Drift here means a
# non-Story-3.3-scoped file was edited, violating AC12's additive-only
# discipline.
AC12_STABLE_FILES=(
  .cursor/rules/agent-identity.mdc
  .cursor/rules/outbound-messaging-guardrail.mdc
  .cursor/rules/memory-vault-protection.mdc
  .cursor/rules/teams-dm-formatting.mdc
  .cursor/rules/email-triage-thread-defaults.mdc
  agents/personas/work.md
  AGENTS.md
  CLAUDE.md
  .cursorrules
  README.md
  LICENSE
  .gitignore
)

AC12_STABLE_BYTES=(
  2347
  2259
  1875
  1870
  1508
  2006
  1048
  1048
  772
  960
  667
  51
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

# Extract the frontmatter body (lines strictly between the first `---`
# on line 1 and the next `---`). POSIX-awk line-walk.
extract_frontmatter() {
  local path="$1"
  awk '/^---$/{c++; if(c==2) exit} c==1 && NR>1 {print}' "${path}"
}

# Fail fast if the host grep mis-parses any regex used downstream.
# Exercises two banned-term tokens (one carry-forward: `derek` + `derekson`
# boundary negative; one Epic-3-added: `personal` + `personally` boundary
# negative) AND the five-item identity-placeholder allowlist (positive
# case `{{employee_name}}`; identity-file semantic miss `{{Meeting Title}}`).
# Guards against a mis-parsing host grep or a mis-escaped allowlist
# before any scrub gate depends on them.
regex_self_probe() {
  # Carry-forward token `derek`: positive match; `derekson` boundary reject.
  if echo "derekson" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary admitted 'derekson' (grep too permissive)"
  fi
  if ! echo "derek smith" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary rejected legitimate hit 'derek smith' (grep too strict)"
  fi

  # Epic-3-added token `personal`: positive match; `personally` boundary reject.
  if ! echo "personal note" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary rejected legitimate hit 'personal note' (grep too strict for personal token)"
  fi
  if echo "personally" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary admitted 'personally' (grep too permissive for personal token)"
  fi

  # Placeholder-allowlist BEHAVIOURAL probes — exercise the real
  # extraction + membership path (not tautological constant echoing).
  # (a) is_allowlisted_placeholder must return 0 for an allowlisted token.
  if ! is_allowlisted_placeholder '{{employee_name}}'; then
    echo "regex_self_probe FAIL: is_allowlisted_placeholder rejected '{{employee_name}}'" >&2
    return 1
  fi
  # (b) is_allowlisted_placeholder must return non-zero for a non-allowlisted token.
  if is_allowlisted_placeholder '{{Meeting Title}}'; then
    echo "regex_self_probe FAIL: is_allowlisted_placeholder accepted '{{Meeting Title}}'" >&2
    return 1
  fi
  # (c) the grep extraction path must emit both tokens for a mixed input.
  local probe_out
  probe_out="$(echo '{{employee_name}} {{Meeting Title}}' | grep -oE '\{\{[^}]+\}\}' | sort -u)"
  case "${probe_out}" in
    *'{{employee_name}}'*) ;;
    *) echo "regex_self_probe FAIL: extraction missed {{employee_name}}" >&2; return 1 ;;
  esac
  case "${probe_out}" in
    *'{{Meeting Title}}'*) ;;
    *) echo "regex_self_probe FAIL: extraction missed {{Meeting Title}}" >&2; return 1 ;;
  esac
}

# Placeholder allowlist membership test: returns 0 if the given token
# is a member of IDENTITY_PLACEHOLDER_ALLOWLIST, non-zero otherwise.
# POSIX-bash-3.2 safe — no namerefs, no associative arrays.
is_allowlisted_placeholder() {
  local token="$1"
  local entry
  for entry in "${IDENTITY_PLACEHOLDER_ALLOWLIST[@]}"; do
    if [[ "${entry}" == "${token}" ]]; then
      return 0
    fi
  done
  return 1
}

# Compare the canonical-order frontmatter key list against the expected
# positional array. Uses awk line-walk + `grep -oE` to extract keys in
# source order; diffs against expected positionally. Fails loudly on
# any missing key, extra key, or reorder.
assert_frontmatter_key_order() {
  local path="$1"
  local gate="$2"
  shift 2
  local expected=("$@")

  local actual_list
  actual_list="$(extract_frontmatter "${path}" \
    | grep -oE '^[a-zA-Z_][a-zA-Z0-9_]*:' \
    | sed 's/:$//')"

  local idx=0
  local actual_key expected_key
  while IFS= read -r actual_key; do
    [[ -z "${actual_key}" ]] && continue
    if (( idx >= ${#expected[@]} )); then
      fail "${gate}: ${path} frontmatter has extra key '${actual_key}' past canonical position ${idx}"
    fi
    expected_key="${expected[$idx]}"
    if [[ "${actual_key}" != "${expected_key}" ]]; then
      fail "${gate}: ${path} frontmatter key ${idx} is '${actual_key}', expected '${expected_key}' (canonical order violated)"
    fi
    idx=$((idx + 1))
  done <<EOF
${actual_list}
EOF

  if (( idx != ${#expected[@]} )); then
    fail "${gate}: ${path} frontmatter has ${idx} keys, expected ${#expected[@]} in canonical order"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 3.3 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 3.3 Baseline Audit'"

  local section
  for section in \
    'gtd-life me/ source inventory' \
    'Per-file frontmatter + heading map' \
    'Banned-term scan of source files' \
    'Derek-specific fixed-string scan of source files' \
    'Out-of-scope files and subdirectories' \
    'Content classes to scrub vs retain' \
    'Mapping: source path'; do
    if ! grep -Fq "${section}" "${BASELINE_AUDIT_PATH}"; then
      fail "${gate}: baseline audit missing required section/keyword: ${section}"
    fi
  done
}

# ------------------------------------------------------------------
# task2 — canonical-blueprint evidence present and complete
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"
  require_file_nonempty "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq '# Story 3.3 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 3.3 Canonical Blueprint'"

  local target
  for target in \
    'memory/me/identity.md' \
    'memory/me/preferences.md'; do
    if ! grep -Fq "Blueprint — \`${target}\`" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing per-file section for ${target}"
    fi
  done

  grep -Fq '## Placeholder vocabulary lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing '## Placeholder vocabulary lock' section"
  grep -Fq '## Banned-term lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing '## Banned-term lock' section"
  if ! grep -Fq '## Forbidden-form lock' "${BLUEPRINT_PATH}"; then
    fail "${gate}: blueprint missing '## Forbidden-form lock' section"
  fi
}

# ------------------------------------------------------------------
# task3 — per-file shape verification
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"

  [[ -d "${ME_DIR}" ]] || fail "${gate}: directory missing: ${ME_DIR}"

  # AC1 — directory contains exactly two entries.
  local entry_count
  entry_count="$(ls -A "${ME_DIR}" | wc -l | tr -d '[:space:]')"
  [[ "${entry_count}" == '2' ]] \
    || fail "${gate}: ${ME_DIR} has ${entry_count} entries, expected exactly 2"

  # AC1 — no subdirectories under memory/me/.
  local subdir_hit
  subdir_hit="$(find "${ME_DIR}" -mindepth 1 -type d 2>/dev/null | head -n 1 || true)"
  [[ -z "${subdir_hit}" ]] \
    || fail "${gate}: ${ME_DIR} contains forbidden subdirectory: ${subdir_hit}"

  # AC1 — no sentinels or scratch files under memory/me/.
  local sentinel sentinel_hit
  for sentinel in .gitkeep .keep empty placeholder '.DS_Store' '*.bak' '*.log' '*.tmp'; do
    sentinel_hit="$(find "${ME_DIR}" -type f -name "${sentinel}" 2>/dev/null | head -n 1 || true)"
    if [[ -n "${sentinel_hit}" ]]; then
      fail "${gate}: forbidden sentinel under ${ME_DIR}: ${sentinel_hit}"
    fi
  done

  # Per-file shape (identity.md + preferences.md).
  local f
  for f in "${IDENTITY_MD}" "${PREFERENCES_MD}"; do
    require_file_exists "${f}" "${gate}"
    require_file_nonempty "${f}" "${gate}"
    assert_trailing_newline "${f}" "${gate}"

    # First three bytes must be `---` (frontmatter opens on line 1).
    local first3
    first3="$(head -c 3 "${f}" | tr -d '[:space:]')"
    [[ "${first3}" == '---' ]] \
      || fail "${gate}: ${f} first 3 bytes are '${first3}', expected '---'"

    # AC8 — byte budget [MIN_BYTES, MAX_BYTES].
    local bytes
    bytes="$(wc -c <"${f}" | tr -d '[:space:]')"
    if (( bytes < MIN_BYTES )); then
      fail "${gate}: ${f} byte length ${bytes} below AC8 lower bound ${MIN_BYTES}"
    fi
    if (( bytes > MAX_BYTES )); then
      fail "${gate}: ${f} byte length ${bytes} above AC8 upper bound ${MAX_BYTES}"
    fi

    # AC8 — LF line endings, no CRLF.
    local cr_count
    cr_count="$(grep -c $'\r' "${f}" 2>/dev/null || true)"
    cr_count="$(printf '%s' "${cr_count}" | tr -d '[:space:]')"
    [[ "${cr_count}" == '0' ]] \
      || fail "${gate}: ${f} contains ${cr_count} CR byte(s) (CRLF line endings forbidden)"

    # Frontmatter closing delimiter must exist (awk walk sees c==2).
    if ! awk '/^---$/{c++; if(c==2){found=1; exit}} END{if(!found) exit 1}' "${f}"; then
      fail "${gate}: ${f} missing closing frontmatter delimiter ---"
    fi
  done

  # AC2 — identity.md frontmatter key order.
  assert_frontmatter_key_order "${IDENTITY_MD}" "${gate}" "${IDENTITY_FRONTMATTER_KEYS[@]}"

  # AC2 — identity.md frontmatter literal values.
  local identity_fm
  identity_fm="$(extract_frontmatter "${IDENTITY_MD}")"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'type: identity' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing literal 'type: identity'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'scope: work' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing literal 'scope: work'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'tags: [identity, work]' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing literal 'tags: [identity, work]'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'created: YYYY-MM-DD' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing literal 'created: YYYY-MM-DD'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'updated: YYYY-MM-DD' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing literal 'updated: YYYY-MM-DD'"
  # AC2 — five identity-placeholder-bearing frontmatter lines.
  printf '%s\n' "${identity_fm}" | grep -Fxq 'name: "{{employee_name}}"' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing 'name: \"{{employee_name}}\"'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'role: "{{employee_role}}"' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing 'role: \"{{employee_role}}\"'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'department: "{{employee_department}}"' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing 'department: \"{{employee_department}}\"'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'manager: "{{employee_manager}}"' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing 'manager: \"{{employee_manager}}\"'"
  printf '%s\n' "${identity_fm}" | grep -Fxq 'email: "{{employee_email}}"' \
    || fail "${gate}: ${IDENTITY_MD} frontmatter missing 'email: \"{{employee_email}}\"'"

  # AC4 — preferences.md frontmatter key order.
  assert_frontmatter_key_order "${PREFERENCES_MD}" "${gate}" "${PREFERENCES_FRONTMATTER_KEYS[@]}"

  # AC4 — preferences.md frontmatter literal values.
  local preferences_fm
  preferences_fm="$(extract_frontmatter "${PREFERENCES_MD}")"
  printf '%s\n' "${preferences_fm}" | grep -Fxq 'type: preferences' \
    || fail "${gate}: ${PREFERENCES_MD} frontmatter missing literal 'type: preferences'"
  printf '%s\n' "${preferences_fm}" | grep -Fxq 'scope: work' \
    || fail "${gate}: ${PREFERENCES_MD} frontmatter missing literal 'scope: work'"
  printf '%s\n' "${preferences_fm}" | grep -Fxq 'tags: [preferences, work]' \
    || fail "${gate}: ${PREFERENCES_MD} frontmatter missing literal 'tags: [preferences, work]'"
  printf '%s\n' "${preferences_fm}" | grep -Fxq 'created: YYYY-MM-DD' \
    || fail "${gate}: ${PREFERENCES_MD} frontmatter missing literal 'created: YYYY-MM-DD'"
  printf '%s\n' "${preferences_fm}" | grep -Fxq 'updated: YYYY-MM-DD' \
    || fail "${gate}: ${PREFERENCES_MD} frontmatter missing literal 'updated: YYYY-MM-DD'"

  # AC4 — preferences.md frontmatter contains zero {{...}} tokens.
  local pref_fm_placeholders
  pref_fm_placeholders="$( { printf '%s\n' "${preferences_fm}" \
    | grep -oE '\{\{[^}]+\}\}' || true; } | wc -l | tr -d '[:space:]')"
  [[ "${pref_fm_placeholders}" == '0' ]] \
    || fail "${gate}: ${PREFERENCES_MD} frontmatter contains ${pref_fm_placeholders} identity-placeholder token(s); expected zero"

  # AC3 — identity.md body headings: monotonic ordering assertion.
  # Each heading must appear AFTER the previous heading's line number.
  local heading prev_line=0 hline
  for heading in "${IDENTITY_BODY_HEADINGS[@]}"; do
    hline="$(grep -Fxn "${heading}" "${IDENTITY_MD}" | head -n 1 | cut -d: -f1)"
    [[ -n "${hline}" ]] \
      || fail "${gate}: ${IDENTITY_MD} missing body heading: '${heading}'"
    (( hline > prev_line )) \
      || fail "${gate}: ${IDENTITY_MD} heading '${heading}' (line ${hline}) not after prior heading (line ${prev_line})"
    prev_line="${hline}"
  done

  # AC3 — Work Scope section includes the literal 'work context only'.
  grep -Fq 'work context only' "${IDENTITY_MD}" \
    || fail "${gate}: ${IDENTITY_MD} body missing literal substring 'work context only'"

  # AC3 — Key References section lists the three required paths.
  grep -Fq '.cursor/rules/agent-identity.mdc' "${IDENTITY_MD}" \
    || fail "${gate}: ${IDENTITY_MD} body missing reference to '.cursor/rules/agent-identity.mdc'"
  grep -Fq 'agents/personas/work.md' "${IDENTITY_MD}" \
    || fail "${gate}: ${IDENTITY_MD} body missing reference to 'agents/personas/work.md'"
  grep -Fq 'memory/me/preferences.md' "${IDENTITY_MD}" \
    || fail "${gate}: ${IDENTITY_MD} body missing reference to sibling 'memory/me/preferences.md'"

  # AC5 — preferences.md body headings: monotonic ordering assertion.
  prev_line=0
  for heading in "${PREFERENCES_BODY_HEADINGS[@]}"; do
    hline="$(grep -Fxn "${heading}" "${PREFERENCES_MD}" | head -n 1 | cut -d: -f1)"
    [[ -n "${hline}" ]] \
      || fail "${gate}: ${PREFERENCES_MD} missing body heading: '${heading}'"
    (( hline > prev_line )) \
      || fail "${gate}: ${PREFERENCES_MD} heading '${heading}' (line ${hline}) not after prior heading (line ${prev_line})"
    prev_line="${hline}"
  done

  # AC5 — Tooling section enumerates the five active Vixxo MCPs.
  local mcp
  for mcp in Linear GitHub 'Microsoft 365' Salesforce Gong; do
    grep -Fq "${mcp}" "${PREFERENCES_MD}" \
      || fail "${gate}: ${PREFERENCES_MD} missing MCP enumeration: '${mcp}'"
  done

  # AC9 — memory/.gitkeep is 0 bytes (Story 1.1 invariance).
  local gitkeep="${MEMORY_DIR}/.gitkeep"
  [[ -f "${gitkeep}" ]] || fail "${gate}: AC9: ${gitkeep} missing"
  local gitkeep_size
  gitkeep_size="$(wc -c <"${gitkeep}" | tr -d '[:space:]')"
  [[ "${gitkeep_size}" == '0' ]] \
    || fail "${gate}: AC9: ${gitkeep} must be 0 bytes (found ${gitkeep_size})"

  # AC9 — Story 3.1 template byte-count fingerprint.
  local t3_idx t3_rel t3_path t3_bytes t3_expected_bytes
  local t3_total="${#STORY_3_1_TEMPLATE_FILES[@]}"
  for (( t3_idx=0; t3_idx<t3_total; t3_idx++ )); do
    t3_rel="${STORY_3_1_TEMPLATE_FILES[$t3_idx]}"
    t3_expected_bytes="${STORY_3_1_TEMPLATE_BYTES[$t3_idx]}"
    t3_path="${MEMORY_DIR}/${t3_rel}"
    [[ -f "${t3_path}" ]] || fail "${gate}: AC9: Story 3.1 template missing: ${t3_path}"
    [[ -s "${t3_path}" ]] || fail "${gate}: AC9: Story 3.1 template empty: ${t3_path}"
    t3_bytes="$(wc -c <"${t3_path}" | tr -d '[:space:]')"
    [[ "${t3_bytes}" == "${t3_expected_bytes}" ]] \
      || fail "${gate}: AC9: Story 3.1 template ${t3_path} byte count ${t3_bytes}, expected ${t3_expected_bytes} (Story 3.1 Task-6 handoff fingerprint)"
  done

  # AC9 — Story 3.2 .obsidian/ files exist and are non-empty; byte-level
  # invariance is owned by the Story 3.2 harness in task6 regression
  # (single source of truth — see Story 3.2 F4 positional fingerprint).
  [[ -d "${OBSIDIAN_DIR}" ]] || fail "${gate}: AC9: ${OBSIDIAN_DIR} missing"
  local ob
  for ob in "${STORY_3_2_OBSIDIAN_FILES[@]}"; do
    [[ -f "${OBSIDIAN_DIR}/${ob}" ]] \
      || fail "${gate}: AC9: Story 3.2 config missing: ${OBSIDIAN_DIR}/${ob}"
    [[ -s "${OBSIDIAN_DIR}/${ob}" ]] \
      || fail "${gate}: AC9: Story 3.2 config empty: ${OBSIDIAN_DIR}/${ob}"
  done

  # AC9 — Story 3.2 .obsidian/ SHA-256 positional fingerprint. Captured
  # 2026-04-20. Loops STORY_3_2_OBSIDIAN_FILES + STORY_3_2_OBSIDIAN_SHA256
  # in parallel. Uses `shasum -a 256`; falls back to `openssl dgst -sha256`;
  # if neither is available, emits a WARN and relies on byte-count via the
  # upstream existence/non-empty check + task6 Story 3.2 harness regression.
  local ob_sha_tool=""
  if command -v shasum >/dev/null 2>&1; then
    ob_sha_tool="shasum"
  elif command -v openssl >/dev/null 2>&1; then
    ob_sha_tool="openssl"
  fi
  if [[ -n "${ob_sha_tool}" ]]; then
    local ob_idx ob_rel ob_path ob_expected_sha ob_actual_sha
    local ob_total="${#STORY_3_2_OBSIDIAN_FILES[@]}"
    for (( ob_idx=0; ob_idx<ob_total; ob_idx++ )); do
      ob_rel="${STORY_3_2_OBSIDIAN_FILES[$ob_idx]}"
      ob_expected_sha="${STORY_3_2_OBSIDIAN_SHA256[$ob_idx]}"
      ob_path="${OBSIDIAN_DIR}/${ob_rel}"
      if [[ "${ob_sha_tool}" == "shasum" ]]; then
        ob_actual_sha="$(shasum -a 256 "${ob_path}" | awk '{print $1}')"
      else
        ob_actual_sha="$(openssl dgst -sha256 "${ob_path}" | awk '{print $NF}')"
      fi
      [[ "${ob_actual_sha}" == "${ob_expected_sha}" ]] \
        || fail "${gate}: AC9: Story 3.2 ${ob_rel} SHA-256 ${ob_actual_sha} != expected ${ob_expected_sha} (byte-level drift since 2026-04-20)"
    done
  else
    echo "${gate}: WARN: neither shasum nor openssl available; Story 3.2 SHA-256 vector not enforced" >&2
  fi
  # workspace.json must not exist (Story 3.2 AC9 exclusion).
  [[ ! -f "${OBSIDIAN_DIR}/workspace.json" ]] \
    || fail "${gate}: AC9: forbidden file present: ${OBSIDIAN_DIR}/workspace.json"
  # plugins/ subdirectory must not exist (Story 3.2 AC4 exclusion).
  [[ ! -d "${OBSIDIAN_DIR}/plugins" ]] \
    || fail "${gate}: AC9: forbidden directory present: ${OBSIDIAN_DIR}/plugins"

  # AC12 — broader byte-stability for the 12 scaffold files Story 3.3
  # must not touch. Positional byte-count fingerprint (parallel arrays
  # per POSIX bash 3.2 constraint). Drift here means Story 3.3 execution
  # edited a non-scoped file (AC12 additive-only discipline violated).
  local ac12_idx ac12_rel ac12_path ac12_bytes ac12_expected
  local ac12_total="${#AC12_STABLE_FILES[@]}"
  for (( ac12_idx=0; ac12_idx<ac12_total; ac12_idx++ )); do
    ac12_rel="${AC12_STABLE_FILES[$ac12_idx]}"
    ac12_expected="${AC12_STABLE_BYTES[$ac12_idx]}"
    ac12_path="${PROJECT_ROOT}/${ac12_rel}"
    [[ -f "${ac12_path}" ]] \
      || fail "${gate}: AC12: required file missing: ${ac12_rel}"
    ac12_bytes="$(wc -c <"${ac12_path}" | tr -d '[:space:]')"
    [[ "${ac12_bytes}" == "${ac12_expected}" ]] \
      || fail "${gate}: AC12: ${ac12_rel} byte count ${ac12_bytes} != expected ${ac12_expected} (byte-stability drift)"
  done
}

# ------------------------------------------------------------------
# task4 — cross-file scrub
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  regex_self_probe

  local f hit
  for f in "${IDENTITY_MD}" "${PREFERENCES_MD}"; do
    require_file_exists "${f}" "${gate}"

    # AC7 — 17-token banned-term regex, boundary-guarded, case-insensitive.
    if hit="$(grep -inE "${BANNED_TERMS_REGEX}" "${f}" 2>/dev/null || true)" && [[ -n "${hit}" ]]; then
      echo "${hit}" >&2
      fail "${gate}: ${f} contains a banned token (boundary-guarded regex hit)"
    fi

    # AC7 — Derek defence-in-depth fixed-string scans.
    local derek_token
    for derek_token in "${DEREK_FIXED_STRINGS[@]}"; do
      if grep -Fiq "${derek_token}" "${f}"; then
        fail "${gate}: ${f} contains Derek-specific fixed-string token: '${derek_token}'"
      fi
    done

    # AC7 / AC14 — path-reference fixed-string scans.
    if grep -Fq 'gtd-life' "${f}"; then
      fail "${gate}: ${f} contains literal path reference 'gtd-life'"
    fi
    if grep -Fq '/Users/' "${f}"; then
      fail "${gate}: ${f} contains absolute filesystem path '/Users/'"
    fi
    if grep -Fq 'Public/' "${f}"; then
      fail "${gate}: ${f} contains source-repo path fragment 'Public/'"
    fi
    if grep -Fq '~/' "${f}"; then
      fail "${gate}: ${f} contains home-path reference '~/'"
    fi

    # AC2 / AC4 backstop — no 'personal' token in tags line.
    if grep -Eq '^tags:.*personal' "${f}"; then
      fail "${gate}: ${f} tags line contains forbidden token 'personal'"
    fi

    # AC6 — forbidden-form probes (single-brace / angle / percent / dollar-brace).
    # Single-brace probe is anchored with surrounding-context checks to avoid
    # matching the inner {employee_*} slice of legitimate {{employee_*}} tokens
    # (Task 3a subagent note). A naive `grep -oE '\{[A-Za-z_][A-Za-z0-9_]*\}'`
    # would yield 10 false-positive hits on identity.md.
    local single_brace_hit
    single_brace_hit="$(grep -oE '(^|[^{])\{[A-Za-z_][A-Za-z0-9_]*\}([^}]|$)' "${f}" 2>/dev/null || true)"
    if [[ -n "${single_brace_hit}" ]]; then
      echo "${single_brace_hit}" >&2
      fail "${gate}: ${f} contains forbidden single-brace placeholder form '{name}'"
    fi
    local angle_hit
    angle_hit="$(grep -oE '<[A-Za-z_][A-Za-z0-9_]*>' "${f}" 2>/dev/null || true)"
    if [[ -n "${angle_hit}" ]]; then
      echo "${angle_hit}" >&2
      fail "${gate}: ${f} contains forbidden angle-bracket placeholder form '<name>'"
    fi
    local percent_hit
    percent_hit="$(grep -oE '%[A-Za-z_][A-Za-z0-9_]*%' "${f}" 2>/dev/null || true)"
    if [[ -n "${percent_hit}" ]]; then
      echo "${percent_hit}" >&2
      fail "${gate}: ${f} contains forbidden percent-wrapped placeholder form '%name%'"
    fi
    local dollar_hit
    dollar_hit="$(grep -oE '\$\{[^}]+\}' "${f}" 2>/dev/null || true)"
    if [[ -n "${dollar_hit}" ]]; then
      echo "${dollar_hit}" >&2
      fail "${gate}: ${f} contains forbidden dollar-brace placeholder form '\${name}'"
    fi
  done

  # AC6 — identity.md: every extracted {{...}} token is allowlisted, and
  # all five allowlisted tokens appear at least once.
  local identity_tokens_raw
  identity_tokens_raw="$(grep -oE '\{\{[^}]+\}\}' "${IDENTITY_MD}" 2>/dev/null || true)"
  if [[ -z "${identity_tokens_raw}" ]]; then
    fail "${gate}: ${IDENTITY_MD} yields zero {{...}} tokens; expected all five allowlisted placeholders"
  fi
  local token
  while IFS= read -r token; do
    [[ -z "${token}" ]] && continue
    if ! is_allowlisted_placeholder "${token}"; then
      fail "${gate}: ${IDENTITY_MD} contains non-allowlisted placeholder token: '${token}'"
    fi
  done <<EOF
${identity_tokens_raw}
EOF

  # AC3 — each of the five allowlisted placeholders appears at least once.
  local allow_token
  for allow_token in "${IDENTITY_PLACEHOLDER_ALLOWLIST[@]}"; do
    if ! grep -Fq "${allow_token}" "${IDENTITY_MD}"; then
      fail "${gate}: ${IDENTITY_MD} missing required allowlisted placeholder: '${allow_token}'"
    fi
  done

  # AC5 / AC6 — preferences.md: ZERO {{...}} tokens (prose-only).
  local preferences_tokens_raw
  preferences_tokens_raw="$(grep -oE '\{\{[^}]+\}\}' "${PREFERENCES_MD}" 2>/dev/null || true)"
  if [[ -n "${preferences_tokens_raw}" ]]; then
    echo "${preferences_tokens_raw}" >&2
    fail "${gate}: ${PREFERENCES_MD} contains {{...}} placeholder token(s); expected zero (prose-only)"
  fi

  # AC5 — personal-assistant / personal-productivity tokens excluded from preferences.md.
  local pref_forbidden
  for pref_forbidden in Chiron Benji Flowtopic Obsidian gmail google-calendar; do
    if grep -Fiq "${pref_forbidden}" "${PREFERENCES_MD}"; then
      fail "${gate}: ${PREFERENCES_MD} contains forbidden personal-tool token: '${pref_forbidden}'"
    fi
  done
}

# ------------------------------------------------------------------
# task5 — self-check (harness well-formed and owns the full gate set)
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${SELF_PATH}" "${gate}"

  head -n 1 "${SELF_PATH}" | grep -Fxq '#!/usr/bin/env bash' \
    || fail "${gate}: harness missing bash shebang on line 1"
  grep -Fq 'set -euo pipefail' "${SELF_PATH}" \
    || fail "${gate}: harness missing 'set -euo pipefail'"

  local required_case
  for required_case in 'task1)' 'task2)' 'task3)' 'task4)' 'task5)' 'task6)' 'all)'; do
    grep -Fq "${required_case}" "${SELF_PATH}" \
      || fail "${gate}: harness missing case branch: ${required_case}"
  done

  local required_const
  for required_const in \
    'ME_DIR=' \
    'IDENTITY_MD=' \
    'PREFERENCES_MD=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'STORY_1_1_HARNESS=' \
    'STORY_1_2_HARNESS=' \
    'STORY_1_3_HARNESS=' \
    'STORY_2_1_HARNESS=' \
    'STORY_2_2_HARNESS=' \
    'STORY_2_3_HARNESS=' \
    'STORY_2_4_HARNESS=' \
    'STORY_3_1_HARNESS=' \
    'STORY_3_2_HARNESS=' \
    'BANNED_TERMS_REGEX=' \
    'DEREK_FIXED_STRINGS=' \
    'IDENTITY_PLACEHOLDER_ALLOWLIST=' \
    'IDENTITY_FRONTMATTER_KEYS=' \
    'PREFERENCES_FRONTMATTER_KEYS=' \
    'IDENTITY_BODY_HEADINGS=' \
    'PREFERENCES_BODY_HEADINGS=' \
    'MIN_BYTES=' \
    'MAX_BYTES=' \
    'STORY_3_1_TEMPLATE_FILES=' \
    'STORY_3_1_TEMPLATE_BYTES=' \
    'STORY_3_2_OBSIDIAN_FILES=' \
    'STORY_3_2_OBSIDIAN_SHA256=' \
    'STORY_1_1_HARNESS_BYTES=' \
    'STORY_1_1_HARNESS_SHA256=' \
    'AC12_STABLE_FILES=' \
    'AC12_STABLE_BYTES='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  # Story 2.4 F4 + Story 3.1 / 3.2 precedent — probe-presence idiom via
  # `declare -F` so a commented-out function body cannot satisfy the gate.
  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"

  # AC10 zero-edit invariant — positional fingerprint of the Story 1.1
  # scaffold-validation harness (byte count primary; SHA-256 secondary
  # if `shasum` / `openssl` available). Any drift means the Story 1.1
  # harness was edited during Story 3.3 execution, violating AC10.
  local story11_actual_bytes
  story11_actual_bytes="$(wc -c <"${STORY_1_1_HARNESS}" | tr -d '[:space:]')"
  [[ "${story11_actual_bytes}" == "${STORY_1_1_HARNESS_BYTES}" ]] \
    || fail "${gate}: story-1-1 harness byte count ${story11_actual_bytes} != expected ${STORY_1_1_HARNESS_BYTES} (AC10 zero-edit invariant violated)"
  local story11_actual_sha=""
  if command -v shasum >/dev/null 2>&1; then
    story11_actual_sha="$(shasum -a 256 "${STORY_1_1_HARNESS}" | awk '{print $1}')"
  elif command -v openssl >/dev/null 2>&1; then
    story11_actual_sha="$(openssl dgst -sha256 "${STORY_1_1_HARNESS}" | awk '{print $NF}')"
  fi
  if [[ -n "${story11_actual_sha}" ]]; then
    [[ "${story11_actual_sha}" == "${STORY_1_1_HARNESS_SHA256}" ]] \
      || fail "${gate}: story-1-1 harness SHA-256 ${story11_actual_sha} != expected ${STORY_1_1_HARNESS_SHA256} (AC10 zero-edit invariant violated)"
  else
    echo "${gate}: WARN: neither shasum nor openssl available; byte-count fingerprint only" >&2
  fi
}

# ------------------------------------------------------------------
# task6 — regression against nine predecessor harnesses
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  require_file_exists "${STORY_1_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_2_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_3_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_2_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_3_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_4_HARNESS}" "${gate}"
  require_file_exists "${STORY_3_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_3_2_HARNESS}" "${gate}"

  # Phase-4 F7 PASS-count fingerprint. Arg tuple:
  # "PATH|display_name|expected_pass_count". Empirically measured on
  # 2026-04-20 via `bash <harness> all | grep -c '^PASS:'`.
  local out pass_count expected_pass
  local -a regressions=(
    "${STORY_1_1_HARNESS}|story-1-1-scaffold-validation.sh|1"
    "${STORY_1_2_HARNESS}|story-1-2-root-files-validation.sh|1"
    "${STORY_1_3_HARNESS}|story-1-3-root-context-validation.sh|1"
    "${STORY_2_1_HARNESS}|story-2-1-agent-identity-validation.sh|1"
    "${STORY_2_2_HARNESS}|story-2-2-guardrail-and-formatting-validation.sh|10"
    "${STORY_2_3_HARNESS}|story-2-3-work-persona-validation.sh|7"
    "${STORY_2_4_HARNESS}|story-2-4-benji-inbox-absence-validation.sh|7"
    "${STORY_3_1_HARNESS}|story-3-1-memory-template-tree-validation.sh|7"
    "${STORY_3_2_HARNESS}|story-3-2-obsidian-config-validation.sh|7"
  )
  local rec path name
  for rec in "${regressions[@]}"; do
    path="${rec%%|*}"
    rec="${rec#*|}"
    name="${rec%|*}"
    expected_pass="${rec##*|}"
    # Phase-4 F6 pattern — capture combined stdout/stderr; echo on failure.
    if ! out="$(bash "${path}" all 2>&1)"; then
      echo "${out}" >&2
      fail "${gate}: ${name} all returned non-zero"
    fi
    pass_count="$(printf '%s\n' "${out}" | grep -c '^PASS:' || true)"
    pass_count="$(printf '%s' "${pass_count}" | tr -d '[:space:]')"
    if [[ "${pass_count}" != "${expected_pass}" ]]; then
      echo "${out}" >&2
      fail "${gate}: ${name} emitted ${pass_count} PASS line(s), expected ${expected_pass}"
    fi
  done
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
    ;;
  *)
    fail "Unknown mode: ${mode}"
    ;;
esac

echo "PASS: ${mode}"
