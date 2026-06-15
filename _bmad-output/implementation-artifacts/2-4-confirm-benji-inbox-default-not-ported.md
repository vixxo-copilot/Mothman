# Story 2.4: Confirm `benji-inbox-default.mdc` is NOT ported

Status: done

## Story

As a template maintainer of the Vixxo `assistants-template`,
I want Benji-specific rules — and `benji-inbox-default.mdc` in particular — explicitly excluded from the ported rule pack and permanently prevented from re-appearing,
so that the personal gtd-life task system does not leak into the work template (neither as a rule file, nor as a content reference) and so the Story 2.3 boundary-guarded content-scrub of `benji` is complemented by a file-level absence assertion that cannot regress.

## Acceptance Criteria

1. **AC1 — `.cursor/rules/benji-inbox-default.mdc` does not exist in the repository**
   - Given the cloned `assistants-template` repository after Stories 2.1, 2.2, and 2.3 landed `.cursor/rules/agent-identity.mdc`, the four sibling guardrail/formatting rules, and `agents/personas/work.md`
   - When `.cursor/rules/` is listed
   - Then the file `.cursor/rules/benji-inbox-default.mdc` is NOT present (neither as a real file, a zero-byte placeholder, nor a symlink)
   - And no file matching the pattern `benji*.mdc` (case-insensitive, any extension variant such as `.md`, `.mdc`, `.markdown`) exists anywhere under `.cursor/rules/`
   - And no file matching the pattern `benji*.mdc` exists anywhere under the repository root tracked by git (excluding `_bmad-output/` planning/test/evidence paths and `.git/`, which legitimately record the banned term in spec and scan regex form)
   - And the existing Story 2.2 rule pack (`outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`) and the Story 2.1 identity rule (`agent-identity.mdc`) remain byte-for-byte unchanged — Story 2.4 must not edit the rule pack

2. **AC2 — Generic `benji`-prefixed rule filename scan is enforced, not just the single specific filename**
   - Given the scan logic for `.cursor/rules/`
   - When the harness enumerates `.cursor/rules/*.mdc` (and any adjacent extensions `.md` / `.markdown`)
   - Then the enumeration rejects any filename whose basename begins with `benji` (case-insensitively) OR contains the substring `-benji-` / `_benji_` / `benji-inbox` / `benji_inbox` — the assertion is pattern-level, not hardcoded to the one currently-known filename, so a renamed variant (e.g. `benji-inbox-default-v2.mdc`, `benji-tasks.mdc`, `benji-default-inbox.mdc`) cannot slip past by filename rewording
   - And the scan treats the `.cursor/rules/` directory as the scope of record; adjacent directories (`.cursor/`, `agents/`, `memory/`, `docs/`, etc.) are explicitly out of scope for AC1 (the persona + memory vault + docs scrub is already owned by Stories 2.3 / 3.1–3.3 / epic-6)

