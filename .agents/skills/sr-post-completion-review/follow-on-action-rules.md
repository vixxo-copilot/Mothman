# Follow-on action rules

## Inputs required

These rules assume SR triage Mode B has already produced:

- Decoded sub-status and `Job Complete` interpretation.
- SR graph with parent, child, sibling, same-asset, and same-FWKD context.
- Asset-data lineage gaps and owners.
- Recurring-failure and post-implementation flags.
- Documentation quality score.
- Quote status, quote notes, approved quote scope, and quote line items when quoted work exists or is likely.
- Quality signals from `.cursor/skills/sr-triage-pre-dispatch/reference/quality-signals.md`.

If any input is missing, state the missing input in packet field 12. Use `unknown` for work outcome when the missing input prevents a field-work call. Use `not-verified-documentation-gap` or `not-verified-functional-gap` for proof status depending on the gap.

## Fixture-level asset handling

Some plumbing and handyman SRs are fixture-level work where the SR may not expose a durable asset id, such as sinks, toilets, drains, doors, or dispensers. Do not treat "no asset id" as a Tech Dispatch or asset-master failure by itself.

When no asset id is available:

- State that same-asset recurrence and post-implementation checks are unresolved, not negative.
- Use site, LOS, symptom, FWKD, parent/child, and sibling search results for the best available graph.
- Lower confidence when asset history would materially change the operating call, such as recurring clogs, warranty rework, replacement decisions, or newly installed fixtures.
- Do not block `close-ready` solely because a fixture-level asset id is absent when completion is otherwise proven and no recurrence, warranty, follow-up, or invoice-risk signal is visible.

## Rule order

Evaluate in order. The first hard blocker sets the **completion proof status** and **final operating call**. Invoice/AP issues set **invoice disposition** and block `close-ready`, but do not rewrite the field-work outcome unless the invoice evidence also proves the work was not done.

### 1. Status contradiction and false-close

Set completion proof status `contradicted` and final operating call `false-close` when any condition is true:

- `Job Complete = Y` but decoded sub-status means scheduled, awaiting quote, awaiting customer, awaiting parts, or technician still on site.
- Exported or report data says complete while live SR status is open, in progress, quote pending, awaiting customer, or known ETA.
- Latest inspection or customer note says the issue remains after the SR was marked complete.
- Time events show no completed visit and no acceptable no-charge / cancellation explanation.

Attach or preserve `LIVE_STATUS_MISMATCH` when the evidence matches the SR triage quality-signal definition.

### 2. Completion proof gap

Set a proof gap when the closure record lacks any material proof element:

- Diagnostic: what failed or what was inspected.
- Action: what was repaired, replaced, adjusted, cleaned, reset, tested, quoted, or declined.
- Verification: how the SP confirmed function, safety, access, leak-free condition, site restoration, or customer acceptance.
- Signoff: customer/site acknowledgement when account workflow requires it.

Use work outcome `unknown` and proof status `not-verified-functional-gap` when the missing proof prevents knowing whether work is functionally resolved. Missing functional verification of the original symptom is a functional proof gap unless another record proves completion, such as photos, customer/site confirmation, sign-off in VIXLA/VixxoLink, inspection pass, time-event closeout detail, or a related SR carrying verified completion.

Use work outcome `resolved`, proof status `not-verified-documentation-gap`, final operating call `follow-up-required`, and follow-up type `documentation/verification correction` when the original symptom appears functionally resolved but required documentation, signoff, attachment access, structured work ticket, coaching, or cleanup remains. This is not `close-ready`; "looks complete" is not complete without required proof.

Use proof status `verified-complete` only after evaluating the work product, not just reading a status flag. Acceptable proof includes photos, detailed notes, inspection results, invoice/work-ticket evidence, customer confirmation, or customer/site sign-off in VIXLA/VixxoLink that shows the original durable scope is complete.

Use proof status `verified-temporary-relief` when that same evidence proves the immediate symptom was relieved, but a root-cause repair, quoted work, customer decision, compliance item, or other required follow-on remains. A temporary clear, reset, snake, patch, or bypass is not `verified-complete` when durable resolution is still open.

### 3. Inspection-generated work

Set final operating call `follow-up-required` when inspection notes identify any item that is not actioned on this SR or on a related SR:

- Repair or replacement needed.
- Quote required or quote promised.
- Return visit needed.
- Project scope recommended.
- PM correction or cadence adjustment.
- Warranty, chargeback, or installer rework.
- Safety, compliance, permit, landlord, lease, or customer-decision dependency.
- Asset/site data capture needed for future dispatch.

Use work outcome `unresolved` and final operating call `return-needed` when the inspection finding is part of the original scope and remains unresolved. Use work outcome `resolved` or `temporary-fix` and final operating call `follow-up-required` when the original scope was completed or temporarily relieved but the inspection created a separate next step.

### 4. Related-work check

Before declaring follow-on work missing, inspect the SR graph:

- If a child or sibling SR already carries the follow-on scope, do not call it missing. Packet field 5 must list that SR and its decoded status.
- If the follow-on scope exists only in notes and no parent/child/sibling SR, quote, task, or owner appears, set final operating call `follow-up-required`.
- If two SRs share the same FWKD, treat them as one work event for completion truth and invoice risk. Do not double-count the work.
- If a cancelled SR is a billing-only clone, suppress it from completion scoring and cite the original work SR.

### 5. Recurrence and temporary fix

