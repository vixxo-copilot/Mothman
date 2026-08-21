# Salesforce Notes

Add context to **Cases** and **Leads** when vetting finds a match. For
SF-primary queues (ksonboarding, COI, spm), the **queue Case Task is the primary
deliverable**. Freshdesk internal notes are secondary (AP Help only, or when a
Freshdesk mirror exists).

This skill does not create Leads or Cases.

## Case Account update (Known SP)

When vetting resolves **Known SP** posture with a Salesforce **Account** Id,
update the queue Case so `AccountId` matches the provider — not just the Task
note.

**Update when:**

- Posture starts with `Known SP`
- Resolved Account has `Service_Provider_Number__c` (or Gateway SP # matches)
- Case `AccountId` is blank, a placeholder, or wrong

**Do not update when:**

- Posture is `Unknown`, `Prospect`, or `Open SF Case` only
- No Account Id resolved from Gateway + Salesforce search
- Case already linked to the correct Account

**Placeholder accounts to replace:**

| Account | Id |
| --- | --- |
| Vixxo Corporation | `001TS00000CLPi9YAH` |
| Service Provider Support Shell Account | `001TS00000mWdvSYAS` |

### CLI — update Case AccountId

```bash
sf data update record --sobject Case \
  --record-id {CaseId} \
  --values "AccountId='{ResolvedAccountId}'"
```

Then post a short audit Task (same pattern as vetting Task):

```bash
sf data create record --sobject Task \
  --values "Subject='SP Inbound Vetting - Case {CaseNumber} Account updated' \
Description='Set Case Account to {SP#} — {AccountName}. Posture: Known SP.' \
WhatId='{CaseId}' Status='Completed' Priority='Normal'"
```

Helper: `scripts/sf_case_account.py` (`update_case_account`, `should_update_case_account`).

## Read path

Use Salesforce MCP `run_soql_query` (see [company-vetting.md](company-vetting.md)
and [queues.md](queues.md)).

## Write path

The Salesforce MCP is read-only for notes. Use Salesforce CLI when available:

### Task on a Case (SF-primary — required for queue Cases)

```bash
sf data create record --sobject Task \
  --values "Subject='SP Inbound Vetting — Case {CaseNumber}' \
Description='{summary + posture + Gateway SP # + routing recommendation}' \
WhatId='{CaseId}' \
Status='Completed' \
Priority='Normal'"
```

When routing table recommends AP Help forward, include in Description:

```text
Recommended routing (requires operator approval): Forward payment/AP portion to
aphelp@vixxo.com. Draft only — do not send until approved.
```

### Task on a Lead

```bash
sf data create record --sobject Task \
  --values "Subject='SP Inbound Vetting — Lead {LeadName}' \
Description='{summary + posture + Gateway SP # if known + SF Case link if any}' \
WhoId='{LeadId}' \
Status='Completed' \
Priority='Normal'"
```

When both Lead and Case match, post on **both** unless the user narrows scope.

### Task on a Case (AP Help — when FD ticket links to SF Case)

```bash
sf data create record --sobject Task \
  --values "Subject='SP Inbound Vetting — FD #{ticket_id}' \
Description='{summary + posture + Gateway SP # if known + Freshdesk link}' \
WhatId='{CaseId}' \
Status='Completed' \
Priority='Normal'"
```

### Task body content

Include:

- Queue key (`ksonboarding` / `coi` / `spm` / `aphelp`)
- SF Case Number or Freshdesk ticket id
- Entity posture (`Known SP`, `Prospect`, etc.)
- Gateway SP number + name when known
- One-line summary of the inbound ask (COI, onboarding, payment, etc.)
- **Routing:** Stay in SF | Recommend forward to AP Help (draft)
- ISO processing timestamp
- **Case Account update:** {updated AccountId + name | skipped — reason}

### Fallback when CLI unavailable

1. Record the intended note text in the vetting packet under **SF notes — pending
   manual entry**.
2. For AP Help, also record in Freshdesk internal note under **Salesforce notes
   — pending manual entry**.
3. Mark packet **Status: partial** in the batch summary.
4. Do not block other enrichment steps for SF write failure.

## Chatter alternative

If Task create fails and the org uses Chatter on Leads/Cases:

```bash
sf data create record --sobject FeedItem \
  --values "ParentId='{LeadOrCaseId}' Body='{short summary}'"
```

Record which object type was used in the triage packet.
