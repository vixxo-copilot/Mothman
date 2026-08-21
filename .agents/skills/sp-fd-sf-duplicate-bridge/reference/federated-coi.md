# Federated Insurance COI — Vetting, Dedupe, and Routing

Use this reference when **Federated Insurance** COI notifications arrive at
`COI@vixxo.com` (Freshdesk) and/or Salesforce Email-to-Case. The goal is to
**prevent duplicate ticket creation** and **route updates to the current open
Case/ticket** for the same Federated request.

Sibling: `vixxo-coi-review` handles field compliance after pairing.

## Subject line anatomy

Federated cert subjects follow a stable pattern (prefixes like `Fwd:` / `FW:` and
suffixes like `- Federated Insurance Auto Reply: …` are noise — strip before
parsing):

```text
Certificate Of Insurance - {Provider Name} {policy-id} Req {req_id}~{timestamp}~{suffix}
```

| Token | Example | Role |
| --- | --- | --- |
| **Provider name** | `Angeles Plumbing, LLC` | SP identity; appears in Account when matched |
| **Policy id** | `450-802-4` | Federated policy / cert bundle id (three-part numeric) |
| **Req id** | `17` | Federated request number — **primary dedupe key** |
| **Timestamp** | `2026-02-02 11:39:27.0` | Stable per request; confirms same Req id |
| **Suffix** | `00002` | Federated internal suffix |

**Regex (case-insensitive):**

```text
Certificate\s+Of\s+Insurance\s*-\s*(.+?)\s+(\d+-\d+-\d+)\s+Req\s+(\d+)~([^~]+)~(\d+)
```

### What is *not* a duplicate

| Situation | Example | Action |
| --- | --- | --- |
| Same SP, **different Req id** | Angeles Plumbing Req **17** vs Req **23** | Separate work items — do not merge |
| Same Req id, **different policy id** | Unlikely from Federated; treat as collision | Operator review |
| Auto-reply only | `… Auto Reply: Your request has been received` | Append to open Case for that Req id |
| Actual cert PDF | Subject without Auto Reply suffix | Same Req id → same thread |

### What *is* a duplicate (same thread)

| Situation | Example |
| --- | --- |
| Forward wrapper | `Fwd: FW: Certificate Of Insurance - … Req 17~…` |
| Auto-reply on same request | Same Req 17 + same timestamp as an existing ticket |
| Dual-intake FD + SF | Same `{policy-id} Req {req_id}` in FD and SF within minutes |
| Re-forward from internal mailbox | `Donotreply` / `Fedcerts-donotreply` resend of same subject |

## Match keys (priority order)

Use these before creating a new SF Case or FD ticket:

| Priority | Key | Pair / route? |
| --- | --- | --- |
| 1 | **`Freshdesk #{id}` in SF Description** | Yes — existing bridge |
| 2 | **`{policy-id} Req {req_id}`** in Subject | **Yes — same Federated request** |
| 3 | Provider name + policy id (no Req id parseable) | Likely same SP; operator confirm |
| 4 | Shared `fedcerts-donotreply@fedins.com` only | **No** — contact collision |

Composite dedupe key: `(policy_id, req_id)` e.g. `("450-802-4", "17")`.

Provider-name-only matching is **insufficient** for Federated batch senders — always
parse Req id when present.

## Vetting workflow — incoming notification

### 1. Parse the subject

Strip `Re:` / `Fw:` / `Fwd:` prefixes and `- Federated Insurance Auto Reply: …`
suffix. Extract `provider`, `policy_id`, `req_id`, `timestamp`.

If parsing fails (non-standard subject), fall back to provider-name SOQL + operator
review.

### 2. Search for existing open SF Case

```sql
SELECT Id, CaseNumber, Subject, Status, Account.Name, CreatedDate
FROM Case
WHERE Subject LIKE '%{policy_id} Req {req_id}~%'
   OR Subject LIKE '%{policy_id} Req {req_id} %'
ORDER BY CreatedDate DESC
LIMIT 10
```

