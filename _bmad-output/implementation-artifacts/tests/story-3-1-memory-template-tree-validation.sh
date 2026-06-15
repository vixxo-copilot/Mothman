#!/usr/bin/env bash
set -euo pipefail

# Story 3.1 — Port `_template.md` / `_template/` trees from gtd-life memory
# vault — deterministic validation harness.
#
# Scope:
#   - Story 3.1 creates the empty per-directory template tree under memory/
#     matching the gtd-life conventions, with all Derek / RevivaGo / personal-
#     context / malformed-frontmatter residue scrubbed. Nine ported files:
#       memory/meetings/_template/meeting.md
#       memory/meetings/_template/agenda.md
#       memory/meetings/_template/prep.md
#       memory/meetings/_template/transcript.md
#       memory/people/_template.md
#       memory/decisions/_template.md
#       memory/reference/_template.md
#       memory/inbox/_template.md
#       memory/appreciations/_template.md  (REPAIRED — source is malformed)
#   - Obsidian config (.obsidian/) is Story 3.2 (out of scope here).
#   - memory/me/identity.md + memory/me/preferences.md are Story 3.3
#     (out of scope here).
#   - This harness extends the Story 2.4 seven-harness regression chain with
#     a seventh predecessor (Story 2.4) and verifies all seven in task6.
#
# Gates:
#   task1  baseline-audit evidence present and structured (story-3-1-baseline-audit.md)
#   task2  canonical-blueprint evidence present and structured (story-3-1-canonical-blueprint.md)
#   task3  per-file shape: existence, non-empty, frontmatter keys in order, required headers, doc-link table in meeting.md, defect repairs in inbox.md + appreciations/_template.md
#   task4  cross-file scrub: boundary-guarded banned-term regex + literal gtd-life path references + placeholder-vocabulary allowlist + forbidden placeholder-form probes
#   task5  self-check: shebang, set -euo pipefail, every case arm, every declared constant, regex_self_probe function definition (declare -F)
#   task6  regression: invoke Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 harnesses in `all` mode; each must exit zero
#   all    runs every gate in order
#
# Invocation: bash _bmad-output/implementation-artifacts/tests/story-3-1-memory-template-tree-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays). Uses only bash,
# grep, awk, sed, find, and shell built-ins. BSD-grep AND GNU-grep compatible.
# Intentionally does not use ripgrep (rg) or Python.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

MEMORY_DIR="${PROJECT_ROOT}/memory"
MEETINGS_TEMPLATE_DIR="${MEMORY_DIR}/meetings/_template"

MEETING_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/meeting.md"
AGENDA_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/agenda.md"
PREP_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/prep.md"
TRANSCRIPT_TEMPLATE="${MEETINGS_TEMPLATE_DIR}/transcript.md"
PEOPLE_TEMPLATE="${MEMORY_DIR}/people/_template.md"
DECISIONS_TEMPLATE="${MEMORY_DIR}/decisions/_template.md"
REFERENCE_TEMPLATE="${MEMORY_DIR}/reference/_template.md"
INBOX_TEMPLATE="${MEMORY_DIR}/inbox/_template.md"
APPRECIATIONS_TEMPLATE="${MEMORY_DIR}/appreciations/_template.md"

BASELINE_AUDIT_PATH="${TESTS_DIR}/story-3-1-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-3-1-canonical-blueprint.md"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"
STORY_2_3_HARNESS="${TESTS_DIR}/story-2-3-work-persona-validation.sh"
STORY_2_4_HARNESS="${TESTS_DIR}/story-2-4-benji-inbox-absence-validation.sh"

# POSIX-ERE composite boundary-guarded banned-term regex. Case-insensitive via
# `grep -iE`. Reused across every one of the nine ported template files in
# task4. 17 tokens: carry-forward set from Stories 2.1 / 2.2 / 2.3 / 2.4 plus
# Epic-3-specific additions (wyoming, cheyenne, family, home, blog, wife, son,
# daughter, dog, personal). `personal` (Phase-4 F4 review fix) catches
# lingering "personal" scope enumerations from the gtd-life source even if the
# frontmatter value is scrubbed — a follow-on defence layer.
BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'

