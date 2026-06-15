---
name: vixxo-handyman-cbsa-coverage-builder
description: Builds VixxoLink-ready Colorado Handyman coverage from the Handyman CBSA recommendation workbook, MCD site export, active LOS/SD export, and active Siebel SP export. Use when the user asks to build Handyman coverage, Colorado Handyman RFP coverage, CBSA-balanced Handyman ranks, or SP Numbers coverage for MCD Handyman work.
---

# VIXXO Handyman CBSA Coverage Builder

Builds Colorado Handyman coverage from four files:

1. **Handyman RFP workbook** with CBSA/provider optimized annual volume and `Work History`.
2. **MCD site export** containing `Customer #`, `Site #`, `Site Id`, address, ZIP, county, and status.
3. **Active LOS/SD export** containing customer `NAME`, `LOS`, and `SHORT_DESCRIPTION`.
4. **Active Siebel SP export** containing `Service Contractor #` and `Service Contractor Name`.
5. Optional **Customer SC relationship export** containing current coverage by `LOS`, `Short Description`, and `Rank 1`..`Rank 9`.

## Default Inputs

- Handyman RFP workbook: `/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage/CO Handyman_RFP Analysis_V3 Remove small markets 05 11 2026_Final for Claude.xlsx`
- Site export: `/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage/mcd-electrical-site-export-output-2026-05-11.csv`
- Active LOS/SD export: `/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/LOS_SD_Export_of_Active_Accounts.xlsx`
- Active Siebel SP export: `/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/Active Siebel 5-7.xlsm`
- Customer SC relationship export: `/Users/mclavijo/Downloads/OPS 10502 Customer SC Relationships.xlsx`

## How To Run

Use the bundled wrapper:

```bash
python3 .cursor/skills/VIXXO-handyman-cbsa-coverage-builder/scripts/build_handyman_cbsa_coverage.py \
  --existing-coverage "/Users/mclavijo/Downloads/OPS 10502 Customer SC Relationships.xlsx" \
  --output ".tmp/mcd-handyman-coverage/mcd-handyman-cbsa-coverage.xlsx" \
  --summary ".tmp/mcd-handyman-coverage/mcd-handyman-cbsa-coverage-summary.md"
```

Dependency: `openpyxl`.

## Build Rules

- Use the workbook sheet that contains `CBSA`, `Service Provider`, and optimized assigned volume as the source of provider recommendations.
- Use only providers where optimized assigned volume is greater than zero.
- Resolve each recommended provider to an active Siebel `Service Contractor #`.
- When multiple recommended/provider-name variants resolve to the same active Siebel `Service Contractor #` in the same CBSA, collapse them to one provider row, use one consistent Siebel display name, and sum the optimized target volume before balancing ranks.
- Include active customer sites when they have either active `LOS = Handyman` rows in the LOS/SD export or matching Handyman work-history evidence.
- If the active LOS/SD export lacks Handyman for a customer, infer `Handyman` SD values from the work-history `Category` values for that exact customer/site first, then customer-level Handyman history.
- If no active LOS/SD or Handyman work-history category exists, still assign coverage by resolved CBSA recommendation and emit `SD = ALL`.
- Emit one load row for each eligible `(Customer #, Site ID, Handyman, SD)` combination.
- Resolve site CBSA using this order:
  - exact Handyman work-history site signal;
  - Handyman work-history ZIP;
  - any work-history ZIP;
  - any work-history city/state;
  - limited fallback from target Colorado counties to target CBSAs.
- Balance R1 within each CBSA by assigning each site to the provider with the lowest assigned-volume-to-target-volume ratio.
- Fill `R2`..`R6` with the remaining nonzero target-volume providers for that CBSA, then use current coverage as backup ranks to fill remaining slots when existing coverage is supplied.
- Compact rank gaps left before writing output. If ranks are `R1`, `R2`, `R3`, and `R5`, the `R5` provider moves to `R4`.
- When `--existing-coverage` is passed, add current Handyman coverage from the Customer SC relationship export for side-by-side review.
- When existing coverage has no proposed replacement, carry the current ranks forward into `SP Numbers` and mark the row `current_only_preserved` in `coverage review` so a load does not remove coverage.
- Do not emit blank or partial proposed rows. Every proposed load/review row must have `Customer #`, `Site ID`, `State`, `CBSA`, `LOS`, `SD`, and at least `R1`; otherwise skip it and count it in the summary.
- Do not import current-coverage rows that have no rank values or are missing the customer/site key.
- In `coverage review`, carry the customer/site/CBSA/state/LOS/SD context into unmatched current-only or proposed-only rows so ranks never appear beside an otherwise blank row.
- In `coverage review`, do not add a blank separator column between current and proposed ranks. Do not repeat proposed context columns that duplicate current context. Show proposed ranks only as combined `Proposed R# SP # and Name` columns.

## Quality Gate

Before sharing the workbook for SPM review:

- Open `SP Numbers`, `account review`, and `coverage review` and confirm there are no fully empty rows, no proposed ranks on rows missing customer/site/CBSA/state/LOS context, no rows with missing CBSA outside `site exceptions`, and no rows where both current ranks and proposed ranks are empty.
- Confirm `coverage review` filters across all columns with no blank separator between current ranks and proposed ranks.
- Confirm no proposed rank gaps exist after compaction.
- Treat any nonzero skipped-row count in the summary as a review item. Explain why the skipped rows are acceptable or rerun with corrected inputs.
- Have Chris H review the workbook before sending it to SPM when the output has site exceptions, unresolved recommended providers, skipped rows, or any default `SD = ALL` assignments.

## Output Workbook

The script writes:

- `SP Numbers`: load-ready `Customer #`, `Site ID`, `LOS`, `SD`, `R1`..`R6`.
- `account review`: same rows with site details, CBSA source, estimated volume, SP numbers, SP names, and combined `SP # : SP Name` reporting columns.
- `new coverage summary`: recommended-provider uptake by CBSA/SP, including optimized target volume, R1 site count, R1 estimated volume, R1 coverage rows, backup-rank appearances, and whether the recommendation appears in new coverage.
- `site assignment review`: one row per covered site showing the site-level R1 assignment.
- `site exceptions`: active Handyman sites that could not be covered because the CBSA was unresolved or had no target providers.
- `provider resolution`: recommended provider names and their resolved Siebel SP numbers.
- `coverage review`: side-by-side team review of current `existing coverage` and proposed `account review`, matched by `Customer #` + `Site ID` + `LOS` + `SD` with status values for matched, current-only, and proposed-only rows.
- `existing coverage`: current Handyman rows from the Customer SC relationship export when supplied.

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
