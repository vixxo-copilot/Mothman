# sr-triage-pre-dispatch

A **living triage layer** that sits between Vixxo Service Request data (Siebel / VixxoLink / Gateway) and any trade skill. Every trade — plumbing, HVAC-R, cold-and-frozen beverage, ice machines, electrical, etc. — inherits this layer. The skill is intentionally written to evolve as we learn from new runs.

**Owner:** Jim McCarthy
**Status:** Production, shadow-mode for Mode A
**Founded:** 2026-04-30
**Last material update:** 2026-05-10

---

## What problem does it solve?

Three real builds in April–May 2026 — a 200+ SR plumbing batch, an 11-SR cold-beverage cohort, and Maria Clavijo-Demchalk's plumbing-queue-monitor for Epic B / AIA-397 — surfaced patterns that no single trade skill should re-learn:

- Agents read SRs in isolation and miss parent / child / sibling SRs that already carry the missing follow-up.
- Agents mistranslate Siebel sub-statuses (`Known ETA`, `Invoice Required for SR`, `Delinquent SC Invoice`).
- Agents attribute SLX → Siebel asset-migration gaps to Tech Dispatch when the gap actually lives in customer-furnished data, the asset master, or install-side write-back.
- Agents miss prior-failure history on the same asset before recommending another routine truck roll.
- Cohort reviewers describe the same quality problems in different words across runs, so cohort artifacts cannot aggregate.
- Different runs of the same skill on the same SR can produce different-depth packets when the resolver fallback is treated as advice instead of a hard call sequence.

This skill bakes those rules in once. Trade skills consume the decoded SR record this layer produces; they don't re-derive the graph, re-translate the sub-status, or re-route the data-lineage gap.

---

## Three operating modes

State the mode explicitly at the top of any output.

### Mode A — Pre-dispatch
Run **before** an SR is routed to a Service Provider. Produces a **dispatch intelligence packet** (eight fields) — not a dispatch recommendation. The packet separates prep before the truck rolls, actions onsite, and evidence we want captured for the asset / location graph so the next SR is smarter. Runs in **shadow mode** while the schema stabilizes; the dispatch decision still belongs to the human dispatcher.

### Mode B — Post-facto
Run during SR-quality review (closed, mid-flight, or cohort sweep). Applies the same decoders to score quality. Catches mistranslated sub-statuses, missed parent / child siblings, mis-attributed asset gaps, recurring-failure clusters, and post-implementation cases.

### Mode C — Next-action classifier
Run when sweeping an open queue. Consumes the decoded record from Mode A or Mode B and returns one of four canonical buckets — `dispatch / follow-up / escalation / close` — per SR, plus a `runDiffStatus` (`new / moved-bucket / unchanged / cleared`) compared with the previous run. Mode C is read-only; it never mutates SRs and it never invents its own decoders.

Modes A and B produce *findings*. Mode C produces a *bucket* a dispatcher (or downstream agent) can act on.

---

## File layout — what lives where and why

```
sr-triage-pre-dispatch/
├── SKILL.md                    Top-level activation. Three modes, behavioral constraints, run discipline.
├── README.md                   This file. Orientation for new readers.
└── reference/
    ├── sub-status-decoder.md   Always read. Siebel sub-status → plain English + agent guidance.
    ├── sr-graph-resolver.md    Always read. Pull parent / child / sibling SRs; FWKD overlap; cancelled-SR triage.
    ├── asset-data-lineage.md   Always read. Route "missing asset data" gaps to the right of four owners.
    ├── quality-signals.md      Always read. Stable codes for repair-review / predispatch-gap / invoice-risk.
    ├── pre-dispatch-checks.md  Mode A. Twelve checks; eight-field dispatch intelligence packet schema.
    ├── post-facto-application.md  Mode B. Seven checks; closure-quality scoring rubric.
    ├── next-action-classifier.md  Mode C. Ordered rule set, cadence thresholds, LLM fallback, run-diff, override capture.
    └── lessons-from-runs.md    Always read. Empirical foundation. New patterns land here first.
```