Use work outcome `temporary-fix` or `unresolved` when same-asset recurrence shows the closeout did not address root cause:

- Same asset/symptom has 2 or more SRs in 90 days, or same-asset lookback reaches 180 days with structural evidence.
- Closeout is reset-only, snake-only, clean-only, descale-only, recharge-only, "no issue found," or brief test only on a recurring issue.
- Trade standard calls for camera/jet, leak search, replacement-vs-repair, warranty decision, or engineering review and no related work exists.

Use work outcome `unresolved` and final operating call `return-needed` when the same SR should not have closed without the deeper scope. Use work outcome `temporary-fix`, proof status `verified-temporary-relief`, and final operating call `follow-up-required` when the immediate condition was verified but a separate customer approval or project path is required.

### 6. Post-implementation, warranty, and chargeback

Set final operating call `follow-up-required` and invoice disposition `hold-ap` when failure occurs within 30 days of install or recently completed project work:

- Confirm installer, commissioning evidence, warranty status, and whether the dispatched SP is the install owner.
- Identify chargeback or no-charge path when the issue appears to be SP rework.
- If the customer was billed for likely warranty/installer rework, set invoice disposition `hold-ap`.

If install date is missing, route the gap through asset-data lineage and lower confidence.

### 7. Quote and customer-decision gaps

Set final operating call `follow-up-required` when notes say quote, approval, customer decision, landlord decision, lease review, or scope conversion is required and no related quote/work SR is visible.

Use work outcome `unresolved` and final operating call `return-needed` when the original SR cannot be resolved without that decision and the SR was still closed as complete.

### 7A. Quoted-work reconciliation

Run this rule when any of these quote signals are present:

- SR notes, sub-status, child SRs, sibling SRs, NTE changes, invoice notes, or inspection findings reference a quote, approval, scope conversion, capital work, parts quote, return quote, or customer decision.
- VixxoLink quote lookup fails, returns incomplete data, or is unavailable while other SR evidence suggests quoted work.
- Invoice or completion evidence refers to work that sounds broader than the original dispatch scope.

When this rule fires, check Gateway quote records when VixxoLink quote data is unavailable or incomplete. Use Gateway service-request, quote search, quote header, quote notes, quote attachments, and quote line-item tools as available. Preserve tool gaps in packet field 12.

Reconcile three scopes in order:

1. **Initial symptom:** customer request, short description, issue, asset/fixture, location, and urgency.
2. **Quoted scope:** approved quote text, notes, line items, attachments, NTE/price, customer approval, declined scope, and any exclusions.
3. **Completion scope:** resolution note, time events, photos, inspection, invoice line items, and customer/site signoff.

Set or adjust the packet as follows:

- If quoted scope does not address the initial symptom and the original symptom is not otherwise verified resolved, use work outcome `unresolved` or `unknown` depending on whether non-completion is proven.
- If completion evidence does not prove the approved quoted scope was performed, use proof status `not-verified-functional-gap`.
- If invoice or AP workflow is advancing and the quoted scope is not supported by approval, line items, photos, or completion evidence, set invoice disposition `hold-ap`.
- If the quote identified additional required work and no child SR, quote follow-up, customer decision, or owner is visible, use final operating call `follow-up-required` only when the original symptom is proven resolved or temporarily relieved; otherwise use `not-close-ready` or `return-needed`.
- If approved quoted work differs materially from the invoice/completion scope, flag quote-scope mismatch and route to SPM / AP reviewer before payment.

### 8. Invoice/AP risk

Set invoice disposition `hold-ap` or `hold-account-team` when any condition is true:

- Invoice starts before fix is verified.
- NTE increase or scope change has no supporting quote, photos, line items, or customer approval evidence.
- Quoted scope, completed scope, and invoice scope do not reconcile.
- Same site/SP/day/time window suggests duplicate billing.
- Trip charge follows cancellation without evidence of authorized truck roll.
- Customer/payment hold, disputed scope, or account-specific hold posture applies.
- Medium/high `invoice-risk` quality signal remains unresolved.

Invoice holds are payment disposition, not completion verdicts. If field work appears resolved but AP should pause payment, use work outcome `resolved`, proof status based on the evidence, final operating call `not-close-ready`, and invoice disposition `hold-ap` or `hold-account-team`.

### 9. Account intelligence threshold

Promote a finding to account intelligence only when it is durable:

- Repeats across 3 or more SRs in a cohort.
- Exposes account workflow friction, such as manual closeout requirements, customer portal evidence rules, payment hold dynamics, or inspection work not converting to child SRs.
- Changes how future SRs should be reviewed for the account.
- Creates executive watch value for a red/yellow COO-monitoring account.

Do not promote one-off SR details to account memory unless they carry material risk, money, customer trust, or process implications.

## Owner defaults

Use these defaults when a named person is unavailable:

| Finding | Default owner |
|---|---|
| Missing or weak SP completion note | SPM / SP manager |
| Follow-on quote or return visit | FL / SPM |
| Customer decision or approval | CSM / account owner |
| Invoice-risk or duplicate-billing review | AP reviewer / SPM |
| Quote-scope mismatch or quoted-work completion gap | SPM / AP reviewer |
| Asset-data or warranty write-back | Asset master owner / install-side write-back owner |
| Account workflow pattern | Account owner / operations leader |
| Trade-standard escalation | Governing trade skill owner / trade SME |

Every owner assignment needs a check-back. If no due date is known, use the next business day for high risk, 3 business days for medium risk, and 1 week for low risk.
