# mothman-daily-ops-report reference

## Day boundary

- **Timezone:** America/Chicago
- **Day label:** calendar date `YYYY-MM-DD`
- **Half-open window:** `[day 00:00, next day 00:00)` in Chicago, converted to UTC for Salesforce/Graph filters
- **DoD delta:** day *N* total − day *N−1* total (prior column in the 5-day window)
- **Rolling window:** last `N` calendar days ending today (default `N=5`)

## Operator

| Field | Value |
|-------|-------|
| Name | Crystal Gagner |
| Email | Crystal.Gagner@vixxo.com |
| SF org | `vixxo` (sf CLI default target) |

## Snapshot layout

```
.agents/skills/mothman-daily-ops-report/snapshots/YYYY-MM-DD/
  manifest.json
  salesforce.json
  outlook.json
  teams.json
```

### `salesforce.json`

```json
{
  "day": "2026-08-10",
  "captured_at": "2026-08-10T13:00:00-05:00",
  "source": "salesforce",
  "open": {
    "total": 42,
    "by_type": { "Service Provider Support": 20 },
    "by_status": { "Working": 12, "New": 8 },
    "point_in_time": true
  },
  "closed": {
    "total": 5,
    "by_type": { "Rate Negotiation": 2 }
  },
  "new": {
    "total": 3,
    "by_type": { "Coverage Change": 1 }
  }
}
```

`open` is live-fetched for **today**. For historical days (or when open is
missing), the runner backfills from Good Morning / Afternoon JSON under
`.tmp/mothman-good-morning/`, preferring afternoon then morning:

| Preference | Path |
|------------|------|
| 1 (preferred) | `data-afternoon-YYYY-MM-DD.json` |
| 2 | `data-YYYY-MM-DD.json` |

Uses `salesforce.cases` (fallback `metrics_snapshot.salesforce_cases`) plus
`case_types[]` for by-type / by-status. Open block may include
`"source": "good-afternoon" | "good-morning" | "live"`. If no GM/GA file
exists, HTML shows `—`.

### `outlook.json`

```json
{
  "day": "2026-08-10",
  "captured_at": "2026-08-10T13:00:00-05:00",
  "source": "outlook",
  "received": 28,
  "sent": 14,
  "unread": 6,
  "notes": ""
}
```

`unread` is point-in-time (today only when live). Historical unread may be
absent (`null`).

### `teams.json`

```json
{
  "day": "2026-08-10",
  "captured_at": "2026-08-10T13:00:00-05:00",
  "source": "teams",
  "messages_from_me": 12,
  "messages_from_others": 19,
  "replies_from_me": 7,
  "chats_active": 8,
  "internal_from_others": 15,
  "external_from_others": 4,
  "chats_sampled": 40,
  "notes": "Proxies from recent chats; not a full tenant export."
}
```

## Salesforce SOQL

Resolve owner once:

```sql
SELECT Id, Name, Email FROM User
WHERE Email = 'Crystal.Gagner@vixxo.com' AND IsActive = true
LIMIT 1
```

Open (today / point-in-time):

```sql
SELECT Id, CaseNumber, Status, RecordType.Name
FROM Case
WHERE OwnerId = '{UID}' AND IsClosed = false
```

Closed (day window, UTC bounds from Chicago day):

```sql
SELECT Id, CaseNumber, Status, RecordType.Name, ClosedDate
FROM Case
WHERE OwnerId = '{UID}' AND IsClosed = true
  AND ClosedDate >= {startUtc} AND ClosedDate < {endUtc}
```

New:

```sql
SELECT Id, CaseNumber, Status, RecordType.Name, CreatedDate
FROM Case
WHERE OwnerId = '{UID}'
  AND CreatedDate >= {startUtc} AND CreatedDate < {endUtc}
```

## Outlook (Graph)

Prefer folder-scoped filters (do not combine `$filter` with `$search`):

```
GET /me/mailFolders/inbox/messages?$filter=receivedDateTime ge {start} and receivedDateTime lt {end}&$select=id&$top=50
GET /me/mailFolders/sentitems/messages?$filter=sentDateTime ge {start} and sentDateTime lt {end}&$select=id&$top=50
GET /me/mailFolders/inbox/messages?$filter=isRead eq false&$count=true&$top=1
```

Runner paginates `@odata.nextLink` and counts ids. MCP fallback: `list-mail-messages`
with `$search="received:YYYY-MM-DD"` / `$search="sent:YYYY-MM-DD"` (KQL; wrap in
double quotes), then write `outlook.json`.

## Teams (Graph) — proxies

1. `GET /me` → `id` (Crystal’s Graph user id)
2. `GET /me/chats?$top=50&$expand=lastMessagePreview&$orderby=lastMessagePreview/createdDateTime desc`
3. For chats whose last activity falls in the 5-day window (or unknown), sample:
   `GET /me/chats/{id}/messages?$top=50`
4. Bucket messages by Chicago calendar day:
   - **from me:** `from.user.id == me`
   - **from others:** otherwise (skip system messages where possible)
   - **replies from me:** from me and `replyToId` set
   - **internal:** other sender email/domain ends with `@vixxo.com`
   - **external:** other sender with a non-vixxo domain (guests / outside)

**Limits:** Not a complete call log. Does not classify PSTN. Channel posts are
included only when they appear in Crystal’s chat list (usually 1:1 / group
chats). Treat Teams numbers as activity proxies.

MCP fallback: `list-chats` then `list-chat-messages` per active chat; write
`teams.json` per day.

## HTML output

Default: `.tmp/mothman-daily-ops/daily-ops-{as-of}.html`

Columns: each day in the window + a **Δ** column for DoD (today vs yesterday
highlighted in the meta line; every day column also shows Δ vs prior day in
stacked tables like SPM).

## Auth

| Source | Mechanism |
|--------|-----------|
| Salesforce | `sf org display --target-org vixxo` / `sf data query` |
| Graph | `MS_GRAPH_ACCESS_TOKEN` or `MS365_MCP_OAUTH_TOKEN` env / `.env`, else MCP |

## Out of scope

- Gong / Teams Phone call journals
- Freshdesk SPM group
- Sending or posting the report
- Scheduled automation
