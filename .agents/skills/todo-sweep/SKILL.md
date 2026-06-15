---
name: todo-sweep
description: >-
  Scans unswept meeting action items, presents them for approval, routes
  approved work to user-linear or user-benji, and marks meetings as swept.
---

# Todo Sweep

## When to use

Use this skill when the user asks to:

- sweep todos from meeting notes
- process meeting action items
- check for unrouted tasks from recent meetings

## Step 1: discover unswept meetings

1. List `memory/meetings/*/meeting.md` (exclude `_template` folders).
2. Read frontmatter and filter where `todos_swept` is missing, `false`, or `null`.
3. Sort oldest-first by meeting date.
4. If none remain, return "No unswept meetings found."

## Step 2: extract pending action items

For the next unswept meeting:

1. Parse unchecked `- [ ]` lines under `## Action Items`.
2. Cross-check frontmatter `action_items` and include unique missing lines.
3. Parse owner, todo text, and optional due-date hints.
4. If no open actions remain, mark `todos_swept: true` and continue.

## Step 3: routing defaults

- Owner is not the current user -> default action: **Skip / Waiting**
- Team-visible work -> default route: `user-linear`
- Individual follow-up -> default route: `user-benji`

These are defaults only; the user can override row-by-row before creation.

## Step 4: review table and approval

Show a concise table with:

- row number
- owner
- todo text
- proposed route
- action status

Ask for edits or "approve all" before creating any task.

## Step 5: execute approved creates

- Create approved Benji tasks through `user-benji`.
- Create approved Linear issues through `user-linear`.
- If Linear is unavailable, fall back to Benji and note it.
- Keep skipped/waiting rows as non-created items.

## Step 6: mark meeting swept

After execution:

1. Set `todos_swept: true` in meeting frontmatter.
2. Update `updated` to today.
3. Leave body checkboxes unchanged for historical traceability.

## Guardrails

- No auto-creation without explicit approval.
- Process one meeting at a time, oldest-first.
- Keep outputs compact and avoid raw MCP payload dumps.
- Keep source traceability in task descriptions (meeting title/date and original action text).
