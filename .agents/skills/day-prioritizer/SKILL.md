---
name: day-prioritizer
description: >-
  Builds a unified daily work plan from Microsoft 365 inbox and calendar,
  open Freshdesk tickets assigned to {{employee_name}}, and open Salesforce
  Cases and Tasks. Use when the user asks to prioritize their day, check email
  and tickets, plan the workday, or decide what to work on first.
---

# Day Prioritizer

Work-only daily planning for {{employee_name}}. Pulls signals from **Outlook**,
**Freshdesk**, and **Salesforce**, then recommends a realistic priority stack
and focus blocks around today's calendar.

## When to use

- "Prioritize my day" / "what should I work on today"
- "Check my email, tickets, and calendar"
- "Day plan" / "daily prioritization" / "start my day"
- End-of-morning replan after meetings shift

**Related skills (do not duplicate):**

| Skill | Use instead when |
| --- | --- |
| `morning-brief` | Calendar + inbox only; Linear/Teams emphasis |
| `email-triage` | Deep inbox reply batching and archive workflow |
| `sp-inbound-vetting` | Queue vetting for aphelp/ksonboarding/invoice concerns |
| `daily-briefing` | Linear + Teams delivery-risk briefing |

## Output format

Return in this order. Keep sections scannable; no wall-of-text.

1. **Today at a glance** — meeting count, first/last meeting, conflicts,
   tentative RSVPs, prep gaps before external meetings
2. **Recommended stack** — ordered P0 → P3 items with one-line rationale each
3. **By surface** — compact counts + top items for Email / Freshdesk / Salesforce
4. **Cross-links** — same issue appearing in mail + FD # or SF Case #
5. **Focus blocks** — 2–4 calendar gaps with suggested work (duration-aware)
6. **First moves** — 3 concrete next actions {{employee_name}} can start now
7. **Defer / skip** — noise, FYI-only mail, waiting-on-others tickets

After the plan, offer: "Want me to deep-dive any item, draft a reply, or open
a ticket thread?"

## Workflow

### 0. Scope and timezone

- Default timezone: `America/Denver` unless {{employee_name}} specifies another.
- "Today" = local calendar day through end of business.
- Read `memory/me/identity.md` for work email when resolving Salesforce User.

### 1. Authenticate (before any pull)

Run in parallel where possible; stop and report auth gaps before synthesizing.

| System | Check |
| --- | --- |
| Microsoft 365 | `verify-login`; if needed `login` + device code, then re-verify |
| Freshdesk | `view_current_agent` — capture agent `id`, `name`, `email` |
| Salesforce | `get_username` with `defaultTargetOrg: true`; then resolve User Id (step 4) |

If a system is unavailable, note it under **Defer / skip** and continue with
the rest. Do not invent ticket or case data.

### 2. Calendar (Microsoft 365)

Use `get-calendar-view`:

- `startDateTime`: start of today (local)
- `endDateTime`: end of today + 1 day
- `orderby`: `start/dateTime asc`
- `select`: `subject,start,end,location,isOnlineMeeting,onlineMeeting,organizer,showAs,responseStatus`
- `top`: 20
- `timezone`: user's local timezone

Paginate via `@odata.nextLink` until today's events are complete.

Flag: back-to-back blocks, external meetings, tentative invites, meetings in
the next 90 minutes needing prep.

### 3. Inbox (Microsoft 365)

Use `list-mail-folder-messages` with `mailFolderId: inbox`.

**Pass A — unread actionable**

- `filter`: `isRead eq false`
- `orderby`: `receivedDateTime desc`
- `select`: `id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,importance,conversationId,flag`
- `top`: 25

**Pass B — flagged / high importance (read or unread)**

- Separate call with `filter`: `flag/flagStatus eq 'flagged' or importance eq 'high'`
- `count`: true if the tool requires it for `flag/flagStatus`

Do **not** combine `$search` and `$filter` on one request.

Classify each surfaced message: **Ask** / **Decision** / **FYI**.

Deprioritize (FYI or skip): GitHub/Cursor onboarding, Meraki WiFi, Teams
"trying to reach you" nudges, marketing, automated reports with no ask.

Extract ticket/case references from subject/body: `Freshdesk #`, `FD-`, `Case
`, `CaseNumber`, `#51234` patterns.

### 4. Freshdesk — open assigned tickets

1. `view_current_agent` → `agent_id`
2. `search_tickets` with query (paginate all pages):

```
agent_id:{agent_id} AND (status:2 OR status:3)
```

Open = status 2; Pending = status 3. Include both unless user asks open-only.

For the top 10 by urgency (priority desc, then oldest `due_by`), optionally
call `view_ticket_summary` when subject alone is insufficient.

Capture per ticket: `#id`, subject, status, priority, type, tags, `due_by`,
`fr_due_by`, `updated_at`, SP custom field if present.

See [reference/queries.md](reference/queries.md) for priority labels and SLA
signals.

### 5. Salesforce — open Cases and Tasks

Resolve org username via `get_username` (`defaultTargetOrg: true`).

Resolve User Id:

```sql
SELECT Id, Name, Email FROM User WHERE Email = '{work_email}' LIMIT 1
```

Use `run_soql_query` with workspace directory path and resolved username.

**Open Cases owned by user:**

```sql
SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate,
       LastModifiedDate, ContactEmail, Origin
FROM Case
WHERE OwnerId = '{userId}' AND IsClosed = false
ORDER BY Priority DESC, LastModifiedDate DESC
LIMIT 25
```

**Open Tasks owned by user:**

```sql
SELECT Id, Subject, Status, ActivityDate, Priority, WhatId,
       LastModifiedDate, Description
FROM Task
WHERE OwnerId = '{userId}' AND IsClosed = false
ORDER BY ActivityDate ASC NULLS LAST, Priority DESC
LIMIT 15
```

If User lookup fails, report the blocker; do not guess OwnerId.

### 6. Normalize and dedupe

Build a unified item list. Each item needs:

| Field | Source |
| --- | --- |
| `id` | Graph message id / FD # / SF Case or Task id |
| `surface` | email / freshdesk / salesforce |
| `title` | subject or case subject |
| `tag` | Ask / Decision / FYI (email) or ticket status |
| `due_signal` | FD due_by, SF ActivityDate, meeting prep deadline |
| `urgency_raw` | importance, FD priority, SF Priority |
| `link_refs` | other surfaces pointing to same issue |

Merge duplicates when the same FD # or SF Case # appears in email subject/body
and ticket list.

### 7. Score and rank

Apply [reference/prioritization-rubric.md](reference/prioritization-rubric.md).

Produce **P0–P3** stack. Cap P0 at 5 items; overflow rolls to P1 with note.

Calendar-aware rules:

- Meeting in ≤90 min that needs prep → boost related items to P0/P1
- No focus time before noon + heavy meeting load → shrink P0 to top 3 only
- Back-to-back afternoon → batch email replies into a single focus block

### 8. Synthesize and offer

Fill the output format. Propose **First moves** that fit the next open calendar
gap (or before first meeting if gap exists).

## Guardrails

- Evidence from system data only; label assumptions.
- **No outbound writes** — no email send, FD reply, SF update, or ticket
  status change unless {{employee_name}} explicitly approves after a draft.
- Do not invent meetings, senders, ticket ids, or case numbers.
- Prefer concise tables over long prose.
- If workload exceeds available focus time, say so and name what to defer.

## Trigger phrases

prioritize my day, day plan, daily prioritization, what should I work on,
check email and tickets, email freshdesk salesforce calendar, start my day,
plan my workday, open tickets and inbox
