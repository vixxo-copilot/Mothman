# Linear Issue Creator

Reusable Cursor skill for getting work into Linear through the Vixxo IT standard
path. It is the single front door for Linear issue creation and **supersedes the
older `linear-issue-manager` skill**.

It handles four modes:

- **Single** — create one issue.
- **Bulk** — create many issues from a list.
- **Business Request Decomposition** — turn a forwarded email / SOW / multi-team
  initiative into a Business Request item plus an epic and routed stories.
- **Update / triage** — status, priority, label, and promotion changes (with
  audit comments) for issues it created.

The skill enforces, for every issue it creates:

- Business Owner required before creation.
- Exactly one Work Type label: `Epic`, `Story`, `Chore`, or `Bug`.
- Epic numbering in titles: `[Epic N]` for epics and `[N.M]` for child issues.
- Every non-epic issue must be attached to its parent epic.
- Team/project/profile validation, with content-based routing for Vixxo
  workspaces (`reference/routing-maps.md`).
- An **intake-readiness bar** so issues pass the `intake-audit:v1` check instead
  of bouncing to "Needs Clarification" (`reference/intake-readiness.md`).
- Linear MCP verification for required metadata.
- Lightweight duplicate check.
- Draft confirmation before creation.

## Install in a Repo

Install the skill from `vixxo-copilot/agent-skills` using the normal skills
distribution flow for your agent environment.

You do **not** have to hand-write any config. The first time you ask the skill
to create a Linear issue in a repo with no profile, it runs a short
**configuration interview** (team, project, Business Owner policy, assignee
policy, duplicate scope, optional labels), then writes
`.agents/skills/linear-issue-creator/local/profile.yaml` for you. See
`reference/onboarding.md`. This is how every IT repo configures the shared
skill for its own Linear team — answers stay in the gitignored local profile.

If you prefer to write the profile by hand, start from one of the shipped
examples and copy it to `local/profile.yaml`:

- `config/example.profile.yaml` — generic template.
- `config/bridge.profile.yaml` — Bridge example with approved Bobby defaults.
- `config/vixxo-explicit-owner.profile.yaml` — Vixxo/VixxoLink-style profile
  where Business Owner varies and must be explicit or resolved.

## What Teams Customize

Only customize the repo-local profile. Do not edit the managed skill workflow
unless you are changing the shared upstream skill.

Customize:

- `linear.team`
- `linear.project`
- `business_owner.policy`
- `business_owner.default_label`, only if ownership is predictable and approved
- `business_owner.allowed_labels`
- `assignee.policy`
- `assignee.default`
- `labels.required`
- `labels.optional`
- `duplicate_check.search_scope`

Do not customize the core gates:

- Business Owner is mandatory.
- Work Type must be exactly one of `Epic`, `Story`, `Chore`, `Bug`.
- Epics must be titled `[Epic N] <title>`.
- Child issues must be titled `[N.M] <title>` and attached to the matching
  parent epic.
- Required Linear metadata must verify through Linear MCP when available.
- Draft confirmation is required before creation.

## Business Owner Policy Examples

Bridge can use:

```yaml
business_owner:
  label_group: "Business Owner"
  policy: approved-default
  default_label: "Robert Hunnicutt"
```

Repos with varied business owners should use:

```yaml
business_owner:
  label_group: "Business Owner"
  policy: explicit-or-current-user
  default_label: ""
```

This lets `me` resolve when the current user maps cleanly to a Linear Business
Owner label, but otherwise forces the agent to ask.

## Assignee Is Separate

Business Owner answers: "Who owns the business outcome and approval context?"

Assignee answers: "Who owns delivery or triage?"

These may be the same person in Bridge, but they should not be assumed to be the
same person in repos like Vixxo or VixxoLink.

## Epic Numbering Convention

Use the title pattern that is easiest to scan in Linear:

```text
[Epic 60] Bridge Agent MCP Server
[60.1] User access tokens and agent auth
[60.2] Hosted Bridge MCP server and Slack lookup tool
```

When creating an `Epic`, the agent must resolve the epic number and format the
title as `[Epic N] <title>`.

When creating a `Story`, `Chore`, or `Bug`, the agent must resolve the parent
epic, attach the issue to that epic, and format the title as `[N.M] <title>`.
If the parent epic or child sequence number is unclear, the agent asks before
creating anything.

## Safe Upgrade Model

This skill is designed as a versioned shared core plus repo-local profile.

When updating from upstream:

1. Replace the managed skill files from `vixxo-copilot/agent-skills`.
2. Preserve the consuming repo's local profile at
   `.agents/skills/linear-issue-creator/local/profile.yaml`.
3. Review `config/profile-schema.yaml` for schema changes.
4. Validate the local profile if validation tooling is available.
5. Run a dry draft in Cursor before creating live issues.

If a team needs behavior the profile cannot express, propose the behavior
upstream instead of patching the local skill core.

## Optional Validation

This repository includes a lightweight validator for profile files:

```bash
node scripts/validate-linear-issue-creator-profile.mjs \
  skills/linear-issue-creator/config/bridge.profile.yaml
```

Use the validator against a consuming repo's local profile after install or
upgrade.
