---
name: starbucks-completed-sr-report
description: >-
  Builds a regional report of completed Starbucks Service Requests from
  VixxoLink MCP across all Starbucks customer records (811, 811C, 811F,
  811F-C). Enriches each SR with time in, time out, job complete, and
  within-SLA via VixxoLink SEP time events. Groups by B&G Tech region with
  executive and per-region tables. Use when the user asks for a Starbucks
  completed SR report, completed Starbucks work by region, Starbucks SLA
  compliance, time in/time out on completed Starbucks SRs, or a VixxoLink
  Starbucks completion rollup.
---

# Starbucks Completed SR Report

Read-only regional report of **completed Starbucks SRs** via **VixxoLink MCP**,
with **SEP time enrichment** on every SR.

## Team quick start

**Requires:** VixxoLink MCP authenticated in this workspace.

**Run it:**

```
Run starbucks-completed-sr-report for the last 7 days.
Include time in, time out, job complete, and within SLA. Group by region.
```

Default window is **7 days** if not specified. Override with "last 24 hours",
"since Monday", or a date range.

## When to use

- "Run starbucks-completed-sr-report"
- "Starbucks completed SR report"
- "Completed Starbucks SRs by region"
- "Starbucks SRs with time in, time out, and SLA status"
- "Which Starbucks SRs missed SLA?"
- "Roll up finished Starbucks work across all regions"

## Dependencies

- **VixxoLink MCP** — `vixxolink_search_service_requests` (primary)
- **SEP time path** — `vixxolink_get_service_request_time_events` for **time in**, **time out**, and **job complete** on every SR in the report (see [sep-time-enrichment.md](sep-time-enrichment.md))
- **Conditional:** `vixxolink_get_service_request_details` for duplicate sub-status resolution and `responseExpiration` when response SLA is requested

## Starbucks customer scope

Pull **all four** Starbucks customer numbers unless the user narrows scope:

| Customer # | Name |
|---|---|
| `811` | Starbucks Corporation (US) |
| `811C` | Starbucks Corporation (Canada) |
| `811F` | Starbucks Licensed/Franchise Record |
| `811F-C` | CAD - Starbucks Licensed/Franchise Record |

## What counts as "completed"

Default completed sub-statuses (Vixxo ops–aligned):

| Sub-status | Include |
|---|---|
| `AR Successful` | yes — financial close complete |
| `Customer Run - Completed` | yes — customer-run work finished |
| `Invoice Review` | yes — work done, invoice in AP review |
| `Cancelled` | **no** |
| `RejectedDoNotProcess` / other cancel variants | **no** |

Run **one search per customer number × completed sub-status** (four customers × three sub-statuses = up to 12 searches). Do not rely on `isJobComplete` alone — it returns in-flight SRs.

## Region assignment

Read [regions.md](regions.md) before grouping. Resolution order:

1. Parse `serviceProvider.name` for `B&G Tech <n> - <Region>` → use `<Region>`
2. Else bucket as **`Other SP`** (third-party / non-B&G providers)
3. For Canada (`811C`, `811F-C`), keep province in detail columns; region label still follows rule 1 when present

Report **every region bucket found** — do not drop empty regions the user named, but do not invent regions with zero SRs unless the user asked for a fixed region list.

## Workflow

```
Task progress:
- [ ] 1. Resolve date window and customer scope
- [ ] 2. Pull completed SR summary rows from VixxoLink
- [ ] 3. Client-side date filter + de-duplicate by SR number
- [ ] 4. Enrich each SR via SEP time events (time in, time out, job complete, within SLA)
- [ ] 5. Assign region and build report
```

### Step 1 — Scope

| Input | Default |
|---|---|
| Date window | **Last 7 days** on `localCreatedDate` |
| Timezone for display | User local if known; else note source offsets |
| Page size | `50` |

If the user gives no window, use 7 days and state it in the report header.

### Step 2 — Pull from VixxoLink

For each `(customerNumber, subStatus)` pair in scope:

```json
{
  "customerNumber": "811",
  "subStatus": "AR Successful",
  "summary": true,
  "pageSize": 50,
  "pageNumber": 1
}
```

