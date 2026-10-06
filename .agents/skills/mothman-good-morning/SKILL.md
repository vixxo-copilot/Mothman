---
name: mothman-good-morning
description: >-
  Builds Crystal Gagner's "Good Morning, Crystal" day briefing with Mothman
  cryptid-themed HTML: weather, calendar, Salesforce workload, daily SF queue
  Excel workbook (by case type × status, oldest first), SF case mail sync,
  account corrections, email briefing (urgency + date, folder ignore list),
  and first moves. Then runs a Phase 2 skill cascade: SF Task breakdown HTML
  (priority queue + buckets), SF Task overview, priority mail HTML (Inbox +
  Maria/Leslie/SPM, Kate/ORMB, Invoices/Statements), Crystal-queue duplicate
  review (report-only), `sp-voicemail-triage` on Crystal-owned Salesforce
  voicemail Cases that have not already been transcribed/triaged, then
  recreate the open-voicemail HTML report for Cases still assigned to
  Crystal. Use
  for good morning, Good Morning Crystal, mothman
  good morning, full morning, or HTML morning report. Say "brief only" to
  skip the cascade.
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
6. **Not Crystal — Prospect SP / onboarding** — Cases that belong to
   recruitment, not SPS (see below)
7. **SF queue Excel** — full open Case breakdown by type × status (oldest first); overwrites daily workbook
8. **SF case mail to sync** — dry-run only
9. **Account corrections** — audit-only (never write AccountId here)
10. **Email briefing** — unread by urgency + date (folder ignore list; see below)
11. **Blockers and risks**
12. **Follow-ups**
13. **First moves** — 2–3 concrete actions (never Prospect SP / onboarding)
14. **Day-over-day** — vs prior JSON snapshot when available
15. **Skill cascade (planned)** — counts / paths when Phase 2 will run (fill results after cascade)

## Workflow

Run in parallel where possible. Constants: [reference.md](reference.md).

### 0. Scope

- **Date / TZ:** today in `America/Chicago` (Central)
- **Operator:** Crystal Gagner — `Crystal.Gagner@vixxo.com`
- Do not send outbound mail or Teams. Do not mutate SF Accounts during brief.
- Phase 2 duplicate review is **report-only** (no merges/closes).
- Voicemail triage in Phase 2 **loads and runs** `sp-voicemail-triage` on
  Crystal-owned Salesforce queue Cases that are still untriaged (generic
  Subject; no Completed `SP Voicemail Triage` Task). Writes follow that
  skill (pre-authorized): transcribe, classify, company-vet, Subject
  rewrite, Case Task. Outlook/QSIAP only when those inventories are waiting.

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

6. **Not Crystal — Prospect SP / onboarding.** These are **not** Crystal’s
   SPS work. Identify and list separately; do **not** put them in first
   moves, High/Medium priority, or “new assignment” as hers.

   Flag when **any** of:
   - `Case.Type` = `Prospect SP`
   - `RecordType.Name` in `Provider Onboarding`, `Recruitment Request`
   - Subject shows onboarding intent (`Potential provider lead`,
     `Prospect SP`, looking/wanting to onboard or become a
     provider/vendor)

   Route note: **Recruitment / onboarding — not Crystal (SPS).** Voicemail
   triage uses the Coverage / Onboarding branch (`spm-recruitment@vixxo.com`
   / Lead Task) and **closes the 4046 Case** off SPS.

   SOQL (Crystal-owned open Cases):

   ```sql
   SELECT Id, CaseNumber, Subject, Status, Type, RecordType.Name, CreatedDate
   FROM Case
   WHERE OwnerId = '{UID}' AND IsClosed = false
     AND (
       Type = 'Prospect SP'
       OR RecordType.Name IN ('Provider Onboarding','Recruitment Request')
       OR Subject LIKE '%Potential provider lead%'
       OR Subject LIKE '%Prospect SP%'
       OR Subject LIKE '%onboard%'
     )
   ORDER BY CreatedDate ASC
   ```

   Put the list in `salesforce.not_crystal_prospect_onboarding` (`cases` +
   `note`). Excel export also paints these and adds a **Not Crystal -
   Prospect/Onboard** sheet.

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

