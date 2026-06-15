---
name: bmad-swarm
description: >-
  Full autonomous BMAD development swarm -- creates story, implements with
  parallel subagents, reviews, fixes, and ships a PR. Supports single story
  or full epic mode. Use when the user says 'swarm', 'bmad swarm',
  'autonomous dev', 'run the pipeline', or wants to implement a story or
  epic end-to-end without manual intervention.
argument-hint: "<story e.g. 0-1> | <epic e.g. epic-0> | 'next'"
---

# BMAD Swarm — Autonomous Development Pipeline (v6.3)

You are orchestrating a FULLY AUTONOMOUS development pipeline using the BMAD Method v6.3.
Your job: take a story from backlog to merged PR with ZERO user interaction.

**Target:** $ARGUMENTS

## Project Paths (resolve from config)

Read `_bmad/bmm/config.yaml` first. Then set:
- PROJECT_ROOT = the project root (where _bmad/ lives)
- PLANNING = resolved `planning_artifacts` from config
- IMPL = resolved `implementation_artifacts` from config
- SPRINT_STATUS = `IMPL/sprint-status.yaml`
- SKILLS_DIR = `.cursor/skills` (BMAD v6.3 skill workflows live here)

---

## PHASE 0: Target Resolution

Read SPRINT_STATUS fully. Then determine mode:

### Mode A — Single Story
If $ARGUMENTS is a story number like "0-1" or "2.3":
- Parse EPIC_NUM and STORY_NUM
- Look up full STORY_KEY in sprint status
- Set MODE = "single"

### Mode B — Next Story
If $ARGUMENTS is "next" or empty:
- Find FIRST story in sprint status with status "backlog" (scan top to bottom)
- Set EPIC_NUM, STORY_NUM, STORY_KEY from that entry
- Set MODE = "single"

### Mode C — Full Epic
If $ARGUMENTS matches "epic-N", "epic N", or just "epic 0", "epic-0":
- Parse EPIC_NUM from the argument
- Set MODE = "epic"
- Scan sprint status for ALL stories in this epic (keys matching `{EPIC_NUM}-*-*`)
- Build an ordered list of stories and their statuses
- Find the FIRST story in this epic that is NOT "done" and NOT "review"
  - If status is "backlog" → this is the target (needs create + dev + review)
  - If status is "ready-for-dev" → this is the target (needs dev + review, skip Phase 1)
  - If status is "in-progress" → this is the target (needs dev continuation + review)
- If ALL stories in the epic are "done":
  - Output: "All stories in epic {EPIC_NUM} are complete."
  - STOP — nothing to do
- Set STORY_KEY to the selected story

**Display status summary before proceeding:**
```
BMAD Swarm — Epic {EPIC_NUM} Status
  {story-key}: done
  {story-key}: done
  {story-key}: backlog  ← targeting this one
  {story-key}: backlog
  {story-key}: backlog
```

Store EPIC_NUM, STORY_NUM, STORY_KEY, MODE for all subsequent phases.

---

## PHASE 0.5: Create Branch

**Create the feature branch BEFORE any work begins.** This ensures all changes happen on the feature branch, not main.

### MODE = "single" (one story)
1. Create and switch to a new branch from main: `git checkout -b story/{STORY_KEY}`
2. Confirm you are on the new branch before proceeding

### MODE = "epic" (full epic)
1. Check if you are already on the epic branch `epic-{EPIC_NUM}/{epic-slug}`
2. If NOT: create and switch to the branch from main: `git checkout -b epic-{EPIC_NUM}/{epic-slug}`
3. If YES (resuming a previous epic run): stay on the branch, do NOT recreate it
4. Confirm you are on the correct branch before proceeding

**If branch creation fails** (e.g., branch already exists from a previous failed run):
- For single mode: `git checkout story/{STORY_KEY}` (switch to existing branch)
- For epic mode: `git checkout epic-{EPIC_NUM}/{epic-slug}` (switch to existing branch)
- If the checkout also fails, report the error and STOP

---

## PHASE 1: Create Story (Sequential — Task Agent)

**Skip this phase if story status is already "ready-for-dev" or "in-progress".**

Launch ONE Task agent (subagent_type: "generalPurpose") with this mission:

**Prompt for the agent — include the FULL contents of `{SKILLS_DIR}/bmad-create-story/workflow.md`:**
> You are running the BMAD create-story workflow AUTONOMOUSLY (YOLO mode — no user interaction).
>
> ## Configuration
> - PROJECT_ROOT = {PROJECT_ROOT}
> - STORY_KEY = {STORY_KEY}
> - EPIC_NUM = {EPIC_NUM}
> - STORY_NUM = {STORY_NUM}
> - story_path = {STORY_KEY} (user-provided story identifier — skip sprint-status discovery)
>
> ## Instructions
> Read and follow ALL of these workflow instructions. At every `<ask>` tag or user prompt, make the
> best autonomous decision (YOLO mode). Never wait for user input.
>
> ## Workflow
> {paste full contents of SKILLS_DIR/bmad-create-story/workflow.md here}
>
> ## Supporting Files
> ### discover-inputs.md
> {paste full contents of SKILLS_DIR/bmad-create-story/discover-inputs.md}
>
> ### template.md
> {paste full contents of SKILLS_DIR/bmad-create-story/template.md}
>
> ### checklist.md
> {paste full contents of SKILLS_DIR/bmad-create-story/checklist.md}
>
> ## Return
> Return: (1) the story file path, (2) a summary of the Tasks/Subtasks section with
> task groups that can be parallelized (tasks with no shared file dependencies).

