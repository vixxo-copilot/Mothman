#!/usr/bin/env bash
set -euo pipefail

# Story 3.2 — Portable `memory/.obsidian/` config port from the gtd-life
# vault — deterministic validation harness.
#
# Scope:
#   - Story 3.2 creates the portable Obsidian config under memory/.obsidian/
#     ported verbatim (six files) or REPAIRED (templates.json) from the
#     gtd-life source, with user-local vault cache (workspace.json) and
#     Derek / Bobby / RevivaGo / meeting-history residue scrubbed or
#     excluded. Seven ported files:
#       memory/.obsidian/app.json
#       memory/.obsidian/appearance.json
#       memory/.obsidian/community-plugins.json
#       memory/.obsidian/core-plugins.json
#       memory/.obsidian/daily-notes.json
#       memory/.obsidian/graph.json
#       memory/.obsidian/templates.json     (REPAIRED — source "_templates" → "")
#     workspace.json is intentionally EXCLUDED — user-local vault cache
#     with 19 banned-term hits + 7 `bobby` hits + 30 meeting-slug hits.
#   - This harness extends the Story 3.1 seven-harness regression chain with
#     an eighth predecessor (Story 3.1) and verifies all eight in task6.
#
# Gates:
#   task1  baseline-audit evidence present and structured (story-3-2-baseline-audit.md)
#   task2  canonical-blueprint evidence present and structured (story-3-2-canonical-blueprint.md)
#   task3  per-file shape: existence, non-empty, trailing newline, first/last non-ws char, key presence, literal values, forbidden-file block (workspace.json, *.bak, *.log, *.tmp, .DS_Store, plugins/), directory count exactly 7, AC11 invariance (.gitkeep + 9 Story 3.1 templates + no new sentinels under .obsidian/)
#   task4  cross-file scrub: boundary-guarded banned-term regex + literal gtd-life / /Users/ / Public/ path scans + bobby fixed-string scan + meeting-slug regex + templates.json `_templates` scrub assertion
#   task5  self-check: shebang, set -euo pipefail, every case arm, every declared constant, regex_self_probe function definition (declare -F)
#   task6  regression: invoke Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 harnesses in `all` mode; each must exit zero and emit the expected PASS-count fingerprint
#   all    runs every gate in order
#
# Invocation: bash _bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays). Uses only bash,
# grep, awk, sed, find, tr, wc, head, tail, od, and shell built-ins. BSD-grep
# AND GNU-grep compatible. Intentionally does not use ripgrep (rg), jq, node,
# or Python — JSON shape assertions use grep-based probes, not a JSON parser.
#
# Context:
#   - templates.json is the one REPAIRED file (source "folder": "_templates"
#     → port "folder": ""; the source string "_templates" points at a
#     non-existent memory/_templates/ directory that Story 3.1 explicitly
#     declined to create).
#   - The Story 1.1 line-155 allowlist is extended additively by Story 3.2
#     to admit `\.obsidian` — documented AC13 / AC15 exception following the
#     Story 2.1 commit `0db273b` + Story 3.1 Phase-4 F1 precedents.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

MEMORY_DIR="${PROJECT_ROOT}/memory"
OBSIDIAN_DIR="${MEMORY_DIR}/.obsidian"

APP_JSON="${OBSIDIAN_DIR}/app.json"
APPEARANCE_JSON="${OBSIDIAN_DIR}/appearance.json"
COMMUNITY_PLUGINS_JSON="${OBSIDIAN_DIR}/community-plugins.json"
CORE_PLUGINS_JSON="${OBSIDIAN_DIR}/core-plugins.json"
DAILY_NOTES_JSON="${OBSIDIAN_DIR}/daily-notes.json"
GRAPH_JSON="${OBSIDIAN_DIR}/graph.json"
TEMPLATES_JSON="${OBSIDIAN_DIR}/templates.json"

