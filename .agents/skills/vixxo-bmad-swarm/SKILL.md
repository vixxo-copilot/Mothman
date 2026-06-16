---
name: vixxo-bmad-swarm
description: >-
  Full autonomous BMAD development swarm -- creates story, implements with
  parallel subagents, reviews, fixes, and ships a PR. Supports single story
  or full epic mode. Repo-portable via a local profile + first-run onboarding.
  Use when the user says 'swarm', 'bmad swarm', 'autonomous dev', 'run the
  pipeline', or wants to implement a story or epic end-to-end without manual
  intervention.
argument-hint: "<story e.g. 0-1> | <epic e.g. epic-0> | 'next'"
---

# BMAD Swarm -- Autonomous Development Pipeline (v6.8, profile-driven)

You are orchestrating a FULLY AUTONOMOUS development pipeline using the BMAD Method v6.8.
Your job: take a story from backlog to merged PR with ZERO user interaction.

This skill is **repo-portable**: a small repo-local **profile** supplies conventions
(branch/commit/changelog/PR), capability toggles, and Linear wiring, while the shared
skill core supplies the orchestration. Linear identity (team, owner, assignee) is reused
from the `linear-issue-creator` profile so the two skills never drift.

**Target:** $ARGUMENTS

---

## PHASE -1: Load Profile (or run onboarding)

Before anything else, load the repo-local profile:

- First set `PROJECT_ROOT` to the current repository root (the directory containing `_bmad/`).
  If `_bmad/` cannot be found from the current working directory, report that the swarm
  must be launched from a BMAD-enabled repo and STOP.
- Profile path: `{PROJECT_ROOT}/.agents/skills/vixxo-bmad-swarm/local/profile.yaml`
- If it does NOT exist, run the detection-first interview in
  `{skill-root}/reference/onboarding.md`, write `local/profile.yaml`, confirm it, then continue.
- Validate the loaded profile against `{skill-root}/config/profile-schema.yaml`.

Resolve these profile values for use in all later phases:
- `LINEAR_ON` = `linear_integration == enabled`
- `SKILLS_DIR` = `{PROJECT_ROOT}/{bmad.skills_dir}` (default `.agents/skills`)
- `BMAD_CONFIG` = `{PROJECT_ROOT}/{bmad.config_path}` (default `_bmad/bmm/config.yaml`)
- `BRANCH_SINGLE` / `BRANCH_EPIC` = `branch.single_template` / `branch.epic_template`
- `COMMIT_FMT` / `COAUTHOR` = `commit.message_format` / `commit.co_authored_by`
- `CHANGELOG_ON` / `CHANGELOG_DIR` / `CHANGELOG_RULE` = `changelog.*`
- `BASE_BRANCH` / `PR_TOOL` / `EPIC_PR_STRATEGY` = `pr.*`
- `RUN_BMAD_REVIEW` / `BUGBOT_ON` / `SECURITY_GLOBS` = `review.run_bmad_adversarial_review` / `review.bugbot_enabled` / `review.security_trigger_globs`
- `LINEAR_MCP` / `LINEAR_UPDATE_CLI` = `linear_tooling.*`
- `KICKOFF_RULE` / `LIFECYCLE_RULE` = `rule_refs.*` (may be empty)
- `WORKSPACE_DIRS` = `workspace_dirs` (list of workspace directory names, e.g. `["backend", "frontend"]`)
- **Linear identity:** if `linear.identity_source == linear-issue-creator`, read team/project/
  business-owner/assignee from `{PROJECT_ROOT}/.agents/skills/linear-issue-creator/local/profile.yaml`; else use
  `linear.inline_identity`.

If any referenced optional file (a rule_ref, the update CLI) is absent, proceed without it
rather than failing.

### Skill authority (read before any other phase)

- When this file at `{PROJECT_ROOT}/.agents/skills/vixxo-bmad-swarm/SKILL.md` is present, it is the
  **authoritative** swarm definition for this repo. Follow ITS phases end to end.
- Do NOT follow commit / push / PR steps from any other installed copy of the swarm skill (for
  example a legacy `bmad-swarm` install or `~/.claude/skills/bmad-swarm/SKILL.md`). Older copies may
  push and open a PR directly from Phase 4 with no pre-push review gate; that path is forbidden in
  this repo.
- If `KICKOFF_RULE` or `rule_refs.pre_push_gate` resolve to a file, read it now and honor it
  through to push/PR. The pre-push gate rule reinforces that Phase 3 and Phase 4b must complete
  before any push.
- If `LIFECYCLE_RULE` resolves to a file, read it now. The swarm satisfies the lifecycle's
  Required Checkpoints at two points: **Phase 0.25** (kickoff → `In Progress` with substantive
  note) and **Phase 4c** (PR-opened → `In Review` with structured summary, commit SHAs,
  changelog fragment path, and PR URL). Mid-work checkpoints (testing notes, progress notes)
  are captured in the story artifact file (`{IMPL}/{STORY_KEY}.md`), not as separate Linear
  comments. The swarm's terminal Linear state is **In Review**; the transition to **Done**
  happens outside the swarm when the PR is merged.

