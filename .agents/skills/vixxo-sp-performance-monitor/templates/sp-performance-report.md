# SP Performance Monitor — {{window_end}}

**Window:** {{window_start}} → {{window_end}} (current 45d) vs {{prior_window_start}} → {{prior_window_end}} (prior 45d)
**Source export:** `{{source_filename}}`
**Ingested at:** {{ingest_timestamp}}
**Active-SP floor:** ≥ {{min_jobs_45d}} jobs in current window
**SPs scored:** {{scored_count}} (of {{total_sp_count}} in export; {{dropped_for_volume}} dropped for low volume)

---

## 1. Executive summary

| Severity    | Count              |
|-------------|--------------------|
| Critical    | {{critical_count}} |
| Warning     | {{warning_count}}  |
| Watch       | {{watch_count}}    |

**Top 3 critical SPs**

1. {{top_critical_1}}
2. {{top_critical_2}}
3. {{top_critical_3}}

{{calibration_gaps_block}}

---

## 2. Critical SPs

> Threshold breached **and** trend degraded. Prioritize intervention this week.

{{#each critical_sps}}
### {{sp_name}}{{#if sp_id}} (`{{sp_id}}`){{/if}}

- **Region / Category:** {{region}} · {{category}}
- **Top customer by current-window volume:** {{top_customer}} ({{top_customer_jobs}} jobs)
- **Flag reasons:** {{reasons}}

| KPI                          | Current 45d        | Prior 45d           | Delta              | Playbook target          |
|------------------------------|--------------------|---------------------|--------------------|--------------------------|
| SLA Compliance               | {{sla_cur}}%       | {{sla_prev}}%       | {{sla_delta}}      | ≥ {{sla_thr}}%           |
| First-Time Fix               | {{ftf_cur}}%       | {{ftf_prev}}%       | {{ftf_delta}}      | ≥ {{ftf_thr}}%           |
| Recall Rate (30d)            | {{recall_cur}}%    | {{recall_prev}}%    | {{recall_delta}}   | ≤ {{recall_thr}}%        |
| Quote Turnaround (P0/P1)     | {{quote_tat_cur}}h | {{quote_tat_prev}}h | {{quote_tat_delta}}| ≤ {{quote_tat_thr}}h     |
| VixxoLink Adoption           | {{vl_adoption_cur}}% | {{vl_adoption_prev}}% | {{vl_adoption_delta}} | ≥ {{vl_adoption_thr}}% |
| Invoice Rejection            | {{invoice_rej_cur}}% | {{invoice_rej_prev}}% | {{invoice_rej_delta}} | ≤ {{invoice_rej_thr}}% |
| WOs Completed (count, +/-)   | {{wo_cur}}         | {{wo_prev}}         | {{wo_delta}}       | informational            |

**Suggested action:** {{suggested_action}}

{{/each}}

---

## 3. Warning SPs

> Threshold breach OR trend degraded at ≥ 1.5× the configured delta. Review and decide.

{{#each warning_sps}}
- **{{sp_name}}**{{#if sp_id}} (`{{sp_id}}`){{/if}} — {{region}} · {{category}} — {{reasons}}
  - SLA {{sla_cur}}% (was {{sla_prev}}%) · FTF {{ftf_cur}}% (was {{ftf_prev}}%) · Recall {{recall_cur}}% (was {{recall_prev}}%) · Quote TAT {{quote_tat_cur}}h (was {{quote_tat_prev}}h) · VixxoLink {{vl_adoption_cur}}% (was {{vl_adoption_prev}}%) · Invoice Reject {{invoice_rej_cur}}% (was {{invoice_rej_prev}}%)
{{/each}}

---

## 4. Watch list

> Trend degraded at the configured delta only; no threshold breach. Monitor next cycle.

{{#each watch_sps}}
- **{{sp_name}}**{{#if sp_id}} (`{{sp_id}}`){{/if}} — {{triggering_metric}} ({{triggering_delta}})
{{/each}}

---

## 5. Methodology

- **Detection model:** hybrid — threshold breach OR 45-day trend degradation (see `config/thresholds.yaml`).
- **KPI source of truth:** SP Playbook (`references/sp-playbook-kpis.md`).
- **Window:** trailing 45 days ending {{window_end}}, compared to the prior 45 days ending {{prior_window_end}}.
- **Active-SP filter:** `min_jobs_45d = {{min_jobs_45d}}`.
- **Playbook thresholds applied:** SLA ≥ {{sla_thr}}%, FTF ≥ {{ftf_thr}}%, Recall ≤ {{recall_thr}}% (30d), Quote Turnaround P0/P1 ≤ {{quote_tat_thr}} hours, VixxoLink Adoption ≥ {{vl_adoption_thr}}%, Invoice Rejection ≤ {{invoice_rej_thr}}%.
- **Trend deltas applied:** SLA −{{sla_delta_cfg}} pts, FTF −{{ftf_delta_cfg}} pts, Recall +{{recall_delta_cfg}}%, Quote TAT +{{quote_tat_delta_cfg}}%, VixxoLink Adoption −{{vl_adoption_delta_cfg}} pts, Invoice Rejection +{{invoice_rej_delta_cfg}}%.
- **Source export:** `{{source_filename}}` (ingested {{ingest_timestamp}}).
- **Raw capture:** `memory/sp-performance/{{run_date}}/raw/`.
- **Skill:** `.agents/skills/VIXXO-sp-performance-monitor/` (v1 file-ingest, schema v2 playbook-aligned; v2 automation tracked in [AIA-486](https://linear.app/vixxo/issue/AIA-486)).
