# Story 5.3: Wizard runs skills install and verifies active MCPs

Status: done

## Story

As a Vixxo employee running `./bin/init` after completing the Story 5.2 prompt flow,
I want the wizard to install the shared skills bundle and run deterministic checks for every active MCP,
so that I can confirm my workstation is genuinely usable before leaving setup.

## Acceptance Criteria

1. **AC1 - `bin/init` executes a post-wizard setup phase in a strict order**
   - Given the user runs `./bin/init` with no flags and completes the Story 5.2 prompts successfully
   - When post-wizard setup starts
   - Then `bin/init` runs: (1) skills install, (2) active MCP verification, (3) consolidated summary
   - And the ordering is deterministic and logged with stable headings
   - And `--help|-h` and `--version|-v` remain fast paths that bypass prompts, skills install, and MCP checks

2. **AC2 - Skills install command is invoked exactly once with deterministic error handling**
   - Given post-wizard setup phase is entered
   - When skills install runs
   - Then the script invokes `npx skills add vixxo-copilot/agent-skills` exactly once via Node child-process execution
   - And stdout/stderr are surfaced to the terminal so users can see real command output
   - And non-zero exit, spawn error (`ENOENT`), or signal interruption are handled explicitly with non-zero result state
   - And failure output always includes a concrete rerun command: `npx skills add vixxo-copilot/agent-skills`

3. **AC3 - Active MCP set is loaded from `.cursor/mcp.json` and verified without placeholder leakage**
   - Given `.cursor/mcp.json` currently defines active MCP servers
   - When verification planning runs
   - Then the active server keys are read from `.cursor/mcp.json` `mcpServers` in JSON key order
   - And verification scope includes only active keys from `.cursor/mcp.json`
   - And placeholder-only servers documented in `.cursor/mcp.placeholders.md` are not probed
   - And malformed JSON or missing `mcpServers` is treated as verification failure with actionable guidance to check `.cursor/mcp.json`

4. **AC4 - Each active MCP receives a deterministic probe and emits PASS/FAIL**
   - Given active server keys are resolved
   - When verification executes
   - Then each active MCP gets one probe function call with a bounded timeout and explicit result object
   - And each result includes: `server_key`, `status` (`PASS` or `FAIL`), `reason`, and remediation text
   - And current active servers are covered: `linear`, `github`, `microsoft-365`, `salesforce`, `gong`
   - And probe implementation does not print secret values

5. **AC5 - FAIL output includes exact fix command or authoritative wiki/upstream link**
   - Given a skills-install or MCP verification failure occurs
   - When failure output is printed
   - Then the output contains a server-specific remediation item with either a concrete command or canonical link
   - And remediations are concrete for known active servers:
     - `linear`: re-auth via MCP UI + `https://linear.app/docs/mcp`
     - `github`: export `GITHUB_PERSONAL_ACCESS_TOKEN`, ensure Docker is running, and reference GitHub MCP install guide
     - `microsoft-365`: rerun device-code auth and reference `@softeria/ms-365-mcp-server`
     - `salesforce`: `sf org login web` and confirm `@salesforce/cli`
     - `gong`: export `GONG_ACCESS_KEY` and `GONG_ACCESS_KEY_SECRET`, reference `github:kenazk/gong-mcp`
   - And unknown future active keys fall back to `docs/mcps.md` and `.cursor/mcp.README.md`

6. **AC6 - Final summary is explicit and exit code reflects overall health**
   - Given post-wizard actions complete
   - When summary is printed
   - Then summary includes:
     - skills install status
     - MCP PASS count and FAIL count
     - bullet list of failing MCP keys with remediation hints
   - And process exits `0` only when skills install passes and all MCP checks pass
   - And process exits non-zero when any required check fails

7. **AC7 - Story 5.2 deterministic write behavior remains intact**
   - Given Story 5.2 write pipeline (`writeAtomic`, path guards, prompt validation) is already implemented
   - When Story 5.3 changes are introduced
   - Then identity/persona/.env generation behavior remains functionally unchanged
   - And cancellation semantics from Story 5.2 remain unchanged (`setup cancelled`, no writes)
   - And no regression is introduced in Story 5.2 unit tests and harness checks that are still applicable