# Placeholder-vocabulary allowlist (17 tokens per blueprint). Newline-separated
# so the harness can iterate via while-read without word-splitting pitfalls
# (placeholder tokens contain spaces and double-quotes).
PLACEHOLDER_ALLOWLIST='{{Meeting Title}}
{{Name}}
{{topic}}
{{owner}}
{{estimated minutes}}
{{person}}
{{action}}
{{action item}}
{{date}}
{{company}}
{{role}}
{{manager or "N/A"}}
{{count or "N/A"}}
{{Decision Title}}
{{Reference Title}}
{{Recipient or Moment}}
{{name}}'

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

# Parse YAML frontmatter block between the first two `---` delimiters.
# Requires the opening `---` to be on line 1 and a matching closing `---` to
# appear strictly after. Prints the frontmatter body (excluding delimiters) to
# stdout. Same pattern as story-2-3-work-persona-validation.sh read_frontmatter.
read_frontmatter() {
  local path="$1"
  local gate="$2"

  local fm_open_line fm_close_line
  fm_open_line="$(grep -n '^---$' "${path}" | head -n 1 | cut -d: -f1 || true)"
  fm_close_line="$(grep -n '^---$' "${path}" | sed -n '2p' | cut -d: -f1 || true)"
  [[ -n "${fm_open_line}" && -n "${fm_close_line}" ]] \
    || fail "${gate}: ${path} missing YAML frontmatter delimiters"
  [[ "${fm_open_line}" -eq 1 ]] \
    || fail "${gate}: ${path} frontmatter must start on line 1 (found line ${fm_open_line})"
  (( fm_close_line > fm_open_line )) \
    || fail "${gate}: ${path} frontmatter block malformed (close <= open)"

  awk -v a="${fm_open_line}" -v b="${fm_close_line}" 'NR>a && NR<b' "${path}"
}

# Assert that every expected frontmatter key appears as the line-prefix `KEY:`
# (not `## KEY:` — which would be the appreciations Defect #1 shape).
# Pass the frontmatter body as stdin, pass the gate name + file path + expected
# keys as arguments.
assert_frontmatter_keys() {
  local frontmatter="$1"
  local gate="$2"
  local path="$3"
  shift 3
  local key
  for key in "$@"; do
    if ! echo "${frontmatter}" | grep -Eq "^${key}:"; then
      fail "${gate}: ${path} frontmatter missing key '${key}:'"
    fi
    # Defect #1 guard — a key rendered as an H2 heading inside the
    # frontmatter (e.g. `## type: appreciation`) is a malformed-source leak.
    if echo "${frontmatter}" | grep -Eq "^##[[:space:]]+${key}:"; then
      fail "${gate}: ${path} frontmatter has key rendered as H2 heading: ## ${key}:"
    fi
  done
}

# Phase-4 F5 review fix — assert a specific KEY:VALUE pair (not merely the
# key name). Guards against silent value drift (e.g. `type: meeting` flipping
# to `type: person` during a copy-paste). `expected_value` must match the
# literal scalar after the colon (with optional leading whitespace). Use for
# discriminator keys whose value is the template's identity.
assert_frontmatter_key_value() {
  local frontmatter="$1"
  local gate="$2"
  local path="$3"
  local key="$4"
  local expected_value="$5"
  if ! echo "${frontmatter}" | grep -Eq "^${key}:[[:space:]]*${expected_value}[[:space:]]*$"; then
    fail "${gate}: ${path} frontmatter key '${key}:' does not equal expected value '${expected_value}'"
  fi
}

# Assert every listed heading string (passed via heredoc stdin, one per line,
# blank lines skipped) appears as an exact whole-line match in the file.
require_exact_headers() {
  local path="$1"
  local gate="$2"
  local headers="$3"
  local line
  while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    grep -Fxq "${line}" "${path}" \
      || fail "${gate}: ${path} missing required header line: ${line}"
  done <<EOF
${headers}
EOF
}

