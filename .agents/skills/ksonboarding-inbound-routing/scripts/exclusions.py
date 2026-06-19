"""Operator-requested ticket exclusions — never retype these IDs."""

from __future__ import annotations

# ticket_id -> reason (shown in dry-run / live-run output)
EXCLUDED: dict[int, str] = {
    56976: "Operator: do not move — Re: Transfer of account",
    51923: "Operator: do not move — RE: Onboarding setup for Golterman and Sabo",
}


def is_excluded(ticket_id: int) -> bool:
    return int(ticket_id) in EXCLUDED


def exclusion_reason(ticket_id: int) -> str | None:
    return EXCLUDED.get(int(ticket_id))
