---
name: VIXXO-coi-review
description: Review a service provider's Certificate of Insurance (COI) against Vixxo's minimum insurance requirements, identify any missing or deficient items, and draft a formal follow-up reply (Freshdesk public reply or standalone email) listing what needs to be corrected or clarified. Use this skill whenever the user uploads, pastes, or references a Certificate of Insurance, ACORD 25, COI, insurance certificate, or anything similar — and also when they ask to "check," "verify," "review," "audit," or "validate" insurance coverage for a vendor, contractor, or service provider. Also use it for Freshdesk-driven COI work — phrases like "work the SPM COI queue," "triage the COI queue," "review COI tickets," "review ticket #NNNNN" when the ticket is tagged `coi` / `risk-compliance-routed` or arrived via `COI@vixxo.com`. Use it even if the user does not explicitly say "compare to Vixxo requirements"; that comparison is the default purpose of this skill.
---

# VIXXO COI Review (Vixxo Minimum Requirements)

This skill reviews a service provider's (SP) Certificate of Insurance against Vixxo's minimum insurance requirements, reports gaps, and drafts a formal reply back to the SP requesting corrections.

The skill has **two modes**. Pick one based on what the user is asking:

- **Mode A — Ad-hoc COI.** The user pastes a COI, attaches a PDF, or refers to a single COI outside of any ticket. Output is a standalone email draft.
- **Mode B — Freshdesk SPM COI queue.** The user wants to work the COI queue in Freshdesk, or names a specific COI ticket. COI tickets arrive at `COI@vixxo.com`, land in the **SPM** group, and get tagged `coi` + `risk-compliance-routed` by upstream triage. Output is a Freshdesk public reply (drafted, then sent only on operator approval) plus an internal private note recording the findings.

If the user's ask is ambiguous, ask which mode before pulling tickets or generating output.

## Outbound messaging guardrail (mandatory, both modes)

Per `.cursor/rules/outbound-messaging-guardrail.mdc`, **never send a reply, note, status change, or tag update without {{employee_name}}'s explicit approval.** This applies to every Freshdesk write action in Mode B (`conversations_manage create_reply`, `create_note`, `tickets_manage update`). The skill drafts; the operator decides; the skill executes on confirmation.

## Workflow (review steps — same for both modes)

Follow these steps in order every time:

1. **Read the SP's COI.** Extract every relevant field — insurer(s), insured name, policy numbers, effective and expiration dates, coverage types, limits, additional insured wording, waiver of subrogation, primary & non-contributory wording, notice of cancellation, certificate holder, and any endorsement form numbers/editions referenced in the Description of Operations or attached endorsements.
2. **Compare against Vixxo's minimum requirements** (see `references/vixxo-requirements.md`). Check each requirement individually rather than scanning generally.
3. **Produce the review output** in the format described under "Output format" below.
4. **Draft the reply** to the service provider in formal tone, listing only the items that are missing, expired, deficient, or unclear. Do not include items that are already compliant.
5. **In Mode B only:** wait for operator approval, then post the reply through Freshdesk and apply the appropriate outcome tags / status (see "Mode B — Freshdesk SPM COI queue" below).

## Vixxo's minimum requirements (summary)

The authoritative list lives in `references/vixxo-requirements.md` — read it before every review. At a high level, an acceptable COI must show all of the following:

- **Commercial General Liability** (occurrence form) with the standard limit boxes populated (Each Occurrence, Damage to Rented Premises, Med Exp, Personal & Adv Injury, General Aggregate, Products – Comp/Op Aggregate).
- **Automobile Liability** with Combined Single Limit (or Bodily Injury / Property Damage equivalents) and the appropriate auto coverage box checked (Any Auto / All Owned / Hired / Non-Owned, etc.).
- **Workers' Compensation / Employers' Liability** with statutory WC limits and EL Each Accident / EL Disease – Each Employee / EL Disease – Policy Limit populated. If "Proprietor/Partner/Executive Officer/Member Excluded" is marked Yes, an explanation must appear in the Description of Operations.
- **Umbrella / Excess Liability** if the underlying limits do not meet the required totals (occurrence form preferred).
- **Additional Insured wording** in the Description of Operations naming: *"Vixxo Corporation, its subsidiaries, affiliates, related entities and their officers, officials, employees, volunteers (collectively, 'Vixxo'), its customers, the owner, operator and, if required, mortgagee of any site where SP performs Services."*
- **Additional Insured endorsements** referenced by form number and edition:
  - General Liability: **CG 20 10 04/13** (or equivalent) **and** **CG 20 37 04/13** (or equivalent) — both are required (ongoing operations *and* completed operations).
  - Automobile Liability: **CA 20 48 10/13** (or equivalent).
- **Primary and non-contributory** wording for the General Liability policy (endorsement equivalent: **CG 20 01 04/13**).
- **Waiver of Subrogation** in favor of the Additional Insureds on **General Liability, Automobile Liability, and Workers' Compensation / Employers' Liability** (endorsement equivalents: **CG 24 04**, **CA 04 44**, **WC 00 03 13**).
- **30 days' Notice of Cancellation** language (endorsement equivalents: **IL 01 03**, **CG 02 24**).

  Full equivalent-form reference (ISO editions, blanket forms, carrier proprietary examples, umbrella forms): **`references/endorsement-equivalents.md`** and **`assets/endorsement-equivalents.pdf`**. Consult when an SP submits non-ISO or older-edition endorsements.
- **Certificate Holder** must read:
  - Vixxo Corporation
  - 7580 N. Dobson Road, Suite 201
  - Scottsdale, AZ 85256

  **Certificate Holder address — date rule (operator-confirmed 2026-05-04):** the Dobson Road address above is required for any COI **dated 3/16/2026 or later**. For COIs **dated before 3/16/2026**, the prior Certificate Holder address (7000 E Shea Blvd., Suite H-1970, Scottsdale, AZ 85254) is acceptable. When reviewing, compare the COI's "Date" field (top-right of the ACORD 25 form) against the 3/16/2026 cutoff before flagging the Certificate Holder as deficient.
- **Policy dates** must be current (not expired) as of the review date.
- **Insured name** on the COI must match the service provider's legal/contracting name.

If anything above is missing, expired, blank, illegible, or worded in a way that materially differs from the requirement, it is a deficiency.

## Mode B — Freshdesk SPM COI queue

COI submissions arrive at `COI@vixxo.com`, get auto-routed into the Freshdesk **SPM** group (`group_id:159000485013`), and the existing `VIXXO-freshdesk-invoice-review` (B5-coi) triage applies tags `coi` and `risk-compliance-routed` and **leaves the ticket Open** so the Risk/Compliance team can action it. This skill is that action layer.

### Critical do-not list

- **Do NOT BCC, `/forward`, or `to_emails`-override to `COI@vixxo.com`.** That mailbox forwards back into Freshdesk and creates a circular reference. All replies go through the ticket's own conversation thread (`conversations_manage create_reply`), which automatically reaches the original requester. This is the same guardrail enforced in `VIXXO-freshdesk-invoice-review` v1.5.
- **Do NOT post a public reply or change ticket state without explicit operator approval.** See "Outbound messaging guardrail" above.
- **Do NOT close the ticket simply because the COI is compliant** unless the operator explicitly says so. Confirm intended end-state with the operator (Resolved vs Closed) before applying it. Default for compliant outcomes is **Resolved (`status: 4`)**.
- **Do NOT review `donotreply@vixxo.com` tickets as single COIs.** Batch/system COI rollup notifications (e.g., daily CSV listings such as `coi_YYYYMMDD.csv` covering many SPs at once) are not single-COI submissions. If the operator asks to clean up rollups, close them using the "Daily CSV rollup cleanup" workflow below; otherwise skip them without public replies or COI findings.
- **Do NOT use `to_emails` overrides on `conversations_manage create_reply` / `POST /reply`.** The Freshdesk tenant's `multiple_to` feature is **disabled**; any reply with a `to_emails` override returns `400 inaccessible_field`. For the (rare) case where the SP-facing message must go to a different address than the ticket's default reply-to (e.g., internal-forward COIs — see "Internal-forward COI handling" below), use `POST /api/v2/tickets/{id}/forward` instead. The forward endpoint accepts `to_emails` and `cc_emails` and is the only sanctioned reroute mechanism.
- **Do NOT trust Freshdesk search status alone immediately after writes.** Search results can lag and may continue to return recently Resolved/Pending tickets as `status:2` Open. Before reworking a ticket from a search result, verify its true current state with direct `GET /api/v2/tickets/{id}` and only process tickets whose direct record is still Open.

