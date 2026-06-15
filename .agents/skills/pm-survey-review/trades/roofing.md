# Roofing PM survey checklist (trade overlay)

Trade-specific overlay applied **on top of**
[`../quality-rubric.md`](../quality-rubric.md) when the survey is a roofing PM —
typically a **roof cleaning / drain cleaning survey** (e.g., Safeway's
`Roofing Cleaning Survey PM`). Built scope-aware: judge only what the form
presents (present+filled = score; present+blank = gap; not present = N/A).

## Critical: roofing forms vary by customer AND by SP

Roofing PM forms differ across customers, and even across SPs on the SAME
customer. Read what THIS form presents; don't hardcode one shape. Two real
variants seen on Safeway (219):

- **Structured `pmSurvey` PDF** (e.g., Pest Force "Roof Drain Cleaning PM") —
  store check-in/out, before/after overall-roof + before/after drain photos, a
  set of Yes/No condition items, and free-text comments.
- **"Audit PDF" delivered as `subType: general`** (e.g., Bonded Filter
  "Vixxo - Cerberus Audit") — NOT classified as `pmSurvey`. Same condition
  questions (often `True - <detail>` / `False`) plus a photo gallery with
  per-photo `Photo description:` lines.

**Attachment-classification note:** for roofing, the survey may be the
`pmSurvey` OR a `general` "Audit PDF". If no `pmSurvey` exists, look for a
`general` PDF whose first page reads as a roof audit/cleaning survey before
concluding "no survey". (Water-filtration and other trades stick to `pmSurvey`;
roofing is the exception.)

## Expected data (when the form presents it)

- Store / site identity; tech check-in and check-out.
- The roof-condition checklist (Yes/No or True/False), commonly these six:
  1. Debris removed
  2. Drains cleared
  3. Standing water / puddles present
  4. Roof / wall damage present
  5. Broken seals (around HVAC curbs, hatches, vents, penetrations)
  6. Abandoned equipment / items left on roof
- Free-text comments / additional findings.

## Photo set (the proof the cleaning happened)

Expected minimum = **4**: before + after **overall roof**, and before + after
**drains**. More is better (audit-style surveys carry 6-24). Photos may be
embedded in the PDF or separate attachments.
- **Logo caveat:** Bonded "Cerberus Audit" PDFs embed a 1x BFC logo image —
  subtract it from the embedded-image count so coverage isn't overstated.
Photo discrepancy: "after" roof/drain shot missing, or an "after" that still
shows the debris/standing water the checklist claims was cleared.

## Two kinds of finding — keep them separate

This is the key roofing rule. Distinguish **conditions found on the roof**
(route to FL) from **the cleaning task not being completed** (route to PM team).

### A. Conditions found -> additional repair (Field 4, route to Facilities Lead)
Flag when any is Yes/True (quote the tech's words):
- Broken seals = Yes -> sealant/flashing repair.
- Standing water / puddles = Yes -> drainage/low-spot issue.
- Roof / wall damage = Yes -> roof repair.
- Abandoned equipment / items left on roof = Yes -> removal / owner follow-up.
These are real roof problems the PM surfaced; they do not by themselves mean the
PM was done wrong.

### B. Core task NOT completed -> pass-with-gaps, route to PM program team
The whole point of this PM is cleaning the roof/drains. So:
- **Debris removed = No** OR **Drains cleared = No** -> the cleaning itself was
  not completed -> verdict `pass-with-gaps` (or `fail` if nothing was done) and
  route completion-verification to the **PM program team**. This is distinct
  from a found-condition. (Founding case: Safeway 0243 Coeur d'Alene - "Heavy
  bricks I can't remove," debris not fully removed.)

## Verdict guidance

- All checklist items answered, before/after photos present, cleaning completed,
  no conditions -> `pass`.
- Cleaning completed but a condition found (seals/water/damage/abandoned) ->
  `pass-with-gaps` with the repair in Field 4 (FL).
- Debris/drains not fully done, or before/after photos missing for the cleaning
  -> `pass-with-gaps` (cleaning not proven) -> PM team.
- No roof survey/audit artifact at all (only a work ticket) -> `data-incomplete`.

## Discrepancy checks (feeds Field 5)

- Checklist says cleared/clean but the "after" photo still shows debris /
  standing water.
- Missing before/after roof or drain photos.
- A condition flagged Yes with no detail -> `needs-detail`.
- Store/site number on the survey != the SR's site.
- Survey delivered only as a work ticket (no audit/survey) -> data-incomplete;
  PM team verifies the PM was performed and enforces survey capture.