**Wait for completion.** Extract from the result:
- STORY_PATH = path to created story file
- PARALLEL_TASK_GROUPS = groups of tasks that can run in parallel

---

## PHASE 2: Dev Story (Parallel Subagent Swarm)

Read the created story file at STORY_PATH. Analyze the Tasks/Subtasks section.

**Strategy for parallelization:**
- Group tasks that are INDEPENDENT (no shared file dependencies, no ordering requirements)
- Tasks within the same acceptance criterion that modify different files CAN be parallel
- Tasks that depend on output from other tasks MUST be sequential
- When in doubt, keep tasks sequential within their group

**Launch parallel Task agents** (subagent_type: "generalPurpose") — one per independent task group:

For each task group, the prompt includes the FULL contents of `{SKILLS_DIR}/bmad-dev-story/workflow.md`:
> You are running the BMAD dev-story workflow AUTONOMOUSLY (YOLO mode — no user interaction).
>
> ## Configuration
> - PROJECT_ROOT = {PROJECT_ROOT}
> - story_path = {STORY_PATH} (use this directly — skip sprint-status discovery)
>
> ## Task Scope
> You are responsible ONLY for implementing these specific tasks from the story:
> {description of tasks in this group}
>
> Do NOT touch tasks outside your assigned group. Do NOT modify the story file's status
> or sprint-status.yaml — the orchestrator handles that.
>
> ## Instructions
> Read the story file at {STORY_PATH}. Follow the dev-story workflow below, but:
> - Skip Step 1 (story discovery) — story_path is provided above
> - Skip Step 4 (sprint status update) — orchestrator handles this
> - Execute Steps 5-8 for your assigned tasks only
> - Skip Steps 9-10 (completion/status) — orchestrator handles this
> - At every `<ask>` tag, make the best autonomous decision (YOLO mode)
>
> ## Workflow
> {paste full contents of SKILLS_DIR/bmad-dev-story/workflow.md here}
>
> ## Supporting Files
> ### checklist.md (Definition of Done)
> {paste full contents of SKILLS_DIR/bmad-dev-story/checklist.md}
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
5. Update sprint-status.yaml: story status = "review"
6. Update story file Status to: "review"

---

## PHASE 3: Code Review (Sequential — Task Agent)

The BMAD v6.3 code review uses a parallel review architecture internally (Blind Hunter,
Edge Case Hunter, Acceptance Auditor). Launch ONE Task agent to run this.

Launch ONE Task agent (subagent_type: "generalPurpose"):

**Prompt — include the FULL contents of `{SKILLS_DIR}/bmad-code-review/workflow.md` AND all step files:**
> You are running the BMAD code-review workflow AUTONOMOUSLY (YOLO mode — no user interaction).
>
> ## Configuration
> - PROJECT_ROOT = {PROJECT_ROOT}
> - spec_file = {STORY_PATH}
> - review_mode = "full"
> - The diff source: uncommitted changes on the current branch vs main
>
> ## Instructions
> Follow the code review workflow below. This workflow uses step-file architecture:
>
> 1. **Step 1 (Gather Context):** The spec file is {STORY_PATH}. The diff is uncommitted
>    changes on the current branch vs main. Skip the user interaction cascade — construct the diff
>    using `git diff main` for tracked files AND `git ls-files --others --exclude-standard` to
>    identify new untracked files (then read those files for review). Auto-confirm the
>    checkpoint summary.
>
> 2. **Step 2 (Review):** Launch the three parallel review layers as described. If subagents
>    are available, use them. Otherwise, run each review layer sequentially in your context.
>
> 3. **Step 3 (Triage):** Normalize, deduplicate, and classify findings exactly as described.
>
> 4. **Step 4 (Present and Act):** Write findings to the story file. For decision-needed
>    findings, make the best autonomous judgment. For patch findings, choose option 1
>    (fix automatically). Update story status per the workflow instructions.
>
> At every HALT or user prompt, make the best autonomous decision. Never wait.
>
> ## Workflow (main)
> {paste full contents of SKILLS_DIR/bmad-code-review/workflow.md}
>
> ## Step Files
> ### step-01-gather-context.md
> {paste full contents of SKILLS_DIR/bmad-code-review/steps/step-01-gather-context.md}
>
> ### step-02-review.md
> {paste full contents of SKILLS_DIR/bmad-code-review/steps/step-02-review.md}
>
> ### step-03-triage.md
> {paste full contents of SKILLS_DIR/bmad-code-review/steps/step-03-triage.md}
>
> ### step-04-present.md
> {paste full contents of SKILLS_DIR/bmad-code-review/steps/step-04-present.md}
>
> ## Return
> Return: (1) total findings by category (decision-needed, patch, defer, dismiss),
> (2) number of patches auto-fixed, (3) updated story status (done or in-progress),
> (4) list of files modified by fixes.

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