- SF open Cases: Subject LIKE `%New voicemail%` **or** (RecordType
  `Service Provider Support` + Subject `Vixxo Voicemail`) owned by Crystal
  **or** Vendor Relations / 4046 queue markers (see `sp-voicemail-triage`)
- **Untriaged SF queue (Phase 2.4 work set):** Crystal-owned open Cases
  whose Subject is still raw intake — 8x8 `New voicemail from …` **or**
  SP Support `Vixxo Voicemail` — and that do **not** already have a
  Completed `SP Voicemail Triage` Task. Include Status New **and** Working
  (full queue, not last-3-days only). Skip Subjects already rewritten to
  `Voicemail — …` / `VM Triage — …`.
- Outlook folder **VM**: unread / recent `New voicemail` subjects
- Optional: open QSIAP FD tickets with subject `New voicemail`

Store counts in `skill_cascade.voicemail.inventory` (see reference-json),
including `sf_generic_subject` / `untriaged`.
Do **not** run full STT/triage until Phase 2.

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

### 6. Email briefing (urgency + date)

Replace shallow “inbox highlights” with a structured **email briefing**.

**Scan:** unread messages in **Inbox** plus other mail folders under the root /
Inbox tree, **except** the ignore list. Prefer modest `$top` per folder
(15–25 unread); do not dump full bodies into HTML.

**Always ignore** (match folder `displayName` case-insensitive; substring OK
for the SP Docs / VixxoLink variants):

| Ignore folder |
| --- |
| Templates |
| Me |
| Vixxo IT |
| SP Docs (incl. `SP Docs/ Help Desk items`) |
| VixxoLink |
| Meeting Notes |
| Claude & Mothman |

Do **not** ignore **VM** here — voicemail inventory still uses that folder in
Phase 1c / cascade. Skip system folders that are never work mail (Junk,
Deleted, Conversation History, Sync Issues, RSS*) unless Crystal asks.

**Classify each actionable thread:**

| Field | Values |
| --- | --- |
| `urgency` | `urgent` · `today` · `this_week` · `fyi` |
| `tag` | `Ask` · `Decision` · `FYI` |
| `received` | ISO date (Chicago day) |
| `folder` | mailbox folder display name |

**Urgency heuristics (Crystal / SPS):**

- **urgent** — external SP/compliance reply blocking work today; manager/SLT
  ask; same-day deadline language; COI/W9/agreement packet waiting on her
- **today** — clear Ask/Decision from work contacts; open Case-linked packet
- **this_week** — aging actionable thread (>1 day) without same-day heat
- **fyi** — status notes, CC chains, resolved-elsewhere; deprioritize noreply
  “2nd floor”, marketing, Teams nudges

**Present in HTML + chat (two cuts, same items):**

1. **By urgency** — urgent → today → this_week → fyi (counts + top rows)
2. **By date** — today → yesterday → last 7 days → older

Keep `inbox` in JSON for backward compatibility (totals + short
`needs_action` mirror of urgent/today). Full structure lives in
`email_briefing` ([reference-json.md](reference-json.md)).

### 7. Day-over-day

Compare to `.tmp/mothman-good-morning/data-{prior}.json` when present.
Always write today’s `metrics_snapshot`.

### 8. Synthesize + render

1. Assemble JSON per [reference-json.md](reference-json.md), including a
   `skill_cascade` stub (`enabled: true` unless brief-only) and
   `email_briefing`.
2. Save snapshot.
3. Run `render_good_morning_html.py` with `--open`.
4. Chat: 4–8 line Mothman lead + path to HTML + first moves + email urgency
   counts.
5. Proceed to Phase 2 when cascade is enabled.

---

## Phase 2 — Skill cascade

Run **after** the HTML brief opens, in this order. Load each sibling
`SKILL.md` and follow it with the Crystal-scoped constraints below.
Record outcomes into `skill_cascade` (re-render HTML optional; chat
summary of cascade results is enough if re-render is slow).

**Hard gate:** Leg **2.0 VixxoLink probe is mandatory** on every full
morning (not brief-only). Run it **before** legs 2.1–2.5. If probe
`status` is not `ok` after `--prompt-oauth`, **stop the cascade** — do
not run task breakdown, mail, dupes, or voicemail. Report the blocker
in chat and set `skill_cascade.status` to `blocked_vixxolink_mcp`. Only
skip 2.0 when Crystal explicitly says "skip vixxolink" / "skip mcp probe".

