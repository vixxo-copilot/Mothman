#!/usr/bin/env python3
"""Export Crystal's open SF Tasks + priority Cases/Leads to JSON for HTML report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[2]
HELPERS = SKILL_ROOT.parent / "sf-case-email-sync" / "scripts"
sys.path.insert(0, str(HELPERS))

from sf_helpers import resolve_user_id, sf_query  # noqa: E402

OUTPUT_DIR = REPO_ROOT / ".tmp" / "mothman-good-morning"
DEFAULT_OWNER = "Crystal.Gagner@vixxo.com"
LIGHTNING = "https://vixxo.lightning.force.com/lightning/r"

BUCKET_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Voicemail / 4046", re.compile(r"voicemail|4046|vendor relations", re.I)),
    ("COI / insurance", re.compile(r"\bcoi\b|certificate|insurance|federated", re.I)),
    ("Rate / negotiation", re.compile(r"rate|negotiation|rbat|ror", re.I)),
    ("Duplicate / merge", re.compile(r"duplicate|merge|dupe", re.I)),
    ("Onboarding / vetting", re.compile(r"onboard|vetting|inbound", re.I)),
    ("Follow-up / callback", re.compile(r"follow[- ]?up|callback|call back", re.I)),
    ("AP / payment", re.compile(r"\bap\b|payment|invoice|remit", re.I)),
]


def _chicago_today() -> date:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/Chicago")).date()
    except Exception:
        return date.today()


def _bucket(subject: str) -> str:
    for label, pat in BUCKET_RULES:
        if pat.search(subject or ""):
            return label
    return "Other"


def _case_pri_rank(priority: str | None) -> int:
    p = (priority or "").lower()
    if p in ("high", "critical"):
        return 0
    if p in ("medium", "normal"):
        return 1
    if "tbd" in p:
        return 2
    return 3


def _rt_name(rec: dict) -> str:
    rt = rec.get("RecordType")
    if isinstance(rt, dict):
        return rt.get("Name") or ""
    return ""


def _case_row(c: dict) -> dict[str, Any]:
    cid = c.get("Id")
    return {
        "kind": "Case",
        "id": cid,
        "number": c.get("CaseNumber"),
        "subject": (c.get("Subject") or "")[:140],
        "status": c.get("Status"),
        "priority": c.get("Priority"),
        "record_type": _rt_name(c),
        "created": (c.get("CreatedDate") or "")[:10],
        "last_modified": (c.get("LastModifiedDate") or "")[:16],
        "url": f"{LIGHTNING}/Case/{cid}/view" if cid else None,
    }


def _task_row(t: dict, as_of: date) -> dict[str, Any]:
    subj = (t.get("Subject") or "").strip() or "(no subject)"
    what = t.get("What") or {}
    what_type = what.get("Type") or ""
    what_name = what.get("Name") or ""
    due_raw = t.get("ActivityDate")
    due = due_raw[:10] if due_raw else None
    tid = t.get("Id")
    what_id = t.get("WhatId")
    return {
        "kind": "Task",
        "id": tid,
        "subject": subj[:140],
        "status": t.get("Status"),
        "priority": t.get("Priority") or "Normal",
        "bucket": _bucket(subj),
        "created": (t.get("CreatedDate") or "")[:10],
        "due": due,
        "what_type": what_type,
        "what_name": what_name,
        "what_id": what_id,
        "overdue": bool(due and date.fromisoformat(due) < as_of),
        "due_today": bool(due and date.fromisoformat(due) == as_of),
        "url": f"{LIGHTNING}/Task/{tid}/view" if tid else None,
        "case_url": (
            f"{LIGHTNING}/Case/{what_id}/view"
            if what_type == "Case" and what_id
            else None
        ),
    }


def _lead_row(l: dict) -> dict[str, Any]:
    lid = l.get("Id")
    return {
        "kind": "Lead",
        "id": lid,
        "name": l.get("Name"),
        "company": l.get("Company"),
        "status": l.get("Status"),
        "rating": l.get("Rating"),
        "source": l.get("LeadSource"),
        "created": (l.get("CreatedDate") or "")[:10],
        "url": f"{LIGHTNING}/Lead/{lid}/view" if lid else None,
    }


def build_payload(owner_id: str, org: str, as_of: date) -> dict[str, Any]:
    tasks_raw = sf_query(
        "SELECT Id, Subject, Status, Priority, ActivityDate, CreatedDate, "
        "LastModifiedDate, WhatId, What.Type, What.Name "
        f"FROM Task WHERE OwnerId = '{owner_id}' AND IsClosed = false "
        "ORDER BY ActivityDate ASC NULLS LAST, CreatedDate ASC",
        org=org,
    )
    tasks = [_task_row(t, as_of) for t in tasks_raw]

    high_cases = sf_query(
        "SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate, LastModifiedDate, "
        "RecordType.Name "
        f"FROM Case WHERE OwnerId = '{owner_id}' AND IsClosed=false AND Priority='High' "
        "ORDER BY CreatedDate ASC",
        org=org,
    )
    med_cases = sf_query(
        "SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate, LastModifiedDate, "
        "RecordType.Name "
        f"FROM Case WHERE OwnerId = '{owner_id}' AND IsClosed=false AND Priority='Medium' "
        "ORDER BY CreatedDate ASC",
        org=org,
    )
    new_cases = sf_query(
        "SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate, LastModifiedDate, "
        "RecordType.Name "
        f"FROM Case WHERE OwnerId = '{owner_id}' AND IsClosed=false "
        "AND CreatedDate = LAST_N_DAYS:3 "
        "ORDER BY CreatedDate DESC",
        org=org,
    )
    rate_new = sf_query(
        "SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate "
        f"FROM Case WHERE OwnerId = '{owner_id}' AND IsClosed=false "
        "AND RecordType.Name='Rate Negotiation' AND Status='New' "
        "ORDER BY CreatedDate ASC",
        org=org,
    )
    leads = sf_query(
        "SELECT Id, Name, Company, Status, LeadSource, CreatedDate, LastModifiedDate, Rating "
        f"FROM Lead WHERE OwnerId = '{owner_id}' AND IsConverted=false "
        "ORDER BY CreatedDate DESC",
        org=org,
    )
    pri_mix = sf_query(
        f"SELECT Priority, COUNT(Id) cnt FROM Case WHERE OwnerId='{owner_id}' "
        "AND IsClosed=false GROUP BY Priority",
        org=org,
    )

    buckets: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        buckets[t["bucket"]].append(t)

    overdue = [t for t in tasks if t["overdue"]]
    due_today = [t for t in tasks if t["due_today"]]

    priority_items: list[dict[str, Any]] = []

    def add_priority(item: dict, tier: str, reason: str) -> None:
        row = dict(item)
        row["tier"] = tier
        row["reason"] = reason
        priority_items.append(row)

    for c in high_cases:
        add_priority(_case_row(c), "P1 — High Case", "SF Priority = High")
    for c in med_cases:
        add_priority(_case_row(c), "P2 — Medium Case", "SF Priority = Medium")
    for t in overdue:
        add_priority(t, "P1 — Overdue Task", f"Due {t['due']}")
    for t in buckets.get("Duplicate / merge", []):
        add_priority(t, "P2 — Duplicate merge", "Carefree / merge queue")
    for c in new_cases:
        row = _case_row(c)
        subj = (row.get("subject") or "").lower()
        if "voicemail" in subj:
            continue
        if row.get("record_type") in ("Provider Onboarding", "Recruitment Request"):
            add_priority(row, "P2 — New assignment", f"Created {row['created']}")
        elif _case_pri_rank(row.get("priority")) <= 2:
            add_priority(row, "P2 — New assignment", f"Created {row['created']}")

    priority_items.sort(
        key=lambda x: (
            0 if x["tier"].startswith("P1") else 1,
            x.get("created") or "",
            x.get("due") or "9999",
        )
    )

    return {
        "report_kind": "sf_task_breakdown",
        "date_label": as_of.strftime("%A, %B %d, %Y"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M CST"),
        "owner_email": DEFAULT_OWNER,
        "summary": {
            "tasks_total": len(tasks),
            "tasks_overdue": len(overdue),
            "tasks_due_today": len(due_today),
            "cases_high": len(high_cases),
            "cases_medium": len(med_cases),
            "cases_new_3d": len(new_cases),
            "rate_new": len(rate_new),
            "leads_open": len(leads),
            "case_priority_mix": {
                (r.get("Priority") or "Unknown"): int(r.get("cnt") or 0)
                for r in pri_mix
            },
            "task_buckets": dict(Counter(t["bucket"] for t in tasks)),
            "task_status": dict(Counter(t["status"] for t in tasks)),
        },
        "priority_items": priority_items,
        "overdue_tasks": overdue,
        "due_today_tasks": due_today,
        "high_cases": [_case_row(c) for c in high_cases],
        "medium_cases": [_case_row(c) for c in med_cases],
        "new_cases_last_3_days": [_case_row(c) for c in new_cases],
        "rate_new_cases": [_case_row(c) for c in rate_new],
        "open_leads": [_lead_row(l) for l in leads],
        "task_buckets": {k: v for k, v in sorted(buckets.items(), key=lambda x: -len(x[1]))},
        "all_tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export SF task breakdown JSON")
    parser.add_argument("--json", action="store_true", help="Print path to stdout")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today Chicago)")
    args = parser.parse_args()

    as_of = date.fromisoformat(args.date) if args.date else _chicago_today()
    org = "vixxo"
    owner_id = resolve_user_id(org, owner_email=DEFAULT_OWNER)
    payload = build_payload(owner_id, org, as_of)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"sf-task-breakdown-{as_of.isoformat()}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps({"ok": True, "path": str(out), "summary": payload["summary"]}))
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
