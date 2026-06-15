# Vixxo PolyAI project profile

Parsed from Jupiter production voice conversations URL (non-secret).

| Field | Value |
| --- | --- |
| UI | `https://jupiter.polyai.app` |
| Account ID | `vixxo-us` |
| Project ID | `vixxo-outbound-usp` |
| Channel | Voice |
| Environment | Live (`client_env=eq:Live`, `view=production`) |
| API region | `us` |

## `.env` values (Direction B)

```bash
POLYAI_REGION=us
POLYAI_ACCOUNT_ID=vixxo-us
POLYAI_PROJECT_ID=vixxo-outbound-usp
POLYAI_API_KEY=<provision from PolyAI — Conversations v3>
```

## Conversations API base

```
https://api.us-1.platform.polyai.app/v3/vixxo-us/vixxo-outbound-usp/conversations
```

## Script smoke test

```bash
python3 .agents/skills/polyai/scripts/polyai_client.py health
python3 .agents/skills/polyai/scripts/polyai_client.py list --limit 5
```

## Notes

- Project name `vixxo-outbound-usp` suggests **outbound voice** (USP likely =
  outbound service-provider calling). Tool pack may differ from inbound
  service-center SR lookup — confirm flows in Agent Studio before enabling
  write tools.
- Jupiter UI host differs from legacy `studio.us.poly.ai` URLs; API path
  segments still use `vixxo-us` / `vixxo-outbound-usp`.