## Project Paths (resolve from config)

Read `BMAD_CONFIG` first. Then set:
- PLANNING = resolved `planning_artifacts` from config
- IMPL = resolved `implementation_artifacts` from config
- SPRINT_STATUS = `{IMPL}/sprint-status.yaml`

---

## PHASE 0: Target Resolution

Read SPRINT_STATUS fully. Then determine mode:

### Mode A -- Single Story
If $ARGUMENTS is a story number like "0-1" or "2.3":
- Parse EPIC_NUM and STORY_NUM
- Look up full STORY_KEY in sprint status
- Set MODE = "single"

### Mode B -- Next Story
If $ARGUMENTS is "next" or empty:
- Find FIRST story in sprint status with status "backlog" (scan top to bottom)
- Set EPIC_NUM, STORY_NUM, STORY_KEY from that entry
- Set MODE = "single"

### Mode C -- Full Epic
If $ARGUMENTS matches "epic-N", "epic N", or just "epic 0", "epic-0":
- Parse EPIC_NUM from the argument
- Set MODE = "epic"
- Scan sprint status for ALL stories in this epic (keys matching `{EPIC_NUM}-*-*`)
- Build an ordered list of stories and their statuses
- Find the FIRST story in this epic that is NOT "done" and NOT "review"
  - If status is "backlog" -> this is the target (needs create + dev + review)
  - If status is "ready-for-dev" -> this is the target (needs dev + review, skip Phase 1)
  - If status is "in-progress" -> this is the target (needs dev continuation + review)
- If ALL stories in the epic are "done":
  - Output: "All stories in epic {EPIC_NUM} are complete."
  - STOP -- nothing to do
- Set STORY_KEY to the selected story

**Display status summary before proceeding:**
```
BMAD Swarm -- Epic {EPIC_NUM} Status
  {story-key}: done
  {story-key}: done
  {story-key}: backlog  <- targeting this one
  {story-key}: backlog
  {story-key}: backlog
```

Store EPIC_NUM, STORY_NUM, STORY_KEY, MODE for all subsequent phases.
Read the active `development_status` row for STORY_KEY. Store:
- `CONTEXT_SOURCE` = `context_source` when present, otherwise `bmad-epic`
- `LINEAR_ID` / `LINEAR_URL` when present

`CONTEXT_SOURCE` controls Phase 1 story creation:
- `bmad-epic` -> BMAD planning artifacts are the primary source
- `linear-issue` -> the Linear issue body is the primary source

### Epic LINEAR_ID resolution (epic mode only)

When `MODE = "epic"` and `LINEAR_ON`:
1. Read `development_status["epic-{EPIC_NUM}"]` from SPRINT_STATUS. If it has a `linear_id`,
   store it as `EPIC_LINEAR_ID`.
2. If not found, scan `$ARGUMENTS` for a Linear URL matching the epic (e.g.
   `https://linear.app/.../issue/BRG-274/...`). Extract the identifier and store as
   `EPIC_LINEAR_ID`. Write it to the epic row in SPRINT_STATUS:
   `epic-{EPIC_NUM}: { status: in-progress, linear_id: "<IDENTIFIER>", linear_url: "<URL>" }`.
3. If no epic `linear_id` is available from either source, set `EPIC_LINEAR_ID = null` and
   proceed — epic parent Linear updates will be skipped with a warning.

`EPIC_LINEAR_ID` is used in Phase 0.25 (epic kickoff) and Phase 4c (PR-opened sync).

---

## PHASE 0.5: Create Branch

**Create the feature branch BEFORE any work begins.** This ensures all changes happen on the feature branch, not the base branch.

### MODE = "single" (one story)
1. Create and switch to a new branch from `{BASE_BRANCH}`: `git checkout -b {BRANCH_SINGLE}` (substitute STORY_KEY)
2. Confirm you are on the new branch before proceeding

### MODE = "epic" (full epic)
1. Check if you are already on the epic branch `{BRANCH_EPIC}` (substitute EPIC_NUM + epic-slug)
2. If NOT: create and switch to a new branch from `{BASE_BRANCH}`: `git checkout -b {BRANCH_EPIC}` (substitute EPIC_NUM + epic-slug)
3. If YES (resuming a previous epic run): stay on the branch, do NOT recreate it
4. Confirm you are on the correct branch before proceeding

**If branch creation fails** (e.g., branch already exists from a previous failed run):
- **MODE = "single":** switch to the existing branch: `git checkout {BRANCH_SINGLE}` (substitute STORY_KEY).
- **MODE = "epic":** switch to the existing branch: `git checkout {BRANCH_EPIC}` (substitute EPIC_NUM + epic-slug).
- If the checkout also fails, report the error and STOP.

---

## PHASE 1: Create Story (Sequential -- Task Agent)

**Skip this phase if story status is already "ready-for-dev" or "in-progress".**

**When Phase 1 is skipped**, resolve STORY_PATH before later phases:
- Set STORY_PATH = `{IMPL}/{STORY_KEY}.md`
- If that file does not exist, scan `{IMPL}/` for a file matching `{STORY_KEY}` or `{EPIC_NUM}-{STORY_NUM}-*.md` and use the first match.
- If no story file is found, report the blocker and STOP.