# Fail fast if the host grep mis-parses the POSIX-ERE boundary pattern for any
# banned token. Exercises positive + negative cases for at least two tokens
# (one from the carry-forward set, one from the Epic-3 additions) plus a
# placeholder-form probe. Guards against a mis-parsing host grep (e.g.
# BusyBox without -E, or LANG misbehavior) before any scrub gate depends on
# the regex.
regex_self_probe() {
  # Negative case: `derekson` must NOT match (boundary guard rejects
  # embedded letters after `derek`).
  if echo "derekson" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary admitted 'derekson' (grep too permissive)"
  fi

  # Positive case: `derek smith` must match (space is a non-letter boundary).
  if ! echo "derek smith" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary rejected legitimate hit 'derek smith' (grep too strict)"
  fi

  # Negative case for an Epic-3 token: `familial` must NOT match (boundary
  # guard rejects embedded letters after `family`).
  if echo "familial" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary admitted 'familial' (grep too permissive for family token)"
  fi

  # Positive case for an Epic-3 token: `family dinner` must match.
  if ! echo "family dinner" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary rejected legitimate hit 'family dinner' (grep too strict for family token)"
  fi

  # Phase-4 F4 review fix — `personal` coverage. Positive: `personal note`
  # must match (space boundary). Negative: `personally` must NOT match
  # (embedded letter after `personal` is a boundary-guard rejection).
  if ! echo "personal note" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary rejected legitimate hit 'personal note' (grep too strict for personal token)"
  fi
  if echo "personally" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "regex probe: banned-term boundary admitted 'personally' (grep too permissive for personal token)"
  fi

  # Placeholder-form probe — double-brace `{{Meeting Title}}` must be
  # admitted by the `\{\{[^}]+\}\}` enumeration regex; single-brace
  # `{employee_name}` must NOT be admitted as a double-brace token.
  if ! echo '{{Meeting Title}}' | grep -oE '\{\{[^}]+\}\}' >/dev/null; then
    fail "regex probe: placeholder enumeration regex rejected '{{Meeting Title}}' (grep too strict)"
  fi
  if echo '{employee_name}' | grep -oE '\{\{[^}]+\}\}' >/dev/null; then
    fail "regex probe: placeholder enumeration regex admitted single-brace '{employee_name}' (grep too permissive)"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"
  require_file_nonempty "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq '# Story 3.1 Baseline Audit' "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title '# Story 3.1 Baseline Audit'"

  local section
  for section in \
    'gtd-life source inventory' \
    'Per-file frontmatter + heading map' \
    'Banned-term scan of source files' \
    'Known defects requiring repair during port' \
    'Out-of-scope directories' \
    'Placeholder vocabulary across source files' \
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

  grep -Fq '# Story 3.1 Canonical Blueprint' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title '# Story 3.1 Canonical Blueprint'"

  # One blueprint section per ported file — assert each target path appears
  # in a `## Blueprint —` section line.
  local target
  for target in \
    'memory/meetings/_template/meeting.md' \
    'memory/meetings/_template/agenda.md' \
    'memory/meetings/_template/prep.md' \
    'memory/meetings/_template/transcript.md' \
    'memory/people/_template.md' \
    'memory/decisions/_template.md' \
    'memory/reference/_template.md' \
    'memory/inbox/_template.md' \
    'memory/appreciations/_template.md'; do
    if ! grep -Fq "Blueprint — \`${target}\`" "${BLUEPRINT_PATH}"; then
      fail "${gate}: blueprint missing per-file section for ${target}"
    fi
  done

  # Both the banned-term lock section and the placeholder-vocabulary lock
  # section must exist — these are the two machine-readable locks the task4
  # scrub gate depends on.
  grep -Fq '## Banned-term lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing '## Banned-term lock' section"
  grep -Fq '## Placeholder vocabulary lock' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing '## Placeholder vocabulary lock' section"
}

