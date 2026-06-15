# Pre-dispatch checks (Mode A)

> **Purpose.** Run at the moment an SR is at assignment, before the SP gets the call. Surface what we know that should change the dispatch decision: prior failures on the same asset, recently-installed assets, dispatch packet completeness, trade-skill routing, customer call recommendation.
>
> **Cadence framing (from Derek brief).** This is the cadence we are after. The plumbing batch run was a one-time learning exercise; the operating cadence is per-SR triage at assignment, with intelligence applied before the truck rolls.

## When to run Mode A

Run Mode A when:

- An SR has been opened and assigned (or is about to be assigned) to an SP.
- An SR has been recalled, recategorized, or rerouted (treat each rerouting as a fresh dispatch decision).
- A child SR is about to be opened off a parent (run Mode A on the child before dispatch).

Do NOT run Mode A on:

- SRs that are already mid-execution, closed, or in invoice-side workflow. Use Mode B (post-facto).
- PM-cadence dispatches that are calendar-driven and not failure-driven. Run a lighter preventive-maintenance dispatch check instead (out of scope for this skill at this time).

## Check sequence

Run in this order. Stop and surface findings if any check returns a hard signal.

### Check 1 — SR graph resolution

Run the SR graph resolver (`reference/sr-graph-resolver.md`) for this SR. Capture parent, children, site siblings, asset siblings, same-trade siblings.

**Lookback window discipline.** Default lookback is 90 days for site-level siblings. Extend to **180 days for same-asset siblings** when any prior SR in the 90-day window resolves to the same asset id (or the same fixture identity when the asset id is missing). Same-asset recurrence is the strongest signal in the graph; the 90-day cap routinely misses the prior repair that would change the dispatch decision (Run D founding case: Freeport ME asset `ASSET-EXAMPLE-004`, prior SR `SR-EXAMPLE-018` from 2026-01-15 sat 109 days back, 19 days outside the default window, and carried the hard-water diagnosis that makes the next visit a category conversation rather than a routine repair).

**Mandatory fallback on empty related-SR result.** If `vixxolink_get_related_service_requests` returns `resultTotal == 0`, Check 1 is not complete. Run `vixxolink_search_service_requests` with at minimum `{customerNumber, siteId, lineOfService, summary: true, pageSize: 50, sortField: createdDate, sortDirection: Descending}` to reconstruct the site / asset / LOS graph. Empty `related` is the trigger for the fallback, not the end of the check. This applies to every customer; on Circle K the fallback fires in nearly 100% of cases per `sr-graph-resolver.md` Rule 6. Narrating the fallback in prose without running the call does not satisfy the check, including in DIAGNOSTICS / test-mode runs.

If the search fallback returns 2+ SRs in the 90-day site window or the 180-day same-asset window on the same site / LOS / asset, treat as the recurring-cluster hard signal and run Check 9 (resolution-note pull and synthesis) before emitting the packet.

**Hard signal:** Asset-sibling cluster of 2+ SRs (90-day site window or 180-day same-asset window) = recurring failure. Skip to Check 4 (customer call recommendation) before continuing routing.

### Check 2 — Recently-installed-asset trigger

Pull `asset.installDate` and compare to `SR.createdDate`.

| Delta | Classification | Action |
|---|---|---|
| < 30 days | Post-implementation case (likely) | Pre-dispatch flag for invoice-integrity audit. Surface install owner and install warranty status. Potentially on the SP, not the customer. |
| 30 – 90 days | Early-life failure (possible) | Note for callback analysis. Continue routing. |
| > 90 days | Normal-life failure | Continue routing. |
| Install date unknown | Cannot evaluate | Note dependency on asset-data lineage check. Continue routing with awareness. |

**Hard signal:** Post-implementation case = elevate the SR for chargeback consideration before normal routing.

### Check 3 — Dispatch packet completeness

For each field below, mark populated / empty:

- Asset make, model, serial number
- Asset install date
- Asset warranty status (parts, labor, install)
- Prior-call summary on this asset (last 3 SRs, last 90 days)
- Site access notes (gate codes, hours, special instructions)
- Customer contact (site contact + escalation contact)
- Customer NTE and any account-specific scope rules

For any empty field, run the asset-data lineage check (`reference/asset-data-lineage.md`) to assign the gap to the right owner. Do NOT default to "Tech Dispatch failure."