**API rules (verified):**

- Use `summary: true` for the standard summary field set.
- Do **not** pass `sortDirection: "desc"` or `"Descending"` — HTTP 400.
- Do **not** filter by `tierName` — upstream 500.
- Server-side date filters (`createdDateFrom`, etc.) do not narrow results — filter client-side.

**Pagination:** Continue until an empty page or **20 pages per search** (1,000 rows); note truncation if hit. Do not stop early from page dates alone — ordering is not guaranteed for the client-side `localCreatedDate` filter.

Tag each returned row with a monotonic fetch sequence before merging so duplicate SRs can keep the latest observed snapshot.

### Step 3 — De-duplicate and filter

1. Merge all search results.
2. Group duplicate SR `number` values, keeping the row with the highest fetch sequence (same SR can appear if status moved during window).
3. If duplicate rows disagree on `subStatus`, call `vixxolink_get_service_request_details` for that SR; use the current detail value when present, otherwise set `subStatus` to `Unknown — duplicate status unresolved` and note it.
4. Keep rows where `localCreatedDate` falls in `[windowStart, windowEnd]`.
5. Drop any row whose resolved `subStatus` is excluded (e.g. `Cancelled`).

### Step 4 — SEP time enrichment

For **each** SR in the filtered set, call `vixxolink_get_service_request_time_events` with `service_request_number`.

Read [sep-time-enrichment.md](sep-time-enrichment.md) for extraction and SLA rules. Attach to each SR row:

| Enriched field | Source |
|---|---|
| Time in | earliest active `type: "in"` timestamp |
| Time out | latest active `type: "out"` timestamp |
| Job complete | `isJobComplete` from time events |
| Completion SLA deadline | `localCompletionSLA` from search summary |
| Within SLA | parsed time out instant ≤ parsed `localCompletionSLA` instant (see reference for edge cases) |

### Priority bands

For executive summary counts, normalize each SR's `priority` by trimming and uppercasing:

- **P1/P1.x** — values whose first token is `P1` or a `P1.` decimal band (`P1`, `P1.1`, `P1 - Emergency`).
- **P2** — values whose first token is `P2` (`P2`, `P2 - Urgent`).
- **P3+ / other** — all remaining values, including `P3`, `P4`, `Planned/PM`, blank, or unknown priority.

### Step 5 — Report output

Use this structure:

```markdown
# Starbucks Completed SR Report

**Window:** <start> → <end> (filtered on SR created date)
**Customers:** 811, 811C, 811F, 811F-C (or subset)
**Completed sub-statuses:** AR Successful, Customer Run - Completed, Invoice Review
**Total SRs:** <n>

## Executive summary

| Region | SR count | Within SLA | Outside SLA | Unknown SLA | P1/P1.x | P2 | P3+ / other |
|---|---:|---:|---:|---:|---:|---:|---:|

## Regional detail

### <Region name> (<count> SRs)

| SR # | Created | Time in | Time out | Job complete | Within SLA | Completion SLA | Customer | Site | ST/Prov | Priority | Sub-status | Short description | Service provider |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

(repeat for each region, sorted by SR count descending)

## Notes

- <truncation, date-filter caveat, or scope adjustments>
```

**Sorting:**

- Executive summary: region count descending
- Detail tables: `localCreatedDate` descending within each region

If zero SRs overall, say so and restate window + filters.

## Guardrails

- Read-only — no SR writes.
- Do not dump raw MCP JSON.
- Label when the window uses **created date** because summary rows lack a completion timestamp.
- Gateway is fallback only if VixxoLink is unavailable.

## Verified payload shapes

| Tool | Payload | Verified |
|---|---|---|
| `vixxolink_search_service_requests` | `{"customerNumber":"811","subStatus":"AR Successful","summary":true,"pageSize":50,"pageNumber":1}` | 2026-06-08 |
| `vixxolink_list_customers` | `{}` — resolves Starbucks numbers `811`, `811C`, `811F`, `811F-C` | 2026-06-08 |
| `vixxolink_get_service_request_time_events` | `{"service_request_number": "1-6580605822"}` | 2026-06-09 |
