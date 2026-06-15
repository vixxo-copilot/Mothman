# Story 1.1: Scaffold directory structure and root files

Status: done

## Story

As a new Vixxo employee,
I want the template repo to have a clear, consistent directory layout when I clone it,
so that I can orient quickly without reading docs.

## Acceptance Criteria

1. **AC1 - Required scaffold directories exist**
   - Given a fresh clone of `assistants-template`
   - When the repository root is inspected
   - Then these directories exist at the root: `.cursor/rules/`, `agents/personas/`, `bin/`, `docs/`, `memory/`, `scripts/`
2. **AC2 - Root ignore rules cover local/runtime artifacts**
   - Given the root `.gitignore`
   - When ignore patterns are reviewed
   - Then it excludes `node_modules/`, `.env`, `.env.*`, `*.log`, and `tmp/`
3. **AC3 - Empty required directories are tracked by Git**
   - Given required scaffold directories that are intentionally empty in this phase
   - When tracked files are listed
   - Then those empty directories contain `.gitkeep` so they persist across clones

## Tasks / Subtasks

- [x] Task 1 - Baseline repo scaffold and identify directory gaps (AC: 1, 3)
  - [x] Inspect root paths and mark which required directories already exist versus missing.
  - [x] Identify which required directories will remain intentionally empty after this story and need `.gitkeep`.
- [x] Task 2 - Create missing root scaffold directories (AC: 1)
  - [x] Create `.cursor/rules/` without disturbing existing `.cursor/skills/`.
  - [x] Create `agents/personas/`, `bin/`, `memory/`, and `scripts/` at repository root.
  - [x] Preserve existing `docs/` if already present.
- [x] Task 3 - Add `.gitkeep` placeholders for empty required directories (AC: 3)
  - [x] Add `.gitkeep` in each required empty directory so Git tracks it.
  - [x] Skip `.gitkeep` only in directories that already contain intentional tracked files.
- [x] Task 4 - Create or update root `.gitignore` with required patterns (AC: 2)
  - [x] Ensure exact entries exist: `node_modules/`, `.env`, `.env.*`, `*.log`, `tmp/`.
  - [x] Keep any additional pre-existing ignore entries unless they conflict with project requirements.
- [x] Task 5 - Validate ACs with command-line checks (AC: 1, 2, 3)
  - [x] Verify required directories exist at root.
  - [x] Verify `.gitignore` behavior with `git check-ignore -v` against representative files.
  - [x] Verify `.gitkeep` files are present in intentionally empty required directories.
- [x] Task 6 - Regression and scope guard checks before handoff (AC: 1, 2, 3)
  - [x] Confirm this story only scaffolds structure and root ignore behavior (no persona/rule content yet).
  - [x] Confirm no personal-context terms are introduced while adding scaffolding files.
- [x] Review Follow-ups (AI)
  - [x] F1 (HIGH): Added `!.env.example` allowlist entry to avoid blocking committed template env example files.
  - [x] F2 (MEDIUM): Added automatic cleanup for validation probe artifacts in `check_task5`.
  - [x] F3 (MEDIUM): Replaced brittle markdown-string assertions in `check_task1` with structural scaffold checks.
  - [x] F4 (LOW): Made `.gitkeep` validation conditional on directory emptiness/intentional non-`.gitkeep` content.

## Dev Notes

- **Story scope boundary:** Epic 1 explicitly defines this as structural bootstrap only ("empty structural bones"; no skills/content logic), so implementation should avoid adding non-essential file content beyond scaffolding.
- **Functional traceability:** This story implements `FR1` directly and lays the base paths used by follow-on stories in Epic 1 (`README/LICENSE/.gitignore` and top-level context files).
- **Non-functional constraints relevant now:**
  - Keep repository portable for macOS/Linux onboarding (`NFR2`).
  - Keep secrets out of source control (`NFR4`) via required `.gitignore` entries.
  - Keep template thin and neutral (`NFR5`, `NFR1`) by avoiding any personal or legacy context in new scaffold files.
- **Architecture/PRD/UX artifact availability:** `architecture.md`, `prd.md`, and `ux-design-specification.md` were not present under `_bmad-output/planning-artifacts`; implementation guidance is therefore derived from `epics.md`, `config.yaml`, sprint status, and current repo state.
- **Tech/version guardrails from current research:**
  - Node.js `v24` is current LTS as of April 2026, with March 2026 security updates published for 20/22/24/25 lines; use actively patched Node releases for any local validation scripts that may be introduced in later stories.
  - `.gitignore` behavior is pattern-order and scope sensitive; tracked files are not retroactively ignored without `git rm --cached`, so do not accidentally commit `.env` before ignore rules are in place.
  - `.gitkeep` remains a convention (not a Git builtin); use it consistently for intentionally empty scaffold directories in this phase.

### Project Structure Notes

- Required root scaffold target for this story:
  - `.cursor/rules/`
  - `agents/personas/`
  - `bin/`
  - `docs/`
  - `memory/`
  - `scripts/`
- Existing observed state before implementation:
  - `.cursor/skills/` exists already and must remain intact.
  - `docs/` exists and should be preserved.
  - `agents/`, `bin/`, `memory/`, and `scripts/` were not present and should be added.
- Directory ownership assumptions for next stories:
  - `agents/personas/` feeds Epic 2 persona/rules work.
  - `bin/` is reserved for setup wizard work in Epic 5.
  - `memory/` is reserved for Epic 3 scaffold content.
  - `scripts/` is reserved for automation/guardrail scripts in later epics.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 1, Story 1.1 ACs, FR/NFR inventory, tier order)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story key, current status model, epic/story tracking semantics)
