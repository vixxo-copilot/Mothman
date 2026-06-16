# Scheduled Cursor Automation Setup

Wire **`sp-voicemail-triage-fast`** to a cron trigger for hands-off KSOnboarding
voicemail processing.

## Transcription is mandatory

Every in-scope voicemail ticket **must** be transcribed from its **`.wav`
attachment** before any Freshdesk write (internal note, forward, or resolve).

If Whisper transcription fails — missing WAV, download error, or API failure —
the batch script **leaves the ticket unchanged** (open, no note, no forward).

Do **not** pass `--no-transcribe` in automation.

## What must be enabled

### 1. Repo secrets (`.env` in workspace root)

| Variable | Required | Purpose |
| --- | --- | --- |
| `FRESHDESK_API_KEY` | **Yes** | Search tickets, download WAV attachments, write on success |
| `OPENAI_API_KEY` | **Yes** | OpenAI Whisper (`whisper-1`) transcription |
| `FRESHDESK_DOMAIN` | No | Default `vixxo-helpdesk.freshdesk.com` |

Alternative for Freshdesk only: `~/.vixxo/freshdesk_token`.

The batch script loads `.env` automatically and **exits immediately** if
`OPENAI_API_KEY` is missing.

### 2. OpenAI API access

- Key must have access to the **Audio / Whisper** API (`/v1/audio/transcriptions`).
- Automation runner needs **network egress** to `api.openai.com`.
- WAV files must be under OpenAI's **25 MB** limit (voicemail WAVs normally are).

### 3. Freshdesk attachment access

- API key must read open KSOnboarding tickets and **download attachments**.
- Each voicemail notification ticket includes a **`.wav`** file — the script picks
  the first WAV on the ticket and transcribes it. No email-body transcript is used
  for classification in the batch path.

### 4. Cursor Automation configuration

| Setting | Value |
| --- | --- |
| **Trigger** | Cron (e.g. weekdays every 15–30 min, or hourly) |
| **Tools** | Shell / repo access (run Python batch script) |
| **Repo** | This assistant repo on `main` |
| **MCP** | Freshdesk MCP **not required** — REST batch script handles everything |

Do **not** enable Gateway, Salesforce, or other vetting MCPs for the fast skill —
vetting is skipped by design.

### 5. Runtime on the automation host

- **Python 3** available on `PATH`
- Outbound HTTPS to Freshdesk and OpenAI (not blocked by firewall)

## Recommended: fast skill (scheduled)

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

WAV download + Whisper + classify + forward + resolve — **no external vetting**.

### Prompt template

```markdown
Run the SP voicemail fast batch for Freshdesk KSOnboarding.

1. Load `.agents/skills/sp-voicemail-triage-fast/SKILL.md`.
2. Execute:
   python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
3. Report JSON summary: processed, transcribed, transcription_failed, routed, closed, failed.
4. Do not pass --no-transcribe. Do not invoke Gateway or Salesforce MCP.

If OPENAI_API_KEY is missing, the script exits — report that and stop.
If transcription_failed > 0, list those ticket IDs; tickets were left open unchanged.
```

## What the batch script does

1. Search open KSOnboarding tickets (paginated REST)
2. Keep subjects that **include** `New voicemail`
3. Download **`.wav`** attachment from each ticket
4. Transcribe via **OpenAI Whisper** (`whisper-1`) — **required**
5. On success only: classify, internal note, forward (unless `--no-email`), resolve
6. On transcription failure: **skip ticket** — no Freshdesk updates

## Flags

| Flag | Automation use |
| --- | --- |
| `--skip-vetting` | Injected by fast skill wrapper |
| `--no-email` | Only for manual no-email runs |
| `--no-transcribe` | **Never in automation** — skips STT; no writes unless dry-run preview |
| `--dry-run` | Preview only; no writes |

## Empty queue behavior

Every run still **searches Freshdesk**. If zero voicemail tickets match, the script
returns `processed: 0` and performs no triage writes.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Script exits immediately | `OPENAI_API_KEY` missing from `.env` |
| `transcription_failed` > 0 | WAV missing, download failed, or Whisper error — tickets left open |
| `no_wav_attachment` | Ticket has no `.wav` on attachments — fix upstream email intake |
| `processed: 0` | No open tickets with `New voicemail` in subject |
| Close fails (when transcribed) | Tenant requires `custom_fields.cf_sp` — script sets `Unknown` |

## Full skill batch (with vetting in agent path)

For **`sp-voicemail-triage`** agent runs with MCP vetting, use the parent skill.
The batch script shares the same **transcription-required** gate:

```bash
python .agents/skills/sp-voicemail-triage/scripts/batch_process_freshdesk.py
```
