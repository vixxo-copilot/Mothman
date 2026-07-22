#!/usr/bin/env python3
"""QSI AP voicemail merge helpers — always merge into an open/pending primary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Freshdesk status: 2=Open, 3=Pending, 4=Resolved, 5=Closed
FD_OPEN = 2
FD_PENDING = 3
FD_TERMINAL = frozenset({4, 5})


def status_label(status: int | None) -> str:
    return {
        2: "Open",
        3: "Pending",
        4: "Resolved",
        5: "Closed",
    }.get(int(status or 0), f"status-{status}")


def is_open_for_merge(ticket: dict) -> bool:
    return int(ticket.get("status") or 0) == FD_OPEN


def is_merge_primary_candidate(ticket: dict) -> bool:
    """Primary must be Open (preferred) or Pending if nothing is open."""
    st = int(ticket.get("status") or 0)
    return st in (FD_OPEN, FD_PENDING)


def pick_open_merge_primary(
    tickets: list[dict],
    *,
    prefer_known_sp: bool = True,
) -> dict:
    """Return the ticket dict to use as merge primary.

    Rules:
    1. Never select Resolved/Closed as primary.
    2. Prefer Open over Pending.
    3. Among equals, prefer known-sp tag, then newest created_at.
    """
    if not tickets:
        raise ValueError("pick_open_merge_primary: empty ticket list")

    open_pool = [t for t in tickets if int(t.get("status") or 0) == FD_OPEN]
    pool = open_pool or [t for t in tickets if int(t.get("status") or 0) == FD_PENDING]
    if not pool:
        ids = [int(t["id"]) for t in tickets]
        statuses = {int(t["id"]): status_label(t.get("status")) for t in tickets}
        raise ValueError(
            f"No open/pending primary available for tickets {ids}; statuses={statuses}. "
            "Reopen the intended primary before merging."
        )

    def sort_key(t: dict) -> tuple:
        tags = set(t.get("tags") or [])
        known = 1 if prefer_known_sp and "known-sp" in tags else 0
        created = t.get("created_at") or ""
        return (known, created)

    return max(pool, key=sort_key)


def merge_secondaries(primary: dict, tickets: list[dict]) -> list[int]:
    """Ticket ids to merge into primary (excludes primary; skips already terminal)."""
    pid = int(primary["id"])
    out: list[int] = []
    for t in tickets:
        tid = int(t["id"])
        if tid == pid:
            continue
        if int(t.get("status") or 0) in FD_TERMINAL:
            continue
        out.append(tid)
    return out


def ensure_primary_open(
    http_json,
    api_key: str,
    primary: dict,
) -> dict:
    """Re-fetch primary; reopen if needed so team sees it in queue."""
    pid = int(primary["id"])
    if int(primary.get("status") or 0) == FD_OPEN:
        return primary
    if int(primary.get("status") or 0) in FD_TERMINAL:
        raise ValueError(
            f"Primary #{pid} is {status_label(primary.get('status'))} — "
            "cannot merge into a closed/resolved ticket. Pick another open ticket in the group."
        )
    # Pending → Open so SPM/VINT queues surface the merged item
    return http_json(
        "PUT",
        f"/api/v2/tickets/{pid}",
        api_key,
        {"status": FD_OPEN},
    )


def merge_qsiap_tickets(
    http_json,
    api_key: str,
    tickets: list[dict],
    *,
    label: str,
    phone: str = "",
    note_lines: list[str] | None = None,
    prefer_known_sp: bool = True,
) -> dict[str, Any]:
    """Merge duplicate qsiap voicemails into the open primary."""
    primary = pick_open_merge_primary(tickets, prefer_known_sp=prefer_known_sp)
    primary = ensure_primary_open(http_json, api_key, primary)
    pid = int(primary["id"])
    secondary_ids = merge_secondaries(primary, tickets)
    if not secondary_ids:
        return {
            "primary_id": pid,
            "primary_status": status_label(primary.get("status")),
            "merged": [],
            "skipped": "no open/pending secondaries",
        }

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"**QSI AP voicemail duplicate merge** ({ts})",
        "",
        f"**Group:** {label}" + (f" ({phone})" if phone else ""),
        f"**Primary kept open:** #{pid} ({status_label(primary.get('status'))})",
        f"**Merged and closed:** {', '.join(f'#{s}' for s in secondary_ids)}",
        "",
        "Primary selected by open-status rule (never closed/resolved).",
    ]
    if note_lines:
        lines.extend(["", *note_lines])

    http_json(
        "PUT",
        "/api/v2/tickets/merge",
        api_key,
        {
            "primary_id": pid,
            "ticket_ids": secondary_ids,
            "convert_recepients_to_cc": True,
            "note_in_primary": {"body": "\n".join(lines), "private": True},
        },
    )
    return {
        "primary_id": pid,
        "primary_status": status_label(primary.get("status")),
        "merged": secondary_ids,
    }
