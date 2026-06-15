---
name: linear-issue-creator
description: >
  The governed path for getting work into Linear from Cursor. Use this skill
  whenever a user asks Cursor to create, file, open, log, or draft Linear
  issues -- a single issue, a bulk list, or a multi-team business request that
  must be decomposed into an epic plus stories. It blocks ownerless or untyped
  issues, holds every issue to an intake-readiness bar, verifies Linear
  metadata, checks for duplicates, shows a draft, and creates only after
  explicit confirmation. It also covers triage updates and audit comments for
  issues it created. Supersedes the older linear-issue-manager skill.
---

# Linear Issue Creator

Get work into Linear through a governed workflow that keeps Vixxo IT issues
routable, approvable, reportable, and ready for execution.

This skill exists to prevent inconsistent Cursor-created Linear issues. Every
issue it creates carries a Business Owner, exactly one Work Type, correct epic
numbering, and enough context to clear the intake-readiness bar before it lands
in a backlog.

It is repo-portable: a small repo-local **profile** supplies the team, project,
ownership, and assignee defaults, while the shared skill core supplies the gates,
modes, routing knowledge, and readiness rubric.

## When to Use

Use this skill whenever the user asks to:

- create a Linear issue (bug, story, chore, or epic)
- log something in Linear, or turn a note, Teams message, email, or request
  into a ticket
- create **many** issues at once from a list (bulk intake)
- decompose a **business request** (forwarded email, SOW, cross-team initiative)
  into a Business Request item plus an epic and routed stories
- triage or update an issue this workflow created (status, priority, labels,
  promotion from intake to a team project)

This is the single front door for Linear issue creation. There is no separate
"manager" skill -- this skill absorbed it.

## Required Local Profile

Before creating anything, load the repo-local profile. The active profile lives
at:

```text
.agents/skills/linear-issue-creator/local/profile.yaml
```

If that file does not exist, **run the first-run configuration interview**
(see `reference/onboarding.md`) instead of failing: ask the user the short,
generic set of setup questions, write a schema-valid `local/profile.yaml` from
their answers, confirm it, and then continue. Only stop if the user declines to
configure. Do not create issues from an unconfigured repo, and do not rely on
agent memory for team, project, ownership, or assignee values.

The profile controls repo-specific defaults: Linear team, project, Business
Owner policy, assignee policy, allowed labels, and duplicate search scope. Every
consuming repo supplies its own values — the skill core never hardcodes one
repo's team, project, or owner. The shipped `config/*.profile.yaml` files are
**examples** to copy or to seed interview answers, not active profiles.

### First-Run Configuration Interview

When `local/profile.yaml` is missing, configure the repo interactively before
the first creation (full question set, allowed answers, and the generated
template are in `reference/onboarding.md`):

1. Linear **team** (key or name) — verify via the Linear MCP `list_teams`.
2. Default **project** (a specific project, or "route by content" for Vixxo
   workspaces) — verify via `list_projects` when a project is named.
3. **Business Owner** policy: `approved-default`, `explicit-or-current-user`, or
   `explicit-only` (plus `default_label` / `allowed_labels` when
   `approved-default`).
4. **Assignee** policy: `default-assignee`, `ask`, or `unassigned-triage` (plus
   `default` when `default-assignee`).
5. **Duplicate-check** scope: `team-project`, `team`, or `workspace`.
6. Optional required/optional labels.

Validate answers against `config/profile-schema.yaml`, write
`local/profile.yaml` with `profile_kind: local`, echo it back, and only then
proceed. The interview is generic: the same questions work in any repo.

## Non-Negotiable Gates

Never create a Linear issue unless all gates pass. These apply to every mode
(single, bulk, and decomposition stories):

1. **Business Owner resolved.** Exactly one valid Linear `Business Owner` label.
   If not, ask. If still unresolved, stop. (See Resolution Rules.)
2. **Work Type resolved.** Exactly one `Work Type` label: `Epic`, `Story`,
   `Chore`, or `Bug`.
