# Siebel sub-status decoder

> **Purpose.** Translate Vixxo Siebel `Substatus` values into plain-English meaning and operational guidance so the agent stops mistranslating them. Seeded from the 259-SR plumbing batch (April 2026); the cold-beverage cohort confirms the same set. Add new values as they appear in the wild.
>
> **Triggering symptom that drove this build.** On Ulta SR SR-EXAMPLE-001 (Riverbank 0784, hot water), the agent translated sub-status `Known ETA` as "closed to bill prematurely." It was not. The vendor had entered invoice line items while awaiting Ulta corporate direction. Carrie Kroeker flagged it on 2026-04-30 as a tuning opportunity for the agent.

## How to apply

1. Look up the SR's `Substatus` value in the table below.
2. Read the **Means** column. That is what the sub-status actually says about the SR.
3. Read the **Agent guidance** column. That is what the agent is allowed and not allowed to conclude from this sub-status.
4. Read the **Pairs with Job Complete = Y/N** column. Some sub-statuses are normal-with-Y, normal-with-N, and abnormal-with-the-other.
5. Pair with the **Substatus Grouping** field (`Friendly`, `Potentially Unfriendly`, `Unfriendly`, `Good`, `New`). That grouping is Vixxo's existing health tier on top of sub-status; honor it.

## Sub-status dictionary (real values, observed counts in the plumbing batch)