Launch ONE Task agent (subagent_type: "generalPurpose") with this mission. The subagent
READS the skill files by path (it has file access) -- do not paste full skill bodies.

**Prompt for the agent:**
> You are running the BMAD create-story workflow AUTONOMOUSLY (YOLO mode -- no user interaction).
>
> ## Configuration
> - PROJECT_ROOT = {PROJECT_ROOT}
> - STORY_KEY = {STORY_KEY}
> - EPIC_NUM = {EPIC_NUM}
> - STORY_NUM = {STORY_NUM}
> - story_path = {STORY_KEY} (user-provided story identifier -- skip sprint-status discovery)
> - CONTEXT_SOURCE = {CONTEXT_SOURCE}
> - LINEAR_ID = {LINEAR_ID if present}
>
> ## Read these workflow files FIRST (you have file access -- read them by path):
> - `{SKILLS_DIR}/bmad-create-story/SKILL.md` -- the workflow you will follow
> - `{SKILLS_DIR}/bmad-create-story/discover-inputs.md` -- follow when the workflow says to discover inputs
> - `{SKILLS_DIR}/bmad-create-story/template.md` -- the story file template
> - `{SKILLS_DIR}/bmad-create-story/checklist.md` -- run validation at the end (auto-accept all improvements)
> (If any path cannot be read, report it and the orchestrator will embed the contents.)
>
> ## Activation Override
> Skip the interactive activation steps (resolve_customization.py, greet user, etc.).
> Instead, load config directly from `{BMAD_CONFIG}` and resolve
> `project_name`, `planning_artifacts`, `implementation_artifacts`, `date` (current datetime).
> Load `{PROJECT_ROOT}/**/project-context.md` if it exists as persistent facts.
>
> ## Context Source Routing
> If `CONTEXT_SOURCE == "linear-issue"` **and** `LINEAR_ID` is present, fetch the Linear issue body
> using LINEAR_ID and use that issue body as the primary story source. Do not fail just because BMAD
> epics/planning files lack a matching story entry. Still load relevant PRD, architecture, UX,
> previous-story, and project-context artifacts for implementation guardrails.
>
> If `CONTEXT_SOURCE == "linear-issue"` **and** `LINEAR_ID` is missing, use the bmad-epic path below;
> Phase 0.25 will backfill the Linear link.
>
> If `CONTEXT_SOURCE == "bmad-epic"`, use the normal BMAD create-story behavior: load the matching
> epic/story content from BMAD planning artifacts and use it as the primary story source.
>
> ## Instructions
> Read and follow ALL of the create-story workflow instructions. At every `<ask>` tag or user
> prompt, make the best autonomous decision (YOLO mode). Never wait for user input.
>
> ## Sprint-Status Update Rules
> {paste the Sprint-Status Update Rules block from the bottom of this skill, substituting status `ready-for-dev`}
>
> ## Return
> Return: (1) the story file path, (2) a summary of the Tasks/Subtasks section with
> task groups that can be parallelized (tasks with no shared file dependencies).

**Wait for completion.** Extract from the result:
- STORY_PATH = path to created story file
- PARALLEL_TASK_GROUPS = groups of tasks that can run in parallel

---

## PHASE 0.25: Linear Kickoff Status Sync

**Skip this entire phase when `LINEAR_ON` is false (pure-BMAD mode).**

After create-story (Phase 1) has populated sprint metadata, and before launching dev work,
move the active story's Linear issue to `In Progress`.

If `KICKOFF_RULE` is set, read and follow it -- it is the authoritative source for what
constitutes a substantive kickoff note. If it is empty, apply the default content standard below.

### Required actions (all modes)
1. Read SPRINT_STATUS and resolve the active story entry (STORY_KEY).
2. Extract LINEAR_ID from `linear_id` in sprint status.
3. If `linear_id` is missing, extract LINEAR_ID from `linear_url` (e.g. `.../<PREFIX>-123/...`).
4. If LINEAR_ID is still missing, invoke `linear-issue-creator` to backfill the issue:
   - Launch one `generalPurpose` subagent.
   - Instruct it to read `{SKILLS_DIR}/linear-issue-creator/SKILL.md`,
     `{SKILLS_DIR}/linear-issue-creator/reference/workflow.md`, and
     `{SKILLS_DIR}/linear-issue-creator/reference/sprint-status-mirror.md`.
   - Prompt:
     ```text
     Create exactly one Linear Story issue for BMAD swarm execution.

     Inputs:
     - PROJECT_ROOT = {PROJECT_ROOT}
     - STORY_KEY = {STORY_KEY}
     - STORY_PATH = {STORY_PATH}
     - CONTEXT_SOURCE = {CONTEXT_SOURCE}
     - Sprint status path = {SPRINT_STATUS}

     Use the story file and BMAD planning context as the issue source. This is an autonomous
     swarm-create invocation: create only if every non-negotiable gate resolves deterministically,
     readiness is PASS, required Linear metadata verifies, and duplicate check finds no likely
     duplicate. If any gate requires judgment, stop and return the blocker.

     After creation, write/update the sprint-status mirror row per the linear-issue-creator
     sprint-status mirror contract with the new `linear_id`, `linear_url`, `context_source: bmad-epic`,
     and `last_updated`. Preserve the existing `status` value from the sprint-status row -- do not
     regress to `backlog`. Do not add dated comment blocks.
     ```
   - Wait for completion, then re-read SPRINT_STATUS and extract LINEAR_ID / LINEAR_URL again.
   - If LINEAR_ID is still missing, report the blocker and STOP.
