# Salesforce Federated COI Duplicate Report (YTD 2026)

**Generated:** 2026-07-01 15:34 UTC
**Source:** `sf-cases-federated-coi-20260701.json` (23 Cases, Federated `Certificate Of Insurance - … Req …` YTD 2026)

## Summary

| Metric | Count |
|--------|------:|
| SF Cases in window | 23 |
| Parsed Federated COI (Req id) | 23 |
| Unique Req keys | 20 |
| Req keys with duplicates | 3 |
| Excess Cases (merge/close candidates) | 3 |

## Duplicate groups — same `(policy_id, Req id)`

| Provider | Req key | Cases | Open | Recommended primary | Merge/close |
|----------|---------|------:|-----:|---------------------|-------------|
| CECCO, Inc. | `150-339-0 Req 201` | 2 | 1 | **00006053** (Working) | 00006107 |
| Storefronts and Entrances, Inc. | `177-561-8 Req 339` | 2 | 1 | **00005853** (New) | 00005852 |
| Smelscer Plumbing, Inc. | `365-728-5 Req 365` | 2 | 2 | **00005986** (New) | 00006007 |

## Detail by duplicate group

### CECCO, Inc. — `150-339-0 Req 201`

**Primary:** 00006053 (Working, KS - Bluefield Glass & Interiors)

| Case | Status | Account | Created | Subject |
|------|--------|---------|---------|---------|
| 00006053 **← primary** | Working | KS - Bluefield Glass & Interiors | 2026-06-30 | Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 20 |
| 00006107 | Closed | KS - Bluefield Glass & Interiors | 2026-06-30 | RE: Certificate Of Insurance - CECCO, Inc. 150-339-0 Re |

### Storefronts and Entrances, Inc. — `177-561-8 Req 339`

**Primary:** 00005853 (New, Service Provider Support Shell Account)

| Case | Status | Account | Created | Subject |
|------|--------|---------|---------|---------|
| 00005852 | Closed | KS - Entrance Door & Glass Co. | 2026-06-25 | Certificate Of Insurance - Storefronts and Entrances, I |
| 00005853 **← primary** ⚠ | New | Service Provider Support Shell Account | 2026-06-25 | Certificate Of Insurance - Storefronts and Entrances, I |

### Smelscer Plumbing, Inc. — `365-728-5 Req 365`

**Primary:** 00005986 (New, Service Provider Support Shell Account)

| Case | Status | Account | Created | Subject |
|------|--------|---------|---------|---------|
| 00005986 **← primary** ⚠ | New | Service Provider Support Shell Account | 2026-06-29 | Fwd: FW: Certificate Of Insurance - Smelscer Plumbing,  |
| 00006007 ⚠ | New | Service Provider Support Shell Account | 2026-06-29 | Fw: Certificate Of Insurance - Smelscer Plumbing, Inc.  |
