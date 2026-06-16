# Scheduled Cursor Automation Setup

Wire **`sp-voicemail-triage`** or **`sp-voicemail-triage-fast`** to a cron trigger
for hands-off KSOnboarding voicemail processing.

## Prerequisites

| Variable | Purpose |
| --- | --- |
| `FRESHDESK_API_KEY` | Freshdesk REST (`.env` or `~/.vixxo/freshdesk_token`) |
| `FRESHDESK_DOMAIN` | `vixxo-helpdesk.freshdesk.com` |
| `OPENAI_API_KEY` | Whisper transcription (required for real transcripts) |

## Recommended: fast skill (scheduled)

Use **`sp-voicemail-triage-fast`** for cron jobs — WAV transcription + routing
**without** Gateway / Salesforce / Siebel / JDE vetting (much faster).

### Automation settings

| Setting | Value |
| --- | --- |
| **Trigger** | Cron (e.g. weekdays every 15–30 min, or hourly) |
| **Tools** | Shell / repo access; Freshdesk not required as MCP if using batch script |
| **Repo** | This assistant repo on `main` |

### Prompt template

```markdown
Run the SP voicemail fast batch for Freshdesk KSOnboarding.

1. Load `.agents/skills/sp-voicemail-triage-fast/SKILL.md`.
2. Execute:
   python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
3. Report the JSON summary (processed, transcribed, routed, closed, failed).
4. Do not run Gateway, Salesforce, or other vetting MCP calls — the script skips them.

If OPENAI_API_KEY is missing, report the error and stop.
```

## Full skill (with vetting in notes)

For **`sp-voicemail-triage`**, use the parent batch script (same transcription,
vetting table in notes marked deferred unless agent runs MCP separately):

```bash
python .agents/skills/sp-voicemail-triage/scripts/batch_process_freshdesk.py
```

## What the batch script does

1. Search open KSOnboarding tickets (paginated)
2. Keep subjects that **include** `New voicemail`
3. Download `.wav` from each ticket
4. Transcribe via **OpenAI Whisper** (`whisper-1`)
5. Classify, post internal note, forward (unless `--no-email`), resolve with `cf_sp`

Flags:

| Flag | Effect |
| --- | --- |
| `--skip-vetting` | Fast skill — vetting skipped in notes; no SF Lead MCP step |
| `--no-email` | No `forward_ticket` (sibling no-email skill) |
| `--no-transcribe` | Metadata-only fallback (not recommended for automation) |
| `--dry-run` | Triage only; no writes |

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| Placeholder transcript in notes | `OPENAI_API_KEY` missing or Whisper failed — check batch JSON |
| No tickets processed | Subject filter — must include `New voicemail` |
| Close fails | Tenant requires `custom_fields.cf_sp` — script sets `Unknown` |
