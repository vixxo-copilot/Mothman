# SR graph resolver — parent, child, and sibling SRs

> **Purpose.** The agent reads SRs in isolation by default. Many quality verdicts (no replacement quote in flight, no callback scheduled, missing follow-up, recurring failure) require knowledge of related SRs on the same parent, the same site, or the same asset. This file specifies how to pull and use that graph before any verdict.
>
> **Triggering symptom that drove this build.** On Ulta SR SR-EXAMPLE-002 (Lincoln NE 0535, clogged toilet), the agent reported "no replacement quote in flight." The replacement quote existed on **child SR SR-EXAMPLE-003**. The agent never looked. Carrie Kroeker flagged this on 2026-04-30 as a tuning opportunity for the agent.

## What "the SR graph" means

For a given SR, the graph includes:

1. **Parent SR.** The SR this one was spawned from. Common when a child SR is opened for a quote, a return visit, a replacement scope, or a recall.
2. **Child SRs.** Any SR spawned from this SR. Common naming convention: `<parent SR>-DS` or a Siebel-generated child SR number tied to the parent.
3. **Sibling SRs on the same site.** Any SR opened on the same site number within the last 90 days, regardless of asset or trade.
4. **Sibling SRs on the same asset.** Any SR opened against the same asset record within the last 90 days, regardless of trade or symptom. This is the strongest recurring-failure signal.
5. **Sibling SRs on the same site and the same trade or short description.** A narrower view useful for callback analysis.

## How to pull the graph (today, with current MCP tools)

Until a native graph primitive exists, build it from the data layer:

1. **Parent / child via SR number conventions.** Plumbing batch evidence: child SRs use suffix patterns and explicit parent_sr fields when present. Pull the SR header via `vixxolink_get_sr` or `gateway_get_sr` and check for `parent_sr` / `originating_sr` / `child_sr_list` fields. Capture every linked SR number in the response.
2. **Sibling site SRs.** Query Gateway / VixxoLink for the site's SR list filtered by `createdDate >= today - 90` and `customer_number = <this SR's customer>`. Drop any SR with `Substatus Grouping = New` from the same hour to avoid race conditions.
3. **Sibling asset SRs.** Query for the asset's SR history. Pull `vixxolink_get_asset_history` if available; otherwise filter the site's SR list by asset id where present in the SR record. **Use a 180-day lookback** for same-asset siblings (per `pre-dispatch-checks.md` Check 1). Same-asset recurrence outside the 90-day site-window is the strongest signal in the graph, and routine 90-day caps miss the prior repair that would change the dispatch decision.
4. **FWKD overlap as a sibling signal when the related-SR endpoint is empty.** Pull `serviceRequest.workOrderNumber` (the FWKD) for this SR. Search the site's SR list for any other SR carrying the same `workOrderNumber`. **If two or more SRs at the same site share the same FWKD, treat them as siblings of one work event regardless of what `vixxolink_get_related_service_requests` returns.** This is the working substitute when the related-SR endpoint returns empty (which is the common case on Circle K HVAC and several other Circle K LOS today). Run D founding case: Lacy Lakeview TX SR `SR-EXAMPLE-016` (5/4) and `SR-EXAMPLE-017` (5/3) share `FWKD7498778`, same site, same asset, same description; `get_related_service_requests` returned empty on both; the FWKD overlap is the signal. Without this rule, the cluster count overstates by one.
5. **Cloned-WO detection in description text.** When the description carries an inline tag of the form `Clone of FWKD<num>` (or `clone of WO <num>`, or similar), do not treat the linked WO as a Vixxo parent SR by default. Run `vixxolink_search_service_requests` with the FWKD number to find the parent Vixxo SR. **If the search returns zero results, the cloned WO is customer-side or external; fire `CLONE_PARENT_NOT_VIXXO_RUN` and stop chasing.** This was Amy Chasse's correction on the 2026-05-03 Farmington case (FWKD7231659 was not Vixxo-run; the agent should not have asked the SPM to pull a Vixxo resolution note for it). When the search returns a parent SR, capture the parent SR number and pull `vixxolink_get_service_request_notes` to add the parent's RESOLUTION text to the dispatch packet.

If a tool call fails or returns empty, do not assume "no related SRs." Note the gap explicitly: "SR graph could not be resolved for this SR; verdicts dependent on the graph are deferred."

## How to use the graph (decision rules)

### Rule 1 — Never claim "no replacement quote in flight" without checking children first

If the agent is about to flag missing follow-up scope (replacement quote, return visit, recall, child task), it must first list the parent and child SRs. If a child exists with the relevant scope, the verdict changes from "missing follow-up" to "follow-up exists on child SR `<number>`; verify status."

### Rule 2 — Recurring failure on the same asset is its own classification

Two or more closed SRs on the same asset within 90 days = the new SR is no longer a routine first-time call. Mark the SR for:

- Pre-dispatch customer call (Mode A) before sending the SP, with a recommended scope change (camera-and-jet on a recurring drain, replacement-vs-repair on a recurring asset, install-defect investigation on a recently-installed asset).
- Callback analysis tagging (Mode B) for SP scorecard and customer reporting.

This is the Rockford 0370 pattern (4 plumbing SRs on the same tankless in months, all reactive, none escalating to replacement) and the Refuel 1328 pattern (3 fountain SRs in 6 days at one site, only visible because Stephanie connected them by hand).

### Rule 3 — Repeat callbacks on the same site (different asset) are an SP scorecard signal

If the same SP shows up on 2+ SRs at the same site within 30 days on different assets, that is not necessarily a quality flag — it can simply be the regional SP. But it is a signal worth surfacing in any SP-level review.

### Rule 4 — Sibling SRs on the same site and same trade need to be checked for symptom drift

If a fountain SR closes "complete" and a refrigeration SR opens 48h later at the same site, the closer-of-the-first SR may not have surfaced an upstream issue (electrical, water supply, condensate). Note for cross-trade root-cause review.

### Rule 5 — Cloned WO references must be checked for Vixxo-run-ness before pulling resolution notes

When an SR description carries a "Clone of FWKD<num>" or similar tag, the agent must determine whether the cloned WO is a Vixxo-run job before asking the SPM (or any downstream consumer) to pull a Vixxo resolution note. Procedure:

1. Run `vixxolink_search_service_requests` with the FWKD number.
2. If a parent Vixxo SR is found: capture the parent SR number, pull `vixxolink_get_service_request_notes`, extract the `RESOLUTION` note, and add it to the dispatch packet (per `pre-dispatch-checks.md` Check 9).
3. If no parent SR is found: fire `CLONE_PARENT_NOT_VIXXO_RUN`, do not surface a "pull the resolution note" prep ask, and add a note to the SPM that the cloned WO is customer-side or external. The packet's recommendation should be based on what we know from the SR text, the asset master, and the site graph, not on a non-existent Vixxo note.

This rule is a direct outgrowth of Amy Chasse's 2026-05-03 review of SR `SR-EXAMPLE-033` (Farmington ME), where the agent's packet asked the SPM to chase FWKD7231659's resolution note even though FWKD7231659 was not Vixxo-run. Wasted SPM time on a note that does not exist in our system.

### Rule 6 — Empty `related` triggers the search fallback; FWKD overlap is the sibling signal inside the fallback

When `vixxolink_get_related_service_requests` returns empty (`resultTotal == 0`), the SR graph is NOT resolved. The agent MUST fall back to `vixxolink_search_service_requests` with at minimum `{customerNumber, siteId, lineOfService, summary: true, pageSize: 50, sortField: createdDate, sortDirection: Descending}` (extend with `assetTag` or `asset_id` when known) to reconstruct site / asset / LOS siblings. Empty `related` is the trigger to run the fallback, not a terminal state. The fallback is the call sequence; narrating it in prose without running it does not satisfy the rule, including in DIAGNOSTICS / test-mode runs. See `pre-dispatch-checks.md` Check 1 mandatory-fallback sub-step for the gate that prevents Mode A emission without this call.

On Circle K the fallback fires on nearly every SR (the related-SR endpoint is sparsely populated against this customer's Siebel records); on other customers it fires whenever the Siebel-side relation is sparse.

Inside the reconstructed graph, FWKD overlap is the sibling signal. When the SR has the same `workOrderNumber` (FWKD) as one or more other SRs at the same site, those SRs are siblings of a single work event. Treat them as one cluster member, not as separate independent SRs.

Procedure:

1. Run the search fallback above whenever `vixxolink_get_related_service_requests` returns `resultTotal == 0`.
2. From the SR details payload, capture `serviceRequest.workOrderNumber`.
3. Across the site-sibling and asset-sibling lists assembled by the search fallback (and steps 2 and 3 of "How to pull the graph"), check whether any other SR carries the same FWKD.
4. If yes, group those SRs as a single cluster member. Use the most recent open SR as the cluster representative; preserve all sibling SR numbers in the resolver output.
5. Adjust the cluster count accordingly. Two SRs sharing FWKD7498778 at the same site, same asset, same description count as one work event in the cluster, not two.
6. When the FWKD-shared SRs include both an open ticket and a recently-closed ticket with `cancelled` sub-status, see Rule 7 below for the cancelled-SR triage.

The FWKD-overlap framing is a direct outgrowth of the Run D Lacy Lakeview TX HVAC case (2026-05-04 review with Brandon Covington and Jai); the skill's "five SRs in 90 days" overstated by one because two of those SRs were the same work event under FWKD7498778. The imperative search-fallback framing is a direct outgrowth of the 2026-05-10 five-run consistency test on Circle K SR SR-EXAMPLE-004: three of five identical-input runs treated empty `related` as terminal, skipped the search, and emitted softer packets that missed the prior SR SR-EXAMPLE-032 RESOLUTION evidence. Both fixes live in this rule, not in manual reviewer correction.

### Rule 7 — Cancelled-SR cluster handling: suppress billing-only clones, count cancelled-with-real-work as paired siblings

Cancelled SRs are not all alike. The cluster construction needs to distinguish two patterns:

**Pattern A — Billing-only clone of a completed SR.** An SR created with description text matching `Clone of FWKD<num>`, `DO NOT DISPATCH`, or similar, and / or a Tracking Hold note containing the phrase `Created for billing purposes only, do not dispatch`. These SRs were never dispatched, never carried independent labor, and exist as a Siebel-side billing structure tied to the original completed SR. **Suppress these from the cluster count.** Including them double-counts a single repair.

**Pattern B — Cancelled SR where work was actually dispatched and executed.** An SR that was dispatched, carried logged time-events, has resolution notes, and was later cancelled (commonly because the work was completed and billed under a sibling SR's FWKD or because a customer-side decision changed the disposition). **Count these as a paired sibling** of the SR that carries the actual work record. Group them under a single cluster member by FWKD overlap (Rule 6) when the FWKD is shared, or as a paired event by site / asset / day proximity when the FWKD differs.

Procedure to distinguish A from B:

1. Pull the cancelled SR's details and notes via `vixxolink_get_service_request_details` and `vixxolink_get_service_request_notes`.
2. Look for Pattern A indicators in three places:
   - Description text containing `Clone of FWKD`, `DO NOT DISPATCH`, or `for billing purposes only`.
   - Tracking Hold note (`type: TrackingHold`) containing `Created for billing purposes only` or `do not dispatch`.
   - Time-events list empty (no tech check-in or check-out events ever logged).
3. If two or more of these indicators are present, classify as Pattern A and suppress from the cluster.
4. Otherwise, classify as Pattern B and count as a paired sibling.

Founding case: Lincoln ME SR `SR-EXAMPLE-019` (cancelled 2026-02-24). Description: "Clone of FWKD6982897 - DO NOT DISPATCH". Tracking Hold note (BCOVINGTON 2026-02-24 19:38): "Created for billing purposes only, do not dispatch." No time-events ever logged. Three indicators present, classify as Pattern A, suppress from the cluster. The actual repair lives on the original SR `SR-EXAMPLE-020` with FWKD7065127, AR Successful.

Operationally, Pattern A is a customer-billing workaround that should be addressed at the customer-success layer (the customer is using SR cancellations to capture customer-internal-tech work into our billing flow, which breaks the data trail). The skill's job here is the cluster construction. The customer-success conversation is a separate routing.

## Output format from the resolver

When the trade skill or another agent calls this resolver, return:

```
SR graph for <SR number>:
- Parent SR: <number or "none">
- Child SRs: <list or "none">
- Site sibling SRs (90d): <count, list with SR number + opened date + status>
- Asset sibling SRs (90d): <count, list>
- Same-trade sibling SRs (30d, same site): <count, list>

