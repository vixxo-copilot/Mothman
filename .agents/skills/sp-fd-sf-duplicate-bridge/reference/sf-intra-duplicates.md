# Salesforce Intra-Org Duplicate Review

Use when the operator asks to review **duplicate Cases within Salesforce only**.
**Default for the duplicate-bridge / shell / all-org pipeline.** Do **not**
compare Cases to Freshdesk here.

## When to use

- "Find duplicate SF Cases for {provider}"
- "SF-only duplicate review" / all-org shell vet + HTML report
- Federated COI spawned multiple Cases for the same `Req {id}`
- Same email thread created multiple Cases (dual Email-to-Case)

## Match signals (priority)

| Signal | Group key | Action |
| --- | --- | --- |
| **Federated COI Req id** | `(policy_id, req_id)` from subject | Merge/close extras; keep oldest **open** non-shell Case |
| **Subject + requester email** | Normalized subject + `ContactEmail`/`SuppliedEmail` | Merge/close extras; prefer open Case |
| **Voicemail phone** | Normalized phone on voicemail Cases | Merge/close extras when same caller |

Skip `@vixxo.com` requester emails for subject+email grouping.

**Out of scope (default):** Freshdesk ticket `#` clustering (`--include-fd-xref`),
live FD↔SF pair detection (`scan_duplicates.py`). Those are **separate** and
only for AP-related SF Cases when the operator asks.

## Unified shell triage (all-org)

For Shell Account duplicate review, use **one SF-only pass** that mirrors
`sp-inbound-vetting` — do not run separate sender/broker/COI enrichment scans
and do **not** pull Freshdesk for duplicate comparison.

```bash
cd .agents/skills/sp-fd-sf-duplicate-bridge/scripts
RUN_DATE=YYYYMMDD python run_allorg_duplicate_vet_pipeline.py
```

Pipeline:

1. Export SF Cases to `.tmp/sf-cases-window-allorg-{RUN_DATE}.json`
2. Seed duplicate clusters from subject/metadata (**SF signals only**)
3. Full **EmailMessage + attachment** intake for shell open cases and duplicate
   cluster members (body context clues, attachment KS tokens)
4. Re-cluster duplicates using intake-enriched text
5. Shell vetting: Gateway + SF Account per case (`vet_shell_accounts_allorg.py`)
6. **COI PDF insured extraction** — download Case + EmailMessage PDFs and read
   insured / SP name (`extract_shell_coi_insured.py`). Required; do not skip.
   Broker subjects like `Re: REVISED Certificate of Insurance` often have the
   SP only in the attachment (e.g. The Pelczar Corporation).
   **Batch to avoid bog-down** (default batch 15, checkpoint + resume):

   ```bash
   RUN_DATE=YYYYMMDD python extract_shell_coi_insured.py --batch-size 10 --resume
   # re-run same command until it prints remaining=0
   ```

   Env: `COI_BATCH_SIZE`, `COI_LIMIT`, `COI_OFFSET`, `COI_RESUME=1`.
7. Write vetted JSON/Markdown/HTML under `.tmp/`
8. Needs-manual list: `python render_shell_needs_manual_html.py` (Chrome)

Outputs: `shell-account-vet-allorg-{RUN_DATE}.json`,
`sf-intra-duplicate-scan-allorg-vetted-{RUN_DATE}.html`

HTML reports **open in Chrome by default** when rendered
(`OPEN_REPORT=0` to skip).

Vet-only (cache already exported):

```bash
RUN_DATE=YYYYMMDD SF_CACHE_PATH=../.tmp/sf-cases-window-allorg-YYYYMMDD.json \
  python vet_shell_accounts_allorg.py
```

Opt-in FD xref clustering inside the SF scan (rarely needed):

```bash
SCAN_INCLUDE_FD_XREF=1 RUN_DATE=YYYYMMDD python vet_shell_accounts_allorg.py
```

## AP-related SF Case → separate FD check

If an SF Case is payment / remittance / invoice-AP and the operator wants to
know whether AP Help already has a ticket, run **after** the SF-only pass:

```bash
python scan_duplicates.py \
  --window-start {iso} \
  --sf-cache ../.tmp/sf-cases-window-allorg-{date}.json \
  --output ../.tmp/fd-sf-duplicate-scan-ap-{date}.json
```

Keep that report separate from the mothman SF duplicate HTML.

## Primary Case selection

1. Prefer **open** status (`New`, `Working`, `Pending`, `On Hold`, …)
2. Prefer non–shell Account over `Service Provider Support Shell Account`
3. Prefer **oldest** `CreatedDate` among ties

## SOQL export (MCP)

Minimum fields (include **Description** for voicemail / body context):

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
- Cross-system FD↔SF (**separate / AP opt-in**): [detection.md](detection.md)
- Federated parsing: [federated-coi.md](federated-coi.md)
