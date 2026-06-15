# VixxoLink voice tool pack

Default posture: **read-only on live voice**. Writes require explicit approval.

## P0 — enable for service-center SR lookup

### `vixxolink_resolve_service_request`

Recommended call shape (matches QA calibration bundle):

```json
{
  "service_request_number": "<sr>",
  "include": ["notes", "time_events"]
}
```

Voice script pattern: caller provides SR number → agent reads status, assigned
SP, ETA, last note summary. Do not read full note history aloud unless asked.

### `vixxolink_search_service_requests`

Use when caller has store number / site id but not SR number. Keep result set
small (top 3 open SRs) before speaking.

## P1 — enable when site context is needed

- `vixxolink_find_site` — site address, contacts
- `vixxolink_get_customer` — confirm customer code
- `vixxolink_get_service_request_details` — lighter than resolve if bundle is
  too heavy for timeout budget

## P2 — write (sandbox only until approved)

- `vixxolink_post_service_request_note` — log call summary on SR. Template:
  "PolyAI voice — caller [intent]. Outcome: [resolution]. Ref: [call id]."

## Block on voice (keep toggled off)

- `vixxolink_patch_service_request`
- `vixxolink_update_service_request_sp_and_eta`
- `vixxolink_release_service_request`
- `vixxolink_set_sp_service_request_decision`
- Any quote/invoice create or update tools

## Gateway (separate MCP server)

Only enable if the voice flow explicitly handles invoice status questions:

- `gateway_*` invoice lookup tools — confirm with AP/ops before enabling on
  live voice (PII and payment data risk).

## Timeout guidance

| Tool | Suggested PolyAI timeout |
| --- | --- |
| `resolve_service_request` | 15–20s |
| `search_service_requests` | 10–15s |
| `find_site` | 10s |

If timeouts persist, drop `attachments` from include arrays and avoid Gateway
on the critical path.
