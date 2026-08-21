# Duplicate Detection — Freshdesk vs Salesforce

## When duplicates happen

| Pattern | Typical origin | Confidence |
| --- | --- | --- |
| **Voicemail dual-intake** | FD first (8x8 `.wav`), then `sp-voicemail-triage` creates SF Case | High — SF Description contains `Freshdesk #{id}` |
| **Email dual-intake** | Same inbound email to FD mailbox and SF Email-to-Case within seconds | High — shared requester email + subject overlap ≥ 0.5 |
| **KS onboarding mirror** | FD KSOnboarding ticket + manually or triage-created SF Case for same SP | Medium — company name + requester email; may lack cross-ref until bridged |
| **Contact collision** | Same requester email, unrelated subjects (AP vs onboarding, batch COI sender) | Low — treat as **not** same thread |
| **Federated COI dual-intake** | Same cert at **COI@vixxo.com** (FD) and SF Email-to-Case; or duplicate forwards/auto-replies on same Req | High — match **`{policy-id} Req {req_id}`** in subject; supporting: provider name |
| **Federated COI re-forward** | `Fwd:` / `FW:` / Auto Reply on an existing Req id | High — same `(policy_id, req_id)` as an open Case/ticket |

## Federated Insurance COI pairing

Full vetting and routing workflow: [federated-coi.md](federated-coi.md).

Federated batch certs share one noreply sender; each message is a **distinct
request** identified by **Req id** in the subject. Pair and route on Req id first,
not sender email.

| Signal | Use for pairing / routing? |
| --- | --- |
| Shared `fedcerts-donotreply@fedins.com` | **No** — contact collision |
| **`{policy-id} Req {req_id}`** in FD + SF subject | **Yes** — same Federated request (`true_same_thread`) |
| Identical provider name only (Req id missing/unparsed) | **Maybe** — operator confirm |
| `Freshdesk #{id}` in SF Description | **Yes** — if present (uncommon for COI) |

**Subject pattern:** `Certificate Of Insurance - {Provider} {policy-id} Req {req_id}~{timestamp}~{suffix}`

**Scan scope note:** batch scan defaults to Freshdesk **SPM group** only. Federated COI dual-intake often lands in the **COI Freshdesk queue** (`COI` tag / `COI@vixxo.com`) — use `--include-coi` or Req-id SOQL + FD subject search.

**Routing note:** deficient COI outcomes (`coi-deficient`, status Resolved) **stay in COI workflow** — never forward to `aphelp@vixxo.com`. SP resubmission reopens the FD ticket. **Do not create a new SF Case** when an open Case already exists for the same `(policy_id, req_id)`.
## Match signals (priority order)

1. **`Freshdesk #{ticket_id}` in SF Case Description or Subject** → `true_same_thread`
2. **Federated COI `(policy_id, req_id)`** in both subjects → `true_same_thread` (see [federated-coi.md](federated-coi.md))
3. **Shared external requester email** on FD contact and SF `ContactEmail` / `SuppliedEmail`
4. **Subject token Jaccard similarity** ≥ 0.35 (supporting signal)
5. **Federated COI provider name** in both subjects (when Req id absent) → `likely_same_thread`
6. **Manual pair** — operator supplies FD `#` + SF Case `#` (always allowed)

Skip internal addresses when matching email: `@vixxo.com`, `@8x8.com`, `@vixxo-helpdesk`, `@notification.intuit.com`.

## Classification

| `dup_type` | Rule |
| --- | --- |
| `true_same_thread` | FD id in SF Description **or** Federated `(policy_id, req_id)` match **or** subject similarity ≥ 0.5 with shared requester |
| `likely_same_thread` | Shared requester + subject similarity 0.25–0.49; or provider-name-only COI match |
| `contact_collision` | Shared requester only; subject similarity &lt; 0.25; or fedcerts sender without Req-id/provider match |

Only **`true_same_thread`** and **`likely_same_thread`** are candidates for attachment sync unless the operator explicitly pairs records.

## Read path

### Single pair lookup

**Freshdesk:** MCP `get_ticket` (include conversations) + `get_ticket_conversation`.

**Salesforce:** MCP `run_soql_query` (org from `get_username`):

```sql
SELECT Id, CaseNumber, Subject, Status, Description, ContactEmail,
       SuppliedEmail, CreatedDate
FROM Case
WHERE CaseNumber = '{case_number}'
   OR Description LIKE '%Freshdesk #{fd_ticket_id}%'
   OR Subject LIKE '%Freshdesk #{fd_ticket_id}%'
ORDER BY CreatedDate DESC
LIMIT 5
```

**Federated COI — find open Case by Req id** (before creating a new Case):

```sql
SELECT Id, CaseNumber, Subject, Status, Account.Name, CreatedDate
FROM Case
WHERE Subject LIKE '%{policy_id} Req {req_id}~%'
   OR Subject LIKE '%{policy_id} Req {req_id} %'
ORDER BY CreatedDate DESC
LIMIT 10
```

Filter to open statuses (`New`, `Working`, `Open`) in application logic.

### Window batch scan

Run `scripts/scan_duplicates.py` (see SKILL.md). Requires a cached SF Case export JSON from MCP SOQL:

```sql
SELECT Id, CaseNumber, Subject, Status, Description, ContactEmail,
       SuppliedEmail, CreatedDate
FROM Case
WHERE CreatedDate >= {window_start_iso}
ORDER BY CreatedDate ASC
```

Save result to `.tmp/sf-cases-window-{date}.json` before running the scan script.

## Freshdesk search caveat

Freshdesk MCP `search_tickets` may return HTTP 400 for some filter syntax. Fallback: REST `/api/v2/search/tickets` day-by-day with `created_at` bounds + `group_id:159000485013`, or list API with `updated_since` + client-side `created_at` filter (may miss never-updated tickets).

## Output

Batch scan writes JSON with `pairs[]` entries:

- `match_reasons`, `dup_type`, `origin` (`fd_first` / `sf_first` / `same_time`)
- `freshdesk`: id, subject, attachment_count, conversation_count
- `salesforce`: id, case_number, subject, status

Summarize for the operator as a table (see [examples.md](examples.md)).
