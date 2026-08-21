# Examples

## KS69082 — Gray, GA shop; Savannah as the priced outlier

Config: [examples/ks69082-gray.json](examples/ks69082-gray.json)

Inputs the team provided:

- Origin: `443 GA Highway 22 E, Gray, GA 31032`
- Standard area: 30-50 miles local, **$75** travel
- Outlier: Savannah trip minimum **$350** includes 1 hour labor at **$75** → travel **$275**
- Cities: CBSA tree (Warner Robins children, Albany/Leesburg, Savannah/Pooler, etc.)
- Optional: SR export for site-level miles

Command:

```bash
python .agents/skills/sp-travel-rate-card/scripts/build_travel_rate_card.py --config .agents/skills/sp-travel-rate-card/examples/ks69082-gray.json
```

Result pattern:

- Macon / Milledgeville / Warner Robins group → Local $75
- Albany / Leesburg / Pooler / Hinesville / Brunswick → Extended, scaled from Savannah $275
- Savannah city and Savannah sites held at $275
