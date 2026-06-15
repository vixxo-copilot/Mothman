# Vixxo PolyAI projects

Account: `vixxo-us` · Region: `us` · UI: `https://jupiter.polyai.app`

Project registry: [projects.json](projects.json) (source of truth for multi-USP tooling).

## Registered projects

| Project ID | Channel | Status | Notes |
| --- | --- | --- | --- |
| `vixxo-outbound-usp` | Outbound | Live | ETA / arrival follow-up (`outbound-live`) |
| `vixxo-inbound-usp` | Inbound | New | Provider inbound USP — add variants when live |
| `vixxo-usp` | Inbound | Legacy | Pre-split inbound; disabled in registry |

## `.env`

```bash
POLYAI_REGION=us
POLYAI_ACCOUNT_ID=vixxo-us
POLYAI_PROJECT_ID=vixxo-outbound-usp   # default when --project omitted
POLYAI_API_KEY=<Conversations v3 key from PolyAI>

# Optional: comma-separated extra project IDs (merged into registry)
# POLYAI_EXTRA_PROJECT_IDS=vixxo-inbound-usp
```

## Jupiter URL → project ID

```
https://jupiter.polyai.app/{account_id}/{project_id}/conversations/voice?...
```

```bash
python3 .agents/skills/polyai/scripts/polyai_client.py parse-jupiter \
  "https://jupiter.polyai.app/vixxo-us/vixxo-inbound-usp/..."
```

Then add the project to `reference/projects.json` (or set `POLYAI_EXTRA_PROJECT_IDS`).

## API base pattern

```
https://api.us-1.platform.polyai.app/v3/{account_id}/{project_id}/conversations
```

## Multi-project commands

```bash
# List registry
python3 .agents/skills/polyai/scripts/polyai_client.py projects

# Health check all enabled projects
python3 .agents/skills/polyai/scripts/polyai_client.py health-all

# Export one or all projects
python3 .agents/skills/polyai/scripts/export_conversations.py --project vixxo-inbound-usp
python3 .agents/skills/polyai/scripts/export_conversations.py --all-projects

# Analyze per project or merged
python3 .agents/skills/polyai/scripts/analyze_export.py summary --project vixxo-outbound-usp
python3 .agents/skills/polyai/scripts/analyze_export.py summary --all-projects
```

CSV output: `exports/polyai/{project_id}-conversations.csv`