# Forbidden-file path constant — asserted absent in check_task3.
WORKSPACE_JSON="${OBSIDIAN_DIR}/workspace.json"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-3-2-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-3-2-canonical-blueprint.md"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"
STORY_2_3_HARNESS="${TESTS_DIR}/story-2-3-work-persona-validation.sh"
STORY_2_4_HARNESS="${TESTS_DIR}/story-2-4-benji-inbox-absence-validation.sh"
STORY_3_1_HARNESS="${TESTS_DIR}/story-3-1-memory-template-tree-validation.sh"

# POSIX-ERE composite boundary-guarded banned-term regex. Case-insensitive
# via `grep -iE`. 17 tokens — identical to the Story 3.1 Phase-4 F4 lock.
# Zero new tokens added for Story 3.2; zero tokens removed.
BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'

# Meeting-slug fingerprint. Any match inside a ported .obsidian/ file
# indicates workspace.json content has leaked into a sibling file
# (workspace.json caches meeting-directory paths like
# `memory/meetings/2026-04-20-bobby-derek-wkly-1-1/agenda.md`). The
# regex requires at least one letter after the date so the literal
# `YYYY-MM-DD` format string in daily-notes.json does not trigger.
MEETING_SLUG_REGEX='[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]+'

# Nine Story 3.1 template files asserted byte-stable per AC11 invariance.
# Paths are relative to MEMORY_DIR.
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

# Expected byte counts per the Story 3.1 Task-6 handoff (2026-04-20
# fingerprint). Positional mapping to STORY_3_1_TEMPLATE_FILES — index N
# in this array is the expected wc -c byte count for the file at index N
# in STORY_3_1_TEMPLATE_FILES. Any drift fails check_task3 AC11.
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

# Assert the first non-whitespace char equals `want_first` and the last
# non-whitespace char equals `want_last`. Structural sanity probe for JSON
# shape without invoking a JSON parser. POSIX-safe: strips all whitespace
# with `tr -d '[:space:]'` and picks endpoints with `head -c 1` / `tail -c 1`.
assert_json_endpoints() {
  local path="$1"
  local want_first="$2"
  local want_last="$3"
  local gate="$4"
  local stripped first last
  stripped="$(tr -d '[:space:]' <"${path}")"
  first="$(printf '%s' "${stripped}" | head -c 1)"
  last="$(printf '%s' "${stripped}" | tail -c 1)"
  [[ "${first}" == "${want_first}" ]] \
    || fail "${gate}: ${path} first non-ws char is '${first}', expected '${want_first}'"
  [[ "${last}" == "${want_last}" ]] \
    || fail "${gate}: ${path} last non-ws char is '${last}', expected '${want_last}'"
}

# Assert the file ends with a single `\n` byte (0x0a).
assert_trailing_newline() {
  local path="$1"
  local gate="$2"
  local last_byte
  last_byte="$(tail -c 1 "${path}" | od -An -tx1 | tr -d ' \n')"
  [[ "${last_byte}" == '0a' ]] \
    || fail "${gate}: ${path} missing trailing newline (last byte: 0x${last_byte})"
}