8. **AC8 - Deterministic non-interactive verification mode exists for tests**
   - Given MCP checks and skills install can be flaky or interactive on real workstations
   - When automated tests run
   - Then an opt-in fixture mode allows deterministic simulation of:
     - skills install success/failure
     - per-MCP PASS/FAIL outcomes
   - And fixture mode is disabled by default for real users
   - And invalid fixture payloads fail fast with clear errors

9. **AC9 - Existing harness compatibility is explicitly managed**
   - Given Story 5.2 harness currently enforces "no Story 5.3 behavior" checks
   - When Story 5.3 lands
   - Then Story 5.2 harness is updated so superseded checks are replaced by compatibility assertions instead of hard failures
   - And Story 5.3 harness becomes the source of truth for skills-install and MCP-verification behavior
   - And Story 5.1 fast-path behavior (`--help`, `--version`, dependency bootstrap) remains validated

10. **AC10 - Story 5.3 validation harness exists and is executable**
    - Given `_bmad-output/implementation-artifacts/tests`
    - When Story 5.3 implementation lands
    - Then a new executable harness exists at `_bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh`
    - And harness implements deterministic gates for command wiring, summary semantics, fixture mode, and regression compatibility
    - And harness supports `task1..taskN` plus `all` dispatcher with `PASS:` output convention

11. **AC11 - Evidence artifacts are produced for reproducible review**
    - Given Story 5.3 implementation is complete
    - When validation is run
    - Then evidence artifacts exist:
      - `_bmad-output/implementation-artifacts/tests/story-5-3-baseline-audit.md`
      - `_bmad-output/implementation-artifacts/tests/story-5-3-canonical-blueprint.md`
      - `_bmad-output/implementation-artifacts/tests/story-5-3-task-handoff.md`
    - And handoff maps each AC to objective evidence (commands, harness gates, checksums)

12. **AC12 - Sprint tracker is synchronized for Story 5.3 creation**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When this story file is created
    - Then `5-3-wizard-runs-skills-install-and-verifies.status` is updated `backlog -> ready-for-dev`
    - And `epic-5.status` remains `in-progress`
    - And existing comments/order/formatting are preserved

## Tasks / Subtasks

- [x] **Task 1 - Baseline audit and Story 5.3 blueprint package (AC: 3, 4, 5, 8, 11)** **[Parallelizable with Task 2]**
  - [x] Read and fingerprint current `bin/init`, `test/bin-init.story-5-2.test.js`, `.cursor/mcp.json`, `.cursor/mcp.README.md`, `docs/mcps.md`, and `docs/setup.md`.
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-5-3-baseline-audit.md` with active MCP matrix, probe strategy, and remediation catalog.
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-5-3-canonical-blueprint.md` with locked function signatures, post-wizard call order, and summary format.
  - [x] Document deterministic fixture payload schema for Story 5.3 verification mode.
  - [x] Record superseded assertions from Story 5.2 harness and planned compatibility replacement.

- [x] **Task 2 - Add post-wizard orchestration in `bin/init` (AC: 1, 2, 6, 7)** **[Parallelizable with Task 1 design phase only]**
  - [x] Add a dedicated post-wizard coordinator function invoked after successful Story 5.2 file writes.
  - [x] Keep `--help|-h` and `--version|-v` behavior unchanged and no-op for post-wizard setup.
  - [x] Keep existing cancellation and file-write semantics untouched.
  - [x] Ensure deterministic heading order: skills install -> MCP verification -> summary.
  - [x] Ensure non-zero final return code when any required post-wizard check fails.

- [x] **Task 3 - Implement `npx skills add` execution helper (AC: 2, 5, 6)**
  - [x] Add helper to run `npx skills add vixxo-copilot/agent-skills` with inherited stdio.
  - [x] Handle spawn error, signal, and non-zero status with explicit structured result.
  - [x] Emit stable failure text containing exact remediation command.
  - [x] Keep logs free of secret values and unrelated environment dump.
  - [x] Add unit tests for success path and each failure class.

