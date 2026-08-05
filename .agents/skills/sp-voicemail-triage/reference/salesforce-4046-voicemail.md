# Salesforce — 8x8 extension 4046 voicemails

**Primary SPM voicemail intake** for `sp-voicemail-triage`. Replaces the retired
Freshdesk **KSOnboarding** (`ksonboarding@vixxo.com`) mailbox.

8x8 leaves Vendor Relations voicemails on **extension 4046**. Notifications look
like:

```
Your extension 4046 just received a new voicemail.
Tap the attachment to listen to your voicemail.
```

Subject pattern (Email-to-Case → Salesforce Case):

```
New voicemail from {CALLER} via VENDOR RELATIONS
```

Body metadata includes caller CID, callback phone, received time, and duration.
**Spoken content is only in the `.wav` / `.mp3` attachment** — never classify
from the notification body alone.

## Discovery (SOQL)

Open Cases owned for SPM / Crystal queue with Vendor Relations voicemail
subjects. Prefer subject filters (Case `Description` is not filterable in SOQL):

```sql
SELECT Id, CaseNumber, Subject, Status, Owner.Name, CreatedDate
FROM Case
WHERE IsClosed = false
  AND Subject LIKE '%New voicemail%'
  AND Subject LIKE '%VENDOR RELATIONS%'
ORDER BY CreatedDate DESC
LIMIT 50
```

Optional owner scope when Crystal owns the Email-to-Case queue:

```sql
… AND Owner.Name = 'Crystal Gagner'
```

**In scope:** subject includes `New voicemail` **and** `VENDOR RELATIONS`
(case-insensitive match on those phrases).

**Out of scope for this source:**

- Amazon Connect Cases with subject `Vixxo Voicemail` (different intake —
  triage only when {{employee_name}} explicitly asks for Connect backlog)
- Freshdesk KSOnboarding tickets — **do not search or write** that mailbox
- QSIAP AP voicemails — still Freshdesk; see [qsiap-voicemail.md](qsiap-voicemail.md)
- Outlook **VM** folder — still M365; dedupe against SF Case by callback phone
  + received window (see Dual intake below)

## Acquire audio

1. `EmailMessage` for the Case (`ParentId = CaseId`, `HasAttachment = true`).
2. `ContentDocumentLink` on the **EmailMessage** Id (not always on the Case).
3. Download `ContentVersion` `VersionData` for the `.wav` / `.mp3`
   (`sf api request rest …/VersionData -S <file>`).
4. Transcribe with **faster-whisper** (or agent STT). Failed STT → leave Case
   unchanged; report failure.

## Phase 2 (SF-native — no Freshdesk)

There is **no Freshdesk ticket** for 4046 intake. Do **not** create FD tickets.

| Step | Action |
| --- | --- |
| Triage packet | Source = `SF Case {CaseNumber}` |
| Billing / Payment | Close Case as Duplicate (`Reason='Existing problem'`, `Not_Filled_Reason__c='Duplicate'`); **no** Completed Task; note AP owns (QSIAP/aphelp) |
| Short / foul / minimal | Completed Task documenting skip + close Case as Duplicate |
| All other categories | Completed **Task** on the Case (`Status='Completed'`); forward email to route recipients when needed (M365); leave Case open/Working for callback |
| Account link | Set `AccountId` when SP Account match is confident |

Task body must include category, caller, company, callback, route, posture,
transcript source, and verbatim transcript. Avoid apostrophes in `sf --values`
strings (CLI parsing is fragile) — strip or rephrase.

## Dual intake (Outlook VM ↔ SF Case)

The same 8x8 message may land in Outlook **VM** and as an SF Case. Triage
**once**:

1. Prefer the open **SF Case** as the system of record when both exist.
2. Skip re-forwarding from Outlook if a Completed `SP Voicemail Triage` Task
   already exists on the matching Case.
3. Link Outlook message id in the Task Description when known.

## Dedupe before creating a *new* Case

4046 intake **already has** a Case from Email-to-Case. Do not create a second
Case for the same voicemail. Create Cases only for Outlook-only items with no
SF match (see [salesforce-notes.md](salesforce-notes.md)).

## Retired path

| Former | Status |
| --- | --- |
| Freshdesk `type:'KSOnboarding'` + `New voicemail` | **Retired** — do not batch-scan |
| `scripts/batch_process_freshdesk.py` | Legacy KSOnboarding REST helper — do not use for default runs |
| Sibling `sp-voicemail-triage-fast` KSOnboarding cron | Out of scope for 4046; use agent/SF path instead |
