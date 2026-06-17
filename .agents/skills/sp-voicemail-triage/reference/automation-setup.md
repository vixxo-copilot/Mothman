# Scheduled Cursor Automation Setup

Wire **`sp-voicemail-triage-fast`** to a cron trigger for hands-off KSOnboarding
voicemail processing.

## Transcription is mandatory

Every in-scope voicemail ticket **must** be transcribed from its **audio attachment**
(`.wav` or `.mp3`) before any Freshdesk write (internal note, forward, or resolve).

**The notification email body does not contain the spoken message.** Triage content
comes exclusively from the attached audio file via **local faster-whisper**
(no OpenAI API key).

If transcription fails — missing audio, download error, or STT error — the batch
script **leaves the ticket unchanged** (open, no note, no forward).

Do **not** pass `--no-transcribe` in automation.

## One-time bootstrap (required before first cron run)

Run once on the automation host (or after Python upgrades):

```bash
python .agents/skills/sp-voicemail-triage/scripts/setup_transcription.py
```

This:

1. `pip install`s `faster-whisper` from `scripts/requirements.txt`
2. Verifies PyAV/ffmpeg decoding
3. Pre-downloads the Whisper model (`small` by default)

## What must be enabled

### 1. Repo secrets (`.env` in workspace root)

| Variable | Required | Purpose |
| --- | --- | --- |
| `FRESHDESK_API_KEY` | **Yes** | Search tickets, download audio attachments, write on success |
| `FRESHDESK_DOMAIN` | No | Default `vixxo-helpdesk.freshdesk.com` |

Freshdesk fallback: `~/.vixxo/freshdesk_token` or `~/.vixxo/freshdesk_api_key`.

Optional Whisper tuning:

| Variable | Default | Purpose |
| --- | --- | --- |
| `WHISPER_MODEL` | `small` | Model size (`tiny`, `base`, `small`, `medium`, …) |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8`, `float16`, etc. |

### 2. Python dependencies

Installed by `setup_transcription.py`:

```bash
pip install -r .agents/skills/sp-voicemail-triage/scripts/requirements.txt
```

First model download ~150MB for `small`. Cached under `~/.cache/huggingface/hub/`.

### 3. Audio decoding

**PyAV** (installed with `faster-whisper`) decodes `.wav` / `.mp3`. **ffmpeg** on
`PATH` also works but is optional when PyAV is present.

### 4. Freshdesk attachment access

- API key must read tickets **with conversations** (`?include=conversations`).
- Voicemail `.wav` / `.mp3` files may appear on the **ticket** or the **first
  email conversation** — the batch script checks both.
- **Email/ticket body is not used for transcription.**

### 5. Cursor Automation configuration

| Setting | Value |
| --- | --- |
| **Trigger** | Cron (e.g. weekdays every 15–30 min, or hourly) |
| **Tools** | Shell / repo access |
| **Repo** | This assistant repo on `main` |

The automation host needs **Python 3**, **faster-whisper**, and a **cached Whisper
model**. No OpenAI API key required.

### 6. Verify setup

```bash
python .agents/skills/sp-voicemail-triage/scripts/verify_transcription.py
python .agents/skills/sp-voicemail-triage/scripts/verify_transcription.py --load-model
```

## Recommended automation flow

```bash
# First run only (or after env rebuild):
python .agents/skills/sp-voicemail-triage/scripts/setup_transcription.py

# Every cron tick:
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

The fast wrapper runs a **preflight** verify automatically (skip with
`--skip-preflight`).

### Prompt template

```markdown
Run the SP voicemail fast batch for Freshdesk KSOnboarding.

1. Load `.agents/skills/sp-voicemail-triage-fast/SKILL.md`.
2. If first run on this host, execute setup_transcription.py once.
3. Execute:
   python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
4. Report JSON summary: processed, transcribed, transcription_failed,
   transcription_failed_ids, transcription_errors, foul_language_closed,
   routed, closed, failed.
5. Do not pass --no-transcribe. Do not invoke Gateway or Salesforce MCP.

If preflight or setup fails, report the error and stop.
If transcription_failed > 0, list ticket IDs and errors; tickets were left open.
```

## What the batch script does

1. Search open KSOnboarding tickets (paginated REST)
2. Filter subjects that **include** `New voicemail`
3. Load ticket + conversations; find **`.wav` or `.mp3`** attachment
4. Download and transcribe via **faster-whisper** (`vad_filter=False` for short VMs)
5. If transcript matches **foul-language** term list → internal note, **no forward**, resolve
6. On success (no foul language): classify, internal note, forward, resolve
7. On failure: skip ticket — no Freshdesk updates

## Flags

| Flag | Automation use |
| --- | --- |
| `--skip-vetting` | Injected by fast skill wrapper |
| `--skip-preflight` | Skip verify check (not recommended) |
| `--no-email` | Manual no-email runs only |
| `--no-transcribe` | **Never in automation** |
| `--dry-run` | Preview only; no writes |

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Preflight fails | Run `setup_transcription.py` |
| `no_audio_attachment` | WAV/MP3 on conversation thread — fixed by `include=conversations`; check ticket manually |
| `missing_attachment_url` | Freshdesk attachment metadata incomplete |
| Empty transcript | Silent/unintelligible audio — ticket skipped |
| Slow first run | Model download — normal |
| `transcription_failed` > 0 | See `transcription_errors` in batch JSON |
| `processed: 0` | No open voicemail tickets in queue |

## Full skill batch

```bash
python .agents/skills/sp-voicemail-triage/scripts/batch_process_freshdesk.py
```
