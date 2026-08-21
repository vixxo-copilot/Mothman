# Angeles Consolidation — Execution Report

**Executed:** 2026-07-01  
**Primary Case:** SF **#00005985** (`500TS00000nmtkLYAQ`)

## Result: Mostly complete

| Step | Status | Notes |
|------|--------|-------|
| Update #5985 Account/Status/Subject | ✅ | Angeles Plumbing LLC, **Working** |
| Reparent EmailMessages | ⚠️ | **Blocked** — `EmailMessage.ParentId` not writable (FLS) |
| Link SF certs to Case | ✅ | EP15270, ET19680 on Files tab |
| Sync FD #48695 → SF | ✅ | E218920.pdf (uploaded twice — dedupe optional) |
| Sync FD #49414 → SF | ✅ | ER12480.pdf |
| FD thread Tasks on #5985 | ✅ | 5 Tasks created |
| Consolidation Task | ✅ | On #5985 |
| SF email archive Tasks | ✅ | 3 Tasks (Req 19/22/23 fallback) |
| Close SF #5886, #5831, #6016 | ✅ | All **Closed** |
| FD notes + close | ✅ | #48695, #49414, #49190, #58276, #58573 **Closed** |

## Primary Case state (post-run)

| Field | Value |
|-------|-------|
| Case | **#00005985** |
| Status | **Working** |
| Account | **Angeles Plumbing LLC** |
| Subject | Certificate Of Insurance - Angeles Plumbing, LLC 450-802-4 (Consolidated Federated COI) |

## Files on #00005985

| File | Source |
|------|--------|
| E218920.pdf (×2) | FD #48695 — remove duplicate link if desired |
| ER12480.pdf | FD #49414 |
| EP15270 | SF Req 22 (Case #5831 email) |
| ET19680 | SF Req 23 (Case #6016 email) |

## Email threads

- **On #5985 Email-to-Case feed:** Req 17 auto-reply (original)
- **Archived via Tasks:** Req 19, 22, 23 (source EmailMessages remain on closed Cases #5886, #5831, #6016 — viewable there; certs on primary Files)

## Closed duplicates

**Salesforce:** #00005886, #00005831, #00006016  
**Freshdesk:** #48695, #49414, #49190, #58276, #58573

## Follow-up (optional)

1. Remove duplicate **E218920.pdf** ContentDocumentLink on #5985
2. Admin: enable EmailMessage ParentId update if true reparent needed in future
3. Continue COI review on **#00005985** only

Log: `.tmp/angeles-consolidate-5985-run/execution-log.json`
