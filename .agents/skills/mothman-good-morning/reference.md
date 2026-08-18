# Mothman Good Morning — Constants

## Operator

| Field | Value |
| --- | --- |
| Name | Crystal Gagner |
| Email | Crystal.Gagner@vixxo.com |
| Role | SPS Lead, Vixxo |
| Greeting | Good Morning, Crystal |
| Timezone | America/Chicago (Central) |
| SF org alias | vixxo |

## Weather (Wichita, KS)

Open-Meteo forecast (no key):

```
https://api.open-meteo.com/v1/forecast?latitude=37.6872&longitude=-97.3301&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FChicago&forecast_days=1
```

Label in UI: **Wichita, KS**.

WMO weather_code → short text (common codes):

| Code | Label |
| --- | --- |
| 0 | Clear |
| 1–3 | Mostly clear / partly cloudy / overcast |
| 45, 48 | Fog |
| 51–57 | Drizzle |
| 61–67 | Rain |
| 71–77 | Snow |
| 80–82 | Rain showers |
| 85–86 | Snow showers |
| 95–99 | Thunderstorm |

## Paths

| Artifact | Path |
| --- | --- |
| Skill root | `.agents/skills/mothman-good-morning/` |
| Renderer | `.agents/skills/mothman-good-morning/scripts/render_good_morning_html.py` |
| Brand image | `assets/mothman-profile.png` |
| JSON snapshots | `.tmp/mothman-good-morning/data-YYYY-MM-DD.json` |
| HTML output | `.tmp/mothman-good-morning/good-morning-YYYY-MM-DD.html` |
| SF queue Excel (stable) | `.tmp/mothman-good-morning/Crystal-SF-Queue.xlsx` |
| SF queue Excel (dated) | `.tmp/mothman-good-morning/Crystal-SF-Queue-YYYY-MM-DD.xlsx` |
| Queue export script | `.agents/skills/mothman-good-morning/scripts/export_sf_queue_workbook.py` |
| Task overview script | `.agents/skills/mothman-good-morning/scripts/export_sf_task_overview.py` |
| Task overview JSON/MD | `.tmp/mothman-good-morning/Crystal-SF-Tasks-YYYY-MM-DD.{json,md}` |
| Mail sync dry-run | `.tmp/sf-email-sync-morning.json` |
| Account audit | `.tmp/sf-account-audit-morning.json` |
| Crystal dupe scan script | `.agents/skills/sp-fd-sf-duplicate-bridge/scripts/scan_crystal_owned_duplicates.py` |
| Crystal dupe window cache | `.agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-cases-window-crystal-queue-YYYYMMDD.json` |
| Crystal dupe report | `.agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-intra-duplicate-*-crystal-owned-YYYYMMDD.*` |

## Salesforce SOQL (open workload)

Resolve UserId once:

```sql
SELECT Id, Name, Email FROM User
WHERE Email = 'Crystal.Gagner@vixxo.com' AND IsActive = true
LIMIT 1
```

Counts (replace `{UID}`):

```sql
SELECT COUNT() FROM Case WHERE OwnerId = '{UID}' AND IsClosed = false
```

```sql
SELECT COUNT() FROM Lead WHERE OwnerId = '{UID}' AND IsConverted = false
```

```sql
SELECT COUNT() FROM Task WHERE OwnerId = '{UID}' AND IsClosed = false
```

Optional open Case sample (top 8 by last activity) — fallback only when
`case_types` is omitted:

```sql
SELECT Id, CaseNumber, Subject, Status, Priority, LastModifiedDate
FROM Case
WHERE OwnerId = '{UID}' AND IsClosed = false
ORDER BY LastModifiedDate DESC
LIMIT 8
```

### Open Cases by RecordType (required for HTML subsections)

Display label mapping: `Rate Negotiation` → **Rate Changes** (highest priority).
“New / not started” = `Status = 'New'`.

```sql
SELECT RecordType.Name, Status, COUNT(Id) cnt
FROM Case
WHERE OwnerId = '{UID}' AND IsClosed = false
GROUP BY RecordType.Name, Status
ORDER BY RecordType.Name, Status
```

```sql
SELECT RecordType.Name,
       COUNT(Id) new_count,
       MIN(CreatedDate) oldest_new,
       MAX(CreatedDate) newest_new
FROM Case
WHERE OwnerId = '{UID}' AND IsClosed = false AND Status = 'New'
GROUP BY RecordType.Name
```

