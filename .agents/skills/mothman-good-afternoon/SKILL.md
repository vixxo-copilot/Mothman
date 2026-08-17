---
name: mothman-good-afternoon
description: >-
  Builds Crystal Gagner's "Good Afternoon, Crystal" mid/late-day check-in with
  the same Mothman HTML sections as mothman-good-morning: remaining calendar,
  Salesforce by case type (Rate Changes first), SF queue Excel refresh, mail
  sync dry-run, account audit, inbox, and close-of-day first moves. Use for
  good afternoon, afternoon check-in, afternoon brief, or HTML afternoon report.
---

# Mothman Good Afternoon

Afternoon check-in for **Crystal Gagner** at Vixxo. Work context only.
Persona: Mothman — confident, smart, no-nonsense.

**Mirrors** [`mothman-good-morning`](../mothman-good-morning/SKILL.md): same
data sources, JSON schema, HTML renderer, and SF queue workbook. Differences
are framing (remaining day), paths, and day-over-day vs this morning’s
snapshot when available.

The morning **Phase 2 skill cascade** (task overview, Crystal-queue
duplicates, voicemail) is **not** default here — run it only when Crystal
asks (e.g. "afternoon with cascade").

## When to use

- "Good afternoon" / "afternoon check-in" / "afternoon brief"
- "HTML afternoon report" / "midday update" / "end of day status"
- Mid/late day re-sync before EOD mail sync or after a Focus block

## Primary deliverable: HTML report

1. Collect sections (same workflow as Good Morning; see sibling skill).
2. Write JSON to `.tmp/mothman-good-morning/data-afternoon-YYYY-MM-DD.json`
   (schema: [../mothman-good-morning/reference-json.md](../mothman-good-morning/reference-json.md)).
3. Set afternoon framing fields:

```json
{
  "report_kind": "afternoon",
  "greeting": "Good Afternoon",
  "glance_heading": "Rest of day at a glance",
  "meetings_heading": "Remaining meetings"
}
```

4. Render (reuse morning script):

```bash
python .agents/skills/mothman-good-morning/scripts/render_good_morning_html.py \
  .tmp/mothman-good-morning/data-afternoon-YYYY-MM-DD.json --open
```

HTML lands next to morning artifacts as
`.tmp/mothman-good-morning/good-afternoon-YYYY-MM-DD.html` when the input
basename contains `afternoon`; otherwise the renderer writes
`good-morning-YYYY-MM-DD.html`. Prefer the `data-afternoon-` prefix.

5. Chat: short lead + HTML path + SF queue Excel path + 2–3 close-of-day moves.
   Do not dump full HTML into chat.

## Output sections (same order as morning)

1. Weather — Wichita, KS (current conditions)
2. Rest of day at a glance — remaining hard stops / coverage
3. Remaining meetings — from now through EOD (Central)
4. Salesforce — open workload
5. Open Cases by type — **Rate Changes** first; New counts + CreatedDate
6. SF queue Excel — regenerate (overwrites stable workbook)
7. SF case mail to sync — dry-run (use `--output .tmp/sf-email-sync-afternoon.json`)
8. Account corrections — audit-only (skip rewrite if morning audit is still fresh and hung risk is high; note in `skipped`)
9. Inbox highlights — actionable unread
10. Blockers / Follow-ups / First moves — oriented to **close of day**
11. Day-over-day — prefer compare to **this morning’s**
    `data-YYYY-MM-DD.json` when present (not only prior calendar day)

## Workflow deltas vs morning

| Step | Afternoon note |
| --- | --- |
| Calendar | `get-calendar-view` from **now** → 23:59:59 `America/Chicago` |
| Day-over-day | Morning snapshot first: `.tmp/mothman-good-morning/data-YYYY-MM-DD.json` |
| Mail sync | Dry-run to `.tmp/sf-email-sync-afternoon.json` |
| Account audit | Optional if morning file is same-day and clean; else re-run with `--json-only` |
| First moves | EOD sync, open Rate Change New work, inbox asks still open |

Constants / SOQL: [../mothman-good-morning/reference.md](../mothman-good-morning/reference.md).

## Guardrails

Same as Good Morning: evidence-only, no outbound sends, dry-run mail sync,
never write Case `AccountId` during this skill.

## Trigger phrases

good afternoon, afternoon check-in, afternoon brief, HTML afternoon report,
midday update, good afternoon crystal
