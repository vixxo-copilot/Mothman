# Examples — FD ↔ SF Duplicate Bridge

## Example 1 — KS onboarding mirror (ProSite)

**Operator ask:** Forward attachments from Freshdesk **57142** to Salesforce Case **#00005739**.

| System | Record |
| --- | --- |
| Freshdesk | [#57142](https://vixxo-helpdesk.freshdesk.com/a/tickets/57142) — Onboarding - ProSite Facilities & Paving Group |
| Salesforce | Case **00005739** — Prospect Account Profile Creation - ProSite Facilities & Paving Group |

**Detection:** Manual pair (operator-supplied). Requester `mager@prositefg.com`; company in `cf_sp`.

**Sync policy:** `ks-onboarding-reply` with `--include-original-packet`

**Files retained on SF Case (7):**

| File | Source |
| --- | --- |
| ProSite Facilities & Paving Group.pdf | FD ticket (original packet) |
| ProSite LOS checklist.pdf | Latest requester reply |
| Vixxo US Construction Provisional SP Request Form.pdf | Latest requester reply (completed) |
| 2026 2027 Vixxo Corporation1.pdf | Latest requester reply (COI) |
| ENDORSEMENTS 1.pdf | Latest requester reply |
| ENDORSEMENTS WORK COMP.pdf | Latest requester reply |
| ENDOESEMENT AUTOS.pdf | Latest requester reply |

**Excluded:** Crystal's outbound templates (blank provisional form, LOS checklist template, Sample COI 2026).

---

## Example 2 — Voicemail dual-intake

**Detection:** SF Case Description contains `Freshdesk #58752`; subjects match; FD created ~3 min before SF.

| Freshdesk | Salesforce |
| --- | --- |
| #58752 — New voicemail from … | Case 00005784 — Fwd: New voicemail … |

**Attachment sync:** Usually **not needed** — triage forward already attaches `.wav` to SF EmailMessage. Verify with:

```sql
SELECT Id, HasAttachment, Subject FROM EmailMessage
WHERE ParentId = '{CaseId}' ORDER BY CreatedDate DESC
```

If FD holds the only `.wav`, upload to Case with `--policy full` or manual single-file upload.

---

## Example 3 — Contact collision (do not sync)

**FD #59058** (Re: PAST DUE INVOICES) ↔ **SF 00005869** (Fw: VixxoLink) — same requester email, subject similarity 0.00.

**Action:** Report as `contact_collision` only. Do **not** sync attachments unless operator confirms same work item.

---

## Example 4 — Batch window scan

**Operator ask:** "Scan FD/SF duplicates since yesterday."

1. MCP SOQL — export SF Cases to `.tmp/sf-cases-window-{date}.json`
2. Run:

```bash
python scripts/scan_duplicates.py \
  --window-start 2026-06-25T00:00:00Z \
  --sf-cache .tmp/sf-cases-window-20260626.json \
  --output .tmp/fd-sf-duplicate-scan-20260626.json
```

3. Present summary table: pair count, true same-thread vs contact collision, top pairs with links.