# Fail fast if the host grep mis-parses the POSIX-ERE boundary pattern for
# any banned token, OR mis-parses the meeting-slug fingerprint regex.
# Exercises two banned-term tokens (one carry-forward: `derek` + `derekson`
# boundary negative; one Epic-3-added: `personal` + `personally` boundary
# negative) and a positive+negative meeting-slug probe. Guards against a
# mis-parsing host grep before any scrub gate depends on the regexes.
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

  # Meeting-slug fingerprint — positive and negative coverage.
  if ! echo "2026-04-20-bobby-derek-wkly-1-1" | grep -Eq "${MEETING_SLUG_REGEX}"; then
    fail "regex probe: meeting-slug regex rejected legitimate fingerprint '2026-04-20-bobby-derek-wkly-1-1'"
  fi
  if echo "foo-bar-baz" | grep -Eq "${MEETING_SLUG_REGEX}"; then
    fail "regex probe: meeting-slug regex admitted non-slug 'foo-bar-baz'"
  fi
  # YYYY-MM-DD on its own (no trailing letters) must NOT match.
  if echo "2026-04-20" | grep -Eq "${MEETING_SLUG_REGEX}"; then
    fail "regex probe: meeting-slug regex admitted bare date '2026-04-20' (would false-trip on daily-notes format literal)"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 3.2 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 3.2 Baseline Audit'"

  local section
  for section in \
    'gtd-life .obsidian source inventory' \
    'Per-file JSON structure + key map' \
    'Banned-term scan of source files' \
    'workspace.json exclusion rationale' \
    'Known defects requiring repair during port' \
    'Out-of-scope .obsidian subdirectories and paths' \
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

  grep -Fq '# Story 3.2 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 3.2 Canonical Blueprint'"

  local target
  for target in \
    'memory/.obsidian/app.json' \
    'memory/.obsidian/appearance.json' \
    'memory/.obsidian/community-plugins.json' \
    'memory/.obsidian/core-plugins.json' \
    'memory/.obsidian/daily-notes.json' \
    'memory/.obsidian/graph.json' \
    'memory/.obsidian/templates.json'; do
    if ! grep -Fq "Blueprint — \`${target}\`" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing per-file section for ${target}"
    fi
  done

  grep -Fq '## Forbidden-file lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing '## Forbidden-file lock' section"
  grep -Fq '## Banned-term lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing '## Banned-term lock' section"
  grep -Fq '## Meeting-slug fingerprint lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing '## Meeting-slug fingerprint lock' section"
}