**Hard signal:** If make/model/serial AND install date AND warranty are all empty, the SP is being dispatched blind. Surface the gap and the lineage owner before the SP is contacted.

### Check 4 — Customer call recommendation (the new primitive)

Triggered by Check 1 (asset cluster) or by Check 3 (dispatch blind spot on a cost-sensitive call). The primitive: when prior failures or data gaps suggest the routine truck roll will fail, recommend a customer call BEFORE dispatch with a specific scope change.

Examples worth surfacing today:

- **Recurring drain (3+ snake calls in 90d at same site).** Recommend customer call. Recommended scope: camera-and-jet, with replacement quote prep if camera surfaces a structural issue.
- **Recurring tankless heater (3+ flame-sensor or descale calls on same asset).** Recommend customer call. Recommended scope: replacement-vs-repair conversation with warranty status. (This is the Rockford 0370 pattern.)
- **Recently-installed equipment failure (< 30 days from install).** Recommend customer call only if the SP being dispatched is different from the install SP, otherwise route directly to install owner. Recommended scope: install-defect investigation, chargeback path identified before dispatch.
- **Site cluster (3+ SRs in 30d at same site, different trades).** Recommend customer call. Recommended scope: ask the customer if there is an underlying issue (recent renovation, equipment changeover, water-quality issue) before sending another reactive truck.

When you recommend a customer call, output:

```
Pre-dispatch customer call recommended for SR <number>:
- Trigger: <which Check fired>
- Recommended scope change: <specific - what we should propose to the customer>
- Why: <prior-failure summary, asset history, or data-gap reasoning>
- Recommended caller: <CSM / SPM / ROM / PM>
- If customer agrees: <updated dispatch instructions>
- If customer declines: <fall back to original dispatch with the specific risks named>
```

### Check 5 — Trade skill routing

Confirm the LOS + Short Description + asset type routes to the right governing trade skill. The cold beverage cohort surfaced 9 of 11 SRs booked under "Cold Beverage Equipment" that needed a different governing skill.

