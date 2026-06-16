# Fast mode — skipped steps

`sp-voicemail-triage-fast` runs the parent batch pipeline with **`--skip-vetting`**.

## Skipped (for speed)

| Step | Parent skill | Fast skill |
| --- | --- | --- |
| Siebel / Gateway SP lookup | MCP | **Skipped** |
| Gateway / VixxoLink customer lookup | MCP | **Skipped** |
| JDE vendor lookup | MCP | **Skipped** |
| Salesforce Lead / Account lookup | MCP | **Skipped** |
| Salesforce Lead note (onboarding branch) | MCP write | **Skipped** |
| Outlook inbox scan (batch REST path) | M365 MCP | **Skipped** (Freshdesk REST only) |

Internal notes record **vetting skipped** and **entity posture: Unknown**.

## Still performed

- Freshdesk KSOnboarding search + voicemail subject filter
- WAV download + **OpenAI Whisper** transcription (`OPENAI_API_KEY`)
- Keyword classification + callback decision
- Freshdesk private internal note
- Email forward to SPM / AP / COI / recruitment (unless `--no-email`)
- Resolve ticket (`status: 5`, `cf_sp: Unknown`)

## When to use parent instead

- Single-item triage with full company vetting table
- Onboarding branch where Salesforce Lead note is required
- Outlook inbox voicemails (M365 MCP)
- SR branch needing Gateway PM/support email resolution

## Batch command

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

Optional flags (passed through to parent script):

| Flag | Effect |
| --- | --- |
| `--dry-run` | Triage only; no writes |
| `--no-email` | Same as `sp-voicemail-triage-no-email` |
| `--no-transcribe` | Metadata-only fallback (not recommended) |

Scheduled automation setup: [../../sp-voicemail-triage/reference/automation-setup.md](../../sp-voicemail-triage/reference/automation-setup.md)
