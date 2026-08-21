# SF Duplicate Merge Automation

Automates consolidation of duplicate Salesforce Cases into **one open ticket
per bucket** — reducing queue inflation while preserving files and audit trail.

## Buckets

| Bucket | `bucket` id | Group key | Auto-merge |
| --- | --- | --- | --- |
| Federated COI | `coi_federated` | `(policy_id, req_id)` | Yes |
| Other COI / proof | `coi_update` | SP name + requester email | Yes (route to onboarding when configured) |
| Rate change / negotiation | `rate_change` | SP name + requester email | Yes |
| VixxoLink assistance | `vixxolink_support` | **Same requester email** (+ SP when present) | Yes |
| Voicemail (SP triage) | `voicemail` | SP name or Freshdesk `#` cross-ref | Yes when SP captured |
| Onboarding | `onboarding` | SP name + email | Manual review |
| Invoice reminder | `invoice_reminder` | subject + email | Manual review |
| Payment / AP | `payment_ap` | SP + email | Yes |

Classification lives in `scripts/sf_case_buckets.py`.

## COI routing

When `--resolve-coi-onboarding` is set and no clear COI primary exists, the
script searches for an **open onboarding Case** for the same SP:

```sql
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE IsClosed = false
  AND Subject LIKE '%{sp_name}%'
  AND (Subject LIKE '%onboarding%' OR Subject LIKE '%KSOnboarding%'
       OR Subject LIKE '%KS - %')
ORDER BY CreatedDate ASC
LIMIT 5
```

Use the earliest open match as primary. COI updates land on the onboarding
thread instead of spawning a third Case.

## Voicemail forwarding

Voicemail Cases from `sp-voicemail-triage` store **Description + transcript**
fields used to find existing open work:

| Field | Example |
| --- | --- |
| `Company:` | SP legal / trade name |
| `Caller:` | Contact name |
| `Callback:` | Phone (last-10 match) |
| Transcript body | Token overlap vs open Cases |
| `Freshdesk #{id}` | Exact cross-ref |

Before merging voicemail dupes, search the full SF export for **open,
actively-worked** Cases matching company, caller, callback phone, or transcript
tokens — **only when the voicemail request context matches the target Case
bucket**.

### Context-aligned routing (required)

Voicemail **Category** + **transcript** resolve to an `intent_bucket`
(`vixxolink_support`, `rate_change`, `coi_update`, etc.). Cross-bucket routing
happens **only** when intent matches target:

| Voicemail intent | May route into open Case buckets |
| --- | --- |
| `vixxolink_support` | VixxoLink Cases only |
| `rate_change` | Rate negotiation Cases only |
| `coi_update` | COI + onboarding Cases |
| `onboarding` | Onboarding + COI Cases |
| `payment_ap` / `invoice_reminder` | Payment / invoice Cases |
| Unknown / general | **No cross-bucket routing** — voicemail dupes only |

Example: VixxoLink support voicemail for Provider X **does not** merge into
Provider X's open rate negotiation Case even when SP name and phone match.

Target must also be **actively worked** (not `New` queue-owned with no activity).

### Primary selection rules

1. **Never merge into a closed Case**
2. **Prefer actively-worked** over `New` when both exist
3. **Prefer most recent touch** — latest of CaseComment, CaseHistory, Task, or `LastModifiedDate`
4. **Prefer user-assigned** over queue-owned when multiple `New` Cases exist
5. **Multiple New, all queue-owned, no activity** → `manual_review` report
6. **Multiple New, only one has comments/history/tasks** → auto-merge into that Case
7. **Multiple New with competing recent touches** → manual review

Live touch lookup runs during plan build (Salesforce CLI SOQL). Use
`--skip-touch-lookup` for cache-only (`LastModifiedDate` from export).

See `scripts/sf_case_activity.py`, `scripts/sf_merge_primary.py`,
`scripts/voicemail_match.py`.

## Merge sequence (live)

For each duplicate → primary:

1. **Copy files** — `ContentDocumentLink` from duplicate Case to primary
2. **Case comment on primary** — documents merged Case number and bucket
3. **Case comment on duplicate** — `Closed Reason: Duplicate` + reference primary Case #
4. **Voicemail sync** (optional) — FD `.wav` → primary if missing
5. **Audit Task** on primary — completed, merge metadata
6. **Close duplicate** — `Status=Closed` + `Not_Filled_Reason__c=Duplicate`

No outbound email. No Freshdesk writes unless operator separately approves FD
close notes.

## Operator workflow

### 1. Scan (existing)

```bash
python scripts/scan_sf_duplicates.py \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --output .tmp/sf-duplicate-scan-{date}.json \
  --report .tmp/sf-duplicate-report-{date}.md
```

### 2. Build merge plan (dry-run default)

```bash
python scripts/merge_sf_duplicates.py \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --scan-input .tmp/sf-duplicate-scan-{date}.json \
  --buckets coi_federated,coi_update,rate_change,vixxolink_support,voicemail \
  --resolve-coi-onboarding \
  --output .tmp/sf-merge-plan-{date}.json
```

Review `.tmp/sf-merge-plan-{date}.json`. Skip `confidence: low` groups
(agent cert batches with different insureds).

### 3. Execute (after explicit approval)

```bash
python scripts/merge_sf_duplicates.py \
  --plan .tmp/sf-merge-plan-{date}.json \
  --execute \
  --sync-voicemail \
  --group-id coi_federated:30201157|12345
```

Omit `--group-id` to run all groups in the plan. Requires Salesforce CLI
(`sf`) authenticated to org `vixxo`.

## Confidence levels

| Level | Meaning |
| --- | --- |
| `high` | Federated Req id, active-work target, voicemail with FD cross-ref |
| `medium` | Bucket match + SP/email; COI routed to onboarding; New-only work target |
| `low` | Agent cert batch — **do not auto-close** without operator confirm |
| `manual` | Multiple New queue-owned with no activity, or competing recent touches |

## Last-touch lookup (plan build)

During merge plan generation, query Salesforce for recent activity per Case:

| Source | SOQL object | Signal |
| --- | --- | --- |
| Case comments | `CaseComment` | Latest `CreatedDate` + author |
| Field changes | `CaseHistory` | Latest status/owner change |
| Tasks | `Task` | Latest `LastModifiedDate` on Case |
| Case record | `Case.LastModifiedDate` | Fallback from export |

Primary selection ranks: **active status → user assigned → has comment/history/task → most recent touch**.

```bash
# Default: live touch lookup via sf CLI
python scripts/merge_sf_duplicates.py --sf-cache ... --output ...

# Offline: export LastModifiedDate only
python scripts/merge_sf_duplicates.py --sf-cache ... --skip-touch-lookup ...
```

## Guardrails

- **Default dry-run** — `--execute` required for writes
- **No outbound** without separate approval
- Deficient COIs stay in COI workflow — never AP Help (`vixxo-coi-review`)
- Prefer single primary per SP per bucket; do not merge across buckets

## Related

- [sf-intra-duplicates.md](sf-intra-duplicates.md) — detection
- [federated-coi.md](federated-coi.md) — Req-id parsing
- [attachment-sync.md](attachment-sync.md) — FD file sync
- `sp-voicemail-triage` — creates voicemail Cases + FD cross-ref
