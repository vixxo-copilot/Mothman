# Water Filtration PM survey checklist (trade overlay)

Trade-specific overlay applied **on top of**
[`../quality-rubric.md`](../quality-rubric.md) when the survey is a water
filtration PM. Load this when the survey title or LOS indicates water
filtration (e.g., `... SEMI-ANNUAL WATER FILTRATION PM`).

## Governing principle: the form is the contract (scope-aware)

Same rule as `trades/hvac.md` and `trades/coffee.md`. Judge each field in one of
three states:

- **present + filled** -> score it; for readings, run the sanity band.
- **present + blank** -> gap (the form asked, the tech skipped).
- **not present / not in scope** -> N/A, never penalized.

## Critical: water filtration specs and equipment vary by CUSTOMER

This is the most important rule for this trade. Do NOT hardcode one customer's
acceptance thresholds or equipment expectations as universal. Water filtration
PMs differ widely:

- **Equipment type drives expectations.** A reverse-osmosis (RO) system, a
  water softener, a carbon/sediment filter bank, and a scale-inhibitor cartridge
  setup all have different "good" readings and different PM steps. Example: an
  **RO** system normally produces **very low outgoing TDS (near 0-25 ppm)** -
  that is healthy, not a defect. A softener targets hardness reduction, not TDS.
- **Acceptance thresholds are customer-specified.** Read the band from the
  **survey's own stated spec** whenever the form prints one, and use that -
  not a global default. (Peet's worked example below.)
- **Required photos / bypass rules are customer-specific.** Peet's mandates a
  "unit is NO longer in bypass" photo; another customer's form may not.

So: **extract the spec and equipment type from the survey itself**, then apply
the bands the form states. Only fall back to general guidance (below) when the
form states no spec. When unsure whether an out-of-band reading is a real
problem or just normal for that equipment type, mark it a **low-confidence**
Field 5 note recommending a verification pass - do not auto-fail.

### How to read scope from the survey (no external lookup)

1. **System count:** "how many Water Filtration Systems are present?" (N>0).
   N=0 with nothing else recorded is the zeroed-survey red flag in
   `../quality-rubric.md`, not a light scope.
2. **Equipment identity:** "Make / Model / Serial Number of unit being
   serviced" - infer equipment type (RO / softener / carbon / scale) from the
   make/model to calibrate expectations (e.g., Kinetico/3M/Pentair Everpure/
   Nimbus/Cirqua cartridge systems vs a softener with a brine tank).
3. **Which sections render:** brine-tank questions apply only to softeners;
   skip cleanly when absent.

## Expected data (only when present on the form)

- System count; make/model/serial of each unit.
- General operational condition / issues-for-repair note.
- **Incoming** water quality: TDS and hardness (pre-filtration).
- **Outgoing** water quality: TDS and hardness (post-filtration).
- Valve checks; filter change-out; pressure-switch/settings; post-filtration
  pressure note.
- Brine-tank level (softeners only).
- System-issues note (membranes, pumps/motors, lines, gauges - items noted but
  not in PM scope).
- Bypass status on arrival + bypass cleared at completion.

## Reading sanity bands (customer-spec first; general fallback)

**Always prefer the spec the form prints.** Peet's form, for example, states:
flag if **outgoing** is outside `TDS 25-200 ppm` or `hardness 17-85 ppm
(1-5 gpg)`. Use those numbers for Peet's. For another customer, use that
customer's stated spec; if none is printed, use the general fallback and lower
confidence.

| Reading | General guidance (use form's spec if it states one) | Flag when | Note |
|---|---|---|---|
| Outgoing TDS | Equipment-dependent: RO ~0-50 ppm is normal; carbon/scale systems leave most TDS in place | Outside the **form's stated** band; or wildly off for the equipment type | RO near-0 TDS is NOT a defect even if below a generic "25" floor - calibrate to equipment. |
| Outgoing hardness | Softener target low; cartridge/scale systems may not reduce hardness much | Outside the form's stated band | Low hardness after a softener is expected. |
| Incoming vs outgoing | Filtration should change the reading | **incoming == outgoing** (no change) | Strong signal the system isn't filtering - often paired with a bypass condition. Real finding. |
| Post-filtration pressure | per system | "low" noted by tech | Surface tech's note. |

Bands are advisory and equipment/customer-specific. State value + the band you
applied (and its source: form-spec vs general) + confidence.

## Mandatory checks (Peet's; confirm per customer)

- **Bypass cleared.** If the unit is found in bypass on arrival, the tech must
  return it to filtration and capture a "**no longer in bypass**" photo. A
  survey whose bypass ANSWER says the unit is/was left on bypass (manager
  unavailable, etc.) is a real finding -> Field 4 actionable repair + Field 5
  discrepancy, verdict `pass-with-gaps` (or `fail` if the store is left on
  unfiltered water with no follow-up). Do NOT confuse the form's boilerplate
  bypass *instruction* with the tech's *answer* - only the answer counts.
- **"No longer in bypass" photo present** when a bypass condition occurred.

(For a customer whose form has no bypass concept, skip these.)

## Discrepancy checks (feeds Field 5)

- Condition/issue note names a **leak / damage / not-working** item (real
  additional repair -> Field 4).
- **incoming == outgoing** readings (filtration not working / on bypass).
- Outgoing reading outside the **form's stated** spec (calibrate to equipment;
  low-confidence if equipment type would explain it).
- Bypass answer indicates the unit was left on bypass.
- System-issues note flags membranes / pumps / gauges needing attention
  (noted-but-not-in-scope -> follow-on).
- Store number on the survey != the SR's site number (data-entry error).

## Expected photo set

Per Peet's: a picture of the unit + a "no longer in bypass" picture. Other
customers vary. Coverage expectation = what the form asks for. Photos may be
embedded in the survey PDF or separate attachments (Peet's uses
`subType: general` .jpg) - count both.

## Additional repairs

Repairs land in the condition / "issues for repair" / system-issues free-text
(no dedicated per-unit Yes/No like HVAC). A named issue with detail ->
`actionable` (Field 4). A vague note -> `needs-detail`. None -> `none-stated`.
Route repair scope to the Facilities Lead (FL); route survey data-quality and
bypass-left-uncleared verification to the PM program team.
