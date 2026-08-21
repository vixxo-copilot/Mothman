---
name: sp-travel-rate-card
description: >-
  Builds a Vixxo-branded suggested travel rate card for any service provider
  from a shop origin address, a standard (local) mile band and dollar amount,
  and a priced extended/outlier market. Geocodes cities and optional SR-export
  sites, measures one-way driving miles, and scales extended travel from the
  outlier the team provides. Use when configuring SP travel, local vs extended
  truck-roll pricing, CBSA/city distance from a shop, trip-minimum minus labor
  as travel, or "what should we pay for travel to this city."
---

# SP Travel Rate Card

Reusable SPM skill. Turns **this SP's shop**, **their standard area**, and
**what they want for a named outlier** into a suggested flat-travel workbook
for every city (and optional site) in scope.

Do **not** invent local or extended dollars. If those are missing, ask.

## When to use

- "Build a travel rate card for SP #…"
- Local vs extended / outlier travel from a shop address
- CBSA or city tree + "Savannah min is $350 including 1 hour labor"
- Distance from origin to coverage cities, with suggested travel

Do **not** use for coverage rank loads (`vixxo-*-cbsa-coverage-builder`) or
dispatch ranking (`workfind`).

## Stop until config is complete

Collect, then write JSON (see [reference/config.md](reference/config.md)):

1. **SP # and name**
2. **Origin address** (shop / home base)
3. **Standard area:** `local.max_miles` and `local.travel`
4. **Outlier:** `extended.anchor_city` plus either `extended.travel` **or**
   `trip_minimum` + `labor_rate` (+ hours included in the min)
5. **Cities** from the CBSA/coverage breakdown (parents + children). Apply
   spelling aliases (e.g. Warner Robbins → Warner Robins)
6. Optional **SR export** path for site-level miles

## Pricing rules

- Local: `miles <= local.max_miles` → `local.travel`
- Extended travel dollars come **only** from provided data:
  - `anchor_travel = trip_minimum - (labor_rate × labor_hours_in_minimum)`, or
  - explicit `extended.travel`
- Extended city/site: `round(anchor_travel × miles / anchor_city_miles, round_to)`
- Time-based travel (column next to flat): `round-trip drive hours × labor_rate`
- Anchor city (and sites in that city when `hold_anchor_exact`) keep `anchor_travel`
- Distances are **one-way driving miles** (Census/Nominatim geocode + OSRM)
- Output is a **suggested** card, not an approved rate file

Worked example: [examples.md](examples.md)

## Workflow

1. Confirm the six inputs above. Do not run with guessed rates.
2. Write config JSON under `.tmp/sp-travel-rate-card/` or reuse
   [examples/ks69082-gray.json](examples/ks69082-gray.json) as a template.
3. Run:

```bash
python .agents/skills/sp-travel-rate-card/scripts/build_travel_rate_card.py --config path/to/config.json
```

Optional `--out` for a custom xlsx path. Default is
`~/Downloads/{SP#}_Travel_Rate_Card_{date}.xlsx`.

Self-check the formula with:

```bash
python .agents/skills/sp-travel-rate-card/scripts/build_travel_rate_card.py --self-test
```

4. Workbook sheets: **Assumptions**, **Cities**, **Sites**, **Extended analysis**
   (plus a copy-ready city travel card). Start from
   `assets/branded-documents/Excel Template.xlsx`.
5. Report origin, local rule, how anchor travel was derived, city count, site
   count, and output path.

## Geocoding

- Street origin/sites: U.S. Census geocoder, Nominatim fallback
- City centroids: Nominatim
- Routes: OSRM driving
- Cache: `.tmp/sp-travel-rate-card/geocode-cache.json`

Needs network. Dependency: `openpyxl`.
