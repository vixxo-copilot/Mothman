# Attachment Sync — Freshdesk → Salesforce Case

## Prerequisites

- Paired FD ticket id + SF Case id (detection or operator-supplied)
- Salesforce CLI (`sf`) authenticated to org alias `vixxo` (default target org)
- Freshdesk credentials (`FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY`)

Resolve SF Case id when only Case Number is known:

```sql
SELECT Id, CaseNumber FROM Case WHERE CaseNumber = '00005739'
```

## Policies

| Policy | Includes | Excludes |
| --- | --- | --- |
| **`ks-onboarding-reply`** (default) | Original ticket attachments (onboarding packet) + attachments on the **latest incoming** (requester) conversation | All **outbound** conversation attachments (Vixxo templates: blank provisional form, LOS checklist template, Sample COI) |
| **`full`** | Every attachment on ticket + all conversations (deduped by attachment id) | Nothing |
| **`latest-reply-only`** | Latest incoming conversation attachments only | Ticket-level + outbound |

Dedupe by Freshdesk attachment `id` before upload. Skip files already on the Case when title + size match an existing `ContentDocumentLink`.

## CLI upload (per file)

```powershell
& "$env:APPDATA\npm\sf.cmd" data create file `
  --file "{local_path}" `
  --parent-id "{CaseId}" `
  --title "{original_filename}" `
  --target-org vixxo
```

## CLI remove (wrong upload)

Delete the `ContentDocument` (removes from Case Files):

```powershell
& "$env:APPDATA\npm\sf.cmd" data delete record `
  --sobject ContentDocument `
  --record-id "{ContentDocumentId}" `
  --target-org vixxo
```

## Scripted sync

```bash
python scripts/sync_attachments_to_sf.py \
  --fd-ticket-id 57142 \
  --sf-case-number 00005739 \
  --policy ks-onboarding-reply \
  --include-original-packet
```

Flags:

- `--dry-run` — list selected files only; no SF writes
- `--skip-existing` — skip when same title already linked to Case
- `--sf-case-id` — use instead of `--sf-case-number`

Download step reuses `vixxo-coi-review/scripts/fetch_coi_attachments.py` (ticket + conversations → local dir + manifest).

## Post-sync documentation (recommended)

After a successful sync, post a **completed Task** on the SF Case:

```bash
sf data create record --sobject Task \
  --values "Subject='FD attachment sync — Freshdesk #{fd_id}' \
Description='Synced {n} files from Freshdesk #{fd_id} per ks-onboarding-reply policy.\nFiles: {comma-separated titles}' \
WhatId='{CaseId}' Status='Completed' Priority='Normal'"
```

Optional Freshdesk internal note when the FD ticket remains open:

```text
SF attachment sync — Case #{case_number} ({n} files). Policy: ks-onboarding-reply.
```

Outbound notes/forwards require operator approval per workspace guardrails.

## Verify

```sql
SELECT ContentDocument.Title, ContentDocument.ContentSize
FROM ContentDocumentLink
WHERE LinkedEntityId = '{CaseId}'
ORDER BY ContentDocument.Title
```
