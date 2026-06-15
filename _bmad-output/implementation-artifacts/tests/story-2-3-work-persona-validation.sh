#!/usr/bin/env bash
set -euo pipefail

# Story 2.3 — Create single generic `agents/personas/work.md` — deterministic validation harness.
#
# Gates:
#   task1  baseline-audit evidence (_bmad-output/implementation-artifacts/tests/story-2-3-baseline-audit.md)
#   task2  canonical-blueprint evidence (_bmad-output/implementation-artifacts/tests/story-2-3-canonical-blueprint.md)
#   task3  persona-file shape: file exists + frontmatter keys/values + required headers + MCP table shape
#   task4  cross-file scrub: banned terms + placeholder parity + deferred-content guards + voice-biography absence + email-pattern absence + sibling-persona absence + why-comment terminator + active/banned MCP tokens + M365-only routing
#   task5  self-check: harness well-formed (shebang, set -euo pipefail, case branches, regex + headers + paths defined, regex_self_probe present)
#   task6  regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 harnesses (bash <harness> all must exit 0)
#   all    runs every gate in order
#
# Invocation: bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays). Uses only bash, grep, awk, sed.
# NOTE: ripgrep (rg) is intentionally not used — `grep -i -E` is the portable scanner here.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

STORY_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md"
BASELINE_AUDIT_PATH="${TESTS_DIR}/story-2-3-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-2-3-canonical-blueprint.md"

PERSONAS_DIR="${PROJECT_ROOT}/agents/personas"
PERSONA_PATH="${PERSONAS_DIR}/work.md"
AGENT_IDENTITY_PATH="${PROJECT_ROOT}/.cursor/rules/agent-identity.mdc"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"
STORY_2_2_HARNESS="${TESTS_DIR}/story-2-2-guardrail-and-formatting-validation.sh"

# Required section headers for `agents/personas/work.md` (Task 2 blueprint lock).
PERSONA_HEADERS="\
# Work Persona
## Role
## Responsibilities
## Available MCPs
## Email
## Calendar
## Task System
## Communication Tone
## Context Files"

# Active MCP tokens that MUST appear (bold-wrapped, exactly once each) in the
# `## Available MCPs` section (AC3).
ACTIVE_MCP_TOKENS="\
**Linear**
**GitHub**
**Microsoft 365**
**Salesforce**
**Gong**"

# Forbidden MCP tokens that MUST NOT appear anywhere in the persona body
# (AC3 negative assertion).
BANNED_MCP_TOKENS="\
**Slack**
**Notion**
**Gmail**
**Google Calendar**
**Google Workspace**
**Google Drive**
**Flowtopic**
**Benji**
**Benji.so**
**Obsidian**
**Freshdesk**
**Dynamics**
**VixxoNow**
**VixxoLink**
**Gateway**
**ZoomInfo**
**HubSpot**
**AWS Connect**
**ChatFPT**
**Elastic**
**Introspection**"

# Context Files bullet list — six paths in locked order (AC7).
CONTEXT_FILES_BULLETS="\
- \`.cursor/rules/agent-identity.mdc\`
- \`memory/me/identity.md\`
- \`memory/me/preferences.md\`
- \`AGENTS.md\`
- \`CLAUDE.md\`
- \`.cursorrules\`"

# Case-insensitive banned-term regex. Reuses the Story 2.2 POSIX-ERE pattern and
# extends the alternation with the Story 2.3 persona-specific additions. Short
# substrings (`deke`, `ASU`, `arete`, `eudaimonia`, `blog`, `slack`, `benji`,
# `family`) use POSIX-ERE non-letter boundaries instead of GNU `\b` so the scan
# behaves identically under macOS BSD grep, GNU grep, and busybox/Alpine grep.
# A fail-fast probe below rejects any host whose grep interprets these patterns
# incorrectly.
BANNED_TERMS_REGEX='(^|[^A-Za-z])derek($|[^A-Za-z])|(^|[^A-Za-z])deke($|[^A-Za-z])|neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|(^|[^A-Za-z])ASU($|[^A-Za-z])|gtd-life|(^|[^A-Za-z])arete($|[^A-Za-z])|(^|[^A-Za-z])eudaimonia($|[^A-Za-z])|(^|[^A-Za-z])blog($|[^A-Za-z])|gmail|google calendar|google workspace|google drive|google chat|personal email|(^|[^A-Za-z])slack($|[^A-Za-z])|(^|[^A-Za-z])benji($|[^A-Za-z])|notion|flowtopic|veincraft|daddy bootcamps|after the stork|peptide|(^|[^A-Za-z])family($|[^A-Za-z])|laurie|bobby hunnicutt|brandon franz|eric burt|gino flores|viswa vadlamani|jignesh patel|jim reavey'

# Voice-biography absence regex (AC6). The persona must NOT restate Derek's
# voice directives or name specific-human voice biography phrasing.
VOICE_BIOGRAPHY_REGEX='### Voice Directives|(^|[^A-Za-z])NVC($|[^A-Za-z])|Non-Violent Communication|Lift people up|Bias to action'

# M365-only routing: the `## Email`, `## Calendar`, `## Task System` sections
# must NOT reference these non-Vixxo stacks.
NON_M365_ROUTING_REGEX='gmail|google calendar|google workspace|google drive|outlook\.com|personal email|(^|[^A-Za-z])sms($|[^A-Za-z])|imessage'

