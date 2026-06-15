---
name: check-flagged-emails
description: >-
  Lists and triages Outlook messages the user has flagged in Microsoft 365,
  with Ask/Decision/FYI tags and suggested next actions. Use only when the
  user explicitly asks to check flagged emails, review flagged mail, or show
  flagged messages.
disable-model-invocation: true
---

# Check Flagged Emails

Explicit-invocation skill for flagged Outlook mail in Microsoft 365.

## When to use

Invoke only when the user says:

- "Check flagged emails"
- "Review flagged mail"
- "Show my flagged messages"

## Output format

1. **Summary** — count flagged, unread vs read, attachments
2. **Flagged messages** (newest first) — one block per message:
   - sender, date, subject
   - body summary (asks, dates, names, action items)
   - tag: **Ask** / **Decision** / **FYI**
   - status: **Open** / **Waiting** / **Closed**
   - suggested next action
3. **Priority order** — what to handle first
4. **Draft offers** — reply drafts only if user asks; never send

Keep line width narrow; no wall-of-text.

## Workflow

### 1. Microsoft 365 auth

`verify-login` first. If needed, `login` + wait for user confirmation.

### 2. Query flagged messages

Use `list-mail-messages` (not inbox folder + orderby — that fails on flag
filters):

```
filter: flag/flagStatus eq 'flagged'
count: true
select: id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,flag,conversationId
top: 25
```

Do not combine `$search` with `$filter`. Paginate via `@odata.nextLink` if
needed.

Sort newest-first in the response (Graph may not support orderby on flag
filter).

### 3. Optional: flag completed

If user asks for completed flags:

```
filter: flag/flagStatus eq 'complete'
count: true
```

### 4. Deep-read when needed

Call `get-mail-message` when bodyPreview is thin but the message is high
priority. For attachments, `list-mail-attachments` then summarize names.

### 5. Thread context

When a flagged message is part of a vendor or work thread, note thread
subject and whether a reply is already sent. Cross-reference `sentitems` only
when it changes the recommended action.

### 6. Triage tags

| Tag | Use when |
|-----|----------|
| Ask | Response or quote requested |
| Decision | Accept/decline, forward to Stacie, pick vendor |
| FYI | Quote received, acknowledgment, reference |

Prioritize: Vixxo senders → vendor quotes → external with clear asks.

## Guardrails

- Work context only; evidence from mailbox data
- Draft-then-approve for any reply (no outbound send)
- No AI sign-off on email drafts
- If zero flagged messages, say so clearly

## Trigger phrases

check flagged emails, review flagged mail, show flagged messages
