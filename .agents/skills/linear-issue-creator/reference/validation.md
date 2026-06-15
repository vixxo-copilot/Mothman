# Profile and Gate Validation

The active profile is the source of repo-specific truth. Agent memory, examples,
or habits from another repo must not override it.

## Required Profile Fields

A valid creation profile declares:

- `profile_schema_version`
- `profile_name`
- `linear.team`
- `business_owner.label_group`
- `business_owner.policy`
- `assignee.policy`
- `work_type_labels`
- `confirmation.required`
- `duplicate_check.enabled`

The allowed Work Type labels are exactly:

```text
Epic
Story
Chore
Bug
```

Profiles may also declare:

- `linear.project` (omit when routing team/project by content; see
  `reference/routing-maps.md`)
- `business_owner.default_label`
- `business_owner.allowed_labels`
- `assignee.default`
- `labels.required`
- `labels.optional`
- `duplicate_check.search_scope`

## Title and Parent Validation

Every created issue must follow the Linear title convention:

- `Epic` issues: `[Epic N] <title>`
- `Story`, `Chore`, and `Bug` issues: `[N.M] <title>`

For child issues, `N` must match the parent epic number, and the issue must be
attached to that parent epic in Linear.

Numbers must be enumerated from live Linear data, never guessed:

- Epic numbers: query existing `[Epic N]` issues in the profile's team/project
  via `list_issues` and use `max(N) + 1`.
- Child sequence numbers: query the parent epic's children via `list_issues`
  with `parentId` and use the next free `M`.

If the next number is unclear or the Linear MCP is unavailable, ask the user or
use verified Linear context. Do not reuse an existing number.

## Business Owner Policies

`approved-default`
: Use the profile default when the user does not supply a Business Owner. This is
allowed only when ownership is predictable for that repo, such as Bridge.

`explicit-or-current-user`
: Accept an explicit owner or `me` when the current user maps to exactly one
Business Owner label. Otherwise ask.

`explicit-only`
: Require the user to supply the Business Owner label for every issue.

## Assignee Policies

`default-assignee`
: Assign new issues to the configured profile assignee.

`ask`
: Ask who should own delivery or triage before creation.

`unassigned-triage`
: Leave unassigned only because the profile explicitly says the team/project uses
unassigned triage.

## Blocking Conditions

Block issue creation when:

- no repo-local profile exists and the user has declined the first-run
  configuration interview (otherwise run the interview to create one)
- Business Owner cannot be resolved to exactly one Linear label
- Work Type is missing, ambiguous, or has more than one selected label
- title does not follow `[Epic N]` or `[N.M]` numbering
- non-epic issue has no verified parent epic relationship
- team or project cannot be verified
- required labels cannot be verified
- assignee policy requires an assignee and none is resolved
- Linear MCP verification fails for a required value
- the user has not confirmed the draft

## Non-Blocking Conditions

Possible duplicates are not automatically blocking. They become part of the
draft, and the user may explicitly choose to create anyway.
