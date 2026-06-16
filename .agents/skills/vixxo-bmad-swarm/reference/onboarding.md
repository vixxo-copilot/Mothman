# First-Run Configuration (Detection-First)

When a repo has no active swarm profile at
`.agents/skills/vixxo-bmad-swarm/local/profile.yaml`, do not fail. Detect what you
can from the repo, ask only the genuinely ambiguous choices, write the profile,
confirm it, then continue with the original swarm request. On later runs the
profile exists, so this is skipped.

## When to run

- The user invokes the swarm (`swarm`, `bmad swarm`, `swarm next`,
  `swarm epic-N`), and
- `.agents/skills/vixxo-bmad-swarm/local/profile.yaml` does not exist.

## Step 1: Detect (do not ask)

Resolve these from the repo silently; only fall back to a question if detection
is genuinely inconclusive.

- **BMAD config** — locate `_bmad/bmm/config.yaml`. If absent, the swarm
  requires BMAD: tell the user to install BMAD first and stop. Set
  `bmad.config_path`.
- **BMAD skills dir** — auto-detect `bmad.skills_dir` by scanning
  `.agents/skills` and `.cursor/skills` for workflow skills
  (`bmad-create-story`, `bmad-dev-story`, `bmad-code-review`) and
  `bmad-code-review/steps/step-*.md` (Phase 3 reads these by path). Prefer
  `.agents/skills` when both are complete; otherwise use whichever has the full
  set including review steps; default `.agents/skills` when neither does.
- **Base branch** — `git symbolic-ref refs/remotes/origin/HEAD` (or
  `git remote show origin`); fall back to `main`. Set `pr.base_branch`.
- **`gh` availability** — `gh --version`. Set `pr.tool` to `gh` if present.
- **Changelog** — if a `.changelog/` dir or `.cursor/rules/changelog-fragments.mdc`
  exists, set `changelog.enabled: true`, `changelog.dir`, `changelog.rule_ref`;
  else `changelog.enabled: false`.
- **Repo rules** — if `.cursor/rules/vixxo-bmad-swarm-linear-kickoff.mdc` or a Linear
  lifecycle rule exists, record them under `rule_refs`; else leave blank.
- **Linear identity** — if
  `.agents/skills/linear-issue-creator/local/profile.yaml` exists, set
  `linear.identity_source: linear-issue-creator` (reuse its team/project/owner).
  If the creator skill is not installed, set `identity_source: inline` and ask
  for team + id_prefix in Step 2.
- **Linear tooling** — detect a repo-local Linear update fallback script (e.g.
  `update-linear-issue.js`) and record it under `linear_tooling.update_cli`;
  default `linear_tooling.mcp: true`.
- **Bugbot / security review** — default `review.bugbot_enabled: true` and a
  conservative `review.security_trigger_globs` set; default
  `review.run_bmad_adversarial_review: true`.
- **Workspace dirs** — scan the repo for directories containing a `package.json`
  with a `test` script (e.g. `backend/`, `frontend/`). Record them under
  `workspace_dirs`. The swarm runs the convention-based full test suite
  (`npm test`, `npm run build` or `npm run typecheck`, `npm run lint`) in each
  listed directory at epic finish. If the repo is a single-package root, use
  `["."]`. Leave empty only when no `package.json` with a `test` script exists.

## Step 2: Ask (only the ambiguous)

Ask only what detection could not settle. Offer the detected value as default.

1. **Linear integration** — `enabled` or `disabled`. Default `enabled` when a
   Linear identity source was detected; offer `disabled` for a pure-BMAD repo.
2. **Epic PR strategy** — profile version 1 supports `single-pr-at-end` only
   because epic mode uses one shared epic branch. Tell the user a true
   per-story epic PR strategy requires per-story branches and is not supported
   by this profile version.
3. **Confirm conventions** — show the detected `branch.*` templates and
   `commit.message_format` and let the user override. Defaults:
   `story/{STORY_KEY}`, `epic-{EPIC_NUM}/{epic-slug}`,
   `feat(epic-{EPIC_NUM}): {story_title} ({LINEAR_ID} / Story {STORY_KEY})`.
4. **Inline Linear identity** — only when `identity_source: inline`: ask for
   `team` and `id_prefix` (verify the team via the Linear MCP `list_teams` when
   available).

## Step 3: Validate, write, confirm

- Validate the assembled profile against `config/profile-schema.yaml`
  (required keys present; values within `allowed_values`).
- Write `.agents/skills/vixxo-bmad-swarm/local/profile.yaml` with
  `profile_kind: local`.
- Echo the generated profile back to the user, confirm it is correct, then
  proceed with the original swarm run.

## Generated profile template

Write this (substituting detected/answered values), omitting
`linear.inline_identity` when `identity_source: linear-issue-creator`:

```yaml
profile_schema_version: 1
profile_name: <repo-or-team-name>
profile_kind: local

linear_integration: <enabled | disabled>

linear:
  identity_source: <linear-issue-creator | inline>
  # inline_identity only when identity_source: inline
  inline_identity:
    team: <TEAM_KEY>
    project: <PROJECT_NAME>
    id_prefix: <PREFIX>

bmad:
  config_path: <_bmad/bmm/config.yaml>
  skills_dir: <.agents/skills>

branch:
  single_template: "story/{STORY_KEY}"
  epic_template: "epic-{EPIC_NUM}/{epic-slug}"

commit:
  message_format: "feat(epic-{EPIC_NUM}): {story_title} ({LINEAR_ID} / Story {STORY_KEY})"
  co_authored_by: "<optional trailer or empty>"

changelog:
  enabled: <true | false>
  dir: ".changelog"
  rule_ref: "<optional rule path or empty>"

pr:
  base_branch: <detected default branch>
  tool: <detected tool, e.g. "gh", or empty if none was detected>
  epic_strategy: single-pr-at-end

review:
  run_bmad_adversarial_review: true
  bugbot_enabled: true
  security_trigger_globs: [ ... ]

workspace_dirs: [ <detected dirs with package.json + test script, e.g. "backend", "frontend"> ]

linear_tooling:
  mcp: true
  update_cli: "<optional fallback script or empty>"

rule_refs:
  kickoff: "<optional or empty>"
  lifecycle: "<optional or empty>"
```

The same detection-first flow works in any consuming repo; nothing here is
repo-specific.
