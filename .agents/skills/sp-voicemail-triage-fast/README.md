# SP Voicemail Triage (Fast)

Sibling of **`sp-voicemail-triage`** for **scheduled Cursor Automations** and agent
batch runs.

- **Local faster-whisper transcription** (`.wav` or `.mp3`; requires pip + ffmpeg)
- **Shell cron:** keyword routing only — no external vetting
- **Agent runs:** **`sp-inbound-vetting`** via **Skills MCP** for lite Gateway/SF
  vetting and quicker reroute before Freshdesk writes
- **Freshdesk REST** for shell batch — agent tier also uses Freshdesk MCP for apply

```bash
# Shell / cron
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py

# Agent preview (then lite vet + apply)
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
```

See [SKILL.md](SKILL.md), [reference/fast-mode.md](reference/fast-mode.md), and
[reference/inbound-vetting-reroute.md](reference/inbound-vetting-reroute.md).