# ------------------------------------------------------------------
# task3 — per-file shape verification (existence + frontmatter + headers)
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"

  # Phase-4 F2 review fix — AC1 "exactly N files, no extras" per-directory
  # count assertions. `ls -A` enumerates everything including dotfiles; the
  # output is piped through `wc -l` (which counts lines and therefore
  # entries) and normalised via `tr -d '[:space:]'` to strip the BSD-`wc`
  # leading spaces. POSIX-safe; no GNU-only flags.
  local expected actual dir
  local -a count_specs=(
    "${MEETINGS_TEMPLATE_DIR}|4"
    "${MEMORY_DIR}/people|1"
    "${MEMORY_DIR}/decisions|1"
    "${MEMORY_DIR}/reference|1"
    "${MEMORY_DIR}/inbox|1"
    "${MEMORY_DIR}/appreciations|1"
  )
  local spec
  for spec in "${count_specs[@]}"; do
    dir="${spec%|*}"
    expected="${spec##*|}"
    [[ -d "${dir}" ]] || fail "${gate}: directory missing: ${dir}"
    actual="$(ls -A "${dir}" | wc -l | tr -d '[:space:]')"
    [[ "${actual}" == "${expected}" ]] \
      || fail "${gate}: ${dir} has ${actual} entries, expected exactly ${expected}"
  done

  # Phase-4 F3 review fix — AC9 sentinel invariance. (1) memory/.gitkeep
  # must exist and be exactly zero bytes (Story 1.1 scaffold contract).
  # (2) No sentinel files (.gitkeep / .keep / empty / placeholder) appear
  # anywhere at depth >= 2 under memory/ — the nine template files already
  # provide git-trackable content, so extra sentinels are a regression.
  local gitkeep="${MEMORY_DIR}/.gitkeep"
  [[ -f "${gitkeep}" ]] || fail "${gate}: AC9: ${gitkeep} missing"
  local gitkeep_size
  gitkeep_size="$(wc -c <"${gitkeep}" | tr -d '[:space:]')"
  [[ "${gitkeep_size}" == '0' ]] \
    || fail "${gate}: AC9: ${gitkeep} must be empty (0 bytes, found ${gitkeep_size})"
  local sentinel sentinel_hit
  for sentinel in .gitkeep .keep empty placeholder; do
    sentinel_hit="$(find "${MEMORY_DIR}" -mindepth 2 -name "${sentinel}" -type f 2>/dev/null | head -n 1 || true)"
    if [[ -n "${sentinel_hit}" ]]; then
      fail "${gate}: AC9: forbidden sentinel file under memory/*/*: ${sentinel_hit}"
    fi
  done

  # Nine files must all exist and be non-empty.
  local f
  for f in \
    "${MEETING_TEMPLATE}" \
    "${AGENDA_TEMPLATE}" \
    "${PREP_TEMPLATE}" \
    "${TRANSCRIPT_TEMPLATE}" \
    "${PEOPLE_TEMPLATE}" \
    "${DECISIONS_TEMPLATE}" \
    "${REFERENCE_TEMPLATE}" \
    "${INBOX_TEMPLATE}" \
    "${APPRECIATIONS_TEMPLATE}"; do
    require_file_exists "${f}" "${gate}"
    require_file_nonempty "${f}" "${gate}"
    # Trailing-newline check — every emitted template must end with `\n`.
    # Uses `tail -c 1` which is BSD + GNU compatible.
    local last_byte
    last_byte="$(tail -c 1 "${f}" | od -An -tx1 | tr -d ' \n')"
    [[ "${last_byte}" == '0a' ]] \
      || fail "${gate}: ${f} missing trailing newline (last byte: 0x${last_byte})"
  done

  # --- meeting.md frontmatter + headers + doc-link table -----------
  local meeting_fm
  meeting_fm="$(read_frontmatter "${MEETING_TEMPLATE}" "${gate}")"
  assert_frontmatter_keys "${meeting_fm}" "${gate}" "${MEETING_TEMPLATE}" \
    type date time attendees context location join_url organizer \
    recurring action_items created updated tags
  # Phase-4 F5 review fix — assert discriminator KEY:VALUE pairs, not just
  # key presence. `type: meeting` identifies this file as the meeting doc;
  # if present, `recurring: false` locks the boolean value.
  assert_frontmatter_key_value "${meeting_fm}" "${gate}" "${MEETING_TEMPLATE}" \
    type meeting
  if echo "${meeting_fm}" | grep -Eq '^recurring:'; then
    assert_frontmatter_key_value "${meeting_fm}" "${gate}" "${MEETING_TEMPLATE}" \
      recurring false
  fi
  # context: value must be empty-string (inline comment allowed, but value
  # itself is `""` — no personal enumeration).
  echo "${meeting_fm}" | grep -Eq '^context:[[:space:]]*""' \
    || fail "${gate}: ${MEETING_TEMPLATE} frontmatter 'context:' value must be \"\" (empty string)"
  require_exact_headers "${MEETING_TEMPLATE}" "${gate}" '# {{Meeting Title}}
