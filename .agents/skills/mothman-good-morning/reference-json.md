# JSON payload for mothman-good-morning HTML

Schema version: 1. Agent writes JSON, then runs:

```bash
python .agents/skills/mothman-good-morning/scripts/render_good_morning_html.py \
  .tmp/mothman-good-morning/data-YYYY-MM-DD.json --open
```

## Example path

`.tmp/mothman-good-morning/data-2026-07-29.json`

## Top-level fields

| Field | Type | Required |
| --- | --- | --- |
| `date_label` | string | no |
| `generated_at` | string | no |
| `report_kind` | string | no — `morning` (default) or `afternoon` |
| `greeting` | string | no — overrides hero (“Good Morning” / “Good Afternoon”) |
| `glance_heading` | string | no |
| `meetings_heading` | string | no |
| `lead` | string | no — short Mothman one-liner |
| `glance` | object | no — meeting load / hard stops / coverage |
| `weather` | object | yes |
| `meetings` | array | yes |
| `salesforce` | object | yes |
| `case_mail_sync` | object | yes |
| `account_corrections` | object | yes |
| `inbox` | object | yes — totals + short needs_action (compat) |
| `email_briefing` | object | yes — urgency + date email briefing |
| `blockers` | string[] | no |
| `follow_ups` | array | no |
| `first_moves` | string[] | yes |
| `metrics_snapshot` | object | yes |
| `day_over_day` | object | no |
| `skill_cascade` | object | no — Phase 2 plan + results |
| `skipped` | string[] | no |

## `glance`

```json
{
  "meeting_count": 4,
  "hard_stops": ["Town Hall 9:00–10:00", "Leslie 1:1 1:30"],
  "coverage": "Kate + Anastasia PTO"
}
```

## `weather`

Prefer °F for Crystal. Location: Wichita, KS. Keep °C optional.

```json
{
  "temp_f": 72,
  "feels_like_f": 70,
  "temp_c": 22.2,
  "feels_like_c": 21.1,
  "weather_code": 2,
  "wind_mph": 8,
  "high_f": 84,
  "low_f": 58,
  "precip_pct": 10,
  "summary": "Partly cloudy; light layers for the office."
}
```

## `meetings[]`

```json
{
  "start": "9:00 AM",
  "end": "10:00 AM",
  "subject": "Town Hall Option 2",
  "notes": "Hard stop",
  "join_url": "https://teams.microsoft.com/..."
}
```

## `salesforce`

Prefer `case_types[]` (RecordType subsections). Put **Rate Changes** first
(`record_type`: `Rate Negotiation`, `label`: `Rate Changes`, `priority`: true).
`new_count` = Status New. Created dates are Case `CreatedDate` (date only OK).

```json
{
  "total_open": 340,
  "cases": 292,
  "leads": 1,
  "tasks": 47,
  "case_types": [
    {
      "record_type": "Rate Negotiation",
      "label": "Rate Changes",
      "priority": true,
      "total": 20,
      "new_count": 14,
      "oldest_new_created": "2026-06-12",
      "newest_new_created": "2026-07-23",
      "status_breakdown": {
        "New": 14,
        "In Negotiation": 4,
        "Approved": 1,
        "Agreement Sent": 1
      },
      "new_cases": [
        {
          "Id": "500...",
          "CaseNumber": "5126",
          "Subject": "Rate change request",
          "Status": "New",
          "CreatedDate": "2026-06-12"
        }
      ]
    },
    {
      "record_type": "Service Provider Support",
      "label": "Service Provider Support",
      "priority": false,
      "total": 266,
      "new_count": 232,
      "oldest_new_created": "2026-06-24",
      "newest_new_created": "2026-07-30",
      "status_breakdown": { "New": 232, "Working": 34 }
    }
  ],
  "open_cases_sample": [],
  "queue_workbook": {
    "path": ".tmp/mothman-good-morning/Crystal-SF-Queue.xlsx",
    "dated_path": ".tmp/mothman-good-morning/Crystal-SF-Queue-2026-08-05.xlsx",
    "total_open": 292,
    "as_of": "2026-08-05",
    "note": "Full breakdown by RecordType × Status; oldest CreatedDate at top of each status group."
  }
}
```

`open_cases_sample` is optional fallback when `case_types` is empty.

`queue_workbook` is required on each Good Morning run after
`export_sf_queue_workbook.py` succeeds. If the export fails, omit it and
add a note to `skipped`.