3. **Epic hierarchy and title numbering resolved.** Epics use `[Epic N] <title>`.
   Non-epic issues attach to a parent epic and use `[N.M] <title>`.
4. **Team and project resolved.** From the profile, routing (see Routing), or an
   explicit user override that verifies through Linear.
5. **Assignee policy applied.** Assignee (delivery/triage owner) is separate from
   Business Owner (accountable business stakeholder).
6. **Intake-readiness bar cleared.** The description must satisfy the readiness
   checklist for its Work Type so it passes the automated `intake-audit:v1`
   check and never bounces to a "Needs Clarification" state. See
   `reference/intake-readiness.md`.
7. **Linear metadata verified.** Verify team, project, Business Owner label, Work
   Type label, parent epic, and required labels through the Linear MCP. If a
   required value cannot be verified, stop.
8. **Duplicate check completed.** Search likely duplicates in scope. If found,
   include them in the draft and require explicit create-anyway confirmation.
   See `reference/duplicate-check.md`.
9. **Draft confirmed.** Show the draft and create only after explicit user
   confirmation. Silence or ambiguous approval is not permission.

## Modes

Detect the mode from the user's input, then follow `reference/workflow.md`:

| Signal | Mode |
|---|---|
| One issue to create | **Single** |
| A numbered/bulleted list, table, or several distinct items | **Bulk** |
| A forwarded email / SOW / multi-team initiative with several workstreams | **Business Request Decomposition** |
| An existing issue identifier with a change instruction | **Update / triage** |

In **Decomposition** mode the skill builds a two-sided structure: a Business
Request item (Side 1, the business-visible ask, carries the permanent
`Business Request` label) linked via `relatedTo` to an epic with routed stories
(Side 2, the IT execution work; stories do **not** get the `Business Request`
label). Full procedure in `reference/workflow.md`.

## Resolution Rules

### Business Owner

Resolve in order: (1) explicit owner supplied by the user; (2) `me`, only when
the current user maps cleanly to exactly one Linear Business Owner label;
(3) profile default, only when the profile policy is `approved-default`;
(4) ask for the exact label. Never create with `TBD`, `Unassigned`,
`Needs Business Owner`, or a guessed person. Do not use `Robert Hunnicutt` as a
global fallback -- only the Bridge profile approves that default.

### Work Type

Exactly one of `Epic`, `Story`, `Chore`, `Bug`. Category and routing labels
(`Feature`, `Backend`, `Integration`, `Business Request`, etc.) are separate
metadata and never replace Work Type.

### Epic Hierarchy and Title Numbering

Epics use `[Epic N] <title>`. Stories/Chores/Bugs use `[N.M] <title>`, attached
to the matching parent epic, where `N` is the epic number and `M` is the
sequence within it. Resolve and verify the parent epic before creating a
non-epic issue. Do not create an unparented non-epic issue.

**Always enumerate before numbering — never guess a number.** Numbers must be
derived from live Linear data scoped to the profile's team/project, not from
memory or assumption:

- New **Epic**: call the Linear MCP `list_issues` for the profile's team (and
  project, when fixed) with `query: "[Epic"` (and/or the `Epic` Work Type
  label), parse every existing `[Epic N]` title, and propose `max(N) + 1`. Show
  the existing epics in the draft so the user can confirm there is no collision.
- New **Story/Chore/Bug**: after resolving the parent epic, call `list_issues`
  with `parentId` set to that epic, parse the existing `[N.M]` children, and
  propose the next `M`.
- If the Linear MCP is unavailable, ask the user for the number instead of
  guessing. Never reuse a number that already exists.

See `reference/linear-mcp.md` for the enumeration filters.

### Assignee

Apply the profile policy: `default-assignee` (use the profile assignee), `ask`
(ask before creation), or `unassigned-triage` (leave unassigned only when the
profile allows it). For decomposition, leave the Business Request item and epic
unassigned unless the user names an owner, and route stories to the owning team
(do not auto-assign stories to bobby).

## Intake-Readiness Bar