## Summary
## Notes
## Decisions
## Action Items'
  # Doc-link table — three literal substrings (not whole-line anchored because
  # they appear inside a markdown table cell).
  grep -Fq '[prep.md](prep.md)' "${MEETING_TEMPLATE}" \
    || fail "${gate}: ${MEETING_TEMPLATE} missing doc-link '[prep.md](prep.md)'"
  grep -Fq '[agenda.md](agenda.md)' "${MEETING_TEMPLATE}" \
    || fail "${gate}: ${MEETING_TEMPLATE} missing doc-link '[agenda.md](agenda.md)'"
  grep -Fq '[transcript.md](transcript.md)' "${MEETING_TEMPLATE}" \
    || fail "${gate}: ${MEETING_TEMPLATE} missing doc-link '[transcript.md](transcript.md)'"

  # --- agenda.md (no frontmatter required) + headers + checkbox ----
  require_exact_headers "${AGENDA_TEMPLATE}" "${gate}" '# Agenda -- {{Meeting Title}}
## Topics
## Parking Lot'
  grep -Fq -- '- [ ] {{topic}} ({{owner}}, {{estimated minutes}})' "${AGENDA_TEMPLATE}" \
    || fail "${gate}: ${AGENDA_TEMPLATE} missing canonical checkbox '- [ ] {{topic}} ({{owner}}, {{estimated minutes}})'"

  # --- prep.md (no frontmatter required) + six H2 sections ---------
  require_exact_headers "${PREP_TEMPLATE}" "${gate}" '# Prep -- {{Meeting Title}}
## My Objectives
## Questions to Raise
## Attendee Context
## Prior Meeting History
## Related Tasks
## Commercial Context'

  # --- transcript.md (no frontmatter required) + header + bold labels + HR
  require_exact_headers "${TRANSCRIPT_TEMPLATE}" "${gate}" '# Transcript -- {{Meeting Title}}'
  grep -q '^\*\*Source:\*\*' "${TRANSCRIPT_TEMPLATE}" \
    || fail "${gate}: ${TRANSCRIPT_TEMPLATE} missing '**Source:**' bold-label line"
  grep -q '^\*\*Recording:\*\*' "${TRANSCRIPT_TEMPLATE}" \
    || fail "${gate}: ${TRANSCRIPT_TEMPLATE} missing '**Recording:**' bold-label line"
  # Exactly-one `---` horizontal-rule line AFTER the bold-label lines.
  # transcript.md has no YAML frontmatter, so any `^---$` is an HR.
  local hr_count
  hr_count="$(grep -c '^---$' "${TRANSCRIPT_TEMPLATE}" || true)"
  [[ "${hr_count}" -ge 1 ]] \
    || fail "${gate}: ${TRANSCRIPT_TEMPLATE} missing horizontal-rule '---' separator"

  # --- people/_template.md frontmatter + headers + overview bold labels
  local people_fm
  people_fm="$(read_frontmatter "${PEOPLE_TEMPLATE}" "${gate}")"
  assert_frontmatter_keys "${people_fm}" "${gate}" "${PEOPLE_TEMPLATE}" \
    type company role email last_1on1 open_action_items created updated tags
  # Phase-4 F5 review fix — `type: person` is the discriminator.
  assert_frontmatter_key_value "${people_fm}" "${gate}" "${PEOPLE_TEMPLATE}" \
    type person
  require_exact_headers "${PEOPLE_TEMPLATE}" "${gate}" '# {{Name}}
