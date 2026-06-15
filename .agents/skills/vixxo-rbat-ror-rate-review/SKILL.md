---
name: vixxo-rbat-ror-rate-review
description: Reviews the weekly Vixxo Finance "Rate issues - RBAT to ROR" Excel report, extracts suspected service-provider rate mismatches, and validates each mismatch against Gateway/ORMB invoice, SR, labor, travel, and rate-card evidence. Use when the user mentions RBAT to ROR, rate issues, rate mismatch reports, SP rate mismatches, ORMB rate validation, or asks to review the weekly MCD Finance rate issue workbook.
---

# VIXXO RBAT to ROR Rate Review

Use this skill to review the weekly Finance rate issue workbook and validate
whether each reported SP rate mismatch is supported by Gateway/ORMB evidence.

Default to **dry run**. Do not update Gateway, ORMB, Freshdesk, email, Teams, or
the workbook unless the operator explicitly approves the exact write-back.

## Inputs

Primary input is an Excel workbook like:

`Rate issues - RBAT to ROR 5-7-2026.xlsx`

Expected workbook shape:

- Detail sheet, usually `Sheet1`, with one row per invoice/SR mismatch.
- Summary sheet, usually `Sheet2`, with pivot counts by owner and aging band.
- Key detail columns: `Billing Reference Number`, `VIID`, `Customer Site-Customer Number`,
  `Customer Site-Customer Name`, `Invoice Status`, `Audit Failures`, `SP Total`,
  `Invoice Hdr-Gross Margin`, `Service Provider Name`, `SR Number`, `Line of Service`,
  `Short Description`, `Assigned to`, `status`, `comments`, `Categorized comments`,
  `Action Item`, `Suggestion`, and follow-up date columns.

Use this review template after the original Finance workbook is available:

`/Users/mclavijo/Downloads/05.14.2026 Rate Issues - Vanessa & Maria.xlsx`

The template workbook contains a working sheet named
`Rate Issues -  Vanessa & Maria` and a `Query` sheet. Preserve the downloaded
template as read-only source material; write any populated copy under
`.tmp/rbat-ror-rate-review/`.

## Quick Start

1. Run the helper to normalize the report and extract rate candidates:

   ```bash
   python3 .cursor/skills/VIXXO-rbat-ror-rate-review/scripts/extract_rate_issues.py "<workbook.xlsx>" --out .tmp/rbat-ror-rate-review
   ```

2. Populate the Vanessa/Maria review template from the original Finance file:
   - Start from `/Users/mclavijo/Downloads/05.14.2026 Rate Issues - Vanessa & Maria.xlsx`.
   - Save a dated working copy under `.tmp/rbat-ror-rate-review/`; do not
     overwrite the file in Downloads.
   - Populate the `Rate Issues -  Vanessa & Maria` sheet by matching original
     rows on `VIID` / `Billing Reference Number` and `SR Number`.
   - Carry forward the operational fields needed for review: `SP Name`, `SP#`,
     `SR#`, `VIID`, `Client #`, geography, priority, `LOS`, work date/day,
     work-hour classification, site visit count, technician count, labor/OT/
     travel amounts, quantities and rates, `AP Amount`, and `Last Comment`.
   - Leave `Research Notes`, `Reco`, and `Comments` blank until Gateway/ORMB
     validation is complete.

3. Prioritize rows with:
   - `status` = `Open`
   - `Categorized comments` = `Rate issues - RBAT to ROR`
   - negative or low `Invoice Hdr-Gross Margin`
   - oldest `Rec Days` / `Sev Days`
   - repeated provider/customer/LOS patterns

4. For each row, validate against Gateway/ORMB before deciding whether the
   report is correct.

## Gateway / ORMB Validation

Before calling any MCP tool, read that tool's JSON descriptor from:

`/Users/mclavijo/.cursor/projects/Users-mclavijo-Documents-Dev-HABLADORA/mcps/project-0-HABLADORA-gateway/tools/`

Use Gateway read tools only unless the operator approves a write. Common reads:

- `gateway_get_service_request` for SR context, customer, provider, LOS/SD, NTE,
  quote linkage, work dates, and dispatch details.
- `gateway_search_invoices` and `gateway_get_invoice` for invoice header/status.
- `gateway_get_invoice_lineitems` for billed labor/travel/material lines,
  quantities, rates, audit failures, and ORMB-calculated amounts.
- `gateway_list_sp_labor_types`, `gateway_list_labor_types`, and
  `gateway_list_sp_markup` when rate-card/labor setup is needed.
- Approved quote tools when a quote controls the rate or invoice amount.

If MCP output is insufficient, use the Gateway/ORMB UI pages and capture the
same facts manually. Do not rely on the spreadsheet comment alone.

