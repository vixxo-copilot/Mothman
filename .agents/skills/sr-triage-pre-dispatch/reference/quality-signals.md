# Quality signals — cross-trade vocabulary

> **Purpose.** Define the stable codes the agent attaches to an SR during triage so cohort runs aggregate, downstream consumers filter, and we can track which patterns repeat across trades. Originated in Maria Clavijo-Demchalk's plumbing-queue-monitor (Epic B / AIA-397) `quality-patterns.md` work; promoted here so every trade inherits the same vocabulary.
>
> **Triggering symptom that drove this build.** The plumbing batch and cold-beverage cohort surfaced repeat patterns (premature close-to-bill, temp fix on a recurring asset, missing dispatch context, wrong-trade routing, duplicate billing) but every reviewer described them in their own words. The cohort artifacts could not be aggregated. Stable codes fix that.

## How to apply

1. After the SR has been decoded (sub-status decoder), graphed (sr-graph-resolver), and lineage-checked (asset-data-lineage), evaluate every signal family below against the SR.
2. Attach zero or more signals. Each signal carries `family`, `code`, `severity`, `confidence`, and `evidence`.
3. Use the signals in two ways:
   - **Pre-dispatch (Mode A):** sharpen the customer-call recommendation and the trade-skill routing.
   - **Post-facto (Mode B):** sharpen the closure-quality verdict and surface the SR for invoice-integrity review.
   - **Mode C (next-action classifier):** drive the rule-based bucket decision (see `next-action-classifier.md`).
4. Do not invent signals from customer name alone. Every signal needs an `evidence` excerpt from SR fields, notes, or asset data.

## Signal record shape

```
{
  "family": "repair-review | predispatch-gap | invoice-risk",
  "code":   "STABLE_UPPER_SNAKE_CASE",
  "severity":   "low | medium | high",
  "confidence": "low | medium | high",
  "evidence": "<short note or field excerpt>"
}
```

## Family 1 — repair-review

Flag when the SR appears complete or in-flight but the fix is not verifiably permanent.

| Code | Trigger | Default severity |
|---|---|---|
| `JOB_COMPLETE_UNVERIFIED` | `Job Complete = Y` or "Work Completed" without a resolution note that names the fixture, asset, or method repaired. | medium |
| `LIVE_STATUS_MISMATCH` | Exported completion fields conflict with live status — CSV / report says complete but live status is `In Progress`, `Awaiting Quote`, `Known ETA`, `Awaiting Customer`. **Cross-references `sub-status-decoder.md` rule "Y + Known ETA = abnormal."** | high |
| `SYSTEM_RECORD_LAG` | TL or supervisor note documents on-site close-out (vendor on-site, parts swapped, customer signed off) but `subStatus`, `isJobComplete`, or time-events are still stale on the SR. Distinct from `LIVE_STATUS_MISMATCH` — that one fires when an export claims complete; this one fires when the field is complete but the system has not caught up. **Validated by Amy Chasse on 2026-05-03 5/3 packet.** | medium |
| `TEMP_FIX_ONLY` | Notes indicate reset, cleaned sensor, snake-only, descale-only, "no issue found", "tested briefly" on a recurring or material issue. | medium |
| `SHOULD_HAVE_PROJECT_SCOPE` | Recurring drain, sewer, hot-water, pinhole, root intrusion, mud, collapse, repeated cabling, or repeated same-asset failure should move toward camera-and-jet, spot repair, replacement, re-pipe, or warranty decision. | high |
| `CUSTOMER_SYMPTOM_NOT_ADDRESSED` | Resolution note solves a different symptom than the original request. | medium |

**Default effect:** favor `escalation` when paired with recurrence, SLA breach, high-impact terms, or invoice/payment risk; otherwise favor `follow-up` for SP/customer verification. Block `close` while a medium/high `repair-review` signal is unresolved.

## Family 2 — predispatch-gap

Flag when dispatch likely lacked critical context. These compose with `pre-dispatch-checks.md` and `asset-data-lineage.md`.

