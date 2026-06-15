# Export and analysis

Use the **local CSV** for bulk questions (hang-ups, providers, time-of-day).
Reserve the live API for fresh pulls and single-call transcript audit.

## 0. Multi-USP setup

Registry: `reference/projects.json` · Profile: [project-profile.md](project-profile.md)

```bash
python3 .agents/skills/polyai/scripts/polyai_client.py projects
python3 .agents/skills/polyai/scripts/polyai_client.py health-all
python3 .agents/skills/polyai/scripts/polyai_client.py parse-jupiter "https://jupiter.polyai.app/vixxo-us/…"
```

Add a new USP: edit `projects.json` or set `POLYAI_EXTRA_PROJECT_IDS` in `.env`.

## 1. Export (refresh data)

```bash
# Default project (POLYAI_PROJECT_ID)
python3 .agents/skills/polyai/scripts/export_conversations.py

# One project
python3 .agents/skills/polyai/scripts/export_conversations.py --project vixxo-inbound-usp

# Every enabled project in registry
python3 .agents/skills/polyai/scripts/export_conversations.py --all-projects
```

Output: `exports/polyai/{project_id}-conversations.csv`

- ~7k+ rows for `vixxo-outbound-usp`; takes ~2–3 minutes (API pagination).
- Retries on 429 / SSL blips automatically.
- Includes `project_id`, `account_id`, `to_number`, `hangup_category`, all `metric_*` fields.

Re-export when the user needs data newer than the file's last row.

## 2. Analyze (no API — fast)

```bash
# Funnel + categories (default outbound project CSV)
python3 .agents/skills/polyai/scripts/analyze_export.py summary

# Per project or merged exports
python3 .agents/skills/polyai/scripts/analyze_export.py summary --project vixxo-outbound-usp
python3 .agents/skills/polyai/scripts/analyze_export.py summary --all-projects

# Why calls disconnect
python3 .agents/skills/polyai/scripts/analyze_export.py hangups
python3 .agents/skills/polyai/scripts/analyze_export.py fixable-buckets

# Most recent outbound call(s)
python3 .agents/skills/polyai/scripts/analyze_export.py recent --limit 5

# Who hangs up most (by dial-to number)
python3 .agents/skills/polyai/scripts/analyze_export.py top-phones --metric hangups

# One provider / number — hours in a timezone
python3 .agents/skills/polyai/scripts/analyze_export.py phone +18004233872 --timezone America/Chicago
```

Custom CSV path: `--csv path/to/file.csv`  
Include inbound test calls: `--inbound`

## 3. User question → command

| User asks | Do this |
| --- | --- |
| Export all calls / make a CSV | `export_conversations.py` or `--all-projects` |
| New USP / Jupiter URL | `parse-jupiter` → add to `projects.json` → `health-all` |
| Why are calls disconnecting? | `analyze_export.py hangups` + `fixable-buckets` |
| Most recent call | `analyze_export.py recent` |
| Which provider hangs up most? | `analyze_export.py top-phones --metric hangups` |
| ICEE / Tech24 hang-up times | `analyze_export.py phone +1XXXXXXXXXX --timezone America/Chicago` |
| Single call quality / VALID_SR | `audit_conversation.py --conversation-id OUT-… --full-scan` |
| API health | `polyai_client.py health` or `health-all` |

## Known provider numbers (hints only)

| Phone | Likely SP |
| --- | --- |
| +18887744950 | Tech24 |
| +12033334112 | Liberty Auto & Electric |
| +18004233872 | The ICEE Company |
| +17082331472 | ABS & Taylor Enterprises |
| +18603493921 | L & I Refrigeration |

Confirm SP name via VixxoLink SR lookup when MCP is available.

## Hangup category glossary

| Category | Meaning |
| --- | --- |
| Success - ETA posted | `UPDATE_ETA_SUCCESSFUL` |
| Out of scope SR | `OUT_OF_SCOPE_SR` |
| ETA started, not posted | ETA flow began; no write |
| Hung up early - intro only | Human, ≤45s, no ETA flow |
| API_OK but no ETA posted | Backend ping OK; no ETA (incl. many VM) |
| IVR timeout | `IVR_DURATION_EXCEEDED` |
| Unreachable (SIP 480) | Could not connect |

## Fixable buckets (leadership framing)

1. **Intro ≤30–45s** — script / ASR / silence (`fixable-buckets`)
2. **ETA confirmed, not posted** — integration (`UPDATE_ETA_DETAILS_CONFIRMED` without `UPDATE_ETA_SUCCESSFUL`)
3. **Voicemail ~27%** — expected; track VM → redial → ETA posted funnel