| # | Skill / script | Morning mode | Writes? |
| --- | --- | --- | --- |
| 0 | `vixxo-mcp-bearer-fix` — VixxoLink probe (**required gate**) | Silent refresh + Chrome if needed | Yes (`~/.vixxo`, `~/.mcp-auth`) |
| 1 | SF Task breakdown (HTML) | Read-only export + render | No |
| 2 | SF Task overview | Read-only export | No |
| 2b | `mothman-priority-mail-review` | Unread Inbox + 3 named boxes HTML | No |
| 3 | `sp-fd-sf-duplicate-bridge` | Crystal-owned seed scan | **No** (report only) |
| 4 | `sp-voicemail-triage` | Untriaged Crystal-owned SF VM Cases: transcribe + classify + **company vet** + **Subject rewrite** + Case Task; Outlook/QSIAP if inventory &gt; 0 | Yes (per that skill) |
| 5 | Open voicemail HTML | Recreate report of **all open** VM Cases still assigned to Crystal (generic + rewritten) | No |

Skip individual legs **2.1–2.5** if Crystal says e.g. "skip voicemail" /
"dupes only". **Never skip 2.0** unless she explicitly skips the VixxoLink probe.
"skip voicemail" skips 2.4 **and** 2.5. "inventory only" still runs 2.5.

### 2.0 VixxoLink MCP bearer probe (**required**)

Load [`vixxo-mcp-bearer-fix`](../vixxo-mcp-bearer-fix/SKILL.md). Run **first**
every morning so VixxoLink MCP is green when Crystal uses Cursor. Crystal
does **not** need a separate VixxoLink login — run this at the desk; complete
Chrome if it opens (~once per week).

```bash
.cursor/bin/probe-vixxolink-bearer-morning.cmd
```

Or (same behavior + hard gate exit code):

```bash
python .agents/skills/vixxo-mcp-bearer-fix/scripts/probe_vixxolink_bearer.py \
  --silent-refresh --prompt-oauth --write-tmp --json --gate
```

- **Agent must execute this command** — do not infer token health from memory.
- Artifact: `.tmp/vixxo-mcp-bearer/probe-vixxolink-latest.json`
- If `status=ok`: set `skill_cascade.vixxolink_mcp.status=done`, continue to 2.1.
- If Chrome opens: Crystal completes sign-in once; re-run probe until `ok`.
- If still not `ok`: **stop cascade**; set `skill_cascade.status=blocked_vixxolink_mcp`;
  list fix: `.cursor/bin/refresh-vixxolink-bearer.cmd`.
- Fold into `skill_cascade.vixxolink_mcp` (`status`, `launch_ok`, `oauth_expires_at`,
  `actions`, `artifact`).

**Scheduled (optional):** Task Scheduler can run
`.cursor/bin/probe-vixxolink-bearer.cmd` daily (silent refresh only, no browser).

### 2.1 SF Task breakdown (HTML)

Priority-ranked snapshot of open Tasks, High/Medium Cases, new assignments
(last 3 days), Rate New, and Leads — **priority items at the top**, with
**Created** dates on every row.

```bash
python .agents/skills/mothman-good-morning/scripts/export_sf_task_breakdown.py --json
python .agents/skills/mothman-good-morning/scripts/render_sf_task_breakdown_html.py \
  .tmp/mothman-good-morning/sf-task-breakdown-YYYY-MM-DD.json --open
```

- Artifacts: `.tmp/mothman-good-morning/sf-task-breakdown-YYYY-MM-DD.{json,html}`
- Chat: tasks open / overdue, High Cases, Rate New, new Cases (3d), top buckets
- Fold summary into `skill_cascade.task_breakdown`
- Also run on demand when Crystal asks to refresh the task breakdown report

### 2.2 SF Task overview

There is no separate skill — this is owned by Good Morning:

```bash
python .agents/skills/mothman-good-morning/scripts/export_sf_task_overview.py --json
```

- Artifacts: `.tmp/mothman-good-morning/Crystal-SF-Tasks-YYYY-MM-DD.{json,md}`
- Chat: open total, overdue, due today, top buckets
- Fold summary into `skill_cascade.task_overview`

