# Salesforce Notes

Add context to existing **Leads** and **Cases** when vetting finds a match.
This skill does not create Leads or Cases.

## Read path

Use Salesforce MCP `run_soql_query` (see [company-vetting.md](company-vetting.md)).

## Write path

The Salesforce MCP is read-only for notes. Use Salesforce CLI when available:

### Task on a Lead

```bash
sf data create record --sobject Task \
  --values "Subject='Freshdesk inbound vetting — FD #{ticket_id}' \
Description='{summary + posture + Freshdesk link}' \
WhoId='{LeadId}' \
Status='Completed' \
Priority='Normal'"
```

### Task on a Case

```bash
sf data create record --sobject Task \
  --values "Subject='Freshdesk inbound vetting — FD #{ticket_id}' \
Description='{summary + posture + Gateway SP # if known}' \
WhatId='{CaseId}' \
Status='Completed' \
Priority='Normal'"
```

When both Lead and Case match, post on **both** unless the user narrows scope.

### Task body content

Include:

- Freshdesk ticket id and inbox (`aphelp` / `ksonboarding`)
- Entity posture (`Known SP`, `Prospect`, etc.)
- Gateway SP number + name when known
- One-line summary of the inbound ask (invoice, onboarding, payment, etc.)
- ISO processing timestamp

### Fallback when CLI unavailable

1. Record the intended note text in the Freshdesk internal note under
   **Salesforce notes — pending manual entry**.
2. Mark the packet **Status: partial** in the batch summary.
3. Do not block Freshdesk note or `cf_sp` update for SF write failure.

## Chatter alternative

If Task create fails and the org uses Chatter on Leads/Cases, try:

```bash
sf data create record --sobject FeedItem \
  --values "ParentId='{LeadOrCaseId}' Body='{short summary}'"
```

Record which object type was used in the triage packet.