| Code | Trigger | Default severity |
|---|---|---|
| `MISSING_DISPATCH_CONTEXT` | Asset make/model/serial/install date/warranty missing, or site access / cleanout / shutoff / store-hours / landlord responsibility / photos / prior-call history not in the dispatch packet, after the lineage owner has been identified. | medium |
| `MISSING_FWKD_WO_NUMBER` | Open SR has no `workOrderNumber` (FWKD) populated. Customer-facing FWKD is the Nuvolo-completion + invoicing key. Per Amy Chasse 2026-05-03: "Without the FWKD, we will struggle with completing the work order in Nuvolo and we won't be able to invoice it." Common cause: CSR manually creates an SR and forgets to enter the FWKD. Founding case: SR `SR-EXAMPLE-033` (Farmington ME, 5/3 run). | high |
| `SENTINEL_SITE_INTAKE_BOT_LATENCY` | SR is created against `site.number = 99999` because the **On Demand Site Creation BOT** did not finish creating the real store within the dispatcher's SLA budget. SOP cadence is 20 minutes; founding case ran 35 minutes against a 4-hour P0 SLA. Distinct from a routing miss — the dispatcher is using 99999 as a deliberate fallback and submits an IT ticket to re-point the SR onto the real store after the bot creates it. Founding case: SR `SR-EXAMPLE-034` (Colorado Springs CO 2703296, 5/3 run, validated by Amy Chasse). | medium |
| `CLONE_PARENT_NOT_VIXXO_RUN` | SR description carries a "Clone of FWKD<num>" or similar tag, and a `vixxolink_search_service_requests` lookup on that FWKD returns no parent SR — meaning the cloned WO is customer-side or external. Per Amy Chasse 2026-05-03: do not ask the SPM to chase a Vixxo resolution note that does not exist. Founding case: SR `SR-EXAMPLE-033` referencing FWKD7231659 (5/3 run). | low |
| `SITE_BUILDING_SYSTEMS_UNKNOWN` | Drain / hot-water / electrical / fuel / gas SR at a site without recorded building-systems metadata in the site-master record (`wastewaterDisposal`, `waterSupply`, `gasService`, `electricService`, `floodPlainStatus`). Default severity: medium on recurring drain or recurring hot-water SRs (where sewer-vs-septic, or hard-water-vs-soft, drives scope); low on first-time SRs. Founding case: Farmington ME drain SR `SR-EXAMPLE-033` (5/3 run, sewer-vs-septic resolved by external research). | medium |
| `WRONG_TRADE_ROUTING` | LOS or short description routes to a trade that does not match the symptom or asset. Cold-beverage cohort: 9 of 11 SRs booked under "Cold Beverage Equipment" needed a different governing skill. Plumbing batch: leaking-pipe ticket that was actually a drain backup (Minnetonka 0065). | high |
| `INTAKE_TAXONOMY_MISMATCH` | Intake mis-labels the symptom (toilet vs urinal, leaking pipe vs drain backup, plumbing vs handyman, plumbing vs electrical). Distinct from wrong-trade routing — same trade, wrong scope. | medium |
| `SP_TYPE_MISMATCH` | Customer asked for vac truck, camera, jetter, replacement, project scope and a generalist was dispatched instead. | high |

**Default effect:** favor `dispatch` only if the SR is unassigned **and** correctly categorized; otherwise use `escalation` for wrong-trade routing or `follow-up` to collect missing context before the next SP action. Pair with the asset-data lineage check before declaring "Tech Dispatch failure."

## Family 3 — invoice-risk

Flag when AP should review before payment. Composes with `post-facto-application.md` Check 6 (documentation) and downstream AP workflow.

| Code | Trigger | Default severity |
|---|---|---|
| `DUPLICATE_BILLING_RISK` | Same site, same SP or tech, same day, overlapping first-time-in / last-time-out windows, repeated trip/labor charges, or paired SRs for one truck roll. | high |
| `NO_SUPPORTING_QUOTE` | NTE increased or scope changed without an attached quote, photos, line items, or clear tech notes. | high |
| `INVOICE_BEFORE_FIX_VERIFIED` | Invoice review starts while symptoms remain unresolved or callback risk is high. | high |
| `TRIP_CHARGE_AFTER_CANCEL` | Customer or portal cancellation predates the SP truck roll. | medium |
| `RESTORATION_NOT_LINE_ITEMED` | Sewer / grease / underground project closed without restoration line items (asphalt, concrete, landscape, sidewalk patch). Plumbing-specific cue from the trade base. | medium |

