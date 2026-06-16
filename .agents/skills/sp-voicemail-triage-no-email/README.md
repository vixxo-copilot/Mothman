# SP Voicemail Triage (No Email)

No-email variant of [`sp-voicemail-triage`](../sp-voicemail-triage/SKILL.md).

| Skill | Outbound email |
| --- | --- |
| `sp-voicemail-triage` | Forwards to SPM, AP, COI, recruitment, SR PM/support |
| **`sp-voicemail-triage-no-email`** | **None** — recommended route recorded in internal note only |
| `sp-voicemail-triage-webhook` | Same forwards as parent (WAV webhook intake) |

Shared triage rules: `../sp-voicemail-triage/reference/`

Batch:

```bash
python .agents/skills/sp-voicemail-triage-no-email/scripts/batch_process_freshdesk.py
```
