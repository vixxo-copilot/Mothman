# Refrigeration PM survey checklist (trade overlay)

Trade-specific overlay applied **on top of**
[`../quality-rubric.md`](../quality-rubric.md) when the survey is a refrigeration
PM (walk-in coolers/freezers, reach-ins, display cases, condensing units, ice
machines). Load when the survey title or LOS indicates refrigeration
(e.g., `Refrigeration PM - Quarterly`). For packaged HVAC/RTU work use
[`hvac.md`](./hvac.md); many refrigeration forms overlap with HVAC-R mechanical
checks, so borrow its band logic when the form captures readings.

## Governing principle: the form is the contract (scope-aware)

Same rule as the other trade overlays. Judge each field in one of three states:
**present + filled** (score it), **present + blank** (gap), **not present / not
in scope** (N/A, never penalized).

## Critical: refrigeration forms differ A LOT by customer

Do NOT assume a fixed field set. Refrigeration PM surveys fall on a spectrum,
and other clients will ask different questions than the one you're looking at:

- **Reading-capture forms** — record box/discharge temps, superheat/subcooling,
  suction/discharge pressures, amp draws, defrost timing, temperature
  differential. Evaluate these against sanity bands (below).
- **Inspection / photo-documentation forms** — a static PM-scope checklist with
  **no numeric entry fields**, an overall assessment rating, a per-unit
  Repairs Yes/No (+ description), and photo prompts. There are no readings to
  band-check; score on completeness, condition/repairs, and photo coverage.
  (ALE01 / Alliance is this type — see worked example below.)
- Equipment mix varies: walk-in cooler vs walk-in freezer vs reach-in vs open
  display case vs ice machine each have different "good" targets.

So: **read what THIS form presents, per equipment unit**, then apply only the
checks that match. When unsure whether something is out of range, emit a
low-confidence Field 5 note for verification rather than auto-failing.

### How to read scope from the survey

1. **Per-unit sections / equipment counts** drive scope (how many walk-in
   coolers / freezers / reach-ins / condensing units). Each renders its own
   section — scan every one (repeated sections are common).
2. **Equipment type per unit** (cooler vs freezer vs case vs ice machine)
   calibrates expectations (a freezer box temp near 0 F is normal; a cooler near
   38 F is normal).
3. **Which fields render** — readings, ratings, repairs, photos. If a field
   isn't on the form, it's N/A.
4. All asset counts 0 / nothing recorded = the zeroed-survey red flag in
   `../quality-rubric.md`, not a light scope.

## Reading sanity bands (ONLY when the form captures the reading)

Advisory; fire only when present and filled; calibrate to equipment + refrigerant.
Produce Field 5 review flags, not auto-fail.

| Reading | Healthy band (calibrate to equipment) | Flag when | Note |
|---|---|---|---|
| Walk-in / reach-in COOLER box temp | ~35-41 F | > ~45 F or < ~32 F | Product-safety relevant. |
| Walk-in / reach-in FREEZER box temp | ~ -10 to +10 F | > ~15 F | Not holding temp. |
| Temperature differential (return vs supply / across coil) | per system | recorded out of expected, or scope says record it but no value | See scope-vs-field gap below. |
| Superheat / subcooling (if captured) | per `hvac.md` bands | per `hvac.md` | Borrow HVAC overlay. |
| Suction / discharge pressure | refrigerant-dependent (R-448A/R-404A/R-134a differ) | clearly off for the stated refrigerant | Identify refrigerant first; low confidence otherwise. |
| Compressor amp draw | vs nameplate RLA | > nameplate, if nameplate captured | Needs nameplate; else note. |
| Defrost (cycles/termination) | per controller | malfunction noted | Surface tech note. |

## Inspection / photo-form handling (e.g., ALE01)

When the form has no numeric fields, do NOT penalize for missing readings.
Evaluate instead:

- **Per-unit asset identity** present and real (make/model/serial). Flag junk /
  placeholder identity: make = `True`, model == serial, repeated `True/True/True`
  (ALE01 examples) -> data-quality discrepancy (Field 5).
- **Overall unit assessment rating** present.
- **Per-unit Repairs Yes/No** — `Yes` with a description = actionable repair
  (Field 4, route to FL); `Yes` with no description = `needs-detail`.
- **Photo coverage** per the form's prompts (commonly: overall unit + coil
  **before/after** cleaning; door gaskets; nameplate). Missing the before/after
  coil pair on a unit whose scope includes coil cleaning = `partial`.
- **"Were all steps performed on ALL units?"** style question — answer `No` (or
  blank) with no variation explanation = discrepancy (Field 5); the PM may be
  incomplete on some units.

## Scope-vs-field gap (generalizable program-quality check)

If the PM **scope text** says to record a value (e.g., "record compressor amps",
"record temperature differential") but the form provides **no field to capture
it**, flag a program/form gap: the required data is never collected. Route to the
**PM program team** (form/scope fix), not the FL. (Founding case: ALE01
refrigeration + HVAC forms instruct "record amps / temp differential" yet have
no entry field for either.)

## Damage / condition -> additional repairs (Field 4, route to FL)

Refrigeration-specific repair signals (quote the survey's words):
- Door gasket/seal torn or not sealing; missing/!damaged strip curtains.
- Coil dirty / "coil cleaning needs to be performed" (esp. if the after-photo
  still shows a dirty coil).
- Fan motor / blade, defrost heater, door heater, hinges/closer issues.
- Excessive ice/frost build-up; condensate/drain-line clog.
- Box not holding temperature.

## Photo set (scales with equipment in scope)

Per unit, per the form: overall unit photo; coil **before** + **after**
cleaning; door gasket; nameplate/asset. HVAC-adjacent units may add belt + filter
before/after. Coverage = what the form asks for; count embedded + separate
attachments (ALE01 uses `mobileTechnicianPhotos` / `asset` .jpg/.png).

## Discrepancy checks (feeds Field 5)

- Reading out of band (only when captured; calibrate to equipment/refrigerant).
- Coil "cleaned" but after-photo still dirty / no after-photo.
- Junk/placeholder asset identity (make `True`, model == serial).
- "All steps performed on all units? = No/blank" with no explanation.
- Scope-vs-field gap (above).
- Store/site number on the survey != the SR's site.
