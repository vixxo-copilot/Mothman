---
name: VIXXO-spm-invoice-concerns
description: >
  Triage and resolve Vixxo Freshdesk SPM-Invoice Concerns tickets by reading
  Freshdesk ticket context, looking up SR/invoice/payment data in Gateway, and
  producing dry-run proposed resolutions. Use when the user mentions
  SPM-Invoice Concerns, invoice concern queue, SPM invoice tickets, provider
  invoice concerns, or asks to resolve invoice tickets using Gateway.
---

# VIXXO SPM-Invoice Concerns

This skill is a focused variant of `VIXXO-freshdesk-invoice-review` for the
Freshdesk queue/view named **SPM-Invoice Concerns**. It is read-first and
approval-gated: analyze tickets and draft proposed resolutions, but do not
reply, forward, tag, close, assign, or mutate Gateway without explicit operator
approval.

## Default Mode

Use **dry run** by default unless the operator explicitly asks to execute.

Dry run means:
- Freshdesk reads only: ticket search/get and conversation list/get.
- Gateway reads only: service request, invoice, quote, line items, payment
  status, and invoice audit data.
- Output proposed actions and draft replies for review.
- No Freshdesk write APIs, no direct REST mutation, no Gateway write APIs.

## Queue Scope

Target the Freshdesk view or filter for **SPM-Invoice Concerns**. If the exact
view ID or filter representation is unknown, discover it safely:

1. Search Freshdesk for Open SPM tickets with invoice-concern wording in the
   subject/body/tags/custom fields.
2. Prefer tickets whose group is SPM and whose category/type/custom field maps
   to invoice concerns.
3. Show the operator the inferred filter before any batch run.

If the view cannot be discovered from MCP output, use the conservative fallback:
`group_id:159000485013 AND status:2` plus invoice concern keywords such as
`invoice concern`, `payment concern`, `short paid`, `short pay`, `not paid`,
`rejected invoice`, `invoice rejected`, `invoice status`, `invoice dispute`,
`amount paid`, `balance due`, `deducted`, `missing payment`, `AP`, and
`remittance`.

### Confirmed SPM Invoice-Support Filter

Confirmed during the 2026-05-06 SPM-Invoice Concerns run:

```text
group_id:159000485013 AND status:2 AND type:'Invoice Support'
```

This returned open SPM invoice-support tickets and excluded adjacent SPM
queues such as COIs, KSOnboarding, Account Update, and other non-invoice
types. Use this as the preferred SPM invoice-concerns batch filter unless the
operator explicitly asks for the broader SPM group.

## Category Filters

Apply these queue-learned filters before spending Gateway calls. They are
classification aids only; they do not authorize writes.

### Payment Follow-Up / Statement

Move to `pending-payment`, `paid-confirmation`, `short-pay-explained`,
`short-pay-unresolved`, or `manual-review` after Gateway validation.

**Voicemail / qsiap exception:** payment-status or past-due **inquiries**
(without invoice attachment submit) → `payment-inquiry` — stay **SPM**
(`159000485013`), type **Invoice Support**, **Open**. **Do not** forward to
`aphelp@vixxo.com` or `invoices@vixxo.com`. See
`sp-inbound-vetting/reference/qsiap-voicemail-routing.md`.

Strong signals:
- Subject/body includes `statement`, `statement of account`, `past due`,
  `overdue`, `aging`, `balance notice`, `outstanding invoice`, `unpaid
  invoice`, `payment status`, `payment date`, or `when will this be paid`.
- Provider sends an AR spreadsheet, account statement, or multiple invoice
  list.
- Body asks for dates/status across many invoices, e.g. APHelp/QSIAP split
  counts or a high-dollar balance.

Routing:
- Single SR/invoice with clear Gateway paid status -> `paid-confirmation`.
- Accepted/in-review invoice with no payment yet -> `pending-payment`.
- Bulk statements, high-dollar balances, ACH/remit content, or mixed paid /
  rejected / accepted rows -> `manual-review` or Accounting/AP review.

### Manual Invoice Intake

Move to `manual-review` or `account-team-needed` unless Gateway confirms a
clean "Invoice Required" SR and the operator approves the AP-intake path.

Strong signals:
- `invoice attached`, `please process attached invoice`, `please attach this
  invoice to SR`, `can you please invoice this`, `documents are not uploaded`,
  QuickBooks/Payzerware invoice body, or an invoice-looking PDF attachment.
