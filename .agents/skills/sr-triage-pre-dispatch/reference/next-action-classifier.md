# Next-action classifier (Mode C)

> **Purpose.** Classify each open SR into one of four canonical next-action buckets — `dispatch / follow-up / escalation / close` — using an ordered, deterministic rule set with an LLM fallback for unmatched SRs. Mode A and Mode B produce *findings*; Mode C produces a *bucket* the dispatcher (or a downstream agent) can act on. Originated in Maria Clavijo-Demchalk's plumbing-queue-monitor (Epic B / AIA-397) `rules.md` work; promoted here so every trade inherits the same classifier scaffold.
>
> **Triggering symptom that drove this build.** The plumbing batch surfaced 259 SRs with no shared decision rule for "what does this SR need next?" Reviewers used personal judgment, descriptions varied, the cohort artifact could not aggregate. Maria built the rule engine for the plumbing trade pod; this file generalizes it.

## When to run Mode C

Run Mode C when:

- Sweeping a queue of open SRs (single trade, single customer, mixed) and you need a prioritized "what to work next" list.
- Producing a per-SR next-action handoff for downstream automation (auto-dispatch, SP status checks, escalation comms, customer cadence).
- Refreshing a trade-pod or account-pod canvas before a standup.

Do NOT run Mode C on:

- A single SR fielded as a customer escalation. That is real-time triage; use the trade skill directly.
- An SR that has not yet been through Mode A or Mode B decoders. The classifier expects a decoded record.
- PM-cadence dispatches that are calendar-driven, not failure-driven.

## Inputs the classifier expects

Each SR record handed to Mode C must already carry:

| Field | Source |
|---|---|
| `status`, `Substatus`, `Substatus Grouping`, `Job Complete` | `sub-status-decoder.md` |
| Parent / child SRs, site siblings (90d), asset siblings (90d), recurring-failure flag | `sr-graph-resolver.md` |
| Asset-data lineage gaps with owners | `asset-data-lineage.md` |
| `recently-installed-asset` flag, dispatch packet completeness | `pre-dispatch-checks.md` |
| `qualitySignals[]` with `family / code / severity / confidence / evidence` | `quality-signals.md` |
| `priority` (P1 / P2 / P3), `ageHours`, `eta`, `slaBreached`, `slaBreachesAt`, latest note + author | SR record itself |
| `tradeDetection.source` (`los | fallback | hybrid`) and confidence | Pre-dispatch Check 5 |

If any of these are missing, surface the gap explicitly — do not silently classify. A classifier output without decoded inputs is an opinion, not a verdict.

## The four canonical buckets

| Bucket | Definition |
|---|---|
| `dispatch` | The SR is unassigned (or assignment was withdrawn) and ready for SP routing. |
| `follow-up` | The SR has an assigned SP or live workflow step but is missing an ETA, schedule commitment, quote response, or recent SP note. A dispatcher nudge is the right next action. |
| `escalation` | The SR has breached SLA, breached an ETA grace window, has a high-severity quality signal, has a recurring-failure flag with SLA risk, or carries an escalation tag. A leader or customer comms decision is needed before another routine SP action. |
| `close` | The SR has a verifiable completion path and no unresolved repair-review or invoice-risk signal. |

The classifier returns exactly one bucket per SR. It also returns `nextActionSource` (which rule fired or `llm`) and a one-sentence `justification`.

## Cadence thresholds (starter set)

These mirror the plumbing-queue-monitor starter values. Treat them as the default for any trade until that trade calibrates its own. Tune per trade in the trade skill or per account in `MAGIC/memory/accounts/<slug>.md`.

