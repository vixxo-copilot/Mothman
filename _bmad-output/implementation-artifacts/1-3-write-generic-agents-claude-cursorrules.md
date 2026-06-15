# Story 1.3: Write generic AGENTS.md, CLAUDE.md, .cursorrules

Status: done

## Story

As the AI agent in a cloned template,  
I want top-level context files that identify me as a Vixxo employee assistant,  
so that I respond with the right tone and guardrails out of the box.

## Acceptance Criteria

1. **AC1 - `CLAUDE.md` and `AGENTS.md` mirror each other**
   - Given the repository root in `assistants-template`
   - When `AGENTS.md` and `CLAUDE.md` are reviewed
   - Then both files contain the same instruction content and section structure
2. **AC2 - `.cursorrules` summarizes critical guardrails**
   - Given the repository root `.cursorrules`
   - When the file is opened
   - Then it includes concise guardrails for outbound messaging and memory protection
3. **AC3 - Placeholder-driven identity language**
   - Given all three root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`)
   - When identity/persona language is inspected
   - Then each file uses `{{employee_name}}` and `{{employee_role}}` placeholders
4. **AC4 - Work-only wording and scrubbed content**
   - Given all three files
   - When content is scanned for disallowed legacy/personal context
   - Then there are no "personal" or "RevivaGo" mentions and no Derek/gtd-life carryover

## Tasks / Subtasks

- [x] Task 1 - Baseline audit and scope guard setup (AC: 1, 2, 4)
  - [x] Confirm whether root `AGENTS.md`, `CLAUDE.md`, and `.cursorrules` already exist and capture baseline state.
  - [x] Verify Story 1.3 scope is limited to root context files and does not pre-implement Epic 2 rule files in `.cursor/rules/`.
  - [x] Establish banned-term scan list for this story (`personal`, `RevivaGo`, `Derek`, `gtd-life`).

- [x] Task 2 - Define canonical shared instruction blueprint for mirrored root files (AC: 1, 3, 4)
  - [x] Design a single section layout to be reused in both `AGENTS.md` and `CLAUDE.md` (identity, scope, tone, operating constraints, handoff expectations).
  - [x] Include `{{employee_name}}` and `{{employee_role}}` placeholders in identity and role-sensitive instructions.
  - [x] Ensure language is work-only and neutral to satisfy scrub requirements.

- [x] Task 3 - Author `AGENTS.md` from the canonical blueprint (AC: 1, 3, 4) **[Parallelizable]**
  - [x] Create root `AGENTS.md` with concise, tool-agnostic assistant instructions.
  - [x] Include explicit work-context boundaries, communication expectations, and do/don't guardrails.
  - [x] Keep content compact and structured for fast agent parsing.

- [x] Task 4 - Author `CLAUDE.md` as a mirrored counterpart (AC: 1, 3, 4) **[Parallelizable]**
  - [x] Create root `CLAUDE.md` with content matching `AGENTS.md` section-for-section.
  - [x] Ensure placeholders and work-only language are preserved exactly.
  - [x] Avoid introducing CLAUDE-only divergence that would violate mirroring requirements.

- [x] Task 5 - Author root `.cursorrules` guardrail summary (AC: 2, 3, 4) **[Parallelizable]**
  - [x] Add concise outbound-messaging guardrail guidance (no autonomous external messaging without explicit user direction).
  - [x] Add concise memory-protection guardrail guidance (no unsafe disclosure/modification of sensitive memory content).
  - [x] Include `{{employee_name}}` and `{{employee_role}}` placeholders where identity context is referenced.
  - [x] Keep this file high-level; reserve detailed operational rule files for Epic 2 stories.

- [x] Task 6 - Deterministic validation checks for AC compliance (AC: 1, 2, 3, 4)
  - [x] Validate `AGENTS.md` and `CLAUDE.md` mirroring with structural and content comparison.
  - [x] Validate placeholder presence in all three files.
  - [x] Validate `.cursorrules` contains both required guardrail topics (outbound messaging, memory protection).
  - [x] Run banned-term scan to confirm scrubbed, work-only content.

- [x] Task 7 - Regression and handoff readiness package (AC: 1, 2, 3, 4)
  - [x] Confirm no regressions in existing scaffold paths from Stories 1.1 and 1.2.
  - [x] Capture validation evidence artifact(s) under `_bmad-output/implementation-artifacts/tests/` for reproducible review.
  - [x] Prepare concise AC-to-file mapping for implementation handoff and PR summary generation.

- [x] Review Follow-ups (AI)
  - [x] F1: Story lifecycle moved to `review` until review fixes and validation are complete.
  - [x] F2: Added `_bmad-output/planning-artifacts/architecture.md` to satisfy architecture-reference dependency.
  - [x] F3: Added `_bmad/bmm/workflows/4-implementation/bmad-code-review/workflow.md` to satisfy review-checklist path dependency.
  - [x] F4: Replaced roadmap-specific wording in `.cursorrules` with timeless guidance.
  - [x] F5: Upgraded Task 7 handoff evidence with explicit commands and result snippets.

## Dev Notes

- **Artifact availability and fallback handling**
  - Available planning/tracking artifacts: `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml`, `_bmad/bmm/config.yaml`, and prior story files `1-1-...` and `1-2-...`.
  - Missing at expected locations: `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/prd.md`, `_bmad-output/planning-artifacts/ux-design-specification.md`.
  - Implementation guidance in this story is therefore anchored to Epic 1 requirements, sprint tracker semantics, prior-story learnings, and current platform docs.

- **Story-level architecture and boundary constraints**
  - Epic 1 remains bootstrap-focused (`FR1`): create root context artifacts only, without pre-implementing full `.cursor/rules/*.mdc` portfolios from Epic 2.
  - `.cursorrules` in this story is a concise compatibility summary file; deeper guardrails and file-scoped rule packs belong to Epic 2 (`2.1` and `2.2`).
  - Root files in scope for this story: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`.

- **Current platform guidance (web research)**
  - Cursor documents `AGENTS.md` as a simple project instruction mechanism and `.cursor/rules` as the structured, metadata-capable rules system; use concise, actionable rule text and avoid overlong instruction files.
  - Claude Code reads `CLAUDE.md` for persistent project instructions; guidance emphasizes concise, specific instructions and clear sectioning for reliability.
  - Because AC1 explicitly requires `AGENTS.md` and `CLAUDE.md` to mirror each other, maintain equivalent instruction content in both files even though tool-specific alternatives (like imports) exist.

- **Previous story intelligence to carry forward**
  - Story 1.1 and Story 1.2 enforce strict scrub requirements: no Derek/RevivaGo/blog/gtd-life context in committed template content.
  - Story 1.2 introduced disciplined content validation and status lifecycle consistency; continue structural validation over brittle prose-only checks.
  - Keep artifact changes tight to story scope and preserve existing bootstrap structure.

### Project Structure Notes

- Target file locations for this story:
  - `AGENTS.md` (root)
  - `CLAUDE.md` (root)
  - `.cursorrules` (root)
- Adjacent paths that should remain intact:
  - `.cursor/rules/.gitkeep` (from Story 1.1 scaffold)
  - `README.md`, `LICENSE`, `.gitignore` (from Story 1.2 root-files completion)
- Forward-compatibility note:
  - Epic 2 stories are expected to add curated `.cursor/rules/*.mdc` files; Story 1.3 should not block that future layout.

### Testing Notes

- Suggested implementation-time checks:
  - `diff -u AGENTS.md CLAUDE.md` (or equivalent) to verify mirrored content
  - `rg -n "\\{\\{employee_(name|role)\\}\\}" AGENTS.md CLAUDE.md .cursorrules` for placeholder coverage
  - `rg -n -i "personal|revivago|derek|gtd-life" AGENTS.md CLAUDE.md .cursorrules` for scrub compliance
  - `rg -n -i "outbound|message|memory" .cursorrules` for guardrail topic presence
- If automated checks are added, place them in `_bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh`.

### References

- `_bmad/bmm/config.yaml` (BMAD module metadata, artifact path variables, version context)
- `_bmad-output/planning-artifacts/epics.md` (Epic 1 Story 1.3 statement and acceptance criteria; FR/NFR inventory)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story key, lifecycle states, tracker semantics)
- `_bmad-output/implementation-artifacts/1-1-scaffold-directory-structure-and-root-files.md` (bootstrap constraints and prior implementation learnings)
- `_bmad-output/implementation-artifacts/1-2-write-generic-readme-license-gitignore.md` (root-file quality patterns and anti-PII discipline)
- Git history (`git log --oneline --decorate -n 20`) for recent commit style and Epic 1 sequencing
- [Cursor Rules Documentation](https://cursor.com/docs/rules) (AGENTS.md behavior, project rules guidance)
- [Claude Code Memory/CLAUDE.md Documentation](https://code.claude.com/docs/en/memory) (CLAUDE.md usage and instruction quality guidance)
- [AGENTS.md Specification](https://agents.md/) (cross-agent AGENTS.md format intent)
- [Node.js Releases](https://nodejs.org/en/about/previous-releases) (current supported Node lines for any optional validation tooling)

## Senior Developer Review (AI)

### REVIEW_SUMMARY

- story: `1-3-write-generic-agents-claude-cursorrules`
- total_issues: `5`
- critical: `1`
- high: `2`
- medium: `2`
- low: `0`
- recommendation: `CHANGES_REQUESTED` (resolved)

### FINDINGS (Resolved)

- `F1` `CRITICAL` `TASK_INCOMPLETE`: story was marked `done` before review closure; story lifecycle moved to `review` during fix pass.
- `F2` `HIGH` `ARCHITECTURE`: missing architecture artifact blocked compliance checks; added `_bmad-output/planning-artifacts/architecture.md`.
- `F3` `HIGH` `DOCUMENTATION`: missing review workflow path; added `_bmad/bmm/workflows/4-implementation/bmad-code-review/workflow.md`.
- `F4` `MEDIUM` `DOCUMENTATION`: `.cursorrules` contained roadmap-specific language; replaced with generic project-agnostic wording.
- `F5` `MEDIUM` `TEST_QUALITY`: handoff evidence lacked command-level traceability; updated with explicit commands and outputs.

### Test Runner Summary

- framework: `python3 -m pytest` + Bash validation suites
- targeted results:
  - `python3 -m pytest .claude/skills/bmad-distillator/scripts/tests -q` => `33 passed`
  - `python3 -m pytest .cursor/skills/bmad-distillator/scripts/tests -q` => `33 passed`
  - `story-1-1`, `story-1-2`, and `story-1-3` Bash validation suites => `PASS: all`

## Change Log

- 2026-04-20: Story created and moved to `ready-for-dev`.
- 2026-04-20: Implemented root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) and validation artifacts.
- 2026-04-20: Applied review follow-up fixes (`F1`-`F5`), expanded review dependencies, and re-ran validation suites.
- 2026-04-20: Validation closed cleanly and story status set to `done`.

## Dev Agent Record

### Agent Model Used

Codex 5.3

### Debug Log References

- RED: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task1` -> missing baseline audit evidence file.
- GREEN: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task1` -> `PASS: task1`.
- RED: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task2` -> missing canonical blueprint file.
- GREEN: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task2` -> `PASS: task2`.
- RED: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task3` -> missing `AGENTS.md`.
- GREEN: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task3` -> `PASS: task3`.
- RED: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task4` -> missing `CLAUDE.md`.
- GREEN: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task4` -> `PASS: task4`.
- RED: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task5` -> missing `.cursorrules`.
- GREEN: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task5` -> `PASS: task5`.
- RED: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task6` -> missing Task 6 validation report.
- GREEN: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task6` -> `PASS: task6`.
- RED: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task7` -> missing Task 7 handoff report.
- Regression after each task gate: `story-1-1-scaffold-validation.sh all` and `story-1-2-root-files-validation.sh all` -> `PASS`.
- GREEN: `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh task7` -> `PASS: task7`.
- Final regression: `story-1-1-scaffold-validation.sh all`, `story-1-2-root-files-validation.sh all`, and `story-1-3-root-context-validation.sh all` -> `PASS`.

### Completion Notes List

- Task 1: captured baseline audit for root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) and documented banned-term scan targets.
- Task 1: confirmed Story 1.3 stays scoped to root context files and does not pre-implement Epic 2 `.cursor/rules/*.mdc` content.
- Task 2: authored canonical instruction blueprint with shared sections (`Identity`, `Scope`, `Tone`, `Operating Constraints`, `Handoff Expectations`) and required placeholders.
- Task 3: created root `AGENTS.md` from the canonical blueprint with concise work-context boundaries and guardrails.
- Task 4: created root `CLAUDE.md` as a section-for-section mirror of `AGENTS.md` with matching placeholder usage.
- Task 5: created root `.cursorrules` with concise outbound-messaging and memory-protection guardrails, keeping scope high-level for Epic 2 compatibility.
- Task 6: executed deterministic checks for mirror parity, placeholder coverage, guardrail-topic presence, and banned-term scrub; persisted validation evidence.
- Task 7: prepared handoff artifact with AC-to-file mapping and regression summary for Stories 1.1/1.2/1.3.
- Final verification: Story 1.3 full validation suite passes with all task gates and completion checks.
- Review follow-up F1: story lifecycle set to `review` until this fix pass and final validation closure.
- Review follow-up F2/F3: added missing architecture and code-review workflow artifacts required by reviewer checklist inputs.
- Review follow-up F4: removed roadmap-specific phrasing from `.cursorrules` scope boundary.
- Review follow-up F5: enriched handoff report with explicit command/result traceability.
- Final closure: after review fixes and regression runs, story status advanced from `review` to `done`.

### File List

- `AGENTS.md` (root assistant instruction source aligned to canonical blueprint).
- `CLAUDE.md` (mirrored counterpart of `AGENTS.md`).
- `.cursorrules` (high-level outbound messaging and memory protection guardrails).
- `_bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh` (Story 1.3 RED/GREEN validation harness).
- `_bmad-output/implementation-artifacts/tests/story-1-3-baseline-audit.md` (Task 1 baseline evidence).
- `_bmad-output/implementation-artifacts/tests/story-1-3-canonical-blueprint.md` (Task 2 canonical instruction blueprint).
- `_bmad-output/implementation-artifacts/tests/story-1-3-task6-validation.md` (Task 6 deterministic AC validation evidence).
- `_bmad-output/implementation-artifacts/tests/story-1-3-task7-handoff.md` (Task 7 regression and AC mapping handoff artifact).
- `_bmad-output/planning-artifacts/architecture.md` (review dependency artifact for architecture-reference checks).
- `_bmad/bmm/workflows/4-implementation/bmad-code-review/workflow.md` (review checklist artifact path used by BMAD code review flow).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Story 1.3 lifecycle synchronization).
- `_bmad-output/implementation-artifacts/1-3-write-generic-agents-claude-cursorrules.md` (implementation record updates and completion tracking).

### PR Summary (AC Mapping)

- `AGENTS.md` + `CLAUDE.md` -> AC1, AC3, AC4: mirrored shared sections, placeholder-driven identity language, and scrubbed work-only wording.
- `.cursorrules` -> AC2, AC3, AC4: concise outbound messaging + memory protection guardrail summary with placeholders and scrubbed content.
- `_bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh` -> AC1, AC2, AC3, AC4: deterministic structural/content checks for all acceptance criteria.
- `_bmad-output/implementation-artifacts/tests/story-1-3-baseline-audit.md`, `story-1-3-task6-validation.md`, and `story-1-3-task7-handoff.md` -> reproducible evidence for baseline state, AC checks, and regression/handoff readiness.
