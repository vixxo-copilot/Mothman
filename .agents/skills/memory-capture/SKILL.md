---
name: memory-capture
description: >-
  Captures notes, decisions, people updates, and meeting records into the
  memory vault with inbox-first routing for ambiguous thoughts.
---

# Memory Capture

## When to use

Use this skill when the user asks to:

- remember something for later
- save a quick thought without immediate action
- log a decision, meeting note, or person update
- store context for future planning

## Capture types

Classify each request into one type:

- **New Person** -> create `memory/people/{slug}.md`
- **Person Update** -> append to an existing person file
- **New Meeting** -> create `memory/meetings/{YYYY-MM-DD-slug}/meeting.md`
- **New Decision** -> create `memory/decisions/{slug}.md`
- **Reference** -> create or update `memory/reference/{slug}.md`
- **Quick Capture / General Note** -> create `memory/inbox/{YYYY-MM-DD-slug}.md`

## Inbox-first rule

If destination is ambiguous, default to `memory/inbox/` using `memory/inbox/_template.md`.
Do not block capture with long follow-up questions unless writing to a specific structured file could overwrite the wrong destination.

## Workflow

1. Determine capture type from the user request.
2. Read the matching template before writing:
   - `memory/people/_template.md`
   - `memory/meetings/_template.md`
   - `memory/decisions/_template.md`
   - `memory/reference/_template.md`
   - `memory/inbox/_template.md`
3. Preserve provided facts and keep unknown fields empty without filler text.
4. Update `updated` on templates that include it.
5. Confirm the saved file path with a short summary of captured content.

## File naming conventions

- People: `{first-last}.md`
- Meetings: `{YYYY-MM-DD-title}/meeting.md`
- Decisions: `{descriptive-title}.md`
- Reference: `{descriptive-slug}.md`
- Inbox: `{YYYY-MM-DD-slug}.md`

## Guardrails

- Never overwrite existing content silently; append or ask before destructive edits.
- Keep YAML arrays valid (`[]` or inline list format).
- Keep dates in `YYYY-MM-DD`.
- Do not include machine-local absolute paths or private repo references.