Recurring-failure flag: <yes/no, with the asset-cluster trigger if yes>
Site-cluster flag: <yes/no, count + window>
Resolver completeness: <complete | partial — fields not resolved listed>
```

The trade skill or quality-review agent uses this output to compose its verdict. It does NOT re-derive the graph.

## When the graph cannot be fully resolved

Common causes:

- **Asset id missing on the SR record.** Cannot pull asset siblings. Note "asset-id-missing" in resolver completeness.
- **Cross-system migration gap (SLX to Siebel at Ulta is the live example).** Asset record exists but is sparse. Use what is there; flag the gap to the asset-data lineage check.
- **Tool failure or rate limit.** Note explicitly. Do not let a failed call become an implicit "no related SRs."

## What this resolver does NOT do

- It does not score callback risk. That is the post-facto Mode B job, in `post-facto-application.md`.
- It does not produce trade diagnostic depth. That is the trade skill's job.
- It does not recommend a customer call. That is the pre-dispatch checks job, in `pre-dispatch-checks.md`.

It produces a clean, structured view of the SR's neighborhood. Other components consume that view.

## Future native primitive (FacilitiesOS)

This resolver is a prosthetic. The native build is tracked in `MAGIC/memory/actions.md` as part of the FacilitiesOS AI primitives backlog. Native primitive should:

- Maintain the graph as a first-class object (not derived per query).
- Update the graph on every SR create, update, or close event.
- Surface the graph in the dispatch UI and in any SR review surface.
- Power callback metrics without per-query reconstruction.

Until that lands, this resolver runs in the agent layer.

**Last updated:** 2026-05-05 — added Rule 6 (FWKD overlap as sibling signal when related-SR endpoint is empty) and Rule 7 (cancelled-SR cluster handling: suppress billing-only clones, count cancelled-with-real-work as paired siblings); extended same-asset lookback to 180 days (step 3 of How to pull the graph). All three changes driven by Amy Chasse's team review of the 2026-05-04 Circle K all-trades run, ratified after VixxoLink verification. Prior version 2026-05-03 (cloned-WO detection step 4 and Rule 5, driven by Amy Chasse's review of the 2026-05-03 Circle K all-trades run, Farmington ME SR `SR-EXAMPLE-033` referencing external FWKD7231659). Founding version 2026-04-30 (Lincoln 0535 / SR SR-EXAMPLE-002 miss).