## Overview
## 1-on-1 History
## Action Items
## Notes'
  local label
  for label in '**Company**' '**Role**' '**Reports to**' '**Direct reports**'; do
    grep -Fq "${label}" "${PEOPLE_TEMPLATE}" \
      || fail "${gate}: ${PEOPLE_TEMPLATE} missing '## Overview' bold-label line: ${label}"
  done

  # --- decisions/_template.md frontmatter + headers + H3 options ---
  local decisions_fm
  decisions_fm="$(read_frontmatter "${DECISIONS_TEMPLATE}" "${gate}")"
  assert_frontmatter_keys "${decisions_fm}" "${gate}" "${DECISIONS_TEMPLATE}" \
    type status date context stakeholders created updated tags
  # Phase-4 F5 review fix — `type: decision` + `status: open` are both
  # discriminators; assert both.
  assert_frontmatter_key_value "${decisions_fm}" "${gate}" "${DECISIONS_TEMPLATE}" \
    type decision
  assert_frontmatter_key_value "${decisions_fm}" "${gate}" "${DECISIONS_TEMPLATE}" \
    status open
  require_exact_headers "${DECISIONS_TEMPLATE}" "${gate}" '# {{Decision Title}}
## Context
## Alternatives
### Option A: {{name}}
### Option B: {{name}}
## Decision
## Rationale
## Implications'

  # --- reference/_template.md frontmatter + headers ----------------
  local reference_fm
  reference_fm="$(read_frontmatter "${REFERENCE_TEMPLATE}" "${gate}")"
  assert_frontmatter_keys "${reference_fm}" "${gate}" "${REFERENCE_TEMPLATE}" \
    type created updated context related_to tags
  # Phase-4 F5 review fix — `type: reference` is the discriminator.
  assert_frontmatter_key_value "${reference_fm}" "${gate}" "${REFERENCE_TEMPLATE}" \
    type reference
  require_exact_headers "${REFERENCE_TEMPLATE}" "${gate}" '# {{Reference Title}}
## Summary
## Details
## Links
## Related notes'

  # --- inbox/_template.md frontmatter + header + Defect #3 repair --
  local inbox_fm
  inbox_fm="$(read_frontmatter "${INBOX_TEMPLATE}" "${gate}")"
  assert_frontmatter_keys "${inbox_fm}" "${gate}" "${INBOX_TEMPLATE}" \
    type created context tags
  # Phase-4 F5 review fix — `type: inbox` is the discriminator.
  assert_frontmatter_key_value "${inbox_fm}" "${gate}" "${INBOX_TEMPLATE}" \
    type inbox
  # Defect #3 repair assertion — `context:` value MUST be empty-string
  # (source had `context: vixxo | revivago | personal` as a VALUE).
  echo "${inbox_fm}" | grep -Eq '^context:[[:space:]]*""' \
    || fail "${gate}: ${INBOX_TEMPLATE} frontmatter 'context:' value must be \"\" (Defect #3 repair)"
  require_exact_headers "${INBOX_TEMPLATE}" "${gate}" '# Thought'

  # --- appreciations/_template.md REPAIRED frontmatter + headers ---
  # Defect #1: source opens `---` then writes `## type: appreciation` as an
  # H2 heading. Port MUST emit `type: appreciation` as a YAML key AND MUST
  # NOT contain the H2 heading form anywhere.
  local appreciations_fm
  appreciations_fm="$(read_frontmatter "${APPRECIATIONS_TEMPLATE}" "${gate}")"
  assert_frontmatter_keys "${appreciations_fm}" "${gate}" "${APPRECIATIONS_TEMPLATE}" \
    type date recipient context tags
  # Phase-4 F5 review fix — `type: appreciation` is the discriminator and
  # doubles as the Defect #1 semantic repair proof (H2-heading form forbidden
  # + YAML-key form required).
  assert_frontmatter_key_value "${appreciations_fm}" "${gate}" "${APPRECIATIONS_TEMPLATE}" \
    type appreciation
  # "Repaired, not copied" assertion — the H2 heading form of the defect
  # must not appear anywhere in the emitted file.
  if grep -Fxq '## type: appreciation' "${APPRECIATIONS_TEMPLATE}"; then
    fail "${gate}: ${APPRECIATIONS_TEMPLATE} contains Defect #1 H2 heading '## type: appreciation' (must be YAML key, not heading)"
  fi
  require_exact_headers "${APPRECIATIONS_TEMPLATE}" "${gate}" '# {{Recipient or Moment}}