# ------------------------------------------------------------------
# task3 — per-file shape verification
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"

  [[ -d "${OBSIDIAN_DIR}" ]] || fail "${gate}: directory missing: ${OBSIDIAN_DIR}"

  # AC1 exactness — directory contains exactly seven entries.
  local entry_count
  entry_count="$(ls -A "${OBSIDIAN_DIR}" | wc -l | tr -d '[:space:]')"
  [[ "${entry_count}" == '7' ]] \
    || fail "${gate}: ${OBSIDIAN_DIR} has ${entry_count} entries, expected exactly 7"

  # Seven files must exist, be non-empty, end with `\n`, and be
  # structurally-valid JSON (first/last non-ws char match).
  local f
  for f in \
    "${APP_JSON}" \
    "${APPEARANCE_JSON}" \
    "${COMMUNITY_PLUGINS_JSON}" \
    "${CORE_PLUGINS_JSON}" \
    "${DAILY_NOTES_JSON}" \
    "${GRAPH_JSON}" \
    "${TEMPLATES_JSON}"; do
    require_file_exists "${f}" "${gate}"
    require_file_nonempty "${f}" "${gate}"
    assert_trailing_newline "${f}" "${gate}"
  done

  # Object files — first `{`, last `}`.
  assert_json_endpoints "${APP_JSON}" '{' '}' "${gate}"
  assert_json_endpoints "${APPEARANCE_JSON}" '{' '}' "${gate}"
  assert_json_endpoints "${CORE_PLUGINS_JSON}" '{' '}' "${gate}"
  assert_json_endpoints "${DAILY_NOTES_JSON}" '{' '}' "${gate}"
  assert_json_endpoints "${GRAPH_JSON}" '{' '}' "${gate}"
  assert_json_endpoints "${TEMPLATES_JSON}" '{' '}' "${gate}"
  # Array file — first `[`, last `]`.
  assert_json_endpoints "${COMMUNITY_PLUGINS_JSON}" '[' ']' "${gate}"

  # --- app.json (AC2) ----------------------------------------------
  grep -Fq '"strictLineBreaks"' "${APP_JSON}" \
    || fail "${gate}: ${APP_JSON} missing key 'strictLineBreaks'"
  grep -Fq '"showFrontmatter"' "${APP_JSON}" \
    || fail "${gate}: ${APP_JSON} missing key 'showFrontmatter'"
  grep -Fq '"defaultViewMode"' "${APP_JSON}" \
    || fail "${gate}: ${APP_JSON} missing key 'defaultViewMode'"
  grep -Fq '"defaultViewMode": "source"' "${APP_JSON}" \
    || fail "${gate}: ${APP_JSON} missing literal value 'defaultViewMode: source'"
  local app_key_count
  app_key_count="$( { grep -o '":' "${APP_JSON}" || true; } | wc -l | tr -d '[:space:]')"
  [[ "${app_key_count}" == '3' ]] \
    || fail "${gate}: ${APP_JSON} has ${app_key_count} keys (via grep -o '\":' | wc -l), expected exactly 3"
  local app_bytes
  app_bytes="$(wc -c <"${APP_JSON}" | tr -d '[:space:]')"
  (( app_bytes <= 200 )) \
    || fail "${gate}: ${APP_JSON} byte length ${app_bytes} exceeds AC2 upper bound 200"

  # --- appearance.json (AC3) — literal `{}` after whitespace strip -
  local appearance_stripped
  appearance_stripped="$(tr -d '[:space:]' <"${APPEARANCE_JSON}")"
  [[ "${appearance_stripped}" == '{}' ]] \
    || fail "${gate}: ${APPEARANCE_JSON} stripped content is '${appearance_stripped}', expected '{}'"
  local appearance_key_count
  appearance_key_count="$( { grep -o '":' "${APPEARANCE_JSON}" || true; } | wc -l | tr -d '[:space:]')"
  [[ "${appearance_key_count}" == '0' ]] \
    || fail "${gate}: ${APPEARANCE_JSON} has ${appearance_key_count} keys (via grep -o '\":' | wc -l), expected exactly 0"
  local appearance_bytes
  appearance_bytes="$(wc -c <"${APPEARANCE_JSON}" | tr -d '[:space:]')"
  (( appearance_bytes <= 10 )) \
    || fail "${gate}: ${APPEARANCE_JSON} byte length ${appearance_bytes} exceeds AC3 upper bound 10"

  # --- community-plugins.json (AC4) — literal `[]` -----------------
  local community_stripped
  community_stripped="$(tr -d '[:space:]' <"${COMMUNITY_PLUGINS_JSON}")"
  [[ "${community_stripped}" == '[]' ]] \
    || fail "${gate}: ${COMMUNITY_PLUGINS_JSON} stripped content is '${community_stripped}', expected '[]'"
  local community_bytes
  community_bytes="$(wc -c <"${COMMUNITY_PLUGINS_JSON}" | tr -d '[:space:]')"
  (( community_bytes <= 10 )) \
    || fail "${gate}: ${COMMUNITY_PLUGINS_JSON} byte length ${community_bytes} exceeds AC4 upper bound 10"
  # AC4 companion — plugins/ subdirectory must not exist.
  [[ ! -d "${OBSIDIAN_DIR}/plugins" ]] \
    || fail "${gate}: forbidden directory present: ${OBSIDIAN_DIR}/plugins (community-plugin binaries out of scope)"

  # --- core-plugins.json (AC5) — 31 keys, 16 true + 15 false -------
  local plugin
  for plugin in \
    file-explorer global-search switcher graph backlink outgoing-link \
    tag-pane page-preview daily-notes templates markdown-importer \
    outline canvas properties bookmarks bases; do
    grep -Fq "\"${plugin}\": true" "${CORE_PLUGINS_JSON}" \
      || fail "${gate}: ${CORE_PLUGINS_JSON} missing enabled plugin: \"${plugin}\": true"
  done
  for plugin in \
    note-composer command-palette slash-command editor-status zk-prefixer \
    random-note word-count slides audio-recorder workspaces file-recovery \
    publish sync footnotes webviewer; do
    grep -Fq "\"${plugin}\": false" "${CORE_PLUGINS_JSON}" \
      || fail "${gate}: ${CORE_PLUGINS_JSON} missing disabled plugin: \"${plugin}\": false"
  done
  # `grep -c '":'` counts MATCHING LINES, not occurrences — unsafe for
  # compact JSON. `grep -o '":' | wc -l` counts occurrences reliably on
  # both BSD and GNU grep. Applied across every key-count assertion.
  local core_key_count
  core_key_count="$( { grep -o '":' "${CORE_PLUGINS_JSON}" || true; } | wc -l | tr -d '[:space:]')"
  [[ "${core_key_count}" == '31' ]] \
    || fail "${gate}: ${CORE_PLUGINS_JSON} has ${core_key_count} keys (via grep -o '\":' | wc -l), expected exactly 31"
  local core_bytes
  core_bytes="$(wc -c <"${CORE_PLUGINS_JSON}" | tr -d '[:space:]')"
  (( core_bytes <= 1024 )) \
    || fail "${gate}: ${CORE_PLUGINS_JSON} byte length ${core_bytes} exceeds blueprint upper bound 1024"

  # --- daily-notes.json (AC6) --------------------------------------
  grep -Fq '"folder": "daily"' "${DAILY_NOTES_JSON}" \
    || fail "${gate}: ${DAILY_NOTES_JSON} missing '\"folder\": \"daily\"'"
  grep -Fq '"format": "YYYY-MM-DD"' "${DAILY_NOTES_JSON}" \
    || fail "${gate}: ${DAILY_NOTES_JSON} missing '\"format\": \"YYYY-MM-DD\"'"
  grep -Fq '"template": ""' "${DAILY_NOTES_JSON}" \
    || fail "${gate}: ${DAILY_NOTES_JSON} missing '\"template\": \"\"'"
  local daily_key_count
  daily_key_count="$( { grep -o '":' "${DAILY_NOTES_JSON}" || true; } | wc -l | tr -d '[:space:]')"
  [[ "${daily_key_count}" == '3' ]] \
    || fail "${gate}: ${DAILY_NOTES_JSON} has ${daily_key_count} keys (via grep -o '\":' | wc -l), expected exactly 3"
  local daily_bytes
  daily_bytes="$(wc -c <"${DAILY_NOTES_JSON}" | tr -d '[:space:]')"
  (( daily_bytes <= 200 )) \
    || fail "${gate}: ${DAILY_NOTES_JSON} byte length ${daily_bytes} exceeds blueprint upper bound 200"

  # --- graph.json (AC7) — 20-key blueprint + explicit empties ------
  grep -Fq '"search": ""' "${GRAPH_JSON}" \
    || fail "${gate}: ${GRAPH_JSON} missing '\"search\": \"\"' (Derek search-query scrubbed / absent)"
  grep -Fq '"colorGroups": []' "${GRAPH_JSON}" \
    || fail "${gate}: ${GRAPH_JSON} missing '\"colorGroups\": []' (no Derek-authored color groups)"
  local graph_key
  for graph_key in \
    'collapse-filter' search showTags showAttachments hideUnresolved \
    showOrphans 'collapse-color-groups' colorGroups 'collapse-display' \
    showArrow textFadeMultiplier nodeSizeMultiplier lineSizeMultiplier \
    'collapse-forces' centerStrength repelStrength linkStrength \
    linkDistance scale close; do
    grep -Fq "\"${graph_key}\":" "${GRAPH_JSON}" \
      || fail "${gate}: ${GRAPH_JSON} missing key '\"${graph_key}\":'"
  done
  local graph_key_count
  graph_key_count="$( { grep -o '":' "${GRAPH_JSON}" || true; } | wc -l | tr -d '[:space:]')"
  [[ "${graph_key_count}" == '20' ]] \
    || fail "${gate}: ${GRAPH_JSON} has ${graph_key_count} keys (via grep -o '\":' | wc -l), expected exactly 20"
  local graph_bytes
  graph_bytes="$(wc -c <"${GRAPH_JSON}" | tr -d '[:space:]')"
  (( graph_bytes <= 1024 )) \
    || fail "${gate}: ${GRAPH_JSON} byte length ${graph_bytes} exceeds AC7 upper bound 1024"

  # --- templates.json (AC8) — REPAIRED single-key `folder: ""` -----
  grep -Fq '"folder": ""' "${TEMPLATES_JSON}" \
    || fail "${gate}: ${TEMPLATES_JSON} missing REPAIRED '\"folder\": \"\"'"
  if grep -Fq '_templates' "${TEMPLATES_JSON}"; then
    fail "${gate}: ${TEMPLATES_JSON} contains forbidden source substring '_templates' (REPAIR regressed)"
  fi
  local templates_key_count
  templates_key_count="$( { grep -o '":' "${TEMPLATES_JSON}" || true; } | wc -l | tr -d '[:space:]')"
  [[ "${templates_key_count}" == '1' ]] \
    || fail "${gate}: ${TEMPLATES_JSON} has ${templates_key_count} keys (via grep -o '\":' | wc -l), expected exactly 1"
  # Exact stripped-literal assertion — content must be the single-key
  # object {"folder":""} with no extra keys or stray characters.
  local templates_stripped
  templates_stripped="$(tr -d '[:space:]' <"${TEMPLATES_JSON}")"
  [[ "${templates_stripped}" == '{"folder":""}' ]] \
    || fail "${gate}: ${TEMPLATES_JSON} stripped content is '${templates_stripped}', expected '{\"folder\":\"\"}'"
  local templates_bytes
  templates_bytes="$(wc -c <"${TEMPLATES_JSON}" | tr -d '[:space:]')"
  (( templates_bytes <= 64 )) \
    || fail "${gate}: ${TEMPLATES_JSON} byte length ${templates_bytes} exceeds blueprint upper bound 64"

  # --- Forbidden-file block (AC9) ----------------------------------
  [[ ! -f "${WORKSPACE_JSON}" ]] \
    || fail "${gate}: forbidden file present: ${WORKSPACE_JSON}"
  local forbidden_pattern forbidden_hit
  for forbidden_pattern in '*.bak' '*.log' '*.tmp' '.DS_Store' \
      'workspace.json.bak' 'workspaces.json'; do
    forbidden_hit="$(find "${OBSIDIAN_DIR}" -type f -name "${forbidden_pattern}" 2>/dev/null | head -n 1 || true)"
    if [[ -n "${forbidden_hit}" ]]; then
      fail "${gate}: forbidden file under ${OBSIDIAN_DIR}: ${forbidden_hit} (matches pattern ${forbidden_pattern})"
    fi
  done
  # Icon\r macOS resource-fork sentinel — literal filename `Icon<CR>`.
  local icon_hit
  icon_hit="$(find "${OBSIDIAN_DIR}" -type f -name "Icon?" 2>/dev/null | head -n 1 || true)"
  if [[ -n "${icon_hit}" ]]; then
    fail "${gate}: forbidden macOS resource-fork sentinel under ${OBSIDIAN_DIR}: ${icon_hit}"
  fi

  # --- AC11 invariance ---------------------------------------------
  local gitkeep="${MEMORY_DIR}/.gitkeep"
  [[ -f "${gitkeep}" ]] || fail "${gate}: AC11: ${gitkeep} missing"
  local gitkeep_size
  gitkeep_size="$(wc -c <"${gitkeep}" | tr -d '[:space:]')"
  [[ "${gitkeep_size}" == '0' ]] \
    || fail "${gate}: AC11: ${gitkeep} must be empty (0 bytes, found ${gitkeep_size})"
  local t3_idx t3_rel t3_path t3_bytes t3_expected_bytes
  local t3_total="${#STORY_3_1_TEMPLATE_FILES[@]}"
  for (( t3_idx=0; t3_idx<t3_total; t3_idx++ )); do
    t3_rel="${STORY_3_1_TEMPLATE_FILES[$t3_idx]}"
    t3_expected_bytes="${STORY_3_1_TEMPLATE_BYTES[$t3_idx]}"
    t3_path="${MEMORY_DIR}/${t3_rel}"
    [[ -f "${t3_path}" ]] || fail "${gate}: AC11: Story 3.1 template missing: ${t3_path}"
    [[ -s "${t3_path}" ]] || fail "${gate}: AC11: Story 3.1 template empty: ${t3_path}"
    t3_bytes="$(wc -c <"${t3_path}" | tr -d '[:space:]')"
    [[ "${t3_bytes}" == "${t3_expected_bytes}" ]] \
      || fail "${gate}: AC11: Story 3.1 template ${t3_path} byte count ${t3_bytes}, expected ${t3_expected_bytes} (Story 3.1 Task-6 handoff fingerprint)"
  done
  # No new sentinels anywhere under memory/.obsidian/.
  local sentinel sentinel_hit
  for sentinel in .gitkeep .keep empty placeholder; do
    sentinel_hit="$(find "${OBSIDIAN_DIR}" -type f -name "${sentinel}" 2>/dev/null | head -n 1 || true)"
    if [[ -n "${sentinel_hit}" ]]; then
      fail "${gate}: AC11: forbidden sentinel under ${OBSIDIAN_DIR}: ${sentinel_hit}"
    fi
  done
}

