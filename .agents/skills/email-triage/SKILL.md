---
name: email-triage
description: >-
  Runs a Microsoft 365 inbox triage workflow that prioritizes actionable mail,
  batches response drafting, and captures follow-up work items from Outlook
  message threads.
---

# Email Triage (M365)

## When to use

Use this skill when the user asks to:

- triage Outlook mail quickly
- decide what to reply to first
- batch responses for similar threads
- capture follow-up actions from message content

## Output format

Return triage results with these sections:

1. **Priority queue** (`urgent`, `today`, `this-week`, `delegate`, `archive`)
2. **Reply batch** (draft-ready responses grouped by tone and urgency)
3. **Follow-up capture** (tasks, owners, due dates, blockers)
4. **Unresolved questions** (missing context needed before sending)

## Workflow

1. Confirm triage scope: mailbox/folder, time window, and priority signals.
2. Pull candidate messages from Microsoft 365 tooling only:
   - Outlook mail folders and message metadata
   - Graph-backed query tools for search/filter/sort
3. Prioritize by urgency, sender role, due-date signals, and dependency risk.
4. Group messages that need similar responses and draft a reply batch.
5. Extract discrete follow-up actions from each handled thread.
6. Return the output format with clear next actions and owners.

## M365 query guidance

- Do not combine `$search` and `$filter` in a single message query.
- If both are needed, run sequential passes (search first, then filter/expand).
- Keep `$search` expressions double-quoted per Graph query requirements.
- Prefer `$select` and modest page sizes, then continue with paging links.
- Resolve recipients through directory tools rather than inventing addresses.

## Guardrails

- Use facts from message content; mark assumptions clearly.
- Keep response drafts concise and ready to send after quick user review.
- Flag missing approvals, dependencies, or ambiguous asks before drafting.
- Keep triage output scoped to work context in Microsoft 365.