### File-by-file purpose

#### `SKILL.md` — top-level activation
Defines the three modes, the behavioral constraints that apply in every mode, the run discipline (run diff and override capture) for cohort and queue runs, and the inheritance pattern trade skills follow. This is the entry point. Trade skills read `SKILL.md` first, run the appropriate mode, and only then read their own trade reference files.

#### `reference/sub-status-decoder.md` — always
Translates Vixxo Siebel `Substatus` values into plain-English meaning and operational guidance. Built from the 259-SR plumbing batch; counts on each row reflect what was observed. Includes:
- Real sub-status dictionary with typical `Job Complete` pairing, plain-English meaning, and agent-guidance line per value.
- Cancelled-SR sub-types (Pattern A — billing-only clone of a completed sibling; Pattern B — genuine cancellation with logged work).
- Vixxo's existing `Substatus Grouping` health tiers (`New / Friendly / Potentially Unfriendly / Unfriendly / Good`).
- Composition rules with `Job Complete` flag and `Breached Description` field.

**Trigger that drove this build.** Riverbank 0784 / SR SR-EXAMPLE-001: agent translated `Known ETA` as "closed to bill prematurely." Carrie Kroeker (Ulta) flagged the mistranslation on 2026-04-30.

#### `reference/sr-graph-resolver.md` — always
Specifies how to pull and use the SR neighborhood (parent, children, site siblings, asset siblings, same-trade siblings). Many quality verdicts depend on this graph; the agent reads SRs in isolation by default, which is the wrong default. Includes seven rules covering:
- Never claim "no replacement quote in flight" without checking children first.
- Recurring failure on the same asset is its own classification.
- Repeat callbacks on the same site are an SP scorecard signal.
- Sibling SRs on the same site / trade need a symptom-drift check.
- Cloned-WO references must be checked for Vixxo-run-ness before pulling resolution notes.
- Empty `vixxolink_get_related_service_requests` triggers the search fallback; FWKD overlap is the sibling signal inside the fallback.
- Cancelled-SR cluster handling: suppress billing-only clones, count cancelled-with-real-work as paired siblings.

**Trigger that drove this build.** Lincoln NE 0535 / SR SR-EXAMPLE-002: agent reported "no replacement quote in flight" while child SR SR-EXAMPLE-003 was already open with the replacement scope.

#### `reference/asset-data-lineage.md` — always
When the agent flags "missing asset data," route the gap to one of four owners instead of attributing every gap to Tech Dispatch:
1. Customer-furnished data (stores, installer)
2. Asset master record / Siebel (data migration / asset master governance / install-side write-back)
3. Dispatch packet build (Tech Dispatch)
4. SP-side awareness (SP / SPM coaching)

Names the live persistent gaps (Ulta SLX → Siebel migration; Refuel install-side write-back) and how to honor them.

**Trigger that drove this build.** Riverbank 0784: agent called "no heater make/model/serial in the dispatch packet" a Tech Dispatch process failure. It was the SLX → Siebel migration gap.

#### `reference/quality-signals.md` — always
Stable codes the agent attaches to an SR after decoding so cohort runs aggregate, downstream consumers filter, and pattern repetition is trackable across trades. Three families:
- `repair-review` — `JOB_COMPLETE_UNVERIFIED`, `LIVE_STATUS_MISMATCH`, `SYSTEM_RECORD_LAG`, `TEMP_FIX_ONLY`, `SHOULD_HAVE_PROJECT_SCOPE`, `CUSTOMER_SYMPTOM_NOT_ADDRESSED`.
- `predispatch-gap` — `MISSING_DISPATCH_CONTEXT`, `MISSING_FWKD_WO_NUMBER`, `SENTINEL_SITE_INTAKE_BOT_LATENCY`, `CLONE_PARENT_NOT_VIXXO_RUN`, `SITE_BUILDING_SYSTEMS_UNKNOWN`, `WRONG_TRADE_ROUTING`, `INTAKE_TAXONOMY_MISMATCH`, `SP_TYPE_MISMATCH`.
- `invoice-risk` — `DUPLICATE_BILLING_RISK`, `NO_SUPPORTING_QUOTE`, `INVOICE_BEFORE_FIX_VERIFIED`, `TRIP_CHARGE_AFTER_CANCEL`, `RESTORATION_NOT_LINE_ITEMED`.

