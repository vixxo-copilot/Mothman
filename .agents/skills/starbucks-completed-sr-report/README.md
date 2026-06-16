# Starbucks Completed SR Report

Regional report of **completed Starbucks Service Requests** from VixxoLink,
with **time in**, **time out**, **job complete**, and **within SLA** on every
SR. Groups results by B&G Tech operational region.

## When to use

- "Run starbucks-completed-sr-report"
- "Starbucks completed SRs by region"
- "Show completed Starbucks work with time in, time out, and SLA status"
- "Which Starbucks SRs missed SLA last week?"

## Requirements

- Cursor workspace with this assistant repo
- **VixxoLink MCP** connected and authenticated

## Example prompts

```
Run starbucks-completed-sr-report for the last 7 days.
Include time in, time out, job complete, and within SLA. Group by region.
```

```
Starbucks completed SR report — last 24 hours, 811 only, outside SLA only.
```

## Output

1. Executive summary — SR counts by region, SLA breakdown, priority bands
2. Per-region detail tables — SR #, times, job complete, within SLA, site, SP
3. Notes — window, truncation, data caveats

## Files

- `SKILL.md` — full workflow
- `sep-time-enrichment.md` — SEP `/times` extraction and SLA rules
- `regions.md` — B&G Tech region assignment
- `metadata.yaml` — skill registry
