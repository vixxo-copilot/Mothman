# SP Voicemail Triage (Fast)

Sibling of **`sp-voicemail-triage`** for **scheduled Cursor Automations** and agent
batch runs.

- **Local faster-whisper transcription** (`.wav` or `.mp3`; requires pip + ffmpeg)
- **Shell cron:** keyword routing only — no external vetting
- **QSIAP AP voicemails:** included by default via the `sp-inbound-vetting`
  QSIAP runner (`qsiap@vixxo.com`, subject `New voicemail`)
- **Agent runs:** **`sp-inbound-vetting`** via **Skills MCP** for lite Gateway/SF
  vetting and quicker reroute before Freshdesk writes
- **Freshdesk REST** for shell batch — agent tier also uses Freshdesk MCP for apply

```bash
# Shell / cron
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py

# KSOnboarding only
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --no-qsiap

# QSIAP only
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --qsiap-only

# Agent preview (then lite vet + apply)
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
```

See [SKILL.md](SKILL.md), [reference/fast-mode.md](reference/fast-mode.md), and
[reference/inbound-vetting-reroute.md](reference/inbound-vetting-reroute.md).
