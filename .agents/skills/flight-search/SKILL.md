---
name: flight-search
description: >-
  Search flights with the fli (Google Flights) MCP, applying the user's saved
  travel preferences (home airport, preferred airline, non-stop, red-eye
  tolerance, layover, cabin, bags, passengers). Runs a short first-run interview
  to capture those preferences, then reuses them. Use when the user asks to
  find, book, compare, or price flights or airfare, mentions a trip / route /
  travel dates, says things like "find me a flight", "fly from X to Y",
  "cheapest dates to fly", "update my flight preferences", or references the fli
  flight tool.
---

# Flight Search

Drive the `fli` MCP (Google Flights) and apply the user's saved travel
preferences by default. Surface the best matching option first, and clearly flag
any time a preference can't be met.

Requires the `fli` MCP for flight search. If its tools aren't available when you
reach the search workflow, see the [setup guide](setup.md) before searching.
Step 0 (the preferences interview) is conversational and does not require MCP.

## Step 0: Load preferences (do this first, every run)

1. Read the per-user config at `~/.config/flight-search/preferences.json`.
2. **If it is missing, unreadable, or its `version` is older than the current
   schema** → run the [first-run interview](#first-run-interview), then write the
   file before continuing.
3. **If the user says "update my flight preferences"** (or similar) → re-run the
   interview and overwrite the file.
4. Otherwise, load it and use it as the defaults for every search below.

### Config schema

`~/.config/flight-search/preferences.json`:

```json
{
  "version": 1,
  "home_airport": "PHX",
  "preferred_airlines": ["AA"],
  "preferred_alliance": "ONEWORLD",
  "nonstop_preference": "prefer",
  "redeye": "avoid",
  "max_layover_minutes": 120,
  "layover_negotiable": true,
  "cabin_class": "ECONOMY",
  "checked_bags": 0,
  "carry_on": true,
  "passengers": 1
}
```

Field values:

- `nonstop_preference`: `require` | `prefer` | `no_preference`
- `redeye`: `avoid` | `ok`
- `preferred_alliance`: `ONEWORLD` | `SKYTEAM` | `STAR_ALLIANCE` | `null`
- `cabin_class`: `ECONOMY` | `PREMIUM_ECONOMY` | `BUSINESS` | `FIRST`
- Any field may be omitted/`null` to mean "no preference".

### First-run interview

Capture the fields below in one short pass, then write `preferences.json` (set
`version: 1`). For fields with a fixed set of options, present the choices with
the `AskQuestion` tool when it's available (e.g. in Cursor); otherwise list the
choices conversationally and ask the user to pick. Ask the free-form ones (home
airport, preferred airline) directly and resolve them to IATA codes — use the
`find_airports` tool when available, otherwise your airport/airline knowledge —
confirming with the user when a city has several airports or a code is ambiguous.

1. **Home airport** — their default origin (free-form; resolve to IATA via
   `find_airports` or your airport knowledge, confirm if a city has several
   airports).
2. **Preferred airline(s)** — free-form; map to IATA codes (e.g. American → AA).
   Allow "no preference".
3. **Preferred alliance** — ONEWORLD / SKYTEAM / STAR_ALLIANCE / no preference.
4. **Non-stop preference** — require non-stop / prefer non-stop / no preference.
5. **Red-eye tolerance** — avoid red-eyes / red-eyes OK.
6. **Max preferred layover** — e.g. 90 / 120 / 180 minutes / no limit; also ask
   if it's negotiable (sets `layover_negotiable`).
7. **Cabin class** — economy / premium economy / business / first.
8. **Bags** — checked bag count (0/1/2) and whether to include a carry-on.
9. **Default passengers** — number of adults.

A **red-eye** = an overnight flight (departs roughly 9pm-5am and arrives the
next morning) OR any itinerary with an overnight layover.

## Tools

`fli` MCP tools:

- **`find_airports`** — resolve a city/airport name to IATA code(s) (param:
  `query`). Part of the fli MCP (v0.9.0+). Use it to confirm codes, especially
  for multi-airport metros; if a given install doesn't expose it, fall back to
  your own airport knowledge and confirm with the user.
- **`search_flights`** — one-way or round-trip on specific dates. Key params:
  `origin`, `destination`, `departure_date`, `return_date`, `airlines`,
  `alliance` (`ONEWORLD` / `SKYTEAM` / `STAR_ALLIANCE`), `max_stops`
  (`NON_STOP` / `ONE_STOP`), `max_layover` (minutes),
  `departure_window` (`"HH-HH"`), `cabin_class`, `sort_by`
  (`CHEAPEST` / `DURATION` / `DEPARTURE_TIME` / `ARRIVAL_TIME`), `passengers`,
  `checked_bags`, `carry_on`, `show_all_results: true` to get the full list.
- **`search_dates`** — cheapest dates across a range when travel is flexible.

If the MCP tools aren't loaded, fall back to the CLI — see [reference.md](reference.md).

## Search workflow

1. **Resolve airports.** Default the origin to the config `home_airport` when the
   user doesn't specify one. Convert any city names to IATA codes via
   `find_airports` (or your airport knowledge if it's unavailable); confirm with
   the user when a metro has several airports.
2. **Pin down dates and times.**
   - **Round trips** — when the user wants a return, resolve `return_date` as
     `YYYY-MM-DD` (infer from context or ask; same relative/fuzzy rules as
     departure). Omit `return_date` for one-way searches.
   - **Flexible dates** (user has not chosen specific days, or asks for
     "cheapest dates", "best time to fly", etc.) → call `search_dates` with
     `origin`, `destination`, and a date range (infer from context or ask).
     Present the cheapest options; if the user picks dates (or one is clearly
     best), continue below with those `YYYY-MM-DD` values via `search_flights`.
   - **Fixed dates** → compute exact `YYYY-MM-DD` from relative terms ("next
     Monday", "Tuesday night"). Map fuzzy time words to a `departure_window`:
     morning `6-11`, afternoon `12-17`, evening `17-21`, night `18-23`. State
     the dates you resolved so the user can correct them.
3. **Apply config defaults**: `airlines` = `preferred_airlines`, `alliance` =
   `preferred_alliance`, `cabin_class`, `passengers`, `checked_bags`, `carry_on`,
   and `max_layover` = `max_layover_minutes`. Map `nonstop_preference` to
   `max_stops`: `require` or `prefer` → `NON_STOP`; `no_preference` → omit
   `max_stops`.
4. **Search the preferred case first** (preferred airline + the strongest stop
   setting). If `nonstop_preference` is `require`, keep `NON_STOP`.
5. **If nothing clean comes back, widen in this order** (stop as soon as a clean
   option appears), re-checking after each step. When `redeye` is `avoid`, a
   result counts as clean only if it is not a red-eye (overnight flight or
   overnight layover).
   1. Non-stop on any airline (omit `airlines` and `alliance`).
   2. Preferred airline with 1 stop (`max_stops` = `ONE_STOP`), within
      `max_layover` (skip when `nonstop_preference` is `require`).
   3. Any airline with 1 stop (`max_stops` = `ONE_STOP`), within `max_layover`
      (omit `airlines` and `alliance`; skip when `nonstop_preference` is
      `require`).
   4. Relax `max_layover` (only if `layover_negotiable`) and re-run the 1-stop
      searches; do this before accepting more stops or a red-eye.
6. **Filter out red-eyes** when `redeye` is `avoid` (overnight flights and
   overnight layovers). Only present one if nothing else works, and label it.
7. **Pick the best match**, then show 2-4 alternatives.

## Resolving preference conflicts

Small airports often have no non-stops and limited evening banks, so preferences
collide. Resolve in this priority order, and **always name the tradeoff** instead
of silently violating a preference:

1. Honor a hard `require` (non-stop required).
2. Avoid red-eyes when `redeye` is `avoid`.
3. Fewest stops (1 stop max as the fallback).
4. Preferred airline (yields to avoid a red-eye or an extra stop).
5. Layover under `max_layover_minutes` (relax first when `layover_negotiable`).

When a hard request is impossible (e.g. "evening departure, home same night"
from a small airport), say so plainly, explain why (route/connection-bank
limits), and offer the closest feasible options as a choice.

## Output format

Lead with the recommended itinerary, then alternatives. For each itinerary:

- Direction + date + day, and whether it meets the preferences (flag misses).
- A table of segments: flight number, route, depart, arrive.
- Stops, layover airport + duration, total duration.
- Note red-eye / overnight layover / next-day arrival explicitly when present.

Don't lead with price unless asked; still show it as a data point. Never book —
present options and let the user choose. Provide flight numbers so they can book
on the airline site or their travel tool.

## Additional resources

- For `fli` MCP install/setup, see [setup.md](setup.md).
- For the CLI fallback and a JSON parsing helper to sort/filter results, see
  [reference.md](reference.md).
