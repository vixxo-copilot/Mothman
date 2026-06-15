# Asset-data lineage check

> **Purpose.** When the agent flags "missing asset data" on an SR, route the gap to the right owner instead of attributing every gap to Tech Dispatch. The agent must distinguish a Tech-Dispatch packet that was built incomplete from a Siebel asset record that was empty when the packet was built.
>
> **Triggering symptom that drove this build.** On Ulta SR SR-EXAMPLE-001 (Riverbank 0784, hot water), the agent reported "no heater make/model/serial in the dispatch packet" and called it a Tech Dispatch process failure. Carrie Kroeker confirmed it is the SLX → Siebel migration gap. Stores rarely surface data tags. Tech Dispatch shipped what Siebel had. Same pattern at Refuel 1328 (asset 2152683 installed 2026-04-17, master had `serialNumber: "N/A"` 12 days later).

## Lineage layers

There are four places asset data can fail to arrive:

1. **Customer-furnished data.** Asset tag, install date, model details that only the customer or the installer knows. Common gaps when stores cannot or will not surface tags during a service call. **Owner: customer / SP.**
2. **Asset master record (Siebel).** The data exists somewhere but never made it into the Siebel asset record. Common after a migration (SLX → Siebel at Ulta) or when SP-side install activity does not write back to the master. **Owner: data migration team / asset master governance / install-side write-back agent.**
3. **Dispatch packet build (Tech Dispatch).** Siebel had the data but the dispatch packet did not include it. **Owner: Tech Dispatch.**
4. **SP-side awareness.** Dispatch packet had the data but the SP did not consume it. **Owner: SP / SPM coaching.**

The agent must place every "missing asset data" finding into exactly one of these four layers.

## How to route a gap (decision rules)

For each missing field on the dispatch packet (asset make, model, serial, install date, warranty status, prior-call summary, site access, customer contact):

### Step 1 — Pull the asset record

Call `vixxolink_get_asset` with the asset id from the SR. Inspect each field individually.

### Step 2 — Compare asset record to dispatch packet

| Asset record state | Dispatch packet state | Lineage owner |
|---|---|---|
| Field populated | Field populated in dispatch packet | No gap |
| Field populated | Field empty in dispatch packet | Tech Dispatch (layer 3) |
| Field empty | Field empty in dispatch packet | Asset master (layer 2). If install was within last 60 days, also flag as install-side write-back gap. |
| Field shows known-bad value (e.g., `"Cornelieus"` misspelling, `"N/A"`, `"unknown"`) | Anything | Asset master (layer 2). Quality issue, not a missing-data issue. |
| Asset record itself missing or unreadable | Anything | Customer-furnished data + asset master (layers 1 + 2). Stores rarely surface tags; recommend in-store data capture as part of next visit. |

### Step 3 — Tag the gap with the owner and the recommended next step

Output format:

```
Asset-data gap on SR <number>, asset <asset id>:
- Field: <make / model / serial / install date / warranty / etc.>
- Asset record state: <populated | empty | bad-value: "<value>">
- Dispatch packet state: <populated | empty>
- Lineage owner: <customer-furnished | asset master | Tech Dispatch | SP awareness>
- Recommended next step: <specific action with named owner>
```

## Special handling for known migration gaps

Two named, persistent migration gaps are live as of 2026-04. Honor them.

### Ulta SLX → Siebel asset migration

Stores rarely surface data tags. Asset make, model, serial, install date, warranty are missing on a meaningful share of Ulta SRs. **Do not attribute these to Tech Dispatch.** Route to the migration backlog and to the in-store data-capture recommendation.

Reference: `MAGIC/memory/accounts/ulta-beauty.md` (section "Plumbing agent pilot — Carrie Kroeker reply (2026-04-30)").

### Refuel install-side write-back gap

Assets installed by SPs are not getting warranty data, nameplate detail, or serial numbers written back into the master. Refuel 1328 fountain (asset 2152683) is the standing example. **Treat as install-side write-back gap, not Tech Dispatch.** Pair with the asset master sweep-and-write-back agent referenced in `MAGIC/memory/actions.md` (cold beverage retro action #9).

## When an asset record is missing entirely

Some SRs have no resolvable asset id. Three subcases:

1. **Asset exists at the site but was not selected at SR open.** Surface for site/asset reconciliation. Do not penalize the SP for missing data they did not have.
2. **Site has no assets registered for this trade at all.** Surface for site/asset master onboarding. This is a Vixxo-side data hygiene gap, often tied to recent customer onboarding.
3. **Trade does not require an asset (e.g., a one-off plumbing call on a fixture not in the asset master).** No gap; do not flag.

## Composing with other checks

This check pairs with:

- **Sub-status decoder** — `Quote Required` plus an asset-data gap usually means scope cannot be quoted accurately until the gap is closed.
- **SR graph resolver** — sibling SRs on the same asset may have the data the current SR is missing. Pull from the prior SR if present.
- **Pre-dispatch checks** — recently-installed-asset check depends on `asset.installDate`; if that field is missing, the post-implementation flag cannot fire. Note explicitly when this happens.
- **Trade skills** — every trade requires asset awareness for repair-vs-replace logic. Trade skills consume the lineage output and decide whether to proceed, defer, or escalate.

## Future native primitive (FacilitiesOS)

The lineage check is a prosthetic. The native build is tracked in `MAGIC/memory/actions.md` as part of the FacilitiesOS AI primitives backlog. Native primitive should:

- Tag every asset field with its provenance (customer-furnished, install-write-back, manual entry, migration source, derived).
- Tag every dispatch packet with the lineage of every field at the moment the packet was built.
- Surface the lineage tag in the dispatch UI so Tech Dispatch can see at a glance whether a gap is theirs or upstream.
- Power the asset master sweep-and-write-back agent natively rather than via per-SR scraping.

Until that lands, this lineage check runs in the agent layer.

**Last updated:** 2026-04-30 (founding version, driven by Riverbank 0784 / SR SR-EXAMPLE-001 miss + Refuel 1328 install-write-back evidence)
