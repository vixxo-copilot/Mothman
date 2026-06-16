# Cursor Automation Setup

Wire **`sp-voicemail-triage-webhook`** to an HTTP webhook that delivers WAV files.

## 1. Create the automation

Use the **automate** skill or the Automations editor:

| Setting | Value |
| --- | --- |
| **Trigger** | `webhook` |
| **Tools** | Microsoft 365, Freshdesk, Gateway, VixxoLink, Salesforce (as needed) |
| **Instructions** | Load and follow `.agents/skills/sp-voicemail-triage-webhook/SKILL.md` |

### Prompt template (automation instructions)

```markdown
You are running the sp-voicemail-triage-webhook skill.

1. Parse the webhook body per reference/webhook-payload.md.
2. Validate auth per reference/webhook-security.md.
3. Transcribe the WAV attachment verbatim.
4. Run the same Phase 1 + Phase 2 pipeline as sp-voicemail-triage using the
   shared reference files under ../sp-voicemail-triage/reference/.
5. Return the JSON response schema from the webhook skill.
6. Honor dry_run when metadata.dry_run is true.

Do not scan Outlook or Freshdesk queues — only process this webhook payload.
```

## 2. After save — webhook URL

Cursor generates the webhook URL **after** the automation is saved. Copy it into
the upstream system (telephony middleware, Power Automate, custom app).

Configure webhook authentication in the editor before accepting production
traffic.

## 3. Upstream POST shape

Prefer **multipart** with:

- File part: `voicemail` (`.wav`)
- JSON part: `metadata` (optional fields from webhook-payload.md)

## 4. Freshdesk-originated voicemails

When Freshdesk (or another system) creates the webhook, include
`freshdesk_ticket_id` in metadata so Phase 2 uses:

- `create_ticket_note`
- `forward_ticket`
- `update_ticket` (resolve)

Without a ticket id, Phase 2 sends a new M365 email via `send-mail`.

## 5. Testing

1. POST a sample WAV with `"dry_run": true` — expect triage JSON, no forwards.
2. POST again with `dry_run: false` and a test ticket id — verify internal note
   + routing.
3. POST a second WAV with the same `callback_number` within 72h — expect **one**
   combined forward (same-contact combine).

Sample validator (local):

```bash
python .agents/skills/sp-voicemail-triage-webhook/scripts/validate_webhook_payload.py payload.json
```