Every signal carries `family / code / severity / confidence / evidence`. A medium- or high-confidence `repair-review` or `invoice-risk` signal **blocks the `close` bucket** — Mode C must route through `follow-up` or `escalation` instead.

**Origin.** Promoted from Maria Clavijo-Demchalk's plumbing-queue-monitor `quality-patterns.md` so every trade inherits the same vocabulary.

#### `reference/pre-dispatch-checks.md` — Mode A only
The twelve-check sequence and the eight-field dispatch intelligence packet schema. Run order matters; checks gate one another:
1. SR graph resolution (with mandatory empty-`related` fallback to `vixxolink_search_service_requests`).
2. Recently-installed-asset trigger (< 30 days from install = post-implementation flag).
3. Dispatch packet completeness, with lineage owner assignment.
4. Customer call recommendation (the new primitive).
5. Trade skill routing.
6. FWKD work-order-number completeness (open SR with empty FWKD blocks dispatch).
7. Sentinel-site fallback resolution (`site.number = 99999` and the On Demand Site Creation BOT cadence).
8. Sewer-vs-septic differentiation on recurring drain SRs.
9. Resolution-note pull and synthesis on recurring-asset clusters (with stop-condition emit-gate — no packet without resolution-note synthesis or an explicit null-fallback record).
10. Facility Lead identification discipline (read FL from SR header, not notes).
11. Diagnosis-vs-symptom provenance and confidence discipline (quote SP literal words first; promote to inferred diagnosis only with named signal and explicit confidence).
12. Asset-id resolution fallback (customer tag → `vixxolink_list_assets` pivot when `vixxolink_get_asset` returns errorCode 6001).

The eight-field packet — recommended decision, hard evidence, prep required, onsite actions, customer / provider asks, asset-memory updates, owner, confidence — separates *prep before the truck rolls* from *actions onsite during the visit* from *evidence captured for the asset / location graph*.

#### `reference/post-facto-application.md` — Mode B only
Seven-check sequence applied during SR-quality review, mid-flight or post-close. Same decoders as Mode A but used to score, not to route. Composes with the trade skill for trade-depth scoring (trade-fit, repair-vs-replace discipline, root-cause capture, install-defect flag, OEM-warranty leverage). Output composes into cohort-review work and writes durable findings into `MAGIC/memory/actions.md`, `MAGIC/memory/accounts/<slug>.md`, and `docs/artifacts/sr-quality-review/`.

#### `reference/next-action-classifier.md` — Mode C only
The deterministic rule set with LLM fallback. Specifies:
- Inputs the classifier expects (the decoded record produced by Mode A or B).
- The four canonical buckets (`dispatch / follow-up / escalation / close`).
- Cadence thresholds (P1 / P2 / P3 ETA grace, max-open-age escalation, recurrence lookback, follow-up note staleness, completion-note patterns).
- Rule order (first match wins): recurrence-escalation → quality-escalation → quality-follow-up → close → dispatch → follow-up → LLM fallback (capped per run).
- Run-diff discipline (`new / moved-bucket / unchanged / cleared`).
- Override-capture discipline (`runs/<timestamp>/overrides.json` for productionized agents; `lessons-from-runs.md` for ad-hoc cohorts).
- Per-SR and run-level output shapes.

Maria Clavijo-Demchalk's plumbing-queue-monitor (Epic B / AIA-397) is the first production implementation. Other trades inherit the scaffolding with their own quality signals and account-tuned thresholds.

