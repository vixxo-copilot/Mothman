# PM survey quality rubric (trade-agnostic)

This rubric scores any PM survey on three dimensions: **data completeness**,
**before/after photo coverage and quality**, and **additional-repairs
detection**. It runs for every trade. Load a `trades/<trade>.md` checklist on
top of it when one exists (see "Trade extension point"); otherwise use
[`trades/generic.md`](./trades/generic.md). The generic rubric below always
applies.

Score each dimension, then map to the Field 1 verdict using the rollup at the
bottom. Always quote the survey's own words or name the specific photo as
evidence — never assert a score without it.

## Dimension 1 — Data completeness

A PM survey is a record. These fields must be present and populated. Mark each
`present`, `partial`, or `missing`.

| Field | What to check |
|---|---|
| Asset identity | Asset id / tag, or make + model + serial. Generic descriptions ("rooftop unit") without an id are `partial`. |
| Site + date | Site/store identifier and the date the PM was performed (not just the date typed). |
| Technician | Named technician who performed the work. |
| Readings / measurements | Trade-relevant readings actually filled in with values (not blank, not "N/A" on fields that should have a number). See `trades/<trade>.md` for which readings matter. |
| Checklist marks | Each checklist line item has a pass/fail/NA mark. Blank line items are `partial`. |
| Free-text notes | Condition notes or work-performed narrative present where the form provides for it. |
| Signature / sign-off | Technician signature and, where the form requires it, customer/site sign-off. |

Scoring:
- **complete** — all required fields present and populated.
- **minor-gap** — one non-critical field missing (e.g., one reading, free-text
  note) while asset id, date, checklist marks, and signature are present.
- **incomplete** — asset id, date, checklist marks, readings as a group, or the
  signature is missing/blank.

Do not accept "the form is attached" as completeness. A blank or half-filled
form is `incomplete`.

## Dimension 2 — Before/after photo coverage and quality

Photos are the proof the PM happened and that conditions changed. Assess
coverage AND quality — a photo that exists but is useless is not coverage.

Coverage:
- A PM that performs corrective/cleaning work needs **before AND after** shots
  of that work.
- An inspection-only PM needs condition photos of the inspected
  asset/components.
- Nameplate/asset-tag photos support the asset-identity field.

Quality (reject a photo that fails any of these):
- **Legible** — not too dark, not blown out, not motion-blurred.
- **In focus** — the relevant detail is sharp.
- **Right subject** — actually shows the asset / component / condition claimed,
  not a floor, a truck, or an unrelated area.
- **Correctly labeled** — an "after" photo shows the after condition. An "after"
  that is identical to or worse than the "before" is a discrepancy (Field 5).

Scoring maps directly to the Field 3 coverage value: `complete`, `partial`,
`missing`. Name each photo and its assessment; do not count a rejected photo.

## Dimension 3 — Additional-repairs detection

Surface everything the survey says needs more work beyond the PM scope. Read
both the checklist (failed items) and the free-text.

For each additional repair:
- Quote the survey's literal words.
- Tag `actionable` (what + where + asset + severity, ideally a photo) or
  `needs-detail` (named but not scope-ready).
- If the survey explicitly states no additional work is needed, record
  `none-stated`.

Cross-check: a failed checklist item with no corresponding repair recommendation
is itself a gap — note it in Field 5 (discrepancies). A repair recommended in
free text but with every checklist item marked "pass" is also a discrepancy.

## Discrepancy checks (feeds Field 5)

Flag any of:
- Reading outside spec but the line item is marked pass/OK.
- "After" photo identical to, missing for, or worse than the "before."
- Checklist failure with no repair recommendation, or a recommendation with no
  failed item.
- Work-performed narrative that contradicts the photos (claims a part replaced
  that the after-photo shows unchanged).
- Date/technician on the form inconsistent with the SR's service record.
- **Zeroed-out asset counts on a "Success" survey** (Run 1, 2026-06-05). The
  asset-count fields are all 0 (no units, no readings, no photos) yet the
  survey is signed and marked complete. This is `data-incomplete` (or `fail`)
  pending verification — either the site genuinely has no in-scope equipment
  or the PM was not performed. Never treat a zeroed survey as `pass`.
- **"Repairs needed = Yes" with no description** (Run 1). The form captures a
  Yes/No but the technician left the scope blank. Each such flag is an
  additional repair tagged `needs-detail` in Field 4 — it cannot convert to a
  quote/SR as-is. Surface the count and route to the Facilities Lead (FL) to
  get scope from the SP and convert it to a quote/follow-on SR.

## Verdict rollup (to Field 1)

| Data | Photos | Verdict |
|---|---|---|
| complete | complete | `pass` |
| complete or minor-gap | partial | `pass-with-gaps` |
| minor-gap | complete | `pass-with-gaps` |
| incomplete | complete or partial | `data-incomplete` |
| complete or minor-gap | missing | `photos-insufficient` |
| incomplete | missing | `fail` |
| any | any + a material discrepancy in Field 5 | downgrade one level (at least `pass-with-gaps`; a contradiction that undermines the record is `fail`) |

A material discrepancy (e.g., "after" photo is actually a "before," reading out
of spec marked OK) overrides an otherwise-clean rollup. Use judgment and state
the reason.

## Trade extension point

Trade-specific checklists live in `trades/<trade>.md` (e.g., `trades/hvac.md`,
`trades/plumbing.md`, `trades/electrical.md`). Each defines the trade's required
readings, the expected photo set, and trade-specific discrepancy checks. When a
matching file exists for the survey's trade, load it and apply it ON TOP of this
generic rubric. When none exists, [`trades/generic.md`](./trades/generic.md)
covers the baseline. Seed new trade files as run patterns accumulate (see
SKILL.md "Future extensions").
