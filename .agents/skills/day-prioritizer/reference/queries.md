# Query Reference — Day Prioritizer

## Freshdesk

### Current agent

Tool: `view_current_agent` (no args)

Use returned `id` as `{agent_id}`.

### Assigned open + pending tickets

Tool: `search_tickets`

```
agent_id:{agent_id} AND (status:2 OR status:3)
```

Paginate until a page returns fewer than 30 results.

Open-only variant (when user asks):

```
agent_id:{agent_id} AND status:2
```

### Priority labels

| Code | Label |
| ---: | --- |
| 4 | Urgent |
| 3 | High |
| 2 | Medium |
| 1 | Low |

### Status labels

| Code | Label |
| ---: | --- |
| 2 | Open |
| 3 | Pending |
| 4 | Resolved |
| 5 | Closed |

### SLA fields

- `due_by` — resolution due
- `fr_due_by` — first-response due

Treat either timestamp in the past as SLA breach for scoring.

## Salesforce

Always call `get_username` first. Use full workspace directory path in
`run_soql_query`.

### Resolve User Id

Replace `{work_email}` with value from `memory/me/identity.md`:

```sql
SELECT Id, Name, Email FROM User WHERE Email = '{work_email}' LIMIT 1
```

### Open Cases (owned)

```sql
SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate,
       LastModifiedDate, ContactEmail, Origin
FROM Case
WHERE OwnerId = '{userId}' AND IsClosed = false
ORDER BY Priority DESC, LastModifiedDate DESC
LIMIT 25
```

### Open Tasks (owned)

```sql
SELECT Id, Subject, Status, ActivityDate, Priority, WhatId,
       LastModifiedDate, Description
FROM Task
WHERE OwnerId = '{userId}' AND IsClosed = false
ORDER BY ActivityDate ASC NULLS LAST, Priority DESC
LIMIT 15
```

### Optional — Cases where user is last modifier (not owner)

Only when user asks "cases I touched" or owner query returns empty:

```sql
SELECT Id, CaseNumber, Subject, Status, Priority, LastModifiedDate
FROM Case
WHERE LastModifiedById = '{userId}' AND IsClosed = false
ORDER BY LastModifiedDate DESC
LIMIT 15
```

## Microsoft 365

### Graph rules

- Never combine `$search` and `$filter` on one message request.
- Wrap `$search` values in double quotes.
- Prefer `$select` and modest `top`; paginate with `@odata.nextLink`.

### Inbox passes

See SKILL.md §3. Recommended selects:

`id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,importance,conversationId,flag`

### Calendar

See SKILL.md §2. Use `timezone` parameter for local display.

## Cross-reference patterns (regex hints)

When parsing email subject/body for dedupe:

- Freshdesk: `#51234`, `ticket 51234`, `freshdesk.com/a/tickets/51234`
- Salesforce Case: `Case 00012345`, `CaseNumber`, `Case #`

Link merged items in output **Cross-links** section.
