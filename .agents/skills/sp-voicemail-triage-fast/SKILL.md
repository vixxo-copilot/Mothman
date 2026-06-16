---
name: sp-voicemail-triage-fast
description: >-
  Fast SP voicemail triage for scheduled automation. Downloads WAV attachments,
  transcribes via OpenAI Whisper, classifies, posts Freshdesk internal notes,
  forwards to SPM/AP/COI/recruitment, and resolves KSOnboarding tickets — without
  Gateway, Salesforce, Siebel, or JDE vetting. Use for cron jobs, batch REST runs,
  or when speed matters more than company lookup. For full vetting use parent
  sp-voicemail-triage; for no email use sp-voicemail-triage-no-email.
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

| Variable | Required |
| --- | --- |
| `FRESHDESK_API_KEY` | Yes |
| `FRESHDESK_DOMAIN` | Optional (default `vixxo-helpdesk.freshdesk.com`) |
| `OPENAI_API_KEY` | **Yes — mandatory**; script exits if missing |

Load from repo `.env` or `~/.vixxo/freshdesk_token`.

**OpenAI:** key must reach the Whisper API; automation host needs egress to
`api.openai.com`. See
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

Each ticket includes a **`.wav`** attachment from the voicemail email.

## Pipeline

1. Search open KSOnboarding tickets (paginated REST)
2. Filter voicemail subjects
3. Download **`.wav`** attachment (required)
4. Transcribe with **OpenAI Whisper** (`whisper-1`) — **required**
5. **On transcription success only:** classify, internal note, forward, resolve
6. **On transcription failure:** skip ticket — no Freshdesk updates

Phase 2 runs automatically (except `--dry-run`).

## Skipped vs parent

See [reference/fast-mode.md](reference/fast-mode.md).

## Scheduled automation

[../sp-voicemail-triage/reference/automation-setup.md](../sp-voicemail-triage/reference/automation-setup.md)

Recommended automation prompt:

```markdown
Run SP voicemail fast batch:
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py

Report processed, transcribed, transcription_failed, routed, closed, failed from JSON summary.
Do not pass --no-transcribe. Do not invoke Gateway or Salesforce MCP — vetting is skipped by design.
Tickets with transcription_failed were left open unchanged.
```

## Sibling skills

| Skill | Use |
| --- | --- |
| `sp-voicemail-triage` | Full vetting + Outlook |
| `sp-voicemail-triage-no-email` | No forwards |
| `sp-voicemail-triage-webhook` | WAV webhook intake |
