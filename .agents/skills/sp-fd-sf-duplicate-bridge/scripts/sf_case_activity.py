"""Fetch last-touch timestamps from Case comments, history, tasks, and LastModifiedDate."""

from __future__ import annotations

from sf_cli import sf_query

BATCH_SIZE = 80


def _chunks(ids: list[str], size: int = BATCH_SIZE) -> list[list[str]]:
    return [ids[i : i + size] for i in range(0, len(ids), size)]


def _in_clause(ids: list[str]) -> str:
    return ",".join(f"'{i}'" for i in ids)


def _max_touch(
    current: dict | None,
    case_id: str,
    at: str | None,
    source: str,
    detail: str | None = None,
) -> dict:
    if not at:
        return current or {}
    entry = current or {
        "last_touch_at": at,
        "last_touch_sources": [],
        "last_touch_detail": None,
    }
    if not entry.get("last_touch_at") or at > entry["last_touch_at"]:
        entry["last_touch_at"] = at
        entry["last_touch_detail"] = detail or source
    if source not in entry["last_touch_sources"]:
        entry["last_touch_sources"].append(source)
    return entry


def seed_from_cache(records: list[dict]) -> dict[str, dict]:
    """Seed touch map from Case LastModifiedDate in SF export."""
    out: dict[str, dict] = {}
    for rec in records:
        cid = rec.get("Id") or rec.get("id")
        lmd = rec.get("LastModifiedDate") or rec.get("last_modified_at")
        if cid and lmd:
            out[cid] = _max_touch(None, cid, lmd, "case_modified")
    return out


def fetch_comment_touches(case_ids: list[str], org: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for batch in _chunks(case_ids):
        rows = sf_query(
            "SELECT ParentId, CreatedDate, CreatedBy.Name, CommentBody "
            f"FROM CaseComment WHERE ParentId IN ({_in_clause(batch)}) "
            "ORDER BY CreatedDate DESC",
            org=org,
        )
        seen: set[str] = set()
        for row in rows:
            pid = row.get("ParentId")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            author = (row.get("CreatedBy") or {}).get("Name") or "unknown"
            body = (row.get("CommentBody") or "")[:80].replace("'", "")
            out[pid] = _max_touch(
                out.get(pid),
                pid,
                row.get("CreatedDate"),
                "case_comment",
                f"comment by {author}: {body}",
            )
    return out


def fetch_history_touches(case_ids: list[str], org: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for batch in _chunks(case_ids):
        rows = sf_query(
            "SELECT CaseId, CreatedDate, Field, CreatedBy.Name, OldValue, NewValue "
            f"FROM CaseHistory WHERE CaseId IN ({_in_clause(batch)}) "
            "ORDER BY CreatedDate DESC",
            org=org,
        )
        seen: set[str] = set()
        for row in rows:
            cid = row.get("CaseId")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            field = row.get("Field") or "field"
            author = (row.get("CreatedBy") or {}).get("Name") or "unknown"
            out[cid] = _max_touch(
                out.get(cid),
                cid,
                row.get("CreatedDate"),
                "case_history",
                f"{field} change by {author}",
            )
    return out


def fetch_task_touches(case_ids: list[str], org: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for batch in _chunks(case_ids):
        rows = sf_query(
            "SELECT WhatId, LastModifiedDate, CreatedDate, Subject, Status "
            f"FROM Task WHERE WhatId IN ({_in_clause(batch)}) "
            "ORDER BY LastModifiedDate DESC",
            org=org,
        )
        seen: set[str] = set()
        for row in rows:
            wid = row.get("WhatId")
            if not wid or wid in seen:
                continue
            seen.add(wid)
            subj = (row.get("Subject") or "")[:60]
            at = row.get("LastModifiedDate") or row.get("CreatedDate")
            out[wid] = _max_touch(
                out.get(wid),
                wid,
                at,
                "task",
                f"task: {subj}",
            )
    return out


def merge_touch_maps(*maps: dict[str, dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for mp in maps:
        for cid, info in mp.items():
            existing = out.get(cid)
            at = info.get("last_touch_at")
            if not existing:
                out[cid] = {
                    "last_touch_at": at,
                    "last_touch_sources": list(info.get("last_touch_sources") or []),
                    "last_touch_detail": info.get("last_touch_detail"),
                }
                continue
            if at and (not existing.get("last_touch_at") or at > existing["last_touch_at"]):
                existing["last_touch_at"] = at
                existing["last_touch_detail"] = info.get("last_touch_detail")
            for src in info.get("last_touch_sources") or []:
                if src not in existing["last_touch_sources"]:
                    existing["last_touch_sources"].append(src)
    return out


def fetch_last_touches(
    case_ids: list[str],
    org: str = "vixxo",
    cache_records: list[dict] | None = None,
) -> dict[str, dict]:
    """Return {caseId: {last_touch_at, last_touch_sources, last_touch_detail}}."""
    unique = sorted({i for i in case_ids if i})
    if not unique:
        return {}

    touch = seed_from_cache(cache_records or [])
    if org:
        touch = merge_touch_maps(
            touch,
            fetch_comment_touches(unique, org),
            fetch_history_touches(unique, org),
            fetch_task_touches(unique, org),
        )
    return touch


def apply_touch_fields(case: dict, touch_map: dict[str, dict]) -> dict:
    cid = case.get("id") or case.get("Id")
    info = touch_map.get(cid or "")
    if info:
        case["last_touch_at"] = info.get("last_touch_at")
        case["last_touch_sources"] = info.get("last_touch_sources")
        case["last_touch_detail"] = info.get("last_touch_detail")
    elif case.get("last_modified_at") and not case.get("last_touch_at"):
        case["last_touch_at"] = case["last_modified_at"]
        case["last_touch_sources"] = ["case_modified"]
    return case