# AC4 — additional sensitive-data patterns that MUST NOT appear in the persona:
# phone numbers, Microsoft Graph UPN/user-ID GUIDs, and Teams chatId tokens.
EMAIL_PATTERN_REGEX='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
PHONE_PATTERN_REGEX='(\+?1[-. ]?)?\(?[0-9]{3}\)?[-. ][0-9]{3}[-. ][0-9]{4}'
GUID_PATTERN_REGEX='[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
TEAMS_CHATID_REGEX='19:[A-Za-z0-9._-]+@thread\.(v2|tacv2|skype)'

# Allowed placeholder tokens across the persona body (Story 1.3 + 2.1 + 2.2 set;
# no new tokens introduced by Story 2.3).
ALLOWED_PLACEHOLDERS="\
{{employee_name}}
{{employee_role}}
{{employee_department}}
{{employee_manager}}"

# Cross-pack placeholder parity file set — root context files + full Story 2.x
# rule pack + new Story 2.3 persona. Every discovered `{{snake_case}}` token in
# any of these files must appear in ALLOWED_PLACEHOLDERS. This closes the
# Task 4 cross-pack parity commitment (previously only the persona file was
# scanned).
PARITY_FILES="\
AGENTS.md
CLAUDE.md
.cursorrules
.cursor/rules/agent-identity.mdc
.cursor/rules/outbound-messaging-guardrail.mdc
.cursor/rules/memory-vault-protection.mdc
.cursor/rules/teams-dm-formatting.mdc
.cursor/rules/email-triage-thread-defaults.mdc
agents/personas/work.md"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_file_exists() {
  local path="$1"
  local gate="$2"
  [[ -f "${path}" ]] || fail "${gate}: missing file ${path}"
}

