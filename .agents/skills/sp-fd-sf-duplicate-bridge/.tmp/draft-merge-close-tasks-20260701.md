# Draft — Federated COI Merge/Close Tasks (SF primary)

**Status:** Draft only — not posted. Approve before SF Tasks, Case updates, or FD notes.

**Policy:** **Salesforce is the system of record.** Keep the SF Case per Req id.
Close Freshdesk tickets as duplicates after attachments are bridged to SF.

**Dedupe key:** `(policy_id, Req id)` — [federated-coi.md](../reference/federated-coi.md)

---

## Summary (revised)

| Group | **Keep (SF)** | Close SF duplicate | Close FD duplicate(s) |
|-------|---------------|--------------------|------------------------|
| CECCO Req 201 | #00006053 | #00006107 | — (none found) |
| Storefronts Req 339 | #00005852 | #00005853 | — (verify) |
| Smelscer Req 365 | #00006007 | #00005986 | — (verify) |
| Angeles Req 17 | **#00005985** | — | #48695, #49190, #58276 |
| Angeles Req 19 | **#00005886** | — | #49414 |

**Order of operations (Angeles Req 17):** Sync FD #48695 cert → SF #00005985 → fix
Account on SF → SF Task → then close FD tickets. Do not close FD #48695 before sync.

---

## Task 1 — CECCO, Inc. (`150-339-0 Req 201`)

| Role | Record |
|------|--------|
| **Keep** | SF #00006053 (`500TS00000npsILYAY`) — Working |
| Close | SF #00006107 — auto-reply duplicate (already Closed) |

### SF Task (Completed) — on #00006053

**Subject:** `Federated COI dedupe — Req 201 — SF primary; duplicate Case #00006107`

**Description:**
```
SF is primary for Federated request 150-339-0 Req 201.

Keep: Case #00006053 (cert delivery, Working).
Duplicate: Case #00006107 — RE/auto-reply only; same Req id.

FD: no paired ticket. Future Federated traffic for this Req id → append to #00006053.

Cross-ref: sp-fd-sf-duplicate-bridge 2026-07-01.
```

### SF — #00006107 (comment if needed)

Already Closed. Optional Case comment:
```
Duplicate of primary Case #00006053 (150-339-0 Req 201). SF primary holds COI workflow.
```

---

## Task 2 — Storefronts and Entrances (`177-561-8 Req 339`)

| Role | Record |
|------|--------|
| **Keep** | SF #00005852 (`500TS00000nYKjHYAW`) — Closed, KS - Entrance Door & Glass Co. |
| Close | SF #00005853 — Shell Account re-intake |

### SF Task (Completed) — on #00005852

**Subject:** `Federated COI dedupe — Req 339 — SF primary; closed Case #00005853`

**Description:**
```
SF is primary for Federated request 177-561-8 Req 339.

Keep: Case #00005852 — cert processed; correct SP Account.
Duplicate: Case #00005853 — same Req id; Shell Account re-intake.

Action: Close #00005853. Reopen #00005852 if new Federated mail arrives for Req 339
(append EmailMessage; do not create new Case or FD ticket).

Cross-ref: sp-fd-sf-duplicate-bridge 2026-07-01.
```

### SF — Close #00005853 (`500TS00000nYWVtYAO`)

**Reason:** Duplicate of #00005852 — same 177-561-8 Req 339.

---

## Task 3 — Smelscer Plumbing (`365-728-5 Req 365`)

| Role | Record |
|------|--------|
| **Keep** | SF #00006007 (`500TS00000nnUiLYAU`) — New |
| Close | SF #00005986 — auto-reply duplicate |

### SF Task (Completed) — on #00006007

**Subject:** `Federated COI dedupe — Req 365 — SF primary; closed Case #00005986`

**Description:**
```
SF is primary for Federated request 365-728-5 Req 365.

Keep: Case #00006007 — Fw: from kmtaylorsa@fedins.com (substantive thread).
Duplicate: Case #00005986 — Fwd/FW auto-reply only.

Action: Close #00005986. Update Account from Shell to Smelscer Plumbing, Inc.
Search FD for same Req id; if found, bridge attachments then close FD as duplicate.

Cross-ref: sp-fd-sf-duplicate-bridge 2026-07-01.
```

### SF — Close #00005986 (`500TS00000nmAlgYAE`)

**Reason:** Duplicate of #00006007 — same 365-728-5 Req 365.

---

## Task 4 — Angeles Plumbing Req 17 (`450-802-4 Req 17`)

