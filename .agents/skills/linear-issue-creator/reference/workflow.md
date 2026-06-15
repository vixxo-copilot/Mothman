# Linear Issue Creator Workflow

This skill gets work into Linear through one governed path. It supports four
modes: **single**, **bulk**, **business request decomposition**, and
**update / triage**. All creation modes pass the same Non-Negotiable Gates from
`SKILL.md`, including the intake-readiness bar (`reference/intake-readiness.md`).

## 0. Detect Mode

| Signal | Mode |
|---|---|
| One issue to create | Single |
| A numbered/bulleted list, table, or several distinct items | Bulk |
| A forwarded email / SOW / multi-team initiative with several workstreams | Business Request Decomposition |
| An existing issue identifier with a change instruction | Update / triage |

## 1. Load Profile (or run first-run setup)

Load the active repo-local profile from:

```text
.agents/skills/linear-issue-creator/local/profile.yaml
```

If no profile exists, **run the first-run configuration interview**
(`reference/onboarding.md`): ask the generic setup questions, validate against
`config/profile-schema.yaml`, write `local/profile.yaml` (`profile_kind: local`),
confirm it with the user, then continue. Do not fall back to another repo's
example profile, and do not create issues from an unconfigured repo. Stop only
if the user declines to configure.

## Single Mode

### 2. Parse Request

Extract a creation envelope: title, description, Business Owner (if supplied),
Work Type (if supplied), parent epic (unless Work Type is `Epic`), team/project
(profile, routing, or override), assignee (profile or override), and optional
category/routing labels. If title or description is missing, ask one concise
clarification.

### 3. Resolve Business Owner

Order: (1) explicit owner; (2) `me` when it maps to exactly one Business Owner
label; (3) approved profile default when policy is `approved-default`; (4) ask.
Fail closed — never create with `TBD`, `Unassigned`, `Needs Business Owner`, or
a guessed person.

### 4. Resolve Work Type

Exactly one of `Epic`, `Story`, `Chore`, `Bug`. If ambiguous, ask.

### 5. Resolve Epic Hierarchy and Title Numbering

Enumerate before numbering — never guess. Numbers come from live Linear data
scoped to the profile's team/project.

`Epic`: call `list_issues` for the profile team (and project when fixed) with
`query: "[Epic"` (and/or the `Epic` Work Type label), parse existing `[Epic N]`
titles, and propose `max(N) + 1`. Title `[Epic N] <title>`. Surface the existing
epics in the draft so the user can confirm there is no collision.

`Story`/`Chore`/`Bug`: resolve and verify the parent epic, then call
`list_issues` with `parentId` = the epic to find existing `[N.M]` children and
propose the next `M`. Title `[N.M] <title>`, attach to the parent. Do not create
an unparented non-epic issue.

If the Linear MCP is unavailable, ask the user for the number rather than
guessing. See `reference/linear-mcp.md` for the enumeration filters.

### 6. Resolve Team, Project, and Assignee

Use the profile. If the team/project is not fixed and the workspace is Vixxo,
route by content using `reference/routing-maps.md`; present options when
ambiguous. Apply assignee policy (`default-assignee` / `ask` /
`unassigned-triage`) separately from Business Owner.

### 7. Satisfy the Intake-Readiness Bar

Build the description from the Work Type template in
`reference/intake-readiness.md`. Score **PASS** or **NEEDS INPUT**. If fields are
missing from the source, ask for them before drafting.

### 8. Verify Through Linear MCP

Inspect the MCP tool descriptor/schema first. Verify team, project, Business
Owner label, Work Type label, parent epic (non-epic), assignee (when required),
and required labels. If a required value cannot be verified, stop with a
specific remediation message.

### 9. Duplicate Check

Search likely duplicates in scope (`reference/duplicate-check.md`). Include any
in the draft; require explicit create-anyway confirmation.

### 10. Draft Confirmation

