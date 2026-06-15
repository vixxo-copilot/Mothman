# PM Survey Review

Reviews preventative-maintenance (PM) survey submissions for data
completeness, before/after photo coverage and quality, and additional repairs
needed, then emits a per-survey chat **review packet** with a verdict, owner,
and next action. Trade-agnostic.

## When to use
"Review this PM survey", "review these PM surveys", "audit these PM SRs",
"check the PM survey for SR <number>", or when handed survey PDFs to review.

## Two input modes
1. **SR list** — give SR numbers; the skill pulls the SR attachments
   (VixxoLink/Gateway), finds the survey PDF + before/after photos, and reviews.
2. **Attached PDFs** — review survey PDFs provided directly.

## How it works
- Data path: `vixxolink_get_service_request_attachments` -> presigned survey
  PDF + photos; reads PDF text and views photos (multimodal); survey completion
  date from the PDF/attachment timestamp (standard field).
- **"The form is the contract"**: only grades fields a given survey presents, so
  light-scope PMs aren't penalized and each customer's different form is handled.
- **Trade overlays** (`trades/`): hvac, coffee, water-filtration, refrigeration,
  roofing, plus a generic baseline. Each is scope-aware and customer/equipment
  -variance-aware (e.g., RO water systems, inspection-only forms).
- Verdict taxonomy: `pass | pass-with-gaps | data-incomplete | photos-insufficient | fail`.
- Owner routing: additional-repair scope -> Facilities Lead; survey
  data-quality / no-survey verification -> PM program team.

## Files
- `SKILL.md` — workflow.
- `review-packet.md` — verdict taxonomy + per-survey packet + cohort summary.
- `quality-rubric.md` — trade-agnostic scoring rubric.
- `trades/` — per-trade overlays (hvac, coffee, water-filtration, refrigeration,
  roofing, generic).
- `lessons-from-runs.md` — empirical patterns from real review runs.
- `metadata.yaml` — skill metadata.

## Validated against
Nordstrom (HVAC), Peet's (water filtration + espresso/coffee), Alliance
(refrigeration + HVAC), Safeway (roofing + water filtration).

Read-only: no outbound messages, no writes to SR/survey/attachments.
