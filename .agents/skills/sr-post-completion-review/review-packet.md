# Post-SR completion intelligence packet

## Purpose

Use this packet after SR triage Mode B has decoded the SR. The packet answers one operating question: did the work really finish, or did the closeout create follow-on work that needs ownership?

## Completion outcomes

Do not force one blended verdict to answer every question. Separate the service outcome from the documentation, follow-up, and invoice disposition.

### Work outcome

Use exactly one work outcome per SR.

| Outcome | Meaning |
|---|---|
| `resolved` | The original symptom appears functionally resolved based on diagnostic, corrective action, and verification evidence. |
| `temporary-fix` | The immediate symptom was relieved, but root cause, recurrence, or inspection evidence shows durable resolution is still needed. |
| `diagnostic-only` | The SR identified the issue but did not complete repair. |
| `unresolved` | Evidence shows the original symptom remains or material work was not completed. |
| `unknown` | Available records do not prove whether the original symptom was resolved. |

### Completion proof status

Use exactly one proof status per SR.

| Proof status | Meaning |
|---|---|
| `verified-complete` | The work product has been evaluated and proves completion: photos, notes, inspection results, invoice/work-ticket evidence, customer confirmation, or customer/site sign-off in VIXLA/VixxoLink show the original durable scope is complete. |
| `verified-temporary-relief` | Evidence proves the immediate symptom was relieved, but root cause, durable repair, customer decision, or follow-on scope remains. |
| `not-verified-documentation-gap` | Work may be functionally complete, but required documentation is missing, weak, unstructured, inaccessible, or contradictory. The SR is not close-ready. |
| `not-verified-functional-gap` | Documentation does not prove the original symptom was functionally resolved. |
| `contradicted` | Status, notes, inspection, time events, quote state, customer evidence, or related work contradict the claimed completion. |

### Invoice disposition

Use exactly one invoice disposition per SR.

| Invoice disposition | Meaning |
|---|---|
| `ready` | Invoice can proceed based on available completion, quote, line-item, and account evidence. |
| `hold-ap` | AP should pause payment or approval because invoice risk remains. |
| `hold-account-team` | Account team or customer-facing owner must resolve a documentation, approval, related-SR, or customer workflow gap before payment. |
| `insufficient-invoice-evidence` | Invoice readiness cannot be determined from available records. |
| `not-reviewed` | Invoice data was unavailable or not in scope. |

### Final operating call

Use exactly one final operating call per SR.

| Operating call | Meaning |
|---|---|
| `close-ready` | Work is verified, no required follow-up remains, and invoice disposition is `ready` or `not-reviewed`. |
| `not-close-ready` | Work may be resolved, but completion proof, invoice disposition, or an unresolved blocker prevents clean closeout and the exact follow-up is not yet known. |
| `follow-up-required` | Original symptom is resolved or temporarily relieved, but a named next action is required, including documentation or verification correction. |
| `return-needed` | A return visit is needed to complete the original work. |
| `false-close` | Completion is claimed but contradicted by the evidence. |

## Per-SR packet

Do not collapse fields into prose. Keep evidence tied to SR fields, notes, related SRs, photos, quotes, or time events.

```markdown
Post-SR completion review - SR <number>

1. Work outcome: <resolved | temporary-fix | diagnostic-only | unresolved | unknown>
2. Completion proof status: <verified-complete | verified-temporary-relief | not-verified-documentation-gap | not-verified-functional-gap | contradicted>
3. Final operating call: <close-ready | not-close-ready | follow-up-required | return-needed | false-close>
4. Work performed: <literal SP / inspection / resolution evidence; quote exact words when they drive the call; include approved quote scope when quoted work exists>
5. Proof of completion: <diagnostic, corrective action, functional verification, customer/site signoff; for quoted work, reconcile initial symptom -> quote scope -> completion scope; say "not present" for missing elements>
6. Follow-up required: <none | documentation/verification correction | quote | return visit | project scope | PM correction | warranty/chargeback | customer decision | account-team escalation> with the exact missing item or next action
7. SR graph and related work: <parent, child, sibling, same-FWKD work; state whether follow-up already exists or is missing>
8. Inspection findings: <findings captured, findings not actioned, and asset/site memory to write back>
9. Invoice disposition: <ready | hold-ap | hold-account-team | insufficient-invoice-evidence | not-reviewed> with invoice/AP risk reason
10. Owner and check-back: <named person/function where available, due/check-back cadence, or "owner unresolved">
11. Account intelligence: <durable account signal if any; otherwise "none">
12. Confidence and evidence gaps: <high | medium | low, with missing inputs that would change the operating call>
```