5. Update Linear immediately:
   - Set status to `In Progress`
   - Post a substantive implementation note containing: story key, Linear ID, scope,
     expected files/areas, artifact link, and trigger.
6. Only continue to Phase 2 after this update succeeds.

### Mode-specific scope
- **MODE = single / next:** update the one targeted story before Phase 2.
- **MODE = epic:** update the first selected story before Phase 2, then repeat this
  kickoff sync each loop when a new story becomes the active STORY_KEY.

### Epic parent kickoff (epic mode, first story only)

When `MODE = "epic"` and `EPIC_LINEAR_ID` is present and this is the **first story** in the
epic loop (not a subsequent loop iteration):
1. Move the epic issue (`EPIC_LINEAR_ID`) to `In Progress`.
2. Post a kickoff note listing: all stories in scope (from the sprint-status scan), the epic
   branch name, the trigger (`swarm epic-{EPIC_NUM}`), and the target PR strategy
   (`single-pr-at-end` or per-story).

Skip this on subsequent loop iterations — the epic stays `In Progress` through the loop.

### Tooling preference
1. Linear MCP `save_issue` with state set to `In Progress` plus the full implementation note (when `LINEAR_MCP`).
2. If MCP is unavailable and `LINEAR_UPDATE_CLI` is set: `node {LINEAR_UPDATE_CLI} <LINEAR_ID> --status "In Progress" --implementation "<substantive note>"`.

### Failure handling
- If no LINEAR_ID can be resolved or backfilled, report a blocker and STOP.
- Do NOT silently continue without status sync.

---

## PHASE 2: Dev Story (Parallel Subagent Swarm)

Read the created story file at STORY_PATH. Analyze the Tasks/Subtasks section.

**Strategy for parallelization:**
- Group tasks that are INDEPENDENT (no shared file dependencies, no ordering requirements)
- Tasks within the same acceptance criterion that modify different files CAN be parallel
- Tasks that depend on output from other tasks MUST be sequential
- When in doubt, keep tasks sequential within their group

**Launch parallel Task agents** (subagent_type: "generalPurpose") -- one per independent task group.
Each subagent READS the workflow files by path:

> You are running the BMAD dev-story workflow AUTONOMOUSLY (YOLO mode -- no user interaction).
>
> ## Configuration
> - PROJECT_ROOT = {PROJECT_ROOT}
> - story_path = {STORY_PATH} (use this directly -- skip sprint-status discovery)
>
> ## Read these workflow files FIRST (read by path):
> - `{SKILLS_DIR}/bmad-dev-story/SKILL.md` -- the workflow you will follow
> - `{SKILLS_DIR}/bmad-dev-story/checklist.md` -- the Definition of Done criteria
> (If any path cannot be read, report it and the orchestrator will embed the contents.)
>
> ## Activation Override
> Skip the interactive activation steps. Load config directly from `{BMAD_CONFIG}` and resolve
> `project_name`, `implementation_artifacts`, `date`. Load `{PROJECT_ROOT}/**/project-context.md` if present.
>
> ## Task Scope
> You are responsible ONLY for implementing these specific tasks from the story:
> {description of tasks in this group}
>
> Do NOT touch tasks outside your assigned group. Do NOT modify the story file's status
> or sprint-status.yaml -- the orchestrator handles that.
>
> ## Instructions
> Follow the dev-story workflow, but:
> - Skip Step 1 (story discovery) -- story_path is provided above
> - Skip Step 4 (sprint status update) -- orchestrator handles this
> - Execute Steps 5-8 for your assigned tasks only
> - Skip Steps 9-10 (completion/status) -- orchestrator handles this
> - At every `<ask>` tag, make the best autonomous decision (YOLO mode)
>
> ## Return
> Return: (1) list of tasks completed with [x], (2) list of files created/modified,
> (3) test results summary, (4) any issues encountered.

**If tasks cannot be parallelized** (too interdependent), launch a single agent with all tasks.

**Wait for ALL dev agents to complete.** Collect results from each.

**After all dev agents finish:**
1. Read the story file to verify all tasks are marked [x]
2. If any tasks remain unchecked, launch additional agents to complete them
3. Run the full test suite to verify no conflicts between parallel work
4. If tests fail, fix integration issues in the main context
5. Update sprint-status.yaml: story status = "review" (or "done" when `RUN_BMAD_REVIEW` is false)
6. Update story file Status to match

---

## PHASE 3: Code Review (Sequential -- Task Agent)

**Skip this phase when `RUN_BMAD_REVIEW` is false.** Phase 2 already promotes the story to
`done` when review is disabled.

