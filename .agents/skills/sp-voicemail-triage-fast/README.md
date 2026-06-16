# SP Voicemail Triage (Fast)

Sibling of **`sp-voicemail-triage`** for **scheduled Cursor Automations** and other
hands-off batch runs.

- **WAV + Whisper transcription** (requires `OPENAI_API_KEY`)
- **No external vetting** (Gateway, Salesforce, Siebel, JDE)
- **Freshdesk REST only** — no Outlook MCP in the batch path

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

See [SKILL.md](SKILL.md) and [reference/fast-mode.md](reference/fast-mode.md).
