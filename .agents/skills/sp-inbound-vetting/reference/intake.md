# Intake — AP Help, KS Onboarding, SPM Invoice Concerns

Find items for SP identity vetting across three Freshdesk intake surfaces.
Primary surface is Freshdesk; Outlook is secondary when the user points at mail
without a ticket.

Queue filters and batch keys live in [queues.md](queues.md).

## Target mailboxes and folders

| Surface | Freshdesk mapping | Notes |
| --- | --- | --- |
| `aphelp@vixxo.com` | SPM group + recipient gate | AP / billing / payment intake |
| `ksonboarding@vixxo.com` | `type:'KSOnboarding'` | SP onboarding / recruitment intake |
| **SPM - Invoice Concerns** | `type:'Invoice Support'` in SPM group | Invoice/payment concern folder |

## Freshdesk batch pull

### 1. KS Onboarding

```
group_id:159000485013 AND status:2 AND type:'KSOnboarding'
```

### 2. SPM - Invoice Concerns

Open, **untouched** tickets in the Freshdesk sidebar folder **SPM - Invoice
Concerns**:

```
group_id:159000485013 AND status:2 AND type:'Invoice Support'
```

Skip tickets already tagged `sp-vetted`. Tickets tagged
`spm-invoice-concerns-reviewed` from `vixxo-spm-invoice-concerns` are still
in scope until `sp-vetted` is applied.

### 3. AP Help (mailbox gate)

```
group_id:159000485013 AND status:2
```

Then apply the recipient gate below.

Paginate all pages (`search_tickets` or REST `/api/v2/search/tickets`).

For each candidate, `get_ticket` + conversations when body is thin.

### Recipient gate (aphelp only)

Keep only tickets sent to a target mailbox. Match on any of:

- `to_emails` / support email on the ticket
- `cc_emails`
- original-envelope recipient in the first conversation
- forwarded-message headers in body (`To:`, `Delivered-To:`, `X-Forwarded-To:`)
- body-visible recipient lines

Target addresses (case-insensitive):

- `aphelp@vixxo.com`
- `ksonboarding@vixxo.com` (when using the broad SPM search + mailbox filter)

**Invoice Concerns** and **KS Onboarding** type-filtered pulls do **not**
require the recipient gate.

## Dedupe and exclusions

| Condition | Action |
| --- | --- |
| Tagged `sp-vetted` | Skip — unless user says `re-vet` or names the ticket id |
| Subject includes `New voicemail` | Skip — use `sp-voicemail-triage` |
| User says `include voicemails` | Process anyway |
| Batch `all` | Dedupe by ticket id across queues |

**Ordering:** oldest-first by `created_at` unless the user asks newest-first.

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
| Email | Requester email — **primary** Gateway `createdByUsername` anchor |
| Contact name | Freshdesk requester `name` — search before company string |
| SP number | Explicit `SP #`, `SP-`, `KS#####`, Siebel-style numbers in body |
| SR / invoice refs | Bootstrap Gateway / VixxoLink when identifiers present |
| Company name | Requester org, signature, subject, body — fuzzy vs Gateway SP name |
| Phone | Requester + body |

Gateway/Siebel SP display names may include internal tracking prefixes (`KS`,
`CCPAY`, `STRYKER ONLY`) that will **not** appear on provider documentation.
Strip those before comparing company text; prefer email and contact name for
identification.
