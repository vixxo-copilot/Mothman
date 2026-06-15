# Story 5.2: Wizard prompts and file generation

Status: done

## Story

As a Vixxo employee running `./bin/init` after cloning `assistants-template`,
I want the setup wizard to prompt for my name, email, role/title, and optional MCP interests, then generate my `memory/me/identity.md` and `agents/personas/work.md` files and copy `.env.example` to `.env`,
so that my local template is personalized without manual edits and remains aligned with the existing Epic 4 and Epic 5 scaffolding.

## Acceptance Criteria

1. **AC1 - `bin/init` enters an interactive wizard flow in normal mode, while preserving fast-path flags**
   - Given `bin/init` from Story 5.1 and `prompts@2.4.2` installed from root `package.json`
   - When the user runs `./bin/init` with no flags
   - Then the script performs dependency bootstrap (`npm install` first-run behavior) and then runs a `prompts`-driven interactive flow in CommonJS mode (`require('prompts')`)
   - And when the user runs `./bin/init --help|-h` or `./bin/init --version|-v`, the script exits successfully without invoking interactive prompts
   - And no bash-specific code is introduced; `bin/init` remains Node-only and portable for macOS/Linux

2. **AC2 - Prompt set and validation rules are deterministic and complete**
   - Given the interactive flow
   - When prompts are displayed
   - Then the wizard asks, in order:
     1) employee name (required, trimmed, non-empty)
     2) employee email (required, trimmed, basic email format validation)
     3) Vixxo role/title (required, trimmed, non-empty)
     4) optional MCPs (multiselect using canonical server-key labels from `docs/mcps.md`)
   - And validation errors are shown inline via `prompts` `validate` callbacks until valid input is provided
   - And prompt labels and help text are work-only and contain no Derek/PII carryover tokens

3. **AC3 - Cancel behavior is explicit and side-effect safe**
   - Given any prompt in the wizard
   - When the user cancels (`esc`, `ctrl+c`, `ctrl+d`)
   - Then `onCancel` is invoked and the script exits with a non-zero code
   - And no target file is created or modified (`memory/me/identity.md`, `agents/personas/work.md`, `.env`)
   - And stderr prints a concise cancellation message that includes recovery guidance (`re-run ./bin/init`)

4. **AC4 - Identity file is generated deterministically from prompt answers**
   - Given valid prompt answers
   - When generation completes
   - Then `memory/me/identity.md` is overwritten atomically with deterministic content and trailing newline
   - And frontmatter values `name`, `role`, `department`/role mapping, `manager` placeholder policy, and `email` reflect prompt answers according to the story's mapping rules
   - And `scope: work` remains intact, no personal context is introduced, and template placeholders are not left behind for answered fields
   - And the file includes an `## Optional MCPs` section listing selected MCP server keys (or `none selected` when empty)

5. **AC5 - Work persona file is generated deterministically from prompt answers**
   - Given valid prompt answers
   - When generation completes
   - Then `agents/personas/work.md` is overwritten atomically with deterministic content and trailing newline
   - And frontmatter fields `name`, `role`, `department`, and `manager` are populated from prompt answers
   - And body sections remain work-scoped and preserve the active MCP table discipline from Story 2.3 (Linear, GitHub, Microsoft 365, Salesforce, Gong) unless explicitly changed by this story's blueprint
   - And no unresolved `{{employee_*}}` placeholders remain for fields answered by the wizard

6. **AC6 - `.env.example` to `.env` copy behavior is safe and idempotent**
   - Given repository root contains `.env.example`
   - When the wizard runs
   - Then `.env` is created from `.env.example` when `.env` does not exist
   - And copied values remain blank/commented (no secret material is inserted by the wizard)
   - And when `.env` already exists, the wizard prompts for overwrite confirmation; default behavior is no overwrite
   - And copy logic preserves `.env.example` content unchanged

7. **AC7 - File-write safety and path safety guardrails are implemented**
   - Given all generated output paths
   - When writes occur
   - Then writes use deterministic rendering and an atomic temp-file-plus-rename strategy in the destination directory
   - And target path resolution is constrained to repo-root descendants (no path traversal from prompt data)
   - And writes are serialized (no concurrent overlapping writes to the same file)
   - And generated files are UTF-8, LF-only, and newline-terminated

