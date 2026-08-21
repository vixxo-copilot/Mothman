# SF Case Email Sync — Reference

## Salesforce objects

### Case fields used

| Field | Use |
| --- | --- |
| `Id` | File and EmailMessage parent |
| `CaseNumber` | Search key (with/without leading zeros) |
| `Subject`, `Description` | SR extraction, subject tokens, email regex |
| `ContactEmail`, `SuppliedEmail` | Contact search keys |
| `OwnerId` | `--owner-me` filter |
| `IsClosed` | Open-case filter |

### EmailMessage payload

| Field | Source |
| --- | --- |
| `ParentId` | Case Id |
| `Subject` | Graph `subject` |
| `FromName`, `FromAddress` | Graph `from` |
| `ToAddress` | Primary recipient or `;`-joined list |
| `CcAddress` | Joined CC list (omit if empty) |
| `TextBody`, `HtmlBody` | Graph body content |
| `Incoming` | `true` when sender ≠ operator mailbox |
| `Status` | `0` incoming, `3` sent |
| `MessageDate` | `receivedDateTime` or `sentDateTime` |
| `MessageIdentifier` | Graph `internetMessageId` |

### Files upload

Use `sf data create file --parent-id {CaseId} --title {title}`.

- `.eml` titles: **without** `.eml` extension (Salesforce adds file type)
- Dedupe checks title, title + `.eml`, and stem for attachments

## Microsoft Graph

### Auth

Uses cached token from `@softeria/ms-365-mcp-server` (same path as
`sp-voicemail-triage/scripts/outlook_graph_helper.mjs`).

Repair auth: `.cursor/bin/repair-vixxolink-oauth.cmd` is unrelated; for M365
use the ms365 MCP login flow documented in `.cursor/mcp.README.md`.

### Search

`scripts/outlook_mail.mjs search --query "1-6574285042"`

- Uses `$search` with `ConsistencyLevel: eventual`
- Do not combine `$search` and `$filter` on the same query
- Default top: 50 messages per search key

### MIME download

`GET /me/messages/{id}/$value` → raw `.eml` bytes

## SF flow errors

**Process:** Email Message: Inbound/Outbound Email Automation

**Symptoms:** HTTP 400 on `EmailMessage` POST; message like "Probably Limit
Exceeded or 0 recipients"

**Mitigation:**

1. Re-run with `--skip-email-message` (Files-only mode)
2. Simplify `ToAddress` to single primary recipient (script already prefers
   single-recipient format when only one `toRecipients` entry)
3. Content remains on Files tab via `.eml`

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SF_TARGET_ORG` | Default org alias (default `vixxo`) |
| `SF_CASE_SYNC_OWNER_EMAIL` | Override owner for `--owner-me` |
| `SF_CLI_PATH` | Custom sf CLI path |

## Output JSON schema

```json
{
  "mode": "dry-run",
  "cases_scanned": 1,
  "lookback_days": 30,
  "cases": [{
    "case_number": "6911",
    "search_keys": { "sr_numbers": ["1-6574285042"], "emails": [] },
    "matched_messages": [{ "confidence": "high", "reasons": ["sr:1-6574285042"] }],
    "manual_review": [],
    "sync_results": [{ "actions": ["would_upload_eml"], "errors": [] }]
  }],
  "summary": { "matched_messages": 10, "synced": 0, "errors": 0 }
}
```

## Account audit (Phase 1 — audit only)

Before email sync, confirm Cases link to the correct SP Account using
`sp-inbound-vetting` identity resolution (Gateway + Salesforce). **No writes**
in Phase 1.

```bash
python .agents/skills/sf-case-email-sync/scripts/audit_case_accounts.py \
  --owner-me --limit 25 --output .tmp/sf-account-audit.json
```

| `account_update` | Meaning |
| --- | --- |
| `recommended` | Placeholder/blank Case → resolved Known SP Account |
| `already_correct` | Case already linked to resolved Account |
| `review` | Known SP resolved but Case linked to different non-placeholder Account |
| `unresolved` | Could not resolve Account from Case evidence |
| `not_applicable` | Posture not Known SP |

Placeholder accounts replaced in Phase 2 (`--fix-accounts`, not yet implemented):

- Vixxo Corporation (`001TS00000CLPi9YAH`)
- Service Provider Support Shell Account (`001TS00000mWdvSYAS`)

Helper module: `scripts/account_audit.py` · rules: `sp-inbound-vetting/scripts/sf_case_account.py`

### Gateway connection (bearer wrapper — same as business-objects)

Gateway and VixxoLink MCPs use **bearer auth**, not localhost OAuth callbacks:

- `.cursor/bin/run-gateway-mcp.cmd` → `mcp-remote` + `Authorization: Bearer …`
- Token source: `mcp_env.resolve_vixxo_bearer_token()` reads, in order:
  1. `~/.vixxo/gateway_api_token`
  2. `~/.mcp-auth/mcp-remote-*/6486a042…_tokens.json`

Shell scripts (`mcp_http.py`, account audit) use the same bearer path.

**If Gateway fails:**

1. `python .cursor/bin/sync_gateway_token.py` (or place token in `~/.vixxo/gateway_api_token`)
2. `.cursor/bin/repair-gateway-oauth.cmd` (clears stale port 29069 listener only)
3. Restart **gateway** and **vixxolink** in Cursor Settings → MCP

## Morning brief integration (optional)

During `morning-brief`, run the compact dry-run scanner (never `--execute`
without explicit approval):

```bash
python .agents/skills/sf-case-email-sync/scripts/morning_case_mail_scan.py \
  --days 7 --limit 15 --output .tmp/sf-email-sync-morning.json
```

Output lands in the morning brief **SF case mail to sync** section. Summary
JSON: `.tmp/sf-email-sync-morning-summary.json`.

For the full plan JSON, use `sync_case_emails.py --owner-me` directly.
