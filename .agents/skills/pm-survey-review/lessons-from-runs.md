# Lessons from runs

Empirical patterns from real PM-survey review runs. Append new runs here;
promote a pattern into SKILL.md / quality-rubric.md only after it repeats or is
severe enough for a one-shot rule.

## Run 1 — Nordstrom Spring HVAC, 10 "Success" surveys (2026-06-05)

**Scope:** 10 surveys selected (status `Success`) from a 110-row VixxoLink
survey export (`data (25).xlsx`), customer NR01, all HVAC package-unit PMs
across 8 SPs (Peak Season, MAB Mechanical, Pacific Mechanical, Allied Detroit,
Summit Air, Service Champions).

**Method:** SR-list mode. `vixxolink_get_service_request_attachments` per SR →
download presigned survey PDF → read text + extract/probe embedded photos
(PyMuPDF) → score against the rubric. Photo quality spot-checked on SR1 (5
images) and SR6 (2 separate images).

**Outcome:** pass 5, pass-with-gaps 4, data-incomplete 1.

### Patterns surfaced

| Pattern | Evidence | Promoted to |
|---|---|---|
| VixxoLink attachment listing is the working data path; returns presigned S3 URLs + a `subType` classifier directly. | All 10 SRs resolved cleanly via `{"service_request_number"}`. Gateway `gateway_list_sr_attachments` returned HTTP 400 on the simple payloads. | SKILL.md Step 2 + Verified payload shapes. |
| `subType` is the authoritative attachment classifier, not filename keywords. | Observed subTypes: `pmSurvey`, `workTicket`, `mobileTechnicianPhotos`, `asset`, `mfgPlate`. | SKILL.md Step 2 classification table. |
| Photos live in two places: embedded in the survey PDF OR as separate attachments. | SR1-5/8/9 embedded photos in the PDF (Read text extraction misses them — extract with PyMuPDF). SR6 (12), SR7 (1), SR10 (1) had separate `mobileTechnicianPhotos`/`asset`/`mfgPlate`. | SKILL.md Step 2/3. |
| Duplicate survey submissions occur; pick the latest. | SR `1-6533423702` had two `pmSurvey` PDFs (05-27 and 05-30). | SKILL.md Step 2 (latest `createdDate`). |
| A "Success" survey can be effectively empty. | SR `1-6533428517` (Store 266, Allied Detroit): all asset-count fields 0 — zero units, readings, photos — but signed and marked Success. | quality-rubric.md discrepancy check (zeroed-out asset counts → data-incomplete/fail). |
| "Repairs needed = Yes" is captured without any description. | 16 unit-level Yes flags across SR3 (5/7), SR6 (1/3), SR7 (3/4), SR10 (7/8) — none had scope text. | quality-rubric.md discrepancy check + Field 4 `needs-detail`. |
| Possible out-of-range HVAC readings that the form still accepts. | SR1 Unit 1 sub-cooling 60 F; Unit 4 superheat ~7 F. A trade-specific `trades/hvac.md` rubric (superheat/subcooling sanity bands) would catch these; the generic rubric does not. | Candidate `trades/hvac.md` (future). |

### Reviewer reads