# Fail fast if the host grep mis-parses the POSIX-ERE boundary patterns above.
# Extends Story 2.2's probe with `family` (Story 2.3 addition).
regex_self_probe() {
  # derek boundary probe (Story 2.3 — derek moved into boundary-guarded group
  # to match the Task 4 subtask spec `(^|[^A-Za-z])(derek|deke|...)(...)`).
  echo "derekolor" | grep -iE '(^|[^A-Za-z])derek($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: derek boundary match admitted 'derekolor' (grep too permissive)"
  echo "hey Derek" | grep -iE '(^|[^A-Za-z])derek($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: derek boundary match rejected legitimate hit 'hey Derek' (grep too strict)"

  # ASU boundary probe (Story 2.1 inheritance).
  echo "XASUX" | grep -iE '(^|[^A-Za-z])ASU($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: ASU boundary match admitted embedded 'XASUX' (grep too permissive)"
  echo "ASU test" | grep -iE '(^|[^A-Za-z])ASU($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: ASU boundary match rejected legitimate hit 'ASU test' (grep too strict)"

  # blog boundary probe (Story 2.1 inheritance).
  echo "blogger" | grep -iE '(^|[^A-Za-z])blog($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: blog boundary match admitted 'blogger' (grep too permissive)"
  echo "my blog" | grep -iE '(^|[^A-Za-z])blog($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: blog boundary match rejected legitimate hit 'my blog' (grep too strict)"

  # deke boundary probe (Story 2.1 inheritance).
  echo "dekerate" | grep -iE '(^|[^A-Za-z])deke($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: deke boundary match admitted 'dekerate' (grep too permissive)"
  echo "hey deke" | grep -iE '(^|[^A-Za-z])deke($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: deke boundary match rejected legitimate hit 'hey deke' (grep too strict)"

  # arete boundary probe (Story 2.1 inheritance).
  echo "pareto" | grep -iE '(^|[^A-Za-z])arete($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: arete boundary match admitted 'pareto' (grep too permissive)"
  echo "the arete path" | grep -iE '(^|[^A-Za-z])arete($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: arete boundary match rejected legitimate hit 'the arete path' (grep too strict)"

  # eudaimonia boundary probe (Story 2.1 inheritance).
  echo "xeudaimoniax" | grep -iE '(^|[^A-Za-z])eudaimonia($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: eudaimonia boundary match admitted 'xeudaimoniax' (grep too permissive)"
  echo "eudaimonia here" | grep -iE '(^|[^A-Za-z])eudaimonia($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: eudaimonia boundary match rejected legitimate hit 'eudaimonia here' (grep too strict)"

  # slack boundary probe (Story 2.2 addition).
  echo "slackened" | grep -iE '(^|[^A-Za-z])slack($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: slack boundary match admitted 'slackened' (grep too permissive)"
  echo "no slack here" | grep -iE '(^|[^A-Za-z])slack($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: slack boundary match rejected legitimate hit 'no slack here' (grep too strict)"

  # benji boundary probe (Story 2.2 addition).
  echo "benjiman" | grep -iE '(^|[^A-Za-z])benji($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: benji boundary match admitted 'benjiman' (grep too permissive)"
  echo "benji inbox" | grep -iE '(^|[^A-Za-z])benji($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: benji boundary match rejected legitimate hit 'benji inbox' (grep too strict)"

  # family boundary probe (Story 2.3 addition).
  echo "familiar" | grep -iE '(^|[^A-Za-z])family($|[^A-Za-z])' >/dev/null \
    && fail "regex probe: family boundary match admitted 'familiar' (grep too permissive)"
  echo "my family" | grep -iE '(^|[^A-Za-z])family($|[^A-Za-z])' >/dev/null \
    || fail "regex probe: family boundary match rejected legitimate hit 'my family' (grep too strict)"
}

# Print the last non-blank line of a file.
last_non_blank_line() {
  awk 'NF{ last=$0 } END{ print last }' "$1"
}

# Assert a file's last non-blank line is a one-line "why" comment in one of
# the approved forms: HTML comment (`<!-- ... -->`), markdown blockquote
# (`> ...`), or markdown italic single line (`_..._`). Reuses the Story 2.2
# Phase-4 form (`grep -Eq` with literal `<` / `>`, not bash `[[ =~ \<...\> ]]`).
require_why_comment_terminator() {
  local path="$1"
  local gate="$2"

  local last
  last="$(last_non_blank_line "${path}")"
  if echo "${last}" | grep -Eq '^<!--.*-->$'; then
    :
  elif echo "${last}" | grep -Eq '^>.*$'; then
    :
  elif echo "${last}" | grep -Eq '^_.*_$'; then
    :
  else
    fail "${gate}: ${path} last non-blank line is not a one-line why comment: ${last}"
  fi

  if echo "${last}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "${gate}: ${path} why comment contains banned term: ${last}"
  fi
}

# Parse the YAML frontmatter block between the first two `---` delimiters.
# Requires the opening `---` to be on line 1 and a matching closing `---` to
# appear strictly after. Prints the frontmatter body to stdout.
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