# ------------------------------------------------------------------
# task4 — cross-file scrub: banned terms + path leaks + bobby + slug + `_templates`
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  regex_self_probe

  local files="${APP_JSON}
${APPEARANCE_JSON}
${COMMUNITY_PLUGINS_JSON}
${CORE_PLUGINS_JSON}
${DAILY_NOTES_JSON}
${GRAPH_JSON}
${TEMPLATES_JSON}"

  local f hit
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue

    # Banned-term scan — boundary-guarded, case-insensitive (AC10).
    if hit="$(grep -inE "${BANNED_TERMS_REGEX}" "${f}" 2>/dev/null || true)" && [[ -n "${hit}" ]]; then
      echo "${hit}" >&2
      fail "${gate}: ${f} contains a banned token (boundary-guarded regex hit)"
    fi

    # Fixed-string path-reference scans (AC10 defence-in-depth).
    if grep -Fq 'gtd-life' "${f}"; then
      fail "${gate}: ${f} contains literal path reference 'gtd-life'"
    fi
    if grep -Fq '~/Public/gtd-life' "${f}"; then
      fail "${gate}: ${f} contains source-repo path '~/Public/gtd-life'"
    fi
    if grep -Fq 'Public/gtd-life' "${f}"; then
      fail "${gate}: ${f} contains source-repo path 'Public/gtd-life'"
    fi
    if grep -Fq '/Users/' "${f}"; then
      fail "${gate}: ${f} contains absolute filesystem path '/Users/'"
    fi

    # Fixed-string `bobby` scan (AC9 backstop — workspace.json leakage).
    if grep -Fiq 'bobby' "${f}"; then
      fail "${gate}: ${f} contains forbidden name 'bobby' (workspace.json leakage)"
    fi

    # Meeting-slug regex scan (AC9 workspace-cache fingerprint).
    if grep -Eq "${MEETING_SLUG_REGEX}" "${f}"; then
      echo "$(grep -nE "${MEETING_SLUG_REGEX}" "${f}" | head -n 3)" >&2
      fail "${gate}: ${f} contains meeting-slug fingerprint (workspace.json leakage indicator)"
    fi
  done <<EOF
