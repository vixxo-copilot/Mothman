# Post-facto application (Mode B)

> **Purpose.** Apply the same decoders during SR-quality review (after dispatch, mid-flight, or post-close) so the agent does not mistranslate sub-statuses, miss parent/child SRs, or attribute Siebel asset gaps to Tech Dispatch. Mode B is what the plumbing batch and the cold-beverage cohort were doing in April 2026; the lessons that drove this skill came from Mode B work.

## When to run Mode B

Run Mode B when:

- Reviewing closed SRs for quality, callback risk, repair-vs-replace discipline, documentation discipline, invoice integrity.
- Reviewing in-flight SRs for closure-quality scoring before AP releases payment.
- Building a cohort review (a hand-picked set of SRs across a customer, a trade, an SP, or a window).
- Building an aggregated quality dashboard for an account or for the SP base.

Do NOT run Mode B on:

- SRs that are at assignment or about to be dispatched. Use Mode A (pre-dispatch).
- A single SR fielded as a customer escalation. That is a real-time triage, not a quality review; use the trade skill directly.

## Check sequence

Mode B applies the same decoders as Mode A but uses them to score, not to route. Run in this order.

### Check 1 — Sub-status decoding before any closure-quality scoring

Read the SR's `Substatus` value. Apply `reference/sub-status-decoder.md`. Do NOT translate `Known ETA` as "premature close," do NOT translate `Invoice Required for SR` as "stuck," do NOT translate `Delinquent SC Invoice` as "Vixxo workflow problem."

If you are about to score the SR for closure quality, you must first state the decoded sub-status and its operational meaning in your output. The decoded meaning informs the score; the raw label does not.

### Check 2 — SR graph resolution before any "missing follow-up" claim

Run the SR graph resolver (`reference/sr-graph-resolver.md`). If you are about to flag "no replacement quote in flight," "no callback scheduled," "no return visit booked," or any other missing-follow-up claim, you must first list the parent and child SRs.

If a child SR carries the relevant scope, the verdict changes. State it explicitly: "Follow-up exists on child SR <number> with status <decoded sub-status>; verify status before scoring missing-follow-up."

### Check 3 — Asset-data lineage check before any Tech Dispatch verdict

Run the asset-data lineage check (`reference/asset-data-lineage.md`) for every "missing asset data" finding. Do NOT default to "Tech Dispatch failure." State the lineage owner explicitly.

This is where the SLX → Siebel migration gap at Ulta and the install-side write-back gap at Refuel get correctly attributed to data migration / asset master rather than to Tech Dispatch.

### Check 4 — Recurring-failure flag from the SR graph

If asset-sibling SRs ≥ 2 in 90 days, set the recurring-failure flag on this SR. Use it for:

- **Callback analysis** (the cold beverage retro action #13 category). Tag the SR for SP scorecard and customer reporting.
- **SP performance scoring.** A second visit on the same asset within 90 days hits the SP's first-time-fix rate. A third visit is a callback cluster.
- **Repair-vs-replace recommendation.** If the trade skill is about to score this SR as an acceptable repair, the recurring-failure flag forces a replacement-vs-repair conversation instead.

### Check 5 — Recently-installed-asset flag from the install date check

If `SR.createdDate - asset.installDate < 30 days`, set the post-implementation flag. Use it for:

- **Invoice integrity audit** (the cold beverage retro action #11 category). Confirm the customer was not invoiced for SP rework.
- **Chargeback case identification.** Flag for Maria / Stephanie review.
- **Install-defect investigation.** Pair with the multi-vendor install consideration (cold beverage retro section 3, "Multi-vendor installs are real").

If `asset.installDate` is missing, note explicitly that this check could not run, and pair with the asset-data lineage check to route the data gap.

### Check 6 — Documentation quality scoring

This is the cold beverage retro action #1 category. Score the SP write-up against a rubric:

- Symptom captured (what was wrong)
- Diagnostic captured (how was it confirmed)
- Parts / action captured (what was done)
- Verification captured (how do we know it is fixed)

Below-bar write-ups (Air America's three-for-three is the standing example) get flagged for SP onboarding compliance review per cold beverage retro action #12.

### Check 7 — Trade-specific quality scoring

Hand off to the governing trade skill for:

- Trade-fit (was the right SP type dispatched)
- Repair-vs-replace discipline at this trade's standard
- Root-cause-captured at this trade's standard
- Repeat-flag-captured at this trade's standard
- Install-defect-flag at this trade's standard
- OEM-warranty-leveraged at this trade's standard

The triage layer hands the trade skill a clean, decoded SR record. The trade skill does the trade-depth scoring on top.

## Mode B output

```
Quality review for SR <number>:

Decoded sub-status: <plain-English meaning + operational guidance>
SR graph: <summary, with verdicts dependent on graph noted>
Asset-data lineage: <gaps with owners, if any>
Recurring-failure flag: <yes/no, with cluster summary if yes>
Post-implementation flag: <yes/no, with delta if yes>
Documentation quality: <score against rubric>

Trade-specific scoring (from governing trade skill): <handoff or summary>

Quality verdict: <one of the cohort scoring axes - see lessons-from-runs.md for the multi-axis proposal>
Action items generated (if any): <listed with owner and check-back date>
```

## Composition with cohort review work

When running Mode B at scale (across a cohort of SRs):

1. Apply Mode B to each SR individually.
2. Aggregate findings to surface cross-SR patterns (cluster sites, cluster SPs, cluster customers, cluster trade-mismatches).
3. Score the SP base on documentation quality, repair-vs-replace bias, callback rate.
4. Surface system-level signals worth promoting to action items (the parent/child resolver was a system-level signal from a cohort run; the NEC loaded coverage gap was a system-level signal from a cohort run).

The cohort review writes findings into:

- `MAGIC/memory/actions.md` for tracked, owned, closed follow-ups (cold beverage retro action #14 category)
- `MAGIC/memory/accounts/<slug>.md` for account-specific durable context
- `docs/artifacts/sr-quality-review/` for the cohort artifact itself

## What this mode does NOT do

- It does not change dispatch decisions retroactively. SRs already dispatched stay dispatched. Mode B produces findings; routing changes only on the next SR.
- It does not produce trade-specific diagnostic depth. That is the trade skill's job.
- It does not own the multi-axis SR scorecard build (cold beverage retro action #7). That is a separate proposal heading to the SR-review leadership group (Maria, Amy, Will Olson, Derek).

## Future native primitive (FacilitiesOS)

Mode B is a prosthetic. The native build is tracked in `MAGIC/memory/actions.md` as part of the FacilitiesOS AI primitives backlog. Native primitive should:

- Apply the decoders as standard transforms on every SR record exposed to a review surface.
- Compute recurring-failure and post-implementation flags as derived properties on the SR record itself.
- Power the documentation quality gate at SR close (cold beverage retro action #1) so the SP cannot close low-quality SRs at will.
- Surface the multi-axis quality score on every SR rather than per-cohort calculation.

Until that lands, Mode B runs in the agent layer.

**Last updated:** 2026-04-30 (founding version)