- `_bmad/bmm/config.yaml` (BMAD module config; artifact path conventions; v6.3.0 generation metadata)
- Git history (`git log`, latest commits) showing planning artifacts and BMAD bundle were recently added and scaffold reset history includes `.cursor/rules/bmad/index.mdc`
- [Node.js Releases](https://nodejs.org/en/about/previous-releases) (current LTS line and support status)
- [Node.js March 2026 Security Releases](https://nodejs.org/en/blog/vulnerability/march-2026-security-releases) (recent security fixes across active release lines)
- [Git `gitignore` Documentation](https://git-scm.com/docs/gitignore) (authoritative ignore pattern semantics)
- [How to add an empty directory to Git](https://stackoverflow.com/questions/115983/how-do-i-add-an-empty-directory-to-a-git-repository) (`.gitkeep` convention background)

## Senior Developer Review (AI)

### REVIEW_SUMMARY

- story: `1-1-scaffold-directory-structure-and-root-files`
- total_issues: `4`
- critical: `0`
- high: `1`
- medium: `2`
- low: `1`
- recommendation: `CHANGES_REQUESTED` (resolved)

### FINDINGS (Resolved)

- `F1` `HIGH` `AC_MISSING` in `.gitignore`: `.env.*` unintentionally ignored `.env.example`; fixed by adding `!.env.example`.
- `F2` `MEDIUM` `TEST_QUALITY` in `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh`: probe artifacts were left behind; fixed with trap-based cleanup.
- `F3` `MEDIUM` `TEST_QUALITY` in `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh`: brittle string checks in `check_task1`; replaced with structural checks.
- `F4` `LOW` `TEST_QUALITY` in `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh`: unconditional `.gitkeep` expectation; now conditional when intentional non-`.gitkeep` content exists.

### Test Runner Summary

- framework: custom Bash validation + `pytest`
- result: `PASS`
- full story validation: `bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all` => `PASS: all`

## Change Log

- 2026-04-20: Story created and moved to `ready-for-dev`.
- 2026-04-20: Implemented scaffold directories, `.gitkeep` placeholders, root `.gitignore`, and validation script.
- 2026-04-20: Applied review/test follow-up fixes (`F1`-`F4`), re-ran validations, and marked story `done`.

## Dev Agent Record

### Agent Model Used

Codex 5.3

### Debug Log References

- Story creation and artifact analysis performed in autonomous Phase 1 run.
- RED/GREEN validation executed with `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` in task modes `task1` through `task6`.
- Full regression validation executed with `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all`.

### Completion Notes List

- Story drafted from Epic 1 Story 1.1 source requirements and marked `ready-for-dev`.
- No previous story intelligence applicable (`STORY_NUM=1`).
- Planning-artifact gaps detected for `architecture.md`, `prd.md`, and `ux-design-specification.md`; mitigated by explicit constraints extracted from available artifacts plus current external technical guidance.
- Task 1 Baseline Audit
- Missing required directories before implementation: agents/personas, bin, memory, scripts, .cursor/rules
- Existing required directories before implementation: docs
- Required directories intentionally empty in this story: .cursor/rules, agents/personas, bin, docs, memory, scripts
- Task 2 Scaffold Creation
- Created required root directories: .cursor/rules, agents/personas, bin, memory, scripts
- Preserved pre-existing directories: .cursor/skills, docs
- Task 3 Empty Directory Tracking
- Added `.gitkeep` in required empty directories: .cursor/rules, agents/personas, bin, docs, memory, scripts
- No `.gitkeep` exceptions were needed because all required scaffold directories were empty
- Task 4 Root Ignore Rules
- Created root `.gitignore` with required entries: node_modules/, .env, .env.*, *.log, tmp/
- No pre-existing `.gitignore` entries required preservation or conflict resolution
- Task 5 AC Validation
- Validation script checks passed for required directories, `.gitkeep` placement, and root `.gitignore` entries
- `git check-ignore -v` representative checks passed for `tmp/story-1-1-ignore-check`, `story-1-1.log`, and `.env.test`
- Task 6 Scope Guard + Regression
- Confirmed scaffold-only changes in required root paths with no persona/rule content additions
- Confirmed no personal-context terms in newly added scaffold files
- Full story regression suite passed (`PASS: all`)
- Phase 4 Review Resolutions
- Applied F1 by adding `!.env.example` to `.gitignore`
- Applied F2 by adding automated probe artifact cleanup in validation script
- Applied F3 by replacing brittle markdown text assertions with structural checks in `check_task1`
- Applied F4 by making `.gitkeep` checks conditional on intentional directory content
- Re-ran full validation suite after fixes (`PASS: all`)

### File List

- `.gitignore` (root ignore patterns required by AC2)
- `.cursor/rules/.gitkeep` (track empty required scaffold directory)
- `agents/personas/.gitkeep` (track empty required scaffold directory)
- `bin/.gitkeep` (track empty required scaffold directory)
- `docs/.gitkeep` (track empty required scaffold directory)
- `memory/.gitkeep` (track empty required scaffold directory)
- `scripts/.gitkeep` (track empty required scaffold directory)
- `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` (task validation and regression checks)
- `_bmad-output/implementation-artifacts/1-1-scaffold-directory-structure-and-root-files.md` (task status, notes, and implementation record)
