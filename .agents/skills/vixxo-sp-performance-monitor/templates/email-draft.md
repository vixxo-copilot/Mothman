# Outlook draft body — VIXXO-sp-performance-monitor

<!--
Rendering: HTML body preferred for Outlook so severity headings and KPI tables
land clean. The skill inlines the Markdown report produced from
`templates/sp-performance-report.md` into the {{report_body}} placeholder.
Recipients resolve from `config/recipients.yaml` via the M365 directory.
Send policy: draft_only — do NOT send without explicit user approval.
-->

**To:** {{recipients_to}}
**Cc:** {{recipients_cc}}
**Bcc:** {{recipients_bcc}}
**Subject:** {{subject_line}}

---

Hi team,

Here's the at-risk SP check for the 45 days ending **{{window_end}}**, drawn from the latest VixxoLens export (`{{source_filename}}`).

**Headline numbers**

- Critical: {{critical_count}}
- Warning: {{warning_count}}
- Watch: {{watch_count}}
- SPs scored: {{scored_count}} (active-SP floor {{min_jobs_45d}} jobs)

**Top 3 critical SPs**

1. {{top_critical_1}}
2. {{top_critical_2}}
3. {{top_critical_3}}

The full report is below with per-SP KPI tables, flag reasons, top-customer context, and a suggested action for each critical SP. Warning and watch lists follow.

{{report_body}}

---

A few notes on method so we stay aligned:

- Detection is hybrid — threshold breach on the KPI **or** degradation vs the prior 45-day window beyond the configured delta. Severity escalates to *critical* when both fire on the same KPI.
- Thresholds and trend deltas live in `config/thresholds.yaml` and are tuned after each run (see Linear [AIA-466](https://linear.app/vixxo/issue/AIA-466)).
- v2 will replace the manual VixxoLens export with an automated pull — tracked in [AIA-486](https://linear.app/vixxo/issue/AIA-486). Until then, the run depends on someone exporting the report and dropping the file in `memory/sp-performance/_inbox/`.

Questions, disagreements, or SPs you think we should re-weigh — reply here and I'll roll it into the next calibration pass.

Thanks,
Maria

<!-- per outbound-messaging-guardrail: no AI sign-off on email. This is an email,
     not a Teams message, so Maria's Outlook signature handles the close. -->
