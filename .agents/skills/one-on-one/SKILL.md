---
name: one-on-one
description: >-
  Prepares one-on-one meeting packets and captures follow-ups into memory files
  with optional Linear task routing for approved action items.
---

# One-on-One

## When to use

Use this skill when the user asks to:

- prep a 1-on-1 agenda
- capture notes after a 1:1
- reconcile open follow-ups for a specific person

## Modes

### Prep mode (default)

1. Resolve the person profile from `memory/people/*.md` (exclude `_template.md`).
2. Summarize open action items and recent 1-on-1 history for the person.
3. Ensure the meeting packet exists at `memory/meetings/{YYYY-MM-DD-person-1-1}/meeting.md`.
4. Ensure packet companions exist in the same folder: `prep.md`, `agenda.md`, `transcript.md`.
5. Write the prep output into `prep.md` and build a tactical `agenda.md`.

### Post-meeting capture mode

1. Append a dated summary block under `## 1-on-1 History` in the person file.
2. Reconcile `## Action Items` checkboxes (mark done, add new open items).
3. Update `updated` and `last_1on1` frontmatter fields.
4. Draft follow-up task titles and request explicit approval before external writes.
5. After approval, route approved work items to Linear when team visibility is needed.

## Output format

Return the result in this order:

1. **Person snapshot** (role/team context and profile path)
2. **Open action items**
3. **Recent 1-on-1 history**
4. **Current work signals**
5. **Suggested discussion prompts**
6. **Prep checklist**

## Linear routing guidance

- Discover tool descriptors before invoking `user-linear` tools.
- Keep list calls bounded (modest limits) and exclude completed items.
- Never create Linear issues without explicit user approval of wording.
- If Linear is unavailable, keep items in vault checklists and note the reason in one line.

## Guardrails

- Do not fabricate people profiles, outcomes, or commitments.
- Do not include raw JSON payloads in user-facing output.
- Keep outputs concise, with short bullets and clear next actions.
- Keep the workflow scoped to work-context systems and memory vault files.
