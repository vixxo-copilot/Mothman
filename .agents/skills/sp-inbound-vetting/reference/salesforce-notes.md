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

## SF match review guardrail (live batch)

Before creating a Salesforce **Task**, confirm the Lead or Case match is
trustworthy. **Do not auto-post Tasks** when:

- `match_type` is `fuzzy`, or
- `confidence` is `Medium` or `Low`

**Exception — Lead email exact:** when requester email equals Lead `Email`
(`match_kind: email`), auto-post the Lead Task even if other signals are weak.

**Exact matches that still auto-post:**

| Object | Auto-post when |
| --- | --- |
| Lead | `match_type: exact` and `confidence: High`, or exact email match |
| Case | `match_type: exact` and `confidence: High` (e.g. `ContactEmail` hit) |

**When skipped — flag for review instead:**

1. Add Freshdesk tag `sf-match-review` (merge with existing tags).
2. In the internal note, include **SF match — review required** with Lead/Case
   Id, `match_score`, `match_type`, and why the Task was skipped.
3. Operator confirms the correct SF record, then posts the Task manually or
   re-runs live after correcting intake entities.

Known SP (Gateway exact KS/SR/email) does **not** require an SF Task unless a
matched Lead also qualifies for auto-post under the rules above.

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
