# No-Email Actions

Variant of **`sp-voicemail-triage`** — identical Phase 1 triage; Phase 2 **never
sends outbound email**.

## What runs (automatic)

| Action | Tool | Notes |
| --- | --- | --- |
| Freshdesk internal note | `create_ticket_note` (private) | Full triage packet + **recommended** route |
| Salesforce Lead note | SF MCP | Onboarding branch when Lead found |
| Freshdesk resolve | `update_ticket` status 5 + `cf_sp` | Same close rules as parent |

## What does **not** run

| Blocked action | Tool | Reason |
| --- | --- | --- |
| Freshdesk ticket forward | `forward_ticket` | Sends email to routing address |
| Outlook forward | `forward-mail-message` | Sends email |
| Freshdesk outbound email | `create_outbound_email` | Sends email |
| M365 send/reply | `send-mail-message`, `reply-mail-message` | Sends email |

The internal note records **Recommended forward to:** `{address}` so
{{employee_name}} or another workflow can route manually.

## Write order

```
internal note → Salesforce Lead note (if applicable) → resolve Freshdesk
```

No forward step.

## Batch script

From this skill directory:

```bash
python scripts/batch_process_freshdesk.py
```

Equivalent to parent script with `--no-email`.

## Shared reference

Classification, callback rules, company vetting, and voicemail intake filter are
unchanged — read from `../sp-voicemail-triage/reference/`.
