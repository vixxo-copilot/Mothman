# Coffee / Espresso PM survey checklist (trade overlay)

Trade-specific overlay applied **on top of**
[`../quality-rubric.md`](../quality-rubric.md) when the survey is a coffee /
espresso PM. Load this when the survey title or LOS indicates espresso, coffee,
grinder, or brewer work (e.g., `PEET'S COFFEE - Espresso Machine ...`,
`Espresso Machine Semi-Annual PM`).

## Governing principle: the form is the contract (scope-aware)

Same rule as `trades/hvac.md`. Do NOT hold every coffee survey to a fixed
superset of questions. A coffee PM may cover an espresso machine, grinders,
brewers, or **any subset** of those. Derive what is expected from the survey
itself, then judge each field in one of three states:

- **present + filled** -> score it; for readings, run the sanity band below.
- **present + blank** -> gap (the form asked, the tech skipped).
- **not present / not in scope** -> N/A, never penalized.

Run 3 (2026-06-05) proved this matters: Peet's Porter Ranch 1347 was a
**brewers-only** site (espresso count 0, grinder count 0). The group
temp/pressure and grind-weight questions did not apply and the survey was a
clean `pass`. Never flag a coffee survey `data-incomplete` for an espresso
reading when no espresso machine is in scope.

### How to read the scope from the survey (no external lookup)

The form is equipment-count-driven, exactly like the HVAC asset-count section:

1. **Equipment-count questions are authoritative:**
   - `How many ESPRESSO equipment are present`
   - `How many GRINDER equipment are present`
   - `How Many BREWERS equipment are present`
2. Each count = N renders N repeated sections for that equipment type. Expect N
   populated sections + the per-type photos for each.
3. Count = 0 (or the question/section absent) -> that equipment type is out of
   scope; expect nothing for it (no group temp if no espresso, no grind weight
   if no grinder).
4. Only the sections actually present are in scope. If the espresso "Group Temp"
   field is not in the form, it is N/A.

> A coffee survey with **every** equipment count 0 (nothing recorded, no photos)
> is the zeroed-survey red flag from `../quality-rubric.md` (verdict
> `data-incomplete`/`fail`, verify the PM was performed) - not a legitimately
> light scope. Distinguish "0 of everything" from "brewers-only".

## Equipment sections and expected data (only when count > 0)

### Espresso machine (per unit)
- Identity: make/model, serial; nameplate/asset/machine photos; top + inside
  element-side photo (looking for damage / calcium).
- Hot water taps checked (leak/function).
- Portafilters engaged on arrival? Dual gauge functioning?
- Scope items: dispersion screens replaced, group diffuser cleaned, portafilter
  gaskets changed, steam valve assemblies rebuilt/replaced, sight glass,
  calcium-buildup check (left side panel), pressure switch, drain box/lines.
- Readings: Group Temp existing / adjusted; Group Pressure existing / adjusted.
- Pump leaks, auto-fill operation, vacuum breaker.

### Grinder (per unit)
- Identity: make/model, serial; nameplate/machine photos.
- Anti-static tabs positioned / damaged? Hopper damage? Hopper lids? Tower lid?
- Clean grind chamber/chutes/impeller; set screws; roller switch.
- Readings: grind weight BEFORE / AFTER adjustment (target 17.5-18.0 g with
  22 mm Swift basket); extraction rate 24-28 sec for 2 fl oz.
- "Additional fixes needed" free-text (per grinder).

### Brewer (per unit)
- Identity: make/model, serial; nameplate/machine photo.
- Fill probe checked/cleaned/replaced.

## Reading sanity bands (advisory; fire only when field present AND filled)

Produce **Field 5 discrepancies** (review flags), not automatic `fail`. State
value + band + confidence.

| Reading | Healthy band | Flag when | Likely meaning |
|---|---|---|---|
| Group temp (espresso) | ~195-205 F (target ~200-201) | < 190 or > 210 F | Brew temp off; taste/extraction impact. |
| Group temp | — | single-digit / nonsensical (e.g. "8") | **Data-entry error** - reading unusable; ask for re-read. (Run 3: Fairfax 1254 & 1250 recorded group temp "8".) |
| Group pressure (espresso) | ~8.5-9.5 bar (target 9) | < 8 or > 10 bar | Pump/OPV out of spec. |
| Grind weight (dose) | 17.5-18.0 g | outside 17.0-18.5 g | Dose off; drink quality / yield. |
| Extraction time | 24-28 sec / 2 fl oz | outside 22-30 sec | Grind/dose/tamp off. |

A reading is only a flag when it is **present and filled**. Bands are advisory
and vary by machine/recipe; on an out-of-band value, write value + band +
one-line meaning + confidence, and recommend a re-read/spot-check rather than
asserting a defect.

## Damage / condition fields — scan EVERY equipment section (required)

The coffee survey has several structured Yes/No damage & condition fields, and
they **repeat once per grinder/brewer**. Do NOT check only the first occurrence
(a multi-grinder survey has several). Scan all occurrences and flag if ANY is a
problem answer. Each is an additional repair (Field 4) / discrepancy (Field 5):

| Field | Problem answer |
|---|---|
| `Are Anti-Static Tabs Damaged?` | Yes |
| `Is there any Damage to Hoppers?` | Yes |
| `Do Hoppers Have Lids?` | No (missing lid) |
| `Grinder Tower Lid Present?` | No (missing lid) |
| `Dual Gauge functioning and responsive?` | No |
| `Are anti-static tabs properly positioned...?` | No |

Watch the blank-answer trap: when a damage field is left blank, the next line is
the following question — do not read that as the answer. Only count a literal
`Yes`/`No`. (Run: SR 1-6464398864 reported `Anti-Static Tabs Damaged = Yes` on
the grinder while the hopper-damage field was blank; checking only hopper damage
missed it.)

## Coffee-specific discrepancy checks (feeds Field 5)

- **Existing reading out of band but "adjusted to" the same value** - tech
  recorded a problem but logged no adjustment.
- **Implausible reading** (group temp single-digit) - data-entry error; the
  reading cannot be trusted.
- **Damage answered "Yes" but "additional fixes = None"** - damage noted but not
  converted to a repair (Run 3: Tarzana 1095 hopper "Damage = Yes", fixes
  "None"). Tag the repair `needs-detail` in Field 4.
- **Store number on the survey != the SR's site number** (Run 3: Tarzana survey
  store 1085 vs site 1095) - data-entry error worth flagging.
- **Incomplete identity** (serial blank/placeholder like "Lo") on an in-scope
  unit.

## Expected photo set (scales with equipment in scope)

Per espresso machine: nameplate/asset + machine, top + inside element-side
(damage/calcium), and any leak/damage shots called out. Per grinder: nameplate +
machine. Per brewer: nameplate + machine. Coverage expectation = function of the
recorded equipment counts, not a fixed number. Photos may be embedded in the
survey PDF or separate attachments (Peet's uses `subType: general` .jpg) - count
both (see SKILL.md Step 2/3).

## Additional fixes / repairs (only when the form has the field)

The grinder section has an "If there are any additional fixes needed, please
list them here!" field; espresso/brewer issues land in service notes / the
free-text. When present:
- A named fix with detail -> `actionable` (Field 4).
- "Yes/identified" with no description -> `needs-detail`.
- "None" / "None needed" -> `none-stated`.
If a section has no additional-fixes field, do not expect an answer for it.
