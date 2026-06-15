# PolyAI API reference (Cursor)

Docs: https://docs.poly.ai/api-reference/introduction.md

## Families

| Family | Base URL | Use |
| --- | --- | --- |
| Conversations (v3) | `api.{region}-1.platform.polyai.app/v3/...` | Read transcripts |
| Agents | `api.{region}.poly.ai/v1/agents/...` | Build/deploy agents |

## Auth

```
x-api-key: YOUR_API_KEY
```

## Scripts in this skill

- `scripts/polyai_client.py` — health, list, get
- `scripts/audit_conversation.py` — redacted audit JSON
