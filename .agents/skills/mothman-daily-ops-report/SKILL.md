---
name: mothman-daily-ops-report
description: >-
  Personal daily ops recap for Crystal: Salesforce queue, Outlook mail, and
  Teams chat activity with day-over-day deltas and a rolling 5-day window.
  HTML + snapshots. Use when the user asks for a daily ops report, personal
  SPM-style daily recap, queue+email+Teams day-over-day, or mothman-daily-ops-report.
---

# Mothman Daily Ops Report

Read-only **personal** daily report (Crystal’s queue only) across **Salesforce**,
**Outlook**, and **Teams chat**, with **day-over-day** deltas and a **rolling
5-day** window. Persisted snapshots enable accurate DoD comparison.

## Quick start

```
Run mothman-daily-ops-report.
```

Or:

```powershell
python .agents/skills/mothman-daily-ops-report/scripts/daily_ops_report.py --open
```

Opens `.tmp/mothman-daily-ops/daily-ops-<as-of>.html` when complete.

## When to use

- "Daily ops report"
- "My queue + email + Teams day-over-day"
- "Personal SPM-style daily recap"
- "mothman-daily-ops-report"

## Scope

| Source | Filter |
|--------|--------|
| Salesforce | Cases owned by `Crystal.Gagner@vixxo.com` |
| Outlook | Crystal’s mailbox (`/me`) |
| Teams | Crystal’s chats (`/me/chats` + recent messages) |

**Not included:** SPM team rollups, Freshdesk SPM group, Gong/PSTN call logs,
channel deep-dives beyond recent active chats (see [reference.md](reference.md)).

## Day definition

- **Timezone:** America/Chicago
- **Day:** calendar day 00:00 → next day 00:00
- **Window:** last **5** calendar days ending today (inclusive)
- **DoD Δ:** each day vs the immediately prior day in the window

## Report slices

| Block | Metrics |
|-------|---------|
| Salesforce — Open | Point-in-time open Case count (+ by type/status). Live for **today**; prior days backfill from Good Morning/Afternoon JSON (afternoon preferred) when available. |
| Salesforce — Closed | Cases closed that day (`ClosedDate`) |
| Salesforce — New | Cases created that day (`CreatedDate`) |
| Outlook | Received, sent (+ unread as-of for today) |
| Teams | Messages from me / others, chats active, replies from me, internal vs external (by sender domain) |

## Agent execution

Run **end-to-end without intermediate confirmation**.

1. Prefer the runner:
   `python .agents/skills/mothman-daily-ops-report/scripts/daily_ops_report.py --open`
2. **Salesforce** always via `sf` CLI (default org `vixxo`).
3. **Outlook + Teams** via Microsoft Graph when a token is available
   (`MS_GRAPH_ACCESS_TOKEN` / `MS365_MCP_OAUTH_TOKEN` or `.env`). If Graph
   auth fails, fill missing `outlook.json` / `teams.json` via MS365 MCP:
   - Outlook: `list-mail-folder-messages` on `inbox` / `sentitems` with
     `$filter` on `receivedDateTime` / `sentDateTime` (do **not** use
     mailbox-wide `$search` for sent vs received — it conflates folders).
   - Teams: `list-chats` then `list-chat-messages` on recent active chats;
     bucket by Chicago day; treat as proxies.
   Then re-run with `--render-only` (keeps cached SF).
4. Request `network` / `all` sandbox permissions proactively for Graph + `sf`.
5. **Outbound guardrail** — do not email or post the report without separate
   explicit approval.

## Workflow

1. Compute the 5-day window ending today (America/Chicago).
2. For each day: load `snapshots/YYYY-MM-DD/*.json` if present and not refreshing;
   else fetch and write.
3. Render HTML to `.tmp/mothman-daily-ops/daily-ops-<as-of>.html`.
4. Return path + headline DoD for today vs yesterday.

## Runner flags

```text
--days N           Window length (default 5)
--refresh-all      Re-fetch every day (ignore snapshots)
--no-salesforce    Skip SF
--no-outlook       Skip Outlook
--no-teams         Skip Teams
--render-only      Rebuild HTML from snapshots only
--open             Open HTML in default browser
```

## Operator output

1. HTML path
2. Today vs yesterday headlines (SF open/closed/new, Outlook received/sent, Teams from-me / chats active)
3. Any days that could not be backfilled (auth, API limits)
