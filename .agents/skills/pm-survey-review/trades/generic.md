# Generic PM survey checklist (trade-agnostic baseline)

This is the default checklist applied when no trade-specific
`trades/<trade>.md` file matches the survey's trade. It is intentionally
trade-neutral. It is applied on top of
[`../quality-rubric.md`](../quality-rubric.md).

## Required data (any trade)

- Asset identity: asset id/tag, or make + model + serial.
- Site/store identifier.
- PM performed date.
- Technician name.
- Every checklist line item has a pass / fail / NA mark.
- Condition / work-performed notes where the form provides for them.
- Technician signature (and customer/site sign-off where the form requires it).

## Expected photos (any trade)

- Asset / nameplate photo supporting the asset-identity field.
- Condition photo of the inspected asset/component.
- Where corrective or cleaning work was performed: a **before** and an
  **after** photo of that work.

## Generic discrepancy checks

- Any checklist item marked `fail` with no corresponding additional-repair
  recommendation.
- Any additional-repair recommendation with no failed checklist item or
  supporting note.
- "After" photo missing, identical to, or worse than the "before."
- Work-performed narrative that the photos do not support.

## Trade-specific checklists (add as needed)

Create a sibling file when a trade earns its own checklist. Each should add the
trade's required readings/measurements, its expected photo set, and any
trade-specific discrepancy checks. **Every trade file must honor the
scope-aware "the form is the contract" principle** (see `trades/hvac.md`): only
evaluate fields the survey presents, and never penalize a light-scope PM for a
section it was never meant to have.

- `trades/hvac.md` — **built.** Profile detection (full-mechanical / filter-
  change / inspection), scope read from the asset-count section, superheat/
  subcooling/temp-split/voltage sanity bands (fire only when present + filled),
  scaled before/after photo expectations.
- `trades/coffee.md` — **built.** Espresso / grinder / brewer PM. Scope from
  equipment-count questions; group temp/pressure, grind-weight bands (fire only
  when present + filled); damage-vs-fix and implausible-reading discrepancy
  checks. Brewers-only / partial-scope surveys not penalized.
- `trades/water-filtration.md` — **built.** Scope-aware; reads acceptance
  thresholds from the survey's OWN stated spec (TDS/hardness bands vary by
  customer + equipment type: RO vs softener vs carbon). Mandatory bypass-cleared
  check + "no-longer-in-bypass" photo, incoming != outgoing sanity. Peet's is
  the worked example; do not hardcode its numbers as universal.
- `trades/roofing.md` — **built.** Roof cleaning / drain-cleaning survey.
  Handles two formats (structured `pmSurvey` AND an "Audit PDF" delivered as
  `subType: general`). Six-item condition checklist; before/after roof + drain
  photo set (with the Bonded logo-image caveat). Key rule: separate a
  **condition found** (broken seals / standing water / damage / abandoned
  equipment -> FL repair) from the **core cleaning not completed** (debris/
  drains = No -> pass-with-gaps -> PM team). Customer/SP-variance is first-class.
- `trades/plumbing.md` — (future) fixture identity, leak-free verification
  photos, water-on test, drain flow before/after.
- `trades/electrical.md` — (future) panel/breaker readings, torque/thermal
  checks, before/after photos of corrected connections.
- `trades/refrigeration.md` — **built.** Walk-in/reach-in/case/ice; box-temp,
  superheat/subcooling, pressure, amp, defrost bands **when the form captures
  readings** — but explicitly handles **inspection/photo-only forms with no
  reading fields** (ALE01) without penalizing. Includes the generalizable
  "scope says record X but no field exists" program-gap check, junk-identity
  detection, and gasket/coil/door repair signals. Customer-variance is a
  first-class rule.

Until a trade file exists, this generic checklist is the baseline and the
generic rubric in `../quality-rubric.md` governs scoring.
