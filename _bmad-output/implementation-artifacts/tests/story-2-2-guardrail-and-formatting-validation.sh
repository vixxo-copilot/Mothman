#!/usr/bin/env bash
set -euo pipefail

# Story 2.2 — Port guardrail and formatting rules — deterministic validation harness.
#
# Gates:
#   task1  baseline-audit-evidence (_bmad-output/implementation-artifacts/tests/story-2-2-baseline-audit.md)
#   task2  canonical-blueprint-evidence (_bmad-output/implementation-artifacts/tests/story-2-2-canonical-blueprint.md)
#   task3  outbound-messaging-guardrail.mdc: file + frontmatter + required headers + cross-refs + signing convention + deferred-content guards
#   task4  memory-vault-protection.mdc: file + frontmatter (globs: memory/**) + required headers + Epic 3 memory-path enumeration
#   task5  teams-dm-formatting.mdc: file + frontmatter + required headers + "contentType": "html" exactly once + Teams-only + locked JSON body shape
#   task6  email-triage-thread-defaults.mdc: file + frontmatter + required headers + no Gmail section + Microsoft 365 framing + conversationId
#   task7  cross-file scrub: banned-term regex (Story 2.1 list + boundary-guarded slack + benji) over all four files + why-comment terminator + placeholder parity + no duplicated identity block
#   task8  self-check: harness well-formed (shebang, set -euo pipefail, case branches, regex + headers definitions)
#   task9  regression against Story 1.1 / 1.2 / 1.3 / 2.1 validation harnesses (bash <harness> all must exit 0)
#   all    runs every gate in order
#
# Invocation: bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh <gate>
#
# Tooling: POSIX-bash 3.2 compatible (no associative arrays). Uses only bash, grep, awk, sed.
# NOTE: ripgrep (rg) is intentionally not used — `grep -i -E` is the portable scanner here.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/tests"
SELF_PATH="${BASH_SOURCE[0]}"

STORY_PATH="${PROJECT_ROOT}/_bmad-output/implementation-artifacts/2-2-port-guardrail-and-formatting-rules.md"
BASELINE_AUDIT_PATH="${TESTS_DIR}/story-2-2-baseline-audit.md"
BLUEPRINT_PATH="${TESTS_DIR}/story-2-2-canonical-blueprint.md"

RULES_DIR="${PROJECT_ROOT}/.cursor/rules"
OUTBOUND_PATH="${RULES_DIR}/outbound-messaging-guardrail.mdc"
MEMORY_PATH="${RULES_DIR}/memory-vault-protection.mdc"
TEAMS_PATH="${RULES_DIR}/teams-dm-formatting.mdc"
EMAIL_PATH="${RULES_DIR}/email-triage-thread-defaults.mdc"
AGENT_IDENTITY_PATH="${RULES_DIR}/agent-identity.mdc"

STORY_1_1_HARNESS="${TESTS_DIR}/story-1-1-scaffold-validation.sh"
STORY_1_2_HARNESS="${TESTS_DIR}/story-1-2-root-files-validation.sh"
STORY_1_3_HARNESS="${TESTS_DIR}/story-1-3-root-context-validation.sh"
STORY_2_1_HARNESS="${TESTS_DIR}/story-2-1-agent-identity-validation.sh"

# Required section headers per file (locked by Task 2 blueprint).
OUTBOUND_HEADERS="\
# Outbound Messaging Guardrail (Mandatory)
## The Rule
## Platforms Covered
## Required Workflow
## No Exceptions
## Signing Convention"

MEMORY_HEADERS="\
# Memory Vault Protection
## Protected Surfaces
## Rules"

TEAMS_HEADERS="\
# Teams Message Formatting
## Rules
### Example Teams body"

EMAIL_HEADERS="\
# Email Triage Thread Defaults
## Rules"

# Epic 3 memory-path enumeration (AC7). Every path must appear verbatim in
# `memory-vault-protection.mdc` under `## Protected Surfaces`.
MEMORY_PATHS="\
memory/me/identity.md
memory/me/preferences.md
memory/meetings/_template/
meeting.md
agenda.md
prep.md
transcript.md
memory/people/_template.md
memory/decisions/_template.md
memory/reference/_template.md
memory/inbox/_template.md
memory/appreciations/_template.md"

