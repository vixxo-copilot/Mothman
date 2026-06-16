# BMAD Sprint-Status Mirror

This optional contract lets `linear-issue-creator` feed `vixxo-bmad-swarm` without
merging the two skills. Linear remains the system of record; the BMAD
`sprint-status.yaml` row is only a local execution mirror.

Use this contract only when the issue is **swarm-bound**: the user asks to turn a
plan/session/story into Linear work that the BMAD swarm should later execute, or
the swarm invokes `linear-issue-creator` to backfill a missing Linear issue.

## Mirror Row Shape

Write or update one `development_status` entry in
`{implementation_artifacts}/sprint-status.yaml`:

```yaml
<story_key>:
  status: backlog
  linear_id: "<TEAM-123>"
  linear_url: "https://linear.app/.../<TEAM-123>/..."
  context_source: linear-issue
  last_updated: "YYYY-MM-DD"
```

For BMAD-planned stories that already have a matching epic/story entry, use:

```yaml
context_source: bmad-epic
```

`context_source` is the discriminator the swarm uses in Phase 1:

- `bmad-epic` -> read BMAD planning artifacts (`epics-and-stories.md` or
  per-epic files) as the story source.
- `linear-issue` -> fetch the Linear issue body by `linear_id` and use that as
  the story source.

## Story Key Mapping

Resolve `story_key` from the created issue's `[N.M]` title:

1. Parse `N` and `M` from the title (`[N.M] ...`).
2. If `sprint-status.yaml` already has exactly one `development_status` key matching
   `{N}-{M}-*`, use that key (BMAD-planned rows often use a different slug than the
   Linear title). Preserve existing `context_source` (typically `bmad-epic`) and
   `status` on that row.
3. If no such row exists, derive the key from the title slug:

- `[N.M] Some Title` -> `N-M-some-title`
- `[Epic N] Some Epic` -> `epic-N` for epic tracking rows

Slug rules:

- Lowercase.
- Replace non-alphanumeric runs with `-`.
- Trim leading/trailing `-`.
- Treat the Linear ID as the stable external identifier; the slug is cosmetic
  and may drift if the title changes.

Insert under the matching epic section when one exists. If no matching section
exists, append under an "unplanned / intake" section at the end of
`development_status:`.

## Update Rules

- Update only the one `development_status` entry for the story and the top-level
  `last_updated` date.
- Preserve existing comments and formatting as much as practical.
- Do **not** add dated journal/comment blocks such as `# YYYY-MM-DD: ...`
  anywhere in `sprint-status.yaml`.
- Never remove existing `linear_id`, `linear_url`, or `context_source` fields
  unless replacing them with verified current values.

## Autonomous Swarm Invocation

When `vixxo-bmad-swarm` invokes this skill to backfill a missing Linear issue, creation
may proceed without a separate user confirmation only when all of these are
true:

- the request includes an explicit autonomous swarm-create instruction;
- Business Owner resolves from the active profile (or explicit input);
- Work Type resolves deterministically;
- parent epic and numbering resolve through Linear;
- readiness is PASS;
- duplicate check finds no likely duplicates;
- all required Linear metadata verifies through MCP.

If any condition fails, stop and return the blocker to the swarm. Do not create
a low-quality or ambiguous issue.
