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

Categories align with [categories.md](categories.md).

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
    "type": "<KSOnboarding | VixxoLink Support | Invoice Support | COIs | as appropriate>"
  }
}
```

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
