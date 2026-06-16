---
name: sp-voicemail-triage-webhook
description: >-
  Webhook-triggered SP voicemail triage. Accepts an HTTP webhook POST with a WAV
  recording plus optional metadata, transcribes the audio, then runs the same
  company vetting, classification, callback decision, Freshdesk notes, forwards,
  Salesforce Lead notes, and ticket resolve flow as sp-voicemail-triage. Use when
  a Cursor Automation webhook fires, an external telephony system posts a WAV,
  or the user says webhook voicemail triage.
---

# SP Voicemail Triage — Webhook

Event-driven variant of **`sp-voicemail-triage`**. Intake is an **HTTP webhook**
carrying a **`.wav` file** (required) and optional metadata — not an inbox or
Freshdesk queue scan.

**Shared pipeline:** classification, company vetting, callback rules, routing,
Freshdesk writes, and email forwards are identical to the parent skill. Read
those reference files from `../sp-voicemail-triage/reference/` — do not
duplicate rules here.

## When to use

- Cursor Automation with a **`webhook`** trigger delivers payload + WAV
- External system POSTs voicemail audio to the automation URL
- User says "webhook voicemail triage" / "process this WAV from the webhook"

**Do not use** for batch Outlook/Freshdesk scans — use **`sp-voicemail-triage`**.

## Operating modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Webhook (default)** | HTTP POST with WAV | Full pipeline on one payload |
| **Dry-run (opt-in)** | User or payload flag `dry_run: true` | Triage + vet only; no writes |

Phase 1 and Phase 2 match the parent skill (automatic routing; no approval gate).

## Webhook intake

See [reference/webhook-payload.md](reference/webhook-payload.md) for the full
contract and examples.

### Required

| Input | Rule |
| --- | --- |
| **WAV audio** | `audio/wav` or `audio/x-wav`; `.wav` extension; max **25 MB** |
| **Delivery** | Multipart field `voicemail` **or** JSON `audio_base64` + `audio_content_type` |

### Recommended metadata

| Field | Purpose |
| --- | --- |
| `callback_number` | Same-contact combine + routing |
| `caller_name` | Triage packet |
| `company_name` | Vetting + classification |
| `freshdesk_ticket_id` | Freshdesk note / forward / resolve path |
| `correlation_id` | Idempotency + audit (`webhook-{uuid}` if omitted) |
| `received_at` | ISO-8601 timestamp (default: now UTC) |
| `duration_seconds` | Optional; echo in packet |
| `dry_run` | `true` skips Phase 2 writes |

### Authenticate the webhook

Apply [reference/webhook-security.md](reference/webhook-security.md). Reject
unsigned or invalid requests before transcribing.

## Workflow

### 0. Parse webhook

1. Validate payload (`scripts/validate_webhook_payload.py` when files are on disk).
2. Extract WAV bytes to a temp path or hold in memory for transcription.
3. Normalize phone numbers (digits only for combine keys).
4. Record `correlation_id` in every log line and triage packet.

### 1. Transcribe WAV

1. Transcribe verbatim from the WAV attachment.
2. Mark `Transcript source: webhook wav transcription`.
3. Merge explicit metadata when transcript omits them:
   - `caller_name`, `company_name`, `callback_number` from payload win when
     transcript says "Not stated".
4. Extract SR #, invoice #, and other reference IDs from transcript text.

If transcription fails, set confidence **Low**, still run classification on
metadata + any partial transcript, and route to
`service.providermanagement@vixxo.com` with failure noted unless `dry_run`.

### 2. Same-contact combine (webhook)

Before routing, check pending/combine cache keyed by:

1. Normalized `callback_number`
2. Normalized `company_name`
3. `freshdesk_ticket_id` (same ticket → append to same item)

When a prior webhook item for the same key exists within **72 hours** (automation
memory, Freshdesk ticket thread, or explicit `combine_with_correlation_id` in
payload):

- Merge transcripts and metadata into **one** triage item
- Produce one forward / one Freshdesk note / one resolve
- Follow parent skill same-contact combine rules

See parent `SKILL.md` **Same-contact combine** section.

### 3. Triage + vet (Phase 1)

Identical to parent steps 3–5:

- [../sp-voicemail-triage/reference/categories.md](../sp-voicemail-triage/reference/categories.md)
- [../sp-voicemail-triage/reference/callback-rules.md](../sp-voicemail-triage/reference/callback-rules.md)
- [../sp-voicemail-triage/reference/company-vetting.md](../sp-voicemail-triage/reference/company-vetting.md)

Set **Source** to `Webhook {correlation_id}` plus `Freshdesk #{id}` when present.

### 4. Route (Phase 2)

Identical to parent steps 6–10:

- [../sp-voicemail-triage/reference/routing-actions.md](../sp-voicemail-triage/reference/routing-actions.md)
- [../sp-voicemail-triage/reference/freshdesk-internal-note-template.md](../sp-voicemail-triage/reference/freshdesk-internal-note-template.md)

**Freshdesk path** when `freshdesk_ticket_id` is set:

1. `create_ticket_note` (private) — include webhook correlation + WAV metadata
2. `forward_ticket` when routing table requires forward
3. Salesforce Lead note when onboarding branch applies
4. `update_ticket` resolve (`status: 5`)

**No Freshdesk ticket:**

- Use M365 `send-mail` to routing address with combined summary + transcript
  (no anchor message to forward — build the email body directly)
- Subject pattern: `Voicemail — {Company} — {Category} — callback {Yes|No}`

SR branch subject remains `{SR_NUMBER}, Need Assistance`.

### 5. Webhook response

Return JSON to the caller (Cursor Automation webhook ack or upstream system):

```json
{
  "correlation_id": "webhook-…",
  "status": "routed | dry_run | failed",
  "category": "Billing / Invoice Support",
  "callback_required": "Yes",
  "route_to": ["aphelp@vixxo.com"],
  "freshdesk_ticket_id": 12345,
  "actions": {
    "internal_note": "posted",
    "forward": "sent",
    "salesforce_lead_note": "n/a",
    "resolve": "done"
  },
  "errors": []
}
```

On failure, set `status: "failed"`, populate `errors`, and do not claim success.

## Output format

Use the parent skill triage packet template. Add:

| Field | Value |
| --- | --- |
| **Webhook correlation** | `{correlation_id}` |
| **Audio** | `{filename} · {duration_seconds}s · {bytes} bytes` |
| **Transcript source** | webhook wav transcription |

## Cursor Automation setup

See [reference/automation-setup.md](reference/automation-setup.md).

## Guardrails

- Work context only — Vixxo SP operations.
- Validate webhook auth before processing audio.
- Do not log or echo full `Authorization` headers.
- Phase 2 writes run automatically unless `dry_run: true`.
- Never invent recipient emails — Gateway / `list-users` only.
- Idempotency: if `correlation_id` was already processed successfully, return
  the prior result and skip duplicate forwards.

## Additional resources

| File | Purpose |
| --- | --- |
| [reference/webhook-payload.md](reference/webhook-payload.md) | POST body schema |
| [reference/webhook-security.md](reference/webhook-security.md) | Auth + validation |
| [reference/automation-setup.md](reference/automation-setup.md) | Cursor webhook wiring |
| [../sp-voicemail-triage/SKILL.md](../sp-voicemail-triage/SKILL.md) | Parent batch skill |
| [../sp-voicemail-triage/reference/](../sp-voicemail-triage/reference/) | Shared triage rules |
