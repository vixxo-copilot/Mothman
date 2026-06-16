# Webhook Payload Contract

The webhook must deliver a **WAV** recording plus optional metadata. Two
encodings are supported.

## Option A — multipart/form-data (preferred)

```http
POST /{automation-webhook-path} HTTP/1.1
Content-Type: multipart/form-data; boundary=----boundary
Authorization: Bearer {token}

------boundary
Content-Disposition: form-data; name="voicemail"; filename="vm-20260616.wav"
Content-Type: audio/wav

{RIFF WAVE bytes}
------boundary
Content-Disposition: form-data; name="metadata"
Content-Type: application/json

{
  "correlation_id": "webhook-7f3a2b1c",
  "callback_number": "2288612196",
  "caller_name": "Dottie",
  "company_name": "Absolute Better Contracting",
  "freshdesk_ticket_id": 123456,
  "received_at": "2026-06-16T14:13:18Z",
  "duration_seconds": 23,
  "dry_run": false
}
------boundary--
```

| Part | Required | Notes |
| --- | --- | --- |
| `voicemail` | Yes | WAV file field |
| `metadata` | No | JSON string; fields below |

## Option B — application/json + base64

```json
{
  "correlation_id": "webhook-7f3a2b1c",
  "audio_base64": "{base64-encoded WAV}",
  "audio_content_type": "audio/wav",
  "audio_filename": "vm-20260616.wav",
  "callback_number": "2288612196",
  "caller_name": "Dottie",
  "company_name": "Absolute Better Contracting",
  "freshdesk_ticket_id": 123456,
  "received_at": "2026-06-16T14:13:18Z",
  "duration_seconds": 23,
  "dry_run": false,
  "combine_with_correlation_id": "webhook-prior-id"
}
```

## Field reference

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `correlation_id` | string | No | Unique idempotency key; generated if missing |
| `audio_base64` | string | Yes* | WAV bytes, base64 (*multipart uses file part instead) |
| `audio_content_type` | string | Yes* | Must be `audio/wav` or `audio/x-wav` |
| `audio_filename` | string | No | Original filename for audit |
| `callback_number` | string | No | E.164 or 10-digit US |
| `caller_name` | string | No | Spoken or CRM name |
| `company_name` | string | No | SP / company for vetting |
| `freshdesk_ticket_id` | integer | No | When voicemail originated from Freshdesk |
| `received_at` | string | No | ISO-8601 UTC |
| `duration_seconds` | number | No | Voicemail length |
| `dry_run` | boolean | No | Skip Phase 2 writes |
| `combine_with_correlation_id` | string | No | Force merge with prior webhook item |

## Validation rules

1. WAV must start with `RIFF` magic bytes after decode.
2. Reject empty audio, non-WAV content types, or payloads over **25 MB**.
3. `freshdesk_ticket_id` must be a positive integer when present.
4. Normalize `callback_number` to digits for combine keys.

## Example minimal JSON payload

```json
{
  "audio_base64": "UklGRi4AAABXQVZFZm10IBAAAAABAAEA…",
  "audio_content_type": "audio/wav",
  "callback_number": "2288612196"
}
```