## What
## Why it mattered'
}

# ------------------------------------------------------------------
# task4 — cross-file scrub: banned terms + placeholders + forbidden forms
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  # Invoke the probe once per run to guard against a mis-parsing host grep
  # before we execute the real cross-file scans.
  regex_self_probe

  local files="${MEETING_TEMPLATE}
${AGENDA_TEMPLATE}
${PREP_TEMPLATE}
${TRANSCRIPT_TEMPLATE}
${PEOPLE_TEMPLATE}
${DECISIONS_TEMPLATE}
${REFERENCE_TEMPLATE}
${INBOX_TEMPLATE}
${APPRECIATIONS_TEMPLATE}"

  local f hit
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue

    # Banned-term scan — boundary-guarded, case-insensitive.
    if hit="$(grep -inE "${BANNED_TERMS_REGEX}" "${f}" 2>/dev/null || true)" && [[ -n "${hit}" ]]; then
      echo "${hit}" >&2
      fail "${gate}: ${f} contains a banned token (boundary-guarded regex hit)"
    fi

    # Fixed-string `gtd-life` scan (defense-in-depth against hyphenated
    # path references — hyphen is not an alpha, so the boundary-guarded
    # regex already catches `gtd-life`, but this is a second layer).
    if grep -Fq 'gtd-life' "${f}"; then
      fail "${gate}: ${f} contains literal path reference 'gtd-life'"
    fi
    if grep -Fq '~/Public/gtd-life' "${f}"; then
      fail "${gate}: ${f} contains source-repo filesystem path '~/Public/gtd-life'"
    fi
    if grep -Fq '/gtd-life/' "${f}"; then
      fail "${gate}: ${f} contains embedded source-repo path '/gtd-life/'"
    fi

    # Placeholder-vocabulary allowlist enforcement. Extract every
    # `{{...}}` token; every extracted token must appear in the allowlist.
    local token
    while IFS= read -r token; do
      [[ -z "${token}" ]] && continue
      if ! echo "${PLACEHOLDER_ALLOWLIST}" | grep -Fxq "${token}"; then
        fail "${gate}: ${f} contains disallowed placeholder: ${token}"
      fi
    done < <(grep -oE '\{\{[^}]+\}\}' "${f}" 2>/dev/null | sort -u || true)

    # Forbidden specific identity-placeholder names (even in `{{...}}` form)
    # — these belong to Stories 2.1 / 2.3 / 3.3, not memory-vault templates.
    local forbidden_name
    for forbidden_name in \
      '{{employee_name}}' \
      '{{employee_role}}' \
      '{{employee_department}}' \
      '{{employee_manager}}' \
      '{{employee_email}}'; do
      if grep -Fq "${forbidden_name}" "${f}"; then
        fail "${gate}: ${f} contains forbidden identity placeholder: ${forbidden_name} (identity placeholders belong in agent-identity.mdc / work.md / memory/me/identity.md, not memory templates)"
      fi
    done

    # Forbidden single-brace `{placeholder}` form. Match a `{` that is NOT
    # preceded by `{` and NOT followed by `{`, with a non-`}` body, and
    # closed by `}` not followed by `}`. Avoids matching `{{...}}`.
    if grep -Eq '(^|[^{])\{[^{}][^}]*\}([^}]|$)' "${f}"; then
      # Double-check: the above pattern could in theory touch the inner
      # braces of `{{ x }}` on some grep versions. Re-scan by stripping
      # `{{...}}` and then looking for any residual `{...}`.
      local stripped
      stripped="$(sed -e 's/{{[^}]*}}//g' "${f}")"
      if echo "${stripped}" | grep -Eq '\{[^{}]+\}'; then
        fail "${gate}: ${f} contains forbidden single-brace '{placeholder}' form"
      fi
    fi

    # Forbidden angle-bracket `<placeholder>` form. Targets tokens of the
    # form `<NAME>` where NAME starts with a letter — does NOT match
    # HTML comments `<!-- -->` (starts with `!`, not a letter).
    if grep -Eq '<[A-Za-z][A-Za-z0-9_-]*>' "${f}"; then
      fail "${gate}: ${f} contains forbidden angle-bracket '<placeholder>' form"
    fi

    # Forbidden percent-wrapped `%placeholder%` form.
    if grep -Eq '%[A-Za-z][A-Za-z0-9_]*%' "${f}"; then
      fail "${gate}: ${f} contains forbidden percent-wrapped '%placeholder%' form"
    fi

    # Forbidden dollar-brace `${placeholder}` form.
    if grep -Eq '\$\{[^}]+\}' "${f}"; then
      fail "${gate}: ${f} contains forbidden dollar-brace '\${placeholder}' form"
    fi

  done <<EOF
