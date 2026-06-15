---
name: vixxo-hvacr-cbsa-coverage-builder
description: Builds VixxoLink-ready Florida HVACR coverage from the HVACR bid workbook, site export, active LOS/SD export, and active Siebel SP export. Use when the user asks to build FL HVACR coverage, HVACR RFP coverage, CBSA-balanced HVACR ranks, or SP Numbers coverage for MCD HVACR work.
---

# VIXXO HVACR CBSA Coverage Builder

Builds Florida HVACR coverage from four files:

1. **HVACR bid workbook** with CBSA/provider optimized annual volume and `Work History`.
2. **MCD site export** containing `Customer #`, `Site #`, `Site Id`, address, ZIP, county, and status.
3. **Active LOS/SD export** containing customer `NAME`, `LOS`, and `SHORT_DESCRIPTION`.
4. **Active Siebel SP export** containing `Service Contractor #` and `Service Contractor Name`.
5. Optional **Customer SC relationship export** containing current coverage by `LOS`, `Short Description`, and `Rank 1`..`Rank 9`.

## Default Inputs

- HVACR bid workbook: `/Users/mclavijo/Downloads/FL HVACR Bid Analysis_for Claude.xlsx`
- Site export: `/Users/mclavijo/Downloads/output (3).csv`
- Active LOS/SD export: `/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/LOS_SD_Export_of_Active_Accounts.xlsx`
- Active Siebel SP export: `/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/5.19ActiveSiebelSPs.xlsm`
- Output folder: `/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage`

## How To Run

Use the bundled wrapper:

```bash
python3 .cursor/skills/VIXXO-hvacr-cbsa-coverage-builder/scripts/build_hvacr_cbsa_coverage.py \
  --output "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage/HVACR_CBSA_Coverage.xlsx" \
  --summary "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage/HVACR_CBSA_Coverage_summary.md"
```

Dependency: `openpyxl`.

## Build Rules

- Use the workbook sheet that contains `CBSA`, `Service Provider`, and optimized assigned volume as the source of provider recommendations.
- Use only providers where optimized assigned volume is greater than zero.
- Resolve each recommended provider to an active Siebel `Service Contractor #`.
- When multiple recommended/provider-name variants resolve to the same active Siebel `Service Contractor #` in the same CBSA, collapse them to one provider row, use one consistent Siebel display name, and sum the optimized target volume before balancing ranks.
- Run the shared CBSA builder with `--area "HVAC"` because the FL workbook's work-history area is `HVAC`.
- Use `SD = HVACR` when active/work-history SD is unavailable.
- Exclude formula-like compound customer rows from the site export by default before building coverage.
- Emit one load row for each eligible `(Customer #, Site ID, HVAC, SD)` combination.
- Resolve site CBSA using this order:
  - exact HVAC work-history site signal;
  - HVAC work-history ZIP;
  - any work-history ZIP;
  - any work-history city/state;
  - limited fallback from target counties to target CBSAs.
- Balance R1 within each CBSA by assigning each site to the provider with the lowest assigned-volume-to-target-volume ratio.
- Fill `R2`..`R6` with the remaining nonzero target-volume providers for that CBSA, then use current coverage as backup ranks to fill remaining slots when existing coverage is supplied.
- Compact rank gaps left before writing output.
- When existing coverage has no proposed replacement, carry the current ranks forward into `SP Numbers` and mark the row `current_only_preserved` in `coverage review` so a load does not remove coverage.
- Do not emit blank or partial proposed rows. Every proposed load/review row must have `Customer #`, `Site ID`, `State`, `CBSA`, `LOS`, `SD`, and at least `R1`; otherwise skip it and count it in the summary.

## Quality Gate

Before sharing the workbook for SPM review:

- Open `SP Numbers`, `account review`, and `coverage review` if present and confirm there are no fully empty rows, no proposed ranks on rows missing customer/site/CBSA/state/LOS context, no rows with missing CBSA outside `site exceptions`, and no rows where both current ranks and proposed ranks are empty.
- Confirm no proposed rank gaps exist after compaction.
- Treat any nonzero skipped-row count in the summary as a review item.
- Have Chris H review the workbook before sending it to SPM when the output has site exceptions, unresolved recommended providers, skipped rows, or any default `SD = HVACR` assignments.

## Output Workbook

The script writes:

- `SP Numbers`: load-ready `Customer #`, `Site ID`, `LOS`, `SD`, `R1`..`R6`.
- `account review`: same rows with site details, CBSA source, estimated volume, SP numbers, SP names, and combined `SP # : SP Name` reporting columns.
- `new coverage summary`: recommended-provider uptake by CBSA/SP, including optimized target volume, R1 site count, R1 estimated volume, R1 coverage rows, backup-rank appearances, and whether the recommendation appears in new coverage.
- `site assignment review`: one row per covered site showing the site-level R1 assignment and whether LOS/SD came from active LOS/SD, work history, or default CBSA coverage.
- `site exceptions`: active HVAC sites that could not be covered because the CBSA was unresolved or had no target providers.
- `provider resolution`: recommended provider names and their resolved Siebel SP numbers.
- `coverage review`: side-by-side team review of current `existing coverage` and proposed `account review`, matched by `Customer #` + `Site ID` + `LOS` + `SD` when an existing coverage export is supplied.
- `existing coverage`: current HVAC rows from the Customer SC relationship export when supplied.

## Expected User Summary

Always report:

- output workbook path;
- summary markdown path;
- covered sites and exception sites;
- coverage rows written;
- side-by-side coverage review rows written;
- coverage review status counts for matched, current-only preserved, and proposed-only rows;
- matched rows split by unchanged vs changed R1-R6 rank order;
- existing coverage rows imported;
- skipped existing/proposed rows from the quality gate;
- unresolved recommended providers;
- R1 assignment counts by CBSA/provider;
- any site exceptions that need business review.