# Case-insensitive banned-term regex (alternation). Extends the Story 2.1 list
# with boundary-guarded `slack` (Teams is the internal chat surface) and `benji`
# (Story 2.4 explicitly excludes `benji-inbox-default.mdc`). Short substrings
# (`deke`, `ASU`, `arete`, `eudaimonia`, `blog`, `slack`, `benji`) use POSIX-ERE
# non-letter boundaries instead of GNU `\b`, so the scan behaves identically
# under macOS BSD grep, GNU grep, and busybox/Alpine grep. A fail-fast probe
# below rejects any host whose grep interprets these patterns incorrectly.
BANNED_TERMS_REGEX='derek|(^|[^A-Za-z])deke($|[^A-Za-z])|neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|(^|[^A-Za-z])ASU($|[^A-Za-z])|gtd-life|(^|[^A-Za-z])arete($|[^A-Za-z])|(^|[^A-Za-z])eudaimonia($|[^A-Za-z])|(^|[^A-Za-z])blog($|[^A-Za-z])|gmail|google calendar|google workspace|personal email|(^|[^A-Za-z])slack($|[^A-Za-z])|(^|[^A-Za-z])benji($|[^A-Za-z])'

# Outbound-messaging-specific deferred-content regex (AC6). The outbound rule
# must not inline Microsoft Graph URLs with parameters, Graph `contentType`
# payloads, or Outlook `Comment` workflow strings — those payload shapes live
# in `teams-dm-formatting.mdc`. Note: the bare phrase "Outlook on the M365
# stack" IS allowed here (platforms-covered bullet), which is why `outlook`
# is intentionally omitted from this regex. `teams-dm-formatting.mdc` is
# allowed to carry the locked JSON body + `"contentType": "html"` and is NOT
# subject to this regex.
OUTBOUND_DEFERRED_REGEX='graph\.microsoft\.com|"contentType"|"contenttype"|"Comment"|"comment"'

# Gmail-absence regex for `email-triage-thread-defaults.mdc` (AC4, AC8).
EMAIL_GMAIL_ABSENCE_REGEX='gmail|chiron/inspiration|chiron/inspirationprocessed|inbox label|google-workspace|google workspace|google calendar|google drive|google chat'

# Non-Teams chat surfaces that must not appear in `teams-dm-formatting.mdc` or
# `outbound-messaging-guardrail.mdc` platforms-covered lists (AC5).
NON_TEAMS_CHAT_REGEX='(^|[^A-Za-z])slack($|[^A-Za-z])|discord|mattermost|imessage|(^|[^A-Za-z])sms($|[^A-Za-z])|google chat'

# Allowed placeholder tokens across the rule pack (Story 1.3 + Story 2.1 set;
# no new tokens introduced by Story 2.2).
ALLOWED_PLACEHOLDERS="\
{{employee_name}}
{{employee_role}}
{{employee_department}}
{{employee_manager}}"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

require_file_exists() {
  local path="$1"
  local gate="$2"
  [[ -f "${path}" ]] || fail "${gate}: missing file ${path}"
}

# Fail fast if the host grep mis-parses the POSIX-ERE patterns above. Guards
# against silent fail-open on exotic hosts where `(^|[^A-Za-z])` is
# interpreted incorrectly. Extends Story 2.1's probe with `slack` and `benji`
# so Story 2.2's scan cannot silently drop those terms.
regex_self_probe() {
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
}