Present the draft (title, description summary, parent epic, team/project,
Business Owner, Work Type, assignee, labels, readiness, possible duplicates).
Ask for explicit confirmation. Silence is not permission.

### 11. Create

Create through Linear MCP only after confirmation. Return identifier, URL,
parent epic relationship, Business Owner and Work Type applied, and any overridden
duplicate warning. For Vixxo items, pair the Linear URL with the Bridge URL.

## Bulk Mode

1. Parse each list item into its own envelope (title, description, routing hints).
2. Resolve Business Owner and Work Type **per item**.
3. Resolve epic hierarchy and title numbering **per item in batch order** —
   enumerate before numbering (same rules as Single Mode step 5: call
   `list_issues` for epics or `parentId` children; never guess `[Epic N]` or
   `[N.M]`). Numbers already assigned to earlier items in this batch count as
   occupied within the same scope (team/project for epics; parent epic for
   `[N.M]` children).
4. Resolve team/project, assignee, and readiness **per item**. Terse items are
   fine if they still satisfy their Work Type's readiness checklist; otherwise
   mark `NEEDS INPUT`.
5. Run duplicate checks for all items and present a single summary table with a
   `Readiness` column and any duplicate flags.
6. Confirm once for the batch. Items marked `NEEDS INPUT` must be resolved or
   explicitly accepted before creation.
7. Create sequentially, reporting each identifier. If one fails, report it and
   continue with the rest.
8. Present a final summary table with identifiers and links.

## Business Request Decomposition Mode

Builds a two-sided structure: a business-visible request (Side 1) plus IT
execution work (Side 2).

### Extract the envelope

Requester and role, stakeholders, hard deadlines, business context (SOW summary,
customer, scope), systems mentioned (drive per-story routing), and any decisions
already made.

### Decompose into stories

One story per distinct concern/workstream, each independently actionable by one
team, in imperative mood, with what/why/acceptance criteria that satisfy the
Story readiness checklist. Route each story to its team via
`reference/routing-maps.md`; collect the full set of teams for the project.

### Resolve epic hierarchy and title numbering

Enumerate before numbering (same rules as Single Mode step 5: call `list_issues`
for the profile team (and project when fixed) with `query: "[Epic"` (and/or the
`Epic` Work Type label), parse existing `[Epic N]` titles, and propose
`max(N) + 1`; never guess). Number routed stories `[N.M]` in decomposition order
(`M` starts at 1 for a new epic). Surface existing epics in the draft so the
user can confirm there is no collision.

### Build the draft (present both sides, then confirm)

- **Side 1 — Business Request item:** team IT Business Requests, project Business
  Requests, labels include the permanent `Business Request` label, unassigned
  unless the user names an owner, deadline if present.
- **Side 2 — project + epic + stories:** a new multi-team project (or an existing
  one if the user says so), an epic (neutral IT Business Requests team by
  default, unassigned), and the routed stories. Stories do **not** get the
  `Business Request` label.

### Create in order

1. Create the project (`save_project` with `addTeams`).
2. Create the epic (`save_issue`, enumerated `[Epic N]` title, in the project).
3. Create each story (`save_issue`, `parentId` = epic, per-story team).
4. Create the Business Request item (`save_issue`, `relatedTo` = epic).
5. Add an audit comment on the Business Request item summarizing the project,
   epic, and story count.
6. Present a final summary with all identifiers and Bridge + Linear links.

## Update / Triage Mode

For changes to an issue this workflow created:

1. Fetch current state via the Linear MCP get tool.
2. Update via the MCP update tool with only the changing fields.
3. Add an audit comment for every **material** change — status, priority
   escalation/de-escalation, re-assignment, project/team transfer, duplicate
   marking, or a triage-affecting label change. Prefix `[Agent]`, state old ->
   new and why.
4. When promoting a business request out of the intake queue to a team project,
   change the project (and team/assignee if directed) but **never** remove the
   `Business Request` label.
5. Do not add audit comments for initial creation or non-material metadata
   (estimates, due dates, links).