## Per-Row Decision Logic

For each mismatch row:

1. Match the report row to Gateway by `SR Number`, `VIID` / `Billing Reference Number`,
   provider name, customer number, LOS/SD, and service date.
2. Extract the reported rate comparison from `comments`:
   - billed rate, e.g. `$95 labor rate`
   - expected contract/rate-card rate, e.g. `rate card $75`
   - rate type: `labor`, `travel`, `trip`, `helper`, `OT`, material/markup, or unknown
3. Pull the invoice line items and identify the line that generated the audit failure.
4. Compare billed invoice rate vs ORMB-calculated rate vs SP contract/rate-card rate.
5. Check whether a valid exception explains the difference:
   - approved quote controls the invoice
   - emergency/after-hours/OT labor type applies
   - travel/trip rate differs from labor rate
   - site/customer-specific rate override
   - tax, material markup, minimum charge, or bundled line
   - stale or incorrect provider/rate-card setup
   - spreadsheet comment references the wrong rate type or wrong provider
6. Classify the row.

Do not close or clear any row from the spreadsheet comment alone. The comment is
often copied from invoice-hold text and can hide the real disposition: provider
overbilling, rate-card setup, accepted emergency/OT rate, flat fee, duplicate
travel, SP/client NTE, quote control, or invoice-line coding.

For full-workbook reviews, process rows in chunks of roughly 20-30 rows and
write one chunk report per batch under `.tmp/rbat-ror-rate-review/`. Each chunk
must include Gateway/ORMB evidence, classification, recommended action, and
summary counts. Consolidate the chunks into the main results file when complete.

## Classification

- `confirmed-mismatch`: billed rate exceeds the applicable Gateway/ORMB rate and
  no valid exception is visible.
- `valid-rate`: Gateway/ORMB supports the billed rate or approved quote amount.
- `wrong-rate-type`: report compares labor vs travel/trip/OT/helper/material.
- `rate-card-setup-issue`: ORMB or Gateway rate setup appears stale/missing.
- `invoice-line-issue`: invoice line item is miscoded, duplicated, or quantity/rate
  is entered incorrectly.
- `quote-or-approval-controlled`: approved quote/NTE/approval supports the amount.
- `insufficient-evidence`: Gateway/ORMB evidence is missing or ambiguous.
- `not-found`: SR or invoice cannot be located from report identifiers.

## Known Patterns

Use these patterns to avoid false closure:

- `confirmed-mismatch`: ORMB-calculated unit price is lower than SP unit price,
  invoice-hold/audit text repeats the mismatch, and no approved exception,
  emergency/OT, quote, flat-fee, or rate-update evidence is visible.
- `rate-card-setup-issue`: provider notes cite "new rate", MSA, service
  agreement, contracted rate, non-aquatics rate, distance/trip schedule, or
  similar, but ORMB/Gateway setup still shows a lower rate or cannot validate.
- `invoice-line-issue`: provider entered a total as the unit rate, labor/trip is
  coded as an expense, a replacement/rejected invoice exists, BUC/duplicate
  context is present, or labor hours exceed on-site time.
- `valid-rate`: accepted tier travel, emergency/out-of-area rate, approved
  payrate, flat fee, or other Gateway evidence supports the billed amount.
- `wrong-rate-type`: the report compares a regular rate against OT, emergency,
  helper, second-tech, flat-fee, expense, trip, blended regular+OT, or customer
  pricing.
- `quote-or-approval-controlled`: approved quote or explicit approval controls
  the invoice better than the spreadsheet's rate-card comparison.

## Output Format

For batch reviews, report:

```markdown
# RBAT to ROR Rate Review

Workbook: <path>
Rows reviewed: <N>
Writes performed: none

## Executive Summary
- Confirmed mismatches: <N>
- Valid rates / false positives: <N>
- Setup issues: <N>
- Needs manual review: <N>

## Findings
| SR | Invoice | Customer | Provider | LOS/SD | Reported issue | Gateway/ORMB evidence | Classification | Recommended action |
|---|---|---|---|---|---|---|---|---|

## Patterns
- <provider/customer/rate type pattern>

## Operator Decisions Needed
- <row/SR>: <decision needed>

## Detail Reports
- <chunk report paths if chunking was used>
```

For single-row deep dives, include the exact report row fields, Gateway/ORMB
evidence, classification, and recommended action.

## Write-Back Protocol

If the operator asks to update the workbook or send follow-up:

1. Present the exact update text or outbound draft first.
2. Wait for explicit approval.
3. Preserve the original workbook; write a dated reviewed copy under `.tmp/`.
4. For outbound email or Teams, follow the workspace draft-then-approve rules.
