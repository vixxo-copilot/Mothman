# Freshdesk ↔ Salesforce Duplicate Scan (COI widened)

**Skill:** `sp-fd-sf-duplicate-bridge`  
**Window:** 2026-06-29 00:00 UTC → 2026-06-30 ~6:16 PM UTC  
**Generated:** 2026-06-30

## Summary

| Metric | Count |
|--------|------:|
| FD inbound (SPM + COI tag widen) | 302 |
| SF Cases (CreatedDate ≥ Jun 29) | 120 |
| Duplicate pairs | 12 |
| True same-thread | **0** |
| COI provider-matched (`coi_provider_name_match`) | **0** |
| Contact collision | 12 |

**Key finding:** Federated COI **provider-name pairing found zero true pairs**. Only one
Federated COI FD ticket exists in the window (#60160 Tri Star Transport). The five
known Jun 29–30 SF Federated COI Cases have **no corresponding FD tickets** (SF-only
intake). Tri Star has an FD ticket but **no SF Case** — not a dual-intake pair.

---

## Federated COI provider-matched pairs (sync candidates)

| FD | Provider | SF Case | Origin | Sync |
|----|----------|---------|--------|------|
| — | — | — | — | **None** — no provider-aligned FD↔SF pairs in window |

### SF Federated COI Cases without FD counterpart

| SF Case | Provider (subject) | Created (UTC) | FD ticket |
|---------|-------------------|---------------|-----------|
| 00006048 | KAA Investments LLC | 2026-06-29 22:19 | **None found** |
| 00006053 | CECCO, Inc. | 2026-06-30 04:37 | **None found** |
| 00006015 | Superior Mechanical Services, Inc. | 2026-06-29 18:40 | **None found** |
| 00006016 | Angeles Plumbing, LLC | 2026-06-29 18:42 | **None found** |
| 00006077 | Storefronts and Entrances, Inc. | 2026-06-30 16:23 | **None found** |

COI tag search (all groups) returned 7 FD tickets in window; only #60160 carries a
Federated `Certificate Of Insurance - {Provider}` subject pattern.

---

## Federated sender collisions (downgraded — no provider match)

Prior scan incorrectly classified #60160 ↔ multiple SF COI Cases as `true_same_thread`
via shared `fedcerts-donotreply@fedins.com` + subject token overlap. Widened scan
downgrades these to `contact_collision` + `fedcerts_sender_collision`.

| FD | FD provider | SF Case | SF provider |
|----|-------------|---------|-------------|
| #60160 | Tri Star Transport LLC | 00006015 | Superior Mechanical |
| #60160 | Tri Star Transport LLC | 00006016 | Angeles Plumbing |
| #60160 | Tri Star Transport LLC | 00006048 | KAA Investments |
| #60160 | Tri Star Transport LLC | 00006053 | CECCO |
| #60160 | Tri Star Transport LLC | 00006077 | Storefronts and Entrances |

---

## Attachment sync results

**No live syncs executed.** Zero `true_same_thread` pairs with
`coi_provider_name_match`. Voicemail pairs (59559/59653/59717/59724) skipped per
prior completion. #60160 skipped — no confirmed SF Tri Star Case.

---

## FD #60160 — Tri Star Transport (deficient COI, aphelp misroute)

**Do not forward.** Document-only review per operator instruction.

| Field | Value |
|-------|-------|
| **Subject** | Certificate Of Insurance - Tri Star Transport LLC 662-298-0 Req 139~… |
| **Type** | COIs |
| **Status** | 4 (Resolved) |
| **Tags** | COI, risk-compliance-routed, spm-routed, coi-reviewed, **coi-deficient** |
| **Requester** | fedcerts-donotreply@fedins.com |
| **To (misroute)** | **aphelp@vixxo.com** (should be COI@vixxo.com intake) |
| **Support email** | vixxocomaphelp@vixxo-helpdesk.freshdesk.com |
| **Attachment** | EU01670.pdf (1 COI PDF) |
| **cf_sp** | Tri Star Transport LLC |
| **SF Case** | **None** — SOQL `Subject LIKE '%Tri Star%'` returned 0 records |

### Conversation timeline

1. **2026-06-30 12:04 UTC** — Internal note: COI review checklist; outcome **DOES NOT
   meet** Vixxo minimum requirements; tags `coi-deficient`; status set Resolved.
2. **2026-06-30 12:04 UTC** — Public reply (Vixxo Risk & Compliance deficiency letter)
   sent **from aphelp@vixxo.com** to fedcerts-donotreply@fedins.com (monitored noreply).
3. **2026-06-30 12:05 UTC** — Federated auto-reply bounce: address not monitored.

### Issues

1. **Mailbox misroute:** Inbound Federated cert delivered to **aphelp** queue instead
   of COI workflow (`COI@vixxo.com` / SPM COI path).
2. **Deficient COI in AP Help context:** Violates guardrail — deficient outcomes must
   stay in COI workflow, never AP Help routing.
3. **No SF dual-intake:** No matching SF Case for Tri Star; cannot bridge attachments.
4. **Reply delivery:** Deficiency notice sent to Federated noreply — SP/broker unlikely
   to receive actionable correction request via that path.

### Recommended remediation (operator)

1. **Fix intake routing** so Federated COI certs to COI@vixxo.com land in SPM COI
   queue, not aphelp.
2. **Do not re-open or forward to aphelp** — ticket is correctly Resolved/deficient
   for COI workflow; await SP resubmission (auto-reopen on reply).
3. **Optional:** Create SF Case for Tri Star if SF COI queue needs the record; then
   run attachment sync FD #60160 → new Case.
4. **Review** COI review automation `to_emails` / reply path for Federated noreply
   requesters — may need manual SP contact lookup for deficiency notices.

---

## Artifacts

| File | Purpose |
|------|---------|
| `.tmp/sf-cases-window-coi-20260630.json` | SF Case export (120 cases, Jun 29+) |
| `.tmp/fd-sf-duplicate-scan-coi-20260630.json` | Scan JSON |
| `.tmp/fd-sf-duplicate-report-coi-20260630.md` | This report |

## Commands run

```powershell
sf data query --query "SELECT ... FROM Case WHERE CreatedDate >= 2026-06-29T00:00:00Z ..." --target-org vixxo --json
python scripts/scan_duplicates.py --window-start 2026-06-29T00:00:00Z --sf-cache .tmp/sf-cases-window-coi-20260630.json --output .tmp/fd-sf-duplicate-scan-coi-20260630.json --report .tmp/fd-sf-duplicate-report-coi-20260630.md --include-coi --no-enrich
```

## Blockers

- **No FD tickets** for KAA / CECCO / Superior Mechanical / Angeles Plumbing /
  Storefronts — provider pairing and FD→SF sync cannot proceed for those SF Cases.
- **No SF Case** for Tri Star Transport — #60160 cannot be synced until SF record
  exists or operator confirms no SF intake expected.