_(pending Eric's review of the Run 1 packets)_

## Run 2 — Nordstrom Spring HVAC, 10 more "Success" surveys (2026-06-05)

**Scope:** SRs 11-20 of the same `Success` set (SPs: Allied Detroit, MAB
Mechanical, Climate Pros, Service Champions, Delfino Refrigeration).

**Outcome:** pass 8, pass-with-gaps 2, data-incomplete 0. Combined with Run 1:
pass 13, pass-with-gaps 6, data-incomplete 1 across 20.

### Patterns surfaced / reinforced

| Pattern | Evidence | Note |
|---|---|---|
| The empty-survey problem (SR5) is NOT systemic to the SP. | Allied Detroit's other two surveys (SR11 store 0267, SR15 store 0231) were complete with photos + readings. SR5 was an isolated empty submission. | Keep the zeroed-survey check; don't over-generalize to the SP. |
| Repairs-needed scope is sometimes in the free-text narrative, sometimes blank - confirms the dual-read. | SR16 (Service Champions) flagged 5 units with full per-RTU detail in Additional Info (low charge, no-start circuits). SR20 (Service Champions) flagged 1 unit with Additional Info = "Na" (no scope). | Reinforces reading BOTH the per-unit flag AND Additional Info (quality-rubric Field 4). |
| SP narratives use their own unit labels, not the form's "Package Unit N". | SR16 narrative references RTU 2A/2B/2G/2H while the form numbers units 1-9. | When mapping repair detail to units, expect label mismatch; quote the SP's label verbatim. |
| Survey-PDF filename format varies. | SR19/SR20 keys are `<uuid>-SurveySubmission_<sr>.pdf` vs Run 1's `<sr>_SurveySubmission-<uuid>.pdf`. | Classify by `subType: pmSurvey`, never by filename pattern (already the rule). |
| Photo coverage scales cleanly with unit count across SPs. | ~5-6 photos/unit consistently; Delfino SR19 had 50 embedded + 12 separate for 10 units. | Coverage-by-count is a reliable first-pass signal; spot-check quality on a sample. |

## Run 3 — Peet's Coffee (PC01), 10 Water Filtration + 10 Coffee/Espresso PMs (2026-06-05)

**Scope:** First cross-customer + cross-trade test. 20 completed-2026 PMs found
live via `vixxolink_search_service_requests` (no export file): 10 Water
Filtration Semi-Annual PM + 10 Espresso/Coffee PM, all `priority=Planned/PM`,
`subStatus=AR Successful`.

**Outcome:** pass 16, pass-with-gaps 4, data-incomplete 0, fail 0.

### Patterns surfaced

| Pattern | Evidence | Note / promoted to |
|---|---|---|
| The skill's data path generalizes to a new customer + trades. | All 20 PC01 SRs returned a `pmSurvey` PDF via the same VixxoLink attachments path; survey templates differ entirely from Nordstrom HVAC. | Confirms trade-agnostic design. |
| PM work is identified by `priority="Planned/PM"`, not LOS/type; completion by `subStatus` (AR Successful / Invoice Review). `isJobComplete` filter is unreliable (returns Open SRs). | PC01 search: 662 Planned/PM; recent 2026-05-16 batch still `SP_HOLD`/`Assigned to Service Contractor` (not done). | Add to SKILL.md search guidance for SR-list discovery from a customer + date window. |
| Peet's photos use `subType: "general"` (.jpg); a `WorkOrderDocument.html` attachment also appears. | All PC01 surveys. | Extend the subType classifier note (general = photo for PC01). |
| `vixxolink_search_service_requests` rejects `sortDirection: "desc"`. | 400 validation error. | Omit sort; default order is newest-first. |
| Water-filtration PM has TDS/hardness readings + a mandatory bypass-cleared check. | Spec on form: outgoing TDS 25-200 ppm, hardness 17-85 ppm. WF04 Arlington 1249: unit found/LEFT on bypass, manager unavailable, leak noted, incoming=outgoing (11/180) confirms no filtration, 'no-longer-in-bypass' photo missing. | Motivates `trades/water-filtration.md` (TDS/hardness bands, bypass check, in!=out sanity). |
| Coffee PM has group temp/pressure + grind-weight readings that can be implausible. | Fairfax 1254 & 1250: group temp recorded "8" (should be ~200F) - data-entry error, reading unusable. Standard good reads: ~198-202F / 9 bar / 17.5-18g. | Motivates `trades/coffee.md` (temp/pressure/grind bands; multi-equipment scope). |
| Scope-aware principle validated on a non-HVAC trade. | Porter Ranch 1347: brewers-only site (espresso#0, grinder#0) - group temp/pressure correctly N/A, not penalized. | Confirms `trades/hvac.md` "form is the contract" generalizes. |
| Store-number / data-entry discrepancies recur. | Tarzana 1095: survey Store# = 1085 (!= site 1095); hopper "Damage = Yes" but "additional fixes = None". | Field 5 discrepancy checks apply cross-trade. |
| Some PMs are completed/submitted by Vixxo-internal staff, not the SP. | WF04, ES Fairfax 1254/1250 submitted by `Deltwan.edwards@vixxo.com`. | Note for SP-quality attribution: a Vixxo email on a pmSurvey means internal completion, not the SP's own write-up. |
