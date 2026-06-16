# Intake — AP Help and KS Onboarding

Find items **received at** `aphelp@vixxo.com` or `ksonboarding@vixxo.com`.
Primary surface is Freshdesk; Outlook is secondary when the user points at mail
without a ticket.

## Target mailboxes

| Mailbox | Typical ticket type | Notes |
| --- | --- | --- |
| `aphelp@vixxo.com` | `Invoice Support`, mixed SPM | AP / billing / payment intake |
| `ksonboarding@vixxo.com` | `KSOnboarding`, mixed SPM | SP onboarding / recruitment intake |

## Freshdesk batch pull

1. Search Open SPM tickets:

```
group_id:159000485013 AND status:2
```

Paginate all pages (`search_tickets` or REST `/api/v2/search/tickets`).

2. For each candidate, `get_ticket` + conversations when body is thin.

3. **Recipient gate (required):** keep only tickets sent to a target mailbox.
   Match on any of:

- `to_emails` / support email on the ticket
- `cc_emails`
- original-envelope recipient in the first conversation
- forwarded-message headers in body (`To:`, `Delivered-To:`, `X-Forwarded-To:`)
- body-visible recipient lines

Target addresses (case-insensitive):

- `aphelp@vixxo.com`
- `ksonboarding@vixxo.com`

4. **Dedupe:** skip tickets already tagged `sp-vetted` unless the user says
   `re-vet` or names the ticket id.

5. **Sibling-skill exclusions (default):**

| Condition | Action |
| --- | --- |
| Subject includes `New voicemail` | Skip — use `sp-voicemail-triage` |
| User says `include voicemails` | Process anyway |

6. **Ordering:** oldest-first by `created_at` unless the user asks newest-first.

## Single-item intake

Accept:

- Freshdesk ticket id or URL
- Outlook message id (when no Freshdesk ticket exists yet)
- Pasted subject + body when the user is previewing one item

When only Outlook mail exists, run vetting and present the packet; skip
Freshdesk writes unless the user links or creates a ticket id.

## Outlook secondary intake (optional)

When the user asks to vet mail in a shared mailbox or their inbox:

1. `verify-login` on Microsoft 365 MCP.
2. Search separately — do not combine `$search` and `$filter` on one Graph call:
   - Pass A: `$search="aphelp@vixxo.com"` with `receivedDateTime ge {window}`
   - Pass B: `$search="ksonboarding@vixxo.com"` with the same window
3. Default window: last 7 days; user may override.
4. Dedupe against Freshdesk ticket ids when the message already spawned a ticket.

## Entity extraction (every item)

From subject, body, requester, and attachments metadata extract:

| Field | Priority |
| --- | --- |
| SP number | Explicit `SP #`, `SP-`, Siebel-style numbers in body |
| Company name | Requester org, signature, subject, body |
| Contact name | Requester display name |
| Email / phone | Requester + body |
| SR / invoice refs | Use to bootstrap Gateway lookup when company is missing |

Normalize company names before search (strip punctuation; keep LLC/Inc when
matching Siebel rows).
