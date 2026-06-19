# Routing Actions

Maps triage **category** → **Freshdesk internal note**, **email forward**, and
**ticket disposition**. Apply after transcription, classification, callback
decision, and [company vetting](company-vetting.md).

## Routing table

| Category | Forward to | Freshdesk disposition | Notes |
| --- | --- | --- | --- |
| VixxoLink Support | `service.providermanagement@vixxo.com` | Internal note + forward; resolve when routed | Include SP # if vetted |
| Technical / Trade Support | `service.providermanagement@vixxo.com` | Internal note + forward; resolve when routed | Same SPM path |
| General Inquiry | `service.providermanagement@vixxo.com` | Internal note + forward; resolve when routed | When no sharper bucket fits |
| Billing / Invoice Support | `aphelp@vixxo.com` | Internal note + forward; resolve when routed | |
| Payment Information | `aphelp@vixxo.com` | Internal note + forward; resolve when routed | |
| COI / Compliance (Insurance) | `COI@vixxo.com` | Internal note + forward; resolve when routed | |
| Coverage / Onboarding | See **Onboarding branch** below | Varies | |
| Service Request / Dispatch | See **SR assistance branch** below | Resolve after forward + note | |
| Wrong Number / Non-SP | None | Internal note only; resolve | No forward |
| Foul Language / Abusive | **None** | Internal note + resolve | **No forward** — profanity in transcript |
| Too Short (<10s) | **None** | Internal note + resolve | **No forward** — duration under 10 seconds |
| Blank / Minimal Speech | **None** | Internal note + resolve | **No forward** — blank or one/two words |
| Client / Customer Voicemail | **None** | Internal note + resolve | **No forward** — flagged for {{employee_name}} review; tag `client-voicemail-review` |
| Client Portal Support | `Amy.Grantham@vixxo.com` | Internal note + forward; resolve when routed | Internal note must state **client support needed** |

Categories align with [categories.md](categories.md).

## No-forward branches

These run **after** successful transcription and **before** forward. Each
**overrides** classification and SR vetting when matched.

### Foul language

When the **transcript** (from audio STT) matches a term on the foul-language
list in `scripts/batch_process_freshdesk.py`:

1. **Do not forward** email — skip forward regardless of what other keywords
   would have matched.
2. Post the **private internal note** (category `Foul Language / Abusive`,
   routing section states skip reason).
3. **Resolve** the ticket (`status: 5`, `cf_sp: Unknown`).
4. **Callback:** No; urgency Normal.

### Short duration (<10 seconds)

When voicemail **duration** (from 8x8 metadata `Duration: MM:SS`, or Whisper
audio length when metadata is missing) is **under 10 seconds**:

1. **Do not forward** email.
2. Post private internal note (category `Too Short (<10s)`).
3. **Resolve** the ticket.
4. **Callback:** No; urgency Normal.

### Blank / minimal speech

When the **spoken transcript** (STT text only, not email metadata) is **blank**
or **one or two words**:

1. **Do not forward** email.
2. Post private internal note (category `Blank / Minimal Speech`).
3. **Resolve** the ticket.
4. **Callback:** No; urgency Normal.

## Client / customer voicemail (review — no forward)

When vetting or heuristics identify the caller as a **Vixxo client/customer**
(not a service provider), and the ask is **not** client portal support:

1. **Do not forward** email — skip forward regardless of billing/SR keywords that
   might otherwise match.
2. Post private internal note (category `Client / Customer Voicemail`).
3. **Resolve** the ticket with tag `client-voicemail-review`.
4. **Callback:** Recommended; urgency High — {{employee_name}} reviews.

**Detection signals** (run after transcription, before SP category routing):

| Signal | Source | Notes |
| --- | --- | --- |
| Caller ID / company name | 8x8 metadata | Known client brands (e.g. `STRYKER CORPORA`) — **not** Gateway SP tracking prefixes like `STRYKER ONLY` |
| Phone number | Gateway customer contacts + Salesforce Lead/Case/Contact/Account | Normalize to last 10 digits; see [company-vetting.md](company-vetting.md) |
| Transcript intent | STT text | Caller describes themselves as a client/customer, their stores/locations, etc. |

**Distinguish customer vs SP:** Gateway Siebel SP display names may include
tracking prefixes (`KS`, `CCPAY`, **`STRYKER ONLY`**, trailing `ONLY`). Those
label **SP-side** accounts, not the Stryker **client** corporation. Caller ID
`STRYKER CORPORA` is a client signal; Gateway SP `STRYKER ONLY — …` is not.

## Client portal support (forward to Amy)

When the transcript indicates **client portal / customer portal support** (not
VixxoLink / SP portal):

1. **Forward** to `Amy.Grantham@vixxo.com` via `forward_ticket` or
   `forward-mail-message`.
2. Forward body and internal note must include **Client support needed**.
3. Post private internal note (category `Client Portal Support`).
4. **Resolve** Freshdesk after forward; tag `client-portal-support`.

**Keywords:** client portal, customer portal, store portal, facilities portal,
client support, customer support portal, portal support.

**Exclude:** VixxoLink, dispatch board, accept work — those remain SP → SPM path.

This branch runs **before** SP category routing when matched. It overrides
billing/AP keyword false matches for known client callers (e.g. Stryker payment
questions still route here for review, not `aphelp@vixxo.com`).

