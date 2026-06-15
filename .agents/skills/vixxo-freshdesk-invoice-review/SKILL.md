---
name: vixxo-freshdesk-invoice-review
description: Triage the Vixxo AP help desk's Freshdesk queue (Open + No Agent) and deep-dive individual invoice tickets using Gateway. Use this skill whenever the user is working the AP help desk backlog, mentions "AP backlog", "AP help desk", "Freshdesk queue", "invoice tickets", "No Agent queue", asks to "review the AP tickets", wants to classify/route/draft replies for provider invoice tickets, or wants to deep-dive a specific Freshdesk ticket number involving invoices, rejected invoices, payment follow-ups, remittance, SR submissions, or consignment parts. Trigger even when the user names a ticket number or a service request number without explicitly saying "help desk" — if it looks like AP/Freshdesk/invoice work, use this skill. Do NOT use for non-invoice Freshdesk work (HR, IT, facilities).
---

# VIXXO Freshdesk Invoice Review

This skill runs the Vixxo AP help desk triage and deep-dive loop end-to-end. It replaces the earlier `ap-helpdesk` prototype, which only handled single-ticket deep-dive. Here we add the batch triage layer so the human isn't forced to read every ticket top-to-bottom before deciding what to do with it.

The skill has **two modes**. Pick one based on what the user is asking:

- **Mode A — Batch Triage.** The user wants to work the queue. "Let's triage the AP backlog," "pull the No Agent queue," "next 10 tickets." Paginated, 10 tickets per page, oldest-first.
- **Mode B — Deep-Dive.** The user names a single Freshdesk ticket or wants to fully analyze one invoice situation. "Look at ticket #28864," "dig into the one from Acme Repair." Full Gateway pull, billing analysis, draft reply.

If the user's ask is ambiguous (e.g., "look at the AP tickets"), default to Mode A and offer Mode B as an option at the end.

---

## Core philosophy

The goal is to compress what's been a 20–40 minute per-ticket manual process down to under two minutes, **without** taking any customer-facing or system-of-record action without the operator's explicit approval. The skill drafts; the operator decides; the skill executes on confirmation.

This matters because (a) mis-sent provider replies damage relationships that Vixxo's account team spends months building, and (b) Freshdesk and Gateway are the authoritative systems — silent writes to either would undermine trust in the automation. So every outbound action (reply, status change, agent assignment, future v2 Gateway SR notes) passes through a named operator approval step.

---

## Before you start

### Queue scope — "All SPM Tickets" (authoritative, pinned 2026-04-24)

The authoritative scope for Mode A batch triage is the **SPM Freshdesk group**, not the AP-help-desk email inbox. Confirmed mapping:

- Group name: `SPM`
- `group_id`: `159000485013`
- Freshdesk UI view: **"All SPM Tickets"**

Filter for batch pulls:

```
group_id:159000485013 AND status:2
```

(Add `order_by:created_at order_type:desc` for newest-first, or `desc`→`asc` for oldest-first.)

**Do NOT use** `email_config_id:159000195932` as the primary filter anymore. That was the earlier heuristic and over-includes non-SPM tickets (Corp AP, VINT, Triage) while missing SPM tickets that arrived via other inboxes. Group ownership is the canonical signal.

Other group_ids observed on this tenant (for reference — do not triage these in Mode A unless explicitly asked):