| Role | Record |
|------|--------|
| **Keep** | SF **#00005985** (`500TS00000nmtkLYAQ`) — New |
| Close FD | [#48695](https://vixxo-helpdesk.freshdesk.com/a/tickets/48695), #49190, #58276 |

**Gap:** SF #00005985 is auto-reply only (Shell Account). FD #48695 holds the cert
(`E218920.pdf`). Remediate SF **before** closing FD.

### Step A — Bridge FD → SF (approve separately)

```bash
python scripts/sync_attachments_to_sf.py \
  --fd-ticket-id 48695 \
  --sf-case-number 00005985 \
  --policy full \
  --dry-run
```

After dry-run review, run without `--dry-run`.

### Step B — SF Case updates on #00005985

1. **Account** → Angeles Plumbing LLC (from subject / FD `cf_sp`)
2. **Status** → Working (or appropriate open status)
3. Optional: add `Freshdesk #48695` to Description for audit trail before FD close

### SF Task (Completed) — on #00005985

**Subject:** `Federated COI dedupe — Req 17 — SF primary; FD duplicates closed`

**Description:**
```
SF is primary for Federated request 450-802-4 Req 17.

Keep: Case #00005985 (SF Case for Req 17).
Remediated: Account → Angeles Plumbing LLC; cert synced from Freshdesk #48695.

FD duplicates closed after sync:
  - #48695 (was Waiting on Third Party — cert source)
  - #49190, #58276 (auto-reply dupes; were already Closed)

Future Req 17 notifications → append to this Case; do not create new SF Case or FD ticket.

Cross-ref: angeles-plumbing-fd-sf-report-20260701.md
```

### FD internal notes (draft — approve before posting)

**#48695** (after SF sync):
```
SF primary — Case #00005985 (450-802-4 Req 17). Cert synced to SF. Closing FD duplicate.
```

**#49190 / #58276** (already Closed; optional note):
```
Duplicate of SF Case #00005985 / FD #48695 — same Req 17 auto-reply. SF is primary.
```

---

## Task 5 — Angeles Plumbing Req 19 (`450-802-4 Req 19`)

| Role | Record |
|------|--------|
| **Keep** | SF **#00005886** (`500TS00000nZfYlYAK`) — Closed, Angeles Plumbing LLC |
| Close FD | [#49414](https://vixxo-helpdesk.freshdesk.com/a/tickets/49414) |

### Step A — Verify SF has cert

FD #49414 has `ER12480.pdf`. Confirm `ContentDocumentLink` on #00005886; if missing:

```bash
python scripts/sync_attachments_to_sf.py \
  --fd-ticket-id 49414 \
  --sf-case-number 00005886 \
  --policy full \
  --dry-run
```

Reopen #00005886 only if COI review still open.

### SF Task (Completed) — on #00005886

**Subject:** `Federated COI dedupe — Req 19 — SF primary; FD #49414 closed`

**Description:**
```
SF is primary for Federated request 450-802-4 Req 19.

Keep: Case #00005886 (Angeles Plumbing LLC).
FD #49414 — dual-intake duplicate; closed after cert verified/synced on SF.

Cross-ref: angeles-plumbing-fd-sf-report-20260701.md
```

### FD internal note — #49414 (draft)

```
SF primary — Case #00005886 (450-802-4 Req 19). Closing FD duplicate.
```

---

## What changed from prior draft

| Item | Prior (wrong) | Revised (SF primary) |
|------|---------------|----------------------|
| Angeles Req 17 | Keep FD #48695, close SF #00005985 | **Keep SF #00005985**, sync cert, close FD #48695 + dupes |
| Angeles Req 19 | Not in close list | **Keep SF #00005886**, close FD #49414 |
| FD role | Primary for Angeles | Duplicate after bridge to SF |

---

## Operator checklist

### SF-only duplicate groups (Tasks 1–3)
- [ ] Task 1 on #00006053
- [ ] Task 2 on #00005852 + Close #00005853
- [ ] Task 3 on #00006007 + Close #00005986 + fix Smelscer Account

### Angeles (Tasks 4–5) — SF primary, FD close
- [ ] Sync FD #48695 → SF #00005985 (dry-run first)
- [ ] Update #00005985 Account + Status
- [ ] Task 4 on #00005985
- [ ] FD notes + close #48695 (and confirm #49190/#58276)
- [ ] Verify/sync FD #49414 → SF #00005886
- [ ] Task 5 on #00005886
- [ ] FD note + close #49414

---

## SF CLI snippets (after approval)

**Task 4 on #00005985:**
```powershell
& "$env:APPDATA\npm\sf.cmd" data create record --sobject Task --target-org vixxo --values "Subject='Federated COI dedupe — Req 17 — SF primary; FD duplicates closed' WhatId='500TS00000nmtkLYAQ' Status='Completed' Priority='Normal' Description='SF primary for 450-802-4 Req 17. Cert synced from FD #48695. FD dupes closed.'"
```

**Task 5 on #00005886:**
```powershell
& "$env:APPDATA\npm\sf.cmd" data create record --sobject Task --target-org vixxo --values "Subject='Federated COI dedupe — Req 19 — SF primary; FD #49414 closed' WhatId='500TS00000nZfYlYAK' Status='Completed' Priority='Normal' Description='SF primary for 450-802-4 Req 19. FD dual-intake closed.'"
```

*(Tasks 1–3 CLI unchanged from prior draft — all SF-on-SF.)*

**Say "post them" to create SF Tasks.** FD closes/notes require separate approval per
outbound guardrail.
