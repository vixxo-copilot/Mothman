# `fetch_coi_attachments.py`

Downloads every attachment on a Freshdesk ticket (and on each conversation reply) so the `VIXXO-coi-review` skill can read the binary COI directly with the agent's `Read` tool. Stdlib only — no pip installs.

## When to use

Mode B of the `VIXXO-coi-review` skill, whenever a COI ticket has the certificate as a PDF/JPG/PNG attachment rather than pasted in the body. The Freshdesk MCP returns attachment **metadata** but not the binary; this script bridges that gap by hitting the Freshdesk REST API directly.

## Environment

The script reads two env vars. Both are already set in this workspace via `.cursor/mcp.json` (the same values the Freshdesk MCP uses):

| Variable | Example | Notes |
|---|---|---|
| `FRESHDESK_DOMAIN` | `vixxo-helpdesk.freshdesk.com` | No scheme, no path |
| `FRESHDESK_API_KEY` | `kbSY1...` | Freshdesk personal API key (Profile → API Key in the Freshdesk UI) |

If you're invoking the script outside Cursor (plain shell), `set` (PowerShell) or `export` (bash) those before running.

## Usage

```powershell
python .agents\skills\VIXXO-coi-review\scripts\fetch_coi_attachments.py --ticket-id 12345
```

Optional flags:

| Flag | Default | Effect |
|---|---|---|
| `--out-dir <path>` | `.tmp/coi-review/<ticket-id>/` | Where to save binaries + manifest |
| `--no-conversations` | off | Skip the conversation pull (faster, but misses attachments on replies — usually NOT what you want for COIs since SPs often re-attach in a follow-up message) |

## Output

A working directory containing:

```
.tmp/coi-review/12345/
├── manifest.json              # ticket metadata, requester, conversations summary, attachment index
├── ACORD_25_2026-04.pdf       # original filename, sanitized
├── coi_renewal_signed.pdf
└── …
```

The script's last stdout line is always:

```
MANIFEST: <absolute path to manifest.json>
```

Parse that line to find the manifest from automation.

### `manifest.json` shape

```json
{
  "fetched_at": "2026-05-01T22:14:08+00:00",
  "freshdesk_domain": "vixxo-helpdesk.freshdesk.com",
  "ticket": {
    "id": 12345,
    "subject": "COI submission - Acme Plumbing",
    "status": 2,
    "tags": ["coi", "risk-compliance-routed"],
    "url": "https://vixxo-helpdesk.freshdesk.com/a/tickets/12345",
    "description_text": "…first 8000 chars of the ticket body…",
    "to_emails": ["coi@vixxo.com"],
    "cc_emails": []
  },
  "requester": {
    "id": 9876,
    "name": "Jane Broker",
    "email": "jane@acme-insurance.com",
    "company_id": 555
  },
  "conversations": [
    {
      "id": 22222,
      "incoming": true,
      "private": false,
      "from_email": "jane@acme-insurance.com",
      "created_at": "…",
      "body_text_preview": "…first 4000 chars…"
    }
  ],
  "attachments": [
    {
      "id": 31111,
      "name": "ACORD_25_2026-04.pdf",
      "content_type": "application/pdf",
      "size": 184302,
      "source": "ticket",
      "saved_path": ".tmp/coi-review/12345/ACORD_25_2026-04.pdf",
      "saved_bytes": 184302,
      "error": null
    }
  ],
  "summary": { "attachments_total": 1, "attachments_saved": 1, "attachments_failed": 0 }
}
```

## How the agent uses the output

1. Run the script.
2. Read `manifest.json` to get the requester (for the public reply addressee), conversation thread, and list of attachment `saved_path`s.
3. For each PDF/image `saved_path`, call the agent's `Read` tool — PDFs auto-extract to text, images come through as visual content.
4. Run the standard COI review against `references/vixxo-requirements.md`.
5. Draft the three artifacts (internal note, public reply, ticket actions) and wait for operator approval.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ERROR: FRESHDESK_DOMAIN not set` | Env var missing in the shell where you ran the script | `set FRESHDESK_DOMAIN=vixxo-helpdesk.freshdesk.com` (PowerShell: `$env:FRESHDESK_DOMAIN="…"`) |
| `HTTP 401: Unauthorized` | Wrong / rotated API key | Pull the current key from `.cursor/mcp.json` or regenerate in your Freshdesk profile |
| `HTTP 403: Forbidden` | The agent associated with the API key lacks permission on this ticket's group | Use a key tied to an agent that's a member of the SPM group |
| `HTTP 404: Not Found` | Wrong ticket ID, or ticket was deleted/archived | Re-check the ticket number; the URL printed by the MCP is the source of truth |
| `download failed` on a specific attachment in the manifest | The Freshdesk presigned S3 URL expired (5-min default) before the script reached it | Re-run the script — each run gets fresh presigned URLs |
| Manifest has the PDF but `Read` returns no text | Image-only/scanned PDF (no embedded text layer) | Flag the ticket `coi-blocked` and request the SP resubmit a text-searchable PDF, OR run a local OCR pass and feed that text in manually |
| `SSL: CERTIFICATE_VERIFY_FAILED` on corporate VPN | Vixxo proxy intercepting TLS | Run from off-VPN, or have IT add the proxy CA to the system trust store |

## Security notes

- The script never prints or logs the API key.
- The presigned S3 URLs returned in `attachment_url` are time-limited (~5 min) and don't require auth themselves; they're safe to fetch with just `User-Agent`.
- `.tmp/coi-review/` is intentionally outside any tracked path — do not commit downloaded COIs. (`.tmp/` is in the workspace's gitignore convention.)
