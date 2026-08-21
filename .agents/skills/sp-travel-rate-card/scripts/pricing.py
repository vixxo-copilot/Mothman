"""Suggested flat-travel math for SP local vs extended rate cards."""
from __future__ import annotations


def round_to_increment(value: float, increment: int) -> int:
    if increment <= 0:
        return int(round(value))
    return int(round(value / increment) * increment)


def resolve_anchor_travel(extended: dict) -> tuple[int, str]:
    """Return (travel_dollars, how_derived)."""
    if extended.get("travel") is not None:
        return int(extended["travel"]), "explicit travel"
    trip_min = extended.get("trip_minimum")
    labor_rate = extended.get("labor_rate")
    hours = extended.get("labor_hours_in_minimum", 1)
    if trip_min is None or labor_rate is None:
        raise ValueError(
            "extended.travel is required, or provide trip_minimum + labor_rate "
            "(travel = minimum minus included labor)"
        )
    travel = int(trip_min) - int(round(float(labor_rate) * float(hours)))
    if travel < 0:
        raise ValueError("anchor travel is negative — check trip_minimum vs included labor")
    return travel, (
        f"trip_minimum ${trip_min} minus {hours} hour(s) at ${labor_rate}"
    )


def territory(miles: float, local_max_miles: float) -> str:
    return "Local" if miles <= local_max_miles else "Extended"


def range_band(miles: float, band_low: float, local_max: float) -> str:
    if miles < band_low:
        return f"Under {band_low:g}"
    if miles <= local_max:
        return f"{band_low:g}-{local_max:g} (local)"
    return f">{local_max:g} (extended)"


def suggested_travel(
    miles: float,
    *,
    local_max_miles: float,
    local_travel: int,
    anchor_miles: float,
    anchor_travel: int,
    round_to: int = 5,
    hold_anchor: bool = False,
) -> int:
    if hold_anchor:
        return int(anchor_travel)
    if miles <= local_max_miles:
        return int(local_travel)
    if not anchor_miles:
        raise ValueError("anchor_miles is 0 — cannot scale extended travel")
    raw = anchor_travel * (miles / anchor_miles)
    return round_to_increment(raw, round_to)


def travel_from_drive_time(
    one_way_minutes: float,
    labor_rate: float,
    *,
    round_trip: bool = True,
) -> int | None:
    """Bill drive time at the hourly labor rate. Default is round-trip."""
    if labor_rate is None:
        return None
    hours = (float(one_way_minutes) * (2 if round_trip else 1)) / 60.0
    return int(round(hours * float(labor_rate)))
