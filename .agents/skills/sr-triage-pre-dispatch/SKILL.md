---
name: sr-triage-pre-dispatch
description: Living triage layer for Vixxo Service Requests. Three modes — pre-dispatch (run at SR assignment to surface prior-failure triggers, asset-history risk, parent/child SR linkage, sub-status truth, asset-data lineage, and dispatch packet completeness before the SP gets the call), post-facto (run during SR-quality review to apply the same decoders so the agent does not mistranslate Siebel sub-statuses, miss parent/child SR siblings, or attribute Siebel asset-record gaps to Tech Dispatch), and next-action classifier (sweep an open-SR queue and bucket each SR into dispatch/follow-up/escalation/close with deterministic rules and an LLM fallback). Built from real plumbing-batch, cold-beverage-cohort, and Epic B plumbing-queue-monitor findings (Apr 2026). Trade skills inherit this layer and call it before any dispatch read, any closure-quality scoring, or any queue sweep. Use when triaging an SR before dispatch, reviewing closed/in-flight SRs for quality, classifying an open queue, or building agent loops over SR data.
disable-model-invocation: true
---

# Vixxo SR Triage — Pre-Dispatch, Post-Facto, and Next-Action Classifier

> **What this is.** A living triage layer that sits between Siebel/VixxoLink/Gateway data and any trade skill. Every trade inherits the rules here. The skill is intentionally written to evolve as we learn.
>
> **Why it exists.** Three real builds in April–May 2026 (200+ SR plumbing batch, 11 SR cold-beverage cohort, Maria Clavijo-Demchalk's plumbing-queue-monitor for Epic B) surfaced patterns that no single trade skill should re-learn: agents reading SRs in isolation, mistranslating Siebel sub-statuses, attributing data-migration gaps to dispatch, missing prior-failure asset history before sending the truck, describing the same quality problems in different words across cohort runs. This skill bakes those rules in once.

## Three operating modes

This skill runs in one of three modes. State the mode explicitly at the top of any output. Modes A and B produce *findings*; Mode C produces a *next-action bucket* per SR.

### Mode A — Pre-dispatch (the cadence we are after)

Triggered when an SR is at assignment and has **not yet been routed to an SP**. The agent runs before dispatch to produce a **dispatch intelligence packet** — not a dispatch recommendation.

1. **Resolve the SR graph.** Pull parent SR, child SRs, and sibling SRs on the same site/asset within the last 90 days. Surface any open or recently-closed work that bears on this dispatch.
2. **Run the prior-failure trigger.** If the same site has 2+ closed SRs on the same asset/symptom in the last 90 days, this is no longer a routine first-time call. Recommend a customer call before dispatch with a specific upgrade or scope change (camera-and-jet vs cable on a recurring drain, replacement-vs-repair on a recurring asset, install-defect investigation on a recently-installed asset).
3. **Run the recently-installed-asset check.** If `SR.createdDate - asset.installDate < 30 days`, mark as potential post-implementation case. Surface install owner and install warranty status. This work may be on the SP, not the customer.
4. **Run the dispatch packet completeness check.** Asset make/model/serial, install date, warranty status, prior-call summary, site access, customer contact. If anything is missing, classify the gap with the asset-data lineage check before declaring "Tech Dispatch failure."
5. **Run the trade-skill routing check.** Confirm the LOS + Short Description routes to the right governing trade skill (this is where future LOS → trade-skill mapping work plugs in).
6. **Output a dispatch intelligence packet** with eight fields: recommended decision, hard evidence, prep required, onsite actions, customer/provider asks, asset-memory updates, owner, and confidence. The packet separates prep before the truck rolls, actions onsite during the visit, and evidence captured for the asset/location graph so next time is smarter. Schema in `reference/pre-dispatch-checks.md`.

**Operating posture — shadow mode.** Mode A runs in shadow mode while the schema stabilizes: the packet is produced and reviewed, the dispatch decision stays with the human dispatcher. Promote to a live recommendation surface only after override-capture data shows the schema is stable across runs.

**Fixture-level identity (lightweight).** Asset-memory updates in field 6 should include fixture-level identity where the SR is fixture-specific (toilets, sinks, sensors, dispensers). "Men's Room Toilet 2 — Sloan Optima ETF-880, install 2024-08-12, parts warranty 2027-08-12" beats "restroom toilet, no detail." Lightweight is fine; precision is not.

### Mode B — Post-facto (review of in-flight or closed SRs)

Triggered when reviewing SRs after they have been dispatched, are mid-execution, or are closed. The agent runs to score quality and surface findings:

1. **Apply the sub-status decoder before any closure-quality scoring.** Do not translate `Known ETA` as "closed to bill prematurely," do not translate `Invoice Required for SR` as "stuck," do not translate `Delinquent SC Invoice` as "vendor problem." Use the decoder.
2. **Resolve the SR graph before any "missing follow-up" claim.** If the agent is about to flag "no replacement quote in flight" or "no callback scheduled," check parent/child/sibling SRs first. The follow-up may already exist on a related ticket.
3. **Apply the asset-data lineage check before flagging missing asset data.** Distinguish "the SP got an empty dispatch packet" (Tech Dispatch issue) from "Siebel asset record was empty when the dispatch packet was built" (data migration / asset master / customer-furnished data issue). Route the gap to the right owner.
4. **Apply the prior-failure check retroactively.** If the SR is part of a 2+ SR cluster on the same asset within 90 days, score callback risk and flag for callback analysis, not just first-time-fix scoring.
5. **Apply the recently-installed-asset check retroactively.** If failure is within 30 days of install, raise the post-implementation flag and route to invoice-integrity audit.
6. **Attach quality signals.** Use `reference/quality-signals.md` to tag the SR with stable codes from the `repair-review`, `predispatch-gap`, and `invoice-risk` families. Block any "close" verdict while a medium/high `repair-review` or `invoice-risk` signal is unresolved.

### Mode C — Next-action classifier (queue sweep)

Triggered when sweeping a queue of open SRs (single trade, single customer, mixed) and the dispatcher or downstream agent needs a prioritized "what to work next" list. Mode C consumes the decoded record produced by Modes A and B and returns one of four canonical buckets — `dispatch / follow-up / escalation / close` — per SR, plus a `runDiffStatus` (`new / moved-bucket / unchanged / cleared`) compared with the previous run.

The full rule order, cadence thresholds (P1 / P2 / P3 ETA grace, escalation age, recurrence lookback, follow-up note staleness), LLM fallback policy, and run-diff + override-capture discipline live in `reference/next-action-classifier.md`. Trade skills should call Mode C *only after* Modes A or B have decoded the SR record. The classifier does not invent its own decoders.

Maria Clavijo-Demchalk's plumbing-queue-monitor (Epic B / AIA-397) is the first production implementation of Mode C. Other trades inherit the same scaffolding with their own quality signals and account-tuned thresholds.

## Reference files (read on activation)

| File | When to read |
|---|---|
| `reference/sub-status-decoder.md` | Always (all modes). Real Siebel sub-statuses with plain-English meaning and operational guidance. |
| `reference/sr-graph-resolver.md` | Always (all modes). How to pull parent/child/sibling SRs and how to use them. |
| `reference/asset-data-lineage.md` | Always (all modes). How to distinguish dispatch-packet gaps from Siebel-record gaps. |
| `reference/quality-signals.md` | Always (all modes). Stable cross-trade vocabulary for `repair-review`, `predispatch-gap`, and `invoice-risk` codes; close-blocker rule. |
| `reference/pre-dispatch-checks.md` | Mode A. Prior-failure trigger, recently-installed-asset check, dispatch packet completeness checklist. |
| `reference/post-facto-application.md` | Mode B. How the decoders apply during SR-quality review and how to compose with trade-skill diagnostic logic. |
| `reference/next-action-classifier.md` | Mode C. Ordered rule set with cadence thresholds and LLM fallback for `dispatch / follow-up / escalation / close` bucketing; run-diff and override-capture discipline. |
| `reference/lessons-from-runs.md` | Always. The empirical patterns this skill is built on (plumbing batch + cold-beverage cohort + plumbing-queue-monitor). |

## How trade skills call this layer

Trade skills (`trades-plumbing`, `trades-cold-frozen-beverage`, `trades-ice-machines`, etc.) inherit this layer. They do NOT re-publish its logic.

**Pattern in trade skills:**

```
Before responding:
1. If pre-dispatch: read sr-triage-pre-dispatch SKILL.md and run Mode A. Use its output as the input to your trade diagnostic.
2. If post-facto: read sr-triage-pre-dispatch SKILL.md and run Mode B. Apply its decoders before any closure-quality scoring you produce.
3. If sweeping an open queue: read sr-triage-pre-dispatch SKILL.md and run Mode C after Modes A/B have decoded the records. Emit the four-bucket classification with run diff.
4. Then read the shared trade base and your own trade reference files.
```

The triage layer produces the pre-dispatch packet, the decoded SR record, or the bucketed queue; the trade skill produces the technical diagnostic and recommendation.

## Behavioral constraints (every mode, every trade)

- Never declare "no follow-up" without first running the SR-graph resolver.
- Never emit a Mode A packet on an SR whose `vixxolink_get_related_service_requests` returned empty without first running the `vixxolink_search_service_requests` fallback per `sr-graph-resolver.md` Rule 6 and `pre-dispatch-checks.md` Check 1. An empty related result is not "graph resolved"; it is "fallback required."
- Never declare "closed to bill prematurely" or any other closure-quality verdict without first running the sub-status decoder.
- Never declare "Tech Dispatch sent an empty packet" without first running the asset-data lineage check.
- Never recommend a routine truck roll on an SR that the prior-failure trigger flags as recurring. Recommend a customer call first.
- When the dispatch packet is incomplete, name the gap owner (Tech Dispatch / data migration / asset master / customer-furnished data) instead of a generic "missing data" flag.
- Never emit a Mode C `close` verdict while a medium- or high-confidence `repair-review` or `invoice-risk` quality signal is unresolved. Route through `follow-up` or `escalation` instead.
- Never silently drop a dispatcher override of a Mode C verdict. Capture every override (`skillSaid` / `actualWas` / reason) and feed it back into the rules or the lessons file.

## Run discipline (cohort and queue runs)

When this skill runs across a cohort (Mode B at scale) or a queue (Mode C), apply two living-document disciplines:

- **Run diff.** Compare the current run against the most recent prior run and surface aggregate counts of `new`, `moved-bucket`, `unchanged`, and `cleared` SRs at the top of the output. Per-SR `runDiffStatus` lets reviewers focus on what changed since last sweep instead of re-litigating every SR.
- **Override capture.** When a dispatcher or reviewer overrides a verdict (the agent said `escalation`, the actual call was `follow-up`), record the override with the SR id, what the skill said, what the actual call was, and the reason. Productionized agent skills (Maria's plumbing-queue-monitor) persist overrides to `runs/<timestamp>/overrides.json`. Ad-hoc cohort reviews append a row to `reference/lessons-from-runs.md` and, if the pattern repeats, promote a refinement into a decoder rule, a quality-signal code, or a Mode C threshold.

Both disciplines are described in detail in `reference/next-action-classifier.md`; they apply equally to Mode B cohort artifacts.

## What this skill does NOT do

- It does not produce trade-specific diagnostic depth. That is the trade skill's job.
- It does not replace the universal trade base (`_shared/reference/vixxo-trade-operating-base.md`). It sits in front of it.
- It does not own the FacilitiesOS native primitive build. The platform-side build is tracked separately in `MAGIC/memory/actions.md`. This skill is the agent-side prosthetic until the native build lands.

## Living document

This skill is expected to grow. New patterns from trade-cohort reviews land in `reference/lessons-from-runs.md`; new sub-statuses observed in the wild land in `reference/sub-status-decoder.md`; new pre-dispatch checks land in `reference/pre-dispatch-checks.md`. Update the references first, then update this SKILL.md only if the mode logic itself changes.

**Owner:** Jim McCarthy
**Founding evidence:**
- `docs/artifacts/sr-quality-review/customer-issue-brief.md` (plumbing batch findings)
- `docs/artifacts/sr-quality-review/carrie-ulta-response-synthesis-2026-04-30.md` (Carrie's reply driving the parent/child resolver, sub-status decoder, asset-data lineage)
- `docs/artifacts/cold-beverage-cohort-retrospective-2026-04-29.md` (cold beverage cohort lessons)
- `docs/artifacts/sr-agent-runs-technical-review-derek-2026-04-30.md` (Derek brief, primitive frame)
- Maria Clavijo-Demchalk's plumbing-queue-monitor skill (Epic B / AIA-397) — promoted the quality-signal vocabulary and the next-action classifier rule scaffold into this triage layer 2026-05-01
- `docs/artifacts/sr-triage-runs/circle-k-plumbing-2026-05-01.md` (Circle K plumbing pre-dispatch run; Derek + Maria reads on 2026-05-01 promoted the dispatch-intelligence-packet schema and the shadow-mode operating posture)