- SR is present and Gateway shows no invoice yet / SR status is `Invoice
  Required for SR`.

Routing:
- Clean SR + invoice attachment + Gateway says invoice required -> proposed
  AP-intake forward/reply package.
- Invoice/document download link with invoice-intake wording and no phishing,
  remit-to-change, ACH/wire, or payment-portal risk -> `invoice-link-forward`.
  Forward the ticket/link to `invoices@vixxo.com`, add an internal note with the
  forwarding rationale, close the Freshdesk ticket, and tag it
  `invoice-link-forwarded` when writes are approved.
- Attachment-only, missing SR, unreadable inline image, or no machine-readable
  invoice/SR -> `not-in-gateway` or `manual-review`; ask for SR/invoice details
  in text or route to AP attachment review.

### Gateway / AP Review Exception

Move to `account-team-needed`, `short-pay-unresolved`, or `manual-review`.

Strong Gateway statuses:
- `UnderARInvestigation`, `ReviewByAP`, `VisualAudit`, `Invoice Review`,
  `PaidOnlyPending`, `Invoice Creation Pending`, `RejectedDoNotProcess`,
  `Delinquent SC Invoice`, or audit exceptions such as duplicate travel, recall
  review, SP NTE exceeded, billed-rate mismatch, or missing line items.

Routing:
- Do not promise payment. Surface the exact status and route to AP,
  Accounting, billing specialist, or Account Team depending on blocker.

### Account Team / VixxoLink Blocker

Move to `vixxolink-portal-support` (preferred) or legacy `account-team-needed`.

Strong signals:
- Provider cannot submit in VixxoLink because travel/rate/NTE/product fields
  are missing, PO is not generating, only `Build Quote` is available, the
  description/dropdown is blank, old portal/new portal confusion exists, or
  login/access is blocked.
