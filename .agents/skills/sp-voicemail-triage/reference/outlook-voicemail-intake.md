# Outlook Voicemail Intake — Extension 4046

Primary intake for **sp-voicemail-triage**. 8x8 sends voicemail notifications to
{{employee_name}}'s Outlook mailbox for **extension 4046** (Vendor Relations).

Freshdesk KSOnboarding is **legacy/optional** — use only when a duplicate ticket
exists for dedupe.

## Typical message shape

| Field | Example |
| --- | --- |
| **From** | `no-reply@8x8.com` |
| **Subject** | `New voicemail from Unknown via VENDOR RELATIONS` |
| **Body** | `Your extension 4046 just received a new voicemail.` |
| **Attachment** | `voicemail_Anonymous_07-28-2026_11-44-46.wav` |

Duration and received timestamp appear in the body footer — use for metadata only.
**Transcription source is the `.wav` / `.mp3` attachment**, not the email body.

## Folder location

Voicemails may land in **Inbox** or a rule-target subfolder (default lookup: **Inbox → VM**).

| Variable | Default | Purpose |
| --- | --- | --- |
| `VM_MAIL_FOLDER_NAME` | `VM` | Display name under Inbox, or `Inbox` to scan inbox directly |
| `VM_MAIL_FOLDER_ID` | *(unset)* | Stable Graph folder id override |

Resolve once and record the id when the folder name is non-obvious:

```bash
node .agents/skills/sp-voicemail-triage/scripts/outlook_graph_helper.mjs list-mail-folders
```

## Inclusion filter (all required)

1. Subject includes **`New voicemail`** (case-insensitive)
2. Subject includes **`via VENDOR RELATIONS`** (override: `VM_VIA_LABEL`)
3. Body preview includes **extension `4046`** (override: `VM_EXTENSION`)
4. From domain **`8x8.com`** (override: `VM_SENDER_DOMAIN`)
5. Has **audio attachment** (`.wav` or `.mp3`)
6. Not a forward (`FW:` prefix)
7. Within lookback window (`VM_LOOKBACK_DAYS`, default **7**)

## Graph auth path (batch + cloud)

Same cached token as **`sf-case-email-sync`**:

- `.cursor/bin/ms365-mcp/node_modules/@softeria/ms-365-mcp-server/dist/auth.js`
- Helper: `scripts/outlook_graph_helper.mjs`
- Batch: `scripts/batch_process_outlook.py`

M365 MCP (`list-mail-folder-messages`, `download-bytes`) is the interactive
fallback when the agent runs inside Cursor Desktop with MCP logged in.

## Batch commands

```bash
# Default — Outlook ext 4046 only
python .agents/skills/sp-voicemail-triage/scripts/batch_process_all.py

# Outlook only
python .agents/skills/sp-voicemail-triage/scripts/batch_process_outlook.py

# Include legacy Freshdesk KSOnboarding queue
python .agents/skills/sp-voicemail-triage/scripts/batch_process_all.py --freshdesk
```

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `VM_EXTENSION` | `4046` | 8x8 extension number in body |
| `VM_VIA_LABEL` | `VENDOR RELATIONS` | Subject `via …` label |
| `VM_SENDER_DOMAIN` | `8x8.com` | Sender domain filter |
| `VM_LOOKBACK_DAYS` | `7` | Batch window |
| `VM_MAIL_FOLDER_NAME` | `VM` | Folder display name or `Inbox` |
| `VM_MAIL_FOLDER_ID` | *(unset)* | Graph folder id override |
