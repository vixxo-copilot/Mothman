# HVAC PM survey checklist (trade overlay)

Trade-specific overlay applied **on top of**
[`../quality-rubric.md`](../quality-rubric.md) when the survey is HVAC. Load
this when the survey title or LOS indicates HVAC (e.g.,
`... HVAC PM Workstep Survey`).

## Governing principle: the form is the contract (scope-aware, v1)

Do NOT hold every HVAC survey to a fixed superset of readings. Derive what is
expected from the **survey itself**, then judge each field in one of three
states:

- **present + filled** -> score it; for readings, run the sanity band below.
- **present + blank** -> gap (the form asked, the tech skipped).
- **not present / not in scope** -> N/A, never penalized.

A basic filter-change PM and a full mechanical PM run through this same file and
each is held only to what its own form contains. Never flag a survey
`data-incomplete` for a section it was never meant to have.

### How to read the scope from the survey (no external lookup in v1)

1. **Profile from the title** (PDF line 1) and overall structure.
2. **Asset-count section is authoritative.** The survey opens with counts:
   `Package Units or Heat Pumps`, `Rotary Chiller Units`, `Air Handler Units`,
   `Cooling Towers`, `Water Source Heat Pump`. The per-equipment sections that
   render (and the readings/photos expected) follow directly from those counts.
   - Count = 0 for a type -> that type is out of scope; expect nothing for it.
   - Count = N -> expect N populated sections + N photo sets for that type.
3. **Sections actually present.** If the compressor reading table is not in the
   form, superheat/subcooling are N/A. If there is no "Repairs needed?"
   question, do not expect a repairs answer.

> All asset counts = 0 is NOT a "light PM" — it is the zeroed-survey red flag
> in `../quality-rubric.md` (verdict `data-incomplete`/`fail`, verify the PM
> was performed). Distinguish "0 of every type" (suspicious) from "filter-only
> form with no compressor section" (legitimately light scope).

## Profiles

| Profile | How to detect | What is expected |
|---|---|---|
| `full-mechanical-pm` | Compressor + electrical reading tables present; asset counts > 0 | Per recorded unit: make/model/serial/ID, filter + before/after condenser + before/after evaporator photos, full reading tables, repairs answer. |
| `filter-change / light` | Filter section present, NO compressor/electrical tables | Filter photos + filter mag (pressure-differential) reading only. No compressor readings expected. |
| `inspection-only` | Checklist + condition photos, no corrective/after photos | Condition photos + checklist marks. No before/after corrective pair expected. |

If unsure which profile, default to what the form presents (the contract
principle) rather than forcing the heaviest profile.

## Expected data by equipment type (only when count > 0)

### Package Unit / Heat Pump (per unit)
- Identity: make, model, serial, identification number.
- Compressor table (per circuit): suction pressure, discharge pressure, liquid
  line pressure (+ converted), liquid line temp, suction line temp, superheat,
  subcooling, oil sight glass, outside air temp, acid test.
- Electrical (per circuit): volts L1-L2/L1-L3/L2-L3, amps L1/L2/L3; crankcase
  heater amps.
- Fans: supply fan + exhaust/condenser fan volts & amps.
- Condenser: entering/leaving air temp. Evaporator: mixed/discharge air temp.
- Main system line voltage. Filter mag reading (pressure differential, "w.c.).
- Heating element y/n. Repairs-needed answer.

### Other types (when count > 0)
- Chillers / Air Handlers / Cooling Towers / Water Source Heat Pumps each have
  their own section in the form. Apply the same contract principle: score the
  fields the section presents; do not import package-unit fields onto them.

## Reading sanity bands (advisory; fire only when field present AND filled)

These produce **Field 5 discrepancies** (review flags), not automatic `fail`.
State the value, the band, and a confidence. They flag a number the checklist
may have passed; they do not by themselves prove a defect.

| Reading | Healthy band | Flag when | Likely meaning |
|---|---|---|---|
| Superheat | ~8-14 F | < 5 F | Overcharge / liquid floodback risk (compressor damage). |
| Superheat | ~8-14 F | > 20-25 F | Undercharge / starvation / restriction. |
| Subcooling | ~8-15 F | < 3 F | Undercharge. |
| Subcooling | ~8-15 F | > 18-20 F | Overcharge / restriction / non-condensables. |
| Evap temp split (return/mixed - supply/discharge) | ~16-22 F | < 14 F | Low airflow excess / low charge / icing. |
| Evap temp split | ~16-22 F | > 25 F | Low airflow (dirty coil/filter, belt). |
| Voltage imbalance across phases | < 2% | > 2% | Supply/phase problem; motor stress. |
| Filter mag (pressure differential) | per spec | rising / high vs peers | Dirty/clogged filter (compare across units same site). |
| Acid test | Neg | Pos | Refrigerant/oil acid -> compressor/system contamination. |
| Oil sight glass | oil visible / "Good" | empty / foaming | Low oil / refrigerant in oil. |

Amp draw vs nameplate RLA/FLA is a useful check but needs the nameplate rating;
flag only if the nameplate is captured (asset/mfgPlate photo or model lookup).
Otherwise note "amps recorded; nameplate not available to validate."

Bands are advisory and may vary by equipment, metering, and ambient. When a
reading is out of band, write it as: value + band + one-line meaning +
confidence, and recommend a spot-check rather than asserting a defect.

## Expected photo set (scales with recorded equipment)

Per package unit in scope: filter change, condenser coil **before** + **after**,
evaporator coil **before** + **after** (~5 shots/unit). Coverage expectation =
function of recorded counts, not a fixed number. Photos may be embedded in the
survey PDF or separate `mobileTechnicianPhotos`/`asset`/`mfgPlate` attachments
(see SKILL.md Step 2/3) - count both.

Photo discrepancy checks: "after" coil photo as dirty as the "before"
(cleaning checked complete but not shown); filter "after" still dirty; nameplate
illegible.

## Repairs answer (only when the form has the question)

The Nordstrom full-mechanical form has a per-unit "Repairs - Are any repairs or
additional work needed...?" question. When present:
- `Yes` with a description -> additional repair, tag `actionable` (Field 4).
- `Yes` with no description -> tag `needs-detail` (Run 1: common - the form
  captures Yes/No but the scope text is often left blank). Surface per-unit.
- Check the survey's free-text **Additional Info** section too - in Run 1 some
  SPs put the actual repair scope there (per-RTU narratives) even when the
  per-unit field was blank.

If the form has no repairs question (light/filter-only profile), do not expect
a repairs answer.