### 2.2b Priority mail review (HTML)

Load [`mothman-priority-mail-review`](../mothman-priority-mail-review/SKILL.md).
Unread only in **Inbox**, **Maria/Leslie/SPM & Adam**, **ORMB/Kate**, and
**Invoices/Statements**. Rank higher-priority asks; list each box oldest → newest.

```bash
python .agents/skills/mothman-priority-mail-review/scripts/export_priority_mail.py \
  --json --open
```

- Artifacts: `.tmp/mothman-priority-mail/priority-mail-YYYY-MM-DD.{json,html}`
- Chat: unread total, urgent/today/this-week counts, HTML path, 2–4 first moves
- Fold into `skill_cascade.priority_mail`
- Skip if Crystal says "skip mail" / "skip priority mail"

### 2.3 SF duplicate review — **Crystal queue only**

Load [`sp-fd-sf-duplicate-bridge`](../sp-fd-sf-duplicate-bridge/SKILL.md).
Morning default is **Salesforce-only, Crystal-owned seed, report-only**.
Crystal does **not** operate in Freshdesk for this cascade — do **not**
open FD, call Freshdesk MCP, run `scan_duplicates.py`, or pass
`--include-fd-xref`. Intra-SF twins only.

1. **Always refresh the Case window cache for today** (do **not** reuse a
   prior-day file — owner changes like Case 6472 → Shelby drop off only when
   the cache is current). Export:

```bash
python .agents/skills/sp-fd-sf-duplicate-bridge/scripts/export_crystal_queue_case_window.py \
  --date YYYYMMDD
```

   Writes
   `.agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-cases-window-crystal-queue-YYYYMMDD.json`
   (open Rate Negotiation / SP Support / Onboarding / Coverage Change /
   Recruitment Request, `CreatedDate = LAST_N_DAYS:100`, **plus** all open
   Cases Crystal still owns — any RecordType).

2. Run the Crystal-owned seed scan against **today’s** cache:

```bash
python .agents/skills/sp-fd-sf-duplicate-bridge/scripts/scan_crystal_owned_duplicates.py \
  --sf-cache .agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-cases-window-crystal-queue-YYYYMMDD.json \
  --date YYYYMMDD \
  --open
```

3. Present: groups count, Cases with dupes, other-owner sibling count, HTML path.
   Open HTML in Chrome (Crystal’s default). SF Case links only — no FD ticket table.
4. **Do not** run `merge_sf_duplicates.py --execute` from Good Morning.
   Offer merge plan only if Crystal asks.
5. **Do not** run the AP→FD check, attachment sync, or Federated FD search
   from Good Morning unless Crystal explicitly asks for Freshdesk.

### 2.4 Voicemail triage — untriaged Salesforce queue

Load [`sp-voicemail-triage`](../sp-voicemail-triage/SKILL.md) and **run it**.
Do **not** stop after listing. Morning default is Crystal’s **Salesforce
queue only** for STT + triage; skip Cases already done.

**1. List untriaged owned Cases** (Crystal’s `sf` login; teammates get their
own queue the same way):

```bash
python .agents/skills/sp-voicemail-triage/scripts/list_owner_vm_cases.py \
  --json --all-generic --skip-triaged-tasks \
  --output .tmp/mothman-good-morning/vm-untriaged-YYYY-MM-DD.json
```

`--all-generic` = every open generic-subject VM Case Crystal owns (New and
Working), not only last-3-days. `--skip-triaged-tasks` drops Cases that
already have a Completed Task `SP Voicemail Triage` / `Voicemail triage`.

**Already triaged — skip (do not re-STT):**

- Subject already starts with `Voicemail —` / `Voicemail -` / `VM Triage —`
  / `VM Triage -` (the list script excludes these)
- Completed Task `SP Voicemail Triage` (or `Voicemail triage`) on the Case
- Failed audio download / STT on a prior pass this morning — leave unchanged
  and count as `failed` (do not loop)

**2. For each in-scope Case (newest `CreatedDate` first):** follow
`sp-voicemail-triage` end to end:

1. Download `.wav` / `.mp3` from the Case inbound EmailMessage
2. Transcribe (faster-whisper)
3. Classify + callback + **company-vet** (Gateway + SF Account/Lead/Contact;
   Lead search includes Closed/converted via `search_sf_leads.py`; first-name
   + ANI → web identity then LastName)
