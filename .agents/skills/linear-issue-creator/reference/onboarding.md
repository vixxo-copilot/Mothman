# First-Run Configuration Interview

When a repo has no active profile at
`.agents/skills/linear-issue-creator/local/profile.yaml`, do not fail. Run this
short, generic interview, then write the profile and continue. The same
questions work in any consuming repo — nothing here is repo-specific.

## When to run

- The user asks to create / log / file a Linear issue, and
- `.agents/skills/linear-issue-creator/local/profile.yaml` does not exist.

Run the interview once, write the profile, confirm it, then proceed with the
original request. On later runs the profile already exists, so the interview is
skipped.

## Questions

Ask these in order. Use multiple-choice prompts for the policy/scope fields and
free text (verified through the Linear MCP) for team/project/labels. Keep it to
one pass; offer sensible defaults but never invent a team, project, owner, or
assignee.

1. **Linear team** — key or name (e.g. `BRG`). Verify it resolves via
   `list_teams`. Stored as `linear.team`.
2. **Default project** — a specific project name, or `route by content` for
   Vixxo workspaces that route per item. Verify a named project via
   `list_projects`. Stored as `linear.project` (omit when routing by content).
3. **Business Owner policy** — one of:
   - `approved-default` — predictable owner for this repo. Also ask for
     `default_label` (the exact Linear Business Owner label) and optionally
     `allowed_labels`.
   - `explicit-or-current-user` — accept an explicit owner or `me` when the
     current user maps to exactly one Business Owner label.
   - `explicit-only` — require an explicit owner on every issue.
   Stored under `business_owner`.
4. **Assignee policy** — one of:
   - `default-assignee` — also ask for `assignee.default` (the delivery/triage
     owner).
   - `ask` — ask who owns delivery before each creation.
   - `unassigned-triage` — leave unassigned because the team uses unassigned
     triage.
   Stored under `assignee`.
5. **Duplicate-check scope** — one of `team-project`, `team`, `workspace`.
   Stored as `duplicate_check.search_scope` (with `duplicate_check.enabled:
   true`).
6. **Labels (optional)** — any `labels.required` that must be on every issue,
   and `labels.optional` the repo commonly uses. Default both to empty/common
   sets if the user has no preference.

Work Type labels are fixed (`Epic`, `Story`, `Chore`, `Bug`) and are written
automatically — do not ask.

## Validation

Validate every answer against `config/profile-schema.yaml`:

- `business_owner.policy` ∈ {`approved-default`, `explicit-or-current-user`,
  `explicit-only`}; `approved-default` requires `business_owner.default_label`.
- `assignee.policy` ∈ {`default-assignee`, `ask`, `unassigned-triage`};
  `default-assignee` requires `assignee.default`.
- `duplicate_check.search_scope` ∈ {`team-project`, `team`, `workspace`};
  `team-project` requires `linear.project` (use `team` or `workspace` when routing
  by content).
- `work_type_labels` is exactly `[Epic, Story, Chore, Bug]`.

Re-ask any field that fails validation.

## Generated profile template

Write this to `.agents/skills/linear-issue-creator/local/profile.yaml`,
substituting the answers. Use `profile_kind: local` so it reads as an active
profile (not an example). Omit `linear.project` when the user chose
route-by-content.

```yaml
profile_schema_version: 1
profile_name: <repo-or-team-name>
profile_kind: local

linear:
  team: <TEAM_KEY_OR_NAME>
  project: <PROJECT_NAME>   # omit if routing by content

business_owner:
  label_group: "Business Owner"
  policy: <approved-default | explicit-or-current-user | explicit-only>
  default_label: "<EXACT_LABEL_OR_EMPTY>"
  allowed_labels:
    - "<LABEL>"

assignee:
  policy: <default-assignee | ask | unassigned-triage>
  default: "<USER_OR_EMPTY>"

work_type_labels:
  - Epic
  - Story
  - Chore
  - Bug

labels:
  required: []
  optional: []

duplicate_check:
  enabled: true
  search_scope: <team-project | team | workspace>

confirmation:
  required: true
```

## Confirm and proceed

Echo the generated profile back to the user, confirm it is correct, then
continue with the original creation request. If a profile validator is available
(see `README.md`), run it against the new `local/profile.yaml` before first use.