3. **AC3 — Story 2.3 boundary-guarded banned-term content scan for `benji` still fires (complementary content scrub preserved)**
   - Given the Story 2.3 harness `_bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh`
   - When the Story 2.4 harness runs in regression mode
   - Then the Story 2.3 harness continues to exit `0` with `PASS: all` (zero edits to the Story 2.3 harness; Story 2.4 adds ON TOP of Story 2.3, not in place of it)
   - And the Story 2.4 harness performs its OWN boundary-guarded `benji` content probe (not a duplicate of Story 2.3's scan over `agents/personas/work.md`, but a harness-local `regex_self_probe` that proves the host grep honors `(^|[^A-Za-z])benji($|[^A-Za-z])` — benjiman rejected, `benji inbox` accepted) so the scan cannot silently fail open on a mis-parsing host grep
   - And the probe is documented as "complementary to Story 2.3", with a comment in the harness header stating that Story 2.3 owns content-level scrub of `agents/personas/work.md` while Story 2.4 owns file-level absence assertion of `.cursor/rules/benji*.mdc`

4. **AC4 — Validation/CI assertion confirms the absence and is wired into the test harness family**
   - Given the existing harness family under `_bmad-output/implementation-artifacts/tests/`
   - When Story 2.4 lands
   - Then a new deterministic harness `story-2-4-benji-inbox-absence-validation.sh` exists at `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh`, is marked executable (`chmod +x`), and can be invoked with `bash <path> <gate>` for individual gates or `bash <path> all` for the full suite
   - And the harness emits `PASS: <gate>` on stdout per passing gate and exits `0` on success; emits `FAIL: <gate>: <reason>` on stderr and exits `1` on failure (matches Story 2.1 / 2.2 / 2.3 harness contract)
   - And optionally (low-priority), a one-line explicit exclusion note is added to the project docs (preferred location: a single bullet under a new `## Exclusions (not ported)` heading in `docs/setup.md`) that names `.cursor/rules/benji-inbox-default.mdc` as intentionally omitted with a pointer to `story-2-4-benji-inbox-absence-validation.sh` — this is a docs convenience, not a test gate; the harness alone satisfies the epic AC "CI assertion OR checklist item" (the OR lets the docs line remain optional without blocking this story)

5. **AC5 — Harness covers file-absence, pattern-level absence, rule-pack integrity, handoff-evidence shape, self-check, and regression**
   - Given `story-2-4-benji-inbox-absence-validation.sh`
   - When `bash <path> all` is run
   - Then it prints `PASS: all` and exits `0`
   - And individual gates each print `PASS: <task>` when invoked independently:
     - `task1` baseline-absence-audit evidence: `_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md` exists and contains the required sections (title, source-file reference, absence assertion, complement-to-Story-2.3 note)
     - `task2` file-absence assertions: `.cursor/rules/benji-inbox-default.mdc` does NOT exist (AC1 primary); pattern-level enumeration of `.cursor/rules/*.mdc` rejects any `benji`-prefixed or `benji`-embedded basename (AC2); `.cursor/rules/*.md` and `.cursor/rules/*.markdown` extension variants also scanned; repository-wide find rejects any `benji*.mdc` outside the `_bmad-output/` and `.git/` evidence paths
     - `task3` rule-pack integrity: the five expected rule files (`agent-identity.mdc`, `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`) ARE present and non-empty (zero-edit verification that Story 2.4 didn't accidentally remove the allowed pack); `agents/personas/work.md` also present and non-empty (Story 2.3 artifact intact)
     - `task4` content-scrub parity probe: `regex_self_probe` confirms the host grep honors `(^|[^A-Za-z])benji($|[^A-Za-z])` boundary guards (benjiman rejected, `benji inbox` accepted); this guards against a silently-failing host grep on systems without GNU regex
     - `task5` self-check: harness shebang on line 1, `set -euo pipefail` present, every required case branch (`task1)`–`task6)` and `all)`) declared, path constants (`RULES_DIR`, `PERSONA_PATH`, `AGENT_IDENTITY_PATH`, prior-harness paths) defined, `BENJI_BASENAME_PATTERN` / `BENJI_BOUNDARY_REGEX` constants defined, `regex_self_probe` function present
     - `task6` regression: invokes `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, `bash story-2-1-agent-identity-validation.sh all`, `bash story-2-2-guardrail-and-formatting-validation.sh all`, and `bash story-2-3-work-persona-validation.sh all`. Each sub-invocation captures combined stdout/stderr and echoes on non-zero exit (Story 2.2 Phase 4 F6 pattern). All six must return zero.
   - And the harness uses only `bash` + `grep` + `awk` + `sed` + shell built-ins (no `rg`, no Python, POSIX-bash-3.2 compatible, BSD-grep and GNU-grep compatible)

6. **AC6 — Regression-runs all predecessor harnesses cleanly with no edits to prior story artifacts**
   - Given all prior harnesses in `_bmad-output/implementation-artifacts/tests/`
   - When the Story 2.4 regression gate is executed
   - Then `story-1-1-scaffold-validation.sh all`, `story-1-2-root-files-validation.sh all`, `story-1-3-root-context-validation.sh all`, `story-2-1-agent-identity-validation.sh all`, `story-2-2-guardrail-and-formatting-validation.sh all`, and `story-2-3-work-persona-validation.sh all` each exit `0` with their final `PASS: all`
   - And zero bytes are changed in any of those six prior harnesses during Story 2.4 execution
   - And zero bytes are changed in `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files, `agents/personas/work.md`, the root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`), `README.md`, `LICENSE`, or `.gitignore` — Story 2.4 is additive only (new harness + new evidence artifacts + optional one-line docs checklist + sprint-status flip)

7. **AC7 — Sprint tracker lifecycle reflects the story transition; epic and sibling-story states are preserved byte-for-byte**
   - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
   - When Story 2.4 opens at Phase 1 (SM pass) and again at Phase 2 (Dev handoff)
   - Then the `2-4-confirm-benji-inbox-default-not-ported.status` entry is updated `backlog → ready-for-dev` (Phase 1) and `ready-for-dev → review` (Phase 2 handoff; the autonomous-swarm lifecycle may collapse interim states per the Story 2.1 / 2.2 / 2.3 precedent — a single on-disk transition is acceptable as long as the final pre-review status is `review`)
   - And `epic-2.status` remains `in-progress` through Phase 1 and Phase 2 (when Story 2.4 transitions to `done`, a separate follow-up pass MAY flip `epic-2.status` to `done`; that transition is NOT part of Story 2.4's AC7 and should be made as its own evidence-only edit)
   - And `last_updated` is set to `2026-04-20` on the Phase 1 edit
   - And no other story's status is regressed; every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` is preserved byte-for-byte (zero reordering, zero comment drift, zero key addition/removal)

8. **AC8 — Story is additive; no new persona, rule, or content files under the repository working set**
   - Given the scope of Story 2.4
   - When the working-set file list is reviewed
   - Then Story 2.4 creates NO new files under `.cursor/rules/`, `agents/`, `memory/`, `docs/legal/`, `bin/`, or `scripts/`
   - And Story 2.4 creates ONLY: one new bash harness at `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh`, one new baseline-audit artifact at `_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md`, one new handoff artifact at `_bmad-output/implementation-artifacts/tests/story-2-4-task6-handoff.md`, this story file itself, and (optional) a one-line checklist addition in `docs/setup.md` if Task 4 elects to add it
   - And Story 2.4 modifies ONLY: `_bmad-output/implementation-artifacts/sprint-status.yaml` (status flip + `last_updated`) and, at Dev-phase handoff, this story file's own Dev Agent Record / Change Log / File List / checkboxes

## Tasks / Subtasks

- [x] Task 1 — Baseline absence audit of `.cursor/rules/` and gtd-life source (AC: 1, 2, 3, 8) **[Parallelizable with Task 2]**
  - [x] Enumerate the current `.cursor/rules/` directory and record the filename list (expected: `.gitkeep`, `agent-identity.mdc`, `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`). Confirm `benji-inbox-default.mdc` is NOT in the list (positive baseline evidence).
  - [x] Inspect the gtd-life source of record at `~/Public/gtd-life/.cursor/rules/benji-inbox-default.mdc` and record (a) its exact filename, (b) its frontmatter (`description: Default Benji todos to inbox`, `alwaysApply: true`), and (c) the fact that it names `Derek` explicitly and references the personal Benji task system — i.e. it is both structurally personal (rule exists) and content-level personal (Derek + Benji tokens inside). This documents WHY the file is excluded, not just that it is.
  - [x] Record the absence-assertion scope: file-level at `.cursor/rules/benji-inbox-default.mdc` (AC1 primary), pattern-level at `.cursor/rules/benji*` (AC2), and repository-wide outside `_bmad-output/` and `.git/` evidence paths. Explicitly note that `_bmad-output/` references to `benji-inbox-default.mdc` are legitimate evidence/spec text (this story file, sprint-status, epics.md, prior story specs) and must NOT be flagged.
  - [x] Record the complementary-scope note: Story 2.3 owns the content-level scrub of `benji` inside `agents/personas/work.md` (boundary-guarded banned-term regex); Story 2.4 owns the file-level absence of `.cursor/rules/benji*.mdc`. The two assertions layer — neither supersedes the other.
  - [x] Persist baseline evidence at `_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md` with sections: `# Story 2.4 Baseline Absence Audit`, `## Current .cursor/rules/ inventory`, `## gtd-life source (reference only — not ported)`, `## Absence-assertion scope`, `## Complement to Story 2.3 content scrub`, `## Banned-filename pattern lock`.

- [x] Task 2 — Author the deterministic validation harness (AC: 1, 2, 3, 4, 5) **[Scaffoldable in parallel with Task 1; final gate wiring depends on Task 1 lock for `BENJI_BASENAME_PATTERN`]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh`. POSIX-bash-3.2 compatible, `#!/usr/bin/env bash` on line 1, `set -euo pipefail` on line 2. Mark executable (`chmod +x`). Model the skeleton on `story-2-3-work-persona-validation.sh` (same `PROJECT_ROOT` / `TESTS_DIR` / `SELF_PATH` derivation, same `fail()` helper, same `require_file_exists()` helper).
  - [x] Declare constants at the top of the file:
    - `RULES_DIR="${PROJECT_ROOT}/.cursor/rules"`
    - `BANNED_RULE_PATH="${RULES_DIR}/benji-inbox-default.mdc"`
    - `BENJI_BASENAME_PATTERN='^[Bb][Ee][Nn][Jj][Ii]'` (case-insensitive basename prefix match via ERE; do not use `shopt -s nocaseglob` because that mutates global shell state)
    - `BENJI_BOUNDARY_REGEX='(^|[^A-Za-z])benji($|[^A-Za-z])'` (content-scrub parity probe; reused from Story 2.2 / 2.3 pattern)
    - `PERSONA_PATH="${PROJECT_ROOT}/agents/personas/work.md"`
    - `AGENT_IDENTITY_PATH="${PROJECT_ROOT}/.cursor/rules/agent-identity.mdc"`
    - `EXPECTED_RULE_FILES="agent-identity.mdc\noutbound-messaging-guardrail.mdc\nmemory-vault-protection.mdc\nteams-dm-formatting.mdc\nemail-triage-thread-defaults.mdc"` (the five rule files that MUST exist — rule-pack integrity check per AC5 task3)
    - Prior-harness paths: `STORY_1_1_HARNESS`, `STORY_1_2_HARNESS`, `STORY_1_3_HARNESS`, `STORY_2_1_HARNESS`, `STORY_2_2_HARNESS`, `STORY_2_3_HARNESS` (all pointing at siblings under `${TESTS_DIR}`)
  - [x] Implement `regex_self_probe()` covering the single boundary-guarded token owned by this story (`benji`): `echo "benjiman" | grep -iE "${BENJI_BOUNDARY_REGEX}"` must FAIL (exit non-zero); `echo "benji inbox" | grep -iE "${BENJI_BOUNDARY_REGEX}"` must SUCCEED. Fail-fast `fail "regex probe: ..."` on mismatch. This guards against a mis-parsing host grep before any content-level scan runs.
  - [x] Implement `check_task1` (baseline-absence-audit evidence): `require_file_exists` on `story-2-4-baseline-absence-audit.md`; `grep -Fq "Story 2.4 Baseline Absence Audit"` title; `grep -Fiq` for each required section header (`Current .cursor/rules/ inventory`, `gtd-life source`, `Absence-assertion scope`, `Complement to Story 2.3 content scrub`, `Banned-filename pattern lock`).
  - [x] Implement `check_task2` (file-absence assertions):
    - `[[ ! -e "${BANNED_RULE_PATH}" ]]` — fail with `banned rule file still present: ${BANNED_RULE_PATH}` if it exists (primary AC1)
    - Enumerate `"${RULES_DIR}"/*.mdc` `"${RULES_DIR}"/*.md` `"${RULES_DIR}"/*.markdown`; for each entry, extract basename and test with `[[ "$(basename "${entry}" | tr '[:upper:]' '[:lower:]')" =~ ${BENJI_BASENAME_PATTERN_LC} ]]` (lower-cased comparison) — reject anything whose basename begins with `benji`. Include a belt-and-suspenders loop over `"${RULES_DIR}"/*benji*` patterns with `[[ -e ... ]]` guards. (AC2 pattern-level)
    - Repository-wide check: `find "${PROJECT_ROOT}" -type f -name 'benji*.mdc' -not -path "${PROJECT_ROOT}/_bmad-output/*" -not -path "${PROJECT_ROOT}/.git/*" -not -path "${PROJECT_ROOT}/_bmad/*"` — output must be empty. Use `find ... -print | head -n1` and assert result is empty (BSD+GNU compatible).
  - [x] Implement `check_task3` (rule-pack integrity): for each file in `EXPECTED_RULE_FILES`, assert `[[ -f "${RULES_DIR}/${rule}" ]] && [[ -s "${RULES_DIR}/${rule}" ]]`. Also assert `[[ -f "${PERSONA_PATH}" ]] && [[ -s "${PERSONA_PATH}" ]]` (Story 2.3 artifact still present and non-empty). Assert `grep -Fq 'agents/personas/work.md' "${AGENT_IDENTITY_PATH}"` (Story 2.1 zero-edit verification that the identity rule still points at the persona — reuses the Story 2.3 zero-edit guard pattern).
  - [x] Implement `check_task4` (content-scrub parity probe): call `regex_self_probe`. Do NOT re-scan `agents/personas/work.md` for banned terms — that is explicitly Story 2.3's responsibility and duplicating the scan here would create coupling. This gate only proves the regex mechanism still works on the host.
  - [x] Implement `check_task5` (self-check): assert `head -n 1` equals `#!/usr/bin/env bash`; assert `grep -Fq 'set -euo pipefail'`; assert every `task1)` through `task6)` and `all)` case branch declared; assert every required constant present (`RULES_DIR=`, `BANNED_RULE_PATH=`, `BENJI_BASENAME_PATTERN=`, `BENJI_BOUNDARY_REGEX=`, `PERSONA_PATH=`, `AGENT_IDENTITY_PATH=`, `EXPECTED_RULE_FILES=`, `STORY_2_3_HARNESS=`); assert `regex_self_probe` function defined.
  - [x] Implement `check_task6` (regression): for each of the six predecessor harness paths, `require_file_exists` and invoke `bash "${harness}" all 2>&1`. Capture combined stdout/stderr; echo on non-zero exit per Story 2.2 Phase 4 F6 pattern; `fail` the gate with the sub-harness name on any non-zero exit. All six must return zero.
  - [x] Implement the `mode` dispatcher (`case "${mode}" in task1) check_task1 ;; ... all) check_task1; echo "PASS: task1"; check_task2; echo "PASS: task2"; ...; echo "PASS: task6" ;; esac`); terminate with `echo "PASS: ${mode}"`.
  - [x] Add a harness header comment block that states: (a) Story 2.4 is file-level absence assertion; (b) Story 2.3 owns content-level scrub of `agents/personas/work.md`; (c) the two scans are complementary, not duplicative; (d) the harness is additive over the Story 2.3 regression chain.

- [x] Task 3 — Placeholder / banned-term parity confirmation via regression (AC: 3, 6) **[Sequential — depends on Task 2 harness existing]**
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all` locally. Confirm it exits `0` with `PASS: all`. Confirm the Story 2.3 harness's `regex_self_probe` still exercises the `benji` boundary-guarded token (it does, per Story 2.3 lines 198–202 of the harness).
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh task4` (parity probe only). Confirm `PASS: task4`.
  - [x] Record in the Dev Agent Record: (a) Story 2.3 harness still green after Story 2.4 lands — no coupling; (b) Story 2.4's own parity probe is harness-local and does not duplicate Story 2.3 content scrub; (c) Story 2.3 boundary-guarded banned-term scan of `agents/personas/work.md` continues to catch content-level `benji` references (regression-proof).

- [x] Task 4 — Optional docs checklist line (AC: 4, 8) **[Independent; OPTIONAL — harness alone satisfies AC4]** — **SKIPPED by Dev agent; see Dev Agent Record for rationale.**
  - [x] Inspect `docs/setup.md` to confirm it exists and identify the safest trailing-insertion location (append a new `## Exclusions (not ported)` heading below the last existing H2). If `docs/setup.md` has no trailing heading pattern that accepts a new H2, skip this task entirely — the harness satisfies AC4 via the "OR" in the epic AC ("CI assertion OR checklist item"). — *Inspected; docs/setup.md exists with a trailing `## Troubleshooting` H2. Amelia elected to SKIP per the AC4 "OR" clause and the additive-only discipline (see Dev Agent Record).*
  - [x] If proceeding, add a single `## Exclusions (not ported)` section with one bullet of the form: `- `.cursor/rules/benji-inbox-default.mdc` — personal Benji task-system rule from gtd-life; intentionally excluded from the Vixxo work template. Absence enforced by `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh`.` Verify the added line contains zero additional banned terms beyond the filename itself (`benji` appears only as part of the banned-rule filename path, which is the correct evidence-citation form) and zero placeholder tokens. — *Not performed (task skipped).*
  - [x] If the docs edit is performed, re-run all six predecessor harnesses plus the Story 2.4 harness and verify no regression. If any regression occurs (e.g. a predecessor harness scans `docs/setup.md` and trips a banned-term guard), revert the docs edit and rely on the harness alone — document the revert in the Dev Agent Record. — *No docs edit performed; no regression risk introduced.*

- [x] Task 5 — Regression run (AC: 5, 6) **[Sequential — runs all prior gates]**
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all`. Capture the full transcript (every `PASS: <gate>` line plus the final `PASS: all`).
  - [x] Re-run `story-1-1` through `story-2-3` harnesses individually in `all` mode (six sub-harnesses). All six must exit `0` with `PASS: all`.
  - [x] Capture the full command-and-transcript log for inclusion in the Task 6 handoff artifact.

- [x] Task 6 — Handoff readiness package (AC: 4, 5, 6, 8) **[Sequential — depends on Task 5]**
  - [x] Persist `_bmad-output/implementation-artifacts/tests/story-2-4-task6-handoff.md` with:
    - An AC-to-file map (one row per AC with pointer to story file, harness gate, or grep output)
    - The full validation command transcript (Story 2.4 harness + six regression harnesses)
    - A forward-looking note: Epic 3 Story 3.1–3.3 will populate `memory/me/` and `memory/companies/` scaffolds — none of which may re-introduce a `benji-inbox-default.mdc` rule; the Story 2.4 harness will catch any such attempt via the repository-wide `find` check. Epic 6 Story 6.1–6.2 will add a shared PII denylist and GitHub Action; the Story 2.4 harness can be invoked directly from the GitHub Action as the rule-file-absence gate without modification (it exits 0 on pass and 1 on fail — standard CI contract).
    - A note confirming `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rules, and `agents/personas/work.md` are byte-for-byte unchanged (zero-edit verification).

- [x] Task 7 — Sprint tracker and story status synchronization (AC: 7) **[Independent; typically last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `2-4-confirm-benji-inbox-default-not-ported.status` from `backlog` to `ready-for-dev` during the story-creation Phase 1 (SM pass); then to `review` at Dev handoff per the Story 2.1 / 2.2 / 2.3 autonomous-swarm pattern (single on-disk transition acceptable). — *Autonomous-swarm collapse: on-disk transition is `backlog → review` in one write. Phase-1 `ready-for-dev` interim was transit-only, as in Story 2.1 / 2.2 / 2.3.*
  - [x] Preserve `epic-2.status` as `in-progress` (Story 2.4 is the final story in Epic 2; the `in-progress → done` transition for `epic-2.status` is explicitly OUT of this story's scope — it will be made as a separate evidence-only pass after Story 2.4 reaches `done` so Story 2.4's review doesn't mix two state transitions).
  - [x] Update `last_updated` in `sprint-status.yaml` to today's date (`2026-04-20`) on the Phase 1 edit. Do not introduce any other key change. — *`last_updated` already set to `2026-04-20` by the Phase 1 SM pass; no additional change required at Phase 2 handoff.*
  - [x] Preserve every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` byte-for-byte. The file is a human-curated YAML with inline comment sections that must not be reordered or stripped; the only diff between the pre-edit and post-edit files must be the single `status:` value change (and `last_updated` on Phase 1). — *Verified via `git diff`: single-line change `status: backlog` → `status: review`.*

## Dev Notes

### Artifact availability

- Available planning/tracking artifacts:
  - `_bmad/bmm/config.yaml` (BMAD v6.3.0, `user_name: Vixxo Employee`).
  - `_bmad-output/planning-artifacts/epics.md` (Epic 2 Story 2.4 at lines 241–250: the two-line AC pair).
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (story key `2-4-confirm-benji-inbox-default-not-ported`, Linear `AIP-32`, current status `backlog`; epic-2 currently `in-progress`).
  - Prior story files `1-1-scaffold-directory-structure-and-root-files.md`, `1-2-write-generic-readme-license-gitignore.md`, `1-3-write-generic-agents-claude-cursorrules.md`, `2-1-port-agent-identity-rule-generic.md`, `2-2-port-guardrail-and-formatting-rules.md`, `2-3-create-single-generic-work-persona.md` (pattern, validation-harness model, boundary-guard discipline, placeholder contract, regression chain).
  - Landed Story 2.1 / 2.2 / 2.3 artifacts under `.cursor/rules/` and `agents/personas/` (all byte-for-byte stable — Story 2.4 must not edit).
  - `~/Public/gtd-life/.cursor/rules/benji-inbox-default.mdc` — the gtd-life source rule that is explicitly NOT ported. Read for baseline audit only; never copy into this template.
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` (not present; rely on epics.md + sprint tracker).
  - `_bmad-output/planning-artifacts/architecture.md` (present but Story 2.4 has no UX / architectural impact — file-absence assertion with a bash harness is platform-neutral).
- Implementation anchors: Epic 2 Story 2.4 ACs (epics.md lines 241–250), the Story 2.3 harness POSIX-ERE boundary-guard pattern, the Story 2.2 Phase 4 F6 sub-harness-capture regression pattern, the `require_why_comment_terminator` helper (not used by Story 2.4 — no new content files — but referenced so the baseline audit can confirm the helper is not erroneously duplicated).

### Epic 2 story partition (why 2.4 is an absence-assertion-only story)

- Story 2.1 (done): `.cursor/rules/agent-identity.mdc` — identity + scope + MCP overview + persona pointer.
- Story 2.2 (done): four sibling `.cursor/rules/*.mdc` — outbound messaging, memory-vault protection, Teams DM formatting, email triage thread defaults. Introduced the boundary-guarded `benji` banned-term scan in the harness (Story 2.2 carryover).
- Story 2.3 (done): `agents/personas/work.md` — single generic Vixxo work persona. Banned-term scan extends the Story 2.2 alternation with `family` and boundary-guards `benji` in the content scan of the persona file.
- Story 2.4 (this story): File-level absence assertion for `.cursor/rules/benji-inbox-default.mdc`. No new persona, no new rule, no new content — the whole job is to install a CI/validation assertion that locks the exclusion in place and to complement (NOT supersede) the Story 2.3 content-scrub boundary guard.

Story 2.4 is deliberately minimal. It is the final story in Epic 2 and functions as a guardrail-only story: after it lands, any attempt to re-introduce `benji-inbox-default.mdc` (accidentally, by a port-everything script, or via a copy-paste merge) fails CI / fails the harness.

### Why a harness and not a git pre-commit hook

The epic AC ("CI assertion OR checklist item") leaves the implementation mechanism open. Three candidates:

1. **Deterministic bash harness under `_bmad-output/implementation-artifacts/tests/`** (this story's chosen approach) — consistent with Stories 2.1 / 2.2 / 2.3; invokable locally; invokable from CI; zero-cost regression chain; no new repo-level infrastructure. CHOSEN.
2. **Git pre-commit hook** — would block the local commit. Rejected: requires opt-in setup (`git config core.hooksPath`), is not enforced on forks, and does not run against already-committed state. Epic 6 will own the proper GitHub-Action-level CI check; Story 2.4 adds the harness that Epic 6 can invoke.
3. **CI-only check (GitHub Action)** — would depend on an Actions workflow that does not yet exist in this repo. Rejected for this story: Epic 6 Story 6.2 is the proper home for a GitHub Action, and the Story 2.4 harness is the primitive that Epic 6 will invoke. Wiring the Action here would over-reach Story 2.4's scope.

Default choice: **harness**. The harness is callable from any future CI orchestration (GitHub Action, pre-commit hook, local `make test` target), so choosing it now does not foreclose any of those options — it is the lowest-level primitive.

### Pattern-level vs filename-specific absence

The epic spells out only the specific filename `benji-inbox-default.mdc`. AC2 widens the assertion to the `benji*` pattern (case-insensitive) so a rename like `benji-inbox-default-v2.mdc`, `benji-tasks.mdc`, or `benji-default-inbox.mdc` cannot bypass the check. This is the same philosophy as Story 2.3's banned-term boundary guards: the canonical instance is the primary target, but the pattern-level assertion is what keeps the regression-proof property under future drift.

The pattern is intentionally scoped to `.cursor/rules/` (plus a repository-wide `find` that excludes evidence directories). Persona files, memory files, docs, and BMAD evidence legitimately reference the banned filename in spec/regex/scrub form; we do NOT want to block those. The persona-body content-scrub of the literal token `benji` is already owned by Story 2.3's boundary-guarded scan; Story 2.4 does not duplicate it.

### Complement to Story 2.3 (not a replacement)

Two independent assertions are required:

- **Story 2.3 content scrub** (already landed): `agents/personas/work.md` contains zero occurrences of the literal token `benji` (boundary-guarded: `(^|[^A-Za-z])benji($|[^A-Za-z])`). This catches content-level leakage (e.g. a copy-paste of a gtd-life persona paragraph that mentions "Benji inbox").
- **Story 2.4 file absence** (this story): `.cursor/rules/benji-inbox-default.mdc` does not exist as a file; no `benji*.mdc` rule file exists under `.cursor/rules/`. This catches file-level leakage (e.g. a port-all script that copies the whole `.cursor/rules/` tree from gtd-life).

Both assertions together = defense-in-depth. Either assertion alone leaves a gap: content-scrub alone does not prevent a file from being added (the file's content might be generic or empty); file-absence alone does not prevent content references in other files. Story 2.4 explicitly adds the second half; it does NOT modify Story 2.3's scan.

### Previous story learnings to carry forward

- Story 2.1 / 2.2 / 2.3: POSIX-ERE boundary guards `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` work on macOS BSD grep, GNU grep, and busybox/Alpine grep identically — do NOT use `\b` (GNU word-boundary) in portable harnesses.
- Story 2.1 / 2.2 / 2.3: `regex_self_probe` fail-fast guard catches a mis-parsing host grep before any scrubbing scan silently fails open. Story 2.4 reuses this helper with a single token (`benji`).
- Story 2.2 Phase 4 F6: sub-harness invocations in the regression gate must capture combined stdout/stderr and echo on non-zero exit so a downstream regression surfaces the offending gate name. Story 2.4's `check_task6` reuses the Phase-4-fixed pattern.
- Story 2.3: the autonomous-swarm lifecycle collapses `backlog → ready-for-dev → review` into one on-disk transition per story (interim states transit-only). Story 2.4 may follow the same pattern; record the skipped hops in the Change Log if so.
- Story 2.3: harness sections are declared with a `# -----` ASCII separator comment block between each `check_taskN` function; Story 2.4 follows the same visual convention for grep-ability.
- Epic 2 commit style (from git log): `feat(epic-2): <change> (Story <key>)`. Story 2.4 commits should follow `feat(epic-2): confirm benji-inbox-default is not ported (Story 2-4-confirm-benji-inbox-default-not-ported)`.

### Architectural constraints

- No runtime service, no application code, no web surface — Story 2.4 is pure file-system absence assertion + shell harness.
- No new dependencies: `bash` + `grep` + `find` + `awk` + `sed` are universally available on macOS and Linux developer machines and on standard CI images (GitHub Actions `ubuntu-latest`, `macos-latest`). `rg` is NOT required (deliberately — stay portable).
- The harness must be BSD-grep and GNU-grep compatible. Use `grep -E` for ERE, `grep -F` for literals, `-i` for case-insensitive, `[[ ! -e ... ]]` for existence tests, `find -name` for filename glob. Do not use `\b`, `\<`, `\>`, `(?:...)`, or Perl-compatible regex syntax.
- The harness must not mutate global shell state (no `shopt -s nocaseglob`, no `LANG=` reassignment); all case-insensitive logic is per-invocation via `grep -i` or `tr '[:upper:]' '[:lower:]'`.
- macOS / Linux portability: `find ... -print | head -n1` is BSD+GNU compatible; avoid GNU-only `find -printf`.

### Project Structure Notes

- Target files for this story (new):
  - `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh` (executable, Task 2)
  - `_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md` (Task 1)
  - `_bmad-output/implementation-artifacts/tests/story-2-4-task6-handoff.md` (Task 6)
- Target files for this story (modified):
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 — `2-4-confirm-benji-inbox-default-not-ported.status` flip + `last_updated`)
  - This story file (Dev Agent Record / Change Log / File List / checkboxes)
  - Optionally `docs/setup.md` (Task 4 — one-line exclusion checklist; skip if it causes any regression)
- Directory state expectations AFTER Story 2.4 lands:
  - `.cursor/rules/` contains exactly `.gitkeep`, `agent-identity.mdc`, `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc` (six entries; zero `benji*` entries).
  - `agents/personas/` contains exactly `.gitkeep` and `work.md` (Story 2.3 output; Story 2.4 does not touch).
  - All Story 1.x and Story 2.1 / 2.2 / 2.3 artifacts remain byte-for-byte stable.
- Forward-compatibility:
  - Epic 3 Stories 3.1–3.3 will populate `memory/` scaffolds. Story 2.4's `find` gate will catch any accidental `benji*.mdc` copy into `memory/` or adjacent paths.
  - Epic 4 Story 4.1 / 4.2 will wire `.cursor/mcp.json`; none of those MCP entries may reference Benji (Story 2.3 persona scrub already enforces `Benji` absence in the persona body; Story 2.4 does not scan `.cursor/mcp.json`).
  - Epic 6 Story 6.2 (GitHub Action) can invoke `bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all` directly as a CI gate. The harness contract (exit 0 on pass, 1 on fail, PASS/FAIL lines on stderr/stdout) is GitHub-Actions-native.

### Testing Notes

- Suggested manual commands:
  - `[[ ! -e .cursor/rules/benji-inbox-default.mdc ]] && echo PASS || echo FAIL`
  - `ls .cursor/rules/ | grep -i '^benji' && echo 'FAIL: benji-prefixed rule found' || echo 'PASS: no benji-prefixed rule'`
  - `find . -type f -name 'benji*.mdc' -not -path './_bmad-output/*' -not -path './.git/*' -not -path './_bmad/*'` (expect empty output)
  - `bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all`
- Regression (each must exit 0 with `PASS: all`):
  - `bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all`
- Keep the Story 2.4 harness self-contained (no network, no external tools beyond `bash`, `grep`, `find`, `awk`, `sed`).

### Parallelization guidance

- Task 1 (baseline absence audit) and Task 2 (harness authoring) are pairwise parallelizable — they write to distinct files under `_bmad-output/implementation-artifacts/tests/` and share no runtime state. A Dev swarm may run them concurrently in two subagents.
- Task 3 (parity confirmation) is sequential — depends on Task 2 harness existing.
- Task 4 (optional docs checklist) is independent of Tasks 1/2/3 and Task 5, but should run BEFORE Task 5 so the regression run covers the docs edit. If skipped, Task 5 proceeds unchanged.
- Task 5 (regression run) is sequential — runs the new harness + all six predecessor harnesses after Tasks 1, 2, 3 (and optionally 4) land.
- Task 6 (handoff) is sequential — depends on Task 5's transcript.
- Task 7 (sprint tracker) is independent; the Phase 1 `backlog → ready-for-dev` flip is the SM-pass edit made when this story file is authored, the Phase 2 `ready-for-dev → review` flip is the Dev handoff edit.

**Swarm parallelization summary:**

- **Parallel pair at story start:** Task 1 (baseline audit) || Task 2 (harness authoring) can run concurrently.
- **Sequential after parallel pair:** Task 3 (parity probe, needs harness) → Task 4 (optional docs) → Task 5 (regression) → Task 6 (handoff).
- **Independent throughout:** Task 7 (sprint tracker) can run at any time after Phase 1 or Phase 2.
- **Shared-file contention:** None across Tasks 1–6 (each writes to a distinct test/evidence file); Task 7 has exclusive write on `sprint-status.yaml`; this story file itself is written by every task — serialize story-file edits per task or batch at the end of each pass.

### References

- `_bmad/bmm/config.yaml` (BMAD module metadata, artifact path variables, version context).
- `_bmad-output/planning-artifacts/epics.md` lines 241–250 (Epic 2 Story 2.4 statement and acceptance criteria — the source of truth).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` lines 93–96 (story key `2-4-confirm-benji-inbox-default-not-ported`, Linear `AIP-32`, initial status `backlog`).
- `_bmad-output/implementation-artifacts/2-1-port-agent-identity-rule-generic.md` (POSIX-ERE banned-term regex, `regex_self_probe`).
- `_bmad-output/implementation-artifacts/2-2-port-guardrail-and-formatting-rules.md` (Story 2.2 Phase 4 F6 sub-harness-capture pattern; consolidated banned-term set including `benji`).
- `_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md` (Story 2.3 harness pattern — boundary-guarded `benji` content scrub; six-gate `task1`–`task6` + `all` dispatcher; Phase 4 fixes F1–F6).
- `_bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh` (harness pattern to inherit — banned-term regex, self-check, regression invocation).
- `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (harness pattern — F1–F6 Phase 4 improvements).
- `_bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh` lines 100 (banned-terms regex with boundary-guarded `benji`), 198–202 (benji self-probe), 662–691 (regression gate with F6 sub-harness capture) — primary pattern to model for Story 2.4.
- `.cursor/rules/agent-identity.mdc` (Story 2.1 output; must remain byte-for-byte unchanged in Story 2.4).
- `.cursor/rules/outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc` (Story 2.2 output; must remain byte-for-byte unchanged in Story 2.4).
- `agents/personas/work.md` (Story 2.3 output; must remain byte-for-byte unchanged in Story 2.4).
- `~/Public/gtd-life/.cursor/rules/benji-inbox-default.mdc` (gtd-life source of record — reference for baseline audit only; never ported).
- Git log (`git log --oneline -n 15`) for recent Epic 2 commit style: `feat(epic-2): <change> (Story <key>)`. Story 2.4 commit should follow: `feat(epic-2): confirm benji-inbox-default is not ported (Story 2-4-confirm-benji-inbox-default-not-ported)`.

## Change Log

- 2026-04-20 (Phase 1, Bob — SM): Story file authored from Epic 2 Story 2.4 spec (epics.md lines 241–250). `sprint-status.yaml` flipped `2-4-confirm-benji-inbox-default-not-ported.status` `backlog → ready-for-dev` and `last_updated` updated to `2026-04-20`. `epic-2.status` remains `in-progress` (Story 2.4 is the final Epic 2 story; the `in-progress → done` transition for `epic-2.status` is explicitly deferred to a separate evidence-only pass after Story 2.4 reaches `done`). Ready for Phase 2 Dev swarm pickup.
- 2026-04-20 (Phase 2, Amelia — Dev): All seven tasks executed (Task 4 skipped by design per AC4 "OR" clause). Created three new artifacts under `_bmad-output/implementation-artifacts/tests/`: the baseline absence audit (Task 1), the deterministic absence-validation harness (Task 2, `chmod +x`, POSIX-bash-3.2, BSD+GNU-grep compatible), and the Task 6 handoff package. Harness gates `task1`–`task6` all pass individually; `all` mode emits six per-gate `PASS:` lines plus final `PASS: all` and exits `0`. Six predecessor harnesses (Story 1.1, 1.2, 1.3, 2.1, 2.2, 2.3) all exit `0` with their contractual `PASS: all` from the `task6` regression gate and from direct invocation. Rule pack, persona, and root context files verified via the `task3` rule-pack integrity gate as present and non-empty with the `agent-identity.mdc → agents/personas/work.md` pointer preserved (the harness does not pin a byte-level checksum; see review fix F5 for the scope clarification). `docs/setup.md` untouched (Task 4 skipped). Sprint status collapsed `backlog → review` in a single on-disk transition per the Story 2.1 / 2.2 / 2.3 autonomous-swarm precedent. Story status flipped to `review`. Ready for Phase 3 code review.
- 2026-04-20 (Phase 4, Amelia — Review follow-up): Six adversarial-review findings resolved in one pass. F1 (HIGH, AC2) — `.cursor/rules/` enumeration made case-insensitive: replaced the extension-indexed `*."${ext}"` globs and the three-variant belt-and-suspenders glob with a single `for entry in "${RULES_DIR}"/*` loop that lowercases basenames and rejects any rule-shaped entry containing `benji`; both `find` invocations now use `-iname`. F2 (MEDIUM, doc) — baseline absence audit corrected to list `.cursor/rules/.gitkeep` and `agents/personas/.gitkeep` as preserved Story 1.1 sentinels. F3 (MEDIUM, AC1) — dropped the undocumented `_bmad/` exclusion from both repo-wide `find` invocations to realign with AC1 verbatim (independently verified: `_bmad/` contains zero benji files). F4 (MEDIUM) — `check_task5` now uses `declare -F regex_self_probe` to prove the probe is a callable function rather than a substring in the file. F5 (MEDIUM) — downgraded the "zero bytes changed" Dev claim to "present and non-empty with identity-rule pointer preserved" so the Dev Agent Record matches what the harness actually enforces. F6 (LOW) — removed the dead `:` no-op + tautological `gate == 'task4'` block in `check_task4` and replaced with a meaningful `BENJI_BOUNDARY_REGEX` presence assertion. Final harness run after fixes: Story 2.4 `PASS: all`; full regression (1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4) all green. Story 2.4 marked `done`.

## Dev Agent Record

### Agent Model Used

Amelia (BMAD autonomous Developer, Claude Opus 4.7) via `bmad-story-dev.md` subagent prompt. Execution mode: autonomous (no user interaction). Parent agent session: Cursor IDE on darwin 25.4.0.

### Debug Log References

Harness development iterated once — the first draft passed all gates on the first `all`-mode run, so no debug iteration was required. Per-gate smoke check and six-harness regression both green on first invocation. No 3-consecutive-failure halt conditions triggered.

Relevant command transcripts (full form in `story-2-4-task6-handoff.md`):

- `bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all` → `PASS: task1` … `PASS: task6` … `PASS: all`; exit `0` (elapsed ~24s, dominated by six predecessor regression harnesses).
- Six predecessor harnesses direct: Story 1.1 `PASS: all`, Story 1.2 `PASS: all`, Story 1.3 `PASS: all`, Story 2.1 `PASS: all`, Story 2.2 `PASS: task1`–`PASS: task9` + `PASS: all`, Story 2.3 `PASS: task1`–`PASS: task6` + `PASS: all`. All six exit `0`.
- `git diff _bmad-output/implementation-artifacts/sprint-status.yaml` → single-line `status: backlog` → `status: review` on the `2-4-confirm-benji-inbox-default-not-ported` entry; no other byte changed.
- `git status --short` → `M sprint-status.yaml`; three new untracked files under `_bmad-output/implementation-artifacts/tests/`; this story file is untracked (Phase 1 SM pass left the file on disk without committing). No other repository files modified.

### Completion Notes List

- **Task 1** — Baseline absence audit authored at `_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md` with all required sections (inventory, gtd-life source reference, absence-assertion scope, Story 2.3 complement, banned-filename pattern lock, plus a rule-pack integrity section). `check_task1` verifies the title and all five required section keywords via `grep -Fiq`.
- **Task 2** — Harness authored at `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh`, `chmod +x`, shebang on line 1, `set -euo pipefail` on line 2. All 13 required constants declared (`RULES_DIR`, `BANNED_RULE_PATH`, `BENJI_BASENAME_PATTERN`, `BENJI_BOUNDARY_REGEX`, `PERSONA_PATH`, `AGENT_IDENTITY_PATH`, `EXPECTED_RULE_FILES`, six prior-harness paths). `regex_self_probe` exercises `benjiman` (negative) and `benji inbox` (positive) against `grep -iE "${BENJI_BOUNDARY_REGEX}"`. `check_task2` implements AC1 primary (`[[ ! -e ... ]]`), AC2 pattern-level (basename prefix via lowercased `[[ =~ ]]` + substring shape case statement), and repository-wide `find` excluding `_bmad-output/`, `_bmad/`, `.git/` for `.mdc`, `.md`, `.markdown` variants. `check_task3` enforces rule-pack integrity for five `.mdc` files plus `agents/personas/work.md` plus the zero-edit guard that `agent-identity.mdc` still references the persona path. `check_task4` calls `regex_self_probe` only (no duplicate content scan of Story 2.3's persona scope). `check_task5` self-checks shebang, `set -euo pipefail`, all 7 case arms, all 13 constants, and the `regex_self_probe` function. `check_task6` captures combined stdout/stderr per Story 2.2 Phase 4 F6 for all six predecessor harnesses.
- **Task 3** — Parity confirmation: Story 2.3 harness runs green independently (`PASS: all`, exit `0`); Story 2.4 `task4` gate also passes (`PASS: task4`). Confirmed: (a) Story 2.3 harness remains byte-for-byte unchanged and green after Story 2.4 lands (no coupling introduced); (b) Story 2.4's `regex_self_probe` is harness-local and operates on synthetic input only — it does not duplicate Story 2.3's persona scrub; (c) Story 2.3's boundary-guarded banned-term scan of `agents/personas/work.md` continues to catch content-level `benji` references (the two scans layer as defense-in-depth).
- **Task 4** — SKIPPED by design. Rationale: AC4 uses an "OR" between CI assertion and checklist item; the Story 2.4 harness satisfies the CI-assertion half on its own. While no current predecessor harness scans `docs/setup.md` for banned-term content, adding a new `## Exclusions (not ported)` section with a citation of the banned filename introduces content containing the literal `benji` token at a path that a future cross-pack parity scan could legitimately add to its scope. Skipping preserves `docs/setup.md` byte-for-byte, reduces diff surface, and remains consistent with AC8's additive-only contract. The story's Task 4 subtask explicitly includes the "if regression occurs, revert and rely on harness alone" escape hatch; exercising it preemptively at zero cost is the conservative choice. See `story-2-4-task6-handoff.md` "Task 4 skip rationale" for the full decision record.
- **Task 5** — Regression run green. Story 2.4 `all` mode: `PASS: task1` → `PASS: task6` → `PASS: all`, exit `0`. Six predecessor harnesses in `all` mode: each exits `0` with `PASS: all`. Full command transcript captured in `story-2-4-task6-handoff.md` under "Full validation command transcript".
- **Task 6** — Handoff package authored at `_bmad-output/implementation-artifacts/tests/story-2-4-task6-handoff.md` with AC-to-file evidence map (every AC1–AC8 clause pointed at its gate/file/section), full validation transcript, zero-edit verification block, and forward-looking Epic 3 / Epic 4 / Epic 6 / Epic 7 notes. Epic 6 Story 6.2 GitHub Action snippet included to show the harness is CI-ready with no modification.
- **Task 7** — Sprint tracker flip: `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `2-4-confirm-benji-inbox-default-not-ported.status` updated to `review`. On-disk transition was `backlog → review` in one write (autonomous-swarm collapse per Story 2.1 / 2.2 / 2.3 precedent). `epic-2.status` preserved as `in-progress` byte-for-byte. `last_updated` already at `2026-04-20` from the Phase 1 edit. No other byte changed in the tracker; `git diff` confirms single-line value change.

### File List

**Created (3):**

- `_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md` (Task 1 evidence artifact)
- `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh` (Task 2 deterministic harness; `chmod +x`; POSIX-bash-3.2; BSD+GNU-grep compatible)
- `_bmad-output/implementation-artifacts/tests/story-2-4-task6-handoff.md` (Task 6 handoff package)

**Modified (2):**

- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7: single-line status flip `backlog → review` on the `2-4-confirm-benji-inbox-default-not-ported` entry; all other bytes preserved)
- `_bmad-output/implementation-artifacts/2-4-confirm-benji-inbox-default-not-ported.md` (this story file: Status line flipped to `review`; checkboxes marked `[x]`; Dev Agent Record / Change Log / File List populated)

**Unchanged (verified via harness + git):**

- `.cursor/rules/agent-identity.mdc` (Story 2.1 — `task3` asserts file is present, non-empty, and still contains the `agents/personas/work.md` pointer; full byte-for-byte identity is verified via `git diff HEAD`)
- `.cursor/rules/outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc` (Story 2.2 — same check shape)
- `agents/personas/work.md` (Story 2.3 — same check shape)
- `AGENTS.md`, `CLAUDE.md`, `.cursorrules` (Story 1.3 — regression harness asserts their presence and content shape)
- `README.md`, `LICENSE`, `.gitignore` (Story 1.2 — same)
- `docs/setup.md`, `docs/legal/*` (Task 4 SKIP preserves these; `git status` confirms)
- All prior harnesses under `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3}-*.sh` (Story 2.4's `task6` invokes them; does not edit them)

## Review Follow-ups (AI)

- [x] **F1 (HIGH, AC2)** — Made `.cursor/rules/` enumeration and both repo-wide `find` invocations case-insensitive. Extension-indexed globs replaced with a case-blind `for entry in "${RULES_DIR}"/*` loop that lowercases basename and checks the lowercased extension against the allowlist before running the `benji` substring and `BENJI_BASENAME_PATTERN` checks.
- [x] **F2 (MEDIUM, doc)** — Corrected baseline audit's `.cursor/rules/` inventory to include `.gitkeep`; added a note that `agents/personas/` also contains both `work.md` and a zero-byte `.gitkeep`; removed the incorrect "superseded by the Story 2.1 / 2.2 rule pack" sentence.
- [x] **F3 (MEDIUM, AC1)** — Dropped `-not -path "${PROJECT_ROOT}/_bmad/*"` from both `find` invocations so the harness's exclusion set matches AC1 verbatim (`_bmad-output/` + `.git/` only). Verified `_bmad/` has zero benji files; harness still green.
- [x] **F4 (MEDIUM, test-quality)** — `check_task5` probe-presence check switched from `grep -Fq 'regex_self_probe'` to `declare -F regex_self_probe >/dev/null 2>&1`; a commented-out or deleted function body can no longer satisfy the gate.
- [x] **F5 (MEDIUM, AC6)** — Downgraded the "zero bytes changed" Dev claim in the Change Log and File List to "present and non-empty with identity-rule pointer preserved" so Dev claims match what the harness enforces (`-f` + `-s` + one specific `grep -Fq` pointer assertion). Full byte-for-byte identity remains verifiable via `git diff HEAD`.
- [x] **F6 (LOW, code-quality)** — Removed the `:` no-op and tautological `[[ "${gate}" == "task4" ]]` comparison in `check_task4`; replaced with a meaningful `[[ -n "${BENJI_BOUNDARY_REGEX:-}" ]]` presence assertion on the boundary-guard constant.

## Senior Developer Review (AI)

**Reviewer:** Adversarial Code Reviewer (BMAD Phase 3 subagent — Claude Opus 4.7).
**Review Date:** 2026-04-20.
**Recommendation (pre-fix):** CHANGES_REQUESTED (6 findings).
**Recommendation (post-fix):** APPROVE — every finding resolved on disk; Story 2.4 harness plus all six regression harnesses (Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3) exit 0 with contractual `PASS:` lines.

### Findings and resolution

| ID | Severity | Category | File | Description | Resolution |
| --- | --- | --- | --- | --- | --- |
| F1 | HIGH | AC_MISSING | `tests/story-2-4-benji-inbox-absence-validation.sh` | `.cursor/rules/` enumeration and repo-wide `find` were case-sensitive, violating AC2's case-insensitive contract on case-sensitive filesystems (Linux CI). | Rewrote the `.cursor/rules/` scan to iterate all files, lowercase both basename and extension, and check for `benji` substring. Both repo-wide `find` invocations now use `-iname`. |
| F2 | MEDIUM | DOCUMENTATION | `tests/story-2-4-baseline-absence-audit.md` | Audit claimed no `.gitkeep` in `.cursor/rules/` — factually wrong; Story 1.1 sentinel is preserved. | Corrected both `.cursor/rules/` and `agents/personas/` inventory paragraphs; removed the bad "superseded" claim. |
| F3 | MEDIUM | AC_MISSING | `tests/story-2-4-benji-inbox-absence-validation.sh` | Harness silently excluded `_bmad/` from repo-wide scan; AC1 lists only `_bmad-output/` + `.git/`. | Dropped the `_bmad/` exclusion from both `find` invocations. Independent `find _bmad -iname 'benji*'` confirms zero collateral damage. |
| F4 | MEDIUM | TEST_QUALITY | `tests/story-2-4-benji-inbox-absence-validation.sh` | `regex_self_probe` presence check was a substring grep, not a function-definition check. | Replaced with `declare -F regex_self_probe >/dev/null 2>&1`. |
| F5 | MEDIUM | AC_MISSING | `2-4-confirm-benji-inbox-default-not-ported.md` | Dev Agent Record claimed "zero bytes changed" but the harness only asserts `-f` + `-s` + one pointer-string grep. | Downgraded the prose to match what the harness actually enforces; pointed readers at `git diff HEAD` for full byte-for-byte verification. |
| F6 | LOW | CODE_QUALITY | `tests/story-2-4-benji-inbox-absence-validation.sh` | `check_task4` contained a `:` no-op + tautological `gate == 'task4'` comparison. | Replaced with `[[ -n "${BENJI_BOUNDARY_REGEX:-}" ]]`. |

### Test evidence after fixes

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
```

Full regression (Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4) — every harness exits 0 with its `PASS: all`. Story 2.2 prints 9 per-task passes, Story 2.3 prints 6 per-task passes, Story 2.4 prints 6 per-task passes; others print only `PASS: all`.

### Non-blocking observations

- AC7 (sprint-tracker lifecycle) and AC8 (diff-shape) remain evidence-only — no harness gate reads `sprint-status.yaml` or counts created files. This matches Story 2.1 / 2.2 / 2.3 precedent.
- Epic-2 `in-progress → done` transition is intentionally OUT of Story 2.4 scope; a separate evidence-only pass flips it after Story 2.4 is `done`.