8. **AC8 - Generated content remains compliant with existing scrub and scope rules**
   - Given generated identity/persona files and `.env` copy behavior
   - When Story 4.x secret/banned/path scans are applied to generated content (with expected allowlist handling where required)
   - Then no new secret-shaped literals are introduced by the wizard
   - And no Derek fixed strings, gtd-life absolute paths, or personal-context banned terms are introduced by generation logic
   - And outputs remain explicitly work-only (`scope: work`, work-context wording)

9. **AC9 - Story 5.2 does not pre-implement Story 5.3 responsibilities**
   - Given Epic 5 scope boundaries
   - When Story 5.2 implementation is reviewed
   - Then it does not run `npx skills add vixxo-copilot/agent-skills`
   - And it does not execute active-MCP health verification calls
   - And it does not alter CI/PII guardrail workflows from Epic 6

10. **AC10 - Deterministic validation harness exists for Story 5.2**
    - Given `_bmad-output/implementation-artifacts/tests`
    - When Story 5.2 lands
    - Then `story-5-2-wizard-prompts-and-file-generation-validation.sh` exists, is executable, and follows the established gate pattern (`task1..taskN`, `all`)
    - And harness gates verify prompt schema wiring, cancellation behavior, deterministic rendering, atomic writes, `.env` copy semantics, and no-scope-creep rules
    - And harness includes a non-interactive test path using `prompts.inject(...)` driven by fixture input so CI/local validation is deterministic

11. **AC11 - Regression strategy is explicit for superseded scaffolds**
    - Given Story 5.2 intentionally rewrites Story 2.3/3.3 scaffold placeholders with concrete employee values
    - When regression is executed
    - Then unaffected predecessor harnesses remain green (Stories 1.1, 1.2, 1.3, 2.1, 2.2, 2.4, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4)
    - And superseded scaffold checks from Stories 2.3 and 3.3 are replaced by Story 5.2 compatibility assertions in the new harness (shape/scope checks rather than placeholder-presence checks)
    - And Story 5.1 compatibility is validated via retained fast paths (`--help`, `--version`) and bootstrap behavior instead of requiring the Story 5.1 scaffold banner to remain the default runtime output

12. **AC12 - Sprint tracker lifecycle updates for Story 5.2 are applied**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When this story is created
    - Then `5-2-wizard-prompts-and-file-generation.status` is set `backlog -> ready-for-dev`
    - And `epic-5.status` remains `in-progress`
    - And file comments/order/formatting are preserved

## Tasks / Subtasks

- [x] **Task 1 - Baseline and blueprint audit for Story 5.2 (AC: 1, 2, 4, 5, 6, 7, 11)**
  - [x] Read current `bin/init`, `package.json`, `memory/me/identity.md`, `agents/personas/work.md`, `.env.example`, `docs/setup.md`, and `docs/mcps.md` and lock expected pre-change fingerprints.
  - [x] Produce `story-5-2-baseline-audit.md` documenting superseded scaffolds (Story 2.3/3.3 placeholders) vs unchanged artifacts.
  - [x] Produce `story-5-2-canonical-blueprint.md` defining final prompt schema, render templates, and `.env` overwrite decision flow.
  - [x] Record mapping rules for `manager` and `department` when only role/title is collected (explicit deterministic fallback policy).
  - [x] Lock canonical optional-MCP source list from `docs/mcps.md` table order.

- [x] **Task 2 - Implement prompt orchestration in `bin/init` (AC: 1, 2, 3, 9)**
  - [x] Add `prompts` flow after dependency bootstrap in default execution path.
  - [x] Implement `validate` callbacks for required text/email fields.
  - [x] Implement multiselect prompt for optional MCPs using canonical server-key labels.
  - [x] Implement `onCancel` handling that exits non-zero before any write side effects.
  - [x] Preserve `--help`/`--version` fast paths and Story 5.1 bootstrap semantics.
  - [x] Keep script CommonJS and Node-only (no shell delegation).