# Validate a rule file's YAML frontmatter block. Enforces: opening `---` on
# line 1; closing `---` strictly after; `description:` present; `alwaysApply:
# true`; `globs:` value equals the expected string ("[]" or "memory/**").
check_frontmatter_shape() {
  local path="$1"
  local gate="$2"
  local expected_globs="$3"

  local fm_open_line fm_close_line
  fm_open_line="$(grep -n '^---$' "${path}" | head -n 1 | cut -d: -f1 || true)"
  fm_close_line="$(grep -n '^---$' "${path}" | sed -n '2p' | cut -d: -f1 || true)"
  [[ -n "${fm_open_line}" && -n "${fm_close_line}" ]] \
    || fail "${gate}: ${path} missing YAML frontmatter delimiters"
  [[ "${fm_open_line}" -eq 1 ]] \
    || fail "${gate}: ${path} frontmatter must start on line 1 (found line ${fm_open_line})"
  (( fm_close_line > fm_open_line )) \
    || fail "${gate}: ${path} frontmatter block malformed (close <= open)"

  local frontmatter
  frontmatter="$(awk -v a="${fm_open_line}" -v b="${fm_close_line}" 'NR>a && NR<b' "${path}")"

  echo "${frontmatter}" | grep -Eq '^description:[[:space:]]*.+' \
    || fail "${gate}: ${path} frontmatter missing non-empty description key"
  echo "${frontmatter}" | grep -Eq '^alwaysApply:[[:space:]]*true[[:space:]]*$' \
    || fail "${gate}: ${path} frontmatter missing alwaysApply: true"

  echo "${frontmatter}" | grep -Eq '^globs:' \
    || fail "${gate}: ${path} frontmatter missing globs key"

  local globs_value
  globs_value="$(echo "${frontmatter}" | awk 'sub(/^globs:[[:space:]]*/,"") {print; exit}')"
  if [[ "${globs_value}" != "${expected_globs}" ]]; then
    fail "${gate}: ${path} globs must be '${expected_globs}' (got: '${globs_value}')"
  fi
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

# Print the last non-blank line of a file.
last_non_blank_line() {
  awk 'NF{ last=$0 } END{ print last }' "$1"
}

# Assert a file's last non-blank line is a one-line "why" comment in one of
# the approved forms: HTML comment (`<!-- ... -->`), markdown blockquote
# (`> ...`), or markdown italic single line (`_..._`). AC9.
require_why_comment_terminator() {
  local path="$1"
  local gate="$2"

  local last
  last="$(last_non_blank_line "${path}")"
  # Use `grep -Eq` against plain POSIX-ERE so `<` and `>` are literal (not
  # GNU word-boundary anchors `\<` / `\>`) across macOS BSD and GNU hosts.
  if echo "${last}" | grep -Eq '^<!--.*-->$'; then
    :
  elif echo "${last}" | grep -Eq '^>.*$'; then
    :
  elif echo "${last}" | grep -Eq '^_.*_$'; then
    :
  else
    fail "${gate}: ${path} last non-blank line is not a one-line why comment: ${last}"
  fi

  # The why comment itself must be scrubbed of banned terms.
  if echo "${last}" | grep -iE "${BANNED_TERMS_REGEX}" >/dev/null; then
    fail "${gate}: ${path} why comment contains banned term: ${last}"
  fi
}

# ------------------------------------------------------------------
# task1 — baseline-audit evidence present and complete
# ------------------------------------------------------------------
check_task1() {
  local gate="task1"
  require_file_exists "${BASELINE_AUDIT_PATH}" "${gate}"

  grep -Fq "Story 2.2 Baseline Audit" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing title"
  grep -Fq "Banned-term set" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Banned-term set section"
  grep -Fq "Source-to-target scrub map" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Source-to-target scrub map"
  grep -Fq "Required present tokens" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Required present tokens matrix"

  # Every source rule subsection present.
  local src
  for src in outbound-messaging-guardrail.mdc memory-vault-protection.mdc \
             teams-dm-formatting.mdc email-triage-thread-defaults.mdc; do
    grep -Fq "${src}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing source rule entry: ${src}"
  done

  # Story 2.1 banned-term carryover recorded.
  local term
  for term in Derek Deke Neighbors Chiron RevivaGo derekneighbors.com \
              "Agile Weekly" MasteryLab Bodybuilding.com Gangplank ASU \
              gtd-life arete eudaimonia blog Gmail "Google Calendar" \
              "Google Workspace" "personal email"; do
    grep -Fq "${term}" "${BASELINE_AUDIT_PATH}" \
      || fail "${gate}: baseline audit missing banned term entry: ${term}"
  done

  # Story 2.2 additions recorded.
  grep -Fq "Slack" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Story 2.2 addition: Slack"
  grep -Fq "Benji" "${BASELINE_AUDIT_PATH}" \
    || fail "${gate}: baseline audit missing Story 2.2 addition: Benji"
}

# ------------------------------------------------------------------
# task2 — canonical-blueprint evidence present and complete
# ------------------------------------------------------------------
check_task2() {
  local gate="task2"
  require_file_exists "${BLUEPRINT_PATH}" "${gate}"

  grep -Fq "Story 2.2 Canonical Blueprint" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing title"
  grep -Fq "Shared placeholder inventory" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Shared placeholder inventory section"
  grep -Fq "Shared signing convention" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Shared signing convention section"
  grep -Fq "Cross-file consistency requirements" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Cross-file consistency requirements section"
  grep -Fq "Cross-AC coverage map" "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing Cross-AC coverage map"

  # All four target files have a locked subsection.
  local target
  for target in outbound-messaging-guardrail.mdc memory-vault-protection.mdc \
                teams-dm-formatting.mdc email-triage-thread-defaults.mdc; do
    grep -Fq "${target}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing locked subsection for: ${target}"
  done

  # Locked section headers per file reachable from the blueprint.
  local header
  while IFS= read -r header; do
    [[ -z "${header}" ]] && continue
    grep -Fq "${header}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing locked header reference: ${header}"
  done <<EOF
${OUTBOUND_HEADERS}
${MEMORY_HEADERS}
${TEAMS_HEADERS}
${EMAIL_HEADERS}
EOF

  # Placeholder inventory locked to the Story 1.3 / 2.1 set only.
  local ph
  for ph in '{{employee_name}}' '{{employee_role}}' '{{employee_department}}' '{{employee_manager}}'; do
    grep -Fq "${ph}" "${BLUEPRINT_PATH}" \
      || fail "${gate}: blueprint missing placeholder: ${ph}"
  done

  # Signing convention and payload locks.
  grep -Fq 'AI assistant for {{employee_name}}' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing locked signing form"
  grep -Fq '"contentType": "html"' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing locked Teams JSON body contentType"
  grep -Fq 'alwaysApply: true' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing alwaysApply: true lock"
  grep -Fq 'globs: memory/**' "${BLUEPRINT_PATH}" \
    || fail "${gate}: blueprint missing globs: memory/** lock"
}

# ------------------------------------------------------------------
# task3 — outbound-messaging-guardrail.mdc file + frontmatter + headers + cross-refs + signing
# ------------------------------------------------------------------
check_task3() {
  local gate="task3"
  require_file_exists "${OUTBOUND_PATH}" "${gate}"

  check_frontmatter_shape "${OUTBOUND_PATH}" "${gate}" "[]"

  # Description contract — AC1.
  local frontmatter
  frontmatter="$(awk '/^---$/{c++; next} c==1' "${OUTBOUND_PATH}")"
  echo "${frontmatter}" | grep -Fq 'CRITICAL safety guardrail' \
    || fail "${gate}: outbound description must contain 'CRITICAL safety guardrail'"

  require_exact_headers "${OUTBOUND_PATH}" "${gate}" "${OUTBOUND_HEADERS}"

  # Cross-ref to agent-identity.mdc (AC10 — sibling defers identity).
  grep -Fq '.cursor/rules/agent-identity.mdc' "${OUTBOUND_PATH}" \
    || fail "${gate}: outbound rule missing cross-ref to agent-identity.mdc"

  # Signing-convention locked form (AC5/AC6 — no assistant proper name).
  grep -Fq -e '-- AI assistant for {{employee_name}}' "${OUTBOUND_PATH}" \
    || fail "${gate}: outbound rule missing locked Teams sign-off form"

  # Platforms-Covered AC5: Microsoft Teams + Microsoft 365 listed; non-Teams chat surfaces absent.
  grep -Fq 'Microsoft Teams' "${OUTBOUND_PATH}" \
    || fail "${gate}: outbound rule missing 'Microsoft Teams' platform entry"
  grep -Fq 'Microsoft 365' "${OUTBOUND_PATH}" \
    || fail "${gate}: outbound rule missing 'Microsoft 365' platform entry"
  # AC5 allows a blockquote exclusion line (`> …`) to explicitly name
  # out-of-scope personal messaging surfaces (SMS, iMessage, personal chat
  # apps). The scan therefore strips blockquote lines before checking that
  # non-Teams chat surfaces do not appear in the covered-platforms body.
  if grep -vE '^[[:space:]]*>' "${OUTBOUND_PATH}" | grep -iE "${NON_TEAMS_CHAT_REGEX}" >/dev/null; then
    fail "${gate}: outbound rule references a non-Teams chat surface (Slack/Discord/Mattermost/iMessage/SMS/Google Chat) outside the AC5 exclusion blockquote"
  fi

  # Required workflow approval tokens (AC5 workflow lock).
  local tok
  for tok in "send it" "go" "fire" "approved"; do
    grep -Fq "\"${tok}\"" "${OUTBOUND_PATH}" \
      || fail "${gate}: outbound rule missing approval token literal: \"${tok}\""
  done

  # AC6 deferred content — outbound must not inline Graph/JSON/HTML payloads.
  if grep -iE "${OUTBOUND_DEFERRED_REGEX}" "${OUTBOUND_PATH}" >/dev/null; then
    fail "${gate}: outbound rule contains Story 2.2 deferred payload content (Graph/JSON)"
  fi
  if grep -nE '^[[:space:]]*```json' "${OUTBOUND_PATH}" >/dev/null; then
    fail "${gate}: outbound rule contains fenced JSON block (payload belongs to teams-dm-formatting.mdc)"
  fi
  if grep -nE '<(div|span|table|tr|td|p|strong|em|br|a)[[:space:]>]' "${OUTBOUND_PATH}" >/dev/null; then
    fail "${gate}: outbound rule contains inline HTML element (Teams HTML payload belongs to teams-dm-formatting.mdc)"
  fi

  # Placeholder presence (AC2).
  grep -Fq '{{employee_name}}' "${OUTBOUND_PATH}" \
    || fail "${gate}: outbound rule missing placeholder {{employee_name}}"

  # File-scoped banned-term scrub (AC3).
  regex_self_probe
  local hit
  hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${OUTBOUND_PATH}" || true)"
  if [[ -n "${hit}" ]]; then
    fail "${gate}: banned term(s) detected in ${OUTBOUND_PATH}: ${hit}"
  fi
}

# ------------------------------------------------------------------
# task4 — memory-vault-protection.mdc file + frontmatter (globs: memory/**) + memory-path enumeration
# ------------------------------------------------------------------
check_task4() {
  local gate="task4"
  require_file_exists "${MEMORY_PATH}" "${gate}"

  check_frontmatter_shape "${MEMORY_PATH}" "${gate}" "memory/**"

  require_exact_headers "${MEMORY_PATH}" "${gate}" "${MEMORY_HEADERS}"

  # Epic 3 memory-path enumeration (AC7).
  local mp
  while IFS= read -r mp; do
    [[ -z "${mp}" ]] && continue
    grep -Fq "${mp}" "${MEMORY_PATH}" \
      || fail "${gate}: memory rule missing required memory path: ${mp}"
  done <<EOF
${MEMORY_PATHS}
EOF

  # "work context only" framing (AC7 positive token, once).
  grep -Fq 'work context only' "${MEMORY_PATH}" \
    || fail "${gate}: memory rule missing 'work context only' framing"

  # AC6 — memory rule must use prose pointers, not inline JSON/code blocks.
  if grep -nE '^[[:space:]]*```json' "${MEMORY_PATH}" >/dev/null; then
    fail "${gate}: memory rule contains fenced JSON block (payload belongs to teams-dm-formatting.mdc)"
  fi
  if grep -nE '^[[:space:]]*```' "${MEMORY_PATH}" >/dev/null; then
    fail "${gate}: memory rule contains a fenced code block (AC6 requires prose pointers only)"
  fi

  # Source-rule framings that MUST NOT survive the port.
  if grep -Fq 'personal AI life operating system' "${MEMORY_PATH}"; then
    fail "${gate}: memory rule contains forbidden gtd-life framing 'personal AI life operating system'"
  fi
  if grep -Fq 'PII is the product' "${MEMORY_PATH}"; then
    fail "${gate}: memory rule contains forbidden gtd-life framing 'PII is the product'"
  fi
  local f
  for f in family.md ventures.md; do
    if grep -Fq "${f}" "${MEMORY_PATH}"; then
      fail "${gate}: memory rule contains forbidden gtd-life memory filename: ${f}"
    fi
  done

  # Placeholder presence (AC2).
  grep -Fq '{{employee_name}}' "${MEMORY_PATH}" \
    || fail "${gate}: memory rule missing placeholder {{employee_name}}"

  # File-scoped banned-term scrub (AC3).
  regex_self_probe
  local hit
  hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${MEMORY_PATH}" || true)"
  if [[ -n "${hit}" ]]; then
    fail "${gate}: banned term(s) detected in ${MEMORY_PATH}: ${hit}"
  fi
}

# ------------------------------------------------------------------
# task5 — teams-dm-formatting.mdc file + frontmatter + required headers + contentType/html payload
# ------------------------------------------------------------------
check_task5() {
  local gate="task5"
  require_file_exists "${TEAMS_PATH}" "${gate}"

  check_frontmatter_shape "${TEAMS_PATH}" "${gate}" "[]"

  require_exact_headers "${TEAMS_PATH}" "${gate}" "${TEAMS_HEADERS}"

  # Scope assertion: Microsoft Teams present.
  grep -Fq 'Microsoft Teams' "${TEAMS_PATH}" \
    || fail "${gate}: teams rule missing 'Microsoft Teams' scope token"

  # Non-Teams chat surfaces must not appear (AC5).
  if grep -iE "${NON_TEAMS_CHAT_REGEX}" "${TEAMS_PATH}" >/dev/null; then
    fail "${gate}: teams rule references a non-Teams chat surface (Slack/Discord/Mattermost/iMessage/SMS/Google Chat)"
  fi

  # AC6: "contentType": "html" appears exactly once. Use `grep -oF | wc -l`
  # to count occurrences (grep -cF counts matching lines, which would miss
  # two occurrences on the same line).
  local ct_count
  ct_count="$(grep -oF '"contentType": "html"' "${TEAMS_PATH}" | wc -l | tr -d ' ')"
  if [[ "${ct_count}" -ne 1 ]]; then
    fail "${gate}: teams rule must contain \"contentType\": \"html\" exactly once (got ${ct_count})"
  fi

  # AC6: locked JSON body — neutral work sentence, single <p> wrapper, locked signing form.
  grep -Fq -e '<p>Short status update. -- AI assistant for {{employee_name}}</p>' "${TEAMS_PATH}" \
    || fail "${gate}: teams rule missing locked example body '<p>Short status update. -- AI assistant for {{employee_name}}</p>'"

  # AC6 hygiene: zero @X@ email-address patterns inside the file (`@mentions` prose OK).
  if grep -E '@[A-Za-z0-9._%+-]+@' "${TEAMS_PATH}" >/dev/null; then
    fail "${gate}: teams rule contains an @X@ email-address pattern"
  fi

  # Exactly one fenced JSON block — assert one `json` opener and total fence
  # lines == 2 (open + close). This catches both "zero fences" and
  # "unclosed fence" regressions that `grep -cE` on just the opener misses.
  local json_count fence_count
  json_count="$(grep -cE '^[[:space:]]*```json[[:space:]]*$' "${TEAMS_PATH}" || true)"
  if [[ "${json_count}" -ne 1 ]]; then
    fail "${gate}: teams rule must contain exactly one fenced JSON block (got ${json_count} openers)"
  fi
  fence_count="$(grep -cE '^[[:space:]]*```' "${TEAMS_PATH}" || true)"
  if [[ "${fence_count}" -ne 2 ]]; then
    fail "${gate}: teams rule must contain exactly one closed fenced block (got ${fence_count} fence lines)"
  fi

  # Placeholder presence (AC2).
  grep -Fq '{{employee_name}}' "${TEAMS_PATH}" \
    || fail "${gate}: teams rule missing placeholder {{employee_name}}"

  # File-scoped banned-term scrub (AC3).
  regex_self_probe
  local hit
  hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${TEAMS_PATH}" || true)"
  if [[ -n "${hit}" ]]; then
    fail "${gate}: banned term(s) detected in ${TEAMS_PATH}: ${hit}"
  fi
}

# ------------------------------------------------------------------
# task6 — email-triage-thread-defaults.mdc file + frontmatter + no Gmail + M365 + conversationId
# ------------------------------------------------------------------
check_task6() {
  local gate="task6"
  require_file_exists "${EMAIL_PATH}" "${gate}"

  check_frontmatter_shape "${EMAIL_PATH}" "${gate}" "[]"

  require_exact_headers "${EMAIL_PATH}" "${gate}" "${EMAIL_HEADERS}"

  # AC4 / AC8 — no Gmail section, no Google references.
  if grep -nE '^## Gmail' "${EMAIL_PATH}" >/dev/null; then
    fail "${gate}: email rule contains forbidden '## Gmail' section header"
  fi
  if grep -iE "${EMAIL_GMAIL_ABSENCE_REGEX}" "${EMAIL_PATH}" >/dev/null; then
    fail "${gate}: email rule contains forbidden Gmail/Google/Chiron-Inspiration/INBOX-label/google-workspace reference"
  fi

  # AC6 — email rule must use prose pointers, not inline JSON/code blocks.
  if grep -nE '^[[:space:]]*```json' "${EMAIL_PATH}" >/dev/null; then
    fail "${gate}: email rule contains fenced JSON block (payload belongs to teams-dm-formatting.mdc)"
  fi
  if grep -nE '^[[:space:]]*```' "${EMAIL_PATH}" >/dev/null; then
    fail "${gate}: email rule contains a fenced code block (AC6 requires prose pointers only)"
  fi

  # AC8 — Microsoft 365 framing + Microsoft Graph conversationId primitive.
  grep -Fq 'Microsoft 365' "${EMAIL_PATH}" \
    || fail "${gate}: email rule missing 'Microsoft 365' framing"
  grep -Fq 'conversationId' "${EMAIL_PATH}" \
    || fail "${gate}: email rule missing Microsoft Graph 'conversationId' thread primitive"

  # AC8 required tag / status tokens.
  local tok
  for tok in Ask Decision FYI Open Closed Waiting Superseded; do
    grep -Fq "${tok}" "${EMAIL_PATH}" \
      || fail "${gate}: email rule missing required tag/status token: ${tok}"
  done

  # Placeholder presence (AC2).
  grep -Fq '{{employee_name}}' "${EMAIL_PATH}" \
    || fail "${gate}: email rule missing placeholder {{employee_name}}"

  # File-scoped banned-term scrub (AC3).
  regex_self_probe
  local hit
  hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${EMAIL_PATH}" || true)"
  if [[ -n "${hit}" ]]; then
    fail "${gate}: banned term(s) detected in ${EMAIL_PATH}: ${hit}"
  fi
}

# ------------------------------------------------------------------
# task7 — cross-file scrub: banned-terms + why-comment terminator + placeholder parity + no duplicated identity block
# ------------------------------------------------------------------
check_task7() {
  local gate="task7"
  require_file_exists "${OUTBOUND_PATH}" "${gate}"
  require_file_exists "${MEMORY_PATH}" "${gate}"
  require_file_exists "${TEAMS_PATH}" "${gate}"
  require_file_exists "${EMAIL_PATH}" "${gate}"

  regex_self_probe

  local path hit last
  for path in "${OUTBOUND_PATH}" "${MEMORY_PATH}" "${TEAMS_PATH}" "${EMAIL_PATH}"; do
    hit="$(grep -n -i -E "${BANNED_TERMS_REGEX}" "${path}" || true)"
    if [[ -n "${hit}" ]]; then
      fail "${gate}: banned term(s) detected in ${path}: ${hit}"
    fi

    # AC9 — each file ends with a one-line "why" comment terminator (scrubbed).
    require_why_comment_terminator "${path}" "${gate}"
  done

  # Placeholder parity (AC2 / AC11) — only the Story 1.3 + 2.1 placeholder
  # inventory may appear anywhere in the four sibling rule files. No new tokens.
  local found ph_token known
  found="$( { grep -oE '\{\{[a-z_]+\}\}' \
      "${OUTBOUND_PATH}" "${MEMORY_PATH}" "${TEAMS_PATH}" "${EMAIL_PATH}" \
      || true; } | awk -F: '{print $NF}' | sort -u )"
  while IFS= read -r ph_token; do
    [[ -z "${ph_token}" ]] && continue
    known=0
    local allowed
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
      fail "${gate}: unapproved placeholder token detected across rule pack: ${ph_token}"
    fi
  done <<EOF
${found}
EOF

  # AC10 / AC11 — no duplicated identity block. Each sibling rule must NOT
  # contain both Story 2.1 scope tokens ('Vixxo employee' AND 'work context
  # only') in the same body. A single scope token is tolerated (e.g.
  # memory-vault-protection keeps 'work context only' once for AC7 framing).
  local has_vix has_wco
  for path in "${OUTBOUND_PATH}" "${MEMORY_PATH}" "${TEAMS_PATH}" "${EMAIL_PATH}"; do
    has_vix=0
    has_wco=0
    grep -Fq 'Vixxo employee' "${path}" && has_vix=1
    grep -Fq 'work context only' "${path}" && has_wco=1
    if [[ "${has_vix}" -eq 1 && "${has_wco}" -eq 1 ]]; then
      fail "${gate}: ${path} duplicates agent-identity.mdc identity block (both 'Vixxo employee' and 'work context only' present)"
    fi
  done

  # AC10 — agent-identity.mdc must still exist and carry the
  # `## Related Rule Files` pointer that Story 2.2 satisfies. Presence of
  # the pointer heading is the bilateral integrity assertion for AC10;
  # full Story 2.1 content is re-validated by `task9`.
  require_file_exists "${AGENT_IDENTITY_PATH}" "${gate}"
  grep -Fq '## Related Rule Files' "${AGENT_IDENTITY_PATH}" \
    || fail "${gate}: agent-identity.mdc missing '## Related Rule Files' pointer"
}

# ------------------------------------------------------------------
# task8 — self-check: harness is well-formed and owns the full gate set
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

  grep -Fq 'BANNED_TERMS_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing BANNED_TERMS_REGEX definition"
  grep -Fq 'OUTBOUND_DEFERRED_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing OUTBOUND_DEFERRED_REGEX definition"
  grep -Fq 'EMAIL_GMAIL_ABSENCE_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing EMAIL_GMAIL_ABSENCE_REGEX definition"
  grep -Fq 'NON_TEAMS_CHAT_REGEX=' "${SELF_PATH}" \
    || fail "${gate}: harness missing NON_TEAMS_CHAT_REGEX definition"
  grep -Fq 'OUTBOUND_HEADERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing OUTBOUND_HEADERS definition"
  grep -Fq 'MEMORY_HEADERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing MEMORY_HEADERS definition"
  grep -Fq 'TEAMS_HEADERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing TEAMS_HEADERS definition"
  grep -Fq 'EMAIL_HEADERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing EMAIL_HEADERS definition"
  grep -Fq 'MEMORY_PATHS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing MEMORY_PATHS definition"
  grep -Fq 'ALLOWED_PLACEHOLDERS=' "${SELF_PATH}" \
    || fail "${gate}: harness missing ALLOWED_PLACEHOLDERS definition"

  grep -Fq 'regex_self_probe' "${SELF_PATH}" \
    || fail "${gate}: harness missing regex_self_probe function"
}

# ------------------------------------------------------------------
# task9 — regression against Story 1.1 / 1.2 / 1.3 / 2.1 harnesses
# ------------------------------------------------------------------
check_task9() {
  local gate="task9"
  require_file_exists "${STORY_1_1_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_2_HARNESS}" "${gate}"
  require_file_exists "${STORY_1_3_HARNESS}" "${gate}"
  require_file_exists "${STORY_2_1_HARNESS}" "${gate}"

  # Capture each sub-harness's combined output so a regression surfaces the
  # failing gate instead of a silent non-zero exit.
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
}

mode="${1:-all}"
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