Until the LOS → trade-skill mapping (cold beverage retro action #15) lands, perform this routing manually:

- Read LOS, Short Description, asset type.
- Compare against the trade skill list (`.cursor/skills/trades-*`).
- If the routing is ambiguous (e.g., a Manitowoc head on a Cornelius dispenser at a c-store), surface the ambiguity and recommend the combo-unit handling per cold beverage retro action #4.

### Check 6 — FWKD work-order-number completeness

Pull `serviceRequest.workOrderNumber` from the SR details payload. The customer-facing FWKD is the Nuvolo-completion + invoicing key.

- If `workOrderNumber` is empty on an open SR, fire `MISSING_FWKD_WO_NUMBER`. Surface as a billing-blocker pre-dispatch and route the backfill ask to the CSR who created the SR or to the dispatch desk. Do not let an FWKD-less SR roll a truck — the field work will complete but Nuvolo will not, and the SP cannot invoice.

**Hard signal:** Any open SR with empty `workOrderNumber`. Block dispatch until backfilled.

Per Amy Chasse 2026-05-03: "Without the FWKD work order number being on the WO, we will struggle with completing the work order in Nuvolo and we won't be able to invoice it." Founding case: Farmington ME drain SR `SR-EXAMPLE-033` (5/3 run).

### Check 7 — Sentinel-site fallback resolution

If `site.number = 99999` or another sentinel value, do not flag this as an intake routing failure by default. Instead:

1. Look at the SR notes for a dispatcher reference to the **On Demand Site Creation BOT** or to an IT ticket.
2. If the bot is referenced, fire `SENTINEL_SITE_INTAKE_BOT_LATENCY` and surface two asks: bot create-time latency (was the SOP 20-minute cadence missed) and IT-ticket cleanup workflow (re-point the SR off 99999 onto the real store after creation).
3. If no bot reference is present and the dispatcher has manually pointed at a real site number in the notes, treat as a true site-master / intake routing gap and route to the asset master / site mapping owner.

Founding case: Colorado Springs CO 2703296 SR `SR-EXAMPLE-034` (5/3 run, validated by Amy Chasse: bot took 35 minutes vs 20-min SOP against a 4-hour P0 SLA).

### Check 8 — Sewer-vs-septic differentiation on recurring drain SRs

On any drain SR — and on any SR carrying `SITE_BUILDING_SYSTEMS_UNKNOWN` for `wastewaterDisposal` — do a quick municipal-vs-septic determination before dispatching the SP:

1. Pull site address from the SR.
2. Identify the municipal authority (town / city / county / village water and sewer department).
3. Confirm whether the address is inside the municipal sewer service area.
4. Cross-check internal corroboration: presence of monthly grease-trap PMs is a strong municipal-sewer signal (FOG ordinances are municipal); absence plus rural location plus prior septic-pump-out SRs is a strong septic signal.
5. Default the dispatch packet:
   - **Municipal sewer:** scope is private-side building lateral (everything from the building to the curb / property line). Camera-and-jet target is the lateral. If a structural defect is found, replacement quote includes coordination with the municipal authority for any right-of-way work.
   - **Septic:** scope adds a tank-and-leach-field inspection. Recurring drain on septic almost always means the tank is full or the leach field is failing; recommend a septic pump-out on the same dispatch where reasonable, and a leach-field assessment if the tank-pump-out interval is less than 12 months.
   - **Unknown:** recommend the camera scope plus the building-systems lookup as a parallel ask to the asset master / site mapping owner, with the packet noting the dispatch was made without the lookup.
6. Capture the resolved value back into the site-master record (`wastewaterDisposal`) so the next drain SR at this site has the answer in hand.

Founding case: Farmington ME SR `SR-EXAMPLE-033` — site is on Town of Farmington municipal sewer (resolved by external research; corroborated by monthly Wind River grease-trap PM cadence). The dispatch was reframed from "drain snake on a possible septic" to "private-side building-lateral camera-and-jet on municipal sewer."

This check is especially important in rural Maine, upstate New York, parts of New England, and the rural South where municipal-sewer coverage ends abruptly at town boundaries and septic is the assumed default.

### Check 9 — Resolution-note pull and synthesis on recurring-asset clusters

Per Amy Chasse 2026-05-03: when Check 1 / SR-graph resolver returns 2+ closed SRs on the same asset within 90 days, the agent does not stop at "review prior resolution notes" as a homework line item for the SPM. The agent pulls those resolution notes, synthesizes them, and recommends the next-step scope inside the packet.

Procedure:

1. From the SR-graph resolver, list the prior closed SRs on the same asset (and same site, when the asset id is missing or the customer-furnished fixture id drifts across SRs).
2. Pull `vixxolink_get_service_request_notes` for each prior SR.
3. Extract the `RESOLUTION` note (and `VisitNote` if present) from each. Capture the SP, the date, the diagnosis, and what was repaired or replaced.
4. Synthesize the cluster into 2-4 lines naming: the recurring failure surface (which valve / line / coupler / fastener / sensor), the most-recent treatment (what the last visit did), and the residual root cause (what the cluster is telling us has not yet been fixed).
5. Convert that synthesis into the next-step scope. Examples:
   - 5 espresso SRs in 90d, three of which involved drain / brew valve / boiler / drip-tray fasteners, and one of which says "filter last changed in 2023" → next-step scope is a full Schaerer PM (boiler clean, filter change, brew-group inspection) on all three brewers, not "fix the leak."
   - 3 drain SRs in 90d at the same fixture, all snake-only → next-step scope is camera-and-jet, not another snake.
   - 4 tankless SRs on the same heater, all flame-sensor cleaning → next-step scope is replacement-vs-repair conversation with warranty status, not another sensor clean.
6. The packet's field 2 (Hard evidence) carries the resolution-note synthesis. The packet's field 3 (Prep required) carries the SP-side scope conversion (parts to bring, scope authority to grant). The packet's field 5 (Asks) carries the customer-side conversation (PM cadence, replacement-vs-repair). Owner of the synthesis is the agent, not the SPM.

When prior resolution notes contradict each other, surface the contradiction in field 2 and call the cluster ambiguous; do not over-fit a single root-cause hypothesis if the data does not support it.

Founding case: Thornville OH SR `SR-EXAMPLE-035` — five prior espresso SRs in 90d, four on `ASSET-EXAMPLE-006`, with resolution notes pointing at brew-valve corrosion, drain clog, missing drip-tray fasteners, and (most importantly) a 2023 water-filter date. Synthesis recommends a full Schaerer PM on all three brewers, not a "find the leak" visit.

When the same-asset cluster spans the 180-day window (per Check 1), pull and synthesize resolution notes across the full extended window, not just the 90-day default. Resolution notes that name a structural cause (hard water, voltage instability, water pressure, refrigerant leak, install defect) at any prior visit on the same asset are first-class evidence and belong in field 2 of the packet.

**Stop-condition (emit-gate).** The Mode A packet cannot be emitted until one of the following is true:

- (a) `vixxolink_get_service_request_notes` has been pulled for each prior SR surfaced by Check 1 (default the most recent 1-3 within the lookback window), and the synthesis is in field 2 of the packet, or
- (b) the Check 1 search fallback has returned `resultTotal == 0` and that null result is recorded explicitly in field 2 as "no prior SRs within 90/180-day window after fallback search."

A "deferred to a deeper run" note, a "verdicts dependent on the cluster size are deferred" note, or any equivalent placeholder is not an acceptable substitute. Diagnostic / test-mode runs do not waive this gate; the packet is the deliverable, and the gate enforces packet integrity regardless of run label.

### Check 10 — Facility Lead identification discipline

Read the FL from the SR header field, not from notes, sadmin traffic, or email cc lines.

Procedure:

1. From `vixxolink_get_service_request_details`, read `teamLeadFirstName` and `teamLeadLastName`. These two fields are the authoritative source for the FL on this SR.
2. Populate the Owner field of the packet (field 7) with the first / last name from the SR header.
3. **Do not** infer the FL from note authors, Teams chat references, sadmin email recipients, or sadmin email cc lines. The notes commonly reference backup contacts, escalation paths, or coverage-team participants who are not the FL of record.
4. **Do not** treat an in-SR `Team Lead` value embedded inside a ranked-coverage record as authoritative. Some teams have used that field as a routing workaround; it can be manipulated and is not reliable.
5. If `teamLeadFirstName` / `teamLeadLastName` are empty on the SR header, output `pending FL territory lookup` in the Owner field rather than guess. Surface the gap as a backfill ask to the requestor or to the dispatch desk.

Founding case: Lacy Lakeview TX SR `SR-EXAMPLE-016` — the SR header carries `teamLeadFirstName: Jainasia, teamLeadLastName: Vanholten`. The notes name Brandon Covington four times because Jainasia could not be reached and Brandon was being asked to cover. The skill incorrectly named Brandon as the FL in field 7. The correct read is Jainasia Vanholten as primary FL, with Brandon noted only in field 5 (provider asks) as the actual escalation contact when the primary FL was unreachable.

This check feeds the diagnostic for whether the FL the skill names is the FL who actually owns the SR. It does not produce a separate output; it gates the population of the Owner field in the eight-field packet.

### Check 11 — Diagnosis vs symptom provenance and confidence discipline

State the SP's literal words first. Promote symptom-level statements to inferred diagnosis only with the explicit signal that supports the inference and explicit confidence.

Procedure:

1. From the SR notes (most often via `vixxolink_get_service_request_notes` with `type: Note` or `type: VisitNote`), pull the SP's actual words. Capture verbatim.
2. In field 2 (Hard evidence) of the packet, lead with the SP's literal statement before any inferred diagnosis. Quote it directly when the words matter (volume thresholds, named components, named symptom families).
3. When the agent infers a diagnosis the SP did not state, name the **signal** the inference is built on (refrigerant volume, recurrence pattern, install defect chain, sub-status sequence, time-on-asset) and the **confidence** (high / medium / low) explicitly. The trade skill (e.g., `trades-hvac-r`, `trades-cold-frozen-beverage`, `trades-plumbing`) is the authority for what counts as a signal in its trade.
4. Do not collapse the SP statement and the inference into a single declarative line. The structure is "SP states X; by [trade] standard practice, [signal] indicates Y; probable diagnosis Y, confidence H." That structure preserves provenance, which preserves operator trust.
5. When the trade skill names a compliance dimension (EPA 608 on refrigerant work, OSHA on confined spaces, manufacturer warranty on parts), flag it explicitly as a constraint on the SP's proposed scope. Approving a non-compliant scope at face value is a near-certain callback and a separate audit exposure.

Founding case: Lacy Lakeview TX SR `SR-EXAMPLE-017` — Falcon 5's literal note: "Tech diagnosed the issue and found out that they needed to add 40-60 pound of freon for 3 units. Freon - $95/pound, Labor - $250 / unit = $750. Customer Total w/Tax: $7,378.86." Skill packet collapsed this to "Falcon 5 diagnosed refrigerant short across three units" and "system-level refrigerant leak now identified." Falcon 5 did not say "leak." The right framing carries the SP's literal volume call, names the HVAC standard practice signal (refrigerant of that volume across three units is leak signal regardless of SP wording, per `trades-hvac-r/reference/operations.md`), names the EPA 608 compliance constraint on recharge-without-leak-search, and assigns confidence high based on the volume threshold. The skill's substantive read was right; the language overreached.

This check feeds field 2 (Hard evidence), field 3 (Prep required for any scope conversion call to the SP), and field 8 (Confidence). It is a cross-cutting discipline, not a separate output.

### Check 12 — Asset-id resolution fallback

Customer-furnished asset tags do not always equal Vixxo asset ids. When `vixxolink_get_asset` returns errorCode 6001 "Input validation failed" on a customer-furnished tag, do not stop and call the asset master "unresolvable." Pivot to `vixxolink_list_assets`.

Procedure:

1. From the SR header, capture the customer-furnished asset tag (commonly the value placed in `assetTag` on the SR description or details payload).
2. Call `vixxolink_list_assets` with `{filters: {siteId, assetTag, pageSize: 25}}` to resolve the Vixxo asset id from the customer tag.
3. With the resolved Vixxo asset id, re-call `vixxolink_get_asset_warranties` (and `vixxolink_get_asset` if the structured asset payload is needed for nameplate / install date / model / serial).
4. If `vixxolink_list_assets` returns no match for the customer tag at the site, treat as a true asset-master gap and route the lineage to customer-furnished data / asset master per `asset-data-lineage.md`.
5. Capture the customer-tag-to-Vixxo-id resolution as an asset-memory write-back in field 6 of the packet so the next SR at this site does not retry blind.

Founding case: SR SR-EXAMPLE-004 Run 1 (Augusta ME 4707037, Schaerer SCA1). Customer tag `ASSET-EXAMPLE-005` returned 6001 from `vixxolink_get_asset`; `vixxolink_list_assets` resolved it to Vixxo asset id `2146696`, which then carried the warranty-record check (and surfaced a `null` install date as a separate lineage gap). Without the pivot the run would have stopped at "asset master unresolvable" and missed both the warranty read and the lineage write-back.

This check feeds field 2 (Hard evidence) when a warranty / install-date answer falls out of the resolved asset, field 6 (Asset-memory updates) for the tag-to-id write-back, and `asset-data-lineage.md` for the gap routing when the tag truly does not resolve.

## Mode A output — dispatch intelligence packet

> **Framing (from Derek read on the 2026-05-01 Circle K plumbing run).** Mode A output is not a dispatch recommendation. It is a **dispatch intelligence packet**. Each truck roll is both execution and learning: the SP fixes the issue *and* improves the asset/location graph so the next SR is smarter. The schema below enforces that framing by separating prep, onsite actions, and evidence we want captured, and by making asset-memory write-backs an explicit field rather than a footnote.

Per-SR output. Eight fields, in this order. Do not collapse fields into prose; downstream consumers (FSR, SPM, AIA-397 Mode C, future FacilitiesOS native primitive) read the schema.

```
Dispatch intelligence packet — SR <number>

1. Recommended decision: <dispatch as-is | dispatch with packet supplement | hold for customer call | hold for data resolution | reroute>
2. Hard evidence: <which checks fired, with the specific SRs / dates / asset records that drove the call. One bullet per signal. No editorializing.>
3. Prep required (before SP rolls): <packet supplements, KB articles, prior-SR resolution notes, scope-change instructions to SP, customer pre-calls. One bullet per item.>
4. Onsite actions (during the visit): <specific tools / scope at the site — camera-and-jet vs cable, sensor kit families to bring, photograph nameplate, confirm same fixture, jurisdictional check before scoping. One bullet per item.>
5. Customer / provider asks: <calls to make and to whom — CSM to customer, SPM to SP, ROM to FSR — with the specific question or scope change. One bullet per ask.>
6. Asset-memory updates (data to write back): <what gets captured and where it goes — serial / model / install date / warranty / fixture-level identity ("Men's Room Toilet 2 — Sloan Optima ETF-880") / nameplate photo / vehicle subrogation evidence. One bullet per write-back, with the lineage owner.>
7. Owner: <caller name + role for each ask in field 5; primary recommended owner if the packet results in a hold.>
8. Confidence: <high | medium | low, with the one-line reason. Confidence drops on missing install date, missing asset master, ambiguous LOS routing, or sparse parent/child linkage.>
```

The trade skill consumes this packet and produces the technical diagnostic. The packet itself does not produce the diagnostic.

### Field discipline

- **Field 1 is one decision.** Not a menu. If two decisions are plausible, the recommended decision is the more conservative one (hold > dispatch with supplement > dispatch as-is) and the alternative is named in field 2.
- **Field 2 is evidence, not narrative.** Each bullet cites a specific SR id, date, asset id, sub-status, or lineage gap. No "appears to be," no "looks like."
- **Field 3 vs Field 4 vs Field 6 are orthogonal.** Prep happens before the truck rolls; onsite happens during the visit; asset-memory updates are the artifact the visit produces for next time. Do not duplicate items across fields.
- **Field 6 names lineage owner per write-back.** Use the four lineage layers from `asset-data-lineage.md` (customer-furnished, asset master / Siebel, dispatch packet / Tech Dispatch, SP awareness).
- **Field 8 is calibrated, not a default.** Rely on the override-capture loop in `runs/<timestamp>/overrides.json` (or `lessons-from-runs.md` for ad-hoc cohort runs) to recalibrate. If the SR has no install date, no asset master record, and no parent/child linkage, confidence cannot be high.

### Operating posture — shadow mode

While the schema stabilizes, Mode A output runs **in shadow mode**: the packet is produced and reviewed, but the dispatch decision in Siebel/Tech Dispatch is still owned by the human dispatcher. Promote Mode A to a live recommendation surface only after override-capture data shows the schema is stable across runs (drive override rate down, drive moved-bucket rate to single digits).

Shadow-mode output should still be saved per run under `docs/artifacts/sr-triage-runs/<account>-<trade>-<YYYY-MM-DD>.md` so the override and run-diff disciplines have a record.

## What this check does NOT do

- It does not produce trade-specific scope or quotes. That is the trade skill's job.
- It does not enforce SLA timing — that is Tech Dispatch governance, not the agent's call.
- It does not select the SP. SP selection is a separate downstream step driven by SP scorecard, geography, and capacity.

## Future native primitive (FacilitiesOS)

The pre-dispatch checks are a prosthetic. The native build is tracked in `MAGIC/memory/actions.md` as part of the FacilitiesOS AI primitives backlog. Native primitive should:

- Run pre-dispatch checks as part of every SR-create workflow, not as an opt-in agent call.
- Surface the customer-call recommendation in the dispatch UI for the CSM / SPM to action.
- Route the dispatch decision (proceed, hold, change scope) into the workflow rather than into a standalone agent output.
- Power the prior-failure trigger from the maintained SR graph (not from per-query reconstruction).

Until that lands, these checks run in the agent layer.

**Last updated:** 2026-05-10 — Check 1 gains a mandatory-fallback sub-step (empty `vixxolink_get_related_service_requests` triggers `vixxolink_search_service_requests` before Check 1 can complete), Check 9 gains a stop-condition emit-gate (no Mode A packet without resolution-note synthesis or an explicit null-fallback record), Check 12 added (customer-tag → `vixxolink_list_assets` pivot when `vixxolink_get_asset` returns errorCode 6001). Driven by the 2026-05-10 five-run consistency test on Circle K SR SR-EXAMPLE-004 (Run-1 through Run-5 in `docs/artifacts/sr-triage-runs/`). Prior version 2026-05-05 — added Check 10 (Facility Lead identification discipline) and Check 11 (diagnosis vs symptom provenance and confidence discipline); extended Check 1 default lookback with a 180-day window for same-asset siblings; extended Check 9 to pull resolution notes across the full 180-day window when the cluster spans it. All three changes are direct outputs of Amy Chasse's team review of the 2026-05-04 Circle K all-trades run, ratified by Jim McCarthy after VixxoLink verification. Prior version 2026-05-03 (Checks 6, 7, 8, 9 from Amy's review of the 2026-05-03 Circle K all-trades run). Founding version 2026-04-30 (driven by Rockford 0370 recurring-tankless evidence and the cold beverage cohort's recurring-failure pattern).