- [x] **Task 3 - Implement deterministic renderers for generated files (AC: 4, 5, 7, 8)**
  - [x] Add pure render function for `memory/me/identity.md` from normalized answers.
  - [x] Add pure render function for `agents/personas/work.md` from normalized answers.
  - [x] Add explicit `## Optional MCPs` section generation rule in identity output.
  - [x] Ensure generated markdown is LF-only, UTF-8, and newline-terminated.
  - [x] Ensure work-only phrasing and no personal-content carryover in rendered text.

- [x] **Task 4 - Implement safe write/copy operations (AC: 6, 7)**
  - [x] Implement `writeAtomic(targetPath, content)` using temp file in same directory plus `rename`.
  - [x] Add repo-root path guard helper before all writes/copies.
  - [x] Write identity and persona files via atomic helper.
  - [x] Implement `.env` copy from `.env.example` when missing.
  - [x] Add overwrite confirm prompt when `.env` exists; default to keep existing.
  - [x] Emit concise summary of changed/skipped files.

- [x] **Task 5 - Add deterministic non-interactive test mode (AC: 10)**
  - [x] Add fixture-driven injection path (`prompts.inject`) for automated validation.
  - [x] Support fixture cancellation simulation via injected `Error`.
  - [x] Ensure test mode is opt-in via environment flag and does not affect normal users.
  - [x] Add explicit guards for invalid fixture payload shape.

- [x] **Task 6 - Author Story 5.2 validation harness and evidence artifacts (AC: 8, 10, 11)**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh`.
  - [x] Add gates for prompt schema, cancellation no-write behavior, generated-file shape, `.env` copy semantics, and no-scope-creep.
  - [x] Add compatibility gates replacing superseded Story 2.3/3.3 placeholder assertions.
  - [x] Add regression gate for unaffected predecessor harness set.
  - [x] Emit `PASS:` fingerprint convention and deterministic failure diagnostics.

- [x] **Task 7 - Execute validation and capture handoff (AC: 10, 11)**
  - [x] Run Story 5.2 harness `all` and capture transcript.
  - [x] Run unaffected predecessor harnesses and capture pass vector.
  - [x] Capture checksums for modified files and preserved-byte-stability anchors.
  - [x] Write `story-5-2-task-handoff.md` with AC-to-evidence map and forward notes for Story 5.3.

- [x] **Task 8 - Sync sprint status and story bookkeeping (AC: 12)**
  - [x] Update `sprint-status.yaml` `5-2-wizard-prompts-and-file-generation` lifecycle through dev completion (`ready-for-dev` during creation, `review` at dev completion).
  - [x] Keep `epic-5` as `in-progress`.
  - [x] Preserve comments/ordering and update `last_updated` only if date changes.

## Dev Notes

### Artifact availability and extracted constraints

- Core planning source: `_bmad-output/planning-artifacts/epics.md` (Epic 5 Story 5.2 AC foundation).
- Architecture guardrails: `_bmad-output/planning-artifacts/architecture.md` (work-only scope, portability, generic content).
- Sprint tracker: `_bmad-output/implementation-artifacts/sprint-status.yaml` (`epic-5` already `in-progress`, `5-2` currently backlog pre-creation).
- Story 5.1 implementation baseline:
  - `bin/init` already contains bootstrap, help/version fast paths, and CommonJS imports.
  - Root `package.json` pins `prompts: "2.4.2"` and `type: "commonjs"`.
- Target files to rewrite from wizard answers:
  - `memory/me/identity.md` (currently placeholder-driven scaffold from Story 3.3).
  - `agents/personas/work.md` (currently placeholder-driven scaffold from Story 2.3).
- `.env` source template:
  - `.env.example` contains active and placeholder MCP sections with intentionally blank/commented values.

### Previous story intelligence to carry into implementation

- Keep Node-only posture from Story 5.1; no shell scripts embedded in `bin/init`.
- Keep dependency bootstrap idempotency (`node_modules/prompts` existence short-circuit).
- Keep fast-path UX for `--help` and `--version`.
- Reuse Story 4.x scan discipline (secret/banned/path/placeholder probes) in Story 5.2 harness.
- Acknowledge that Story 5.2 intentionally supersedes placeholder-only expectations from Story 2.3 and Story 3.3 outputs.

### Web research guidance (current)

- `prompts` docs (`2.4.2`) confirm:
  - `onCancel(prompt, answers)` can return `true` to continue, otherwise aborts and returns collected responses.
  - `validate` functions should return `true` or error message.
  - `override` and `inject` exist; `inject` is intended for tests and supports cancellation simulation via `Error`.
- Node fs docs confirm:
  - `fsPromises.writeFile()` is unsafe for concurrent writes to same file without awaiting settlement.
  - Use serialized writes and avoid access-before-write race checks.
  - `fsPromises.rename(oldPath, newPath)` is the primitive for rename replacement behavior.
- `write-file-atomic` package documents temp-file+rename strategy and serialized same-file writes; use as reference pattern if native implementation is retained.

### Implementation guardrails

- Keep all new code in CommonJS (`require(...)`) to match current project contract.
- Do not alter `package.json` dependency versions unless strictly required by implementation and justified in story execution notes.
- Do not write secrets; generated files must only contain user-entered identity/persona text and blank credential templates.
- Any normalization (trim, whitespace collapse) must be deterministic and documented.
- Preserve UTF-8 + LF + trailing newline for generated markdown files.

### Project Structure Notes

- Primary code touchpoint: `bin/init`.
- Primary generated output targets:
  - `memory/me/identity.md`
  - `agents/personas/work.md`
  - `.env` (copy target only; `.env.example` must remain unchanged)
- Test/evidence artifacts expected under:
  - `_bmad-output/implementation-artifacts/tests/story-5-2-*.md`
  - `_bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh`

### Regression strategy note

- Story 5.2 changes semantic intent of Story 2.3 and 3.3 scaffolds by replacing placeholders with concrete employee data.
- Therefore Story 5.2 validation must:
  - Continue running unaffected predecessor harnesses unchanged.
  - Replace superseded placeholder assertions with Story 5.2 compatibility checks in the new harness.
  - Validate Story 5.1 compatibility through bootstrap/help/version behavior, not scaffold-banner immutability.

### References

- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/implementation-artifacts/5-1-scaffold-bin-init-node-entry-point.md`
- `_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md`
- `_bmad-output/implementation-artifacts/3-3-seed-empty-identity-and-preferences.md`
- `_bmad-output/implementation-artifacts/4-3-write-env-example.md`
- `_bmad-output/implementation-artifacts/4-4-rewrite-setup-and-mcps-docs.md`
- `_bmad-output/implementation-artifacts/tests/story-5-1-baseline-audit.md`
- `_bmad-output/implementation-artifacts/tests/story-5-1-canonical-blueprint.md`
- `_bmad-output/implementation-artifacts/tests/story-5-1-task-handoff.md`
- `https://www.npmjs.com/package/prompts`
- `https://nodejs.org/api/fs.html`
- `https://www.npmjs.com/package/write-file-atomic`