## Field rules

- **Fields 1-3 are the operating answer.** Field 1 says what likely happened in the field. Field 2 says whether completion is proven. Field 3 says what the business should do next. Do not hide documentation or invoice problems inside the work outcome.
- **Verified complete means the work product was evaluated.** Do not use `verified-complete` because a closeout note says "job complete" or because `Job Complete = Y`. Use it only when photos, notes, inspection results, invoice/work-ticket evidence, customer confirmation, or customer/site sign-off in VIXLA/VixxoLink prove the original durable scope is done.
- **Temporary relief is not verified complete.** When notes, photos, customer confirmation, or sign-off prove the immediate symptom stopped but root cause or a required follow-on remains, use `verified-temporary-relief`, not `verified-complete`.
- **Looks complete is not complete.** If the work appears functionally resolved but required proof is missing, use `resolved` or `temporary-fix` in Field 1, `not-verified-documentation-gap` in Field 2, `follow-up-required` in Field 3, and `documentation/verification correction` in Field 6.
- **Missing functional verification blocks completion proof.** If the original symptom lacks functional verification, use `not-verified-functional-gap` unless photos, customer confirmation, inspection, time events, or a related SR clearly prove resolution.
- **Contradiction is stronger than a documentation gap.** If completion is contradicted, use `contradicted` in Field 2 and `false-close` in Field 3.
- **Field 4 is literal evidence.** Quote the SP, inspection note, customer note, or resolution note before adding inference.
- **Field 5 requires all four proof elements when available:** symptom/diagnostic, action taken, functional verification, and customer/site acknowledgement. If a proof element is absent, say "not present."
- **Quoted-work reconciliation:** When quoted work exists or is likely, Field 5 must state whether the approved quote scope addresses the initial symptom and whether completion evidence proves the quoted scope was performed. If VixxoLink quote data is blocked or incomplete, check Gateway quote records before finalizing or state the Gateway gap in Field 12.
- **Field 6 names the next work, not the generic concern.** "Open quote for drain camera and jet due to third snake-only closeout" is better than "follow up on drain."
- **Field 7 prevents false "no follow-up" claims.** If a child SR or sibling SR already carries the next work, the packet must say so and verify its status.
- **Field 8 treats inspection as work generation.** Any inspection note that identifies repair, quote, warranty, chargeback, PM, safety, compliance, or customer-decision work belongs here.
- **Field 9 separates payment readiness from service completion.** AP/account-team holds do not automatically mean the field work failed, but they do block `close-ready`.
- **Field 10 must be actionable.** Name the owner by role if a person is unavailable: FL, SPM, CSM, account owner, AP reviewer, SP manager, asset master owner.
- **Field 11 is durable account intelligence only.** Do not restate normal SR facts. Capture repeat patterns, workflow friction, closure standard gaps, customer-specific evidence requirements, or recurring provider behavior.
- **Field 12 calibrates confidence.** Low confidence means the next action is evidence collection, not operational certainty.

## Cohort summary

Start cohort runs with this summary.

```markdown
Post-SR completion review - cohort summary

Scope: <account / trade / SP / site / date window>
SRs reviewed: <n>
Work outcomes: resolved <n>, temporary-fix <n>, diagnostic-only <n>, unresolved <n>, unknown <n>
Proof status: verified-complete <n>, verified-temporary-relief <n>, not-verified-documentation-gap <n>, not-verified-functional-gap <n>, contradicted <n>
Operating calls: close-ready <n>, not-close-ready <n>, follow-up-required <n>, return-needed <n>, false-close <n>
Follow-on actions: documentation/verification correction <n>, quote <n>, return visit <n>, project scope <n>, PM correction <n>, warranty/chargeback <n>, customer decision <n>, account-team escalation <n>
Invoice dispositions: ready <n>, hold-ap <n>, hold-account-team <n>, insufficient-invoice-evidence <n>, not-reviewed <n>
Repeated patterns: <top 3-5 patterns with evidence, including quote-scope mismatch if present>
Recommended action capture: <actions with owner/check-back, or "none">
Durable account intelligence: <signals to consider for account memory, or "none">
```

## Escalation threshold

Escalate the cohort, not just the SR, when any pattern repeats across 3 or more SRs in the run, any high-severity invoice-risk signal appears, or inspection findings repeatedly fail to generate child SRs, quotes, or owner-assigned follow-up.
