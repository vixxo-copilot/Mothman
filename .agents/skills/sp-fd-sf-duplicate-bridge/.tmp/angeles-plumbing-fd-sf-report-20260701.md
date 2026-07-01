# Angeles Plumbing LLC — Federated COI Duplicate Report

**Generated:** 2026-07-01 (live SF SOQL + Freshdesk MCP)  
**Policy id:** `450-802-4`  
**SP:** Angeles Plumbing, LLC (`cf_sp`: Angeles Plumbing - 101659)

## Executive summary

Angeles Plumbing has **4 distinct Federated requests** (Req 17, 19, 21, 22, 23) across FD and SF.
The duplicate problem is concentrated on **Req 17**: three Freshdesk tickets and one Salesforce
Case for the same Federated request. Other Req ids are mostly 1:1 or single-system only.

| Req id | FD tickets | SF Cases | Duplicate? |
| ---: | --- | --- | --- |
| **17** | #48695, #49190, #58276 | #00005985 | **Yes — 3 FD + 1 SF** |
| **19** | #49414 | #00005886 | Paired (no intra-system dupes) |
| **21** | #58573 | — | FD only |
| **22** | — | #00005831 | SF only |
| **23** | — | #00006016 | SF only |

---

## Req 17 — `450-802-4 Req 17~2026-02-02 11:39:27.0~00002` (PRIMARY DUPLICATE)

**Recommended primary FD ticket:** [#48695](https://vixxo-helpdesk.freshdesk.com/a/tickets/48695)  
- Status: Waiting on Third Party (7)  
- Created: 2026-05-25  
- Has cert attachment (`E218920.pdf`)  
- Original forward from Federated (not auto-reply only)

**Recommended primary SF Case:** None ideal — #00005985 is auto-reply on Shell Account.  
Prefer routing future Req 17 traffic to **FD #48695** until SF is corrected.

### Freshdesk (3 tickets — same Req id)

| FD | Status | Created | Notes |
|----|--------|---------|-------|
| [#48695](https://vixxo-helpdesk.freshdesk.com/a/tickets/48695) | Waiting on Third Party | 2026-05-25 | **Primary** — FW: cert with PDF |
| [#49190](https://vixxo-helpdesk.freshdesk.com/a/tickets/49190) | Closed | 2026-05-26 | Auto-reply duplicate |
| [#58276](https://vixxo-helpdesk.freshdesk.com/a/tickets/58276) | Closed | 2026-06-23 | Auto-reply duplicate |

### Salesforce (1 Case)

| SF Case | Status | Account | Created | Notes |
|---------|--------|---------|---------|-------|
| #00005985 | **New** | ⚠ Shell Account | 2026-06-29 | Fwd/FW auto-reply — should merge/close |

**Actions:**
1. Close SF **#00005985** or merge into correct Angeles Plumbing account workflow via FD #48695.
2. Close FD **#49190** and **#58276** as duplicate auto-replies (already Closed).
3. Route new Req 17 notifications to **FD #48695** (reopen if needed), not new tickets.

---

## Req 19 — paired FD ↔ SF

| System | Record | Status |
|--------|--------|--------|
| FD [#49414](https://vixxo-helpdesk.freshdesk.com/a/tickets/49414) | Closed | Cert + `coi-blocked` |
| SF #00005886 | Closed | Angeles Plumbing LLC account ✓ |

No intra-system duplicates. Bridge attachment if SF Case lacks PDF.

---

## Req 21 — FD only

| FD [#58573](https://vixxo-helpdesk.freshdesk.com/a/tickets/58573) | Closed | Auto-reply only, no SF Case found |

---

## Req 22 / 23 — SF only (separate cert cycles)

| SF Case | Req | Status | Account |
|---------|-----|--------|---------|
| #00005831 | 22 | Closed | Angeles Plumbing LLC |
| #00006016 | 23 | Closed | Angeles Plumbing LLC |

These are **not** duplicates of Req 17 — different Federated request numbers.

---

## Cross-system routing matrix

| Req id | Route updates to | Do not create |
|--------|------------------|---------------|
| 17 | FD #48695 | New FD tickets; SF #00005985 dupes |
| 19 | FD #49414 / SF #00005886 (closed — reopen if new cert) | New Cases |
| 21 | FD #58573 if reopened | New tickets |
| 22 | SF #00005831 | New Cases |
| 23 | SF #00006016 | New Cases |
