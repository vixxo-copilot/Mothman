---
name: mothman-good-morning
description: >-
  Builds Crystal Gagner's "Good Morning, Crystal" day briefing with Mothman
  cryptid-themed HTML: weather, calendar, Salesforce workload, daily SF queue
  Excel workbook (by case type × status, oldest first), SF case mail sync,
  account corrections, inbox triage, and first moves. Use for good morning,
  Good Morning Crystal, mothman good morning, or HTML morning report.
---

# Mothman Good Morning

Personal morning briefing for **Crystal Gagner** at Vixxo. Work context only.
Persona: Mothman — confident, smart, no-nonsense.

Mirrors the Celestia / `vanessa-good-morning` pattern (JSON snapshot + HTML
render) with Crystal’s morning-brief sections and a cryptid visual theme.

## When to use

- "Good morning" / "Good Morning, Crystal" / "mothman good morning"
- "HTML morning report" / "render my day"
- Start-of-day snapshot before the first meeting

For a chat-only brief without HTML, `morning-brief` is also fine; this skill
**always** writes JSON and renders HTML unless the operator says chat-only.

## Primary deliverable: HTML report

1. Collect all sections (workflow below).
2. Write JSON to `.tmp/mothman-good-morning/data-YYYY-MM-DD.json`
   (schema: [reference-json.md](reference-json.md)).
3. Render HTML:

```bash
python .agents/skills/mothman-good-morning/scripts/render_good_morning_html.py \
  .tmp/mothman-good-morning/data-YYYY-MM-DD.json --open
```

4. Post a short chat summary (glance + first moves) and the HTML path.
   Do not dump the full HTML into chat.

## Output sections (order)

1. **Weather** — Wichita, KS
2. **Today at a glance** — meeting load, hard stops, conflicts
3. **Today's meetings** — chronological table
4. **Salesforce — open workload** — total / cases / leads / tasks
5. **Open Cases by type** — RecordType subsections; **Rate Changes** first
6. **SF queue Excel** — full open Case breakdown by type × status (oldest first); overwrites daily workbook
7. **SF case mail to sync** — dry-run only
8. **Account corrections** — audit-only (never write AccountId here)
9. **Inbox highlights** — actionable unread only
10. **Blockers and risks**
11. **Follow-ups**
12. **First moves** — 2–3 concrete actions
13. **Day-over-day** — vs prior JSON snapshot when available

## Workflow

Run in parallel where possible. Constants: [reference.md](reference.md).

### 0. Scope

- **Date / TZ:** today in `America/Chicago` (Central)
- **Operator:** Crystal Gagner — `Crystal.Gagner@vixxo.com`
- Do not send outbound mail or Teams. Do not mutate SF Accounts during brief.

### 1. Weather — Wichita, KS

Open-Meteo (no API key). URL in [reference.md](reference.md).

Summarize: current temp (°F preferred for Crystal; include °C in JSON),
conditions, wind, today’s high/low, precip chance.

### 2. Microsoft 365 auth + calendar

1. `verify-login` on Microsoft 365 MCP; `login` if needed.
2. `get-calendar-view` for today 00:00–23:59:59 `America/Chicago`
   (`orderby: start/dateTime asc`, `top: 25`, follow nextLink).
3. Flag tentative RSVPs, back-to-backs, coverage PTO markers.

### 3. Salesforce — open workload

Resolve Crystal’s `UserId`, then COUNT open Cases / Leads / Tasks
(`IsClosed = false` / `IsConverted = false`). See [reference.md](reference.md).

Then break open Cases by **RecordType** (not the Case `Type` picklist):

1. Aggregate `RecordType.Name` + `Status` for open owned Cases.
2. Build `salesforce.case_types[]` ordered with **Rate Changes** first
   (`RecordType.Name = 'Rate Negotiation'`, display label `Rate Changes`,
   `priority: true`).
3. Remaining types by open volume (typically Service Provider Support,
   Provider Onboarding, Coverage Change).
4. Per type include: `total`, `new_count` (Status = `New` / not started),
   `oldest_new_created` / `newest_new_created` (Case `CreatedDate`),
   optional `status_breakdown`.
5. For **Rate Changes**, list every New case in `new_cases[]` with
   CaseNumber, Subject, Status, CreatedDate (and Id for Lightning links).
   For large buckets (e.g. SP Support), summary + New date range only —
   do not dump hundreds of rows into HTML.

### 3b. SF queue Excel (full breakdown — required daily)

Regenerate Crystal’s open-Case workbook every Good Morning run (overwrites
the stable path so the same file stays current):

```bash
python .agents/skills/mothman-good-morning/scripts/export_sf_queue_workbook.py --json
```

- Stable path: `.tmp/mothman-good-morning/Crystal-SF-Queue.xlsx`
- Dated copy: `.tmp/mothman-good-morning/Crystal-SF-Queue-YYYY-MM-DD.xlsx`
- Sheets: **Summary** (type + type×status counts), **All Cases**, then one
  sheet per RecordType (**Rate Changes** first). Within each type sheet,
  status section banners; **oldest CreatedDate at the top of each status**.
- Put paths + totals into `salesforce.queue_workbook` in the JSON payload.
- Mention the workbook path in the chat summary (do not paste hundreds of rows).

### 4. SF case mail to sync (dry-run)

```bash
python .agents/skills/sf-case-email-sync/scripts/morning_case_mail_scan.py \
  --days 7 --limit 15 \
  --output .tmp/sf-email-sync-morning.json
```

Include Cases needing sync in the HTML payload. Never `--execute` here.

### 5. Account corrections (audit-only)

```bash
python .agents/skills/sf-case-email-sync/scripts/audit_case_accounts.py \
  --owner-me --limit 15 \
  --output .tmp/sf-account-audit-morning.json
```

Surface recommended / review / unresolved. Flag known false positives
(local-part / Gmail / SP 1000) as **do not apply**. Never update Case
`AccountId` during this skill.

Known keep-as-is (operator confirmed):

- Case **7263** → SP **101023** Pinnacle Roofing Partners
- Case **6657** → SP **66466** Armstrong Electric

### 6. Inbox triage

Unread Inbox (`isRead eq false`, `top: 20+`). Classify Ask / Decision / FYI.
Deprioritize noreply “2nd floor”, marketing, Teams nudges.

### 7. Day-over-day

Compare to `.tmp/mothman-good-morning/data-{prior}.json` when present.
Always write today’s `metrics_snapshot`.

### 8. Synthesize + render

1. Assemble JSON per [reference-json.md](reference-json.md).
2. Save snapshot.
3. Run `render_good_morning_html.py` with `--open`.
4. Chat: 4–8 line Mothman lead + path to HTML + first moves.

## Guardrails

- Evidence from system data only; label assumptions.
- Do not invent meetings, Case numbers, or weather.
- Dry-run only for mail sync and account audit.
- If an MCP/script fails, note it in `skipped` and continue.

## Trigger phrases

good morning, Good Morning Crystal, mothman good morning, HTML morning report,
render my day, cryptid brief
