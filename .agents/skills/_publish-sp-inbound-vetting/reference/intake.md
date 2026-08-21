# Intake — Salesforce Queues + AP Help

Find items for SP identity vetting across **three Salesforce queues** and
**Freshdesk AP Help**. Salesforce is primary for ksonboarding, COI, and
service.providermanagement; Freshdesk is primary for AP Help.

Queue filters, SOQL, and routing rules live in [queues.md](queues.md).

## Target surfaces

| Surface | Primary system | Queue key | Notes |
| --- | --- | --- | --- |
| KS Onboarding | **Salesforce** | `ksonboarding` | SP onboarding / recruitment Cases and Leads |
| COI | **Salesforce** | `coi` | Certificate of insurance / compliance Cases |
| Service Provider Management | **Salesforce** | `spm` | SPM account, sourcing, VixxoLink/trade support Cases |
| AP Help | **Freshdesk** | `aphelp` | AP / billing / payment intake at `aphelp@vixxo.com` |

## Salesforce batch pull (primary — ksonboarding, coi, spm)

1. `get_username` on Salesforce MCP.
2. Discover queue Ids if not cached — see [queues.md](queues.md) discovery SOQL.
3. For each queue key (`ksonboarding`, `coi`, `spm`):
   - Pull open Cases with the queue `OwnerId` filter.
   - For `ksonboarding`, also pull open Leads owned by the queue when your org
     routes onboarding that way.
4. Paginate / raise `LIMIT` when backlog exceeds 200.
5. Skip Cases already vetted unless user says `re-vet`.

**Case content sources:** `Subject`, `Description`, `SuppliedEmail`,
`ContactEmail`, Email-to-Case thread (when available via Case feed or linked
EmailMessage — use org-appropriate SOQL or UI export when MCP is read-only).

**Single-item SF intake:** accept Case Number, Case Id (15/18 char), Case URL,
Lead Id, or pasted subject + body.

When only email exists (no Case yet), run vetting and present the packet; skip
SF writes unless the user links or creates a Case Id.

## Freshdesk batch pull (AP Help only)

```
group_id:159000485013 AND status:2
```

Then apply the recipient gate below. Paginate all pages (`search_tickets` or
REST `/api/v2/search/tickets`).

For each candidate, `get_ticket` + conversations when body is thin.

### Recipient gate (aphelp)

Keep only tickets sent to `aphelp@vixxo.com`. Match on any of:

- `to_emails` / support email on the ticket
- `cc_emails`
- original-envelope recipient in the first conversation
- forwarded-message headers in body (`To:`, `Delivered-To:`, `X-Forwarded-To:`)
- body-visible recipient lines

Target address (case-insensitive): `aphelp@vixxo.com`

## Payment/AP detection (SF queues)

Before vetting, scan subject and body for payment/AP signals from the routing
table in [queues.md](queues.md). When matched:

1. Still run full Gateway + Salesforce identity vetting.
2. Set packet **Routing** = `Recommend forward to AP Help`.
3. Include draft forward recommendation in the SF Case Task — **do not send**.

Examples: "status of payment for invoice 12345", "haven't received check",
"AP hold on my account", "duplicate payment".

## Dedupe and exclusions

| Condition | Action |
| --- | --- |
| SF Case already has vetting Task | Skip — unless `re-vet` or Case id named |
| Freshdesk tagged `sp-vetted` | Skip — unless `re-vet` or ticket id named |
| Subject includes `New voicemail` | Skip — use `sp-voicemail-triage` |
| User says `include voicemails` | Process anyway |
| Batch `all` | Dedupe by Case Id / ticket id across queues |

**Ordering:** oldest-first by `CreatedDate` / `created_at` unless user asks
newest-first.

## Single-item intake

Accept:

- Salesforce Case Number, Case Id, or URL
- Salesforce Lead Id (ksonboarding)
- Freshdesk ticket id or URL (AP Help)
- Outlook message id (when no Case/ticket exists yet)
- Pasted subject + body for preview

## Outlook secondary intake (optional)

When the user asks to vet mail in a shared mailbox:

1. `verify-login` on Microsoft 365 MCP.
2. Search separately — do not combine `$search` and `$filter` on one Graph call:
   - Pass A: `$search="aphelp@vixxo.com"` with `receivedDateTime ge {window}`
   - Pass B: `$search="ksonboarding@vixxo.com"` with the same window
   - Pass C: `$search="COI@vixxo.com"` / `$search="service.providermanagement@vixxo.com"`
3. Default window: last 7 days; user may override.
4. Dedupe against Salesforce Case ids and Freshdesk ticket ids when mail
   already spawned a record.

## Entity extraction (every item)

From Case/ticket subject, body, contact, and attachments metadata extract:

| Field | Priority |
| --- | --- |
| Contact name | SF Case contact / FD requester `name` |
| SP number | Explicit `SP #`, `SP-`, `KS#####`, Siebel-style numbers |
| Company name | Requester org, **email signature**, subject, body, email domain |
| Email | `ContactEmail`, `SuppliedEmail`, or requester email |
| Phone | Contact + body |
| SR / invoice refs | Bootstrap Gateway / VixxoLink when company is missing |
| Routing signals | Payment/AP vs COI/onboarding/SPM (see [queues.md](queues.md)) |

### Email signature company (required when present)

Parse the message body for SP legal names in closing signatures **before**
falling back to generic mailbox display names.

| Pattern | Example |
| --- | --- |
| `{Role} for {Company}` | `Bookkeeper for Brewer Lock & Safe Co, Inc.` |
| Standalone line ending in LLC/Inc before phone/website | `FCS Facility Maintenance LLC` |

When the requester display name is a generic mailbox label (`Workorders`,
`Billing`, `Support`, etc.), prefer the signature company.

**Subject-line company (COI / onboarding):** parse quoted or plain company names
from subjects like `COI from "PEAK SEASON"`. Strip job title prefixes
(`Account Manager-`, etc.) from signature rows.

Normalize company names before search (strip punctuation; keep LLC/Inc when
matching Siebel rows).
