# Scheduled Cursor Automation Setup

Wire **`sp-voicemail-triage-fast`** to a cron trigger for hands-off KSOnboarding
voicemail processing.

## Transcription is mandatory

Every in-scope voicemail ticket **must** be transcribed from its **audio attachment**
(`.wav` or `.mp3`) before any Freshdesk write (internal note, forward, or resolve).

**The notification email body does not contain the spoken message.** Triage content
comes exclusively from the attached audio file via **local faster-whisper**
(no OpenAI API key).

If transcription fails — missing audio, download error, missing ffmpeg, or STT
error — the batch script **leaves the ticket unchanged** (open, no note, no forward).

Do **not** pass `--no-transcribe` in automation.

## What must be enabled

### 1. Repo secrets (`.env` in workspace root)

| Variable | Required | Purpose |
| --- | --- | --- |
| `FRESHDESK_API_KEY` | **Yes** | Search tickets, download audio attachments, write on success |
| `FRESHDESK_DOMAIN` | No | Default `vixxo-helpdesk.freshdesk.com` |

Freshdesk fallback: `~/.vixxo/freshdesk_token` or `~/.vixxo/freshdesk_api_key`.

Optional Whisper tuning (defaults shown):

| Variable | Default | Purpose |
| --- | --- | --- |
| `WHISPER_MODEL` | `small` | faster-whisper model size (`tiny`, `base`, `small`, `medium`, …) |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8`, `float16`, etc. |

### 2. Python dependencies (one-time)

```bash
pip install -r .agents/skills/sp-voicemail-triage/scripts/requirements.txt
```

Installs **`faster-whisper`** (local Whisper inference). First transcription run
downloads model weights (~150MB for `small`).

### 3. Audio decoding

**ffmpeg** on `PATH` is recommended. If not installed, **PyAV** (installed with
`faster-whisper` via pip) can decode `.wav` / `.mp3` instead.

- Windows ffmpeg: [https://ffmpeg.org](https://ffmpeg.org) or `winget install ffmpeg`
- Verify: `python .agents/skills/sp-voicemail-triage/scripts/verify_transcription.py`

### 4. Freshdesk attachment access

- API key must read open KSOnboarding tickets and **download attachments**.
- Each voicemail notification ticket includes **`.wav` or `.mp3`** — the script
  prefers `.wav` when both exist.
- **Email/ticket body is not used for transcription.**

### 5. Cursor Automation configuration

| Setting | Value |
| --- | --- |
| **Trigger** | Cron (e.g. weekdays every 15–30 min, or hourly) |
| **Tools** | Shell / repo access (run Python batch script) |
| **Repo** | This assistant repo on `main` |
| **MCP** | Freshdesk MCP **not required** — REST batch script handles everything |

The automation host must have **Python 3**, **ffmpeg**, and **faster-whisper**
installed. No OpenAI API key or outbound access to `api.openai.com` is required
(after model download).

Do **not** enable Gateway, Salesforce, or other vetting MCPs for the fast skill.

### 6. Verify setup

```bash
python .agents/skills/sp-voicemail-triage/scripts/verify_transcription.py
python .agents/skills/sp-voicemail-triage/scripts/verify_transcription.py --load-model
```

First `--load-model` run downloads weights and may take several minutes.

## Recommended: fast skill (scheduled)

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

Audio download + local Whisper + classify + forward + resolve — **no external vetting**.

### Prompt template

```markdown
Run the SP voicemail fast batch for Freshdesk KSOnboarding.

1. Load `.agents/skills/sp-voicemail-triage-fast/SKILL.md`.
2. Execute:
   python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
3. Report JSON summary: processed, transcribed, transcription_failed, routed, closed, failed.
4. Do not pass --no-transcribe. Do not invoke Gateway or Salesforce MCP.

If verify_transcription.py fails, report missing ffmpeg or faster-whisper and stop.
If transcription_failed > 0, list those ticket IDs; tickets were left open unchanged.
```

## What the batch script does

1. Search open KSOnboarding tickets (paginated REST)
2. Keep subjects that **include** `New voicemail`
3. Download **audio attachment** (`.wav` or `.mp3`) from each ticket
4. Transcribe via **faster-whisper** — **required**
5. On success only: classify, internal note, forward (unless `--no-email`), resolve
6. On transcription failure: **skip ticket** — no Freshdesk updates

## Flags

| Flag | Automation use |
| --- | --- |
| `--skip-vetting` | Injected by fast skill wrapper |
| `--no-email` | Only for manual no-email runs |
| `--no-transcribe` | **Never in automation** |
| `--dry-run` | Preview only; no writes |

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Script exits on startup | `faster-whisper` not installed or `ffmpeg` missing |
| Slow first run | Model download — normal; subsequent runs reuse cached weights |
| `transcription_failed` > 0 | Audio missing, download failed, or STT error — tickets left open |
| `no_audio_attachment` | No `.wav`/`.mp3` on ticket |
| `processed: 0` | No open tickets with `New voicemail` in subject |

## Full skill batch

```bash
python .agents/skills/sp-voicemail-triage/scripts/batch_process_freshdesk.py
```