Prefer Cases in **New**, **Working**, or **Open** status. If multiple matches,
pick the **oldest open** Case for that `(policy_id, req_id)`.

**Do not create a new SF Case** when an open Case exists for the same Req id.

### 3. Search Freshdesk (same Req id)

Freshdesk MCP `search_tickets` or REST search:

```text
"{policy_id} Req {req_id}"
```

Or tag + client-side filter on COI queue tickets.

If an open FD ticket exists (`Waiting on Third Party`, `Open`, etc.), **add a
note / conversation** rather than opening a parallel ticket.

### 4. Route the update

| Target | Action |
| --- | --- |
| **Open SF Case** | Add EmailMessage / attach cert; optional FD→SF attachment sync |
| **Closed SF Case, new cert on same Req** | Operator: reopen Case or link to successor Req |
| **Open FD only** | Bridge attachments to SF when SF Case appears; document cross-ref |
| **No match** | New intake — set Account from provider name in subject |

Attachment sync policy for COI: **`full`** or **`latest-reply-only`** (see
[attachment-sync.md](attachment-sync.md)).

### 5. Document

- SF **Task** on Case: `Federated COI update — Req {req_id} ({policy_id})`
- Note body: source (FD # or inbound email), files synced, prior Case numbers
  closed as duplicates (if operator merges)

## Batch scan — Federated COI mode

```bash
python scripts/scan_duplicates.py \
  --window-start 2026-06-01T00:00:00Z \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --include-coi \
  --output .tmp/fd-sf-duplicate-scan-coi-{date}.json
```

Report sections:

- **Req-id matched pairs** — `(policy_id, req_id)` aligned FD ↔ SF
- **Intra-system duplicates** — multiple FD or multiple SF with same Req id
- **Provider-only collisions** — downgraded fedcerts sender matches

## Example — Angeles Plumbing, LLC (`450-802-4`)

Multiple tickets were created for the **same Federated Req id** because forwards
and auto-replies were treated as new intake.

| Req id | Freshdesk | Salesforce | Status pattern |
| ---: | --- | --- | --- |
| **17** | #48695, #49190, #58276 | #00005985 | 3 FD + 1 SF — **same thread** |
| **19** | #49414 | #00005886 | FD closed + SF Working |
| **21** | #58573 | — | FD only (closed) |
| **22** | — | #00005831 | SF closed |
| **23** | — | #00006016 | SF New (Jun 29) — **new request**, not Req 17 |

**Correct handling for Req 17:**

1. Parse `450-802-4 Req 17~2026-02-02 11:39:27.0~00002` from any variant subject.
2. Find open Case/ticket with that key → route auto-reply and forwards there.
3. Close or merge duplicate Cases (#00005985 on Shell Account is a misroute).
4. Set Account to **Angeles Plumbing LLC** (provider name in subject).

**Req 23** is a **separate** Federated request (new cert cycle Jun 29) — keep as
its own Case unless operator confirms supersession.

## Senders and queues

| Sender | Typical meaning |
| --- | --- |
| `fedcerts-donotreply@fedins.com` | Cert delivery or Federated system message |
| `donotreply@…` (internal forward) | Vixxo mailbox re-forward — still parse Req id |

| Queue | Notes |
| --- | --- |
| FD **COI** tag / `COI@vixxo.com` | Primary Federated intake |
| FD **SPM** group | Some COI tickets routed here with `coi-reviewed` tag |
| SF **Service Provider Support** | Email-to-Case parallel intake |

Widen FD scan beyond SPM when investigating COI duplicates (`--include-coi`).

## Guardrails

- **No outbound** forwards unless {{employee_name}} approves.
- **Do not merge different Req ids** for the same SP without operator confirmation.
- Deficient COI (`coi-deficient`) stays in COI workflow — do not route to
  `aphelp@vixxo.com`.
- Prefer **`--dry-run`** on attachment sync when Req-id match is ambiguous.
