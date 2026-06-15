---
name: polyai
description: >-
  Standalone PolyAI operations skill. Export outbound conversations to CSV,
  analyze hang-ups and provider patterns, audit single calls, verify API health,
  and parse Jupiter/Studio config. Use for PolyAI, Jupiter, Agent Studio, voice
  agent, outbound USP, conversation audit, hang-ups, disconnect reasons,
  VALID_SR, API_OK, or ETA post failures. For VixxoLink MCP Studio wiring use
  polyai-vixxo-bridge.
---

# PolyAI

Standalone skill for PolyAI Agent Studio and the Conversations API.

## Pick a mode (30 seconds)

```
User needs bulk data / hang-ups / providers / CSV?
  → Export (once) then Analyze on local CSV

User needs one call transcript + integration signals?
  → Audit

User needs fresh JSON from API / health check?
  → API

User pastes Jupiter URL?
  → Config
```

**Default for outbound quality work:** export if CSV is missing or stale, then
`analyze_export.py`. Do not paginate 7k+ API pages in chat when the CSV exists.

## Prerequisites

`.env` at repo root:

```bash
POLYAI_API_KEY=
POLYAI_REGION=us
POLYAI_ACCOUNT_ID=vixxo-us
POLYAI_PROJECT_ID=vixxo-outbound-usp
# Optional: extra USP project IDs (comma-separated; merged into reference/projects.json)
# POLYAI_EXTRA_PROJECT_IDS=vixxo-inbound-usp
```

```bash
python3 -m pip install --user certifi   # if SSL fails on macOS
```

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/polyai_projects.py` | Multi-USP registry loader |
| `scripts/polyai_fetch.py` | Shared API pagination + retry |
| `scripts/export_conversations.py` | Full project → CSV |
| `scripts/analyze_export.py` | Hang-ups, funnel, phone/time stats on CSV |
| `scripts/audit_conversation.py` | Single-call redacted audit |
| `scripts/polyai_client.py` | Health, list, get, projects, parse-jupiter |

```bash
# List USP projects + health
python3 .agents/skills/polyai/scripts/polyai_client.py projects
python3 .agents/skills/polyai/scripts/polyai_client.py health-all

# Health (default or --project)
python3 .agents/skills/polyai/scripts/polyai_client.py health
python3 .agents/skills/polyai/scripts/polyai_client.py health --project vixxo-inbound-usp

# Export (~2–3 min for outbound; use --project / --all-projects)
python3 .agents/skills/polyai/scripts/export_conversations.py
python3 .agents/skills/polyai/scripts/export_conversations.py --all-projects

# Analyze export (fast — preferred for bulk questions)
python3 .agents/skills/polyai/scripts/analyze_export.py summary
python3 .agents/skills/polyai/scripts/analyze_export.py summary --all-projects
python3 .agents/skills/polyai/scripts/analyze_export.py fixable-buckets
python3 .agents/skills/polyai/scripts/analyze_export.py top-phones --metric hangups
python3 .agents/skills/polyai/scripts/analyze_export.py phone +18004233872 --timezone America/Chicago
python3 .agents/skills/polyai/scripts/analyze_export.py recent

# Single-call audit
python3 .agents/skills/polyai/scripts/audit_conversation.py --pick-best
python3 .agents/skills/polyai/scripts/audit_conversation.py --conversation-id OUT-xxxxxxxx --full-scan

# Jupiter URL → project IDs
python3 .agents/skills/polyai/scripts/polyai_client.py parse-jupiter "https://jupiter.polyai.app/vixxo-us/…"
```

CSV path: `exports/polyai/{project_id}-conversations.csv`  
Registry: `reference/projects.json`

## Mode — Export

1. Run `export_conversations.py`.
2. Report `row_count`, date range, and CSV path.
3. Re-run only when user needs newer data than the file's last `started_at`.

See [reference/export-and-analysis.md](reference/export-and-analysis.md).

## Mode — Analyze

Use **after** export exists. Commands:

| Command | Use when |
| --- | --- |
| `summary` | Funnel, category breakdown |
| `hangups` | Why calls disconnect |
| `fixable-buckets` | Intro / integration / voicemail buckets |
| `recent` | Latest call(s) |
| `top-phones --metric hangups` | Which dial-to numbers hang up most |
| `phone +1… --timezone America/Chicago` | Time-of-day for one SP line |

Optional: cross-check `extracted_sr_number` via VixxoLink when MCP is up.

## Mode — Audit

1. `audit_conversation.py` with `--pick-best` or `--conversation-id`.
2. Read `integration_signals`: `VALID_SR`, `API_OK`, `UPDATE_ETA_*`.
3. Report using [reference/conversation-audit.md](reference/conversation-audit.md).

Note: v3 per-ID **get** often 404 — audit scans the list API with `--limit`.

## Mode — API

1. `polyai_client.py health` then `list --limit N` for raw JSON.
2. Redact PII unless user requests a compliance export.

## Mode — Config

Jupiter URL: `https://jupiter.polyai.app/{account_id}/{project_id}/…`  
Use `polyai_client.py parse-jupiter` then add the project to
`reference/projects.json`. See [reference/project-profile.md](reference/project-profile.md).

## Guardrails

- API keys are secrets — never commit.
- Do not send outbound messages from audit findings without user approval.
- Default to redacted agent-script excerpts; `to_number` is business dispatch data.

## Reference

| File | Purpose |
| --- | --- |
| [reference/export-and-analysis.md](reference/export-and-analysis.md) | Export + analyze workflows |
| [reference/conversation-audit.md](reference/conversation-audit.md) | Single-call report template |
| [reference/vixxo-metrics.md](reference/vixxo-metrics.md) | Metric glossary |
| [reference/project-profile.md](reference/project-profile.md) | Multi-USP project IDs |
| [reference/projects.json](reference/projects.json) | Enabled project registry |
| [reference/api.md](reference/api.md) | API auth and URLs |
| [reference/studio-mcp.md](reference/studio-mcp.md) | Studio MCP wiring |

## Related skills

- `polyai-vixxo-bridge` — VixxoLink MCP in Studio
- `polyai-conversation-audit` — alias → this skill

## Test phrases

- "Export all PolyAI outbound calls to CSV"
- "Why are outbound calls hanging up?" → export + `fixable-buckets`
- "Which provider hangs up on us most?" → `top-phones --metric hangups`
- "ICEE hang-up times in CST" → `phone +18004233872 --timezone America/Chicago`
- "Audit the best recent outbound conversation"