# Assert every line in a heredoc block appears as an exact-line match in the
# given file (grep -Fxq). Blank lines are skipped.
require_exact_headers() {
  local path="$1"
  local gate="$2"
  local headers_blob="$3"

  local header
  while IFS= read -r header; do
    [[ -z "${header}" ]] && continue
    grep -Fxq "${header}" "${path}" \
      || fail "${gate}: ${path} missing required section header (exact line): ${header}"
  done <<EOF
${headers_blob}
EOF
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq "Story 2.3 Baseline Audit" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title"

  local section
  for section in "vixxo-cto.md" "revivago-ceo.md" "personal.md" \
                 "banned-term set" "Active-MCP lock" "Source-to-target collapse map"; do
    grep -Fiq "${section}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing required section/keyword: ${section}"
  done

  # Every persona-specific Story 2.3 addition recorded (supplement to the
  # Story 2.1 / 2.2 carryover already referenced in the audit body).
  local term
  for term in Notion Flowtopic VeinCraft "Daddy Bootcamps" "After the Stork" \
              peptide family Laurie "Bobby Hunnicutt" "Brandon Franz" \
              "Eric Burt" "Gino Flores" "Viswa Vadlamani" "Jignesh Patel" \
              "Jim Reavey"; do
    grep -Fq "${term}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing Story 2.3 banned-term addition: ${term}"
  done

  # Active-MCP lock records the five Vixxo-active MCPs.
  local mcp
  for mcp in Linear GitHub "Microsoft 365" Salesforce Gong; do
    grep -Fq "${mcp}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing active-MCP entry: ${mcp}"
  done
}

# ------------------------------------------------------------------
# task2 — canonical-blueprint evidence present and complete
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq "Story 2.3 Canonical Blueprint" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title"

  # Every locked section header is referenced in the blueprint.
  local header
  while IFS= read -r header; do
    [[ -z "${header}" ]] && continue
    grep -Fq "${header}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing locked section header reference: ${header}"
  done <<EOF
${PERSONA_HEADERS}
EOF

  # Frontmatter key locks referenced.
  local key
  for key in "type: persona" "scope: work" "role: \"{{employee_role}}\"" \
             "department: \"{{employee_department}}\"" \
             "name: \"{{employee_name}}\"" \
             "manager: \"{{employee_manager}}\"" \
             "tags: [persona, work, vixxo]"; do
    grep -Fq "${key}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing frontmatter lock: ${key}"
  done

  # Active-MCP tokens referenced.
  local tok
  while IFS= read -r tok; do
    [[ -z "${tok}" ]] && continue
    grep -Fq "${tok}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing active-MCP token: ${tok}"
  done <<EOF
${ACTIVE_MCP_TOKENS}
EOF

  # Routing one-liners locked.
  local line
  for line in "Microsoft 365 (Outlook)." \
              "Microsoft 365 (Outlook calendar)." \
              "Linear (Vixxo work task system)."; do
    grep -Fq "${line}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing routing lock: ${line}"
  done

  # Placeholder inventory locked to Story 1.3 + 2.1 + 2.2 set.
  local ph
  for ph in '{{employee_name}}' '{{employee_role}}' '{{employee_department}}' '{{employee_manager}}'; do
    grep -Fq "${ph}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing placeholder: ${ph}"
  done

  # Cross-AC coverage map present.
  grep -Fq "Cross-AC coverage map" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Cross-AC coverage map"
}

# ------------------------------------------------------------------
# task3 — persona-file shape: file exists + frontmatter + required headers + MCP table shape
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${PERSONA_PATH}" "${gate}"

  # File must be non-empty (AC1 — no zero-byte placeholder).
  [[ -s "${PERSONA_PATH}" ]] \
    || fail "${gate}: ${PERSONA_PATH} is empty"

  # Frontmatter shape (AC2).
  local frontmatter
  frontmatter="$(read_frontmatter "${PERSONA_PATH}" "${gate}")"

  echo "${frontmatter}" | grep -Fxq 'type: persona' \
    || fail "${gate}: frontmatter missing exact line 'type: persona'"
  echo "${frontmatter}" | grep -Fxq 'scope: work' \
    || fail "${gate}: frontmatter missing exact line 'scope: work'"
  echo "${frontmatter}" | grep -Fxq 'role: "{{employee_role}}"' \
    || fail "${gate}: frontmatter missing exact line 'role: \"{{employee_role}}\"'"
  echo "${frontmatter}" | grep -Fxq 'department: "{{employee_department}}"' \
    || fail "${gate}: frontmatter missing exact line 'department: \"{{employee_department}}\"'"
  echo "${frontmatter}" | grep -Fxq 'name: "{{employee_name}}"' \
    || fail "${gate}: frontmatter missing exact line 'name: \"{{employee_name}}\"'"
  echo "${frontmatter}" | grep -Fxq 'manager: "{{employee_manager}}"' \
    || fail "${gate}: frontmatter missing exact line 'manager: \"{{employee_manager}}\"'"
  echo "${frontmatter}" | grep -Fxq 'tags: [persona, work, vixxo]' \
    || fail "${gate}: frontmatter missing exact line 'tags: [persona, work, vixxo]'"

  # No forbidden frontmatter keys (the gtd-life donors used `company:` — must
  # be replaced by `scope: work` + the `vixxo` tag).
  if echo "${frontmatter}" | grep -Eq '^company:'; then
    fail "${gate}: frontmatter contains forbidden 'company:' key (use scope: work + vixxo tag)"
  fi

  # Required section headers (AC1, AC3, AC5, AC6, AC7).
  require_exact_headers "${PERSONA_PATH}" "${gate}" "${PERSONA_HEADERS}"

  # Active-MCP table positive assertion (AC3).
  local tok count
  while IFS= read -r tok; do
    [[ -z "${tok}" ]] && continue
    count="$(grep -oF "${tok}" "${PERSONA_PATH}" | wc -l | tr -d ' ')"
    if [[ "${count}" -ne 1 ]]; then
      fail "${gate}: persona MCP table must contain ${tok} exactly once (got ${count})"
    fi
  done <<EOF