The BMAD v6.8 code review uses a step-file architecture with parallel internal review layers
(Blind Hunter, Edge Case Hunter, Acceptance Auditor). Launch ONE Task agent to run this.

Launch ONE Task agent (subagent_type: "generalPurpose"):

> You are running the BMAD code-review workflow AUTONOMOUSLY (YOLO mode -- no user interaction).
>
> ## Configuration
> - PROJECT_ROOT = {PROJECT_ROOT}
> - spec_file = {STORY_PATH}
> - review_mode = "full"
> - The diff source: uncommitted changes on the current branch vs `{BASE_BRANCH}`
>
> ## Read these workflow files FIRST (read by path):
> - `{SKILLS_DIR}/bmad-code-review/SKILL.md`
> - `{SKILLS_DIR}/bmad-code-review/steps/step-01-gather-context.md`
> - `{SKILLS_DIR}/bmad-code-review/steps/step-02-review.md`
> - `{SKILLS_DIR}/bmad-code-review/steps/step-03-triage.md`
> - `{SKILLS_DIR}/bmad-code-review/steps/step-04-present.md`
> (If any path cannot be read, report it and the orchestrator will embed the contents.)
>
> ## Activation Override
> Skip the interactive activation steps. Load config directly from `{BMAD_CONFIG}` and resolve
> `project_name`, `planning_artifacts`, `implementation_artifacts`, `date`. Load project-context.md if present.
>
> ## Instructions
> 1. Step 1 (Gather Context): spec file is {STORY_PATH}. The diff is uncommitted changes on
>    the current branch vs `{BASE_BRANCH}`. Construct it using `git diff {BASE_BRANCH}` for
>    tracked files AND `git ls-files --others --exclude-standard` to identify new untracked
>    files (then read those files for review). Skip the user interaction cascade. Auto-confirm
>    the checkpoint summary.
> 2. Step 2 (Review): launch the three parallel review layers; if subagents are unavailable,
>    run each layer sequentially in your context.
> 3. Step 3 (Triage): normalize, deduplicate, classify findings exactly as described.
> 4. Step 4 (Present and Act): write findings to the story file. For decision-needed findings,
>    make the best autonomous judgment. For patch findings, fix automatically. Update story status.
> At every HALT or user prompt, make the best autonomous decision. Never wait.
>
> ## Sprint-Status Update Rules
> {paste the Sprint-Status Update Rules block from the bottom of this skill, with status as determined by review outcome}
>
> ## Return
> Return: (1) total findings by category, (2) number of patches auto-fixed,
> (3) updated story status (done or in-progress), (4) list of files modified by fixes.

**Wait for completion.** Extract results.

**After code review completes:**
- If story status is "done": proceed to test verification below
- If story status is "in-progress" (unresolved findings): attempt fixes in main context,
  then re-run a lightweight review. If still failing after one retry, report and STOP.
- Read the updated sprint-status.yaml to confirm status was synced by the workflow
- **Safety net:** If sprint-status.yaml still shows "review" but the story is ready for commit
  (all tests pass, no unresolved findings), update sprint-status.yaml to "done" directly.
  This ensures epic mode's Phase 5 loop does not stall on stories stuck at "review".

**Final test verification (after any review fixes):**
1. Run the full test suite one final time
2. Verify ALL tests pass
3. If any test fails, debug and fix in main context, then re-run tests
4. Only proceed to Phase 4 when all tests pass

---

## PHASE 4: Commit, Pre-Push Review Gate, and PR (Sequential)

**The branch was already created in Phase 0.5. You should already be on it.** Verify the branch
matches `BRANCH_SINGLE` / `BRANCH_EPIC` before committing; switch to it if not.

### Phase 4a: Generate Changelog Fragment

**Skip when `CHANGELOG_ON` is false.**

Generate a changelog fragment per `CHANGELOG_RULE` (the single source of truth for fragment
shape and the labels -> `category` mapping). Workflow:
1. Extract the Linear identifier (from `linear_id` in sprint-status.yaml or the story metadata).
2. Derive `category` using the table in `CHANGELOG_RULE`.
3. Write `{CHANGELOG_DIR}/{IDENTIFIER}.yaml` with the required fields.
4. Include the fragment file in the staged files below.
5. Reference the fragment path in the Linear issue's implementation note (when `LINEAR_ON`).

If no Linear identifier is associated with this story, skip fragment generation.

