# PolyAI API — Cursor (Mode B)

Docs index: https://docs.poly.ai/llms.txt

## API families

| Family | Purpose | Base URL |
| --- | --- | --- |
| **Conversations** (read) | Transcripts, metrics, tool events | `https://api.{region}-1.platform.polyai.app/v3/...` |
| **Agents** (write) | Build, deploy, configure agents | `https://api.{region}.poly.ai/v1/agents/...` |
| **Chat** (runtime) | Webchat / SMS test | platform host |

Regions: `us`, `uk`, `euw` (platform uses `us-1`, `uk-1`, `euw-1`).

## Identifiers

From Studio URL:

```
https://studio.{region}.poly.ai/{account_id}/{project_id}/...
```

Both slug and `ACCOUNT-xxx` / `PROJECT-xxx` forms work in API paths.

## Auth

Header on every request:

```
x-api-key: YOUR_API_KEY
```

- Conversations v3 keys are provisioned by PolyAI (project-scoped).
- Agents API may use a separate workspace-scoped key.

Store in `.env` — never commit.

## Conversations v3 endpoints (this skill)

List:

```
GET https://api.{region}-1.platform.polyai.app/v3/{account_id}/{project_id}/conversations
```

Get one:

```
GET https://api.{region}-1.platform.polyai.app/v3/{account_id}/{project_id}/conversations/{conversation_id}
```

Use `scripts/polyai_client.py` rather than hand-rolling curl in chat.

## Agents API

Use only when the user asks to script agent configuration or deployment:

```
https://api.{region}.poly.ai/v1/agents/...
```

Requires `POLYAI_AGENTS_API_KEY` if different from the Conversations key.

## PII

Conversation payloads may include caller phone numbers and names. Summarize in
chat; full export only when the user requests compliance or QA review.