| group_id | name |
|---|---|
| 159000485013 | **SPM** (this skill's scope) |
| 159000486559 | **VINT** (manual-entry invoice routing target) |
| 159000486566 | Corp AP |
| 159000486567 | Data Ops |
| 159000486568 | Capital Supervisors |
| 159000486569 | Project Managers |
| 159000486570 | FinOps |
| 159000578548 | SWS |
| 159000560699 | Triage |

Subject/invoice-keyword heuristics are no longer needed to widen the net — SPM group membership is the definition of "in scope for this skill."

### First-run confirmation of the "No Agent" filter

 Freshdesk represents "no assigned agent" differently across instances — sometimes it's `responder_id = null`, sometimes a sentinel agent ID, sometimes a custom field. On the first Mode A run in a session, detect this by listing a few Open tickets and showing the user how agent assignment is represented. Confirm with the user which value means "No Agent" before building the filter. Cache this decision for the rest of the session.

Why: hard-coding a field value would silently break triage the first time Freshdesk config changes, and mis-filtering the queue would cause us to either skip tickets or pull ones already being worked.

### Manual-review recipient exclusion

If a ticket was sent to either `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com` in the `to`, `cc`, original-envelope recipient, forwarded-message header, or body-visible recipient list, **remove it from this skill's rule flow and leave it alone for manual review**.

This is a hard exclusion, not a bucket. Do not classify it as B6-onboarding, B9-signs-sp-update, bucket 4, or any other rule-driven action. Do not pull Gateway, draft a reply, add tags, add notes, close, forward, or mutate the ticket. In Mode A reports, list it as `manual-review-recipient-exclusion` with the matched recipient so the operator knows why it was skipped.

### QSI AP source tag overlay

If a ticket came from or was forwarded from `qsiap@vixxo.com`, add the tag `qsiap-source` to the ticket during the normal write phase.

Evaluate the combined match surface: requester email, `from`, `reply-to`, `to`, `cc`, original-envelope recipients, forwarded-message headers, body-visible forwarded headers, conversation history, and attachment filenames when available. Treat any clear occurrence of `qsiap@vixxo.com` as a match.

This is a source-tag overlay, not a bucket. It **does not change classification, Gateway lookup rules, drafting behavior, close/keep-open decisions, or owner routing**. Merge `qsiap-source` into whatever tags the classified bucket already applies. If the ticket has no other write action planned, perform a tag-only update after operator approval. The manual-review recipient exclusion remains stronger: if a ticket is excluded because it was sent to `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com`, report the QSI AP match in the triage output but do not mutate the ticket unless the operator explicitly overrides the exclusion for that ticket.

### SPM invoice-concern category overlays

These overlays were added from the 2026-05-18 SPM Invoice Support queue review.
Use them to move tickets into the right bucket before drafting or Gateway
research. They are classification and routing aids only; they do not authorize
writes or bypass operator approval.

Apply them after the hard exclusions and pre-screens (manual-review recipient
exclusion, QSI AP overlay, phishing/BEC, onboarding, SAP, vendor-hold, and
Signs & Lighting) and before Rules 1–7. If an overlay strongly matches, use the
mapped bucket below; if another normal rule also strongly matches, set the
`ambiguity_flag`.

| Overlay | Strong signals | Bucket / route |
|---|---|---|
| Payment follow-up / statement | `statement`, `statement of account`, `past due`, `overdue`, `aging`, `balance notice`, `outstanding invoice`, `unpaid invoice`, `payment status`, `payment date`, "when will this be paid", AR spreadsheet, account statement, or multi-invoice payment list | Bucket 3 if a Gateway-backed payment answer is possible. If bulk/high-dollar, mixed paid/rejected/accepted rows, ACH/remit content, or no single SR/invoice anchor, keep Open and route to AP/Accounting manual review. |
| Manual-entry invoice request / VINT route | Ticket explicitly states that the requester is looking for, asking for, or needs `manual entry` / `manual-entry` / `manually entered` handling for an invoice. Examples: "looking for manual entry of this invoice", "please manually enter the invoice", "needs manual invoice entry", "submit for manual entry". | **B10-manual-entry-vint overlay on Bucket 4.** Process using the normal bucket 4 invoice-submission writes — Gateway research when an SR is present, AP-intake `/forward` to `invoices@vixxo.com`, requester acknowledgment when replyable, internal note, and close — and additionally change `group_id` from SPM to VINT (`159000486559`) with tags `manual-entry-invoice` + `vint-routed` in the status update. |
| Manual invoice intake | `invoice attached`, `please process attached invoice`, `please attach this invoice to SR`, `can you please invoice this`, `documents are not uploaded`, QuickBooks/Payzerware invoice body, invoice-looking PDF, or SR present with Gateway status `Invoice Required for SR` | Bucket 4 when SR + invoice attachment are clean and Gateway has no blocking anomaly. If missing SR, attachment-only, inline image, or unreadable data, Bucket 7/manual AP attachment review. |
| Gateway / AP review exception | Gateway status or ticket text shows `UnderARInvestigation`, `ReviewByAP`, `VisualAudit`, `Invoice Review`, `PaidOnlyPending`, `Invoice Creation Pending`, `RejectedDoNotProcess`, `Delinquent SC Invoice`, duplicate travel, recall review, SP NTE exceeded, billed-rate mismatch, or missing line items | Bucket 6 / Pending-hold owner routing, not close. Route to AP, Accounting, billing specialist, or Account Team based on blocker; do not promise payment. |
| Account Team / VixxoLink blocker | Portal cannot submit because travel/rate/NTE/product fields are missing, PO is not generating, only `Build Quote` is available, description/dropdown is blank, old/new portal confusion, login/access issue, provider setup, customer/SAP/PO, NTE, rate, or portal-visibility blocker | Bucket 6 / Account Team or VixxoLink support route. Leave Open/Pending; do not treat as normal AP payment follow-up. |
| Duplicate / resubmission cluster | Same provider/requester repeats same subject, invoice number, SR, account statement, amount, or attachment name/size; repeated QuickBooks/payment-link reminders from same provider for same invoice/batch | Bucket 6 or 7 until confirmed. If confirmed, tag `duplicate-or-resubmission` and keep best working ticket open; propose duplicate close only after operator review. |
| Payment-link / remittance risk | External `view and pay`, `complete payment`, Intuit/SendGrid/payment portal links, ACH/wire/routing/account instructions, new remit-to details, "verify banking", or statement with payment instructions/BEC warning | Rule 0/security if BEC/phishing indicators fire. Otherwise Bucket 7/manual with `payment-link-caution`; do not click links or forward remit details to AP intake as if verified. |
| Missing identifiers / no SR | Generic subject/body (`Invoice`, `Work order`, `Urgent`, `Your account information`) with no machine-readable SR, PO, invoice number, customer/site, or only image/attachment-only identifiers | Bucket 7/manual. Ask for SR/invoice details in body or route to AP attachment review if attachments likely contain facts. |
| Credit card / internal process | Internal Vixxo sender reports credit-card payment, asks AP to reject an invoice, mark no-invoice-pending, or says invoice was attached and SR notated | Bucket 6/internal AP or Accounting process route. No provider-facing payment commitment. |

---

## Mode A — Batch Triage

### Workflow

1. **Filter the queue** to Status = Open AND Agent = No Agent (using the confirmed representation from "Before you start"). Order oldest-first by ticket created date. Oldest-first is deliberate: it prevents the backlog bottom from rotting while newer tickets get attention.

2. **Pull one page of 10 tickets.** If the user asks for a different page size (they sometimes will), honor it — 10 is the default because it bounds Gateway API load to roughly 50 calls per page in the worst case and keeps the resulting report short enough to scan.

3. **For each ticket on the page:**
   a. Pull the ticket's subject, description, and requester.
   b. Check the manual-review recipient exclusion. If the ticket was sent to `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com`, report it as `manual-review-recipient-exclusion` and do nothing else with that ticket.
   c. Check the QSI AP source tag overlay. If the ticket came from or was forwarded from `qsiap@vixxo.com`, mark `qsiap-source` as a tag to merge into the ticket's write phase and surface the match in the report.
   d. Apply the SPM invoice-concern category overlays, then classify against the decision tree (below), top-down, first-match wins.
   e. If a later rule also strongly matches, surface the secondary match as an `ambiguity` flag so the operator can sanity-check the routing.
   f. If the bucket is 2, 3, 4, or B10-manual-entry-vint: extract the SR number from ticket content, then pull Gateway context in order — service request → invoice + line items → quote + line items. **Skip Gateway entirely for buckets 0, 1-close, 1-follow-up, 5, 6, 7, and `manual-review-recipient-exclusion`** (Gateway data doesn't inform those decisions; pulling it would waste API budget and, for bucket 0, could lend credibility to a fake SR # fabricated by an attacker).
   g. Cache SR lookups within the run. It's common for multiple tickets to reference the same SR (or for an operator to request deep-dive on a ticket already pulled in this page's triage); don't hit Gateway twice for the same SR.

4. **Produce the triage report.** Format is a markdown table grouped by bucket, with columns: `ticket_id`, `subject`, `requester`, `bucket`, `ambiguity_flag`, `gateway_findings_summary`, `recommended_action`. Render inline AND save a timestamped copy in the working folder with the page number in the filename, e.g. `triage-page-03-2026-04-16T1422.md`. The saved copy exists so the operator can go back to it after a deep-dive without re-running the triage.

5. **Pause at end of page** and ask the operator: continue to the next page of 10, or deep-dive a specific ticket from the page just shown? Don't roll forward automatically — the operator is the control loop.

### Gateway call budget per page (worst case)

- 10 tickets × (1 SR + 1 invoice + 1 invoice-lineitems + 1 quote + 1 quote-lineitems) = 50 Gateway calls maximum.
- Real-world average is much lower because buckets 0/1-close/1-follow-up/5/6/7 skip Gateway entirely and SR lookups cache.

---

## Mode B — Deep-Dive

### Workflow

1. **Take a ticket ID** from the operator (either named directly, or selected from a Mode A page).

2. **Pull the full ticket**: subject, description, full conversation history (not just the first message — threads matter), requester info, status, any attachments referenced in the body.

3. **Check the manual-review recipient exclusion.** If the ticket was sent to `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com`, stop the deep-dive and report that the ticket is excluded from this skill's rule flow. Do not pull Gateway, draft, tag, note, close, or forward it unless the operator explicitly overrides the exclusion for that ticket.

4. **Check the manual-entry / VINT route overlay.** If the ticket explicitly states that the requester is looking for manual entry of an invoice, classify as B10-manual-entry-vint and continue the normal bucket 4 research/write path. The final recommendation should include the bucket 4 forward/reply/note/close writes plus `group_id:159000486559` and tags `manual-entry-invoice` + `vint-routed`.

5. **Extract the SR number.** Look in subject, body, and conversation replies. Providers are inconsistent about where they put it. If multiple SR numbers appear, prefer the one in the subject or the one referenced most frequently in the thread — and flag the others.

6. **Pull the full Gateway context:**
   - Service request (status, site, provider, total approved, any rejection reasons)
   - Invoice header (invoice number, total billed, status, date)
   - All invoice line items — for each line: product code/name, quantity, unit price, **ORMB calculated unit price**, extended amount, any short-pay/over-pay reasons
   - Quote header (if one exists)
   - All quote line items (approved amount, incurred vs. proposed)
   - Payment records (paid / pending / on hold / returned)

7. **Analyze the billing situation.** Look for:
   - **Short pay:** Invoice total < quote-approved total. Walk each line to find where the delta is.
   - **Over-bill:** Invoice total > quote-approved total. Identify which lines exceeded quote.
   - **Consignment parts (Starbucks):** Apply the SBUX / $0 ORMB heuristic — see below.
   - **Rejected lines:** Any invoice lines with non-zero billed amount but $0 ORMB-calculated, and the product is NOT in the SBUX consignment pattern.
   - **Payment status:** Paid + when. Pending + reason. On hold + reason code.
   - **Duplicate billing:** Same SR + invoice number appearing on multiple tickets.

8. **Draft the customer-facing reply** appropriate to the ticket's classified bucket (see Per-Bucket Drafting Behavior). Keep it relationship-first. Providers are under real financial pressure when they're writing these tickets — don't be robotic.

9. **Return structured output:**
   - Findings summary (one paragraph, plain English — what's going on with this invoice)
   - Root cause (one or two sentences on *why* there's an issue, if there is one)
   - Draft reply (ready to paste or, with operator approval, send through Freshdesk)
   - Suggested ticket action (reply + close / reply + keep open / forward+close+move to VINT / reassign Account Team / escalate Accounting / flag for manual)

### SBUX / $0 ORMB consignment heuristic

From ticket #28864: invoice line items where the product name is prefixed `SBUX-` **and** the ORMB calculated unit price is `$0.00` are reliable markers for Starbucks consignment parts. Consignment means the part was supplied by Starbucks (not purchased by the provider), so the $0 calculated price is *correct* — the short-pay is not a billing error and the provider reply should explain the consignment structure rather than promising a correction.

Present this as a *high-confidence hypothesis* in the findings ("Lines 3, 7, 12 are likely Starbucks consignment parts based on SBUX- prefix + $0 ORMB price — this explains the short-pay.") and let the operator confirm before the reply goes out. Don't silently assume it in the draft without calling it out.

---

## Decision Tree (used in both modes)

**Match surface:** evaluate the **subject, full description/body, conversation history, AND attachments together** — not the subject in isolation. Providers often write a one-line subject and put the real content in the body, or send a terse body ("thanks") with the substantive content as an attached invoice PDF. Classifying on subject alone will mis-route these. Read the whole ticket before deciding.

**Matching philosophy:** the keywords listed in each row below are examples, not a closed list — match on intent, not exact phrase. A ticket with the subject "Need status on my invoices from last week" matches bucket 3 (payment follow-up) even though none of those exact keywords appear.

**Evaluation order:** top-down, first rule that matches wins.

0. **Manual-review recipient exclusion** — evaluated before the decision tree. Tickets sent to `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com` are removed from this skill's rules and left untouched for manual review.
1. **Rule 0** (phishing screen) — evaluated first within the remaining rule flow; if it fires, short-circuits the rest of the tree. We don't want to research a phishing ticket in Gateway or draft a reply to an attacker.
2. **Rule 0b** (onboarding screen, added v1.6) — evaluated after Rule 0; if it fires, short-circuits rules 0c, 0d, 0e, and 1–7. Onboarding tickets are routinely worded with remittance/invoice/payment vocabulary and will mis-classify into B5-remittance or B4-invoice if they hit the keyword tree.
3. **Rule 0c** (SAP screen, added v1.7) — evaluated after Rule 0b; if it fires, short-circuits rules 0d, 0e, and 1–7. SAP tickets need ERP-side reconciliation and must not be closed or BCC'd from AP.
4. **Rule 0d** (vendor-hold notification screen, added v1.8) — evaluated after Rule 0c; if it fires, short-circuits rules 0e and 1–7. Internal `knowledgesync@vixxo.com` automation generates "Vendor on Hold / WDOnHold / Do Not Use Vendor assigned to Open Ticket" notifications that are SPM-ops work items, not SP-facing AP work — they must stay Open and route to Account Team for vendor-status reconciliation.
5. **Rule 0e** (Signs & Lighting internal-sender screen, added v1.10) — evaluated after Rule 0d; if it fires, short-circuits rules 1–7. Emails from internal `@vixxo.com` parties where the ticket contains **both** `\bsigns?\b` AND `\blighting\b` (AND semantics, not OR) get an immediate AP-side confirmation reply and split into two sub-buckets: invoice content → forward original message (with attachments) to `invoices@vixxo.com` + ack reply + Close (corrected from BCC pattern in v1.11); SP-update content → tag for Vendor Maintenance and leave Open.
6. **SPM invoice-concern category overlays** — payment statements, manual-entry invoice requests, manual invoice intake, Gateway/AP exceptions, VixxoLink blockers, duplicates, payment-link/remit risk, missing identifiers, and credit-card/internal-process tickets are mapped to the safest bucket before the generic keyword rules. These overlays prevent broad statements from becoming one-off payment replies, portal blockers from becoming AP closes, manual-entry requests from staying in SPM, and payment-link/remittance tickets from entering normal invoice intake.
7. **Rules 1–7** — normal decision tree; first rule that matches wins.

> **v1.11 changelog (2026-05-01) — AP-intake forward must carry attachments.**
>
> The v1.0–v1.10 implementation of the bucket 4 and B9-signs-invoice "forward to `invoices@vixxo.com`" leg was a `create_reply` with `bcc_emails: ["invoices@vixxo.com"]`, on the assumption that the BCC carried the same content as the SP-facing reply. Operator audit on 2026-05-01 (WERCS, Inc. batch — 7 tickets) confirmed that Freshdesk's `/reply` endpoint sends only the reply *body* to BCC recipients; **the original ticket attachments are not carried**. AP was receiving acknowledgments without the actual invoice PDFs and could not process them.
>
> **Fix.** All bucket 4 and B9-signs-invoice closes now use `POST /api/v2/tickets/{id}/forward` (Freshdesk REST API direct, since the MCP does not expose a forward action) for the AP intake leg. The `/forward` endpoint defaults `include_original_attachments: true`, which carries the original message and PDF attachments to AP intake — that is what AP needs to process the invoice. The SP-facing acknowledgment reply (`create_reply`) is now a separate write with no BCC. The no-reply guardrail (v1.4) also normalizes to `/forward` for AP intake (it always did for no-reply senders; v1.11 makes it the default for replyable senders too).
>
> **Impact on prior closes.** Any bucket 4 or B9-signs-invoice ticket closed by this skill before 2026-05-01 may have failed to deliver the invoice PDF to `invoices@vixxo.com`. If invoices appear "missing" from AP intake even though the Freshdesk ticket is closed with `invoices-bcc` tag, re-forward via `POST /api/v2/tickets/{id}/forward` to `invoices@vixxo.com` from the closed ticket and add an internal note recording the re-forward. The 2026-05-01 remediation tag is `v1.11-remediation-2026-05-01`.

If a later rule also strongly matches one of rules 1–7, set the `ambiguity_flag` to the secondary match so the operator can review.

### Rule 0 — Phishing / security screen (pre-triage)

AP help desks are a high-value target for invoice fraud. Before applying rules 1–7, check the ticket for phishing indicators. If any **strong indicator** fires, or two or more **soft indicators** fire together, classify as bucket 0 (suspected phishing / security) and stop.

**Strong indicators (any one → bucket 0):**

- Request to **change a supplier's remit-to / banking / ACH / wire information**, especially with urgency ("please update before next run", "we changed banks"). This is the #1 AP phishing pattern.
- **Sender domain spoofs Vixxo** or a known SP (lookalike domains like `vixxo-payments.com`, `vixxo.co`, `vixx0.com`, or an SP domain with a one-character difference).
- **From-address / Reply-To address mismatch** where the reply-to points at a free webmail or unrelated external domain.
- **Dangerous attachment type:** `.exe`, `.scr`, `.iso`, `.hta`, `.js`, `.vbs`, `.lnk`, `.msi`, `.bat`, `.cmd`, double-extension files (`invoice.pdf.exe`), password-protected archives, macro-enabled Office docs (`.docm`, `.xlsm`, `.xlsb`) from a sender not in the established SP list.
- **Embedded link** to a non-Vixxo / non-VixxoLink credential page ("log in to view your payment", "click here to confirm your banking details") pointing to an unfamiliar domain.

**Soft indicators (any two → bucket 0):**

- Generic greeting ("Dear Supplier", "Dear Sir/Madam") with urgent payment language.
- Unusual urgency or threats ("must be processed today", "legal action if not paid").
- HTML body styled to look like a Vixxo/VixxoLink notification but sent from an external domain.
- SP name in the body does not match any SP in Gateway (when this is easy to confirm without doing a full research pass).
- Requester email domain does not match the SP's name / prior correspondence pattern on file.
- Unexpected attachment from a sender whose prior tickets never included attachments of this type.

**Action for bucket 0 — do not do any of the following:**

- Do NOT open, preview, or download the attachment to "see what's in it". Rely on filename, sender, and ticket metadata.
- Do NOT click any link in the body.
- Do NOT pull Gateway data for the SR — the SR # itself may be fabricated.
- Do NOT draft a reply. Any reply to a phishing sender confirms the address is monitored.
- Do NOT assign to a normal AP agent.

**Action for bucket 0 — do these:**

- Flag in the triage report as `🚩 SUSPECTED PHISHING` with the specific indicators that fired.
- Recommend escalation to Vixxo IT / security (the operator routes it according to Vixxo's current incident process — if that process isn't documented in this skill, surface that gap to the operator so they can add it).
- Recommend the ticket be set to a holding status (e.g., Pending with an internal note) rather than replied to.
- If the operator confirms the ticket is NOT phishing after review, they can explicitly re-classify it and the skill will fall through to rules 1–7.

### Rule 0b — Onboarding / vendor-setup screen (pre-triage, added 2026-04-27, v1.6)

Evaluate immediately after Rule 0. If it fires, classify as **B6-onboarding** (action `keep-open-onboarding`) and **stop** — do **not** fall through to rules 1–7. Onboarding tickets routinely contain words like "remittance", "invoice", "payment", "ACH", or "setup" and will be mis-routed to bucket 5 (remittance) or bucket 4 (invoice submission) if any keyword tree gets to them first. The 2026-04-27 audit found 13 onboarding tickets that had been mis-closed this way (10 as B5-remittance, 3 as B4-invoice).

**Strong indicators (any one → B6-onboarding, regardless of other matches):**

- Subject or body contains any of (case-insensitive, whole-word): `\bonboarding\b`, `\bonboard\b`, `\bonboarded\b`, `\bnew vendor\b`, `\bnew supplier\b`, `\bvendor setup\b`, `\bsupplier setup\b`, `\bvendor registration\b`, `\bvendor packet\b`, `\bsupplier packet\b`, `\bnew provider\b`, `\bprovider setup\b`, `\bset up (as|a) (vendor|supplier|provider)\b`, `\bbecome a vendor\b`, `\bbecome an? supplier\b`, `\bSAP onboarding\b`, `\bvendor portal access\b`, `\bsupplier portal registration\b`.
- Subject is just `SAP` or `SAP setup` or `SAP vendor` (we have observed this exact pattern from internal Vixxo systems forwarding new-vendor ERP setup requests).
- Subject or body contains "Onboarding with Vixxo", "Onboarding - Vixxo", "FW: Onboarding", "Re: Onboarding".

**Soft indicators (two or more together → B6-onboarding):**

- Body asks how to "get started", "get set up", "begin doing work", "submit our first invoice", "register as a supplier".
- Sender has no prior tickets in the SPM queue AND no SR number anywhere in the body AND no invoice attachment AND the body discusses banking / W-9 / direct deposit / payment setup paperwork.
- Subject mentions a customer name (Boyd, PetSmart, Ulta, etc.) PLUS the words "new", "setup", "interested", or "introducing".

**Tie-breakers when remittance or invoice keywords ALSO appear:**

- If both onboarding indicators AND `\bremittance\b` appear, **onboarding wins.** Onboarding inquiries often ask "where will remittance be sent" — they're describing the future state, not requesting access to past remittance. Bucket 5 is for SPs who already have an active payment relationship and need access to historical remittance data; bucket B6-onboarding is for SPs who don't yet have one.
- If both onboarding indicators AND an invoice attachment appear, **onboarding wins** unless the body is a clean SR-referenced invoice submission. A common pattern is a new SP attaching a sample invoice as part of their setup packet (templates, contract addenda) — this is NOT a B4 invoice submission. The signal: no SR number in the body, sender is not yet in Gateway as an active SP, body is conversational rather than transactional.
- If the onboarding screen and another rule both fire and you can't tell which wins, **route to B6-onboarding** rather than B4 or B5. Mis-routing to onboarding is recoverable (Account Team will redirect); mis-routing onboarding to remittance closes the ticket with a generic VixxoLink redirect that does not help the SP and creates the confusion we just had to clean up.

**Action — `keep-open-onboarding`:**

1. `conversations_manage create_note` (private) — internal note: `Bucket B6-onboarding (new SP / vendor setup / SAP onboarding inquiry). Routed to Account Team / SP Onboarding via tags. Ticket left OPEN — do not close from the AP side. Onboarding team picks up by tag.`
2. `PUT /tickets/{id}` — apply tags: `sp-onboarding`, `account-team-routed`. **Leave `status=2` (Open). Do NOT set status. Do NOT post a customer-facing reply. Do NOT BCC `invoices@vixxo.com` — onboarding is not an AP function.**

**Why no customer-facing reply:** the SP Onboarding team owns the SP-facing message. AP doesn't know the customer-specific onboarding path (which packet to send, who their assigned account manager is, what NTE thresholds apply, whether the SP needs an MSA before getting Gateway credentials), so an AP-side ack would be wrong-by-default.

**Why leave Open:** the SP Onboarding / Account Team subscribes to the `sp-onboarding` and `account-team-routed` tags and pulls Open tickets directly from the SPM view. Closing from the AP side removes them from the onboarding queue.

**Audit reconciliation (2026-04-27):** 13 historical tickets that had been mis-classified as B5-remittance (10) or B4-invoice (3) were reopened on 2026-04-27, tagged `onboarding-misroute-2026-04-27` + `sp-onboarding` + `account-team-routed`, and noted with the misroute explanation. Affected ticket IDs: 32276, 33542, 35445, 37863, 38133, 38368, 39756, 39813, 39906, 40012 (B5-remittance misroutes); 35988, 37933 (B4-invoice misroutes). Ticket 39756 was already Open (auto-reopened by SP reply) so received tags + note only; the other 11 were reopened from `status=5`.

**No-reply guardrail interaction:** moot — `keep-open-onboarding` never posts a customer-facing reply, so the no-reply check has nothing to suppress.

### Rule 0c — SAP ticket screen (pre-triage, added 2026-04-28, v1.7)

Evaluate immediately after Rule 0b (onboarding). If it fires, classify as **B7-sap** (action `keep-open-sap`) and **stop** — do **not** fall through to rules 1–7. SAP tickets — whether they're SP invoices that reference a SAP PO, customer-side SAP onboarding requests that didn't match Rule 0b, or internal Vixxo ERP-integration messages — are **not closed from the AP side** going forward. They require Account Team / ERP-Ops review before any customer-facing action. Closing them with an ack + BCC to `invoices@vixxo.com` (the previous v1.0–v1.6 behavior) was observed to interleave ERP-specific SR context with normal AP intake, which doesn't surface to the right downstream owner.

**Strong indicators (any one → B7-sap):**

- Subject contains `\bSAP\b` as a whole word (case-insensitive). Examples observed on this tenant:
  - `Paid only Invoice SAP - BCP 39258 Marysville, CA`
  - `7-Eleven 39637 - BCP Remodel - GC Invoice 8857 - SAP PO 932166 All Four - Payment status`
  - `Recall: 7-Eleven 39637 - BCP Remodel - GC Invoice 8857 - SAP PO 932166 All Four - Payment`
  - `SAP`
  - `RE: Vixxo Fleet Farm 3310 Blaine SAP On Boarding 3/26/26`
- Body contains `SAP PO <number>`, `SAP invoice`, `SAP vendor`, `SAP onboarding`, `SAP setup`, `SAP portal`, `SAP ID`, `SAP registration`, `uploaded to SAP`, `SAP routing`, `SAP interface`, `SAP gateway`.
- Attached document filename contains `SAP` (e.g., `SAP_PO_932166.pdf`, `SAP-onboarding-packet.xlsx`).

**Scope note — "SAP" is a three-letter acronym so literal whole-word matching is required.** Do not match inside other words (e.g., `SAPhire`, `misapply`, `sapphire`). Regex `(?i)\bSAP\b` is correct.

**Tie-breakers:**

- SAP + onboarding indicators → both Rule 0b (B6-onboarding) and Rule 0c (B7-sap) would fire. **B7-sap wins** — SAP onboarding needs the ERP-integration owner, not just the generic SP Onboarding team. The internal note names both routing targets so Account Team can hand off appropriately.
- SAP + invoice attachment / SR number in body → **B7-sap wins over B4-invoice.** The SP invoice that references a SAP PO is not a normal AP-intake item — the ERP side needs to reconcile before AP processes.
- SAP + any other bucket (remittance, aging, COI, etc.) → **B7-sap wins** unless the SAP reference is incidental (e.g., SP mentions in passing "we use SAP internally" while asking about an unrelated VixxoLink password reset). When in doubt, route to B7-sap — the worst case is the Account Team reroutes the ticket, which is cheaper than a wrong-owner close.

**Action — `keep-open-sap`:**

1. `conversations_manage create_note` (private) — internal note: `Bucket B7-sap (SAP-related ticket — invoice / PO reference / onboarding / ERP integration). Per v1.7 policy, SAP tickets are NOT closed from the AP side. Routed to Account Team / ERP-Ops via tags. Ticket left OPEN. If this is an SP invoice with a SAP PO, the ERP side needs to reconcile the PO before AP processes the invoice. If this is SAP onboarding, SP Onboarding + ERP jointly own the setup.`
2. `PUT /tickets/{id}` — apply tags: `sap-ticket`, `account-team-routed`, and **additionally** `erp-ops` if the body references a SAP PO or interface/routing issue (not just mentions SAP in passing). **Leave `status=2` (Open). Do NOT set status. Do NOT post a customer-facing reply. Do NOT BCC `invoices@vixxo.com`.**

**Why no customer-facing reply and no BCC to `invoices@vixxo.com`:** SAP invoices need ERP-side reconciliation before AP can intake them — BCC'ing invoices@ while the SAP PO is still being aligned pollutes the AP intake queue with items that aren't ready to process. The SP does not need an AP-side ack; the Account Team handles SAP-specific SP communication because they have the customer-specific PO context AP doesn't.

**Audit reconciliation (2026-04-28):** 5 SAP invoices were previously closed as B4-invoice with BCC to `invoices@vixxo.com` (Batches 11 and 23). Ticket IDs: 32278, 32281, 32285, 40400, 40405. Plus 1 B3-aging close (ticket 30466, subject `SAP`) and 1 X-admin-route close (ticket 33504, Fleet Farm SAP onboarding). Operator can review `tmp\sap_invoice_bcc_audit.csv` and decide whether to reopen these 7 historically closed SAP tickets and apply the B7-sap tags (same pattern as the 2026-04-27 onboarding-misroute reconciliation).

**No-reply guardrail interaction:** moot — `keep-open-sap` never posts a customer-facing reply.

### Rule 0d — Vendor-hold notification screen (pre-triage, added 2026-04-29, v1.8)

Evaluate immediately after Rule 0c (SAP). If it fires, classify as **B8-vendor-hold** (action `keep-open-vendor-hold`) and **stop** — do **not** fall through to rules 1–7. These are internal Vixxo automation notifications generated by KnowledgeSync when an SPM work-order is auto-assigned to a vendor whose Workday status is `On Hold`, `WDOnHold`, or `Do Not Use`. They are SPM-operations work items (the work order needs to be reassigned to a different vendor, or the vendor's hold status needs to be reconciled in Workday) — they are **not** SP-facing AP work and **never** require an AP-side response, BCC, or close.

Closing them as B7-manual or B5-remittance (the v1.0–v1.7 default-fallback path) silently removed them from the SPM Open queue without anyone reassigning the work order, which leaves the underlying customer SR stranded. Multiple instances were observed in the 2026-04-29 batch (16/270 tickets, 5.9% of the unrouted queue).

**Strong indicators (any one → B8-vendor-hold, regardless of other matches):**

- `requester_email` is `knowledgesync@vixxo.com` (or any `@vixxo.com` automation account on KnowledgeSync) AND the subject starts with one of:
  - `Vendor on Hold assigned to Open Ticket notification:`
  - `Vendor with Workday Status of WDOnHold assigned to Open Ticket notification:`
  - `Do Not Use Vendor assigned to Open Ticket notification:`
- Body matches the KnowledgeSync template: `The following ticket has been assigned a vendor that is on hold:` / `The following ticket has been assigned a vendor that has the status of WDOnHold:` / `Parent Account: ... SubType: Do Not Use`, followed by an `Account Name`, `Ticket Number` (Gateway WO), `Ticket Status`, `Ticket Substatus`, and parent-account block.
- Regex shortcut: `(?i)(Vendor (on Hold|with Workday Status of WDOnHold)|Do Not Use Vendor) assigned to Open Ticket notification`.

**Scope note:** the requester must be the internal KnowledgeSync automation. An external SP writing "we are on hold, please remove us" is **not** B8-vendor-hold — that's a B6-onboarding (vendor-maintenance) or surface-exception. Only the internal-automation pattern routes here.

**Tie-breakers:**

- Vendor-hold notification + SAP indicators in the body → B7-sap wins (the body may name a SAP PO; ERP-Ops needs to see those alongside the KnowledgeSync feed).
- Vendor-hold notification + onboarding indicators → B6-onboarding wins (rare, but if a new vendor is auto-flagged hold during setup, SP Onboarding owns the resolution).
- Vendor-hold notification standing alone → B8-vendor-hold.

**Action — `keep-open-vendor-hold`:**

1. `conversations_manage create_note` (private) — internal note: `Bucket B8-vendor-hold (KnowledgeSync auto-notification: vendor with hold/WDOnHold/Do-Not-Use status was auto-assigned to Open work order WO #<extract>). Per v1.8 policy, vendor-hold notifications are NOT closed from the AP side. Routed to Account Team / SPM Ops via tags. Ticket left OPEN. Action required: SPM Ops reassigns the work order to an active vendor, OR Account Team reconciles the vendor's Workday status. AP has no role in either path.`
2. `PUT /tickets/{id}` — apply tags: `vendor-hold-notify`, `account-team-routed`. **Leave `status=2` (Open). Do NOT set status. Do NOT post a customer-facing reply. Do NOT BCC `invoices@vixxo.com`.**

**Why no customer-facing reply:** the requester is `knowledgesync@vixxo.com` — an internal automation that does not consume Freshdesk replies. Replying to it generates a no-op autoresponder loop and clutters the audit trail. There is no external SP to acknowledge.

**Why leave Open:** Account Team / SPM Ops subscribes to the `vendor-hold-notify` and `account-team-routed` tags and pulls Open tickets directly from the SPM view. Closing from the AP side removes them from the ops queue and the underlying work order remains stranded.

**No-reply guardrail interaction:** moot — `keep-open-vendor-hold` never posts a customer-facing reply, and `knowledgesync@vixxo.com` would be flagged as no-reply by the v1.4 guardrail anyway (no human inbox monitors it).

### Rule 0e — Signs & Lighting internal-sender screen (pre-triage, added 2026-04-30, v1.10)

Evaluate immediately after Rule 0d (vendor-hold). If it fires, classify into one of two sub-buckets — **B9-signs-invoice** or **B9-signs-sp-update** — based on content, post an AP-side confirmation reply to the internal Vixxo sender, and **stop** — do **not** fall through to rules 1–7.

This rule exists because internal Vixxo Signs & Lighting traffic (LSI Signs, Vixxo Signs, Vixxo Lighting business unit, sign shop coordination) routinely lands in the SPM AP queue but follows a different routing pattern than external SP traffic: the internal sender is the right point of contact for confirmation (so we ack them directly), invoices need to flow to the AP intake mailbox like normal bucket 4, and SP-update content (coverage, roster, contact, performance, rate updates for Signs SPs) needs Vendor Maintenance — not the Account Team — to action. Falling through to bucket 4 would close the SP-update variant prematurely, and falling through to bucket 6 (manual) would lose the time-sensitive invoice variant.

**Trigger (ALL conditions must hold):**

1. `requester_email` ends with `@vixxo.com` (internal Vixxo sender). External SP emails do not match this rule even if they discuss Signs business — those follow normal bucket 2/3/4 routing.
2. The combined match surface (subject + full body + conversation history + attachment filenames, treated as one text blob) matches **both** of the following regexes (case-insensitive):
   - **Signs side:** `(?i)\bsigns?\b` — matches "sign" or "signs" anywhere (also satisfied by phrases like "sign shop", "Vixxo Signs", "LSI Signs").
   - **Lighting side:** `(?i)\blighting\b` — matches "lighting" anywhere (also satisfied by phrases like "Vixxo Lighting", "LSI Lighting").
3. Both sides must be present in the same ticket. A ticket containing only "sign" or only "lighting" does **not** match this rule and falls through to rules 1–7.

**Scope note — AND semantics, tightened 2026-04-30.** The original v1.10 draft used OR semantics (any of `\bsigns?\b` / `\blighting\b` / `\bLSI\b` / `\bsign shop\b` / etc. fires), which over-matched on routine internal emails using "sign" or "lighting" generically ("please sign off on...", "lighting in the breakroom"). The current AND requirement (both `\bsigns?\b` AND `\blighting\b` present) eliminates that false-positive class — a generic "please sign" email would not also contain "lighting", and a "breakroom lighting" email would not contain "sign(s)". The combined phrase "Signs and Lighting" / "Signs & Lighting" naturally satisfies both regexes in one match. Standalone variants — `LSI` alone, `Vixxo Signs` alone, `Vixxo Lighting` alone, `sign shop` alone — no longer fire on their own; if those appear without the other side present, the ticket falls through to normal triage.

**Edge case:** an internal email saying "please sign off on the lighting estimate" technically matches both regexes and would route to B9. This is acceptable — the email references signs/lighting work AND comes from an internal sender, so the AP-side confirmation + downstream routing (invoices@ for invoice content, Vendor Maintenance for SP updates) is the right behavior. If post-batch audit shows this edge case mis-routes frequently, escalate to per-ticket review rather than further regex tightening.

**Sub-bucket disambiguation — invoice vs SP update:**

Route to **B9-signs-invoice** if any of:

- Body explicitly references an invoice number, "invoice attached", "invoice for SR <number>", or "submitting invoice".
- An attachment is present whose filename suggests an invoice (`invoice`, `inv`, `bill`, `statement` in the filename, or PDF + dollar amount in the body).
- Body asks for payment, references aging, or requests AP intake / processing.
- Subject contains `invoice`, `billing`, or `payment`.

Route to **B9-signs-sp-update** if any of:

- Body discusses SP info changes (contact, address, hours, banking handled internally — not BEC, since sender is internal Vixxo).
- Body discusses SP coverage, area, LOS, or service-schedule changes for the Signs program.
- Body discusses SP performance, ratings, qualifications, or quality issues.
- Body discusses SP roster changes (adding/removing SPs from the Signs program), rate updates, or labor-type changes.
- No invoice attachment AND no payment-related ask.

**Tie-breakers:**

- Both invoice and SP-update indicators present → **B9-signs-invoice wins**. The AP intake path is time-sensitive (an invoice not routed to `invoices@vixxo.com` ages); `invoices@` can re-route to Vendor Maintenance if the content is actually an SP update.
- Neither set of indicators clear → **B9-signs-sp-update wins**. Vendor Maintenance can absorb the ambiguity; routing an SP-update to AP intake creates noise in `invoices@vixxo.com` that AP cannot action.
- Rule 0e + Rule 0c (SAP) both fire → **B7-sap wins** (per Rule 0c precedence). SAP-related Signs business needs ERP-Ops first.
- Rule 0e + Rule 0b (onboarding) both fire → **B6-onboarding wins** (per Rule 0b precedence). New-vendor Signs onboarding goes to SP Onboarding.
- Rule 0e + Rule 0 (phishing) both fire → **bucket 0 wins**. A spoofed `@vixxo.com` sender with banking-change language is BEC and must not get a confirmation reply.

**Action — `close-signs-invoice` (B9-signs-invoice):**

1. `POST /api/v2/tickets/{id}/forward` (REST API) to `to_emails: ["invoices@vixxo.com"]` — carries the original message + invoice PDF attachments to AP intake via `include_original_attachments: true` (default). Body is a brief AP-focused header (SR / customer / SP / **SP NTE only** / invoice # if extractable). This is the AP intake leg and must fire first.
2. `conversations_manage create_reply` to the internal sender (Appendix C-1) — **no BCC** (the forward in step 1 already handled AP intake). The internal sender IS the ticket requester (their `@vixxo.com` address), so the default `/reply` recipient is correct — no `to_emails` override needed.
3. `conversations_manage create_note` (private) — internal note: `Bucket B9-signs-invoice (Signs & Lighting internal-sender invoice content). Forwarded original message + attachments to invoices@vixxo.com for AP intake. Confirmation reply sent to internal sender. Closing per v1.11 policy.`
4. `PUT /tickets/{id}` — close (status=5) with the canonical close body. Required custom_fields:
   - `type`: `Invoice Support`
   - `cf_sp`: extracted SP name from body, or `Vixxo Signs (internal)` if not extractable
   - `cf_sr`: SR# if present, else `Invoice #<num>` or `N/A`
   - `cf_amount`: extracted dollar amount or `N/A`
   - `cf_sr_required`: `Yes` if a real Gateway SR is referenced, else `No`
   - `cf_customer`: `Other` (Signs & Lighting is an internal Vixxo business unit, not a customer on the cf_customer whitelist)
   - `cf_type_of_request`: `Submit an Invoice for manual entry`
   - `tags`: `signs-lighting`, `vixxo-signs-internal`, `invoices-forward` (renamed from `invoices-bcc` in v1.11)

**Action — `keep-open-signs-sp-update` (B9-signs-sp-update):**

1. `conversations_manage create_reply` — AP-side confirmation reply to the internal sender (Appendix C-2). **No BCC** to `invoices@vixxo.com` — this is not invoice content and AP has no role in the action.
2. `conversations_manage create_note` (private) — internal note: `Bucket B9-signs-sp-update (Signs & Lighting internal-sender SP-update content). Confirmation reply sent to internal sender. Routed to Vendor Maintenance via tags. Ticket left OPEN per v1.10 policy.`
3. `PUT /tickets/{id}` — apply tags only: `signs-lighting`, `vixxo-signs-internal`, `vendor-maintenance`, `signs-lighting-sp-update`. **Leave `status=2` (Open). Do NOT set status. Do NOT BCC `invoices@vixxo.com`.**

**Why an AP-side confirmation reply (departure from B5-coi / B6-onboarding / B7-sap / B8-vendor-hold "no reply" pattern):** the internal sender is a Vixxo employee waiting for AP to acknowledge that their handoff was received. Silent routing (note + tags only) leaves the sender wondering whether their email was acted on, prompting follow-up tickets. The keep-open-* patterns suppress replies because the next action is owned by a non-AP team and AP can't make accurate commitments — but for Signs & Lighting traffic, the AP-side ack is "we received this and routed it to <X>", which AP CAN commit to without overstepping. The reply is a routing receipt, not a substantive answer.

**SP-NTE-only rule interaction (v1.7):** the SP-NTE-only rule still applies — even though the recipient is an internal Vixxo sender, the AP-side confirmation reply must not include customer NTE in case the thread is later forwarded outside Vixxo (defense in depth). SP NTE may appear if directly relevant; customer NTE goes in the internal note only.

**No-reply guardrail interaction (v1.4):** if the internal sender is itself a no-reply automation (`noreply@vixxo.com`, `notifications@vixxo.com`, `knowledgesync@vixxo.com`), the no-reply guardrail still suppresses the customer-facing reply. The note + tags + close (B9-signs-invoice) or note + tags + leave-open (B9-signs-sp-update) still fire. For B9-signs-invoice with a no-reply internal sender, replace `/reply+BCC` with `POST /api/v2/tickets/{id}/forward` to `invoices@vixxo.com` (per the v1.4 guardrail) so the AP intake leg still happens. (Note: KnowledgeSync senders are caught by Rule 0d before reaching here, so this case is rare in practice.)

### SP-NTE-only rule — customer NTE is internal only (added 2026-04-28, v1.7)

**Rule:** any customer-facing reply drafted by this skill (buckets 2, 3, 4, 5) **must** reference **only the SP NTE**, never the customer NTE. Customer NTE is internal-audit data used by AP, Finance, and Account Team to assess budget compliance; exposing it to the SP discloses customer-side commercial terms the SP is not entitled to see.

**Where NTE may appear:**

| Context | Customer NTE | SP NTE |
|---|---|---|
| SP-facing reply body (all buckets) | **Never** | OK to include, only if directly relevant (e.g., "SR NTE is $X.XX, invoice is within") |
| Internal private note to Account Team / AP | Include with full context | Include with full context |
| Forward to `invoices@vixxo.com` (bucket 4, B9-signs-invoice) — body header | **Never** — the forward header is operator-authored AP-intake context and goes to the same place the original message goes; customer NTE has no place in either. AP can look up customer NTE from Gateway by SR when needed. | OK (SR / SP / SP NTE / completion summary) |
| Mode B Deep-Dive output "Gateway detail" section | Marked INTERNAL — operator-facing only, never pasted verbatim into a reply | Marked operator-facing, OK to cite in draft |

**Why this matters:** Vixxo's customer contracts frequently include NTE values set at commercially-sensitive thresholds — disclosing them to an SP effectively tells that SP "Vixxo's customer has authorized up to $X for this work." That information can leak back into the SP's future bid strategy (bidding up to, but not over, the customer NTE even when the actual cost is lower), damaging the customer relationship and Vixxo's vendor-management value.

**Drafting guidance for bucket 4 (the main SP-facing reply bucket):** the ack summary should include SR number, customer name, SP name, SP NTE (if present), scheduled/actual completion date, and a brief "invoice received, processing" line. If the customer NTE is material to the reply (e.g., the invoice is slightly over customer NTE and the SP is asking about payment), **do not** reference the customer NTE in the body — instead (a) put the customer NTE discussion in the internal note only, and (b) switch the ticket action to `pending-hold-accounting` or escalate to the Account Team so a human can have the customer-NTE conversation with the SP appropriately.

**Implementation check in draft-review:** before sending any SP-facing reply, the skill must verify the draft does not contain the literal string "customer NTE" and does not contain a dollar-valued NTE reference that came from `ServiceRequest.customer_nte` (vs `ServiceRequest.sp_nte`). If either check fails, halt and surface to the operator.

**No-reply guardrail interaction:** independent — the SP-NTE-only rule applies to the *content* of replies; the no-reply guardrail controls *whether* the reply is sent. Both evaluate separately and both must be satisfied for a write to fire.

### Rules 1–7

| # | Bucket | Triggers (subject / body / attachments) | Action |
|---|---|---|---|
| 1-close | Thank you / auto-reply | (a) A clean courtesy-only message such as "Thanks", "Thank you", "Appreciate it", "Got it", or "Sounds good" **AND no attachments present** **AND no request for status/update/next step**; OR (b) auto-reply indicators: subject prefixed "Automatic reply:", "Auto-reply:", "Out of Office:", "Out of the Office:"; body containing "I am out of the office", "I will respond when I return", "on vacation until"; or standard auto-responder headers (`Auto-Submitted: auto-replied`, `X-Auto-Response-Suppress`). | Recommend close. No draft. No Gateway. **Exceptions:** (1) if a ticket looks like a "thank you" but has an attachment, fall through to bucket 4 (SP is almost certainly also submitting an invoice); (2) if the body thanks Vixxo but also asks for an update, status, ETA, action, response, or expresses frustration about waiting, classify as **1-follow-up**, not 1-close. |
| 1-follow-up | SP update chase / no-attachment status request | A reply that may include "thanks" or polite language but is actually asking for movement, e.g. "any update?", "following up again", "still waiting", "haven't heard back", "please advise", "need an update", "second request", "why has this not been approved/paid?", "what else is needed?", "we have been waiting", or similar. This bucket includes SP/provider payment, invoice, NTE-approval, rejection, or SR-status questions when **no invoice/supporting attachment is present**. Tone signals include frustration, urgency, repeated outreach, concern that the SP has been ignored, or pressure caused by delayed payment / unresolved work. | Keep ticket Open. Gateway context may be pulled to enrich the internal note, but it must not convert the ticket into a close. Route to the AP Team with tags `ap-team-routed` and `sp-update-request`, and add a private note summarizing the SP ask, SR/invoice refs, Gateway findings if checked, and the specific AP next action. Draft a warm SP-facing reassurance reply only if the operator approves. Do not close after replying. |
| 2 | Rejected invoice (*from Vixxo → SP*) | Subject or body language like "Reject", "Rejected Invoice", "Notice of Rejected Invoices" — these are Vixxo notifying an SP that their invoice was rejected, or an SP asking *why* their invoice was rejected. | Gateway research. Draft customer reply with rejection reason and corrective path. If reason is unclear from Gateway, escalate to Account Team with a drafted internal note. **Exception:** if the body/description contains "Please reject this invoice" or variants ("please reject invoice #…", "can you reject the invoice I submitted", "we need this invoice rejected because we made a mistake"), this is an SP or Ops asking Vixxo *to* reject an invoice the SP themselves submitted in error. Route to **bucket 6** (account maintenance / exception) instead of bucket 2. |
| 3 | Payment follow-up / aging | "Payment reminder", "Payment status", "Outstanding invoices", "Statement", "Past due", "Aging", "Overdue" | Gateway research. Draft customer reply with payment status (paid / pending / on hold / rejected) and any reason codes. **Exception:** if the ticket is an SP/provider asking for an update or asking why an SR/invoice/NTE approval has not moved forward and there are no attachments to process, classify as **1-follow-up** instead. That work needs AP Team ownership, an open ticket, and routing tags; closing with a note does not move it forward. |
| 4 | SR# only / SR# + attachment / invoice submission | SR number alone, "Submitting Invoices", "Invoice attached", "Delinquent SC Invoice", or a short body + an invoice-looking attachment (PDF with line items, amounts, invoice #). | Gateway research. Three outputs, all gated behind a single operator approval, fired in this canonical order: **(a) `POST /api/v2/tickets/{id}/forward` to `to_emails: ["invoices@vixxo.com"]`** with a brief AP-focused header (SR / customer / SP / **SP NTE only** / completion-date / invoice # if extractable). The `/forward` endpoint defaults `include_original_attachments: true`, which carries the SP's invoice PDF (and any other attachments) to the AP intake mailbox — this is what AP actually needs to process the invoice. **(b)** brief customer acknowledgment reply addressed to the SP/requester via `POST /reply` (or `conversations_manage create_reply`); **no BCC** to `invoices@vixxo.com` on this reply (the forward in (a) already handled AP intake — adding a BCC duplicates the notification with a payload-less copy). **(c)** internal private note to Account Team with SR context. **NEVER include customer NTE in either the SP-facing reply body OR the forward header** (see SP-NTE-only rule in v1.7 — customer NTE is internal-audit data that goes in the internal note only; invoices@ looks up customer NTE by SR from Gateway when needed). No CC on the customer reply. Operator must explicitly approve all three writes together; no silent forwards. **Implementation note (v1.11, 2026-05-01):** the prior v1.0–v1.10 implementation used `create_reply` with `bcc_emails: ["invoices@vixxo.com"]` as a stand-in for forward, on the assumption that the BCC carried the same content. Operator audit on 2026-05-01 (WERCS batch) confirmed this assumption was wrong — Freshdesk's `/reply` endpoint sends only the reply body to BCC recipients; the **original attachments are not carried**. AP was receiving acknowledgments without the actual invoice PDFs and could not process them. The fix is to use `POST /api/v2/tickets/{id}/forward` (REST API direct, since the MCP does not expose a forward action) for the AP intake leg. The MCP `conversations_manage create_reply` is still the right tool for the SP-facing ack. See "v1.11 — AP-intake forward must carry attachments" changelog below for the remediation history. |
| 5 | Remittance | "Remittance" | Draft the VixxoLink canned reply (see Canned Replies below). If this ticket has already been responded-to with VixxoLink and the provider is still stuck, route to Accounting. |
| 6 | Account maintenance / exception | "change", "update", "missing", "error", "duplicate", "help", "question"; also any SP-initiated "please reject this invoice" request per bucket 2's exception. | Flag for manual human handling. No draft. No Gateway. **Do not use bucket 6 to close SP/provider status requests.** If the requester is asking AP for movement on payment, rejection, NTE approval, SR approval, or "what else is needed" and no attachment is present, route as **1-follow-up** with AP Team tags and leave Open. |
| 7 | None of the above | — | Flag for manual triage. No draft. No Gateway. |

**Why the bucket 1 and bucket 2 exceptions matter:** the most common mis-routes on this queue are (a) auto-closing a "thanks" ticket that had an invoice attached (losing an invoice submission), (b) auto-closing a polite but frustrated follow-up that actually needs Account Team attention, and (c) treating an SP's "please reject my invoice" request as a Vixxo-originated rejection notice and sending the wrong drafted reply. All are relationship-damaging. The extra checks above prevent them.

**Attachment handling across modes:** during Mode A triage, don't download or render attachments — use filename, sender, and ticket metadata to inform classification and phishing screen. Mode B may legitimately need attachment content to analyze a submitted invoice, but only *after* rule 0 has cleared the ticket. If in Mode B you encounter an attachment type listed as a strong phishing indicator, stop and re-route to bucket 0 even if the ticket previously classified as something else.

---

## Per-Bucket Drafting Behavior

| Bucket | Draft type | Tone |
|---|---|---|
| 0 | None. Escalate to IT/security per Vixxo incident process. | — |
| 1-close | None | — |
| 1-follow-up | Private note to AP Team plus tags `ap-team-routed` and `sp-update-request`; keep Open and do not set Resolved/Closed. Optional customer-facing reassurance reply only after operator approval. | Warm, calming, accountable |
| 2 | Customer-facing reply with rejection reason, required correction, and path forward | Relationship-first, specific, accountable |
| 3 | Customer-facing reply with payment status and any reason codes | Relationship-first, definitive where possible |
| 4 | **Three writes, fired in this order:** (a) `POST /api/v2/tickets/{id}/forward` to `invoices@vixxo.com` (REST API; the MCP does not expose forward) — carries original SP message + invoice PDF attachments via `include_original_attachments: true` (default). Body is a brief AP-focused header: SR / customer / SP / **SP NTE only** / completion-date / invoice # if extractable. (b) Customer acknowledgment to SP/requester via `create_reply` — **no BCC** (the forward in (a) already handled AP intake). Body must include SR / customer / SP / **SP NTE only** / completion-date summary. **Customer NTE is forbidden in the SP-facing reply body AND in the forward header** — see SP-NTE-only rule; customer NTE belongs in the internal note only. (c) Internal private note to Account Team with full SR context **including customer NTE, SP NTE, delta, and any Gateway anomalies**. All three writes in one approval batch, no CC on (b). | Brief, professional |
| 5 | VixxoLink canned redirect (verbatim below) | Warm, self-service oriented |
| 6 | None | — |
| 7 | None | — |
| B10-manual-entry-vint | Same as bucket 4: AP-intake `/forward` to `invoices@vixxo.com`, requester acknowledgment when replyable, internal private note, and close. Add the VINT routing change in the final update: `group_id:159000486559` plus tags `manual-entry-invoice` + `vint-routed`. | Brief, professional |
| B9-signs-invoice | **Three writes (v1.11):** (1) `POST /forward` to `invoices@vixxo.com` (REST API) — carries original message + invoice attachments to AP intake. Body is a brief AP-focused header (SR / SP / SP-NTE-only / invoice # if extractable). (2) AP-side confirmation reply to the internal `@vixxo.com` sender (Appendix C-1) via `create_reply` — **no BCC**. (3) Internal private note for the audit trail. **Customer NTE forbidden** in both (1) and (2) per SP-NTE-only rule. All three writes in one approval batch; close after. | Brief, professional, internal-collegial |
| B9-signs-sp-update | AP-side confirmation reply to the internal `@vixxo.com` sender (Appendix C-2). Body: brief receipt + statement that the SP-update content has been routed to Vendor Maintenance for review. **No BCC.** Internal private note. Tags only — leave Open. | Brief, professional, internal-collegial |

Keep customer drafts short. Providers read these on a phone between jobs. Lead with the answer; put the context second.

---

## Canned Replies

### Appendix A — Bucket 5 — Remittance (VixxoLink redirect)

Use this reply verbatim. Do not paraphrase. It was reviewed and approved by Jim McCarthy on 2026-04-16; alterations would change a message the Accounting team is already coordinated on.

> Hello,
>
> Remittance information is available for you in VixxoLink.
>
> Please log in and navigate to your payment details to view and download the remittance associated with your invoice(s).
>
> If you're unable to locate the information in VixxoLink, please let us know and we can assist further or connect you with our Accounting team.
>
> Thank you,

**Supporting resource (for the operator, and for follow-ups if the provider gets stuck):** the Freshdesk knowledge-base article *Reviewing Payments* walks through the VixxoLink Payments section step-by-step — https://vixxo-helpdesk.freshdesk.com/support/solutions/articles/159000414633-reviewing-payments — share this URL in a follow-up reply if the provider responds that they can't locate the remittance on their own.

### Appendix B — Bucket 1-follow-up — Reassurance reply

Use this as the starting draft when an SP is following up with frustration or concern about an unresolved payment, invoice, rejection, NTE approval, or SR update. Keep the ticket Open and route to the AP Team with tags `ap-team-routed` and `sp-update-request` before or with the reply. Adjust only the bracketed specifics.

> Hello,
>
> Thank you for following up. I understand you've been waiting on an update, and I appreciate your patience while we look into this.
>
> We're checking with the appropriate team now and will follow up as soon as we have more information on [SR / invoice / request].
>
> Thank you,

### Appendix C — Bucket B9 — Signs & Lighting internal-sender confirmation replies

These two drafts cover the v1.10 Signs & Lighting internal-sender pre-screen (Rule 0e). The recipient is an internal Vixxo employee who routed Signs/Lighting traffic into the SPM AP queue; the reply is a routing receipt, not a substantive answer. Adjust only the bracketed specifics.

#### Appendix C-1 — B9-signs-invoice (invoice content variant)

Use when the email contains invoice content (attachment, invoice number, payment ask, billing language). The reply is sent to the internal sender. **AP intake is handled separately via `POST /forward` to `invoices@vixxo.com` (v1.11) — that forward carries the original message and invoice PDF attachments. Do NOT BCC `invoices@vixxo.com` on this reply** (the forward already covered AP intake; a BCC would just duplicate the notification with a payload-less copy). **Do not include customer NTE in the body** — SP-NTE-only rule applies.

> Hello,
>
> Confirming receipt of your Signs & Lighting invoice submission for [SR / invoice #]. The details have been routed to invoices@vixxo.com for AP processing — the AP intake team will pick it up from there.
>
> Thank you,

#### Appendix C-2 — B9-signs-sp-update (SP-update variant)

Use when the email contains SP-update content (coverage, roster, contact, performance, rate, or labor-type change for the Signs program). The reply is sent to the internal sender only — no BCC. The ticket is left Open with `vendor-maintenance` + `signs-lighting-sp-update` tags so Vendor Maintenance picks it up.

> Hello,
>
> Confirming receipt of your Signs & Lighting SP update. The details have been routed to Vendor Maintenance for review. They will follow up directly if any additional information is needed.
>
> Thank you,

---

## Output Format

### Mode A — Triage Report

Inline AND saved to `triage-page-<NN>-<YYYY-MM-DDTHHMM>.md` in the current working folder. Group rows by bucket; within each bucket, order by ticket_id ascending.

```markdown
# AP Triage — Page <N> (<timestamp>)

Queue filter: Status=Open, Agent=<No-Agent-representation>
Ordered oldest-first. Tickets <first>–<last> of page.
QSI AP source tag overlay: add `qsiap-source` to any non-excluded ticket that came from or was forwarded from `qsiap@vixxo.com`.

## Manual-review recipient exclusion — left untouched
| Ticket | Subject | Requester | Matched recipient | QSI AP match | Recommended action |
|---|---|---|---|---|---|
| #### | ... | ... | ksonboarding@vixxo.com | qsiap@vixxo.com in forwarded header / — | Manual review only; no rule classification, Gateway lookup, draft, note, tag, close, or forward |

## Bucket 0 — 🚩 SUSPECTED PHISHING (escalate to security)
| Ticket | Subject | Requester | Indicators fired | Recommended action |
|---|---|---|---|---|
| #### | ... | ... | remit-to change request + external domain | Escalate to IT/security; do not reply; hold ticket |

## Bucket 1-close — Thank you / auto-reply (close)
| Ticket | Subject | Requester | Source tags | Ambiguity | Findings | Recommended action |
|---|---|---|---|---|---|---|
| #### | ... | ... | qsiap-source / — | — | — | Close |

## Bucket 1-follow-up — SP update chase / no-attachment status request (keep open)
| Ticket | Subject | Requester | Source tags | Ambiguity | Findings | Recommended action |
|---|---|---|---|---|---|---|
| #### | ... | ... | qsiap-source / — | SP update request / no attachment | SP has followed up for payment, invoice, NTE approval, rejection, or SR-status movement; no attachment is present to process | Keep Open; tag `ap-team-routed` + `sp-update-request`; private note to AP Team; optional reassurance reply |

## Bucket 2 — Rejected invoice
| Ticket | Subject | Requester | Source tags | Ambiguity | Gateway findings | Recommended action |
|---|---|---|---|---|---|---|
| #### | ... | ... | qsiap-source / — | — | SR: ..., Invoice: ..., reason: ... | Draft ready — review and send |

... (and so on through buckets 3–7)

## Bucket B10-manual-entry-vint — Manual-entry invoice request (move to VINT)
| Ticket | Subject | Requester | Source tags | Ambiguity | Findings | Recommended action |
|---|---|---|---|---|---|---|
| #### | ... | ... | qsiap-source / — | — | Ticket explicitly requests manual invoice entry | Follow bucket 4: Gateway if SR present; forward original message + attachments to `invoices@vixxo.com`; send requester ack if replyable; add internal note; change group to VINT (`group_id:159000486559`); tag `manual-entry-invoice` + `vint-routed`; close |

## Counts
- Bucket 0 (🚩 phishing): N
- Bucket 1-close (close): N
- Bucket 1-follow-up (keep open / AP Team): N
- Bucket 2 (rejected): N
...
- Bucket B10-manual-entry-vint (move to VINT): N
- Manual-review recipient exclusions: N
- QSI AP source matches: N
- Skipped Gateway (manual-review-recipient-exclusion/0/1-close/1-follow-up/5/6/7): N tickets
- Gateway calls this page: N
```

Then ask: "Continue to next page, or deep-dive a specific ticket?"

### Mode B — Deep-Dive Output

```markdown
# Ticket #<ID> — Deep-Dive

**Subject:** ...
**Requester:** ... (<email>)
**Classified bucket:** <N> — <name> [ambiguity: <other bucket or "none">]
**SR #:** <SR>
**Invoice #:** <Invoice>

## Findings
<one-paragraph plain-English summary of what's going on>

## Root cause
<one-to-two-sentence explanation of why the issue exists, if it does>

## Gateway detail (INTERNAL — not for SP-facing reply)
- Quote approved: $<amount>
- Invoice billed: $<amount>
- Delta: $<amount> (<short-pay / over-bill / match>)
- Customer NTE: $<amount>   <!-- INTERNAL ONLY — never include in SP-facing reply body (SP-NTE-only rule, v1.7) -->
- SP NTE: $<amount>          <!-- OK to include in SP-facing reply if relevant -->
- Likely consignment parts: <lines, or "none detected">
- Payment status: <paid / pending / on hold / rejected> <date or reason>

## Draft reply (bucket <N>) — SP-facing, SP NTE only, NO customer NTE
<drafted message, ready to review>

## Suggested next action
<reply+close / reply+keep open / reply+forward-to-invoices@ (bucket 4) / reassign Account Team / escalate Accounting / manual>
```

---

## Write-back Protocol (Freshdesk)

After the operator reviews a draft and confirms, the skill may:
- Post the reply to the ticket (`conversations_manage create_reply`)
- Post an internal private note (`conversations_manage create_note` with `private: true`)
- Change ticket group ownership with `tickets_manage update` when routing requires it, including B10-manual-entry-vint (`group_id:159000486559`) as part of the normal bucket 4 close update.
- **Forward to `invoices@vixxo.com`** (bucket 4 and B9-signs-invoice) via `POST /api/v2/tickets/{id}/forward` (REST API, since the MCP does not expose a forward action) with `to_emails: ["invoices@vixxo.com"]` and `include_original_attachments: true` (default). The forward carries the original SP message and invoice PDF attachments — that is what AP needs to actually process the invoice. Body of the forward is a brief AP-focused header (SR / customer / SP / **SP-NTE-only** / completion-date / invoice # if extractable). **Customer NTE is never included in the forward body or the SP-facing reply body** (SP-NTE-only rule, v1.7). The SP-facing acknowledgment reply (`create_reply`) is a separate write with **no BCC** — the forward already handled AP intake; adding a BCC would just duplicate the notification without the PDF. No CC on the SP-facing reply. See Per-Bucket Drafting Behavior. (v1.11 — superseded the v1.0–v1.10 "BCC IS the forward" pattern after operator audit confirmed BCC does not carry attachments.)

**Never execute these silently.** Present the draft, name the specific writes you're about to make (e.g., "I'll forward the original message and attachments to `invoices@vixxo.com`, post this reply, add an internal note to the Account Team, and set status=Pending" for a bucket 4; "I'll post this reassurance reply, add the Account Team escalation note, tag `account-team-routed`, and leave the ticket Open" for a bucket 1-follow-up; "I'll forward the original message and attachments to `invoices@vixxo.com`, post the requester acknowledgment, add an internal note, tag `manual-entry-invoice` + `vint-routed`, change the group to VINT, and close" for B10-manual-entry-vint; or "I'll post this reply, post the AP-team note, and close (status=5)" for a bucket 2/3), and wait for an explicit approval. If the operator says "send it" or "looks good, go", proceed. If they edit the draft inline, re-confirm before sending. Status / tag / assignment mutations normally go through the Freshdesk MCP `tickets_manage update`; use direct REST only for endpoints the MCP still does not expose, such as `/forward` and `/spam`, or as a fallback if the MCP regresses.

When the QSI AP source tag overlay matches, include `qsiap-source` in the named writes and merge it with existing tags. If the classified bucket would otherwise require no Freshdesk write, present a tag-only write for operator approval. Do not use the overlay as justification to bypass draft approval, manual-review exclusions, or any bucket-specific hold/close rule.

**Gateway writes are out of scope for v1.** The planned v2 write is: add a note to the SR recording that a Freshdesk help desk ticket was submitted, including the ticket # for traceability. Do not attempt this in v1 — note it as a future enhancement if the operator asks why traceability is missing.

---

## MCP capability gaps (v1, observed 2026-04-24)

Recorded so the skill doesn't keep re-discovering them. Re-test these whenever the freshdesk MCP version changes; if any are fixed, update the relevant workflow sections above.

- **Resolved 2026-05-12: `tickets_manage update` now reaches Freshdesk.** Probe used `tickets_manage update { ticket_id: 999999999, status: 5 }` and returned Freshdesk `NOT_FOUND`, not the prior MCP `Validation failed`, confirming the wrapper no longer rejects update payloads before dispatch. Linear bug tracker AIA-489 was canceled. Use MCP `tickets_manage update` for normal status / tag / priority / assignment mutations.
- **`conversations_manage create_note` rejects `notify_emails`** regardless of value, regardless of `private` flag, regardless of whether the email is a registered agent. Standard Freshdesk API supports this; the MCP wrapper or the underlying token does not. **Workflow consequence:** cannot use a private-note-with-notify as a forward mechanism. Use the direct `POST /api/v2/tickets/{id}/forward` REST API for AP intake forwards (v1.11) — see "Direct Freshdesk REST API fallback / forward endpoints" below.
- **MCP does not expose a `forward_ticket` action.** `conversations_manage` actions are limited to `create_reply`, `create_note`, `list`, `get`, `update`, `delete`. **Workflow consequence:** the AP-intake forward for bucket 4 and B9-signs-invoice must be issued via direct REST `POST /api/v2/tickets/{id}/forward`. The v1.0–v1.10 "BCC on reply IS the forward" pattern was a workaround built on the false assumption that BCC carries attachments — it does not. See v1.11 changelog for the bug history.
- **`conversations_manage delete` requires `conversation_id`** (not `id`). Worth flagging because `tickets_manage get` uses `ticket_id` and the inconsistency burns a round-trip when probing.
- **`conversations_manage create_reply` accepts `bcc_emails` and `cc_emails`** (arrays). Confirmed working — but **note (v1.11):** `bcc_emails` carries only the reply *body*, NOT the original ticket's attachments. For AP intake forwarding (bucket 4, B9-signs-invoice) where attachments matter, use direct REST `POST /api/v2/tickets/{id}/forward` instead.
- **Probing on real tickets sends real emails.** `create_reply` posts to the ticket AND emails the requester immediately — there is no dry-run flag. Never test parameter shapes on a customer ticket; always use a Vixxo-internal sandbox ticket. If a probe leaks to a customer, delete the conversation immediately AND post a follow-up apology reply (deletion removes it from the ticket but the email already left).

---

## Direct Freshdesk REST API fallback / forward endpoints (v1.1, updated 2026-05-12)

The MCP `tickets_manage update` issue tracked by AIA-489 is resolved as of 2026-05-12. Use the MCP for normal status / tag / priority / assignment updates. Keep this REST section for endpoints the MCP still does not expose (`POST /api/v2/tickets/{id}/forward`, `/spam`, `/restore`) and as an emergency fallback if the MCP regresses.

### Token discovery (run at start of every Mode A session)

When a direct REST endpoint is required, look for the token in this order, **stop at first hit**:
1. File: `$env:USERPROFILE\.vixxo\freshdesk_token` (preferred — persistent, ASCII, no newline, ACL'd to user only)
2. Env var: `$env:FRESHDESK_TOKEN` in the Cursor Shell process
3. If neither: ask the operator to either save the token to the file (one-time) or paste it as `$env:FRESHDESK_TOKEN = "..."`. Do not proceed with direct REST writes without one.

Token-bearing requests must use HTTP Basic with `"${TOKEN}:X"` (the literal `X` is a Freshdesk convention for "no password needed"). Domain is `vixxo-helpdesk.freshdesk.com`.

### Working direct REST endpoints (all confirmed 2026-04-24 against this token)

| Action | Method | Path | Body | Notes |
|---|---|---|---|---|
| Close | `PUT` | `/api/v2/tickets/{id}` | `{"status":5}` | Idempotent. Re-closing already-closed returns OK. |
| Set Pending | `PUT` | `/api/v2/tickets/{id}` | `{"status":3}` | Use for bucket 4 after bcc forward, signals "waiting on invoices@ team". |
| Resolve | `PUT` | `/api/v2/tickets/{id}` | `{"status":4}` | Use sparingly — Closed (5) is the canonical end state for AP. |
| Assign agent | `PUT` | `/api/v2/tickets/{id}` | `{"responder_id":<agentId>}` | Combine with status flip in one call. |
| Add tags | `PUT` | `/api/v2/tickets/{id}` | `{"tags":["foo","bar"]}` | **Replaces** existing tags — to append, GET first and merge. |
| Mark spam | `PUT` | `/api/v2/tickets/{id}/spam` | (none) | **Must be called BEFORE closing** — `/spam` returns 404 on already-Closed tickets. |
| Restore | `PUT` | `/api/v2/tickets/{id}/restore` | (none) | Inverse of spam. |
| Delete | `DELETE` | `/api/v2/tickets/{id}` | (none) | Soft delete. Use only for confirmed garbage; spam+close is preferred. |

### Endpoints that DO NOT work the way the docs suggest

- **`spam` is NOT a valid field on `PUT /tickets/{id}`.** Returns `400 invalid_field`. Use the dedicated `/spam` sub-endpoint.
- **`/spam` returns `404` unreliably on this tenant** — has been observed on both already-Closed AND Open tickets (2026-04-24, ticket #41608 was Open when `/spam` was called and still 404'd). Root cause not yet confirmed (permission scope on this token? endpoint not enabled for this tenant?). **Operational workaround:** tag the ticket with `phishing` + `security-review` (or an appropriate security-routing tag) in the main `PUT /tickets/{id}` body and close as normal. The spam flag is cosmetic for reporting — the tags + Closed status still remove it from the Open queue and route it to the security reviewer. If hard spam-flagging is required, do it manually in the FD UI after close.

### Pending-hold routing pattern (v1.2.1, added 2026-04-24)

Not every exception-set ticket should be Closed. When the ticket requires **another Vixxo team's action** before the AP desk can complete it, set to Pending (status=3) so it stays visible in the "waiting for external party" bucket rather than vanishing into Closed and getting reopened later as a "why didn't this happen?" ticket.

Use Pending (not Closed) for these exception patterns:

| Pattern | Owner on hold | Rationale |
|---|---|---|
| Bucket 4 Gateway anomaly (SR not complete, NTE breach, etc.) that needs Account Team to fix SR before invoicing can proceed | Account Team | Closing would orphan the SP invoice — SP will just resend |
| Bucket 3 aging where dollar > $10k and Accounting needs to reconcile before replying | Accounting | AP desk isn't authorized to commit to a resolution path at that $ level |
| Bucket 5 remittance access issues (locked VixxoLink, wrong CC, etc.) that need VixxoLink Support or IT | VixxoLink Support / IT | SP is blocked on a system fix, not an AP action |
| Bucket 6 relationship / tone complaints that need Account Team human outreach | Account Team / CRM | A canned close would escalate the relationship damage |

Combine the Pending status with a priority bump (`priority: 2` medium or `priority: 3` high) and a descriptive internal note naming the hold owner + action requested. Do NOT close these — the Pending state is the handoff.

**Pending-hold API gotcha (confirmed 2026-04-24 Batch 7):** When a ticket has a null `type` field (no one set it on creation), a `PUT /tickets/{id}` with only `{status:3, priority:N}` will 400 with `{"field":"type","message":"It should be one of these values: 'Account Update,Invoice Support,VixxoLink Support,Credit/Debit Submission,NTE,Capital Project,SWS,COIs,No Action Required,KSOnboarding'"}`. Fix: always include `"type": "Invoice Support"` in the pending-hold PUT body the same way the close body does. The full canonical Pending-hold body:

```json
{
  "status": 3,
  "priority": 2,
  "type": "Invoice Support",
  "tags": ["<owner-tag>", "pending-hold"]
}
```

### BEC / banking-change-unverified pattern (X-bec-banking, added 2026-04-25, Batch 13)

**Trigger:** Inbound email claiming to be from a vendor, asking the AP desk to "update" their banking / remittance / wire / ACH / routing / account number details. Red flags:

- Unsolicited (no prior ticket thread, no ongoing SR, no invoice attached)
- No verification artifacts (no W-9, no voided check, no "secondary channel" callback number matching the vendor record)
- Subject/body uses language like "please use the new account details below", "our banking info has been updated", "kindly update your records"
- Bank account is at a different institution than the one on file (if verifiable), or the email signature doesn't match the known vendor contact
- Sometimes slightly misspelled domain or a gmail/yahoo reply-to on a "corporate" email

**This is the Business Email Compromise (BEC) / vendor-impersonation attack pattern. Treat all of them as hostile until proven otherwise.**

**Required action (auto-fire default):**

1. `create_note` (private) with the full security flag note naming: "SECURITY FLAG — unsolicited banking info change, no verification, classic BEC vector. NOT forwarded to invoices@vixxo.com to avoid risk propagation. If this vendor is legitimate, they must resubmit through verified Vendor Setup channel (W-9 + voided check + phone verification via known-good contact on file). Ticket preserved for Vendor Maintenance / AP Risk audit."
2. `PUT /tickets/{id}` — close with tags: `bec-risk`, `banking-change-unverified`, `security-review`, `vendor-maintenance-audit`
3. **NO customer reply.** Silence is the correct response here — replying acknowledges receipt and may encourage escalation of the attack. Vendor Maintenance / AP Risk will follow up through the verified channel if the vendor is legitimate.
4. **NEVER BCC `invoices@vixxo.com`.** This is the key deviation from bucket 4. Forwarding a BEC attempt to the AP processing inbox is exactly what the attacker wants — it moves the request from "random email from outside" to "item in our internal AP queue" and raises the chance a human later processes it as legitimate.

**Close body uses:**
- `type: "No Action Required"`
- `custom_fields.cf_type_of_request: "Other"`
- `custom_fields.cf_customer: "Other"`
- Other cf_* fields: `N/A`

**Why this is its own bucket (not phishing):** generic phishing (Punchbowl-style invite links, marketing bait with redirect URLs) is already handled by X-phishing with the same close-and-tag pattern. BEC is distinct because:
- The sender often claims to be a *real* vendor already on file — tagging it `phishing` alone doesn't capture the BEC-specific audit trail Vendor Maintenance needs
- The content is specifically a financial-controls attack vector, not a consumer phishing/spam message
- Vendor Maintenance has a standing responsibility to audit these flags (separate from the security team's general phishing triage)

The `vendor-maintenance-audit` tag is the hook that pulls these into the Vendor Maintenance audit report; `bec-risk` is the hook that pulls them into security reporting. Both are applied.

**Escalation trigger:** If a batch surfaces **3+ BEC attempts targeting the same vendor name or bank account in a rolling 7-day window**, stop auto-firing and escalate to the human operator — that pattern suggests either an active campaign against a specific vendor relationship or a vendor whose email has been compromised. The human should loop in AP Risk + the actual vendor via a verified phone number before any more of these are closed silently.

### No-reply sender guardrail (added 2026-04-25, Batch 20)

**Trigger:** If the ticket requester's email address contains `no-reply`, `noreply`, `donotreply`, `do-not-reply`, `no_reply`, or `no.reply` (case-insensitive, match anywhere in the local-part or subdomain — e.g., `noreply@8x8.com`, `no-reply@docusign.net`, `mailer-daemon`, `notifications@`), **skip the customer-facing reply step**. Perform every other action in the canonical write order exactly as planned (internal note, tags, close, pending-hold, AP-intake forward to `invoices@vixxo.com` if bucket 4, etc.).

**Why:** Replying to a no-reply mailbox is pure noise — the message bounces (polluting the Freshdesk conversation history with bounce-back artifacts and adding deliverability failures to the tenant's reputation), or silently disappears, or in the worst case auto-creates a new ticket in the sender's helpdesk (creating a reflective loop). None of those outcomes help the vendor. All the *internal* parts of the workflow (bucket classification, internal note, status close, tags, AP-intake forward to `invoices@vixxo.com`) remain valuable because they serve Vixxo AP's audit trail regardless of whether the original sender could have received a reply.

**Important — bucket 4 AP-intake forward fires regardless of no-reply status.** As of v1.11 (2026-05-01), the AP-intake leg is **always** `POST /api/v2/tickets/{id}/forward` to `invoices@vixxo.com` (it carries the original message + invoice PDF attachments). The no-reply guardrail does NOT change the forward — it only suppresses the SP-facing `/reply` ack:

| Sender type | `POST /forward` to invoices@ | `create_reply` to SP/internal |
|---|---|---|
| Real, replyable inbox | ✅ Fires (AP intake) | ✅ Fires (ack) |
| No-reply auto-sender | ✅ Fires (AP intake) | ❌ Suppressed (would bounce) |

For a no-reply bucket-4 ticket, the canonical AP-intake write is unchanged from the normal case:
```json
POST /api/v2/tickets/{id}/forward
{
  "body": "<forward wrapper with AP-focused context: SR / customer / SP / SP-NTE-only / completion-date / invoice #>",
  "to_emails": ["invoices@vixxo.com"]
}
```
(Defaults: `include_original_attachments: true`, which is what makes this carry the invoice PDF.)

**Historical note (v1.0–v1.10):** the prior implementation used `POST /reply` with `bcc_emails: ['invoices@vixxo.com']` for the AP-intake leg in the normal case, and only switched to `/forward` for no-reply senders. Operator audit on 2026-05-01 confirmed that the BCC-on-reply path **does not carry the original attachments** — only the reply body — so AP was receiving acknowledgment text without the invoice PDFs and could not process them. v1.11 normalizes both paths to use `/forward` for AP intake. The `/reply` endpoint is now used **only** for the SP-facing ack, never for AP intake. The reference to `to_emails` not being accepted on `/reply` (Batch 21 learning, tickets 33863, 33524, 33521, 33432) remains true and is the reason `/reply` cannot substitute for `/forward` even in the all-replyable case.

The internal note for a no-reply bucket-4 ticket should log: `NOTE: Requester address (<email>) matched no-reply pattern; SP-facing reply suppressed. AP intake forward to invoices@vixxo.com still fired (carries original attachments).` so the audit trail makes the routing decision explicit.

**All other buckets with a no-reply requester:** just skip the reply entirely (`$reply = $null`), add the suppression note, and proceed to close. No forward needed — those buckets never had an AP-forward leg in the first place.

**Coverage examples (non-exhaustive):**
- 8x8 voicemail notifications (`no-reply@8x8.com`) — already handled via X-voicemail-ops auto-close, but this makes the rule explicit
- Amazon Connect voicemail notifications
- DocuSign / Adobe Sign bounces
- Quickbooks / NetVendor / NetSuite auto-resends
- GoTo fax notifications (already X-phishing pattern, but rule applies defensively even for non-phishing variants)
- Internal Vixxo system emails with no-reply senders (8x8 call notifications, Amazon SES bounces)

**Evaluation:** This rule is a **suppression overlay**, not a bucket. It evaluates after bucket classification, just before the write phase. If it fires, the skill logs `sender=no-reply-detected` and proceeds to the non-reply writes.

---

### B5-coi handling — keep open, do not forward, do not close (added 2026-04-27, v1.5)

**Bucket:** `B5-coi` — Certificate of Insurance submissions, insurance renewals, COI requests, W-9 forms, hold-harmless agreements, and any other Risk/Compliance documentation that arrives in the SPM Freshdesk queue.

**Subject heuristics (case-insensitive, any of):** `\bCOI\b`, `\bCertificat[es]?\b`, `\bInsurance\b`, `\bW[-_ ]?9\b`, `Hold Harmless`, `Proof of Insurance`, `Renewal Certificate`, `Certificate of Liability`, `ALOB`, `Workman's Comp`, `Risk Management`.

**Action — `keep-open-coi` (replaces the prior `close-coi` action):**

1. `conversations_manage create_note` — internal note: `Bucket 5 (COI / insurance / compliance documentation). Routed to Risk/Compliance via tags. Ticket left OPEN for the Risk team to action — do not close from the AP side.`
2. `PUT /tickets/{id}` — apply tags: `coi`, `risk-compliance-routed`. **Leave `status=2` (Open). Do NOT set status. Do NOT post a customer-facing reply. Do NOT BCC or `/forward` to `coi@vixxo.com`.**

**Why no forward / no BCC to `coi@vixxo.com`:** the `coi@vixxo.com` distribution list **forwards back into Freshdesk** as a new ticket in the SPM queue. Forwarding or BCC'ing the address from inside SPM creates a circular reference that re-ingests our own messages and pollutes the queue indefinitely. Confirmed by operator on 2026-04-27 after audit of 205 historical B5-coi tickets.

**Why leave the ticket open:** the Risk/Compliance team subscribes to the `coi` and `risk-compliance-routed` tags and pulls open tickets from those tags directly out of the SPM view. Closing the ticket from the AP side would remove it from their working list and they'd never see it. Leaving it Open with the routing tags is the actual handoff.

**Why no customer-facing reply:** the SP submitting the COI does not need an AP acknowledgment — Risk/Compliance will respond if action is required (deficiency, missing endorsement, additional insured wording, etc.). An AP-side ack would imply AP ownership and confuse the SP about who is processing the document.

**Audit trail expectation:** every B5-coi ticket should end up with at least these tags on it after triage: `coi`, `risk-compliance-routed`. The internal note provides the timestamp and the operator/skill version that made the routing decision. Closure (if any) happens later, by Risk/Compliance, after their review.

**Historical reconciliation (2026-04-27):** the prior `close-coi` action (Batches 8–27, 205 tickets) closed COI tickets as part of the AP-side write phase, which removed them from Risk/Compliance's working view. All 205 tickets were reopened on 2026-04-27 with the audit tag `coi-reopened-2026-04-27`. Going forward, B5-coi tickets must use `keep-open-coi` and never transition to `status=5` from this skill.

**No-reply guardrail interaction:** the no-reply sender guardrail above is moot for B5-coi because B5-coi never posts a customer-facing reply in the first place — the new `keep-open-coi` action is note + tags only. No special no-reply handling needed.

---

### Canonical write-phase order (per ticket, when status mutations are needed)

1. `POST /api/v2/tickets/{id}/forward` to `invoices@vixxo.com` for bucket 4 and B9-signs-invoice AP-intake forwards. This is a direct REST call because the MCP still does not expose ticket forwarding.
2. `conversations_manage create_reply` — customer-facing or internal-sender reply. **Skip this step if the no-reply sender guardrail (see above) fires.** For bucket 4 with a no-reply requester, the AP-intake `/forward` still fires; only the SP-facing acknowledgment reply is suppressed. For all other buckets with a no-reply requester, skip the reply entirely and document the suppression in the internal note.
3. `conversations_manage create_note` — internal note for the next-action owner. When the no-reply guardrail fires, the note includes a line like `NOTE: Customer-facing reply suppressed — requester address matched no-reply pattern (<address>).` so the audit trail is clear.
4. **(if marking spam)** `PUT /tickets/{id}/spam` via direct REST unless the MCP adds a dedicated spam action later.
5. `tickets_manage update` — single MCP call combining `status`, `responder_id`, `group_id`, `tags`, `priority`, and required closure fields as needed. For B10-manual-entry-vint, include the normal bucket 4 close body (`status:5`) and add `group_id:159000486559` plus merged tags `manual-entry-invoice` + `vint-routed`.

This ordering matters: replies/notes timestamp the customer/internal record before the status flip, so anyone looking at the ticket history sees "we acknowledged → we documented → we closed" rather than "we closed → wait, why."

### Operator approval pattern

The skill still presents the draft + named writes block before executing. The named writes now include the status mutation explicitly, e.g.:

> "I'll post this reply to Sarah, post the internal note to AP, **and then close the ticket (status=5)**. One operator approval covers all three writes."

For batches: present the per-ticket draft set as before, then list the status mutations as a final block ("after all writes succeed, I'll close: 41606, 41582, 41578, 41609, 41605"). If any reply/note write fails, abort the batch and surface the error — do not proceed to status mutations on a partially-written ticket.

### Why this lives in the skill instead of "just call it inline"

Three reasons. (1) Direct REST tokens have the same destructive power as the operator's UI session — close / spam / delete any ticket — so discovery, scoping, and approval need to be on-script every time, not improvised per session. (2) The "spam before close" / "spam-flag-cosmetic-after-close" gotchas are non-obvious and have already burned one round of triage. (3) The MCP still lacks a forward action, so the direct REST path remains necessary for AP-intake forwards even though AIA-489 is resolved.

---

## Ambiguity & escalation

Classification is imperfect. When you're genuinely unsure which bucket applies — or when the ticket language suggests it's a *variation* on a bucket you haven't seen before — route to bucket 7 (manual) rather than guessing. The operator's time spent on a manual triage is cheaper than the account damage of a mis-routed auto-reply.

For bucket 2 (rejected invoices) specifically: if Gateway data doesn't surface a clear rejection reason, don't invent one. Draft an internal note to the Account Team describing what you found (and didn't) and ask them to close the loop with the provider. The Account Team has context the skill doesn't.

---

## What this skill does NOT do

- Does not send anything without the operator's explicit approval.
- Does not write to Gateway in v1.
- Does not handle Freshdesk tickets already assigned to an agent — those are somebody's active work.
- Does not handle tickets sent to `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com` — those are excluded from the rule flow and left untouched for manual review.
- Does not process tickets older than one calendar year without the operator first confirming (to avoid silently re-opening very stale threads).
- Does not cover HR, IT, facilities, or other non-AP help desk queues — wrong triggers for those.

---

## Auto-pilot default-action policy (v1.2, added 2026-04-24)

**Purpose:** compress large-backlog triage from "present every draft, wait for operator per-batch approval" to "auto-fire the obvious stuff, only stop for anomalies". Approved by operator on 2026-04-24 after three batches of observed defaults.

**Scope:** this policy applies ONLY to Mode A batch triage runs at page size ≥ 50 when the operator explicitly requests auto-pilot (phrases: "auto-pilot", "trust the pattern", "default-action policy", "I trust you will follow the pattern we have used"). For smaller batches (≤ 20) or Mode B deep-dives, keep the original "draft → approve → execute" flow.

### Patterns that auto-fire (no per-batch approval)

Recipient-excluded tickets sent to `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com` never auto-fire. They are reported as `manual-review-recipient-exclusion` and left untouched.

| Bucket | Pattern | Auto-action (fires immediately, in the canonical write order) |
|---|---|---|
| 1 | Thank-you / auto-reply with NO attachment | Close only. No reply, no note. |
| 2 | Rejected-invoice bounceback where Gateway shows a clear rejection reason **and** the reason is something the SP can self-correct (wrong remit, missing PO, wrong line item) | Ack reply with the reason + corrective path, internal note for AP, Close. |
| 3 | Aging / payment-follow-up where Gateway shows a definitive status (paid on date X / pending with reason Y / rejected for Z) **and the ticket is not a no-attachment SP update chase** | Ack reply with the status, internal note, Close. If past-due-but-not-yet-due (proactive reminder from SP), internal note for AP only (no customer reply), Close. **Do not auto-close SP/provider questions asking why an SR/invoice/NTE/rejection has not moved forward when no attachment is present; those are bucket 1-follow-up AP-team handoffs.** |
| 4 | Clean SR-referenced invoice submission: SR number parses, Gateway SR found, no anomalies (see below) | **(v1.11) Three writes in this order:** (1) `POST /forward` to `invoices@vixxo.com` (REST API) carrying original SP message + invoice PDF attachments, with a brief AP-focused header (SR / customer / SP / **SP-NTE-only** / completion-date / invoice # if extractable); (2) ack reply to SP/requester with same SR / customer / SP / **SP-NTE-only** / completion summary, **no BCC**; (3) internal note for Account Team with full customer + SP NTE context. Then Close. **Never include customer NTE in either the forward header or the SP-facing reply body.** |
| 6 | Internal-source CC payment confirmations, SR-completion notifications, and other Vixxo-internal informational notices | Internal note summarizing, Close. No customer reply. **External SP/provider update requests are excluded even if the text contains "update", "question", or "what else is needed"; route those as bucket 1-follow-up, tag AP Team, and leave Open.** |
| 7a | Spam / marketing / cold outreach with zero ticket relevance | Mark spam (before close), then Close. No reply, no note. |
| 7b | QuickBooks auto-resend that is a confirmed duplicate of another ticket processed in the same or a recent batch | Internal note linking to the original ticket, Close as duplicate. |
| 0b | Obvious phishing with strong indicators AND no legitimate reason to keep the thread open | Mark spam, Close. Also post the security-escalation internal note per the bucket 0 rules. |
| X-bec-banking | Unsolicited banking / remittance / wire / ACH info-change request from a purported vendor with no verification artifacts (see full BEC section above) | Internal security-flag note, Close with tags `bec-risk`, `banking-change-unverified`, `security-review`, `vendor-maintenance-audit`. **NO customer reply. NO BCC to invoices@vixxo.com.** |
| X-phishing | Punchbowl-style invite links, marketing bait with `.icu`/`.xyz` redirect URLs, obvious consumer-phishing | Close with tags `phishing`, `security-review`. No reply. |
| X-voicemail-ops | 8x8 voicemail notification landing in SPM queue (ext 4046 Vendor Relations, or customer-helpdesk P0 WO voicemail) | Close with tags `voicemail`, `vendor-relations` or `operations-not-ap`, `wrong-queue`. No reply — Vendor Relations/Ops has their own channel. |
| X-misroute | Sender explicitly apologizes / states the email was not meant for Vixxo AP | Close with tags `misroute`, `sender-apologized`, `no-action`. No reply. |
| B5-coi | COI / certificate-of-insurance submission, insurance renewal, W-9, hold-harmless, or other Risk/Compliance doc (subject heuristics in B5-coi section above) | Internal note + apply tags `coi`, `risk-compliance-routed`. **Leave status=2 (Open). Do NOT close. Do NOT reply. Do NOT BCC or /forward to `coi@vixxo.com` — circular ref.** Risk/Compliance picks up by tag. (added v1.5, 2026-04-27) |
| B6-onboarding | New SP / vendor setup / SAP onboarding inquiry. Triggers in Rule 0b (subject/body keywords: `onboarding`, `new vendor`, `vendor setup`, `new supplier`, `supplier setup`, `new provider`, `provider setup`, `SAP onboarding`, etc.). **Onboarding screen wins over B4-invoice and B5-remittance even when those keywords also appear** — see Rule 0b tie-breakers. | Internal note + apply tags `sp-onboarding`, `account-team-routed`. **Leave status=2 (Open). Do NOT close. Do NOT reply. Do NOT BCC `invoices@vixxo.com`.** SP Onboarding / Account Team picks up by tag. (added v1.6, 2026-04-27) |
| B7-sap | Any SAP-related ticket: SP invoice referencing a SAP PO, customer-side SAP onboarding not caught by Rule 0b, internal Vixxo ERP-integration messages. Triggers in Rule 0c (subject/body/attachment-name contains whole-word `SAP`). **SAP screen wins over B4-invoice, B5-remittance, and most other buckets** — see Rule 0c tie-breakers. | Internal note + apply tags `sap-ticket`, `account-team-routed`, and `erp-ops` if SAP-PO / ERP-interface referenced. **Leave status=2 (Open). Do NOT close. Do NOT reply. Do NOT BCC `invoices@vixxo.com`.** Account Team / ERP-Ops picks up by tag. (added v1.7, 2026-04-28) |
| B8-vendor-hold | Internal KnowledgeSync automation notification — Vixxo SPM auto-assigned a work order to a vendor with Workday status `On Hold`, `WDOnHold`, or `Do Not Use`. Triggers in Rule 0d (`requester_email` is `knowledgesync@vixxo.com` AND subject matches the vendor-hold notification template). The work order needs to be reassigned by SPM Ops or the vendor's Workday status reconciled by Account Team — neither of which is an AP function. | Internal note + apply tags `vendor-hold-notify`, `account-team-routed`. **Leave status=2 (Open). Do NOT close. Do NOT reply. Do NOT BCC `invoices@vixxo.com`.** Account Team / SPM Ops picks up by tag. (added v1.8, 2026-04-29) |
| B10-manual-entry-vint | Ticket explicitly states that the requester is looking for, asking for, or needs manual entry / manual-entry / manually entered handling for an invoice. This overlay adds VINT ownership to the normal bucket 4 invoice submission workflow. | **Follow bucket 4 canonical writes:** `POST /forward` to `invoices@vixxo.com`, requester acknowledgment when replyable, internal note, then close (`status=5`). In the close update, also change group to VINT (`group_id:159000486559`) and merge tags `manual-entry-invoice`, `vint-routed`. (added 2026-05-18) |
| B9-signs-invoice | Internal `@vixxo.com` sender + ticket contains **both** `\bsigns?\b` AND `\blighting\b` (AND, not OR) + invoice content (invoice attachment, invoice #, payment ask, billing language). Triggers in Rule 0e. **Sub-bucket tie-breaker: when both invoice and SP-update indicators are present, B9-signs-invoice wins** — see Rule 0e tie-breakers. | **(v1.11) Three writes:** (1) `POST /forward` to `invoices@vixxo.com` (REST API) carrying original message + invoice attachments, brief AP-focused header. (2) AP-side confirmation reply to the internal sender (Appendix C-1), **no BCC**. (3) Internal note. Then Close (status=5). Tags: `signs-lighting`, `vixxo-signs-internal`, `invoices-forward` (renamed from `invoices-bcc` in v1.11). cf_customer = `Other`, cf_type_of_request = `Submit an Invoice for manual entry`. (added v1.10, 2026-04-30; AP-intake leg corrected to `/forward` in v1.11, 2026-05-01) |
| B9-signs-sp-update | Internal `@vixxo.com` sender + ticket contains **both** `\bsigns?\b` AND `\blighting\b` (AND, not OR) + SP-update content (SP info / coverage / roster / performance / rate / labor-type change for the Signs program). Triggers in Rule 0e. **Default route when content is ambiguous between invoice and SP-update** — see Rule 0e tie-breakers. | AP-side confirmation reply to the internal sender (Appendix C-2), internal note + apply tags `signs-lighting`, `vixxo-signs-internal`, `vendor-maintenance`, `signs-lighting-sp-update`. **Leave status=2 (Open). Do NOT close. Do NOT BCC `invoices@vixxo.com`.** Vendor Maintenance picks up by tag. (added v1.10, 2026-04-30) |

### Patterns that always escalate (require operator approval)

Any of these means **stop auto-firing and surface in the exception list** for per-ticket operator review:

1. **Manual-review recipient exclusion:** any ticket sent to `ksonboarding@vixxo.com` or `service.providermanagement@vixxo.com`. Report it, but do not classify, draft, tag, note, forward, close, or otherwise mutate it.
2. **Gateway anomaly on a bucket 4 ticket:** NTE breach (invoice > customer NTE by >20%, or > SP NTE by >20%), SR status in `Quote Required` / `New ETA Required` / `Cancelled` when the SP is invoicing, invoice submitted when a BRN already exists at >$0 on the same SR (likely real duplicate, not QB resend), customer NTE = $0 when SP is billing.
3. **Ambiguous classification:** more than one rule scores strongly, subject and body suggest different buckets, or the content is genuinely unclear.
4. **Bucket 6 that needs a human next action:** mystery payment reconciliation, credit/adjustment requests post-payment, SP asking questions Vixxo AP can't answer from Gateway alone.
5. **No-attachment SP/provider update chase:** requester asks why payment, invoice approval, NTE approval, rejection correction, or SR movement has not happened and no attachment is present. Route to AP Team, tag `ap-team-routed` + `sp-update-request`, leave Open. Do not close as Bucket 3 or Bucket 6 even when Gateway reveals the likely root cause.
6. **Bucket 7 no-SR:** no SR number anywhere in subject/body/attachments, can't auto-route to Account Team, needs a human to open the attachment and identify the customer.
7. **Phishing soft-indicators only (no strong indicator):** 2+ soft indicators but nothing conclusive — operator reviews before spam/close.
8. **Any ticket where the customer-facing reply would contain a dollar amount > $10,000 or would be the first touch on an SP Vixxo has flagged for quality issues** (e.g., current WERCS pattern). Auto-generated replies on high-$ or flagged-SP tickets are reputational risk.
9. **Tickets older than 14 days:** the aging-bias rule — very old tickets often have context the skill can't see. Surface for review.
10. **X-bec-banking cluster:** 3+ BEC/banking-change attempts targeting the same vendor name or bank account within a rolling 7-day window. Stop auto-firing and escalate to AP Risk + verified vendor contact before closing any more of that cluster. (Individual BEC attempts still auto-fire per the X-bec-banking pattern above; the escalation is for the *cluster*.)

### Auto-pilot execution protocol

1. Operator requests auto-pilot batch of size N.
2. Skill pulls N tickets, classifies each, pulls Gateway for buckets 2/3/4.
3. Skill partitions into `auto-fire` and `exception` sets per the rules above.
4. Skill posts a compact **pre-execution digest** before firing:
   - Count of auto-fires by bucket (with ticket IDs)
   - Count of exceptions by category
   - Dollar total of all customer-facing replies being auto-sent
   - Count of status mutations (Close / Pending / Spam)
5. Skill executes all auto-fires in parallel (conversation writes first, then REST status mutations per the canonical order).
6. Skill presents the **exception set** as a table with pre-filled recommendations. Operator responds by exception — silence on an item means "take the recommendation".
7. Skill fires the exception-set decisions per operator response.

The pre-execution digest is the ONE approval gate. It's non-interactive in the sense that operator silence = approval, but the digest is always posted so the operator can halt before writes fire. This is the same trust model as the existing per-batch flow, just compressed.

### Audit after execution

After the batch completes, surface for the operator:

- Any auto-fire that FAILED (typically Freshdesk closure-required fields — see section below)
- Any Gateway lookup that returned no result (possible fabricated SR or data issue)
- Any ticket where the classification confidence was borderline (post-hoc audit — operator can override if the classification was wrong)
- Running backlog counter: how many Open tickets remain after this batch

---

## Closure-required fields (v1.2, added 2026-04-24)

**Discovery:** the Freshdesk AP help desk has a **closure-validation policy** that enforces required fields on status transition to Closed (status=5). `Pending` (status=3) does NOT enforce these. First-try closes on Open tickets typically fail with `400 Validation failed` if any required field is null.

**Required-on-close fieldset** (all must be non-null on the PUT body or already set on the ticket):

| Field | Type | Accepted values |
|---|---|---|
| `type` | string | One of: `Account Update`, `Invoice Support`, `VixxoLink Support`, `Credit/Debit Submission`, `NTE`, `Capital Project`, `SWS`, `COIs`, `No Action Required`, `KSOnboarding` |
| `custom_fields.cf_sp` | string | Free-form SP name. Use Gateway SP display name (e.g., `KS - Habitat Solutions`). For non-SR internal submissions, use a descriptive label (e.g., `ESS 3514 Sacramento CA (Supplier 1034293)`). |
| `custom_fields.cf_sr` | string | Free-form. Use the SR number (`1-6547778552`) if one exists, or `Invoice #<num>` / `Sales Order <num>` / `N/A` otherwise. |
| `custom_fields.cf_amount` | string | Free-form dollar amount (`$8,642.00`) or `N/A`. |
| `custom_fields.cf_sr_required` | string | `Yes` or `No`. Use `Yes` if the ticket references a real Gateway SR, `No` for internal submissions / aging reminders / non-SR work. |
| `custom_fields.cf_customer` | string | **Constrained whitelist** — see mapping table below. |
| `custom_fields.cf_type_of_request` | string | One of: `Submit an Invoice for manual entry`, `Follow up on an Unpaid Invoice`, `Resolve Rejected Invoice`. |

**Gateway customer → Freshdesk cf_customer whitelist mapping** (the most common AP-desk customers; fall through to `Other` if no match):

| Gateway customer | Freshdesk cf_customer value |
|---|---|
| Boyd Group / Boyd Collision / Boyd Autobody | `The Boyd Group` |
| PetSmart / PetSmart-SMS Assist | `Petsmart` |
| Ulta / Ulta Beauty | `Ulta Beauty` |
| Circle K / 7-Eleven Circle K | `Circle K` |
| 7-Eleven / 7Eleven | `7-Eleven` |
| Starbucks | `Starbucks` |
| Walmart / Wal-Mart | `Wal-Mart Stores` |
| Kroger | `Kroger Company` |
| Target | `Target Corporation` |
| Dollar General | `Dollar General` |
| Family Dollar | `Family Dollar` |
| TJX / TJ Maxx / Marshalls / HomeGoods | `TJX Companies (TJ Maxx, HomeGoods, Marshalls)` |
| Bath & Body Works | `Bath & Body Works` |
| O'Reilly Auto / O'Reilly | `O'Reilly Auto Parts` |
| Speedway | `Speedway` |
| GPM | `GPM Investments` |
| Costco | `Costco Wholesale Corporation` |
| TravelCenters of America / TA | `Travelcenters of America` |
| Global Partners | `Global Partners` |
| Waste Management | `Waste Management` |
| Rivian | `Rivian` |
| Hertz | `Hertz Corporation` |
| Any ESS / LSI Signs / Vixxo Construction / internal non-customer | `Other` |
| Direct Sign Wholesale / SP-initiated aging with no customer context | `Other` |

If the Gateway customer name doesn't match any of the above, check the full whitelist embedded in the Freshdesk API error response (it's returned verbatim on validation failure), then pick the closest. If no match, use `Other`.

### Canonical bucket → `cf_type_of_request` mapping

**HARD CONSTRAINT (confirmed by API error 2026-04-24 batch 6):** `cf_type_of_request` has ONLY three valid values. Any other string — including `Payment Inquiry`, `Remittance`, `Other`, `General` — returns `400 invalid_value`. Map every bucket to exactly one of these three:

| Bucket | cf_type_of_request value |
|---|---|
| 2 (rejected invoice) | `Resolve Rejected Invoice` |
| 3 (aging / follow-up / paid-inquiry / wrong-queue / remittance-status) | `Follow up on an Unpaid Invoice` |
| 4 (SR-referenced submission) | `Submit an Invoice for manual entry` |
| 5 (CC/VCC payment / remittance access) | `Follow up on an Unpaid Invoice` |
| 6 (internal info / routing / SR-dispatch noise) | `Submit an Invoice for manual entry` (fallback — the dropdown has no generic value) |
| 7 (sign-shop / manual intake / general no-SR) | `Submit an Invoice for manual entry` |
| 0 (phishing / security-review / non-due noise) | `Follow up on an Unpaid Invoice` (closest semantic; no phishing value exists) |

**Customer whitelist gotcha:** Customers with apostrophes (e.g. `David's Bridal`) are NOT always on the tenant whitelist exactly as spelled — the Freshdesk tenant whitelist omits some names our Gateway data uses. When a close fails on `cf_customer`, re-read the whitelist verbatim from the 400 response body and pick the closest match, or fall back to `Other` to unblock the close. Known gaps: `David's Bridal`.

### Canonical `PUT /tickets/{id}` close body

Apply this shape at close time — fill all seven fields from the classifier's collected data so the close lands first try:

```json
{
  "status": 5,
  "type": "Invoice Support",
  "custom_fields": {
    "cf_sp": "<SP display name>",
    "cf_sr": "<SR# or 'Invoice #<num>' or 'N/A'>",
    "cf_amount": "<$NN.NN or 'N/A'>",
    "cf_sr_required": "<Yes|No>",
    "cf_customer": "<whitelist value>",
    "cf_type_of_request": "<bucket-mapped value>"
  }
}
```

Pending (status=3) mutations can omit all the custom_fields — Freshdesk only enforces them on Closed transitions.

### Failure handling

If a close still fails after filling all seven fields, the likely causes are:
- A **new required field** not yet in this list (Freshdesk admins can add fields). The API error response names the missing field — update this section with the new field and its accepted values, then retry.
- A **closure-blocking status rule** (e.g., ticket has unresolved dispatcher automation). Check `status_in_freshdesk_portal` manually. Rare; has not been observed to date.

---

## Gotchas observed in the wild

- **Providers often paste the invoice *image* rather than the number in the body.** If you can't find an SR# or invoice# in text, check attachments and note that in findings.
- **"Statement" subject lines are bucket 3**, even though they look more formal than the rest. They're almost always aging follow-ups.
- **Payment links and remit instructions are risk signals, not AP-intake
  shortcuts.** Screen them through BEC/phishing first; if they do not meet the
  security threshold, route as manual/payment-link-caution and verify through
  trusted vendor records.
- **VixxoLink blockers are not payment answers.** Missing travel/rate/NTE
  fields, PO-not-generating, Build Quote only, login, and portal-visibility
  problems need Account Team / portal-owner routing before AP can resolve them.
- **Bulk AR statements often contain mixed statuses.** Treat multi-invoice lists
  as AP/Accounting review unless each line has a clear Gateway-backed answer.
- **A single ticket sometimes references multiple SRs.** In Mode B, surface all of them and let the operator point to the one they want the deep-dive on.
- **Duplicate tickets are common** — the same provider may have filed the same concern twice. In Mode A's triage report, call this out as an ambiguity note when two rows on the same page have the same SR or obviously duplicate subjects.

---

## Version history

- **v1.15 (2026-05-18)** — Added SPM invoice-concern category overlays from the live queue review: payment follow-up/statements, manual invoice intake, Gateway/AP review exceptions, Account Team/VixxoLink blockers, duplicate/resubmission clusters, payment-link/remittance risk, missing identifiers/no-SR, and credit-card/internal-process notices. These overlays run after pre-screens and before generic Rules 1–7 so broad statements do not become one-off replies, portal blockers do not become AP closes, and payment-link/remit tickets do not enter normal invoice intake without security/manual review.
- **v1.14 (2026-05-18)** — Added QSI AP source tag overlay. Tickets that came from or were forwarded from `qsiap@vixxo.com` now get `qsiap-source` merged into the normal write-phase tags without changing bucket classification, Gateway lookup rules, drafting behavior, or close/keep-open decisions.
- **v1.13 (2026-05-12)** — Retired AIA-489 workaround after `tickets_manage update { ticket_id: 999999999, status: 5 }` returned Freshdesk `NOT_FOUND` instead of MCP `Validation failed`, confirming the update wrapper now dispatches payloads. Normal status / tag / priority / assignment mutations should use MCP `tickets_manage update`; direct REST remains only for unexposed endpoints (`/forward`, `/spam`, `/restore`) or emergency fallback.
- **v1.12 (2026-05-06)** — Corrected no-attachment SP/provider update-chase routing after ticket #41397 was closed with only an internal note. Bucket **1-follow-up** now explicitly covers payment, invoice, rejection, NTE-approval, and SR-status questions where no invoice/supporting attachment is present. Required action: private note to AP Team, tags `ap-team-routed` + `sp-update-request`, leave ticket **Open**, optional reassurance reply only after operator approval. Bucket 3 and Bucket 6 now include explicit exceptions so Gateway findings or generic "update/question" language cannot convert these tickets into note-and-close auto-fires.
- **v1.10 (2026-04-30)** — **Rule 0e — Signs & Lighting internal-sender screen** added. Trigger: `requester_email` ends `@vixxo.com` AND the combined match surface (subject + body + conversation history + attachment filenames) contains **both** `(?i)\bsigns?\b` AND `(?i)\blighting\b` — AND semantics, not OR. The original draft used OR semantics across a broader keyword list (`\bsigns?\b`, `\blighting\b`, `\bLSI\b`, `\bsign shop\b`, `\bvixxo signs?\b`, `\bvixxo lighting\b`); operator tightened to AND in the same release because OR over-matched routine internal emails using "sign" or "lighting" generically. Standalone variants (`LSI` alone, `Vixxo Signs` alone, `sign shop` alone) no longer fire. When the trigger fires, the ticket splits into two sub-buckets. **B9-signs-invoice**: invoice content → AP-side confirmation reply to internal sender + BCC `invoices@vixxo.com` + Close (tags `signs-lighting`, `vixxo-signs-internal`, `invoices-bcc`). **B9-signs-sp-update**: SP-update content → AP-side confirmation reply to internal sender + tag for Vendor Maintenance + leave Open (tags `signs-lighting`, `vixxo-signs-internal`, `vendor-maintenance`, `signs-lighting-sp-update`). Departure from the keep-open-* family: B9 always sends an AP-side confirmation reply because the internal sender is the right point of contact for a routing receipt — silent routing was producing follow-up tickets. Tie-breakers: invoice + SP-update both present → invoice wins; ambiguous → SP-update wins; SAP / onboarding / phishing precedence rules unchanged. Appendix C-1 / C-2 added with the two canned replies.
- **v1.9 (2026-04-29)** — Bucket 1 split into **1-close** (true courtesy-only thank you / auto-reply) and **1-follow-up** (polite but frustrated update chase). 1-follow-up tickets stay **Open**, get tagged/routed to Account Team, receive an internal escalation note, and generate a warm SP-facing reassurance draft instead of being auto-closed.
- **v1.8 (2026-04-29)** — **Rule 0d — Vendor-hold notification screen** added. KnowledgeSync auto-notifications (`requester_email = knowledgesync@vixxo.com`, subject matches "Vendor on Hold / WDOnHold / Do Not Use Vendor assigned to Open Ticket notification") are now classified as **B8-vendor-hold** with action `keep-open-vendor-hold`: internal note + tags (`vendor-hold-notify`, `account-team-routed`), ticket left **Open** for Account Team / SPM Ops to reassign the work order or reconcile the vendor's Workday status. Previously these fell through to B7-manual `surface-exception`, which delayed reassignment and let underlying customer SRs sit stranded. Surfaced in the 2026-04-29 batch (16/270 unrouted tickets, 5.9%) — the recurrence rate justifies a dedicated rule.
- **v1.7 (2026-04-28)** — Two policy changes. (1) **SP-NTE-only rule** for all customer-facing replies — SP NTE may appear in the reply body when relevant; **customer NTE must never appear** in SP-facing text (including the bucket-4 BCC copy to `invoices@vixxo.com`, which is the same body the SP sees). Customer NTE remains in the internal note and Mode B's Gateway-detail INTERNAL section. (2) **Rule 0c — SAP screen** — any ticket whose subject, body, or attachment filename contains whole-word `SAP` is classified as **B7-sap** with action `keep-open-sap`: note + tags (`sap-ticket`, `account-team-routed`, optionally `erp-ops`), ticket left **Open** for Account Team / ERP-Ops. SAP tickets are no longer closed or BCC'd to `invoices@vixxo.com` from the AP side. 2026-04-28 audit surfaced 5 prior SAP invoice closures (tickets 32278, 32281, 32285, 40400, 40405) plus 2 other SAP closures (30466, 33504) as candidates for reconciliation — see `tmp\sap_invoice_bcc_audit.csv`.
- **v1.6 (2026-04-27)** — B6-onboarding `keep-open-onboarding` rule + Rule 0b onboarding pre-screen. New SP / vendor-setup / SAP-onboarding tickets are tagged (`sp-onboarding`, `account-team-routed`) + note-only and **left Open** for the Account Team / SP Onboarding to action. Rule 0b is evaluated immediately after the phishing screen and short-circuits rules 1–7 — onboarding keywords win over remittance and invoice heuristics, fixing the 2026-04-27 audit finding where 13 onboarding tickets were mis-closed as B5-remittance (10) or B4-invoice (3). The 13 tickets were reopened with audit tag `onboarding-misroute-2026-04-27`.
- **v1.5 (2026-04-27)** — B5-coi `keep-open-coi` rule. COI / insurance / compliance documentation tickets are tagged (`coi`, `risk-compliance-routed`) + note-only and **left Open** for Risk/Compliance to action. No close, no reply, no `/forward` to `coi@vixxo.com` (circular ref — that mailbox forwards back into Freshdesk). Replaces the v1.0–v1.4 `close-coi` behavior. 205 historical COI tickets reopened on 2026-04-27 with audit tag `coi-reopened-2026-04-27`.
- **v1.4 (2026-04-25)** — No-reply sender guardrail. Skip customer-facing reply if requester address contains `no-reply` / `noreply` / `donotreply` / etc. For Bucket 4 with no-reply requester, replace `/reply+BCC` with `/forward` to `invoices@vixxo.com` (Freshdesk `/reply` does not accept `to_emails` overrides).
- **v1.3 (2026-04-25)** — `X-bec-banking` BEC / banking-change-unverified pattern. Internal note + tags + close, no customer reply, no BCC to AP.
- **v1.2.1 (2026-04-24)** — `/spam` 404 workaround (use `phishing` + `security-review` tags + normal close). Pending-hold pattern for non-AP teams; pending-hold accounting variant for payment-discrepancy tickets.
- **v1.2 (2026-04-24)** — Auto-pilot default-action policy. Closure-required fields (7 custom fields + `type`) documented for `status=5` transitions.
- **v1.0–v1.1** — Initial Mode A / Mode B skill, decision tree, original REST-API workaround for AIA-489.