### MODE = "single" (one story)
1. Stage all changed files (be specific -- list files, don't use `git add -A`)
2. Create a commit using `COMMIT_FMT` (substitute EPIC_NUM, story_title, LINEAR_ID, STORY_KEY).
   Append a `Co-Authored-By: {COAUTHOR}` trailer only when `COAUTHOR` is non-empty.
   Include the Linear identifier in the message so git-log extraction can find it as a fallback.
3. Run **Phase 4b: Pre-Push Bugbot / Security Gate** below. This reviews the committed
   branch diff before it is pushed, so the PR's Bugbot run can recognize the same diff and skip.
4. Run the **Pre-Push Self-Check** below. Only if every box passes:
   push branch and create PR using `{PR_TOOL}` against `{BASE_BRANCH}`:
   - Title: `feat(epic-{EPIC_NUM}): {story_title}`
   - Body: story summary, ACs satisfied, review fixes applied, test results
5. Run **Phase 4c: PR-opened Linear Sync** below.

### MODE = "epic" (full epic)
1. Stage all changed files (be specific)
2. Create a commit using `COMMIT_FMT` (same trailer rule as single mode)
3. Run **Phase 4b: Pre-Push Bugbot / Security Gate** below for early per-story defect detection,
   but do NOT push yet.
4. Continue to Phase 5. Epic mode uses one shared epic branch and opens a single PR at the
   end of the epic.

### Phase 4b: Pre-Push Bugbot / Security Gate

**Skip this phase when `BUGBOT_ON` is false.** If skipped:
- Continue to the **Pre-Push Self-Check** when this gate is the final step before push
  (single mode after step 3, or epic mode at Phase 5 `remaining == 0`).
- Continue to Phase 5 when this gate runs during epic per-story commits (Phase 4).

This gate reviews the **committed branch diff** (`{BASE_BRANCH}...HEAD`) before push. Any
fixes made after review must be committed and then reviewed again, because the pushed diff
must match the last reviewed diff for the PR's Bugbot run to skip.

1. Confirm the working tree has no uncommitted implementation changes except intentionally
   excluded local artifacts. If there are relevant unstaged/staged changes, stage and commit
   them before review.
2. Launch exactly one `bugbot` subagent with:
   - `readonly: true`
   - `run_in_background: false`
   - `description: "Bugbot"`
   - `subagent_type: "bugbot"`
   - Prompt:
     ```text
     Full Repository Path: {PROJECT_ROOT}
     Diff: branch changes
     Base Branch: {BASE_BRANCH}
     Custom Instructions: Review the committed branch diff for correctness regressions, missed edge cases, broken orchestration, and test gaps. Focus on actionable bugs only.
     ```
3. Decide whether to run `security-review` using two independent trigger lanes. An empty
   `SECURITY_GLOBS` disables ONLY the glob lane; the content-heuristic lane always runs. (To
   disable the security pass entirely, set `BUGBOT_ON` to false, which skips all of Phase 4b.)
   - **Path globs:** when `SECURITY_GLOBS` is non-empty, match it against **file paths** from
     `git diff --name-only {BASE_BRANCH}...HEAD`. When `SECURITY_GLOBS` is empty, this lane is
     off (no path-based trigger) — fall through to the content-heuristic lane.
   - **Content heuristics:** run security review when the diff content touches auth/authz,
     secrets/env vars, crypto, SQL/migrations, API routes, webhooks, file upload, permission
     checks, or external input handling — even if no path glob matched (or globs are empty).
   - When uncertain, run security review.
   - If either lane triggers:
     - Launch exactly one `security-review` subagent with `readonly: true`,
       `run_in_background: false`, `description: "Security Review"`, and
       `subagent_type: "security-review"`.
     - Use this prompt shape:
       ```text
       Full Repository Path: {PROJECT_ROOT}
       Diff: branch changes
       Base Branch: {BASE_BRANCH}
       Custom Instructions: Review security-sensitive changes only. Flag vulnerabilities, authorization gaps, secret exposure, injection risks, and unsafe external input handling.
       ```
4. Handle findings. This gate runs the **local** Bugbot/security subagent before push; it is
   separate from the GitHub PR Bugbot, which runs unlimited on the PR and is unaffected by this
   guard. The guard exists only to prevent local fix/review loops, NOT to throttle real findings.
   - If Bugbot/security-review reports no findings, continue.
   - Auto-fix patch-level findings in the main context, run the relevant local tests, commit
     the fixes, and rerun this Phase 4b gate.
   - Stop and report any HIGH/security finding that requires product, architecture, or risk
     judgment — these stop immediately on first occurrence.
   - **No fixed cap on gate runs.** Keep looping fix → review as long as each cycle makes
     progress — i.e., it addresses new/distinct findings or the total finding count decreases.
     STOP and report only when: (a) the gate is clean (proceed to push), (b) the **same** finding
     recurs after a fix attempt (oscillation), or (c) a cycle yields **no net progress** versus the
     prior cycle (same set of findings, none resolved). This honors "don't throttle if it's finding
     real things" while still terminating on loops or stalls.

### Pre-Push Self-Check (mandatory before any push or PR)

Run this checklist immediately before `git push` / `{PR_TOOL}` in both single mode (Phase 4)
and epic finish (Phase 5 `remaining == 0`). If ANY box is unchecked, STOP and do not push --
fix the gap (or report the blocker) first. Do not push to "let CI/PR Bugbot catch it".

- [ ] Phase -1 loaded the repo profile from `{PROJECT_ROOT}/.agents/skills/vixxo-bmad-swarm/local/profile.yaml`,
      and this repo skill (not another swarm-skill copy) is the one being followed.
- [ ] Phase 3 (`bmad-code-review`) completed for the work being pushed -- or was skipped ONLY
      because `RUN_BMAD_REVIEW` is false.
- [ ] All implementation work is committed; the working tree has no relevant uncommitted changes
      (Phase 4b reviews the committed `{BASE_BRANCH}...HEAD` diff).
- [ ] Phase 4b ran on the diff being pushed and reports zero remaining patch-level findings --
      or was skipped ONLY because `BUGBOT_ON` is false.
- [ ] Any fixes made after the last Phase 4b run were committed and Phase 4b was rerun, so the
      pushed diff matches the last reviewed diff.
- [ ] Epic mode only: the final Phase 4b ran against the cumulative epic diff, not just the last story --
      or was skipped ONLY because `BUGBOT_ON` is false.
- [ ] `graphify-out/` changes are not in the committed diff (`git diff --name-only {BASE_BRANCH}...HEAD`
      shows no `graphify-out/` paths).

Only when every applicable box is checked may you push and open the PR.

### Phase 4c: PR-opened Linear Sync

**Skip when `LINEAR_ON` is false.**

After `git push` and `{PR_TOOL}` succeed (single mode Phase 4 step 5, or epic mode Phase 5
epic finish), update Linear to reflect that the work is in review. Capture the PR URL from the
`gh pr create` output.

**For each story in the PR** (single mode: one story; epic mode: all stories with `done` status):
1. `save_issue` with `state: "In Review"`.
2. `save_comment` with a structured note containing:
   - **Summary:** one-line from the commit message for this story.
   - **PR:** the PR URL.
   - **Commits:** SHA(s) from `git log --oneline {BASE_BRANCH}..HEAD` that reference this story's
     LINEAR_ID (use `grep` on the log output).
   - **Testing:** pass counts from the dev/review phases (stored by the orchestrator during
     Phase 2/3).
   - **Review:** findings summary (N patches applied, N deferred, N dismissed).
   - **Changelog:** `{CHANGELOG_DIR}/{IDENTIFIER}.yaml` (when `CHANGELOG_ON`).
   - **Story artifact:** `{IMPL}/{STORY_KEY}.md`.

**For the epic parent** (when `EPIC_LINEAR_ID` is present):
1. `save_issue` with `state: "In Review"`.
2. `save_comment` with a rollup note: PR URL, list of all stories completed, total test results
   across the epic, migrations added, and a link to each story's changelog fragment.

**Scope boundary:** `In Review` is the swarm's terminal Linear state — the swarm never sets
`Done`. The post-swarm tail is a human/post-deploy responsibility: on PR merge the issue moves to
`Pending Deployment`, and only after the deployment is verified does it move to `Done` (with final
implementation/testing/deploy notes and artifact links). `Done` means deployed, not merged.

---

## PHASE 5: Epic Loop or Finish

**If MODE = "single":**
- This story is done.
- Run **Phase 4c: PR-opened Linear Sync** (already triggered in Phase 4 step 5).
- Report completion. The swarm's terminal Linear state is `In Review`.

**If MODE = "epic":**
- Re-read SPRINT_STATUS to get fresh state
- Count remaining stories in epic {EPIC_NUM} that are NOT "done"
- Display updated epic progress table
- If remaining > 0:
  - Output: "Story {STORY_KEY} complete. {remaining} stories left in epic {EPIC_NUM}. Continuing..."
  - **LOOP BACK TO PHASE 0** -- resolve the next story and repeat Phases 1, 0.25, and 2-5
  - The loop continues until every story in the epic is "done"
- If remaining == 0:
  1. **Merge base branch:** `git fetch origin {BASE_BRANCH} && git merge origin/{BASE_BRANCH}`.
     If merge conflicts arise, attempt auto-resolution. If auto-resolution fails, STOP and
     report the conflicts — do not push a conflicted branch.
  2. **Full test suite:** resolve the workspace set first. If `WORKSPACE_DIRS` is non-empty, use
     it. If it is empty, do NOT silently skip verification — auto-detect at runtime every
     directory containing a `package.json` with a `test` script (use `.` for a single-package
     root). If detection still finds none, STOP and report "epic-end verification skipped: no
     `WORKSPACE_DIRS` configured and no `package.json` with a test script found" rather than
     passing the gate. For each resolved directory, run `npm test`, `npm run build` (or
     `npm run typecheck` if `build` is absent), and `npm run lint`. If any fail, fix and rerun.
     Only proceed when all pass.
  3. **Sprint-status finalization:** update the epic row `development_status["epic-{EPIC_NUM}"]`,
     preserving its object shape and metadata — set its `status` field to `done`, keep
     `linear_id` / `linear_url` if present, and set `last_updated`. Do NOT replace the row with
     the bare string `"done"` (that drops `linear_id` and breaks later reads). Also bump the
     top-level `last_updated`. Stage and commit this change.
  4. Run **Phase 4b: Pre-Push Bugbot / Security Gate** one final time on the full epic branch
     diff. This final pass is required even if per-story gates already ran, because the PR will
     contain the cumulative epic diff.
  5. Run the **Pre-Push Self-Check**. Only if every box passes:
     push the epic branch and create a single PR using `{PR_TOOL}` against `{BASE_BRANCH}`
     (Title: `feat(epic-{EPIC_NUM}): {epic title}`; Body: summary of ALL stories,
     total test results, review fixes, migrations).
  6. Run **Phase 4c: PR-opened Linear Sync** (all stories + epic parent → `In Review`).
  7. Output: "All stories in epic {EPIC_NUM} are complete! PR opened, Linear issues In Review."

**Epic loop keeps the orchestrator lean because:**
- All heavy work happens in subagents (fresh context each)
- The main context only tracks phase orchestration
- Each story's subagents start clean -- no context bleed between stories

---

## Error Recovery

- If story creation fails: report error, do NOT proceed
- If a dev agent fails on a task: retry once with a fresh agent, then report failure
- If tests fail after parallel dev: attempt fix in main context, re-run tests
- If code review finds issues that can't be auto-fixed after one retry: report and stop
- If Bugbot/security-review finds HIGH/security issues that need human judgment, stop immediately
- If the local Phase 4b gate stops making progress — the same finding recurs after a fix (oscillation) or a cycle resolves nothing — stop and report. There is no fixed run cap; the loop only ends on clean, oscillation, or no-progress. (The GitHub PR Bugbot is separate and runs unlimited.)
- If git push fails: report error with details
- At any failure: report what completed and what failed

## Orchestration Rules

- Use TodoWrite to track progress through phases (mark in_progress / completed)
- Launch parallel agents using multiple Task tool calls in a SINGLE message
- Subagents are "generalPurpose" type (Cursor Task tool) unless a phase specifies otherwise
  (Phase 4b uses `bugbot` and `security-review`)
- Subagents have file access: instruct them to READ the workflow/step files by path. Only if a
  path read fails and the file is <= 15 KB, the orchestrator may embed the file contents as a
  fallback. If the file exceeds 15 KB, do NOT embed — report: "Skill file at {path} is too large
  to embed. Ensure the skill is installed at the expected path." and STOP.
- The main orchestrator (you) handles sequencing; the subagents handle execution
- Monitor subagent results and handle failures before proceeding to next phase
- Sprint-status and story-status updates are handled by the BMAD workflows in Phases 1-3;
  the orchestrator only intervenes for Phase 2 post-completion sync and error recovery
- Never stage or commit `graphify-out/**` files during a swarm run. After each commit, if the
  graphify hook modifies `graphify-out/`, discard those changes before staging the next story:
  `git checkout -- graphify-out/ 2>/dev/null || true`. Graphify rebuild happens post-merge via
  the hook.

## Sprint-Status.yaml Update Rules

When dispatching create-story / dev-story / code-review subagents, you MUST instruct them to update ONLY the `development_status:` entry for the story. You MUST NOT instruct them to add or amend dated comment blocks (e.g. `# 2026-MM-DD: Story ...`) anywhere in `sprint-status.yaml`.

**Rationale:** every BMAD skill that reads this file reads only the metadata header (`generated`, `last_updated`, `project_key`, `tracking_system`, `story_location`), the STATUS DEFINITIONS / WORKFLOW NOTES, and the `development_status:` map. The dated comment-block journal has no downstream consumer and is a guaranteed merge-conflict generator: every parallel PR prepends a new block at the same insertion point under `last_updated:`, and git cannot auto-resolve these.

Story-level history is already captured in per-story files under `{implementation_artifacts}/{story-key}.md` and in changelog fragments; the journal is pure duplication.

**Required subagent instruction** (use this exact wording in every create-story / dev-story / code-review prompt that touches sprint-status.yaml):

> Update `{IMPL}/sprint-status.yaml`:
> - Add or update a `development_status` entry with the story_key `<key>`, status `<status>`, `linear_id`, `linear_url`, `context_source`, and `last_updated`.
> - Preserve an existing `context_source` value. If it is missing, set `context_source: bmad-epic` for BMAD-planned stories and `context_source: linear-issue` for creator-driven stories.
> - Bump top-level `last_updated:` to today's date.
> - Do NOT add any dated comment block (`# YYYY-MM-DD: ...`) anywhere in the file -- not at the top under `last_updated:`, not inline above the new `development_status:` entry, not anywhere else. Only the `development_status:` entry update and the top-level `last_updated:` bump are allowed.
> - Preserve ALL existing comments (STATUS DEFINITIONS, WORKFLOW NOTES) verbatim. Do not delete pre-existing dated journal entries either -- those will be cleaned up in a separate dedicated PR.

**Failure mode to watch for:** if a subagent returns a result that says it "added a dated comment block summarizing the story" anywhere in `sprint-status.yaml`, treat that as drift: (a) revert the comment-block addition before continuing, (b) re-emit the explicit "Do NOT add any dated comment block" instruction before re-dispatching, and (c) note the deviation in the swarm run log.

## Conventions

- `{skill-root}` resolves to this skill's installed directory (where `config/` and `reference/` live).
- `{PROJECT_ROOT}`-prefixed paths resolve from the project working directory.
- The active repo profile lives at `{PROJECT_ROOT}/.agents/skills/vixxo-bmad-swarm/local/profile.yaml`
  (gitignored). If it is missing, run `{skill-root}/reference/onboarding.md` before Phase 0.