Every issue must clear the readiness checklist for its Work Type before
creation. Summary (full rubric and templates in `reference/intake-readiness.md`):

- **Bug** requires: ordered steps to reproduce, expected result, actual result,
  and domain identifiers (SR #, order #, customer, environment).
- **Story / Chore / Feature work** requires: a clear problem statement, the
  desired outcome, and identifiers / affected systems (system, customer,
  requester where known).

During the draft step, score each issue **Readiness: PASS** or
**Readiness: NEEDS INPUT** (list the missing fields). If a field is missing from
the source, ask the user to supply it rather than silently creating an issue
that will fail `intake-audit:v1`. Use the matching description template in
`reference/intake-readiness.md`.

## Routing (Vixxo workspaces)

When the profile points at a Vixxo workspace and the target team/project is not
fixed by the profile, route by content using the team, project, and label maps
in `reference/routing-maps.md`. Business requests start in the IT Business
Requests intake queue with the permanent `Business Request` label and are later
promoted to a team project (the label always stays). If routing is ambiguous,
present the top options and let the user choose.

## Workflow

Follow `reference/workflow.md` for the full per-mode procedure. At a minimum, for
any creation: load and validate the profile, parse the request, resolve Business
Owner and Work Type, resolve epic hierarchy, apply assignee policy, satisfy the
readiness bar, inspect Linear MCP tool schemas and verify required metadata, run
the duplicate check, present a draft, and create only after confirmation.

## Updates and Audit Comments

For triage updates to an issue this workflow created (status, priority, labels,
promotion to a team project), use the Linear MCP update tool with only the
changing fields, and add an audit comment for every **material** change
(status, priority escalation/de-escalation, re-assignment, project/team
transfer, duplicate marking, triage-affecting label change). Prefix audit
comments with `[Agent]`, state what changed (old -> new) and why. Do not add
audit comments for initial creation or non-material metadata. When promoting a
business request out of the intake queue, never remove the `Business Request`
label.

## Expected Output

### Single draft

```text
Linear issue draft
- Title: <[Epic N] / [N.M] title>
- Mode: single
- Parent epic: <epic identifier/title or n/a for Epic>
- Team / project: <team> / <project>
- Business Owner: <label>
- Work Type: <Epic|Story|Chore|Bug>
- Assignee: <assignee | unassigned-triage>
- Labels: <labels>
- Readiness: <PASS | NEEDS INPUT: missing ...>
- Possible duplicates: <none | list>

Create this issue?
```

### Bulk draft

Present a table with a `Readiness` column and flag any `NEEDS INPUT` rows before
creating. Confirm once for the batch, then create sequentially and report each
identifier.

### Decomposition draft

Present both sides (Business Request item; new project with teams; epic; routed
stories with per-story team and readiness), then create in order: project ->
epic -> stories -> Business Request item -> link via `relatedTo` -> audit
comment. See `reference/workflow.md`.

After creation, return the Linear identifier(s) and URL(s), the parent epic
relationship where applicable, the Business Owner and Work Type applied, and any
duplicate warning the user overrode. For Vixxo items, pair each Linear URL with
its Bridge URL (`https://bridge.vixxo.com/?item=<ID>` for Business Requests,
`https://bridge.vixxo.com/projects?item=<ID>` otherwise) so non-Linear users can
follow along.

## References

- `README.md` — install, customization, and upgrade guidance.
- `reference/onboarding.md` — first-run configuration interview that writes `local/profile.yaml`.
- `reference/workflow.md` — full per-mode creation flow (single, bulk, decomposition, update).
- `reference/validation.md` — profile and gate validation rules.
- `reference/intake-readiness.md` — the `intake-audit:v1` readiness bar and description templates.
- `reference/routing-maps.md` — Vixxo team / project / label routing maps and IDs.
- `reference/linear-mcp.md` — Linear MCP verification expectations.
- `reference/duplicate-check.md` — duplicate search guidance.
- `config/example.profile.yaml` — copy into each consuming repo and customize.
