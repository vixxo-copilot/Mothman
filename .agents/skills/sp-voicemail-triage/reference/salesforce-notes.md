# Salesforce — Voicemail Triage

Salesforce is part of **every** voicemail triage run (except explicit
`--skip-vetting` / **`sp-voicemail-triage-fast`**). Use Salesforce MCP for
**read**; use Salesforce CLI for **Task** (and Case) **writes** when Phase 2
runs.

Sibling reference: [sp-inbound-vetting/reference/salesforce-notes.md](../../sp-inbound-vetting/reference/salesforce-notes.md)
(queue Case Tasks). This file covers **voicemail-specific** SF behavior.

## MCP tools

| Step | Tool | Notes |
| --- | --- | --- |
| Resolve org | `get_username` | Run once per session |
| SOQL | `run_soql_query` | Lead, Case, Account, Contact searches — see [company-vetting.md](company-vetting.md) |

The Salesforce MCP is **read-only** for record creation. Use `sf data create
record` for Tasks and Cases.

## Read path (Phase 1 — every item)

Run **in parallel** with Gateway vetting after company, caller, and callback
# are extracted from the **audio transcript**:

1. **Lead** — company + contact name + callback phone (onboarding / prospect)
2. **Case** — callback phone, company, caller name; **Freshdesk id** when present
3. **Account** — `Type = 'Service Provider'` when Gateway SP # is unknown but
   company name is confident
4. **Contact** — callback phone or email when known

Record all hits in the triage packet vetting table and **Reference IDs**.

### Freshdesk dedupe search (required when FD ticket exists)

Before creating a new Salesforce Case, search for an existing Case created by
prior triage:

```sql
SELECT Id, CaseNumber, Subject, Status, Description, CreatedDate
FROM Case
WHERE Description LIKE '%Freshdesk #{ticket_id}%'
   OR Subject LIKE '%Freshdesk #{ticket_id}%'
ORDER BY CreatedDate DESC
LIMIT 5
```

If a match exists, **do not create a duplicate Case** — post the voicemail
Task on the existing Case and reference `CaseNumber` in the Freshdesk internal
note.

### Outlook-only dedupe (no Freshdesk ticket)

Search by callback phone + received date window when no FD id exists:

```sql
SELECT Id, CaseNumber, Subject, Status, Description, CreatedDate
FROM Case
WHERE Description LIKE '%{last10_digits}%'
  AND CreatedDate = LAST_N_DAYS:7
ORDER BY CreatedDate DESC
LIMIT 5
```

## Write path (Phase 2)

**Write order (Salesforce slice):** after Freshdesk internal note + email
forward (when applicable):

1. **Task on matched Lead** (onboarding branch or Lead hit)
2. **Task on matched Case** OR **create Case** then Task (see below)
3. Record SF ids + write status in Freshdesk internal note

### Task on a Lead (onboarding / prospect)

```bash
sf data create record --sobject Task \
  --values "Subject='SP Voicemail Triage — Lead {Company}' \
Description='Freshdesk #{ticket_id or n/a}\nCategory: {category}\nCallback: {phone}\nPosture: {entity posture}\n\n{transcript}' \
WhoId='{LeadId}' \
Status='Completed' \
Priority='Normal'"
```

### Task on an existing Case

```bash
sf data create record --sobject Task \
  --values "Subject='SP Voicemail Triage — Case {CaseNumber}' \
Description='Freshdesk #{ticket_id or n/a}\nCategory: {category}\nRoute: {forward recipients}\nPosture: {entity posture}\nReview for {{employee_name}}: {Yes/No}\n\n{transcript}' \
WhatId='{CaseId}' \
Status='Completed' \
Priority='Normal'"
```

### Create Case (when no open Case matches)

Create only when dedupe search returns **no** matching Case and category
warrants SF queue ownership. Map category → queue:

| Category | SF queue (expected) | Queue key |
| --- | --- | --- |
| Coverage / Onboarding | KS Onboarding | `ksonboarding` |
| COI / Compliance | COI | `coi` |
| Sourcing / Account Team, VixxoLink, Technical, General | Service Provider Management | `spm` |
| Billing / Payment (AP forward path) | Usually **no new Case** — document on FD only; optional Task on open onboarding Case if Lead/Case exists | — |

Resolve queue OwnerId via Group SOQL (see
[sp-inbound-vetting/reference/queues.md](../../sp-inbound-vetting/reference/queues.md)
queue discovery).

```bash
sf data create record --sobject Case \
  --values "Subject='{voicemail subject or category summary}' \
Description='SP Voicemail triage\nFreshdesk #{ticket_id}\nCategory: {category}\nCaller: {caller}\nCompany: {company}\nCallback: {phone}\nRoute: {recipients}\n\n{transcript}' \
Origin='Phone' \
Status='New' \
OwnerId='{QUEUE_ID}' \
SuppliedPhone='{callback_phone}'"
```

Then post the **Task** on the new Case Id.

**Case Description must include** `Freshdesk #{ticket_id}` when a Freshdesk
ticket exists — this is the cross-system dedupe key.

### Chatter fallback

If Task create fails:

```bash
sf data create record --sobject FeedItem \
  --values "ParentId='{LeadOrCaseId}' Body='SP Voicemail Triage — {summary}'"
```

Record success or failure in the Freshdesk internal note **Salesforce notes**
section.

## Triage packet — Salesforce fields

Include in every packet (agent runs):

| Field | Value |
| --- | --- |
| **SF Lead** | {Id — Status — Company} or None |
| **SF Case** | {CaseNumber — Status} or None |
| **SF Account** | {Id — SP # if known} or None |
| **SF Case created** | Yes / No / Skipped — {reason} |
| **SF Lead Task** | posted / failed / N/A |
| **SF Case Task** | posted / failed / N/A |

## When SF writes are skipped

| Condition | SF action |
| --- | --- |
| `--skip-vetting` / fast skill | No SF reads or writes |
| No-forward branch (foul language, &lt;10s, minimal speech) | Optional Task on open Case only if one already exists; do **not** create Case |
| Dry-run | SOQL allowed; no CLI writes |
| CLI unavailable | Record **SF notes — pending manual entry** in FD internal note; continue FD forward + resolve |

## Dual-intake awareness

Voicemail often exists in **both** Freshdesk (8x8 notification + `.wav`) and
Salesforce (Case from triage forward or Email-to-Case). Always:

1. Search SF before creating Case
2. Link FD `#` in Case Description / Task body
3. Note the paired id in the internal note (**SF Case:** 0000xxxx ↔ **FD:** #nnnnn)

See **`sp-fd-sf-duplicate-bridge`** ([SKILL.md](../../sp-fd-sf-duplicate-bridge/SKILL.md),
[examples.md](../../sp-fd-sf-duplicate-bridge/reference/examples.md)) for voicemail
dual-intake detection, batch scan, and FD → SF attachment sync.
