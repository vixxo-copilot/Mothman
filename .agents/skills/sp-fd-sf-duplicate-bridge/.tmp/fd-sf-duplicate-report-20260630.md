# Freshdesk ↔ Salesforce Duplicate Scan
**Skill:** `sp-fd-sf-duplicate-bridge`  
**Window:** 2026-06-26 00:00 UTC → 2026-06-30 ~5:46 PM UTC  
**Generated:** 2026-06-30

## Summary
| Metric | Count |
|--------|------:|
| FD inbound (SPM group) | 698 |
| SF Cases | 197 |
| Duplicate pairs | **23** |
| True same-thread | **7** |
| Likely same-thread | **3** |
| Contact collision | **13** |

**Answer:** Yes — duplicates exist. Dominant true-duplicate pattern is **voicemail dual-intake** (4 pairs): FD holds `.wav`, SF Case created by `sp-voicemail-triage` with `Freshdesk #{id}` in Description. **No SF ContentDocumentLink files** on voicemail Cases checked — attachment gap on SF side.

---

## True same-thread pairs (action candidates)

| FD | SF Case | Origin | Pattern | FD attach | SF files |
|----|---------|--------|---------|-----------|----------|
| [#59559](https://vixxo-helpdesk.freshdesk.com/a/tickets/59559) | 00005919 | FD first | Voicemail — Andrea Spicer | 1 `.wav` | EmailMessage only |
| [#59653](https://vixxo-helpdesk.freshdesk.com/a/tickets/59653) | 00005932 | FD first | Voicemail — Roberts Plumbing | 1 `.wav` | EmailMessage only |
| [#59717](https://vixxo-helpdesk.freshdesk.com/a/tickets/59717) | 00005946 | FD first | Voicemail — wireless caller | 1 `.wav` | EmailMessage only |
| [#59724](https://vixxo-helpdesk.freshdesk.com/a/tickets/59724) | 00005953 | FD first | Voicemail — Electronic Recy | 1 `.wav` | EmailMessage only |
| [#60160](https://vixxo-helpdesk.freshdesk.com/a/tickets/60160) | 00006077 | FD first | COI — Tri Star Transport | 1 COI PDF | Triage Case |
| [#60160](https://vixxo-helpdesk.freshdesk.com/a/tickets/60160) | 00006048 | SF first | COI batch sender collision | 1 COI PDF | — |
| [#60160](https://vixxo-helpdesk.freshdesk.com/a/tickets/60160) | 00006053 | SF first | COI batch sender collision | 1 COI PDF | — |

**Recommended sync (voicemail pairs only):** Run attachment sync for FD → SF on Cases **00005919, 00005932, 00005946, 00005953** if SF operators need the `.wav` on the Case record:

```bash
python scripts/sync_attachments_to_sf.py --fd-ticket-id {id} --sf-case-number {number} --policy ks-onboarding-reply --dry-run
```

**60160 ↔ multiple SF COI Cases:** Federated Insurance batch-sender pattern — treat **00006077** as the likely true pair (FD-first + cross-ref); others are contact-level COI duplicates.

---

## Likely same-thread (review before sync)

| FD | SF Case | Notes |
|----|---------|-------|
| #60160 | 00005915, 00006015, 00006016 | Same Federated noreply sender; different provider names in subject |

---

## Contact collisions (report only — no auto-sync)

Notable clusters:
- **#59827 / #59986** ↔ SF **00006032, 00006033** — Enterprise/Encore WO emails vs unrelated SF Cases
- **#60082 / #60278** ↔ SF **00006068** — past-due invoice campaign vs NCRI invoice
- **#60088 / #60142 / #60465 / #60466** ↔ SF **00005997** — NEC Building past-due thread vs other senders on same Case email

---

## Artifacts
- Scan JSON: `.tmp/fd-sf-duplicate-scan-20260629.json`
- SF cache: `.tmp/sf-cases-window-20260629.json`

## Next steps (operator)
1. **Voicemail gaps:** Sync `.wav` from FD to SF for the 4 voicemail pairs if SF team needs files on Case.
2. **COI #60160:** Confirm which SF Case owns Tri Star Transport COI; close/merge duplicate SF Cases if applicable.
3. **Contact collisions:** No action unless manual pairing requested.