4. Rewrite Subject, then post the Completed Case Task (or close AP/short /
   **Circle K Help Desk** as Duplicate per that skill). Circle K Maintenance
   / Help Desk voicemails go to the **Circle K account team** (SR PM +
   Support when an FWKD is present) — **not SPS**. Subject:
   `Voicemail — Circle K Help Desk — {ask}`.

```
Voicemail — {SP Name} ({SP#}) — {request}
```

`{request}` is the plain-English sub-reason (not the raw 8x8 caller ID).
Omit `({SP#})` when unknown. Apply with:

```bash
python .agents/skills/sp-voicemail-triage/scripts/update_vm_case_subject.py \
  --case-id 500... --sp-name "ACR Maintenance" --sp-number KS12345 \
  --request "SR callback / dispatch"
```

**3. After the SF queue pass**, run Outlook VM / QSIAP batches only when
those inventories are **&gt; 0**.

- Empty untriaged SF list **and** Outlook/QSIAP 0 → skip; note
  "no untriaged voicemails" in `skill_cascade.voicemail`.
- That skill’s SF writes (Task, Subject, AccountId when confident) and its
  own voicemail forwards are pre-authorized **for voicemail triage**; still
  do **not** send Teams or non-voicemail mail from this cascade.
- If Crystal said "inventory only" / "dry-run voicemail" / "skip voicemail"
  → list only (or `--dry-run` on the updater); no writes.
- Do **not** treat a large untriaged count as a reason to skip. Process the
  full in-scope list; if time-boxed, finish remaining Cases in the same
  session rather than reporting "listed only".

### 2.5 Open voicemail HTML (recreate after triage)

Rebuild the HTML inventory of **open voicemail Cases Crystal still owns**
after 2.4 so rewritten Subjects and closes drop off / update. Do **not**
reuse yesterday’s HTML.

```bash
python .agents/skills/mothman-good-morning/scripts/export_open_vm_cases.py --json
python .agents/skills/mothman-good-morning/scripts/render_open_vm_html.py \
  .tmp/mothman-good-morning/open-voicemail-YYYY-MM-DD.json --open
```

- Includes generic `New voicemail` / `Vixxo Voicemail` **and** rewritten
  `Voicemail —` / `VM Triage —` Cases that are still `IsClosed = false`
  and `OwnerId` = Crystal.
- Sections: untriaged · rewritten still on queue · Prospect SP / onboarding
  (not Crystal).
- Artifacts: `.tmp/mothman-good-morning/open-voicemail-YYYY-MM-DD.{json,html}`
- Open in Chrome. Fold `html`, `json`, totals into
  `skill_cascade.voicemail.open_report`.
- Run even when 2.4 found zero untriaged (queue may still have rewritten
  leftovers). Skip only with "skip voicemail" / brief-only.

### 2.6 Cascade chat wrap

After Phase 2, add 4–8 lines:

- VixxoLink MCP: ok / refreshed / needs sign-in + expires_at
- Task breakdown HTML path + priority highlights (High Cases, Rate New, new 3d)
- Tasks: open / overdue / due today
- Priority mail: unread total + urgent/today + HTML path
- Dupes: N groups (M with other-owner siblings) + report path
- Voicemail: N untriaged in-scope · M triaged (subjects + Tasks) · skipped
  already-done · failed STT · Outlook/QSIAP line
- Open VM HTML: total open · untriaged · rewritten still assigned · path
- Not Crystal: N Prospect SP / onboarding Cases listed (not SPS)

---

## Guardrails

- Evidence from system data only; label assumptions.
- Do not invent meetings, Case numbers, or weather.
- Dry-run only for mail sync and account audit.
- Duplicate cascade = report only; never auto-merge. **SF-only** — no Freshdesk.
- **Exception:** VixxoLink probe (2.0) failure **blocks** legs 2.1–2.5 — do not continue.
- Other MCP/script failures: note in `skipped` / `skill_cascade.*.error` and continue.

## Trigger phrases

good morning, Good Morning Crystal, mothman good morning, HTML morning report,
render my day, cryptid brief, full morning

**Cascade off:** brief only, skip cascade