${ACTIVE_MCP_TOKENS}
EOF

  # MCP table header shape — `| MCP | Purpose |` must appear exactly once.
  local hdr_count
  hdr_count="$(grep -cF '| MCP | Purpose |' "${PERSONA_PATH}" || true)"
  if [[ "${hdr_count}" -ne 1 ]]; then
    fail "${gate}: persona MCP table header '| MCP | Purpose |' must appear exactly once (got ${hdr_count})"
  fi

  # Context Files bullet list — six bullets in locked order (AC7).
  local bullet
  while IFS= read -r bullet; do
    [[ -z "${bullet}" ]] && continue
    grep -Fxq -- "${bullet}" "${PERSONA_PATH}" \
      || fail "${gate}: persona Context Files missing bullet (exact line): ${bullet}"
  done <<EOF
${CONTEXT_FILES_BULLETS}
EOF
}

# ------------------------------------------------------------------
# task4 — cross-file scrub: banned terms + placeholder parity + deferred-content guards + voice-biography absence + email-pattern absence + sibling-persona absence + why-comment terminator + routing + banned-MCP tokens
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${PERSONA_PATH}" "${gate}"

  regex_self_probe

  # AC4 — banned-term scrub over the persona body.
  local hit
  hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${PERSONA_PATH}" || true)"
  if [[ -n "${hit}" ]]; then
    fail "${gate}: banned term(s) detected in ${PERSONA_PATH}: ${hit}"
  fi

  # AC4 — email-address pattern absence.
  if grep -E "${EMAIL_PATTERN_REGEX}" "${PERSONA_PATH}" >/dev/null; then
    fail "${gate}: persona contains an email-address pattern"
  fi

  # AC4 — phone-number pattern absence (common US/NANP formats).
  if grep -E "${PHONE_PATTERN_REGEX}" "${PERSONA_PATH}" >/dev/null; then
    fail "${gate}: persona contains a phone-number pattern"
  fi

  # AC4 — Microsoft Graph UPN / user-ID GUID pattern absence.
  if grep -E "${GUID_PATTERN_REGEX}" "${PERSONA_PATH}" >/dev/null; then
    fail "${gate}: persona contains a GUID pattern (Graph user id / UPN)"
  fi

  # AC4 — Teams chatId pattern absence (`19:<id>@thread.(v2|tacv2|skype)`).
  if grep -E "${TEAMS_CHATID_REGEX}" "${PERSONA_PATH}" >/dev/null; then
    fail "${gate}: persona contains a Teams chatId pattern"
  fi

  # AC6 — voice-biography absence (no Derek-specific subsection, no NVC, etc.).
  if grep -iE "${VOICE_BIOGRAPHY_REGEX}" "${PERSONA_PATH}" >/dev/null; then
    fail "${gate}: persona contains forbidden voice-biography content (### Voice Directives / NVC / Lift people up / Bias to action)"
  fi

  # AC3 negative — no banned MCP tokens anywhere in the body.
  local banned_mcp
  while IFS= read -r banned_mcp; do
    [[ -z "${banned_mcp}" ]] && continue
    if grep -Fq "${banned_mcp}" "${PERSONA_PATH}"; then
      fail "${gate}: persona contains forbidden MCP token: ${banned_mcp}"
    fi
  done <<EOF