```yaml
cadence:
  p1: { etaGraceHours: 2 }     # P1 ETA grace before escalation
  p2: { etaGraceHours: 8 }     # P2 ETA grace before escalation
  p3: { etaGraceHours: 24 }    # P3 ETA grace before escalation

escalation:
  maxOpenAgeHours: 120         # 5 days; aged opens auto-escalate unless customer-held
  triggerTags: [customer-complaint, exec-escalation, safety]

recurrence:
  lookbackDays: 90             # see sr-graph-resolver.md
  semanticSimilarity: medium   # "toilet backing up" ~ "restroom drain clogged again"

followUp:
  quotePendingHoursByPriority: { p1: 4,  p2: 24, p3: 72 }
  lastNoteStaleHoursByPriority: { p1: 6, p2: 24, p3: 72 }

close:
  completionNotePatterns:
    - 'work complete'
    - 'job done'
    - 'completed on site'
    - 'closed out'

llm:
  maxCallsPerRun: 25           # cap to control cost; default to follow-up beyond cap
```

These thresholds are educated starting points. Log every change in the iteration log at the bottom of this file.

## Rule order (first match wins)

Evaluate in order. The first rule that matches wins; do not keep evaluating.

### 1. recurrence-escalation

All required:

- `recurrence.recurringFailureFlag == true` (from sr-graph-resolver)
- AND one of: priority `P1` or `P2`, OR `slaBreached == true`, OR an entry in `escalation.triggerTags` is on the SR

Output: `nextAction = "escalation"`, justification cites the recurring asset cluster.

### 2. quality-escalation

Any one triggers:

- `slaBreached == true`
- `eta` is in the past by more than the priority-specific grace window
- Any `escalation.triggerTags` value on the SR
- `ageHours > escalation.maxOpenAgeHours` AND `status != "Awaiting Customer"`
- Any `qualitySignals` entry with `severity == high` AND `confidence in [medium, high]`
- `recently-installed-asset` flag is set with `< 30` days since install AND a failure (post-implementation case)

Output: `nextAction = "escalation"`, justification cites the first matching trigger.

### 3. quality-follow-up

Any one triggers:

- Any `qualitySignals` entry with `severity == medium` AND `confidence in [medium, high]`
- Any `qualitySignals` entry with code `JOB_COMPLETE_UNVERIFIED`, `LIVE_STATUS_MISMATCH`, `TEMP_FIX_ONLY`, `NO_SUPPORTING_QUOTE`, `CUSTOMER_SYMPTOM_NOT_ADDRESSED`, or `MISSING_DISPATCH_CONTEXT` AND no high-severity escalation trigger
- A `predispatch-gap` signal is present and the SR is already assigned (collect missing context before another SP action)

Output: `nextAction = "follow-up"`, justification cites the signal code + short evidence.

### 4. close

Any one triggers (re-admits the SR if upstream filters dropped it):

- `status in ["Resolved", "Completed", "Work Completed"]` AND the SR is still present in the open queue on our side
- Latest note matches one of `close.completionNotePatterns` AND no outstanding invoice action remains on us

Block `close` when any unresolved `qualitySignals` entry has `family in [repair-review, invoice-risk]` AND `confidence in [medium, high]`. Route through `quality-follow-up` or `quality-escalation` instead.

Output: `nextAction = "close"`, justification cites the matched trigger.

### 5. dispatch

All required:

- `status in ["New", "Open"]`
- `sp` is null or `sp.id` empty
- No active quote (`quote` absent or `quote.status in ["None", "Rejected", "Expired"]`)
- `tradeDetection.confidence != low` OR priority is `P1` OR a high-impact term is in the SR text (`no water`, `flood`, `overflow`, `restroom closed`, `safety`)

Output: `nextAction = "dispatch"`, justification cites the unassigned SR with no active quote.

### 6. follow-up

Any one triggers:

- `sp` is set AND `eta == null` AND `status != "Awaiting Customer"`
- `eta` is in the past but inside the priority grace window (rule 2 did not fire)
- Active quote pending SP response longer than `followUp.quotePendingHoursByPriority`
- Last SP note older than `followUp.lastNoteStaleHoursByPriority`

Output: `nextAction = "follow-up"`, justification cites which stale field + hours.

### 7. LLM fallback (unmatched)