## Concerns and ambiguities

- Story 2.3/3.3 harnesses were designed for placeholder scaffolds; Story 5.2 must explicitly supersede those checks to avoid false regressions.
- Department/manager values are not directly prompted in Epic 5.2 scope; blueprint must define deterministic fallback behavior (for example: preserve manager placeholder or map department from role prompt policy).
- Existing `docs/setup.md` text still frames `./bin/init` as future-facing; decide in dev execution whether to update docs in this story or defer to a documentation follow-up.

## Senior Developer Review (AI)

- **F1 (HIGH, OUTPUT_INTEGRITY, AC4/AC5)**: YAML frontmatter interpolation did not escape quotes/backslashes from prompt input.
  - **Resolution**: added `yamlDoubleQuoted()` and routed all quoted frontmatter fields through it.
- **F2 (MEDIUM, TEST_MODE_DETERMINISM, AC10)**: fixture payload validation was underspecified and could permit non-deterministic fallback.
  - **Resolution**: added `validateFixtureResponses()` with ordered position/type checks, cancellation-aware validation, and explicit missing-index errors.
- **F3 (MEDIUM, TEST_QUALITY, AC2/AC10)**: Node test hard-coded MCP table cardinality, creating brittle false failures for legitimate catalog growth.
  - **Resolution**: rewrote test to assert structural invariants (ordered prefix, uniqueness, key inclusion) instead of exact row count.
