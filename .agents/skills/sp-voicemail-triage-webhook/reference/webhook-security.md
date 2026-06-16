# Webhook Security

Validate every request **before** transcribing audio or calling MCP write APIs.

## Cursor Automation webhooks

After saving an automation with a `webhook` trigger, Cursor provides:

- A unique **webhook URL**
- **Authentication** configuration in the Automations editor (complete setup there
  before production traffic)

The agent run receives the authenticated payload. Treat unauthenticated test
posts as dry-run only.

## Shared secret (external POST)

When an external telephony or middleware system POSTs directly:

1. Require `Authorization: Bearer {SP_VOICEMAIL_WEBHOOK_TOKEN}` **or**
   header `X-Vixxo-Webhook-Secret: {same token}`.
2. Store the token in `.env` as `SP_VOICEMAIL_WEBHOOK_TOKEN` — never commit it.
3. Reject missing or mismatched tokens with HTTP **401** and no processing.

## Replay protection (recommended)

- Require `X-Webhook-Timestamp` within **5 minutes** of server time.
- Optionally require `X-Webhook-Signature: sha256={hmac}` over
  `{timestamp}.{raw_body}` using the same secret.

## Idempotency

- Honor `correlation_id` — if already processed with `status: routed`, return
  the stored JSON response without re-forwarding.

## Data handling

- Do not write WAV files to git-tracked paths; use temp storage only.
- Redact tokens and full phone numbers in automation logs shared outside
  {{employee_name}}'s workspace.
