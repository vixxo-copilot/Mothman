"""Flag Cases that are Prospect SP or onboarding-intent — not Crystal's queue."""

from __future__ import annotations

import re
from typing import Any

RECRUITMENT_RECORD_TYPES = frozenset(
    {"Provider Onboarding", "Recruitment Request"}
)
PROSPECT_SP_TYPE = "prospect sp"

ONBOARDING_SUBJECT_RE = re.compile(
    r"potential provider lead"
    r"|prospect\s*sp"
    r"|looking to (?:onboard|join)"
    r"|want(?:s|ing)? to (?:onboard|join|become)"
    r"|interested in becoming"
    r"|become (?:a |an )?(?:provider|vendor|service provider)"
    r"|new service provider"
    r"|\bonboard(?:ing)?\b",
    re.I,
)

ROUTE_NOTE = "Recruitment / onboarding — not Crystal (SPS)"


def _rt_name(row: dict[str, Any]) -> str:
    rt = row.get("RecordType")
    if isinstance(rt, dict):
        return (rt.get("Name") or "").strip()
    return (
        row.get("record_type")
        or row.get("RecordType.Name")
        or ""
    ).strip()


def _type_picklist(row: dict[str, Any]) -> str:
    return (
        row.get("Type")
        or row.get("type")
        or row.get("type_picklist")
        or ""
    ).strip()


def _subject(row: dict[str, Any]) -> str:
    return row.get("Subject") or row.get("subject") or ""


def prospect_onboarding_reason(row: dict[str, Any]) -> str | None:
    """Why this Case should not stay on Crystal's SPS queue, or None."""
    type_pick = _type_picklist(row)
    if type_pick.lower() == PROSPECT_SP_TYPE:
        return "Prospect SP"
    rt = _rt_name(row)
    if rt in RECRUITMENT_RECORD_TYPES:
        return rt
    if ONBOARDING_SUBJECT_RE.search(_subject(row)):
        return "Onboarding intent (subject)"
    return None


def is_prospect_or_onboarding(row: dict[str, Any]) -> bool:
    return prospect_onboarding_reason(row) is not None