- Reply to APHelp past-due / outstanding-invoice campaigns where the **requester
  message** (before quoted history) asks for portal login, account setup, or
  VixxoLink access — even when quoted text mentions past due balances or an
  attachment is a portal screenshot (audit: FD **#70128**).
- The request is really about provider setup, rates, customer/SAP/PO, NTE,
  portal visibility, or business ownership rather than AP payment status.

Routing (execute path — `portal_support_routing.py`):
- Assign **VINT** group (`159000486559`).
- Set Freshdesk **type** to **`VixxoLink Support`**.
- Tags: `vixxolink-portal-support`, `vint-routed`, `open-hold`.
- **Do NOT** forward to `invoices@vixxo.com` or `aphelp@vixxo.com`. **Leave Open.**

**Voicemail:** explicit “VixxoLink support” or portal/login language in the
transcript uses the same VINT route (`voicemail_intake_routing.py`).

### Duplicate / Resubmission Cluster

Move to `duplicate-or-resubmission` only after confirming overlap.

Strong signals:
- Same requester/provider repeats the same subject, invoice number, SR, account
  statement, amount, or attachment metadata across tickets.
- Repeated QuickBooks/payment-link reminders from the same provider for the
  same invoice or same batch.

Routing:
- Compare requester, subject, SR/invoice/account details, amount, attachment
  name/size, and timestamps. Keep the best working ticket open; propose closing
  duplicates only after operator review.

### Payment-Link / Remittance Risk

Move to `security-risk` when BEC/phishing indicators fire; otherwise
`manual-review`. If the link is clearly an invoice/document download rather
than a payment/remittance action, classify it under `invoice-link-forward`
instead.

Strong signals:
- Body includes external `view and pay`, `complete payment`, SendGrid/Intuit
  links, ACH/wire/routing/account instructions, new remit-to details, or
  "verify banking" language.
- Statement emails include payment instructions or BEC warnings.

Routing:
- Treat unsolicited banking/remit changes as `security-risk`.
- For ordinary payment portal links with no BEC trigger, do not click links;
  route as `manual-review` / `payment-link-caution` and validate from trusted
  vendor records.
- For invoice-only links, do not click the link unless a trusted workflow
  requires it. Forward the ticket/link to `invoices@vixxo.com` and close the
  ticket after operator-approved write-back.

### Missing Identifiers / No SR

Move to `not-in-gateway` or `manual-review`.

Strong signals:
- Subject/body is generic (`Invoice`, `Work order`, `Urgent`, `Your account
  information`) and no SR, PO, invoice number, or customer/site can be extracted
  from text.
- Critical identifiers appear only in an image or attachment that was not
  parsed into text.

Routing:
- Ask requester for SR/invoice details in the reply body, or route to manual AP
  attachment review if the attachment likely contains the needed facts.

### Credit Card / Internal Process

Move to `manual-review` unless Gateway clearly shows the expected invoice
state.

Strong signals:
- Internal Vixxo sender reports a credit card transaction, asks AP to reject an
  invoice, asks to mark no-invoice-pending, or says the invoice was attached
  and SR notated.

Routing:
- Add internal findings and route to AP/Accounting or Account Team; do not send
  provider-facing payment commitments.

## Per-Ticket Workflow

For each ticket:

1. Pull ticket subject, requester, description, attachments metadata, tags,
   custom fields, and full conversation history.
2. If the requester or latest sender address is a non-reply mailbox such as
   `no-reply`, `noreply`, `donotreply`, `do-not-reply`, `notification`,
   `mailer-daemon`, or an automated portal address, do not send a public reply.
   Use internal notes, status/tag routing, or manual review instead.
3. Screen for security issues using the phishing/BEC rules from
   `VIXXO-freshdesk-invoice-review`. Do not pull Gateway for suspected hostile
   tickets.
4. If the latest requester message is only an acknowledgement such as
   "Thank you", "Thanks", "Thank you!", or "Appreciate it", and it has no new
   ask, SR, invoice, payment dispute, attachment, or portal issue, classify it
   as `provider-acknowledgement`. Do not pull Gateway again.
5. Apply the Category Filters above to decide whether the ticket is a payment
   follow-up, invoice intake item, Gateway/AP review exception, VixxoLink
   blocker, duplicate/resubmission, invoice-link intake,
   payment-link/remittance risk, missing-ID case, or credit-card/internal-process
   notice.
6. Extract SR numbers, invoice numbers, PO numbers, provider name, amount, and
   customer from subject, body, replies, and attachment filenames.
7. If an SR is present and the category is not security-risk, missing-ID,
   payment-link/remittance risk without a trusted invoice anchor, or pure
   portal/account-team blocker, pull Gateway service request context.
8. Pull Gateway invoice header, invoice line items, quote/approved quote data,
   payment records, and audit output when available.
9. Compare the provider ask against Gateway facts:
   - paid vs pending vs rejected vs not submitted
   - invoice billed amount vs quote/approved amount
   - short-pay, over-bill, duplicate invoice, missing line, or rejected line
   - ORMB calculated amount vs billed amount
   - consignment pattern: `SBUX-` product plus `$0.00` ORMB price
   - NTE exposure: SP NTE may be used in drafts; customer NTE is internal only
10. Classify the resolution path and produce a proposed action.

## Resolution Buckets

- `paid-confirmation`: Gateway shows payment was made. Draft a concise reply
  with paid date/reference if available.
- `pending-payment`: invoice is accepted but unpaid/pending. Draft status and
  next expected owner if visible.
- `rejected-correctable`: invoice rejected with a clear reason. Draft the
  correction path.
- `short-pay-explained`: paid amount is lower for a supported reason
  (approved amount, ORMB, consignment, duplicate, NTE/SP-NTE constraint).
- `short-pay-unresolved`: short-pay exists but Gateway does not explain it.
  Recommend Accounting/AP review; keep open or pending.
- `not-in-gateway`: SR or invoice cannot be found. Recommend requester provide
  missing SR/invoice details or route to manual.
- `invoice-link-forward`: requester provided a link to an invoice/document for
  AP intake, with no BEC/phishing/remittance risk. Forward to
  `invoices@vixxo.com`, add a private note documenting the invoice-link intake,
  close the ticket, and tag it `invoice-link-forwarded` after approval.
- `duplicate-or-resubmission`: same SR/invoice appears in another ticket or
  Gateway record. Recommend closing duplicate only after operator review.
- `account-team-needed`: SR status, provider setup, customer/SAP/PO, or NTE
  issue blocks AP resolution.
- `provider-acknowledgement`: latest requester message only says thanks or
  otherwise acknowledges the prior answer, with no new ask or attachment. Add a
  private note, close the ticket, and tag it `provider-acknowledgement`.
- `security-risk`: phishing/BEC/remit-to change. No reply; escalate per policy.
- `manual-review`: ambiguous, high-dollar, stale, or missing critical facts.
  Also use for payment-link/remittance-risk tickets that do not meet the BEC or
  phishing threshold, broad/high-dollar statements, mixed-status invoice lists,
  internal credit-card/process notices, and tickets whose required identifiers
  appear only in attachments or inline images.

## Drafting Rules

Customer-facing drafts must be short, relationship-first, and factual.

Do not draft or send public replies to non-reply senders. Treat addresses and
display names containing `no-reply`, `noreply`, `donotreply`, `do-not-reply`,
`notification`, `mailer-daemon`, or automated portal/billing sender patterns as
non-replyable. For those tickets, use private notes, status/tag routing, or
manual review; if a human contact is needed, route internally rather than
replying to the non-reply address.

Do not include customer NTE in any SP-facing draft or AP-intake forward body.
Only include SP NTE when it directly explains the answer. If customer NTE or a
large dollar threshold is material, put it in the internal findings and route to
Account Team or Accounting instead of drafting an SP commitment.

Never say an invoice will be paid unless Gateway evidence supports that exact
status. Use "our records show" and name the record source when helpful.

## Output Format

Use this format for dry-run batches:

```markdown
# SPM-Invoice Concerns Dry Run

Filter inferred: <Freshdesk filter/view>
Tickets reviewed: <N>
Writes performed: none

## Proposed Resolutions
| Ticket | Requester | Ask | Gateway facts | Proposed resolution | Draft/action |
|---|---|---|---|---|---|
| #123 | name/email | short-pay question | invoice paid $X on date; approved $Y | short-pay-explained | draft reply |

## Exceptions / Needs Operator Decision
- #123: <why not safe to resolve from Gateway alone>
```

For a single-ticket deep dive, use the same findings sections as
`VIXXO-freshdesk-invoice-review` Mode B, but label the result
`SPM-Invoice Concerns Dry Run` and include `Writes performed: none`.

## Write-Back Protocol

Do not write during dry run. If the operator approves execution later, follow
the write-back protocol from `VIXXO-freshdesk-invoice-review`:

1. Present the exact reply/note/status/tag/forward actions.
2. Wait for explicit approval.
3. Use Freshdesk writes only after approval.
4. Use Gateway writes only if a future approved workflow explicitly allows them.

For `invoice-link-forward` tickets, the exact approval package must include:

- Freshdesk forward target: `invoices@vixxo.com`.
- Forward body: concise AP intake context with ticket number, requester,
  provider when known, SR/invoice/PO identifiers found in the ticket, and the
  invoice link from the provider message.
- Private note: "Invoice-link intake forwarded to invoices@vixxo.com per SPM
  invoice-concerns workflow; closing ticket."
- Close action: set Freshdesk status to closed, preserve existing tags, and add
  `invoice-link-forwarded`.

### Freshdesk Write-Back Details

Confirmed during the 2026-05-06 SPM-Invoice Concerns write-back:

- `conversations_manage create_reply` works for approved public replies.
- `conversations_manage create_note` works for approved private notes.
- `tickets_manage update` rejects status/tag updates with validation errors.
  Use the direct Freshdesk REST API bypass from
  `VIXXO-freshdesk-invoice-review` for status and tag mutations.
- Closing an `Invoice Support` ticket through REST may require these fields in
  addition to `status: 5` and `type: "Invoice Support"`:
  - `custom_fields.cf_sp`: string, e.g. provider name or `Internal Vixxo`
  - `custom_fields.cf_sr`: string, use the SR when known or `N/A` if no SR
  - `custom_fields.cf_customer`: enum value; use the known customer from
    Gateway when available, otherwise `Other`
  - `custom_fields.cf_type_of_request`: one of:
    `Submit an Invoice for manual entry`,
    `Follow up on an Unpaid Invoice`,
    `Resolve Rejected Invoice`
- Freshdesk tag updates replace the full tag set. Preserve existing tags when
  appending unless intentionally clearing them.
- Do not close replied tickets unless closure was explicitly included in the
  approval package. A reply-only approval means post the reply and leave the
  ticket open.

For duplicates, confirm the duplicate relationship before closing by comparing
requester, subject, SR/invoice/account details, timestamps, and attachment
metadata. Inline image filenames can differ even when the substantive ticket
content is identical.
