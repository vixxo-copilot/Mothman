---
name: morning-brief
description: >-
  Builds a personal morning work briefing from Microsoft 365 calendar and inbox,
  plus Linear and Teams when available. Use when the user asks for a morning
  brief, personal day start, what's on today, inbox and calendar check, or how
  to start the workday.
---

# Morning Brief

Personal day-start workflow for AJ Sheth at Vixxo. Work context only.

## When to use

- "Morning brief" / "what's my day" / "personal day start"
- Start-of-day calendar + inbox check
- Prep before the first meeting block

If the Vixxo project skill `daily-briefing` is available, use it for work-only
operating-context briefings and use `morning-brief` for personal day-start
requests; `morning-brief` adds the personal day-start sections below.

## Output format

Return in this order:

1. **Today at a glance** — meeting load, first/last meeting, conflicts
2. **Priority items** — must-do today, ordered by urgency
3. **SF case mail to sync** — open Cases you own with Outlook mail not yet on SF
4. **Account corrections** — Cases on placeholder/wrong Account (audit-only)
5. **Inbox highlights** — unread actionable mail only (skip noise)
6. **Blockers and risks** — waiting states, tentative RSVPs, auth gaps
7. **Follow-ups** — owner + suggested timing
8. **First moves** — 2–3 concrete next actions

Keep sections scannable. No wall-of-text.

## Workflow

### 1. Microsoft 365 auth

Before any Graph call:

1. Call `verify-login` on the Microsoft 365 MCP.
2. If unauthenticated, call `login` and give the user the device-code URL
   and code. Wait for confirmation, then re-verify.

Default timezone: `America/Denver`.

### 2. Calendar

Use `get-calendar-view`:

- `startDateTime`: start of today (local)
- `endDateTime`: end of today + 2 days
- `orderby`: `start/dateTime asc`
- `select`: `subject,start,end,location,isOnlineMeeting,onlineMeeting,organizer,showAs`
- `top`: 15

Follow `@odata.nextLink` (or use `fetchAllPages` if supported) until the
full window is retrieved before calculating today's first/last meeting and
conflicts.

Flag: tentative invites needing RSVP, back-to-back blocks, external meetings.

### 3. Inbox

Use `list-mail-folder-messages` with `mailFolderId: inbox`:

- Unread pass: `filter: isRead eq false`, `top: 20`
- `select`: `id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,importance,conversationId`
- `orderby`: `receivedDateTime desc`

Classify each item: **Ask** / **Decision** / **FYI**. Deprioritize:
GitHub/Cursor/Slack onboarding, Meraki WiFi confirmations, Teams
"trying to reach you" nudges, marketing mail.

Surface Vixxo senders and attachments first.

Do not combine `$search` and `$filter` on the same Graph request.

### 4. SF case mail to sync (dry-run)

Scan open Salesforce Cases assigned to the operator for Outlook threads not
yet archived on the Case. **Dry-run only** — do not pass `--execute` during
the morning brief unless the user explicitly approves sync.

Run:

```bash
python .agents/skills/sf-case-email-sync/scripts/morning_case_mail_scan.py \
  --days 7 --limit 15 \
  --output .tmp/sf-email-sync-morning.json

python .agents/skills/sf-case-email-sync/scripts/audit_case_accounts.py \
  --owner-me --limit 15 \
  --output .tmp/sf-account-audit-morning.json
```

Include mail scan output in **SF case mail to sync** and account audit output in
**Account corrections** (recommended Case `AccountId` updates — audit only, no
writes). If either scan fails, note what was skipped and continue.

- Cases with only `skip_file_exists` are omitted from mail sync (already synced).
- Account audit is **read-only** — never update Case `AccountId` during the brief.
- Offer execute per Case after review; never auto-sync during the brief.
- Full skill: `sf-case-email-sync` · vetting: `sp-inbound-vetting`.

**Full portfolio run** (schedule once each morning after the compact scan, or
weekly; allow ~45–60 min for ~156 open Cases):

```bash
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --owner-me --days 7 --limit 156 --account-audit \
  --output .tmp/sf-email-sync-full-plan.json
```

Review the JSON plan before any `--execute` sync or account corrections.

### 5. Linear (if MCP available)

Pull active issues assigned to the user with due-date pressure.
Note blocked or stale items.

### 6. Teams (if MCP available)

Scan recent mentions and unanswered asks in the last 24–48 hours.

### 7. Synthesize

Merge into the output format. Propose a realistic first execution sequence
given meeting load.

## Inbox triage tags

| Tag | Meaning |
|-----|---------|
| Ask | Someone needs a response or decision |
| Decision | Calendar invite, approval, or fork in the road |
| FYI | Informational; archive after skim |

## Guardrails

- Evidence from system data only; label assumptions.
- Do not send outbound mail or Teams messages — draft only if asked.
- Do not invent meetings, senders, or issue IDs.
- If an MCP is unavailable, say what was skipped and continue with the rest.

## Trigger phrases

morning brief, personal day start, what's my day, check my calendar and email,
start my day, day overview, inbox and calendar
