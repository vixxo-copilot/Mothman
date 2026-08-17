---
name: mothman-good-morning
description: >-
  Builds Crystal Gagner's "Good Morning, Crystal" day briefing with Mothman
  cryptid-themed HTML: weather, calendar, Salesforce workload, daily SF queue
  Excel workbook (by case type × status, oldest first), SF case mail sync,
  account corrections, inbox triage, and first moves. Then runs a Phase 2
  skill cascade: Crystal-queue SF duplicate review (report-only), SF Task
  overview, and voicemail triage when inventory is waiting. Use for good
  morning, Good Morning Crystal, mothman good morning, full morning, or HTML
  morning report. Say "brief only" to skip the cascade.
---

# Mothman Good Morning

Personal morning briefing for **Crystal Gagner** at Vixxo. Work context only.
Persona: Mothman — confident, smart, no-nonsense.

Mirrors the Celestia / `vanessa-good-morning` pattern (JSON snapshot + HTML
render) with Crystal’s morning-brief sections and a cryptid visual theme.

## When to use

- "Good morning" / "Good Morning, Crystal" / "mothman good morning"
- "HTML morning report" / "render my day" / "full morning"
- Start-of-day snapshot before the first meeting

**Opt out of cascade:** "brief only" / "good morning brief only" / "skip cascade"
→ Phase 1 HTML only.

For a chat-only brief without HTML, `morning-brief` is also fine; this skill
**always** writes JSON and renders HTML unless the operator says chat-only.

Afternoon / mid-day mirror: [`mothman-good-afternoon`](../mothman-good-afternoon/SKILL.md)
(same renderer; `report_kind: afternoon`). Cascade is **morning-default**;
afternoon runs Phase 2 only when Crystal asks.

## Primary deliverable: HTML report (Phase 1)

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
5. **Unless brief-only**, continue to [Phase 2 — Skill cascade](#phase-2--skill-cascade).

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
14. **Skill cascade (planned)** — counts / paths when Phase 2 will run (fill results after cascade)

## Workflow

Run in parallel where possible. Constants: [reference.md](reference.md).

### 0. Scope

- **Date / TZ:** today in `America/Chicago` (Central)
- **Operator:** Crystal Gagner — `Crystal.Gagner@vixxo.com`
- Do not send outbound mail or Teams. Do not mutate SF Accounts during brief.
- Phase 2 duplicate review is **report-only** (no merges/closes).
- Voicemail triage in Phase 2 follows `sp-voicemail-triage` write rules
  (pre-authorized for that skill) — only when inventory is waiting.

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

### 3c. Voicemail inventory (lightweight — for cascade gate)

During Phase 1, count pending sources (no transcription yet):

- SF open Cases: Subject LIKE `%New voicemail%` owned by Crystal **or**
  Vendor Relations / 4046 queue markers (see `sp-voicemail-triage`)
- Outlook folder **VM**: unread / recent `New voicemail` subjects
- Optional: open QSIAP FD tickets with subject `New voicemail`

Store counts in `skill_cascade.voicemail.inventory` (see reference-json).
Do **not** run full triage until Phase 2.

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

1. Assemble JSON per [reference-json.md](reference-json.md), including a
   `skill_cascade` stub (`enabled: true` unless brief-only).
2. Save snapshot.
3. Run `render_good_morning_html.py` with `--open`.
4. Chat: 4–8 line Mothman lead + path to HTML + first moves.
5. Proceed to Phase 2 when cascade is enabled.

---

## Phase 2 — Skill cascade

Run **after** the HTML brief opens, in this order. Load each sibling
`SKILL.md` and follow it with the Crystal-scoped constraints below.
Record outcomes into `skill_cascade` (re-render HTML optional; chat
summary of cascade results is enough if re-render is slow).

| # | Skill / script | Morning mode | Writes? |
| --- | --- | --- | --- |
| 1 | SF Task overview | Read-only export | No |
| 2 | `sp-fd-sf-duplicate-bridge` | Crystal-owned seed scan | **No** (report only) |
| 3 | `sp-voicemail-triage` | Full batch **only if** inventory &gt; 0 | Yes (per that skill) |

Skip individual legs if Crystal says e.g. "skip voicemail" / "dupes only".

### 2.1 SF Task overview

There is no separate skill — this is owned by Good Morning:

```bash
python .agents/skills/mothman-good-morning/scripts/export_sf_task_overview.py --json
```

- Artifacts: `.tmp/mothman-good-morning/Crystal-SF-Tasks-YYYY-MM-DD.{json,md}`
- Chat: open total, overdue, due today, top buckets
- Fold summary into `skill_cascade.task_overview`

### 2.2 SF duplicate review — **Crystal queue only**

Load [`sp-fd-sf-duplicate-bridge`](../sp-fd-sf-duplicate-bridge/SKILL.md).
Morning default is **SF-only, Crystal-owned seed, report-only**.

1. Ensure a Case window cache exists (Rate Negotiation + Service Provider
   Support open Cases since ~60 days **or** Owner = Crystal). Prefer reusing
   today’s
   `.agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-cases-window-crystal-queue-YYYYMMDD.json`
   when fresh; otherwise export via SOQL/`sf` and save that path.
2. Run:

```bash
python .agents/skills/sp-fd-sf-duplicate-bridge/scripts/scan_crystal_owned_duplicates.py \
  --sf-cache .agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-cases-window-crystal-queue-YYYYMMDD.json \
  --date YYYYMMDD \
  --open
```

3. Present: groups count, Cases with dupes, other-owner sibling count, HTML path.
4. **Do not** run `merge_sf_duplicates.py --execute` from Good Morning.
   Offer merge plan only if Crystal asks.

### 2.3 Voicemail triage

Load [`sp-voicemail-triage`](../sp-voicemail-triage/SKILL.md).

- If Phase 1 inventory is **0** across SF / Outlook VM / QSIAP → skip; note
  "no voicemails waiting" in `skill_cascade.voicemail`.
- If inventory **&gt; 0** → run the skill’s default batch (transcribe + route).
  That skill’s outbound/SF writes are pre-authorized **for voicemail triage**;
  still do **not** send Teams or non-voicemail mail from this cascade.
- If Crystal said "inventory only" / "dry-run voicemail" → triage preview only
  (`dry-run` mode in that skill); no writes.

### 2.4 Cascade chat wrap

After Phase 2, add 3–6 lines:

- Tasks: open / overdue / due today
- Dupes: N groups (M with other-owner siblings) + report path
- Voicemail: skipped / dry-run / batch summary line

---

## Guardrails

- Evidence from system data only; label assumptions.
- Do not invent meetings, Case numbers, or weather.
- Dry-run only for mail sync and account audit.
- Duplicate cascade = report only; never auto-merge.
- If an MCP/script fails, note it in `skipped` / `skill_cascade.*.error` and continue.

## Trigger phrases

good morning, Good Morning Crystal, mothman good morning, HTML morning report,
render my day, cryptid brief, full morning

**Cascade off:** brief only, skip cascade
