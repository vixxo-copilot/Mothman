---
name: sp-voicemail-triage-fast
description: >-
  Fast SP voicemail triage for scheduled automation. Downloads audio attachments
  (.wav or .mp3), transcribes locally with faster-whisper, classifies, posts
  Freshdesk internal notes, forwards to SPM/AP/COI/recruitment, and resolves
  KSOnboarding tickets — without Gateway, Salesforce, Siebel, or JDE vetting.
  Use for cron jobs, batch REST runs, or when speed matters more than company
  lookup. For full vetting use parent sp-voicemail-triage; for no email use
  sp-voicemail-triage-no-email.
---

# SP Voicemail Triage — Fast

Automation-first variant of **`sp-voicemail-triage`**. Same Freshdesk intake,
**Whisper transcription**, classification, callback decision, internal note,
forward, and resolve — **no external system vetting**.

## When to use

- Scheduled Cursor Automation on the KSOnboarding voicemail queue
- "Run fast voicemail triage" / "automation voicemail batch"
- Batch processing when Gateway/Salesforce MCP latency is unacceptable

**Use parent `sp-voicemail-triage`** when Siebel/Gateway/JDE/Salesforce vetting
or Salesforce Lead notes are required.

**Use `sp-voicemail-triage-no-email`** when forwards must not send.

## Prerequisites

| Requirement | Details |
| --- | --- |
| `FRESHDESK_API_KEY` | Yes — `.env` or `~/.vixxo/freshdesk_token` |
| `FRESHDESK_DOMAIN` | Optional (default `vixxo-helpdesk.freshdesk.com`) |
| **faster-whisper** | `pip install -r ../sp-voicemail-triage/scripts/requirements.txt` |
| **ffmpeg** | On `PATH` |

Optional: `WHISPER_MODEL` (default `small`), `WHISPER_DEVICE` (`cpu`), `WHISPER_COMPUTE_TYPE` (`int8`).

Verify:

```bash
python .agents/skills/sp-voicemail-triage/scripts/setup_transcription.py
python .agents/skills/sp-voicemail-triage/scripts/verify_transcription.py
```

The fast batch wrapper runs preflight automatically. See
[../sp-voicemail-triage/reference/automation-setup.md](../sp-voicemail-triage/reference/automation-setup.md).

## Batch command (default path)

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

The wrapper injects **`--skip-vetting`**. Transcription is **always on** — do not
pass `--no-transcribe` in automation.

## Intake filter

Same as parent — subject must **include** `New voicemail`:

[../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md](../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md)

Each ticket includes an **audio attachment** (`.wav` or `.mp3`) from the voicemail
email. The email body is notification metadata only — **not a transcript**. Spoken
content must come from transcribing the attachment.

## Pipeline

1. Search open KSOnboarding tickets (paginated REST)
2. Filter voicemail subjects
3. Download **audio attachment** (`.wav` or `.mp3`, required)
4. Transcribe with **faster-whisper** (local) — **required**
5. If **no-forward** rule matches (foul language, &lt;10s, blank/1–2 words,
   **client/customer voicemail**) → note, no forward, resolve
6. If **client portal support** keywords match → note, forward to
   `Amy.Grantham@vixxo.com`, resolve
7. **Otherwise:** classify, internal note, forward, resolve
8. **On transcription failure:** skip ticket — no Freshdesk updates

Phase 2 runs automatically (except `--dry-run`).

## Skipped vs parent

See [reference/fast-mode.md](reference/fast-mode.md).

## Scheduled automation

[../sp-voicemail-triage/reference/automation-setup.md](../sp-voicemail-triage/reference/automation-setup.md)

Recommended automation prompt:

```markdown
Run SP voicemail fast batch:
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py

Report processed, transcribed, transcription_failed, client_review_closed,
client_portal_support_routed, routed, closed, failed from JSON summary.
Do not pass --no-transcribe. Do not invoke Gateway or Salesforce MCP — vetting is skipped by design.
Client/customer detection in fast mode uses caller-ID and transcript heuristics only (no phone lookup).
Tickets with transcription_failed were left open unchanged.
```

## Sibling skills

| Skill | Use |
| --- | --- |
| `sp-voicemail-triage` | Full vetting + Outlook |
| `sp-voicemail-triage-no-email` | No forwards |
| `sp-voicemail-triage-webhook` | WAV webhook intake |