**Default effect:** favor `escalation` when payment hold, consolidation, dispute, or rejection-with-reason is needed; otherwise `follow-up` for missing documentation. Block `close` while a medium/high `invoice-risk` signal is unresolved.

## Severity, confidence, and the close-blocker

The agent's classifier (Mode C) treats severity and confidence together:

- `severity = high` AND `confidence in [medium, high]` → strong driver toward `escalation`.
- `severity = medium` AND `confidence in [medium, high]` → strong driver toward `follow-up`.
- `confidence = low` → keep the signal for context but do not let it override deterministic SLA / dispatch rules.

Any unresolved `repair-review` or `invoice-risk` signal at `confidence in [medium, high]` blocks the `close` bucket. Route through `follow-up` or `escalation` instead.

## Composing with other triage components

| Component | How to compose |
|---|---|
| `sub-status-decoder.md` | `Job Complete = Y` paired with `Known ETA` is the canonical `LIVE_STATUS_MISMATCH` trigger. |
| `sr-graph-resolver.md` | Recurrence on the same asset is the canonical `SHOULD_HAVE_PROJECT_SCOPE` trigger when the trade calls for camera, replacement, or warranty decision. |
| `asset-data-lineage.md` | Identify the lineage owner first; tag `MISSING_DISPATCH_CONTEXT` only when the gap is real and routed. |
| `pre-dispatch-checks.md` | Use `WRONG_TRADE_ROUTING` and `SP_TYPE_MISMATCH` to feed Check 5 (trade-skill routing). |
| `post-facto-application.md` | Use the full signal list to drive Check 6 (documentation) and Check 7 (trade-specific scoring). |
| `next-action-classifier.md` | Mode C rules read severity + confidence to pick `dispatch / follow-up / escalation / close`. |

## Evidence standards

- Every emitted signal must include a short evidence string drawn from SR fields, notes, or asset data.
- Do not infer a signal from customer name, SP name, or sub-status grouping alone.
- If the evidence is weak, set `confidence = low` and let downstream rules ignore the signal for routing.
- Capture the exact field, note line, or asset attribute that produced the signal so a reviewer can validate.

## Extending this vocabulary

Add a new code when:

1. The pattern repeats across runs OR is severe enough to warrant a one-shot rule.
2. The code has a clear input (what the agent sees), a clear default severity, and a clear evidence pattern.
3. The pattern is not already covered by an existing code under a clearer name.

When you add a code, update the relevant table here, add a row to `lessons-from-runs.md` citing the run that surfaced it, and reference the new code from `next-action-classifier.md` if it should affect bucket selection.

## Future native primitive (FacilitiesOS)

This vocabulary is a prosthetic. The native build is tracked in `MAGIC/memory/actions.md` as part of the FacilitiesOS AI primitives backlog. Native primitive should:

- Tag every SR with applicable quality signals as a derived property at write time.
- Expose the signal list to the dispatch UI, the SR review surface, and AP workflow filters.
- Power the close-blocker as a workflow gate rather than a per-query agent rule.

Until that lands, the agent layer attaches signals at triage time.

**Last updated:** 2026-05-03 — added `SYSTEM_RECORD_LAG`, `SENTINEL_SITE_INTAKE_BOT_LATENCY`, `MISSING_FWKD_WO_NUMBER`, `CLONE_PARENT_NOT_VIXXO_RUN`, `SITE_BUILDING_SYSTEMS_UNKNOWN`, all promoted from the 2026-05-03 Circle K all-trades run after Amy Chasse's review. Original founding version 2026-05-01 (promoted from `plumbing-queue-monitor/quality-patterns.md` by Maria Clavijo-Demchalk; generalized for cross-trade use).
