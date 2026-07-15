# Salesforce Intra-Org Duplicate Review

Use when the operator asks to review **duplicate Cases within Salesforce only**
(no Freshdesk pairing).

## When to use

- "Find duplicate SF Cases for {provider}"
- "SF-only duplicate review"
- Federated COI spawned multiple Cases for the same `Req {id}`
- Same email thread created multiple Cases (dual Email-to-Case)

## Match signals (priority)

| Signal | Group key | Action |
| --- | --- | --- |
| **Federated COI Req id** | `(policy_id, req_id)` from subject | Merge/close extras; keep oldest **open** non-shell Case |
| **Subject + requester email** | Normalized subject + `ContactEmail`/`SuppliedEmail` | Merge/close extras; prefer open Case |

Skip `@vixxo.com` requester emails for subject+email grouping.

## Primary Case selection

1. Prefer **open** status (`New`, `Working`, `Pending`, `On Hold`, …)
2. Prefer non–shell Account over `Service Provider Support Shell Account`
3. Prefer **oldest** `CreatedDate` among ties

## SOQL export (MCP)

Minimum fields (include **Description** for voicemail / FD cross-ref merge):

```sql
SELECT Id, CaseNumber, Subject, Description, Status, ContactEmail, SuppliedEmail,
       CreatedDate, LastModifiedDate, Account.Name, Owner.Username, Owner.Type
FROM Case
WHERE CreatedDate >= {window_start}
ORDER BY CreatedDate ASC
```

For Federated COI–focused review, filter subjects:

```sql
WHERE Subject LIKE 'Certificate Of Insurance -%'
   OR Subject LIKE 'RE: Certificate Of Insurance -%'
   OR Subject LIKE 'Fw:%Certificate Of Insurance -%'
```

Save MCP JSON to `.tmp/sf-cases-window-{date}.json`.

## Batch scan

```bash
python scripts/scan_sf_duplicates.py \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --output .tmp/sf-duplicate-scan-{date}.json \
  --report .tmp/sf-duplicate-report-{date}.md \
  --window-note "CreatedDate >= 2026-06-29"
```

## Output

- **JSON:** `federated_duplicates[]`, `subject_duplicates[]`, `by_provider{}`
- **Markdown:** summary table + **one row per SP** with primary Case and merge list

## Merge / close automation

After scan, build a bucket-based merge plan (dry-run default):

```bash
python scripts/merge_sf_duplicates.py \
  --scan-input .tmp/sf-duplicate-scan-{date}.json \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --output .tmp/sf-merge-plan-{date}.json
```

Execute only after operator approval: `--execute`. See
[merge-automation.md](merge-automation.md).

## Guardrails

- **Default dry-run** — use `merge_sf_duplicates.py --execute` only after operator approval.
- Federated **auto-reply** Cases (`RE: Certificate Of Insurance … Auto Reply`) are often dupes of the cert Case with the same Req id — merge into primary.
- Same Req id with **different** suffix (`~00001` vs `~00002`) is still one Federated request when Req id matches.
- Skip `confidence: low` groups (agent cert batches) unless operator confirms.

## Related

- Merge automation: [merge-automation.md](merge-automation.md)
- Cross-system (FD↔SF): [detection.md](detection.md)
- Federated parsing: [federated-coi.md](federated-coi.md)
