# SP Playbook KPIs (canonical)

Source: current SP performance goals provided 2026-05-13.

This file is the **authoritative KPI list** for the SP Performance Monitor.
Every other config in this skill — `export-schema.yaml`, `thresholds.yaml`,
the report template, the email template — must conform to the names,
definitions, and targets below. If the playbook changes, edit this file
first, then propagate.

## KPI table

| KPI | Definition | Target |
|---|---|---|
| **SLA Compliance Rate** | % of work orders completed within customer-required response and resolution windows | ≥ 85% |
| **First-Time Fix Rate** | % of WOs completed without a subsequent recall for the same issue | ≥ 90% |
| **Recall Rate** | % of completed WOs that generate a recall work order within 30 days | ≤ 5% |
| **Quote Turnaround Time (P0/P1)** | Hours from quote request/open to quote submission for P0 and P1 quote activity | ≤ 24 hours / 1 day |
| **VixxoLink Adoption Rate** | % of eligible work performed through VixxoLink by the service provider | ≥ 70% |
| **Invoice Rejection Rate** | % of submitted invoices rejected during the reporting window | ≤ 2% |

## Direction of breach

- **SLA Compliance, First-Time Fix, VixxoLink Adoption:** higher is better.
 Breach when the value is **below** the target.
- **Recall Rate, Quote Turnaround Time, Invoice Rejection:** lower is better.
 Breach when the value is **above** the target.

## Notes the skill enforces

- **Recall Rate** uses a 30-day lookback for the recall WO. The export must
 honor that window; if VixxoLens uses a different lookback the schema diff
 will surface it at validation time.
- **Quote Turnaround Time** applies only to P0 and P1 quote activity. If the
 export cannot isolate P0/P1 quote turnaround, the skill must surface a schema
 or calibration gap instead of scoring all-priority quote turnaround.
- **SLA Compliance** replaces the older `response_time_hours_avg` signal.
 Average response time is a component of SLA, not a separate KPI. The
 playbook treats SLA as the consolidated measure.

## Mapping from the prior (pre-playbook) schema

| Prior column | Playbook KPI | Action |
|---|---|---|
| `response_time` (hours) | — (subsumed by SLA Compliance) | removed |
| `first_time_fix` | First-Time Fix Rate | retained, target 85% → 90% |
| `callback_rate` | Recall Rate | renamed (alias kept), target ≤ 5% over 30d |
| `nte_compliance` | — | removed from current goal set |
| — | SLA Compliance Rate | new |
| — | Quote Turnaround Time (P0/P1) | new, target ≤ 24 hours / 1 day |
| — | VixxoLink Adoption Rate | new, target ≥ 70% |
| — | Invoice Rejection Rate | new, target ≤ 2% |
