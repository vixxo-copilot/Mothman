# Angeles Plumbing — Consolidate onto SF Case #00005985

**Status:** Draft only — approve before executing.  
**Primary (keep):** SF **#00005985** (`500TS00000nmtkLYAQ`) — **New** ✓ open  
**Policy:** Single SF Case for all Angeles Plumbing Federated COI (`450-802-4`); close all other SF + FD intake.

---

## Consolidation map

| Source | Req | Type | Move to #5985 |
|--------|-----|------|----------------|
| SF #00005985 | 17 | EmailMessage (auto-reply) | Already on primary |
| SF #00005886 | 19 | EmailMessage (auto-reply) | Reparent email `02sTS00000lFFLVYA4` |
| SF #00005831 | 22 | EmailMessage + cert **EP15270** | Reparent `02sTS00000lCFg9YAG` + link file |
| SF #00006016 | 23 | EmailMessage + cert **ET19680** | Reparent `02sTS00000lSDnJYAW` + link file |
| FD #48695 | 17 | **E218920.pdf** + thread | Sync to SF Case |
| FD #49414 | 19 | **ER12480.pdf** + thread | Sync to SF Case |
| FD #49190 | 17 | Auto-reply thread | Sync note / close |
| FD #58276 | 17 | Auto-reply thread | Sync note / close |
| FD #58573 | 21 | Auto-reply thread | Sync note / close |

**After merge — close as duplicate:**

| Close | System |
|-------|--------|
| #00005886, #00005831, #00006016 | Salesforce |
| #48695, #49414, #49190, #58276, #58573 | Freshdesk |

---

## Step 1 — Prepare primary Case #00005985

| Field | Value |
|-------|-------|
| **Account** | Angeles Plumbing LLC (`001TS00000en7sdYAA`) |
| **Status** | Working |
| **Subject** (optional) | `Certificate Of Insurance - Angeles Plumbing, LLC 450-802-4 (Consolidated Federated COI)` |

**Description append:**
```
CONSOLIDATED CASE — 2026-07-01
Merged Angeles Plumbing Federated COI intake from SF Cases #00005886, #00005831, #00006016
and Freshdesk #48695, #49414, #49190, #58276, #58573.

Federated Req ids on this Case: 17, 19, 21, 22, 23.
Primary SF Case retained: #00005985.
Cross-ref: sp-fd-sf-duplicate-bridge / angeles-plumbing consolidation.
```

---

## Step 2 — Move SF email threads to #00005985

Re-parent `EmailMessage.ParentId` → `500TS00000nmtkLYAQ`:

| EmailMessage Id | From Case | Subject (abbrev) | HasAttachment |
|-----------------|-----------|------------------|---------------|
| `02sTS00000lFFLVYA4` | #00005886 | Req 19 auto-reply | No |
| `02sTS00000lCFg9YAG` | #00005831 | Req 22 cert | **Yes** |
| `02sTS00000lSDnJYAW` | #00006016 | Req 23 cert | **Yes** |
| `02sTS00000lRF4kYAG` | #00005985 | Req 17 auto-reply | No (already here) |

**SF CLI (after approval):**
```powershell
$primary = '500TS00000nmtkLYAQ'
foreach ($em in @('02sTS00000lFFLVYA4','02sTS00000lCFg9YAG','02sTS00000lSDnJYAW')) {
  & "$env:APPDATA\npm\sf.cmd" data update record --sobject EmailMessage --record-id $em --values "ParentId='$primary'" --target-org vixxo
}
```

If reparent is blocked by org rules, fallback: create **Completed Tasks** on #5985 with
Subject = original email subject, Description = `TextBody` + source Case number.

---

## Step 3 — Link cert files on SF Case #5985

Files currently on EmailMessages (also link to Case for Files tab):