| Substatus | Plumbing-batch count | Typical Job Complete | Means | Agent guidance |
|---|---:|---|---|---|
| `Invoice Required for SR` | 123 | Y | Work is done; SP has not yet uploaded a billable invoice into Service Channel / Vixxo. The work happened; AP is waiting on paperwork. | Do **not** translate as "stuck" or "incomplete." Translate as "billing-side waiting on SP." Score callback risk only if other signals (no resolution note, customer dispute) exist. |
| `Invoice Review` | 62 | Y (rare N) | Invoice is in AP review. Reviewer is checking line items, NTE, photos, scope. | Do **not** treat as a quality flag by itself. Treat as a quality flag only if (a) ETA breach or (b) the SR has REPAIR_REVIEW or COST_OUTLIER signals already raised. |
| `Known ETA` | 27 | N (rare Y) | SP has provided an ETA that is in the future. Work is scheduled but not yet performed. | Do **not** translate as "closed to bill prematurely." If Job Complete is `Y` with this sub-status, that combination is itself a quality signal worth flagging (likely a system or vendor mis-step). Otherwise treat as "scheduled, on track unless ETA breaches." |
| `Delinquent SC Invoice` | 21 | Y | SP has not uploaded the Service Channel invoice within the SC SLA window. Vendor-side delinquency. | Translate as "vendor billing delinquency, AP follow-up needed." Do **not** translate as "Vixxo workflow problem" without checking SP scorecard / repeat-offender pattern. |
| `Quote Required` | 14 | N | Work needs a quote before proceeding. SP or Vixxo has identified scope that needs approval. | Treat as normal mid-flight. Score risk only if quote has been outstanding > the customer's quote-aging SLA (varies by account; check `MAGIC/memory/accounts/<slug>.md`). |
| `No ETA` | 12 | N | SP has not yet provided an ETA. | Treat as a watchpoint. Score escalation risk if the SR has been in `No ETA` past the TTA deadline. |
| `Technician On-site` | 10 | N | Tech is currently working the SR. | Treat as in-flight. Closure-quality scoring is not yet meaningful; wait for completion or note. |
| `FSN Ordered - Awaiting Parts` | 7 | N | Field service note indicates parts have been ordered. Waiting on parts to return. | Score risk on parts lead time, NLA flag, SLA exposure. Pair with quoting-anchors check from the trade base. |
| `Known ETA - Store Notified` | 6 | N | Same as `Known ETA` plus the store has been informed. | Treat exactly like `Known ETA`. The "store notified" qualifier is positive, not negative. |
| `No Time Out` | 5 | N | SP did not record a time-out at end of shift. Documentation gap, not necessarily a work-quality gap. | Flag for documentation discipline. Pair with the documentation-quality check (cold beverage cohort action 1). |
| `New ETA Required` | 4 | N | Original ETA is no longer valid. SP needs to provide a new one. | Score escalation risk if multiple ETA resets exist on the same SR (callback / SP reliability flag). |
| `Assigned to Service Contractor` | 4 | N | SR has been routed to an SP. SP has not yet acknowledged or scheduled. | Treat as early-stage. Score risk only if it has been in this state past the assignment SLA. |
| `Quoted - Submitted to Customer` | 4 | N | Quote has been sent to the customer for approval. | Treat as normal mid-flight. Pair with quote-aging by account. |
| `Action Pending - CRM` | 3 | N | A Vixxo CRM-side action is required (often a CSM or PM task). | Translate as "Vixxo-side ball." Surface owner for follow-up. |
| `Quoted - Approved by Customer` | 3 | N | Customer has approved the quote. SP can proceed. | Treat as positive forward motion. Score risk if no progress is observed within a reasonable scheduling window after approval. |
| `Quote Received` | 2 | N | SP has submitted a quote into the system. Vixxo or customer has not yet acted. | Translate as "Vixxo-side or customer-side ball." Surface owner. |
| `SC Ordered - Awaiting Parts` | 2 | N | Service Channel has ordered parts. Waiting on parts. | Same guidance as `FSN Ordered - Awaiting Parts`. |
| `Customer Order-Awaiting Parts` | 1 | N | Customer-furnished material on order. | Pair with site-readiness check; this is customer-side, not SP-side. |
| `Submit Quote to CRM` | 1 | N | A quote needs to be submitted into the CRM by Vixxo. | Vixxo-side action. Surface owner. |
| `No Invoice Pending` | 1 | N | No invoice is expected on this SR (often a no-charge or warranty case). | Do **not** flag as missing invoice. |
| `AR Successful` | 1 | Y | AR has booked the invoice successfully. Closed-loop financially. | Treat as fully resolved on the financial side. |
| `Cancelled` | (varies) | Either | The SR was cancelled before completion or in lieu of completion. Two distinct subtypes: (A) billing-only clone of a completed sibling SR, never dispatched, never carried labor; (B) genuinely cancelled mid-flight or post-dispatch where work may or may not have been performed. | Run the cancelled-SR triage in `sr-graph-resolver.md` Rule 7 to distinguish A from B. **Suppress Pattern A from cluster counts**; including a billing-only clone double-counts one repair. **Count Pattern B as a paired sibling** of any SR that carries the actual work record (group by FWKD overlap, Rule 6). Do not treat all cancelled SRs as evidence of a customer-experience failure; some are billing structures and some are genuine cancellations, and the operational meaning differs. |

## Cancelled SR sub-types

`Cancelled` is the highest-variance sub-status because it covers two operational realities that look identical on the substatus field but mean very different things.

**Pattern A — billing-only clone.** An SR with a description like `Clone of FWKD<num> - DO NOT DISPATCH`, a Tracking Hold note containing `Created for billing purposes only, do not dispatch`, and zero time-events. These exist as a Siebel-side billing structure to capture customer-internal-tech work or warranty interactions into the Vixxo billing flow. The actual repair lives on the original SR (the source of the FWKD reference). The cancelled clone never carried independent dispatch and should not be counted in cluster construction. Founding case: Lincoln ME SR `SR-EXAMPLE-019` (Run D, 2026-05-04 review).

**Pattern B — genuine mid-flight or post-dispatch cancellation.** An SR that was dispatched and either (1) cancelled because the customer reversed the request, (2) cancelled because the work was completed and billed under a sibling SR with the shared FWKD, or (3) cancelled because the original scope was rolled into a different LOS or dispatch. These SRs may carry time-events, partial resolution notes, or paired sibling SRs that hold the actual work record. Pattern B should be counted as a paired sibling of the SR carrying the work, grouped by FWKD overlap.