- [x] **Task 4 - Implement active MCP verification engine (AC: 3, 4, 5, 6)**
  - [x] Parse active server keys from `.cursor/mcp.json` `mcpServers`.
  - [x] Add per-server probe adapters for current active keys (`linear`, `github`, `microsoft-365`, `salesforce`, `gong`) with bounded timeout.
  - [x] Add remediation map with exact command/link per active key and fallback for unknown keys.
  - [x] Produce deterministic result objects and formatted PASS/FAIL lines.
  - [x] Aggregate PASS/FAIL counts and failing-key list for final summary.

- [x] **Task 5 - Add deterministic Story 5.3 fixture mode and test surfaces (AC: 8)**
  - [x] Introduce Story 5.3 fixture env flag (for example `BMAD_STORY_5_3_FIXTURE_PATH`) independent from Story 5.2 fixture behavior.
  - [x] Validate fixture payload schema before execution; fail fast on malformed payloads.
  - [x] Allow fixture-driven simulation of skills-install and per-MCP probe results.
  - [x] Add focused Node tests under `test/bin-init.story-5-3.test.js` for parser, orchestration, and summary logic.
  - [x] Keep real-user default path unchanged when fixture env flag is absent.

- [x] **Task 6 - Update and align validation harnesses (AC: 9, 10)**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh` with deterministic `task1..taskN` gates.
  - [x] Include gates for command wiring, MCP result formatting, fixture mode determinism, and non-zero on failure.
  - [x] Update Story 5.2 harness to replace superseded "no 5.3 logic" checks with compatibility checks aligned to Story 5.3.
  - [x] Keep Story 5.1 harness compatibility expectations for fast paths and bootstrap.
  - [x] Preserve PASS-count fingerprint discipline and deterministic stderr diagnostics.

- [x] **Task 7 - Execute full validation and capture handoff evidence (AC: 10, 11)**
  - [x] Run Story 5.3 Node tests (`node --test test/bin-init.story-5-3.test.js`) and capture transcript.
  - [x] Run Story 5.3 harness `all` and capture transcript.
  - [x] Re-run Story 5.2 and Story 5.1 harnesses after compatibility updates.
  - [x] Run unaffected predecessor harness sweep (Stories 1.x/2.x/3.x/4.x as applicable) with regression-depth guard.
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-5-3-task-handoff.md` with AC-to-evidence map, checksums, and explicit fail-remediation examples.

- [x] **Task 8 - Sprint status and story bookkeeping (AC: 12)** **[Independent, usually last]**
  - [x] Update `sprint-status.yaml` lifecycle values for Story 5.3 (`ready-for-dev` at creation, then dev-phase transitions later).
  - [x] Keep `epic-5` in `in-progress` until Story 5.3 implementation and review are complete.
  - [x] Preserve file comments/order/spacing and update `last_updated` if date changes.

## Dev Notes

### Current implementation baseline to extend

- `bin/init` already includes Story 5.2 prompt flow, deterministic renderers, atomic writes, and fixture mode via `BMAD_STORY_5_2_FIXTURE_PATH`.
- `main()` currently runs: fast-path flags -> `ensureDependencies()` -> `runWizard()`.
- Story 5.3 should add post-wizard logic after successful `runWizard()` completion without breaking prior flows.
- Existing exports in `bin/init` are unit-test friendly; Story 5.3 should continue exporting pure helpers for new logic.

### Active MCP verification matrix (Story 5.3 target)