| ContentDocumentId | Title | Source Req |
|-------------------|-------|------------|
| `069TS00000f5Xq9YAE` | EP15270 | 22 (#00005831) |
| `069TS00000fJbpAYAS` | ET19680 | 23 (#00006016) |

**SF CLI — ContentDocumentLink to Case:**
```powershell
$caseId = '500TS00000nmtkLYAQ'
foreach ($doc in @('069TS00000f5Xq9YAE','069TS00000fJbpAYAS')) {
  & "$env:APPDATA\npm\sf.cmd" data create record --sobject ContentDocumentLink --target-org vixxo --values "ContentDocumentId='$doc' LinkedEntityId='$caseId' ShareType='V' Visibility='AllUsers'"
}
```

---

## Step 4 — Sync Freshdesk documents + threads to #5985

Run **after** Step 1 (Case Id known). Dry-run first.

```bash
# Req 17 cert (critical — not on SF today)
python scripts/sync_attachments_to_sf.py \
  --fd-ticket-id 48695 \
  --sf-case-id 500TS00000nmtkLYAQ \
  --policy full \
  --dry-run

# Req 19 cert
python scripts/sync_attachments_to_sf.py \
  --fd-ticket-id 49414 \
  --sf-case-id 500TS00000nmtkLYAQ \
  --policy full \
  --dry-run
```

Remove `--dry-run` after review.

**FD thread notes → SF Tasks** (Completed, on #5985) — one per FD ticket if conversations not in email sync:

| Task Subject | Source FD | Notes |
|--------------|-----------|-------|
| `FD thread merge — #48695 Req 17` | #48695 | FW: cert forward; Waiting on Third Party history |
| `FD thread merge — #49414 Req 19` | #49414 | Closed; coi-blocked tags |
| `FD thread merge — #49190 Req 17 auto-reply` | #49190 | Duplicate auto-reply |
| `FD thread merge — #58276 Req 17 auto-reply` | #58276 | Duplicate auto-reply |
| `FD thread merge — #58573 Req 21 auto-reply` | #58573 | Auto-reply only |

**Task Description template:**
```
Merged from Freshdesk #{fd_id} into primary SF Case #00005985.
Original subject: {subject}
Status at merge: {status}
Action: FD ticket closed as duplicate; SF is system of record.
```

---

## Step 5 — SF Task (Completed) on #00005985 — consolidation record

**Subject:**
```
Angeles Plumbing COI consolidated — SF #00005985 primary
```

**Description:**
```
Consolidated all Angeles Plumbing, LLC Federated COI (450-802-4) onto this Case.

SF Cases merged (closed as duplicate):
  #00005886 (Req 19), #00005831 (Req 22), #00006016 (Req 23)

EmailMessages reparented: 02sTS00000lFFLVYA4, 02sTS00000lCFg9YAG, 02sTS00000lSDnJYAW
SF files linked: EP15270 (Req 22), ET19680 (Req 23)

FD tickets synced + closed:
  #48695 (Req 17, E218920.pdf), #49414 (Req 19, ER12480.pdf),
  #49190, #58276 (Req 17 dupes), #58573 (Req 21)

Account updated: Angeles Plumbing LLC.
Future Federated traffic for this SP → append to Case #00005985 only.
```

---

## Step 6 — Close duplicate SF Cases

| Case | Close reason |
|------|--------------|
| #00005886 | Merged into #00005985 — Req 19 email thread moved |
| #00005831 | Merged into #00005985 — Req 22 email + EP15270 moved |
| #00006016 | Merged into #00005985 — Req 23 email + ET19680 moved |

**Closure comment (each):**
```
Consolidated into primary Case #00005985 (Angeles Plumbing Federated COI).
Email thread and attachments moved. Do not reopen — append to #00005985.
```

---

## Step 7 — Close duplicate FD tickets (draft notes — approve before posting)

**#48695:**
```
Consolidated to SF Case #00005985. Cert E218920.pdf synced to SF. FD duplicate closed.
```

**#49414:**
```
Consolidated to SF Case #00005985. Cert ER12480.pdf synced to SF. FD duplicate closed.
```

**#49190, #58276, #58573:**
```
Duplicate — merged to SF Case #00005985 (Angeles Plumbing consolidated COI).
```

---

## Execution order

1. Update #5985 Account, Status, Description  
2. Reparent EmailMessages (or Task fallback)  
3. ContentDocumentLink certs to Case  
4. FD attachment sync (48695, 49414) — dry-run → live  
5. FD thread Tasks on #5985  
6. Consolidation Task on #5985  
7. Close SF #5886, #5831, #6016  
8. FD internal notes + close FD tickets  

---

## Expected file inventory on #5985 after merge

| File | Source |
|------|--------|
| EP15270 | SF Req 22 email |
| ET19680 | SF Req 23 email |
| E218920.pdf | FD #48695 |
| ER12480.pdf | FD #49414 |

Verify with:
```sql
SELECT ContentDocument.Title, ContentDocument.ContentSize
FROM ContentDocumentLink
WHERE LinkedEntityId = '500TS00000nmtkLYAQ'
ORDER BY ContentDocument.Title
```

---

## Checklist

- [ ] #00005985 still **New/Working** before starting
- [ ] Account = Angeles Plumbing LLC
- [ ] 3 EmailMessages reparented
- [ ] 2 SF certs + 2 FD certs on Case
- [ ] 5 FD thread Tasks (or equivalent)
- [ ] 1 consolidation Task
- [ ] 3 SF Cases closed
- [ ] 5 FD tickets closed

**Say "execute Angeles consolidation" to run SF steps.** FD closes require separate approval.