### Compliant outcome — ticket field flip (verified 2026-05-04)

When closing out a **compliant** COI ticket, the canonical action is to flip the ticket `type` from `COIs` to **`Account Update`** and set the Account Update "Type of Request" custom field to **`Profile Update`**.

The verified API field key is **`cf_vixxo_link_type_of_request`** (not `cf_type_of_request` — that one belongs to the Invoice Support / AP-help-desk form and stays `null` on Account Update tickets). Verified against tickets 43469 and 43500 on 2026-05-04 — both `type: "Account Update"` carry `custom_fields.cf_vixxo_link_type_of_request: "Profile Update"`.

The compliant-outcome `tickets_manage update` PUT body must include:

```json
{
  "type": "Account Update",
  "custom_fields": {
    "cf_vixxo_link_type_of_request": "Profile Update"
  },
  "tags": ["coi", "risk-compliance-routed", "coi-reviewed", "coi-compliant", "coi-accepted"],
  "status": 4
}
```

(Replace `status: 4` with `5` only if the operator explicitly says Closed instead of Resolved. Tag list must include the existing `coi` and `risk-compliance-routed` tags — Freshdesk's `tags` array on update **replaces** the full set, it does not append, so always include the existing tags plus the new ones.)

If a future API change rejects this key with `400 invalid_value`, re-discover by `tickets_manage get` against any recent Account Update ticket and inspect `custom_fields` for the field whose value is `Profile Update`. Update this section with the new key.

### Queue scope (first-run discovery)

On the first Mode B invocation in a session, confirm the COI queue filter with the operator before pulling tickets. Use this as the candidate filter:

```
group_id:159000485013 AND status:2 AND tag:'COI'
```

> **Tag is case-sensitive.** Freshdesk stores the upstream COI triage tag as **`COI`** (uppercase). Searching with `tag:coi` (lowercase) returns 0 results — confirmed empirically 2026-05-04. Always quote the tag in single quotes (`tag:'COI'`) so the filter parser preserves the case exactly.

Show the operator the count and 3-5 sample subjects, and ask whether to:

- proceed with this filter, or
- broaden to `email_config_id` for `COI@vixxo.com` (some COI submissions may arrive untagged), or
- restrict further (e.g., only `tag:'COI' AND tag:'risk-compliance-routed'`).

Cache the chosen filter for the rest of the session. While iterating, **filter out** tickets whose requester email is `donotreply@vixxo.com` or that match the daily CSV rollup pattern unless the operator explicitly asks for rollup cleanup (see "Daily CSV rollup cleanup" below).

**Freshdesk search lag (operator-discovered 2026-05-06):** after batch writes, `/search/tickets` may temporarily return stale Open results. When continuing to a next page or confirming remaining queue volume, treat search as a candidate list only. For every non-rollup candidate, direct-fetch `GET /api/v2/tickets/{id}` and use that record's `status`, `type`, `tags`, and `custom_fields` as the source of truth.

**Rate limiting:** Freshdesk may return `429 Too Many Requests` during attachment pulls or verification loops. Use modest pacing and retry with short backoff (for example 10-30 seconds) rather than re-running the whole batch. Write scripts should print per-action `OK` / `FAIL` labels so a retry can target only failed or unverified items.

### Per-ticket workflow

For each ticket on the page (oldest-first by default):

1. **Pull the ticket** with `tickets_manage get` (full conversation + attachments).
2. **Locate the COI**:
   - **If the COI is an attachment (typical — PDF/JPG ACORD 25):** run `scripts/fetch_coi_attachments.py --ticket-id <id>` to download every attachment on the ticket and on every conversation entry. The script reads `FRESHDESK_DOMAIN` and `FRESHDESK_API_KEY` from env (already set in `.cursor/mcp.json` for this workspace), saves binaries to `.tmp/coi-review/<ticket-id>/`, and writes a `manifest.json` listing each attachment with its `saved_path`, `content_type`, and source (`ticket` or `conv:<id>`). The agent's Read tool auto-converts PDFs to text and supports PNG/JPG/GIF/WEBP, so once the manifest is written, read each attachment from disk to extract COI fields. See `scripts/README.md` for full usage.
   - **If the COI is pasted in the body** or in a forwarded email body, extract it directly from the conversation text in the manifest (`description_text` and `conversations[].body_text_preview`).
   - **If neither is present**, post a private note to that effect and ask the operator how to proceed (skip / request COI from sender / mark as `coi-blocked` and Pending).
   - **Do not invent COI fields you cannot see.** If a PDF is image-only and Read returns no extractable text, flag it as `coi-blocked` and request the operator either OCR locally or ask the SP to resubmit a text-based PDF.
3. **Identify the requester**: `requester.email` and `requester.name` from the ticket. This is who the public reply will go to.
4. **Run the review** (steps 1-3 of "Workflow" above) using `references/vixxo-requirements.md`.
5. **Draft the artifacts** for operator approval, in this order:
   1. **Internal private note (Findings audit)** — full Findings table (Compliant / Missing / Deficient / Needs clarification per checklist item) plus the compliance summary line. This is the durable record on the ticket. Use `assets/freshdesk-internal-note-template.md` as the skeleton.
   2. **Public reply body** — formal SP-facing message. Use `assets/freshdesk-reply-deficient.md` if there are deficiencies, or `assets/freshdesk-reply-compliant.md` if the COI is fully compliant.
   3. **Compliant-only second internal note (Siebel handoff)** — when the COI is compliant, draft a second, short private note with this exact text:

      > This COI was confirmed as compliant, please upload to Siebel and update Additional SC Info tab.

      Skip this artifact for any non-compliant outcome.
   4. **Proposed ticket actions** — `type`, custom fields, tags, and status to set, depending on outcome:

      | Outcome | `type` | Custom fields to set | Add tags | Status |
      |---|---|---|---|---|
      | Deficient — corrections requested from SP | leave as `COIs` | **`cf_sp: "<SP company name>"`** (required for status:4 — see note below) | `coi-reviewed`, `coi-deficient` | **Resolved (`status: 4`)** — SP's reply will auto-reopen the ticket with the corrected COI attached |
      | Compliant — COI accepted | **`Account Update`** | **`cf_vixxo_link_type_of_request: "Profile Update"`** + **`cf_sp: "<SP company name>"`** | `coi-reviewed`, `coi-compliant`, `coi-accepted` | Operator's call — default Resolved (`4`), Closed (`5`) only on explicit operator request |
      | Needs clarification only — non-blocking questions | leave as `COIs` | (none) | `coi-reviewed`, `coi-clarification-pending` | Pending (`status: 3`) |
      | Missing/illegible COI — cannot review | leave as `COIs` | (none) | `coi-blocked`, `coi-missing-attachment` | Pending (`status: 3`) |
      | Duplicate / related cleanup | leave as `COIs` | **`cf_sp: "<SP company name>"`** if resolving | `coi-reviewed`, `coi-duplicate`, `coi-related-cleanup` | Resolved (`status: 4`) if no separate action is needed on that duplicate thread |
      | Daily CSV rollup cleanup | leave as `COIs` | **`cf_sp: "Daily COI CSV Rollup"`** and clear stale `cf_vixxo_link_type_of_request` | `coi-reviewed`, `coi-rollup-cleanup` | Closed (`status: 5`) when the operator explicitly asks to clean up rollups |
      | Internal exception review needed | leave as `COIs` | `cf_sp: "<SP company name>"` when known | `coi-reviewed`, `coi-blocked`, `coi-exception-review` | Pending (`status: 3`) |

      Keep the existing `COI` and `risk-compliance-routed` tags in place; do not strip them. Do **not** add `awaiting-sp-resubmission` on the deficient outcome — the ticket is resolved and will reopen on SP reply, so a "waiting" tag would mislead the queue.

      **Never forward deficient COI to AP Help.** Deficient outcomes resolve the FD ticket and wait for the SP/broker to resubmit on the same thread. `aphelp@vixxo.com` is for payment/AP intake only — not COI compliance review or deficiency follow-up.

      **Required field on resolution (operator-discovered 2026-05-04):** any `tickets_manage update` (or REST `PUT /api/v2/tickets/{id}`) that sets `status: 4` (Resolved) **must** include `custom_fields.cf_sp: "<SP company name>"` — Freshdesk rejects the call with `{"field":"custom_fields.cf_sp","message":"It should be a/an String","code":"missing_field"}` otherwise. This applies to both `type: "COIs"` and `type: "Account Update"`. Set `cf_sp` to the SP's legal/contracting name as it appears on the COI (free-text string; no Vixxo SP-number prefix required for COI tickets). Pending (`status: 3`) does NOT trigger this requirement, so clarification-only tickets do not need `cf_sp`.

      **Stale Account Update custom field:** when a ticket is updated back to `type: "COIs"` after previously carrying Account Update metadata, clear any stale `custom_fields.cf_vixxo_link_type_of_request` value (set it to `null` in the REST body if the API accepts it). Otherwise a deficient `COIs` ticket can misleadingly retain `Profile Update` from a prior compliant/account-update state.

      **Tag length cap:** every individual tag must be **≤ 32 characters** (Freshdesk schema). Verified empirically 2026-05-04 — a 36-char tag (`internal-forward-rerouted-to-broker`) was rejected with `{"field":"tags","message":"It should only contain elements that have maximum of 32 characters","code":"invalid_value"}`. Keep new tags short (e.g., `coi-broker-reroute` is 18 chars — good; `internal-fwd-broker` is 19 chars — also good).
6. **Wait for explicit approval** ("send it", "go", "approved", or equivalent) before any Freshdesk write. The operator may approve the artifacts as-is, edit any of them, or skip the ticket.
7. **On approval, execute in this order:**
   1. `conversations_manage create_note` with the **Findings audit** note body (always first — durable record before the SP-facing send).
   2. `conversations_manage create_reply` with the public reply body. **No BCC, no forward, no `to_emails` override** — the default reply addresses the requester via the thread. (Internal-forward COIs are the documented exception — see "Internal-forward COI handling" below.)
   3. **Compliant-only:** `conversations_manage create_note` with the **Siebel handoff** note body (placed after the public reply so it sits at the top of the activity stream as the actionable handoff to the next reviewer).
   4. **Ticket update — REST API bypass (mandatory for status: 4).** The MCP `tickets_manage update` action returns generic `Validation failed` for any payload that sets `status: 4`, even when all required fields are present (confirmed 2026-05-04; sister bug AIA-489 in `VIXXO-freshdesk-invoice-review`). Use the direct Freshdesk REST API instead. Use the per-batch PowerShell script pattern at `.tmp/coi_review_writes.ps1` (or one-off `Invoke-RestMethod`). The PUT body must include `type`, `custom_fields.cf_sp`, `tags`, and `status` per the table above. For the compliant outcome, also include `"type": "Account Update"` and `"custom_fields": {"cf_vixxo_link_type_of_request": "Profile Update", "cf_sp": "<SP company name>"}`.

      Reminder: Freshdesk's `tags` array **replaces** the full tag set on update, so include the existing `COI` and `risk-compliance-routed` tags alongside the new ones in the same call. Use UTF-8 encoding for the request body (`-Body ([System.Text.Encoding]::UTF8.GetBytes($json))`) — em-dashes and smart quotes get mangled otherwise.

      Pending (`status: 3`) updates DO work via the MCP `tickets_manage update`, so clarification-only and missing-COI outcomes can use the MCP path directly.
8. **Verify writes from direct ticket records.** After writes complete, direct-fetch the updated tickets with `GET /api/v2/tickets/{id}` and verify `status`, `type`, `tags`, `cf_sp`, and for compliant tickets `cf_vixxo_link_type_of_request`. If verification hits `429`, wait briefly and retry the readback rather than assuming failure. Do not use search results alone for write verification.
9. **Confirm the writes back to the operator** with the ticket URL: `https://vixxo-helpdesk.freshdesk.com/a/tickets/{ticket_id}`. Call out the new `type`, custom-field key/value, and final status explicitly. Then move to the next ticket on the page.

### Duplicate, related, and exception handling

Some COI tickets are follow-on replies, duplicate submissions, or parallel threads for the same SP and broker. If a duplicate thread does not need a separate SP-facing action:

1. Post a private note that identifies the primary related ticket, explains why no public reply is being sent from the duplicate, and records any attached-file caveat.
2. Do **not** send a public reply from the duplicate thread.
3. Resolve the duplicate with `coi-reviewed`, `coi-duplicate`, and `coi-related-cleanup` tags, preserving `COI` and `risk-compliance-routed`.
4. Continue substantive review/correction requests on the primary ticket only.

For tickets needing internal exception decisions (for example WC/EL limits below Vixxo expectations, Canadian-equivalent coverage questions, or a broker stating coverage cannot be provided):

1. Do **not** mark compliant by exception.
2. Post a private note summarizing the otherwise-compliant items and the exact exception question.
3. Move the ticket Pending with `coi-reviewed`, `coi-blocked`, and `coi-exception-review`.
4. Do not send a public acceptance reply unless the operator explicitly confirms the exception is approved.

### Daily CSV rollup cleanup

Daily CSV rollup tickets are system/batch notifications, not SP-facing COI submissions. Operator-confirmed 2026-05-13: when the operator asks to clean up the queue, close these rollup tickets rather than leaving them Open.

Detection:

1. `type: "COIs"` and direct ticket `status: 2` Open.
2. Subject matches `Certificates of Insurance - M/D/YYYY`.
3. Description text matches `Certificates of Insurance for M/D/YYYY attached.`
4. Attachment is a CSV named like `coi_YYYYMMDD.csv`.
5. Requester is the system/distribution sender for the rollup, not an SP or broker.

Handling:

1. Do **not** review the CSV contents as a COI.
2. Do **not** send a public reply or broker forward.
3. Preserve existing tags and add `coi-reviewed` and `coi-rollup-cleanup`.
4. Update the ticket with:

   ```json
   {
     "type": "COIs",
     "status": 5,
     "custom_fields": {
       "cf_sp": "Daily COI CSV Rollup",
       "cf_vixxo_link_type_of_request": null
     },
     "tags": ["<existing tags>", "coi-reviewed", "coi-rollup-cleanup"]
   }
   ```

5. Verify by direct ticket fetch or by the update response itself. Do not rely on Freshdesk search immediately after the write because search can show just-closed rollups as stale Open candidates.

### Internal-forward COI handling (operator-confirmed 2026-05-04)

Some COI tickets originate as **internal forwards** — a Vixxo employee (e.g., `vanessa.pepin@vixxo.com`, `michele.kautz@vixxo.com`) receives the COI directly from the broker / insurer and forwards it into `COI@vixxo.com`. The original sender chain looks like: `Broker → SP (cc COI@vixxo.com) → internal Vixxo person forwards to COI@vixxo.com`. The Freshdesk ticket's requester ends up being the internal forwarder, not the broker.

Detection: ticket requester email is `*@vixxo.com` AND the description / first conversation entry quotes a `From:` line with an external broker / insurer email (`*@cinfin.com`, `*@marshmma.com`, `*@conexusins.com`, `*@fedins.com`, etc.) on a date earlier than the forward.

Handling rule (operator-confirmed 2026-05-04): the SP-facing deficiency notice goes **directly to the broker**, not to the internal forwarder. The broker is the action owner; the internal forwarder is just a passthrough. Steps:

1. **Pre-reply internal note** — explain the reroute. Include the broker's email, the original send date, the internal forwarder's name/email, and the conversation id of the (forthcoming) forward call. Use the `coi-broker-reroute` tag (≤ 32 chars) on the final ticket update.
2. **Send via `POST /api/v2/tickets/{id}/forward`** (REST API), NOT `create_reply`. The `multiple_to` feature is disabled on this Freshdesk tenant, so `to_emails` overrides on `/reply` return `400 inaccessible_field`. The `/forward` endpoint accepts `to_emails` and `cc_emails` natively. Body: same deficiency content as a normal `create_reply` would carry, just delivered as a forward. The broker's reply will land back in Freshdesk and auto-reopen the ticket with the corrected COI attached.
3. **Findings audit note** — same as the standard flow (Findings + outcome).
4. **Ticket update** — same as the standard deficient/compliant outcome from the table above, with the `coi-broker-reroute` tag added to the tag list.

Do NOT post a separate `create_reply` to the internal forwarder — that pollutes their inbox with an SP-facing message they did not need to see. The internal forwarder is informed only via the ticket activity stream (which their notification preferences may or may not surface).

### Page pause

After a page of tickets (default 10), pause and ask the operator: continue to the next page, deep-dive a specific ticket, or stop. Do not roll forward automatically.

## Output format

Structure your reply to the user in three clearly labeled sections, in this order:

### 1. Compliance summary
A short statement: either *"This COI meets Vixxo's minimum requirements"* or *"This COI does NOT meet Vixxo's minimum requirements. The following items are missing or need clarification:"*

### 2. Findings
For every requirement, state whether it is **Compliant**, **Missing**, **Deficient**, or **Needs clarification**, with a one-line note. Group by coverage line (General Liability, Auto, WC/EL, Umbrella, Additional Insured / Endorsements / Waivers / Notice, Certificate Holder, Dates). Include exact values from the COI where useful (e.g., "GL Each Occurrence: $1,000,000 — Compliant").

### 3. Reply draft
A formal reply addressed to the service provider. Structure depends on mode:

**Mode A (ad-hoc / standalone email)** — use `assets/email-template.md`:

- **Subject line** — e.g., *"Certificate of Insurance — Items Required for Compliance"* (you may include the SP's name and/or COI effective date).
- **Salutation** — generic ("Dear [Service Provider Contact],") unless the user has given you a name.
- **Opening** — thank the SP for sending the COI and state that, upon review, certain items do not meet Vixxo's minimum requirements and need to be corrected or clarified before the COI can be accepted.
- **Itemized list** — bullet only the deficiencies, each phrased as a specific, actionable request (e.g., *"Please add additional insured endorsement CG 20 37 04/13 (or equivalent) for completed operations on the General Liability policy."*). Reference exact form numbers/editions, exact wording, and the certificate holder address verbatim where applicable.
- **Closing** — ask the SP to have their broker issue an updated COI reflecting the corrections and send it to **COI@vixxo.com**, offer to answer questions, and sign off formally.

**Mode B (Freshdesk public reply)** — use `assets/freshdesk-reply-deficient.md` or `assets/freshdesk-reply-compliant.md`:

- **No subject line** — Freshdesk inherits it from the ticket.
- Same opening / itemized list / closing structure as Mode A, but the closing **must instruct the SP to reply to the existing thread** (not to send to `COI@vixxo.com`) so the resubmitted certificate stays attached to the same ticket and avoids the `COI@vixxo.com → SPM ingest` circular reference.
- **No BCC, no `to_emails` override, no `/forward`** when posting via `conversations_manage create_reply`.

Keep the tone professional, neutral, and non-accusatory in both modes. Do not use contractions excessively. Do not threaten contract termination or invoice holds unless the user explicitly asks for that escalation.

## Important rules

- **Never invent values.** If a field is illegible or absent on the COI, treat it as missing and ask for it in the email — do not guess limits or dates.
- **Never mark something Compliant by inference.** If the COI does not actually show CG 20 37 04/13 (or equivalent), do not assume it is included just because CG 20 10 is present. They are separate endorsements. Use `references/endorsement-equivalents.md` to decide whether a submitted form is an acceptable equivalent.
- **Waiver of Subrogation must apply to all three lines** (GL, Auto, WC/EL). Confirm each one individually; if only "Waiver of Subrogation applies" is written without specifying the lines, flag it as needs clarification. For WC WOS, consult `references/state-law-quick-reference.md` — several states prohibit or limit WC waivers (KY, NH, monopolistic fund states, construction bans in MO/OR/KS).
- **The Additional Insured wording is exact.** The Vixxo language is long and specific (see `references/vixxo-requirements.md` for the verbatim text). If the SP's COI uses generic "Vixxo Corporation is named as Additional Insured," flag it as deficient and request the full wording.
- **Certificate Holder address must match exactly.** A different suite number, misspelled street, or wrong ZIP is a deficiency.
- **If the COI is expired or expires within 30 days**, flag the dates and request a renewal certificate.
- **If you are unsure** whether an item meets the requirement, place it under "Needs clarification" rather than guessing — and ask about it in the email.

## Reference files

- `references/vixxo-requirements.md` — Full verbatim Vixxo additional insured language, required endorsement form numbers and editions, certificate holder address, and a per-requirement checklist. Read this file at the start of every review.
- `references/endorsement-equivalents.md` — Endorsement equivalents map for every Sample COI 2026 Description of Operations provision (AI ongoing/completed, auto AI, primary/non-contributory, WOS by line, notice of cancellation, umbrella forms, carrier proprietary examples). Read when evaluating non-ISO or older-edition endorsements.
- `references/state-law-cancellation-wos.md` — State law analysis for cancellation notices and WC waiver of subrogation (prohibited states, partial-protection states, monopolistic fund states, COI review actions).
- `references/state-law-quick-reference.md` — One-page reviewer quick reference (tier tables, decision shortcuts, endorsement lookup).
- `assets/endorsement-equivalents.pdf` — PDF export of the endorsement equivalents reference (regenerate with `scripts/build_endorsement_equivalents_pdf.py`).
- `assets/state-law-cancellation-wos.pdf` — PDF export of the full state law analysis (regenerate with `scripts/build_state_law_pdfs.py`).
- `assets/state-law-quick-reference.pdf` — One-page landscape PDF quick reference (regenerate with `scripts/build_state_law_pdfs.py`).
- `assets/email-template.md` — Standalone email skeleton for **Mode A** (ad-hoc COI review outside Freshdesk). Includes copy-paste deficiency phrasings.
- `assets/freshdesk-reply-deficient.md` — **Mode B** public reply template for COI tickets with deficiencies. No subject line (Freshdesk inherits it); no BCC; addresses the requester via the existing thread.
- `assets/freshdesk-reply-compliant.md` — **Mode B** public reply template for COI tickets where the certificate is fully compliant.
- `assets/freshdesk-internal-note-template.md` — **Mode B** internal-note skeleton that records the full Findings table on the ticket as a durable audit trail before the SP-facing reply is sent.
- `scripts/fetch_coi_attachments.py` — **Mode B** helper. Downloads every attachment on a Freshdesk ticket (and on each conversation reply) via REST so the agent can read the COI binary directly. Stdlib only — no pip installs. Reads `FRESHDESK_DOMAIN` and `FRESHDESK_API_KEY` from env. See `scripts/README.md`.
- `scripts/README.md` — Usage notes for `fetch_coi_attachments.py` (env, output layout, troubleshooting).