Rate Changes detail (list all New; include non-New in summary only):

```sql
SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate, RecordType.Name
FROM Case
WHERE OwnerId = '{UID}' AND IsClosed = false
  AND RecordType.Name = 'Rate Negotiation'
ORDER BY Status ASC, CreatedDate ASC
```

### Full queue for Excel workbook

```sql
SELECT Id, CaseNumber, Subject, Status, Priority, Origin, Type,
       CreatedDate, LastModifiedDate, RecordType.Name,
       Account.Name, Account.Service_Provider_Number__c
FROM Case
WHERE OwnerId = '{UID}' AND IsClosed = false
ORDER BY CreatedDate ASC
```

Daily export (overwrites stable workbook + dated copy):

```bash
python .agents/skills/mothman-good-morning/scripts/export_sf_queue_workbook.py --json
```

Workbook layout:

| Sheet | Contents |
| --- | --- |
| Summary | Totals by type; type × status counts with oldest/newest/max age |
| All Cases | Full open queue: type → status → oldest CreatedDate |
| Rate Changes | Status banners; oldest first within each status |
| Service Provider Support | Same |
| Provider Onboarding | Same |
| Coverage Change | Same |

## Theme tokens (cryptid)

| Token | Hex | Use |
| --- | --- | --- |
| `--void` | `#0d0b14` | page background |
| `--plume` | `#1a1228` | card / panel |
| `--mist` | `#2a1f3d` | borders / secondary panels |
| `--ember` | `#e63e3e` | accent / eyes / CTAs |
| `--ember-dim` | `#a82828` | muted accent |
| `--lavender` | `#c4b5d8` | body text |
| `--moon` | `#f0e6f6` | headings |
| `--gold` | `#d4a84b` | rare highlights |
| `--ok` | `#6bcb8a` | positive / clear |
| `--warn` | `#e6b84a` | caution |
| `--danger` | `#e63e3e` | blockers |

Fonts: **Cinzel** (display) + **Nunito** (body) — same pairing as Celestia,
dark cryptid palette instead of lavender cream.

## Phase 2 cascade — Task overview SOQL

```sql
SELECT Id, Subject, Status, Priority, ActivityDate, CreatedDate,
       LastModifiedDate, WhatId, What.Type, What.Name, Description
FROM Task
WHERE OwnerId = '{UID}' AND IsClosed = false
ORDER BY ActivityDate ASC NULLS LAST, CreatedDate ASC
```

```bash
python .agents/skills/mothman-good-morning/scripts/export_sf_task_overview.py --json
```

## Phase 2 cascade — Crystal-owned duplicate review

Window cache should include sibling candidates (not Crystal-only). Typical
filter: open Cases where `CreatedDate` ≥ ~60 days ago AND
(`OwnerId = '{UID}'` OR `RecordType.Name` IN Rate Negotiation /
Service Provider Support). Save as
`sf-cases-window-crystal-queue-YYYYMMDD.json` under the duplicate-bridge
`.tmp` folder.

```bash
python .agents/skills/sp-fd-sf-duplicate-bridge/scripts/scan_crystal_owned_duplicates.py \
  --sf-cache .agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-cases-window-crystal-queue-YYYYMMDD.json \
  --date YYYYMMDD \
  --open
```

**Report-only** from Good Morning — no merge execute.

## Email briefing — folder ignore list

Case-insensitive `displayName` match (substring allowed where noted):

| Ignore | Notes |
| --- | --- |
| Templates | exact |
| Me | exact |
| Vixxo IT | exact |
| SP Docs | also `SP Docs/ Help Desk items` |
| VixxoLink | any folder name containing VixxoLink |
| Meeting Notes | exact |
| Claude & Mothman | exact |

Also skip Junk, Deleted Items, Conversation History, Sync Issues, Outbox,
Drafts, RSS* unless Crystal asks. **Always scan Inbox.** Keep **VM** available
for voicemail inventory (not on the ignore list).

## Related skills

- `morning-brief` — chat-oriented daily rundown (same data sources)
- `sf-case-email-sync` — mail scan + account audit scripts
- `sp-fd-sf-duplicate-bridge` — Phase 2 Crystal-owned duplicate scan
- `sp-voicemail-triage` — Phase 2 when voicemail inventory &gt; 0
- `daily-briefing` — lighter work-only brief when MCP is thin
