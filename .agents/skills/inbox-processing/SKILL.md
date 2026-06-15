---
name: inbox-processing
description: >-
  Triages memory inbox captures, classifies each item, routes work items to
  user-linear or user-benji when approved, and cleans up successfully routed files.
---

# Inbox Processing

## Scope

This skill processes `memory/inbox/*.md` files created by capture workflows.
It classifies each inbox item and routes it to the correct destination inside `memory/` or approved task systems.

## Processing modes

- **Process all**: iterate through all inbox files in filename order
- **Process next**: process one selected item and stop

If mode is unspecified, ask once which mode to use.

## Classification model

Each inbox item must map to exactly one class:

- actionable
- reference
- person-context
- meeting-context
- decision
- trash

Provide a one-line rationale before routing.

## Routing behavior

### actionable

1. Propose the route and ask for approval:
   - `user-linear` for team-visible work
   - `user-benji` for personal follow-up tracking
2. Create the approved item with source context from the inbox file.
3. If MCP calls fail, append a flagged follow-up line to `memory/me/goals.md` and keep processing.

### reference

Create or update `memory/reference/{slug}.md` using the reference template.

### person-context

Create or update `memory/people/{name}.md`, then append to Notes, Action Items, or 1-on-1 History.

### meeting-context

Create or update meeting notes under `memory/meetings/{YYYY-MM-DD-slug}/meeting.md`.

### decision

Create a decision note at `memory/decisions/{slug}.md`.

### trash

Require confirmation before deletion unless the user opted into bulk trash for obvious empty/test captures.

## Cleanup and confirmations

- Delete the source inbox file only after a successful route.
- If routing fails, keep the inbox file and report remediation options.
- End each run with a concise summary listing source file, class, destination, and notes.

## Guardrails

- Keep writes scoped to `memory/` plus approved MCP task creates.
- Never silently drop captures.
- Never paste raw MCP payloads in user-visible output.
- Keep each step idempotent and auditable.