If no rule above matches, hand the SR to the LLM classifier with: priority, status, ageHours, SP name, ETA, last 3 notes (truncated), recurrence evidence, and the full `qualitySignals` array. The LLM must return one of `dispatch | follow-up | escalation | close` plus a one-sentence reason. Reject any other output and default to `follow-up` for human review.

LLM cap: `llm.maxCallsPerRun` (starter 25) per run. Beyond the cap, default unmatched SRs to `follow-up` with justification `"LLM cap reached; defaulting to follow-up for human review."`

## Run diff

After classification, compare the current run against the most recent prior run:

| `runDiffStatus` | Meaning |
|---|---|
| `new` | SR did not exist in the previous run. |
| `moved-bucket` | SR existed but `nextAction` changed. Capture `previousNextAction`. |
| `unchanged` | SR existed and `nextAction` stayed the same. |
| `cleared` | SR existed in the previous run but no longer appears in the current open queue. |

Surface aggregate counts (`newCount`, `movedBucketCount`, `clearedCount`) at the top of any cohort or queue output. Run diff is the discipline that lets us track "what changed since the last sweep" rather than re-litigating every SR.

## Override capture

When a dispatcher or reviewer overrides a classifier verdict (the agent said `escalation`, the actual call was `follow-up`), capture it. The shape:

```json
{
  "runId": "<YYYY-MM-DD-HHmm>",
  "capturedAt": "<ISO-8601>",
  "overrides": [
    {
      "srId": "<SR number>",
      "skillSaid": "escalation",
      "actualWas": "follow-up",
      "reason": "SP called with confirmed ETA after run generated."
    }
  ]
}
```

Where it lives:

- For productionized agent skills (Maria's plumbing-queue-monitor), in `runs/<timestamp>/overrides.json`.
- For ad-hoc cohort reviews, append a row to `lessons-from-runs.md` and (if a pattern repeats) promote a refinement into the rule order above or into `quality-signals.md`.

Do not silently swallow an override. Every override is a signal about either a missing rule, a miscalibrated threshold, or a missing input. Treat it as a learning loop entry.

## Output format

The classifier's per-SR output:

```
SR <number> classification:
- nextAction: <dispatch | follow-up | escalation | close>
- nextActionSource: <rule:<name> | llm>
- justification: <one sentence>
- runDiffStatus: <new | moved-bucket | unchanged | cleared>
- previousNextAction: <bucket | null>
```

The classifier's run-level output:

```
Run summary:
- SRs classified: <n>
- By bucket: dispatch <n>, follow-up <n>, escalation <n>, close <n>
- Run diff: new <n>, moved-bucket <n>, cleared <n>
- LLM calls: used <n> of cap <n>; cache hits <n>
- Calibration gaps: <list of any threshold or input that ran on default>
```

## What this mode does NOT do

- It does not produce trade-specific diagnostic depth. That is the trade skill's job.
- It does not select an SP. SP selection is downstream of `dispatch`.
- It does not write outbound communication. Escalation and customer comms drafting belong to downstream agents (Epic B B6 / B8).
- It does not mutate SRs. The classifier is read-only.

## Future native primitive (FacilitiesOS)

Mode C is a prosthetic. The native build is tracked in `MAGIC/memory/actions.md` as part of the FacilitiesOS AI primitives backlog. Native primitive should:

- Maintain `nextAction` as a derived property on the SR record, refreshed on every state change.
- Expose the bucket in dispatch UI and account-pod canvases.
- Power the close-blocker as a workflow gate rather than per-query agent logic.
- Power run-diff and override capture from event history rather than per-run reconstruction.

Until that lands, the classifier runs in the agent layer.

## Iteration log

| Version | Date | Change | Owner |
|---|---|---|---|
| 0.1 | 2026-05-01 | Founding version, promoted from `plumbing-queue-monitor/rules.md` (Maria) and generalized for cross-trade use. | Jim McCarthy |

When a trade or account tunes a threshold, log the change here with the trade or account, the threshold, the old and new values, and a one-sentence reason.
