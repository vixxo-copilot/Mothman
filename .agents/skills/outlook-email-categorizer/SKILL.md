---
name: outlook-email-categorizer
description: >-
  Classifies and applies Outlook categories to Microsoft 365 mail using a
  governed dry-run workflow. Use when the user asks to organize, categorize,
  label, or sort Outlook email, inbox mail, or message threads into categories.
---

# Outlook Email Categorizer (M365)

## When to use

Use this skill when the user asks to:

- organize or categorize Outlook mail
- label inbox messages by type, urgency, or topic
- sort uncategorized email into a category system
- review and apply category assignments in bulk

This skill applies **Outlook categories** (colored labels on messages). It does
not move mail to folders unless the user explicitly asks for folder moves.

## Operating modes

- **Dry-run (default):** classify messages and show a proposed plan. Make no
  mailbox changes.
- **Apply:** after explicit user approval, write categories to messages.

If the user does not specify a mode, run dry-run first.

## Output format

Return results in this order:

1. **Scope** (folder, time window, message count, mode)
2. **Category inventory** (existing Outlook categories used in this run)
3. **Classification plan** grouped by proposed category
4. **Uncertain items** (low-confidence assignments with rationale)
5. **Skipped items** (already categorized, out of scope, or excluded)
6. **Next action** (approval prompt or apply summary)

### Classification plan entry

For each message (or thread), include:

- received time
- sender
- subject
- current categories (if any)
- proposed category (exact `displayName`, case-sensitive)
- confidence (`high` / `medium` / `low`)
- one-line rationale

Keep line width readable. Do not collapse a thread into one vague summary.

## Workflow

### 1. Confirm scope

Ask once if unspecified:

- **Folder:** Inbox (default), or a named folder
- **Time window:** last 24h, 7d, 30d, or custom
- **Volume cap:** default 50 newest messages; raise only if requested
- **Thread behavior:** categorize all Inbox messages sharing a
  `conversationId` consistently (default: yes)
- **Overwrite policy:**
  - `skip-categorized` (default): leave messages that already have categories
  - `replace`: set only the proposed category
  - `append`: add proposed category to existing categories

### 2. Load category rules

1. Read [categories.md](categories.md) for the default taxonomy and signals.
2. Call `list-outlook-categories` to load the user's master category list.
3. Prefer **existing Outlook category names** over creating new ones.
4. Map each rule in `categories.md` to the closest existing category name.
5. If a required category is missing, propose creating it with
   `create-outlook-category` and stop until the user approves creation.

Category names are **case-sensitive** when applied to messages.

### 3. Pull candidate messages

Use Microsoft 365 mail tools only:

- `list-mail-messages` for the default mailbox view
- `list-mail-folder-messages` when a specific folder is requested

Query guidance:

- Do not combine `$search` and `$filter` on one request.
- Wrap `$search` values in double quotes.
- Use a modest page size and paginate with `@odata.nextLink`.
- Recommended select:
  `id,subject,from,toRecipients,receivedDateTime,bodyPreview,categories,conversationId,isRead,importance,hasAttachments`
- Use `bodyPreview` for classification. Call `get-mail-message` only when
  preview text is insufficient for a borderline decision.

### 4. Classify

For each in-scope message:

1. Apply rules from `categories.md` in priority order (top = highest).
2. Use sender domain, subject keywords, body preview, importance, and
   attachment signals.
3. If multiple rules match, choose the highest-priority rule.
4. If confidence is `low`, move the item to **Uncertain items** instead of
   auto-assigning in apply mode.
5. For thread mode, propagate the highest-confidence category across all
   in-scope messages in the same `conversationId`.

Mark assumptions clearly when classification depends on incomplete preview
text.

### 5. Present dry-run plan

Show the full plan grouped by proposed category. End with an explicit approval
prompt:

> Reply **apply** to write these categories, **apply high-confidence only** to
> skip uncertain items, or **revise** with changes.

Do not call `update-mail-message` before approval.

### 6. Apply (approved only)

After explicit approval:

1. Re-fetch each target message's current `categories` when using `append`.
2. Call `update-mail-message` with:

```json
{
  "messageId": "<id>",
  "body": {
    "categories": ["Exact Category Name"]
  }
}
```

3. For `append`, merge unique category names (preserve existing + proposed).
4. For `replace`, send only the proposed category list.
5. Report per-category counts and any failures with the next best action.

Batch updates in small groups. If a call fails, continue the run and report
failures at the end.

## Guardrails

- **Dry-run first** unless the user explicitly says to apply in the same turn.
- **No silent writes.** Category creation and message updates require explicit
  approval.
- **Work context only.** Classify Vixxo work mail; do not process personal or
  out-of-scope mail if the user narrows scope that way.
- **Do not delete or archive** unless the user explicitly requests it.
- **Do not send mail** as part of categorization.
- Resolve organizational senders through directory tools; do not invent SMTP
  addresses.

## Related skills

- `email-triage` — prioritize replies and capture follow-ups from categorized
  or uncategorized mail.
- `daily-briefing` — morning summary after categories clarify what needs action.

## Additional resources

- Default taxonomy and signal rules: [categories.md](categories.md)
