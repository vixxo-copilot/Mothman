# Linear MCP Verification

Use the Linear MCP as the source of truth for teams, projects, labels, users, and
issue creation.

## Tool Schema Rule

Before calling any MCP tool, inspect the tool descriptor/schema exposed in the
current environment. Do not guess parameters.

## Values to Verify

Verify these values before creation whenever Linear MCP access is available:

- selected Linear team
- selected Linear project
- Business Owner label group and selected Business Owner label
- Work Type labels: `Epic`, `Story`, `Chore`, `Bug`
- parent epic issue for non-epic work types
- required labels from the active profile
- assignee, when the profile policy requires one

If verification fails for a required value, stop. Return the value that failed
and the profile field or user input that needs correction.

## Enumerating Epic and Child Numbers

Before proposing any `[Epic N]` or `[N.M]` number, enumerate what already exists
so numbers never collide. Use the MCP list/search tool (e.g. `list_issues`)
scoped to the profile values:

- **Next epic number:** `list_issues` with the profile `team` (and `project`
  when fixed) plus `query: "[Epic"` and/or `label: "Epic"`. Parse the `[Epic N]`
  prefixes from the returned titles and propose `max(N) + 1`. Page through
  results (`cursor`) if the team has many epics.
- **Next child sequence:** `list_issues` with `parentId` set to the resolved
  parent epic. Parse the `[N.M]` prefixes and propose the next free `M`.

Inspect the tool schema first; filter names vary by environment. If the tool is
unavailable, ask the user for the number rather than guessing.

## Creation Expectations

Create with the Linear MCP tool that supports rich issue creation in the current
environment. The creation payload should include:

- title
- description
- team
- project
- parent epic relationship for `Story`, `Chore`, and `Bug`
- labels including Business Owner and exactly one Work Type
- assignee when required by profile policy

Do not invent IDs, labels, projects, teams, parent issues, users, or email
addresses. Ask or stop when the MCP cannot verify a required value.

## Label Preservation

When a profile includes required labels, include them alongside Business Owner
and Work Type labels. Do not let Work Type replace category, routing, or
Business Owner labels.
