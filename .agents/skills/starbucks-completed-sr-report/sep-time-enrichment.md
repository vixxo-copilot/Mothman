# SEP time enrichment (VixxoLink `/times`)

Use **`vixxolink_get_service_request_time_events`** for each SR in the report set. This is the Service Execution time path (`GET /times?serviceRequestNumber={sr}`). Prefer it over `vixxolink_get_service_requests_activity_detail` (403 on Service Center tokens).

## Extract from time events

From `data.results[]`, take the **active** rows (`isActive: true`):

| Field | Source |
|---|---|
| **Time in** | Earliest `timestamp` where `type === "in"` |
| **Time out** | Latest `timestamp` where `type === "out"` |
| **Job complete** | `isJobComplete` on the latest time-event row (or any active row — they match when complete) |

If multiple `in` or `out` events exist, use earliest `in` and latest `out`.

Display timestamps in the SR's local offset when present; otherwise convert from UTC and note the timezone.

## SLA fields from search summary

Search with `summary: true` returns **`localCompletionSLA`** per row. Keep it from the search result — do not re-fetch for SLA deadline alone.

Optional response SLA (include when user asks or when completion SLA is inconclusive):

- **`responseExpiration`** from `vixxolink_get_service_request_details` vs time in
- Within response SLA when parsed time in instant ≤ parsed `responseExpiration` instant

## Within completion SLA

Parse **time out** and **`localCompletionSLA`** as timestamp instants before comparing them. Do not compare the raw strings because time out can be UTC (`Z`) while `localCompletionSLA` can carry a local offset.

| Condition | Label |
|---|---|
| Time out present and parsed time out instant ≤ parsed `localCompletionSLA` instant | **Yes** |
| Time out present and parsed time out instant > parsed `localCompletionSLA` instant | **No** |
| No time out, job complete false | **Unknown — no time out** |
| No time out, job complete true | **Unknown — job complete, no time out** |
| Missing localCompletionSLA | **Unknown — no SLA deadline** |

Do not infer SLA from created date alone.

## Batch guidance

- Call time events **after** the search merge and de-dupe.
- Parallelize in batches of ≤10 SRs when the set is large.
- If the report set exceeds **50 SRs**, show time/SLA columns in the executive summary only and cap per-region detail to the **20 most recent** SRs unless the user asks for full detail.

## Verified example (2026-06-09)

SR `1-6580605822`:

- Time in: `2026-06-07T15:33:23Z`
- Time out: `2026-06-07T17:06:57Z`
- Job complete: `true`
- localCompletionSLA: `2026-06-07T18:05:21-07:00` → **Within SLA: Yes**
