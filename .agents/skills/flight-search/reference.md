# Flight Search — CLI Fallback Reference

Use the `fli` CLI when the MCP tools aren't loaded in the session. It hits the
same Google Flights data.

## Install / paths

See [setup.md](setup.md) for full install steps. Resolve your local paths with:

```bash
which fli          # CLI, e.g. ~/.local/bin/fli
which fli-mcp      # MCP stdio server (registered in mcp.json as `fli`)
```

The venv Python used by the JSON helper below lives alongside the install,
typically `~/.local/pipx/venvs/flights/bin/python` for a pipx install. Any
`python3` with a standard library works too.

## Common CLI commands

Replace `<ORIG>`, `<DEST>`, `<CODE>` (airline IATA), and dates as needed.

```bash
# One-way, preferred airline, non-stop, sorted by departure
fli flights <ORIG> <DEST> 2026-06-16 --airlines <CODE> --stops NON_STOP --sort DEPARTURE_TIME

# Round-trip with filters
fli flights <ORIG> <DEST> 2026-06-15 --return 2026-06-16 --stops ONE_STOP --max-layover 120

# Cheapest dates in a range
fli dates <ORIG> <DEST> --from 2026-06-01 --to 2026-06-30

# Multi-city
fli multi --leg SEA,HKG,2026-12-26 --leg PEK,SEA,2027-01-02
```

Key flags: `--airlines <CODE>`, `--exclude-airlines`, `--stops NON_STOP|ONE_STOP`,
`--max-layover 120`, `--min-layover`, `--time 17-21`, `--class BUSINESS`,
`--sort CHEAPEST|DURATION|DEPARTURE_TIME|ARRIVAL_TIME`, `--return`,
`--format json`.

## JSON parsing helper

The pretty CLI output is hard to scan and gets truncated. Use `--format json`
piped to Python to sort/filter and compute layovers. Example: list all
1-stop / sub-2h itineraries sorted by departure, flagging the preferred airline
(set `PREF`) and same-day arrivals.

```bash
PREF=AA   # preferred airline IATA code to flag
fli flights <ORIG> <DEST> 2026-06-17 --stops ONE_STOP --max-layover 120 --format json 2>/dev/null \
| PREF="$PREF" python3 -c '
import sys, os, json
from datetime import datetime
pref = os.environ.get("PREF", "")
data = json.load(sys.stdin)
flights = data if isinstance(data, list) else data.get("flights", data.get("results", []))
def t(x): return x[11:16]
rows = []
for f in flights:
    legs = f["legs"]
    if len(legs) != 2:        # one stop
        continue
    dep, arr = legs[0]["departure_time"], legs[1]["arrival_time"]
    lay = int((datetime.fromisoformat(legs[1]["departure_time"])
               - datetime.fromisoformat(legs[0]["arrival_time"])).total_seconds() // 60)
    hub = legs[0]["arrival_airport"]["code"]
    al = legs[0]["airline"]["code"]
    f1 = legs[0]["airline"]["code"] + legs[0]["flight_number"]
    f2 = legs[1]["airline"]["code"] + legs[1]["flight_number"]
    rows.append((dep, arr, hub, lay, f1, f2, f["price"], al))
rows.sort()
for dep, arr, hub, lay, f1, f2, price, al in rows:
    star = f" <-- {pref}" if pref and al == pref else ""
    sameday = "same-day" if dep[:10] == arr[:10] else "arrives " + arr[8:10] + "th"
    print(f"DEP {t(dep)} -> ARR {t(arr)} ({sameday}) | via {hub} ({lay}m) | {f1}, {f2} | ${price}{star}")
'
```

### JSON shape

`search_flights` JSON returns a list of itineraries. Each has: `duration`
(minutes), `stops`, `price`, `currency`, `layovers`, and `legs[]`. Each leg has
`departure_airport`/`arrival_airport` (`{code, name}`), `departure_time`/
`arrival_time` (ISO `YYYY-MM-DDTHH:MM:SS`), `duration`, `airline` (`{code,
name}`), `flight_number`, `aircraft`, `legroom`, `amenities`.

Non-stop itineraries have one leg (no layover); one-stop have two legs. Compute
layover as leg2 departure minus leg1 arrival. A next-day `arrival_time` date
versus `departure_time` date signals a red-eye / overnight itinerary.

## Notes

- ICT and similar small airports have no non-stops to the coasts; everything
  routes through DFW / ORD / DEN / PHX. Evening departures often can't reach a
  small destination the same night.
- `--format json` is marked experimental upstream; the schema may shift.
- This uses Google Flights' unofficial API — treat as a personal-use tool.
