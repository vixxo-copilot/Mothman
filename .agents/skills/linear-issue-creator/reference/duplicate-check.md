# Duplicate Check

Run a lightweight duplicate check before creating a new Linear issue.

## Search Scope

Use the active profile's duplicate search scope:

- `team-project` searches within the selected team/project.
- `team` searches within the selected team.
- `workspace` searches broadly only when the profile explicitly allows it.

Default to `team-project` when the profile does not specify a scope.

## Search Terms

Search with:

- the proposed title
- two or three distinctive terms from the description
- named systems, customers, or incidents when present

Do not perform a long investigation. This is a creation-time hygiene check, not
a full dedupe project.

## Draft Behavior

If likely duplicates are found, include them in the draft:

```text
Possible duplicates
- VIX-123: Existing title
- BRG-456: Existing title
```

Ask the user to either:

- create anyway
- cancel and use the existing issue
- revise the new issue title/description

Possible duplicates do not block creation by themselves, but the user must
explicitly confirm create-anyway before the Linear MCP create call.