${BANNED_MCP_TOKENS}
EOF

  # AC5 — M365-only routing. The `## Email`, `## Calendar`, `## Task System`
  # sections must each reference the locked one-liner AND must NOT reference
  # any non-M365 / non-Vixxo stack.
  grep -Fq 'Microsoft 365 (Outlook).' "${PERSONA_PATH}" \
    || fail "${gate}: persona missing '## Email' one-liner 'Microsoft 365 (Outlook).'"
  grep -Fq 'Microsoft 365 (Outlook calendar).' "${PERSONA_PATH}" \
    || fail "${gate}: persona missing '## Calendar' one-liner 'Microsoft 365 (Outlook calendar).'"
  grep -Fq 'Linear (Vixxo work task system).' "${PERSONA_PATH}" \
    || fail "${gate}: persona missing '## Task System' one-liner 'Linear (Vixxo work task system).'"
  if grep -iE "${NON_M365_ROUTING_REGEX}" "${PERSONA_PATH}" >/dev/null; then
    fail "${gate}: persona references a non-M365 email/calendar/task stack"
  fi

  # AC7 — sibling-persona absence (explicit gtd-life donor filenames).
  local sibling
  for sibling in vixxo-cto.md revivago-ceo.md personal.md; do
    if [[ -e "${PERSONAS_DIR}/${sibling}" ]]; then
      fail "${gate}: sibling persona file must not exist: ${PERSONAS_DIR}/${sibling}"
    fi
  done

  # AC1 — generic sibling-persona absence. Enumerate `agents/personas/*.md`
  # and reject anything other than `work.md`. Closes the hardcoded-3-names
  # narrowness flagged in code review (F2).
  local entry
  for entry in "${PERSONAS_DIR}"/*.md; do
    [[ -e "${entry}" ]] || continue
    if [[ "${entry}" != "${PERSONAS_DIR}/work.md" ]]; then
      fail "${gate}: unexpected persona file: ${entry}"
    fi
  done

  # AC1 — `.gitkeep` sentinel remains zero-byte (Story 1.1 scaffold dependency;
  # if retained, it must not be a persona file or carry content).
  local gitkeep="${PERSONAS_DIR}/.gitkeep"
  if [[ -e "${gitkeep}" ]]; then
    [[ ! -s "${gitkeep}" ]] \
      || fail "${gate}: ${gitkeep} must remain zero-byte (Story 1.1 sentinel)"
  fi

  # AC7 — no `memory/companies/...` path leakage, no family/ventures/properties
  # paths, no sibling-persona file references in the body.
  local fb
  for fb in 'memory/companies/vixxo/' 'memory/companies/revivago/' \
            'memory/companies/blog/' 'memory/me/family.md' \
            'memory/me/ventures.md' 'memory/me/properties.md' \
            'agents/personas/vixxo-cto.md' 'agents/personas/revivago-ceo.md' \
            'agents/personas/personal.md'; do
    if grep -Fq "${fb}" "${PERSONA_PATH}"; then
      fail "${gate}: persona references forbidden path: ${fb}"
    fi
  done

  # AC7 zero-edit verification — identity rule still references the persona.
  require_file_exists "${AGENT_IDENTITY_PATH}" "${gate}"
  grep -Fq 'agents/personas/work.md' "${AGENT_IDENTITY_PATH}" \
    || fail "${gate}: .cursor/rules/agent-identity.mdc no longer references agents/personas/work.md"

  # Deferred-content guard — the persona must NOT restate both identity tokens
  # `Vixxo employee` and `work context only` (those belong to agent-identity.mdc).
  local has_vix has_wco
  has_vix=0
  has_wco=0
  grep -Fq 'Vixxo employee' "${PERSONA_PATH}" && has_vix=1
  grep -Fq 'work context only' "${PERSONA_PATH}" && has_wco=1
  if [[ "${has_vix}" -eq 1 && "${has_wco}" -eq 1 ]]; then
    fail "${gate}: persona duplicates agent-identity.mdc identity block (both 'Vixxo employee' and 'work context only' present)"
  fi

  # AC8 — last non-blank line is a scrubbed "why" comment.
  require_why_comment_terminator "${PERSONA_PATH}" "${gate}"

  # Outbound-rule pointer present (AC6).
  grep -Fq '.cursor/rules/outbound-messaging-guardrail.mdc' "${PERSONA_PATH}" \
    || fail "${gate}: persona missing pointer to .cursor/rules/outbound-messaging-guardrail.mdc"

  # Cross-pack placeholder parity — every `{{snake_case}}` token discovered in
  # the persona body AND in the sibling rule pack / root context files must
  # belong to the Story 1.3 + 2.1 + 2.2 allowlist. Story 2.3 introduces no new
  # tokens; a new token showing up here means a future edit drifted parity.
  local parity_file parity_path found ph_token known allowed
  while IFS= read -r parity_file; do
    [[ -z "${parity_file}" ]] && continue
    parity_path="${PROJECT_ROOT}/${parity_file}"
    require_file_exists "${parity_path}" "${gate}"
    found="$( { grep -oE '\{\{[a-z_]+\}\}' "${parity_path}" || true; } | sort -u )"
    while IFS= read -r ph_token; do
      [[ -z "${ph_token}" ]] && continue
      known=0
      while IFS= read -r allowed; do
        [[ -z "${allowed}" ]] && continue
        if [[ "${ph_token}" == "${allowed}" ]]; then
          known=1
          break
        fi
      done <<EOF
${ALLOWED_PLACEHOLDERS}
EOF
      if [[ "${known}" -ne 1 ]]; then
        fail "${gate}: unapproved placeholder token ${ph_token} in ${parity_file}"
      fi
    done <<EOF
${found}
EOF
  done <<EOF
${PARITY_FILES}
EOF
}

# ------------------------------------------------------------------
# task5 — self-check: harness is well-formed and owns the full gate set
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

  grep -Fq 'BANNED_TERMS_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing BANNED_TERMS_REGEX definition"
  grep -Fq 'VOICE_BIOGRAPHY_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing VOICE_BIOGRAPHY_REGEX definition"
  grep -Fq 'NON_M365_ROUTING_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing NON_M365_ROUTING_REGEX definition"
  grep -Fq 'PERSONA_HEADERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing PERSONA_HEADERS definition"
  grep -Fq 'ACTIVE_MCP_TOKENS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing ACTIVE_MCP_TOKENS definition"
  grep -Fq 'BANNED_MCP_TOKENS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing BANNED_MCP_TOKENS definition"
  grep -Fq 'CONTEXT_FILES_BULLETS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing CONTEXT_FILES_BULLETS definition"
  grep -Fq 'ALLOWED_PLACEHOLDERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing ALLOWED_PLACEHOLDERS definition"
  grep -Fq 'PARITY_FILES=' "${SELF_PATH}" \
    || fail "${gate}: harness missing PARITY_FILES definition (cross-pack parity)"
  grep -Fq 'EMAIL_PATTERN_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing EMAIL_PATTERN_REGEX definition"
  grep -Fq 'PHONE_PATTERN_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing PHONE_PATTERN_REGEX definition"
  grep -Fq 'GUID_PATTERN_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing GUID_PATTERN_REGEX definition"
  grep -Fq 'TEAMS_CHATID_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing TEAMS_CHATID_REGEX definition"
  grep -Fq 'PERSONA_PATH=' "${SELF_PATH}" \
    || fail "${gate}: harness missing PERSONA_PATH definition"

  grep -Fq 'regex_self_probe' "${SELF_PATH}" \
    || fail "${gate}: harness missing regex_self_probe function"
  grep -Fq 'require_why_comment_terminator' "${SELF_PATH}" \
    || fail "${gate}: harness missing require_why_comment_terminator helper"
}

# ------------------------------------------------------------------
# task6 — regression against Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 harnesses
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  require_file_exists "${STORY_1_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_2_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_3_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_2_HARNESS}" "${gate}"

  local out
  if ! out="$(bash "${STORY_1_1_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-1-1-scaffold-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_1_2_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-1-2-root-files-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_1_3_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-1-3-root-context-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_2_1_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-2-1-agent-identity-validation.sh all returned non-zero"
  fi
  if ! out="$(bash "${STORY_2_2_HARNESS}" all 2>&1)"; then
    echo "${out}" >&2
    fail "${gate}: story-2-2-guardrail-and-formatting-validation.sh all returned non-zero"
  fi
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