| Server key | Verification intent | Primary remediation |
| --- | --- | --- |
| `linear` | Verify reachable/usable MCP entry path and auth readiness | Reconnect via MCP UI and review [Linear MCP docs](https://linear.app/docs/mcp) |
| `github` | Verify Docker-backed GitHub MCP prerequisites and token wiring | Export `GITHUB_PERSONAL_ACCESS_TOKEN`; ensure Docker is running; review [GitHub MCP install guide](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md) |
| `microsoft-365` | Verify package/auth readiness for device-code flow | Re-run device-code auth flow; see [ms-365-mcp-server](https://github.com/softeria/ms-365-mcp-server) |
| `salesforce` | Verify CLI-session-backed MCP readiness | Run `sf org login web`; ensure `@salesforce/cli` is installed |
| `gong` | Verify env-backed MCP prerequisites | Export `GONG_ACCESS_KEY` and `GONG_ACCESS_KEY_SECRET`; see [gong-mcp](https://github.com/kenazk/gong-mcp) |

Implementation note: probe functions can be transport/prerequisite checks rather than destructive operations; each must be deterministic, timeout-bounded, and produce actionable remediation on failure.

### Scope boundaries (explicit)

**In scope**
- Extend `bin/init` to run skills install and active MCP verification after successful Story 5.2 wizard completion.
- Add Story 5.3 tests, harness, baseline audit, canonical blueprint, and handoff evidence.
- Update Story 5.2 harness for superseded assertions now that Story 5.3 behavior is expected.

**Out of scope**
- Editing `.cursor/mcp.json` active/placeholder definitions.
- Verifying placeholder MCPs from `.cursor/mcp.placeholders.md`.
- Adding new MCP servers or changing MCP transport/auth architecture.
- Changing Story 5.2 prompt schema or generated file contracts unless required for non-breaking integration.
- Introducing CI workflow changes from Epic 6.

### Verification strategy and expected command set

- Story 5.3 unit tests:
  - `node --test test/bin-init.story-5-3.test.js`
- Story 5.3 harness:
  - `bash _bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh all`
- Compatibility reruns:
  - `bash _bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all`
- Regression sweep for unaffected predecessor harnesses:
  - execute with `BMAD_REGRESSION_DEPTH=1` guard to avoid nested recursion.

### Risks and concerns to manage during implementation

- Real MCP probes can be interactive or network-sensitive; fixture mode is required for deterministic automation.
- Story 5.2 harness currently contains anti-5.3 assertions and must be revised in the same change set to avoid false failures.
- `docs/setup.md` still contains forward-reference wording for `./bin/init`; Story 5.3 implementation should verify whether wording cleanup is needed and keep scope disciplined if edited.
- Failure messages must avoid leaking secrets while still giving exact remediation commands.

## Project Structure Notes

- Primary code file to modify: `bin/init`
- New/updated test files:
  - `test/bin-init.story-5-3.test.js` (new)
  - `test/bin-init.story-5-2.test.js` (update only if shared helpers change)
- New validation/evidence files:
  - `_bmad-output/implementation-artifacts/tests/story-5-3-baseline-audit.md`
  - `_bmad-output/implementation-artifacts/tests/story-5-3-canonical-blueprint.md`
  - `_bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh`
  - `_bmad-output/implementation-artifacts/tests/story-5-3-task-handoff.md`
- Existing files likely touched for compatibility:
  - `_bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh`
  - `_bmad-output/implementation-artifacts/sprint-status.yaml`

## References

- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/implementation-artifacts/5-1-scaffold-bin-init-node-entry-point.md`
- `_bmad-output/implementation-artifacts/5-2-wizard-prompts-and-file-generation.md`
- `_bmad-output/implementation-artifacts/tests/story-5-2-task-handoff.md`
- `bin/init`
- `.cursor/mcp.json`
- `.cursor/mcp.README.md`
- `.cursor/mcp.placeholders.md`
- `docs/mcps.md`
- `docs/setup.md`

## Senior Developer Review (AI)

- **F1 (CRITICAL, TASK_INCOMPLETE, AC11)**: required handoff artifact was missing.
  - **Resolution**: added `_bmad-output/implementation-artifacts/tests/story-5-3-task-handoff.md` with AC evidence map, transcripts, and checksums.
- **F2 (HIGH, AC_MISSING, AC3/AC4)**: known MCP probes could return PASS when active server config entries were null/invalid.
  - **Resolution**: added `validateServerConfigObject()` and enforced config-object checks in `probeGithub`, `probeMicrosoft365`, `probeSalesforce`, and `probeGong`.
- **F3 (MEDIUM, CODE_QUALITY, AC4/AC6)**: unknown probe statuses were normalized to PASS.
  - **Resolution**: changed `normalizeProbeStatus()` to only pass explicit `PASS`; all other states normalize to `FAIL`.
- **F4 (MEDIUM, TEST_QUALITY, AC2)**: `runSkillsInstall` signal/non-zero failure classes lacked direct unit tests.
  - **Resolution**: added unit coverage for signal (`SIGTERM`) and non-zero (`status 3`) branches in `test/bin-init.story-5-3.test.js`.

## Review Follow-ups (AI)

- [x] Added Story 5.3 handoff evidence artifact.
- [x] Hardened known MCP probes against malformed active config entries.
- [x] Removed implicit PASS fallback for unknown probe statuses.
- [x] Added unit tests for `runSkillsInstall()` signal and non-zero exit classes.
- [x] Re-ran `node --test test/bin-init.story-5-3.test.js` (10/10 pass).
- [x] Re-ran Story 5.3 harness `all` (`PASS: task1..task9`, `PASS: all`).
- [x] Re-ran compatibility harnesses for Story 5.2 and Story 5.1 (`PASS: all` each).
- [x] Updated sprint tracker state to close Story 5.3 and Epic 5.

## Change Log

- 2026-04-21: Story created in `ready-for-dev` state with BDD acceptance criteria, implementation task graph, verification strategy, and explicit scope boundaries for Epic 5 Story 5.3.
- 2026-04-22: Story 5.3 implemented with post-wizard skills install, active MCP verification engine, deterministic fixture mode, Story 5.3 harness, and Story 5.2/5.1 compatibility updates.
- 2026-04-22: Phase 4 review fixes (F1-F4) applied and fully re-validated; story moved to `done`, Epic 5 moved to `done`.

## Dev Agent Record

### Agent Model Used

- Codex 5.3 (Story Creation phase).
- Codex 5.3 (Story Dev + Review/Fix + Validation phases).

### Debug Log References

- Artifact review completed for `epics.md`, `architecture.md`, `sprint-status.yaml`, Story 5.1/5.2 story files, Story 5.2 evidence artifacts, `bin/init`, tests, and MCP documentation surfaces.
- `node --test test/bin-init.story-5-3.test.js` (pass: 10, fail: 0).
- `bash _bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh all` (`PASS: task1..task9`, `PASS: all`).
- `bash _bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh all` (`PASS: all`).
- `bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all` (`PASS: all`).

### Completion Notes List

- Added Story 5.3 post-wizard coordinator flow in `bin/init`: skills install -> active MCP verification -> summary -> exit code.
- Added deterministic active MCP verification parsing from `.cursor/mcp.json` in key order with per-server remediation mapping.
- Added Story 5.3 fixture mode (`BMAD_STORY_5_3_FIXTURE_PATH`) with strict payload validation.
- Added Story 5.3 unit tests covering parser, install failure classes, fixture loading, summary semantics, and malformed-config behavior.
- Added Story 5.3 validation harness and Story 5.3 handoff artifact.
- Updated Story 5.2 and Story 5.1 harnesses for Story 5.3-compatible regression coverage.
- Applied review fixes for AC completeness, malformed active-config handling, status normalization hardening, and failure-class test depth.

### File List

- `_bmad-output/implementation-artifacts/5-3-wizard-runs-skills-install-and-verifies.md` (new)
- `bin/init` (updated: Story 5.3 orchestration + probe hardening + status normalization fix)
- `test/bin-init.story-5-3.test.js` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-3-baseline-audit.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-3-canonical-blueprint.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh` (new, executable)
- `_bmad-output/implementation-artifacts/tests/story-5-3-task-handoff.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh` (updated for Story 5.3 compatibility)
- `_bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh` (updated for Story 5.2/5.3 compatibility)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated: Story 5.3 -> done, Epic 5 -> done)
