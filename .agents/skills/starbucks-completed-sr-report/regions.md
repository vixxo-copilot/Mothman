# Starbucks region assignment

Operational regions for this report come from the **National Accounts Espresso B&G Tech** naming pattern on the assigned service provider.

## Primary rule — B&G Tech suffix

When `serviceProvider.name` matches:

```text
National Accounts Espresso B&G Tech <number> - <Region>
```

use **`<Region>`** as the report region label (trim whitespace).

Observed region labels include:

| Region label | Typical scope |
|---|---|
| Dallas | Texas / south-central |
| Kansas City | Central |
| Midwest | Midwest |
| Miami | Southeast / Florida |
| NYC | New York metro / northeast |
| N. California | Northern California |
| Toronto | Ontario / Canada B&G |

New labels appear over time. **Do not normalize** unless the user asks — use the suffix exactly as returned.

## Fallback — non-B&G providers

When the SP name does not match the B&G Tech pattern, bucket under:

```text
Other SP
```

Keep `site.state` / province in the detail table so the reader can still see geography.

## Canada

For `811C` and `811F-C`, B&G Tech regions (e.g. `Toronto`) take precedence over province. Non-B&G Canadian SPs still land in `Other SP` with province shown.

## Do not use

- `tierName` as a search filter (upstream error)
- `site.state` alone as the region header when a B&G Tech suffix is present