#### `reference/lessons-from-runs.md` — always
The empirical foundation. Six runs are documented as of 2026-05-10:
- **Run A** — Plumbing batch (April 2026): 259 SRs across Ulta / Luxottica / DriveTime / Boyd / Circle K / Lenscrafters. Founding evidence for the SR-graph resolver, sub-status decoder, asset-data lineage, and the recurring-failure pre-dispatch trigger.
- **Run B** — Cold-and-frozen-beverage cohort (April 2026): 11 SRs across Circle K and Refuel. Founding evidence for the trade-skill routing check, documentation quality scoring, recently-installed-asset trigger, and warranty-data treatment.
- **Run C** — Circle K plumbing pre-dispatch (2026-05-01): 6 SRs, first per-SR Mode A run. Derek Neighbors and Maria Clavijo-Demchalk reads promoted the dispatch-intelligence-packet schema and the shadow-mode operating posture.
- **Run D** — Circle K all-trades pre-dispatch with Amy Chasse's team review (2026-05-04): 12 SRs reviewed by FLs Brandon Covington and Jai. Drove five rule changes: FL identification discipline (Check 10), FWKD sibling detection (Rule 6), 180-day same-asset lookback (Check 1 / Check 9 update), cancelled-SR cluster handling with billing-clone suppression (Rule 7 + sub-status Cancelled row), diagnosis-vs-symptom provenance (Check 11).
- **Run E** — Boyd plumbing pre-dispatch with Carrie Kroeker's customer-success review (2026-05-05): 7 SRs at Gerber Collision. First account expansion beyond Circle K. Surfaced TL placeholder dwell-time policy signal (`TL_PLACEHOLDER_DWELL_BREACH` candidate) and confirmed two-layer feedback loop shape (technical / per-SR from operations + cross-cutting / process-improvement from customer success).
- **Run F** — Five-run consistency test on Circle K SR SR-EXAMPLE-004 (2026-05-10): identical inputs produced 4x packet-depth differences depending on whether the search fallback actually ran. Drove four rule changes: Check 1 mandatory-fallback sub-step, Check 9 stop-condition emit-gate, Check 12 asset-id resolution fallback, Rule 6 promoted from advice to imperative.

New patterns land in `lessons-from-runs.md` first. They get promoted to a new check, decoder rule, or quality-signal code only after the pattern repeats or is severe enough to warrant a one-shot rule.

---

## How trade skills call this layer

Trade skills (`trades-plumbing`, `trades-cold-frozen-beverage`, `trades-ice-machines`, `trades-hvac-r`, etc.) inherit this layer. They do **not** re-publish its logic.

Pattern in trade skills:

```
Before responding:
1. If pre-dispatch: read sr-triage-pre-dispatch SKILL.md and run Mode A.
   Use its output as the input to your trade diagnostic.
2. If post-facto: read sr-triage-pre-dispatch SKILL.md and run Mode B.
   Apply its decoders before any closure-quality scoring you produce.
3. If sweeping an open queue: read sr-triage-pre-dispatch SKILL.md and
   run Mode C after Modes A/B have decoded the records. Emit the
   four-bucket classification with run diff.
4. Then read the shared trade base and your own trade reference files.
```

The triage layer produces the pre-dispatch packet, the decoded SR record, or the bucketed queue. The trade skill produces the technical diagnostic and recommendation on top.

---

## Behavioral constraints (every mode, every trade)

These constraints live in `SKILL.md` and apply to every caller:

- Never declare "no follow-up" without first running the SR-graph resolver.
- Never emit a Mode A packet on an SR whose `vixxolink_get_related_service_requests` returned empty without first running the `vixxolink_search_service_requests` fallback. An empty `related` result is "fallback required," not "graph resolved."
- Never declare "closed to bill prematurely" or any other closure-quality verdict without first running the sub-status decoder.
- Never declare "Tech Dispatch sent an empty packet" without first running the asset-data lineage check.
- Never recommend a routine truck roll on an SR the prior-failure trigger flags as recurring. Recommend a customer call first.
- When the dispatch packet is incomplete, name the gap owner (Tech Dispatch / data migration / asset master / customer-furnished data) instead of a generic "missing data" flag.
- Never emit a Mode C `close` verdict while a medium- or high-confidence `repair-review` or `invoice-risk` signal is unresolved. Route through `follow-up` or `escalation` instead.
- Never silently drop a dispatcher override of a Mode C verdict. Capture every override (`skillSaid` / `actualWas` / `reason`) and feed it back into the rules or the lessons file.

---

## Run discipline — cohort and queue runs

When this skill runs across a cohort (Mode B at scale) or a queue (Mode C):

- **Run diff.** Compare the current run against the most recent prior run. Surface aggregate counts of `new`, `moved-bucket`, `unchanged`, and `cleared` SRs at the top of the output. Per-SR `runDiffStatus` lets reviewers focus on what changed since the last sweep instead of re-litigating every SR.
- **Override capture.** When a dispatcher or reviewer overrides a verdict, record the override with the SR id, what the skill said, what the actual call was, and the reason. Productionized skills persist overrides to `runs/<timestamp>/overrides.json`. Ad-hoc cohort reviews append a row to `reference/lessons-from-runs.md` and, if the pattern repeats, promote a refinement into a decoder rule, a quality-signal code, or a Mode C threshold.

Both disciplines are described in detail in `reference/next-action-classifier.md`; they apply equally to Mode B cohort artifacts.

---

## What this skill does NOT do

- It does not produce trade-specific diagnostic depth. That is the trade skill's job.
- It does not replace the universal trade base (`_shared/reference/vixxo-trade-operating-base.md`). It sits in front of it.
- It does not own the FacilitiesOS native primitive build. The platform-side build is tracked separately in `MAGIC/memory/actions.md`. This skill is the agent-side prosthetic until the native build lands.

---

## Living document

This skill is expected to grow. New patterns from trade-cohort reviews land in `reference/lessons-from-runs.md`; new sub-statuses observed in the wild land in `reference/sub-status-decoder.md`; new pre-dispatch checks land in `reference/pre-dispatch-checks.md`. Update the references first, then update `SKILL.md` only if the mode logic itself changes.

---

## Founding evidence

- `docs/artifacts/sr-quality-review/customer-issue-brief.md` — plumbing batch findings (Run A)
- `docs/artifacts/sr-quality-review/carrie-ulta-response-synthesis-2026-04-30.md` — Carrie Kroeker's reply that drove the parent / child resolver, sub-status decoder, and asset-data lineage decoders
- `docs/artifacts/cold-beverage-cohort-retrospective-2026-04-29.md` — cold beverage cohort lessons (Run B)
- `docs/artifacts/sr-agent-runs-technical-review-derek-2026-04-30.md` — Derek Neighbors brief, primitive frame
- Maria Clavijo-Demchalk's plumbing-queue-monitor skill (Epic B / AIA-397) — promoted the quality-signal vocabulary and the next-action classifier rule scaffold into this triage layer on 2026-05-01
- `docs/artifacts/sr-triage-runs/circle-k-plumbing-2026-05-01.md` — Run C; Derek + Maria reads promoted the dispatch-intelligence-packet schema and the shadow-mode operating posture
- `docs/artifacts/sr-triage-runs/circle-k-all-trades-2026-05-04.md` — Run D; Amy Chasse's team review drove five rule changes
- `docs/artifacts/sr-triage-runs/boyd-plumbing-2026-05-03.md` — Run E; Carrie Kroeker's customer-success review confirmed the two-layer feedback-loop pattern
- `docs/artifacts/sr-triage-runs/Run-1-SR-EXAMPLE-004.md` through `Run-5-SR-SR-EXAMPLE-004.md` — Run F; five-run consistency test that promoted resolver fallback from advice to imperative
