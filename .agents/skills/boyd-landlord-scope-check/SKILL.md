---
name: boyd-landlord-scope-check
description: Checks BOYD/Gerber VixxoLink service requests against the monthly Landlord-Tenant Responsibility Report and VKS lease-review SOPs to decide whether a work scope is tenant-responsible, landlord-responsible, pass-through, or requires lease review. Use when the user asks about BOYD landlord check, landlord vs tenant responsibility, VKS lease review, BYD01 SR scope, or whether BOYD work is in scope.
---

# BOYD Landlord Scope Check

## Purpose

Use this skill to evaluate BOYD/Gerber service requests before dispatch from `BYD_LLDREV` or similar landlord-review queues.

Adopt the evaluation posture of a tenant-side real estate attorney or lease expert representing Boyd/Gerber. Read the lease evidence conservatively for the tenant: do not volunteer tenant responsibility unless the workbook and cited lease language clearly support it. When the lease is silent, mixed, approval-based, or ambiguous, recommend lease review / landlord approval rather than clean dispatch.

The monthly workbook is the first source of truth:
`~/Downloads/Landlord-Tenant Responsibility Report.XLSX`

The current extracted cache is:
`data/responsibility_report.csv`

## Workflow

1. Identify the SR details in VixxoLink using a fixed evidence sequence:
   - customer `BYD01`
   - site number, usually `CC######`
   - site address/city/state when available
   - line of service, short description, and full request description
   - priority, especially whether it is `P1 - Emergency`
   - current status/substatus
   - quote/work description when the SR is quote-related

   Required call backbone for diagnostic runs:
   1. Fetch SR details by SR number.
   2. Search the SR number with `summary:false` to get full site number/address when the detail endpoint omits them. Use the VixxoLink `site.addressLineOne`, `site.city`, `site.state`, and `site.zipcode` values as the address fallback for the checker.
   3. Fetch Gateway SR / quote scope when status or substatus includes `Quote`, `Quoted`, `Submitted`, `Customer Review`, or `Declined`.
   4. Run the checker by site number.
   5. Run the checker by address when address is available. Address fallback should use fuzzy matching against the lease report despite punctuation, ZIP, country, street-suffix, abbreviation, or joined/split street-name differences. If site number matches but address fails, treat the address failure as a normalization defect to fix, not as missing-site evidence.
   6. If the checker reports a missing site, verify the extracted CSV and source XLSX search evidence before finalizing.

2. Run the checker:

```bash
python3 .cursor/skills/boyd-landlord-scope-check/scripts/check_scope.py --site CC123011 --scope "Exterior Painting" --sr 1-6563589332
```

3. If the workbook was updated this month, refresh the extract first:

```bash
python3 .cursor/skills/boyd-landlord-scope-check/scripts/extract_report.py --workbook "$HOME/Downloads/Landlord-Tenant Responsibility Report.XLSX"
```

   For multi-agent diagnostics, refresh the workbook once before launching subagents and record the metadata. All runs should use the same extracted CSV so run differences reflect reasoning/call-path drift, not data timing.

4. Interpret the result:
   - `tenant_responsible`: Boyd/Vixxo appears responsible. Move from `BYD_LLDREV` to `BYD_TL01` unless a pass-through rule applies.
   - `landlord_responsible`: reassign to `BYD_LLD`, set spend category `Landlord`, and follow landlord dispatch SOP.
   - `lease_review_required`: do not assume tenant responsibility. Use CoStar / lease abstract review and Boyd LL Request Admin if needed.
   - `pass_through_direct_dispatch`: non-P1 HVAC, FLS, roofing, or paving may bypass Boyd Team Lead to named pass-through providers if the report does not point to landlord responsibility.

## Decision Rules

- The workbook beats generic norms when there is an exact site + repair-item match.
- Treat `Lease Is Silent`, `LL/Ten`, blanks, or mixed language as `lease_review_required`, not clean tenant responsibility.
- Escalate exterior, shared/common, structural, below-grade, capital replacement, new electrical-run, full-building, parking, roofing, exterior painting, or signage scopes for lease review even when the initial request seems simple.
- Escalate substantial quote-scope expansion for lease review. If the intake sounds minor but the quote/work description includes exterior fixtures, wall packs, pole lights, high bays, demolition/replacement of many fixtures, panel/switch work, or possible new electrical work, cite that expanded scope and hold for lease review unless the workbook clearly supports tenant responsibility.
- When the checker returns `diagnostic_code: site_not_found_in_responsibility_report`, treat the operational recommendation as `lease_review_required`. The root cause is a workbook/site-mapping gap, not tenant or landlord responsibility. Do not move to `BYD_TL01` or `BYD_LLD` until CoStar, the lease abstract, or a corrected workbook row establishes responsibility.
- For `P1 - Emergency` landlord-responsible tickets, call the landlord and send the emergency email. If no landlord or Boyd regional response within 4 hours, Vixxo stops further follow-up and the Boyd regional manager owns completion notification.
- Always cite the workbook row: site, client lease ID, repair item, responsible party, reimbursable by, and the lease citation/comments that support the assessment.

## Response Standard

When responding to the user, include:

- recommendation and confidence
- diagnostic code when present
- site, address, client lease ID, repair item, responsible party, and reimbursable by
- quote/work-description scope if quote-related
- report metadata: extracted CSV path/time and source workbook path/time when available
- missing-site search evidence when applicable: searched site identifiers, searched address terms, CSV match count, source XLSX match count
- tenant-side lease expert assessment
- lease citation: quote or summarize the specific lease section/page language from `Repairs - Comments`
- operational next action

Do not just say "tenant" or "landlord." Explain how the cited lease language drove the conclusion.

## Supporting References

- Procedure summary: [PROCEDURES.md](PROCEDURES.md)
- Extracted workbook cache: [data/responsibility_report.csv](data/responsibility_report.csv)
- Report metadata and source paths: [data/report_metadata.json](data/report_metadata.json)