## `case_mail_sync`

From `morning_case_mail_scan.py` dry-run.

```json
{
  "cases_needing_sync": 0,
  "cases": [],
  "note": "Dry-run only — no uploads during brief."
}
```

Case row shape:

```json
{
  "case_number": "7286",
  "subject": "Hall Service Co COI",
  "missing_count": 2,
  "url": "https://vixxo.lightning.force.com/lightning/r/Case/500.../view"
}
```

## `account_corrections`

From `audit_case_accounts.py` audit-only.

```json
{
  "recommended": [],
  "review": [],
  "do_not_apply": [
    {
      "case_number": "7263",
      "keep_account": "101023 Pinnacle Roofing Partners",
      "reason": "Operator confirmed — Lindbergh hits are false positives"
    }
  ],
  "note": "Never write AccountId during this skill."
}
```

## `inbox`

Backward-compatible summary. Prefer populating **`email_briefing`** as the
primary email section; keep `inbox` totals + a short `needs_action` mirror of
urgent/today items.

```json
{
  "total": 40,
  "unread": 12,
  "needs_action_count": 3,
  "needs_action": [
    { "from": "Leslie Nemechek", "subject": "1:1 follow-up", "tag": "Ask" }
  ],
  "no_action_count": 9,
  "no_action_summary": "Noreply digests, Teams nudges, marketing."
}
```

## `email_briefing`

Unread scan across Inbox + non-ignored folders. See ignore list in
[reference.md](reference.md).

```json
{
  "scanned_unread": 28,
  "folders_scanned": ["Inbox", "AP", "To Be Processed", "VM"],
  "folders_ignored": [
    "Templates",
    "Me",
    "Vixxo IT",
    "SP Docs/ Help Desk items",
    "VixxoLink",
    "Meeting Notes",
    "Claude & Mothman"
  ],
  "counts_by_urgency": {
    "urgent": 2,
    "today": 4,
    "this_week": 5,
    "fyi": 17
  },
  "by_urgency": {
    "urgent": [
      {
        "from": "Jerry Medina",
        "subject": "Men's Wearhouse — signed agreement + W9",
        "tag": "Ask",
        "urgency": "urgent",
        "received": "2026-08-13",
        "folder": "Inbox",
        "note": "Case 8172 packet"
      }
    ],
    "today": [],
    "this_week": [],
    "fyi": []
  },
  "by_date": {
    "today": [],
    "yesterday": [],
    "last_7_days": [],
    "older": []
  },
  "noise_summary": "Teams nudges, noreply digests, marketing."
}
```

Each item may appear under both `by_urgency` and `by_date`. Cap HTML rows
(~8 per urgency bucket, ~10 per date bucket); put overflow in counts only.

## `follow_ups[]`

```json
{ "item": "Leslie 1:1 prep", "owner": "Crystal", "when": "before 1:30 PM" }
```

## `metrics_snapshot`

```json
{
  "date": "2026-07-29",
  "salesforce_total_open": 120,
  "salesforce_cases": 80,
  "salesforce_leads": 5,
  "salesforce_tasks": 35,
  "case_mail_needing_sync": 0,
  "account_recommended": 0,
  "inbox_unread": 12
}
```

## `day_over_day`

Same shape as Celestia / vanessa-good-morning (`available`, `prior_date`, `rows`, `summary`).

## `skill_cascade`

Present on every Good Morning unless brief-only (`enabled: false`).

```json
{
  "enabled": true,
  "status": "planned",
  "task_overview": {
    "status": "pending",
    "total_open": null,
    "overdue_count": null,
    "due_today_count": null,
    "bucket_counts": {},
    "path": null
  },
  "duplicates": {
    "status": "pending",
    "mode": "crystal_owned_seed_report_only",
    "duplicate_rows": null,
    "crystal_cases_with_duplicates": null,
    "with_external_owner": null,
    "html": null,
    "md": null
  },
  "voicemail": {
    "status": "pending",
    "inventory": {
      "sf_new_voicemail": 0,
      "outlook_vm": 0,
      "qsiap": 0
    },
    "ran_batch": false,
    "summary": null
  }
}
```

After Phase 2, set each leg `status` to `done` / `skipped` / `error` and
fill counts + artifact paths. `status` at the top becomes `complete` when
all legs finish.