${files}
EOF
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
    'MEETINGS_TEMPLATE_DIR=' \
    'MEETING_TEMPLATE=' \
    'AGENDA_TEMPLATE=' \
    'PREP_TEMPLATE=' \
    'TRANSCRIPT_TEMPLATE=' \
    'PEOPLE_TEMPLATE=' \
    'DECISIONS_TEMPLATE=' \
    'REFERENCE_TEMPLATE=' \
    'INBOX_TEMPLATE=' \
    'APPRECIATIONS_TEMPLATE=' \
    'BASELINE_AUDIT_PATH=' \
    'BLUEPRINT_PATH=' \
    'STORY_1_1_HARNESS=' \
    'STORY_1_2_HARNESS=' \
    'STORY_1_3_HARNESS=' \
    'STORY_2_1_HARNESS=' \
    'STORY_2_2_HARNESS=' \
    'STORY_2_3_HARNESS=' \
    'STORY_2_4_HARNESS=' \
    'BANNED_TERMS_REGEX=' \
    'PLACEHOLDER_ALLOWLIST='; do
    grep -Fq "${required_const}" "${SELF_PATH}" \
      || fail "${gate}: harness missing constant: ${required_const}"
  done

  # Story 2.4 F4 review fix — probe-presence idiom via `declare -F` so a
  # commented-out or deleted function body cannot satisfy the gate.
  declare -F regex_self_probe >/dev/null 2>&1 \
    || fail "${gate}: harness missing regex_self_probe function definition"
}

# ------------------------------------------------------------------
# task6 — regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 harnesses
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

  # Phase-4 F7 review fix — fingerprint the expected number of `^PASS:`
  # lines each sub-harness emits under `all` mode. A divergence (e.g. a
  # sub-harness silently losing a gate) is caught before the aggregate-exit
  # check masks it. Empirically measured on 2026-04-20 via
  # `bash <harness> all | grep -c '^PASS:'`.
  local out pass_count expected_pass
  # Arg tuple: "HARNESS_PATH|display_name|expected_pass_count".
  local -a regressions=(
    "${STORY_1_1_HARNESS}|story-1-1-scaffold-validation.sh|1"
    "${STORY_1_2_HARNESS}|story-1-2-root-files-validation.sh|1"
    "${STORY_1_3_HARNESS}|story-1-3-root-context-validation.sh|1"
    "${STORY_2_1_HARNESS}|story-2-1-agent-identity-validation.sh|1"
    "${STORY_2_2_HARNESS}|story-2-2-guardrail-and-formatting-validation.sh|10"
    "${STORY_2_3_HARNESS}|story-2-3-work-persona-validation.sh|7"
    "${STORY_2_4_HARNESS}|story-2-4-benji-inbox-absence-validation.sh|7"
  )
  local rec path name
  for rec in "${regressions[@]}"; do
    path="${rec%%|*}"
    rec="${rec#*|}"
    name="${rec%|*}"
    expected_pass="${rec##*|}"
    # Story 2.2 Phase 4 F6 pattern — capture combined stdout/stderr and
    # echo on non-zero exit.
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