## Onboarding branch (want to join as SP)

Applies when the caller wants to **onboard as a service provider** (Coverage /
Onboarding category, or clear recruitment intent).

1. Run [company vetting](company-vetting.md) — **Salesforce Lead search is
   mandatory**.
2. **Lead found** in Salesforce:
   - Freshdesk **internal note** referencing Salesforce Lead Id / number, full
     transcript, callback number, and vetting summary.
   - Add a **Salesforce note** on the Lead with the transcribed voicemail (Task
     or Chatter — see company-vetting.md). Post automatically.
   - **Resolve** the Freshdesk ticket (`status: 5`). Set `type: KSOnboarding`
     when updating if not already set.
3. **No Lead found**:
   - **Forward** ticket to `spm-recruitment@vixxo.com` via `forward_ticket`
     (include transcript + callback number in body).
   - Freshdesk **internal note** documenting no SF match and recruitment
     routing.
   - **Resolve** Freshdesk ticket after forward.

Do **not** send onboarding recruitment mail when vetting shows a **Known SP**
already in Siebel unless the caller explicitly says they are a new entity or
re-onboarding.

## SR assistance branch

Applies when the caller needs help with a **Service Request** (SR cited or
clear SR/dispatch ask).

1. Extract **SR number** from transcript. If missing, internal note only — do
   not forward; flag for callback.
2. Resolve SR via **`vixxolink_resolve_service_request`** and/or
   **`gateway_get_service_request`**.
3. From the Gateway SR payload, collect **Project Manager** and **Support
   staff** email addresses (field names vary by program — inspect the response
   for PM, support, CSR, or account-team contacts). Use `list-users` (M365) to
   validate addresses; never invent emails.
4. **Forward** to PM + Support staff (and `service.providermanagement@vixxo.com`
   only if no PM/support emails are on the SR — note the gap in the internal
   note).
5. Set forward **subject** to exactly: `{SR_NUMBER}, Need Assistance` (example:
   `12345678, Need Assistance`).
6. Freshdesk **internal note**: transcript, SR summary, PM/support recipients,
   vetting summary.
7. **Resolve** Freshdesk ticket (`status: 5`).

For **email-sourced** voicemails (no Freshdesk ticket), use M365
`forward-mail-message` with the same subject and recipients.

When **multiple Outlook voicemails** share a contact, forward **once** using
the **newest** message as the anchor. Put the combined summary and every
transcript in the forward `Comment` (see SKILL.md same-contact combine rule).

### Same-contact combine (Freshdesk + Outlook)

Match key (any of):

- Same callback phone number (normalized)
- Same company name (normalized)
- Same Freshdesk requester email

Actions:

1. Triage each message; merge into one packet.
2. One **internal note** listing all source ticket/message IDs and transcripts.
3. One **forward** with combined summary + per-VM transcript blocks.
4. One **resolve** after forward completes.

Do not forward twice to the same recipient for the same contact in one run.

## Forward mechanics

### Freshdesk ticket

Use `forward_ticket`:

```json
{
  "ticket_id": "<id>",
  "forward": {
    "body": "<routing summary + transcript + callback number>",
    "to_emails": ["<recipient@vixxo.com>"],
    "include_original_attachments": true
  }
}
```

Add additional `to_emails` entries for SR PM/support branch.

Always post the **internal note** (`create_ticket_note`, `"private": true`)
**before** forward + resolve so the audit trail exists even if forward fails.

### Outlook voicemail (no Freshdesk ticket)

Use `forward-mail-message` with:

- `ToRecipients`: routing address(es) from the table above
- `Comment`: triage summary + transcript
- Override **subject** for SR branch: `{SR_NUMBER}, Need Assistance`

### Resolve Freshdesk ticket

Use `update_ticket`:

```json
{
  "ticket_id": "<id>",
  "ticket": {
    "status": 5,
    "type": "<KSOnboarding | VixxoLink Support | Invoice Support | COIs | as appropriate>",
    "custom_fields": {
      "cf_sp": "<SP number or Unknown>"
    }
  }
}
```

This tenant requires `cf_sp` when closing — use `Unknown` when the SP is not
identified during triage.

Only resolve tickets that pass the voicemail filter in
[freshdesk-voicemail-filter.md](freshdesk-voicemail-filter.md) (subject includes
`New voicemail`).

Freshdesk requires a valid `type` when changing status. Allowed values include:
`Account Update`, `Invoice Support`, `VixxoLink Support`, `Credit/Debit
Submission`, `NTE`, `Capital Project`, `SWS`, `COIs`, `No Action Required`,
`KSOnboarding`.

## Internal note template

Use [freshdesk-internal-note-template.md](freshdesk-internal-note-template.md).

## Automatic routing (Phase 2)

All actions below run **automatically** when this skill is invoked. No separate
approval step. Opt out only when the user explicitly requests **dry-run**.

| Action | When |
| --- | --- |
| Post Freshdesk internal note | Every routed item |
| Forward email / Freshdesk forward | Per routing table or branch rules |
| Resolve Freshdesk ticket | After note + forward (or note-only paths) |
| Salesforce Lead note | Onboarding branch when Lead found |

**Write order:** internal note → forward → Salesforce Lead note → resolve.