- **F4 (LOW, RESILIENCE, AC7)**: `writeAtomic()` could leave temp artifacts on write/rename error.
  - **Resolution**: wrapped atomic write with best-effort temp cleanup in error path.
- **F5 (MEDIUM, REGRESSION_COMPAT, AC11)**: extra QA sweep flagged Story 5.1 harness incompatibility with Story 5.2 runtime text.
  - **Resolution**: updated Story 5.1 harness `task3` to accept either Story 5.1 steady-state banner set or Story 5.2 compatible text set.

## Review Follow-ups (AI)

- [x] Escaped YAML frontmatter values in identity/persona renderers.
- [x] Hardened fixture validation for deterministic non-interactive mode, including cancellation-aware sequencing.
- [x] Made MCP parser test resilient to future docs table growth.
- [x] Added temp-file cleanup on atomic write errors.
- [x] Restored Story 5.1 harness compatibility under Story 5.2 `bin/init` behavior.
- [x] Re-ran `node --test test/bin-init.story-5-2.test.js` after fixes.
- [x] Re-ran Story 5.2 harness `all` after fixes.
- [x] Re-ran Story 5.1 harness `all` after compatibility update.
- [x] Updated sprint tracker from `review` to `done` after final green verification.

## Change Log

- 2026-04-21: Story created in ready-for-dev state for Epic 5 Story 5.2. Includes prompt schema, deterministic generation guardrails, and explicit superseded-scaffold regression strategy.
- 2026-04-21: Story 5.2 implemented and validated. Added wizard prompt orchestration, deterministic render/copy pipeline, Story 5.2 harness, and handoff evidence; status moved to review.
- 2026-04-21: Review findings (F1-F5) applied; Story 5.2 and Story 5.1 harnesses re-verified green; status moved review -> done.

## Dev Agent Record

### Agent Model Used

- Story authored by Codex 5.3 in Story Creation phase.
- Story implemented by Codex 5.3 (Amelia dev execution).

### Debug Log References

- `node --test test/bin-init.story-5-2.test.js` (pass: 6, fail: 0).
- `bash _bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh all` (PASS task1..task9, PASS all).
- predecessor pass-vector sweep (`BMAD_REGRESSION_DEPTH=1`) across Stories 1.1, 1.2, 1.3, 2.1, 2.2, 2.4, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4 (all exit 0; expected PASS counts matched).
- checksum capture for modified outputs and preserved-byte-stability anchors (documented in Story 5.2 handoff artifact).
- post-review-fix re-run: `node --test test/bin-init.story-5-2.test.js` (pass: 7, fail: 0).
- post-review-fix re-run: `bash _bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh all` (PASS task1..task9, PASS all).
- post-review-fix compatibility run: `bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all` (PASS task1..task9, PASS all).

### Completion Notes List

- Implemented interactive wizard flow in `bin/init` with deterministic prompt ordering, validation, canonical MCP multiselect wiring, and explicit cancel exit semantics.
- Added deterministic output pipeline: normalization, role-to-department mapping, manager placeholder policy, pure markdown renderers, optional MCP section, LF/newline normalization.
- Added safe write/copy layer with path-guarded atomic writes (`temp + rename`) and serialized per-target writes.
- Added opt-in fixture-driven non-interactive mode (`BMAD_STORY_5_2_FIXTURE_PATH`) with strict payload validation and injected-cancellation support.
- Authored Story 5.2 validation harness and executed full gate suite plus unaffected predecessor regression sweep.
- Authored Story 5.2 handoff artifact mapping ACs to concrete evidence and Story 5.3 forward boundaries.
- Applied Phase 4 review fixes across output escaping, fixture determinism, temp-file cleanup, and regression compatibility.
- Updated sprint status for `5-2-wizard-prompts-and-file-generation` to `done` while preserving `epic-5` as `in-progress`.

### File List

- `_bmad-output/implementation-artifacts/5-2-wizard-prompts-and-file-generation.md` (new)
- `bin/init` (updated)
- `test/bin-init.story-5-2.test.js` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-2-baseline-audit.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-2-canonical-blueprint.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh` (new, executable)
- `_bmad-output/implementation-artifacts/tests/story-5-2-task-handoff.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh` (updated: Story 5.2 compatibility in banner/text checks)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated: story 5-2 status -> done)