Apply the triage logic in `sr-graph-resolver.md` Rule 7 before assigning a verdict to any cancelled SR. The substatus value alone is not enough.

Note on the customer-billing workaround: Pattern A typically signals a process gap on the customer side (the customer is using cancellations and clones to capture customer-internal-tech repair into our billing flow because there is no proper disposition for it). The skill's job is to recognize the pattern and avoid double-counting. The customer-success conversation about the right disposition is a separate routing through the customer's AR / facilities owner, not a skill change.

## Substatus Grouping (Vixxo's existing health tier)

Vixxo already classifies sub-statuses into a Friendly/Unfriendly tier. Honor it. Do not invent your own.

| Grouping | Plumbing-batch count | Meaning |
|---|---:|---|
| `New` | 208 | Recently opened or recently transitioned; not yet a health signal. |
| `Friendly` | 37 | Sub-status is on a normal, healthy path. |
| `Potentially Unfriendly` | 37 | Sub-status is borderline. Watch closely. |
| `Unfriendly` | 16 | Sub-status reflects a real problem path. Triage now. |
| `Good` | 15 | Sub-status reflects a positive, closed-out condition. |

## Composing with Job Complete Flag

`Job Complete = Y` does not mean the work is verified. It means the SP has marked the work as complete. Three clean rules:

- **Y + `Invoice Required for SR` / `Invoice Review` / `Delinquent SC Invoice` / `AR Successful`** = normal post-work billing path. Closure-quality scoring applies based on resolution-note quality, not sub-status.
- **Y + `Known ETA`** = abnormal combination. The work cannot be both done and scheduled-for-the-future. Flag the SR for SP behavior review (likely premature close-to-bill or a system mis-step). This is the Riverbank 0784 pattern Carrie called out. **Attach the `LIVE_STATUS_MISMATCH` quality signal** (`reference/quality-signals.md`, family `repair-review`, severity `high`) when this combination fires. The same code applies whenever exported completion fields conflict with live status (CSV says complete but live status is `In Progress`, `Awaiting Quote`, `Awaiting Customer`, etc.).
- **Y + anything else** = inspect the resolution note before scoring. Sub-status alone is not enough.

`Job Complete = N` is normal in any mid-flight sub-status. Do not flag mid-flight `N` as a problem unless TTA / TTC deadlines are breached or the sub-status has aged past its SLA.

## Composing with Breached Description

`Breached Description` adds the SLA-time axis on top of sub-status. Combine, do not collapse.

| Breached Description | Plumbing-batch count | Operational meaning |
|---|---:|---|
| `Already Breached` | 123 | TTA or TTC has already been missed. Triage urgency. |
| `Other Not Breached` | 114 | Within SLA. Normal triage cadence. |
| `Breaching Two Days` | 47 | Will breach inside 48h. Escalation candidate. |
| `Breaching Tomorrow` | 29 | Will breach inside 24h. Escalation now. |

## When to extend this dictionary

Add a new row when you observe a Siebel sub-status not listed here. When you do, capture: the value, the typical Job Complete pairing, what it actually means in Vixxo workflow (confirm with operations if uncertain), and the agent guidance line. Do not invent meanings. Confirm with Maria Clavijo-Demchalk or the Operations team if a new sub-status appears and its meaning is not obvious from context.

**Last updated:** 2026-05-05 — added `Cancelled` row to the dictionary with the billing-clone-vs-genuine-cancellation distinction; added the Cancelled SR sub-types section pointing to `sr-graph-resolver.md` Rule 7 for the triage procedure. Driven by Run D Lincoln ME SR `SR-EXAMPLE-019` review with Brandon Covington and Jai (Amy Chasse's team review of the 2026-05-04 Circle K all-trades run). Founding version 2026-04-30 (seeded from plumbing batch + Carrie Kroeker reply).
