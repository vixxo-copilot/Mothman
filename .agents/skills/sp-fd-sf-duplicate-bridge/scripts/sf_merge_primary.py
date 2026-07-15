"""Primary Case selection for merge automation — status and assignment aware."""

from __future__ import annotations

import re

OPEN_STATUSES = {"new", "working", "open", "pending", "escalated", "on hold"}
ACTIVE_STATUSES = {"working", "open", "pending", "escalated", "on hold"}
NEW_STATUS = "new"
SHELL_ACCOUNT = "Service Provider Support Shell Account"

QUEUE_NAME_HINTS = re.compile(
    r"\b(onboarding|queue|management|support|spm|coi|ksonboarding)\b",
    re.I,
)


def status_key(status: str | None) -> str:
    return (status or "").strip().lower()


def is_open(case: dict) -> bool:
    return status_key(case.get("status")) in OPEN_STATUSES


def is_closed(case: dict) -> bool:
    return not is_open(case)


def is_actively_worked(case: dict) -> bool:
    return status_key(case.get("status")) in ACTIVE_STATUSES


def is_new(case: dict) -> bool:
    return status_key(case.get("status")) == NEW_STATUS


def is_user_assigned(case: dict) -> bool:
    if case.get("is_user_assigned") is True:
        return True
    if case.get("is_user_assigned") is False:
        return False
    owner_type = (case.get("owner_type") or "").lower()
    if owner_type == "user":
        return True
    if owner_type in {"group", "queue"}:
        return False
    owner = case.get("owner") or ""
    if "@" in owner:
        return True
    if QUEUE_NAME_HINTS.search(owner):
        return False
    return bool(owner and owner.strip())


def enrich_owner_fields(entry: dict, raw_case: dict) -> dict:
    owner = raw_case.get("Owner") or {}
    if isinstance(owner, dict):
        entry["owner_id"] = owner.get("Id")
        entry["owner_type"] = owner.get("Type")
        entry["owner"] = owner.get("Username") or owner.get("Name") or entry.get("owner")
        entry["is_user_assigned"] = (owner.get("Type") or "").lower() == "user"
        if owner.get("Type") is None and owner.get("Username"):
            entry["is_user_assigned"] = "@" in (owner.get("Username") or "")
    entry["description"] = raw_case.get("Description") or entry.get("description") or ""
    entry["last_modified_at"] = raw_case.get("LastModifiedDate") or entry.get("last_modified_at")
    return entry


def last_touch_at(case: dict) -> str:
    return (
        case.get("last_touch_at")
        or case.get("last_modified_at")
        or case.get("created_at")
        or ""
    )


def has_activity_touch(case: dict) -> bool:
    sources = case.get("last_touch_sources") or []
    return any(s in sources for s in ("case_comment", "case_history", "task"))


def _rank(case: dict) -> tuple:
    """Higher rank = better merge primary."""
    touch = last_touch_at(case)
    return (
        is_actively_worked(case),
        is_user_assigned(case),
        has_activity_touch(case),
        (case.get("account") or "") != SHELL_ACCOUNT,
        touch,
        case.get("created_at") or "",
    )


def _sort_key(case: dict) -> tuple:
    """Lower is better primary (inverse of rank for stable sorts)."""
    rank = _rank(case)
    return (
        0 if rank[0] else 1,
        0 if rank[1] else 1,
        0 if rank[2] else 1,
        0 if rank[3] else 1,
        _invert_iso(rank[4]),
        rank[5],
    )


def _invert_iso(iso: str) -> str:
    """Sort ascending prefers newer ISO timestamps."""
    if not iso:
        return ""
    return "".join(chr(255 - ord(c)) if ord(c) < 255 else c for c in iso)


def pick_best(cases: list[dict]) -> dict:
    return max(cases, key=_rank)


def pick_merge_primary(cases: list[dict]) -> tuple[dict | None, str | None]:
    """Select merge primary from open Cases only.

    Returns (primary, manual_review_reason). primary is None when operator review
    is required. Never returns a closed Case.
    """
    open_cases = [c for c in cases if is_open(c)]
    if not open_cases:
        return None, "all_closed"

    active = [c for c in open_cases if is_actively_worked(c)]
    if active:
        return pick_best(active), None

    new_cases = [c for c in open_cases if is_new(c)]
    if not new_cases:
        return pick_best(open_cases), None

    assigned = [c for c in new_cases if is_user_assigned(c)]
    if len(assigned) == 1:
        return assigned[0], None
    if len(assigned) > 1:
        return pick_best(assigned), "multiple_new_assigned"
    if len(new_cases) > 1:
        touched = [c for c in new_cases if has_activity_touch(c)]
        if len(touched) == 1:
            return touched[0], None
        if len(touched) > 1:
            best = pick_best(touched)
            runner_up = sorted(touched, key=_rank, reverse=True)[1]
            if last_touch_at(best) > last_touch_at(runner_up):
                return best, None
            return best, "multiple_new_recent_activity"
        return None, "multiple_new_unassigned"
    return new_cases[0], None


def pick_primary(cases: list[dict]) -> dict:
    """Backward-compatible wrapper — never pick closed when open exist."""
    primary, reason = pick_merge_primary(cases)
    if primary:
        return primary
    if reason == "all_closed":
        return sorted(cases, key=lambda c: c.get("created_at") or "")[0]
    open_cases = [c for c in cases if is_open(c)]
    return pick_best(open_cases or cases)
