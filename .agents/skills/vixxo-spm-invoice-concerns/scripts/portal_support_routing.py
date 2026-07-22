#!/usr/bin/env python3
"""Route VixxoLink portal login/access blockers to VINT — no AP forward."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

VINT_GROUP_ID = 159000486559
VIXXOLINK_SUPPORT_TYPE = "VixxoLink Support"
ROUTING_TAGS = ("vixxolink-portal-support", "vint-routed", "open-hold")
DEFAULT_NOTE = (
    "Assigned to VINT group (159000486559) — VixxoLink portal login/access/setup. "
    "Type set to VixxoLink Support. No forward to invoices@vixxo.com; leave Open."
)


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.I | re.M) is not None


def primary_message_text(text: str) -> str:
    """Requester content before forwarded/reply history."""
    if not text:
        return ""
    parts = re.split(
        r"\n_{5,}|\nFrom:\s|\n-----Original Message-----|\nOn .+ wrote:\s*",
        text,
        maxsplit=1,
        flags=re.I,
    )
    return (parts[0] or text).strip()


def is_vixxolink_portal_blocker(subject: str, text: str) -> bool:
    """
    True when the provider ask is portal login/access/setup — not invoice AP intake.

    Audit: FD #70128 — reply to past-due campaign; quoted thread mentions outstanding
    invoices but requester cannot log in to VixxoLink. Must not forward to invoices@.
    """
    primary = primary_message_text(text)
    combined = f"{subject}\n{primary}"
    portal = _has(r"\b(vixxolink|vixxolink\.com|portal)\b", combined)
    access = _has(
        r"\b("
        r"log ?in|login|log-in|access|set up|setup|account setup|"
        r"cannot submit|can't submit|can not submit|"
        r"do not have a log|don't have a log|no log in|"
        r"gain access|reach out to help us set up|help us set up the account|"
        r"someone will reach out to help us set up"
        r")\b",
        combined,
    )
    if portal and access:
        return True
    if _has(r"\bgain access to\b.{0,60}\b(vixxolink|portal)\b", combined):
        return True
    if _has(r"\bhelp\b.{0,40}\b(vixxolink|portal)\b", combined) and _has(
        r"\b(log ?in|login|access|account)\b", combined
    ):
        return True
    return False


@dataclass
class PortalSupportRouteResult:
    ticket_id: int
    status: str  # routed | skipped-already-routed | error
    group_id: int = VINT_GROUP_ID
    ticket_type: str = VIXXOLINK_SUPPORT_TYPE
    tags: list[str] = field(default_factory=list)
    error: str = ""


def merge_tags(existing: list[str], new: list[str]) -> list[str]:
    merged = list(existing or [])
    for tag in new:
        if tag not in merged:
            merged.append(tag)
    return merged


def route_vixxolink_portal_support(
    domain: str,
    api_key: str,
    ticket: dict,
    *,
    note: str | None = None,
    get_ticket,
    update_ticket,
    create_private_note,
) -> PortalSupportRouteResult:
    """Move ticket to VINT, set type VixxoLink support, leave Open — no AP forward."""
    ticket_id = int(ticket["id"])
    result = PortalSupportRouteResult(ticket_id=ticket_id, status="routed")
    try:
        fresh = get_ticket(domain, api_key, ticket_id)
        tags = list(fresh.get("tags") or [])
        if (
            int(fresh.get("group_id") or 0) == VINT_GROUP_ID
            and fresh.get("type") == VIXXOLINK_SUPPORT_TYPE
            and all(t in tags for t in ROUTING_TAGS)
        ):
            result.status = "skipped-already-routed"
            result.tags = tags
            return result

        new_tags = merge_tags(tags, list(ROUTING_TAGS))
        cur = int(fresh.get("status") or 2)
        hold_status = cur if cur in (2, 3) else 2
        update_ticket(
            domain,
            api_key,
            ticket_id,
            {
                "status": hold_status,
                "type": VIXXOLINK_SUPPORT_TYPE,
                "group_id": VINT_GROUP_ID,
                "tags": new_tags,
            },
        )
        create_private_note(domain, api_key, ticket_id, note or DEFAULT_NOTE)
        refreshed = get_ticket(domain, api_key, ticket_id)
        result.tags = list(refreshed.get("tags") or new_tags)
        result.group_id = int(refreshed.get("group_id") or VINT_GROUP_ID)
    except Exception as exc:  # noqa: BLE001
        result.status = "error"
        result.error = str(exc)
    return result
