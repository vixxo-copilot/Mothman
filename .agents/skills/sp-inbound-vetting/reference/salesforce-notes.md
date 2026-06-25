# Salesforce Notes

Add context to **Cases** and **Leads** when vetting finds a match. For
SF-primary queues (ksonboarding, COI, spm), the **queue Case Task is the primary
deliverable**. Freshdesk internal notes are secondary (AP Help only, or when a
Freshdesk mirror exists).

This skill does not create Leads or Cases.

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