${files}
EOF

  # templates.json `_templates` REPAIR assertion is owned by check_task3
  # shape gate (see the TEMPLATES_JSON block that asserts
  # `! grep -Fq '_templates' "${TEMPLATES_JSON}"`). AC8 maps cleanly onto
  # that single gate; duplicating it here would obscure the invariant
  # map. F7 (Senior Dev Review) removed the redundant block.
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
    'MEMORY_DIR=' \
    'OBSIDIAN_DIR=' \
    'APP_JSON=' \
    'APPEARANCE_JSON=' \
    'COMMUNITY_PLUGINS_JSON=' \
    'CORE_PLUGINS_JSON=' \
    'DAILY_NOTES_JSON=' \
    'GRAPH_JSON=' \
    'TEMPLATES_JSON=' \
    'WORKSPACE_JSON=' \
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
    'BANNED_TERMS_REGEX=' \
    'MEETING_SLUG_REGEX=' \
    'STORY_3_1_TEMPLATE_FILES=' \
    'STORY_3_1_TEMPLATE_BYTES='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  # Story 2.4 F4 + Story 3.1 precedent — probe-presence idiom via
  # `declare -F` so a commented-out function body cannot satisfy the gate.
  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"
}

# ------------------------------------------------------------------
# task6 — regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 harnesses
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

  # Phase-4 F7 fingerprint. Arg tuple: "PATH|display_name|expected_pass_count".
  # Empirically measured on 2026-04-20 via `bash <harness> all | grep -c '^PASS:'`.
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
