# Salesforce Federated COI Duplicate Report

**Generated:** 2026-07-01 15:21 UTC

## Summary

| Metric | Count |
|--------|------:|
| Total SF Cases in export | 23 |
| Parsed Federated COI (Req id) | 23 |
| Unique Req keys | 20 |
| Req keys with duplicates | 3 |
| Excess Cases (could merge/close) | 3 |

## Duplicate groups — same `(policy_id, Req id)`

Each row is one Federated request that spawned multiple SF Cases.
Prefer the **recommended primary** (oldest open); close or merge others.

### CECCO, Inc. — `150-339-0 Req 201` (2 Cases, 1 open)

**Recommended primary:** 00006053 (Working, KS - Bluefield Glass & Interiors, 2026-06-30)

| Case | Status | Account | Created | Owner | Subject |
|------|--------|---------|---------|-------|---------|
| 00006053 **← primary** | Working | KS - Bluefield Glass & Interiors | 2026-06-30 | andrea.heppler | Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 20 |
| 00006107 | Closed | KS - Bluefield Glass & Interiors | 2026-06-30 | andrea.heppler | RE: Certificate Of Insurance - CECCO, Inc. 150-339-0 Re |

### Storefronts and Entrances, Inc. — `177-561-8 Req 339` (2 Cases, 1 open)

**Recommended primary:** 00005853 (New, Service Provider Support Shell Account, 2026-06-25)

| Case | Status | Account | Created | Owner | Subject |
|------|--------|---------|---------|-------|---------|
| 00005852 | Closed | KS - Entrance Door & Glass Co. | 2026-06-25 | andrea.heppler | Certificate Of Insurance - Storefronts and Entrances, I |
| 00005853 **← primary** ⚠ shell | New | Service Provider Support Shell Account | 2026-06-25 | crystal.gagner | Certificate Of Insurance - Storefronts and Entrances, I |

### Smelscer Plumbing, Inc. — `365-728-5 Req 365` (2 Cases, 2 open)

**Recommended primary:** 00005986 (New, Service Provider Support Shell Account, 2026-06-29)

| Case | Status | Account | Created | Owner | Subject |
|------|--------|---------|---------|-------|---------|
| 00005986 **← primary** ⚠ shell | New | Service Provider Support Shell Account | 2026-06-29 | andrea.heppler | Fwd: FW: Certificate Of Insurance - Smelscer Plumbing,  |
| 00006007 ⚠ shell | New | Service Provider Support Shell Account | 2026-06-29 | crystal.gagner | Fw: Certificate Of Insurance - Smelscer Plumbing, Inc.  |

## Angeles Plumbing LLC spotlight

No duplicate Req-id groups in export (each Req has one SF Case).

Angeles Plumbing Cases in export (all Req ids): see duplicate table above and FD↔SF scan report.