## PHASE 4: Commit (Sequential)

**The branch was already created in Phase 0.5. You should already be on it.**

Verify you are on the correct branch before committing:
- Single mode: `story/{STORY_KEY}`
- Epic mode: `epic-{EPIC_NUM}/{epic-slug}`

If you are NOT on the correct branch, switch to it now before staging files.

### Phase 4a: Generate Changelog Fragment

Before staging and committing, generate a changelog fragment for this story:

1. Read the story file to extract the Linear identifier (from `linear_id` in sprint-status.yaml
   or the story metadata). If the story has a known Linear URL, extract the identifier from it.
2. Generate `.changelog/{IDENTIFIER}.yaml` with:
   ```yaml
   identifier: VIX-XXX
   title: "{story title}"
   category: "{derived from labels — Feature, Bug Fix, Infrastructure, Improvement, etc.}"
   labels: [{labels from the Linear issue}]
   summary: "{one-line summary of what was implemented}"
   ```
3. Include the fragment file in the staged files below.

If no Linear identifier is associated with this story, skip fragment generation.

### MODE = "single" (one story)
1. Stage all changed files (be specific — list files, don't use `git add -A`)
2. Create a commit with message format:
   ```
   feat(epic-{EPIC_NUM}): {story title} ({LINEAR_ID} / Story {STORY_KEY})

   - [summary of what was implemented]
   - [key technical decisions]
   - Code review findings addressed ({N} fixes applied)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
   Note: Include the Linear identifier (e.g. `VIX-663`) in the commit message so
   git-log extraction can find it as a fallback. Format: `({LINEAR_ID} / Story {STORY_KEY})`.
3. Push branch and create PR using `gh pr create`:
   - Title: `feat(epic-{EPIC_NUM}): {story title}`
   - Body: include story summary, ACs satisfied, review fixes applied, test results

### MODE = "epic" (full epic)
1. Stage all changed files (be specific — list files, don't use `git add -A`)
2. Create a commit with message format:
   ```
   feat(epic-{EPIC_NUM}): {story title} ({LINEAR_ID} / Story {STORY_KEY})

   - [summary of what was implemented]
   - [key technical decisions]
   - Code review findings addressed ({N} fixes applied)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
   Note: Include the Linear identifier in the commit message (same format as single mode).
3. Do NOT push or create a PR yet — continue to Phase 5 for the next story
4. Push and create PR only when ALL stories in the epic are done (in Phase 5)

---

## PHASE 5: Epic Loop or Finish

**If MODE = "single":**
- This story is done. Report completion.

**If MODE = "epic":**
- Re-read SPRINT_STATUS to get fresh state
- Count remaining stories in epic {EPIC_NUM} that are NOT "done"
- Display updated epic progress table
- If remaining == 0:
  - Push the epic branch and create a single PR using `gh pr create`:
    - Title: `feat(epic-{EPIC_NUM}): {epic title}`
    - Body: include summary of ALL stories completed, total test results, review fixes
  - Output: "All stories in epic {EPIC_NUM} are complete!"
- If remaining > 0:
  - Output: "Story {STORY_KEY} complete. {remaining} stories left in epic {EPIC_NUM}. Continuing..."
  - **LOOP BACK TO PHASE 0** — resolve the next story in this epic and repeat Phases 1-5
  - The loop continues until every story in the epic is "done"

**Epic loop keeps the orchestrator lean because:**
- All heavy work happens in subagents (fresh context each)
- The main context only tracks phase orchestration
- Each story's subagents start clean — no context bleed between stories

---

## Error Recovery

- If story creation fails: report error, do NOT proceed
- If a dev agent fails on a task: retry once with a fresh agent, then report failure
- If tests fail after parallel dev: attempt fix in main context, re-run tests
- If code review finds issues that can't be auto-fixed after one retry: report and stop
- If git push fails: report error with details
- At any failure: report what completed and what failed

## Orchestration Rules

- Use TodoWrite to track progress through phases (mark in_progress / completed)
- Launch parallel agents using multiple Task tool calls in a SINGLE message
- Subagents are "generalPurpose" type (Cursor Task tool)
- ALWAYS read the workflow file contents and EMBED them in the Task agent's prompt
  (subagents cannot read skill files on their own — you must provide the full text)
- The main orchestrator (you) handles sequencing; the subagents handle execution
- Monitor subagent results and handle failures before proceeding to next phase
- Sprint-status and story-status updates are handled by the BMAD workflows in Phases 1-3;
  the orchestrator only intervenes for Phase 2 post-completion sync and error recovery
