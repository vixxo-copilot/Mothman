# Config schema

JSON only. Do not invent dollar amounts. Copy this skeleton, then fill from the SPM / SP conversation.

```json
{
  "sp_number": "KS00000",
  "sp_name": "Legal or trade name",
  "origin": {
    "address": "street, city, ST ZIP"
  },
  "local": {
    "max_miles": 50,
    "band_low_miles": 30,
    "travel": 75
  },
  "extended": {
    "anchor_city": "Outlier City, ST",
    "trip_minimum": 350,
    "labor_rate": 75,
    "labor_hours_in_minimum": 1,
    "round_to": 5,
    "hold_anchor_exact": true
  },
  "aliases": {
    "Misspelling": "Canonical City, ST"
  },
  "cities": [
    { "name": "City, ST", "parent_cbsa": "Parent CBSA Name" }
  ],
  "sr_export": "C:/path/to/SR Export.xlsx"
}
```

`sr_export` is optional. Omit it for a city-only card.

## Required before run

| Field | Meaning |
| --- | --- |
| `origin.address` | SP shop / home-base used as mile zero |
| `local.max_miles` | Standard coverage radius. Miles at or below this are Local |
| `local.travel` | Flat travel the team wants inside the standard area |
| `extended.anchor_city` | Named outlier they already priced (or want to price) |
| `extended` travel **or** min+labor | See formula below |
| `cities` | At least the CBSA parents and child cities in scope |

## Local vs extended

- **Local (standard area):** `miles <= local.max_miles` → `local.travel`
- **`band_low_miles`:** label only (Under X vs X-max). Does not change the dollar
- **Extended (outliers):** `miles > local.max_miles` → scaled from the anchor

## Extended formula (must be data-driven)

Preferred when the SP quotes a **trip minimum that includes labor**:

```
anchor_travel = trip_minimum - (labor_rate × labor_hours_in_minimum)
```

Or set `extended.travel` directly if they already named the travel dollars.

Then for each extended city/site:

```
suggested = round(anchor_travel × (one_way_miles / anchor_city_miles), round_to)
```

If `hold_anchor_exact` is true (default), the anchor city and sites in that city keep `anchor_travel` even when site miles differ slightly.

`labor_rate` is also added as **suggested trip min = travel + labor_rate** so the card can be compared to the quoted minimum.

## Cities

- `name` should include state (`Macon, GA`)
- `parent_cbsa` groups child cities under the CBSA header from coverage tools
- `aliases` collapse spelling variants (Warner Robbins → Warner Robins) so they are not priced twice

## SR export

Expected headers on the first sheet: `Customer #`, `Site #`, `Site Name`, `Address`, `City`, `State`, `Zip`. Unique sites are geocoded at street level (Census), with city-centroid fallback.
