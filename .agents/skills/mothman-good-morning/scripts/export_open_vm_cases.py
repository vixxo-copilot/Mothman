#!/usr/bin/env python3
"""Export Crystal-owned open Salesforce voicemail Cases to JSON.

Includes generic intake subjects and rewritten `Voicemail —` Cases still
assigned to the operator. Used by Good Morning cascade 2.5 to rebuild the
open-voicemail HTML report after triage.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[2]
HELPERS = SKILL_ROOT.parent / "sf-case-email-sync" / "scripts"
sys.path.insert(0, str(HELPERS))
sys.path.insert(0, str(SCRIPT_DIR))

from prospect_onboarding import (  # noqa: E402
    ROUTE_NOTE,
    prospect_onboarding_reason,
)
from sf_helpers import resolve_user_id, sf_query  # noqa: E402

OUTPUT_DIR = REPO_ROOT / ".tmp" / "mothman-good-morning"
DEFAULT_OWNER = "Crystal.Gagner@vixxo.com"
LIGHTNING = "https://vixxo.lightning.force.com/lightning/r"
RENAMED_PREFIXES = ("voicemail —", "voicemail -", "vm triage —", "vm triage -")


def _chicago_today() -> date:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/Chicago")).date()
    except Exception:
        return date.today()


def _rt_name(rec: dict[str, Any]) -> str:
    rt = rec.get("RecordType")
    if isinstance(rt, dict):
        return rt.get("Name") or ""
    return ""


def _is_renamed(subject: str) -> bool:
    return (subject or "").strip().lower().startswith(RENAMED_PREFIXES)


def _intake(subject: str, record_type: str) -> str:
    lowered = (subject or "").lower()
    if _is_renamed(subject):
        return "rewritten"
    if "new voicemail" in lowered:
        return "8x8"
    if "vixxo voicemail" in lowered:
        return "vixxo_voicemail"
    if "voicemail" in lowered:
        return "voicemail"
    return "other"


def _case_row(rec: dict[str, Any], as_of: date) -> dict[str, Any]:
    cid = rec.get("Id")
    subject = rec.get("Subject") or ""
    created_raw = rec.get("CreatedDate") or ""
    created = created_raw[:10]
    age = None
    if created:
        try:
            age = (as_of - date.fromisoformat(created)).days
        except ValueError:
            age = None
    account = rec.get("Account") or {}
    reason = prospect_onboarding_reason(rec)
    renamed = _is_renamed(subject)
    return {
        "id": cid,
        "number": str(rec.get("CaseNumber") or "").lstrip("0") or rec.get("CaseNumber"),
        "subject": subject,
        "status": rec.get("Status"),
        "priority": rec.get("Priority"),
        "type_picklist": rec.get("Type") or "",
        "origin": rec.get("Origin") or "",
        "record_type": _rt_name(rec),
        "created": created,
        "age_days": age,
        "account": account.get("Name") or "",
        "sp_number": account.get("Service_Provider_Number__c") or "",
        "intake": _intake(subject, _rt_name(rec)),
        "triaged": renamed,
        "not_crystal_reason": reason,
        "url": f"{LIGHTNING}/Case/{cid}/view" if cid else None,
    }


def fetch_open_vm_cases(owner_id: str, org: str) -> list[dict[str, Any]]:
    soql = (
        "SELECT Id, CaseNumber, Subject, Status, Priority, Type, Origin, "
        "CreatedDate, LastModifiedDate, RecordType.Name, "
        "Account.Name, Account.Service_Provider_Number__c "
        "FROM Case "
        f"WHERE OwnerId = '{owner_id}' AND IsClosed = false "
        "AND (Subject LIKE '%New voicemail%' "
        "OR Subject LIKE '%Vixxo Voicemail%' "
        "OR Subject LIKE 'Voicemail%' "
        "OR Subject LIKE 'VM Triage%') "
        "ORDER BY CreatedDate DESC"
    )
    return sf_query(soql, org=org)


def build_payload(owner_id: str, org: str, as_of: date, owner_email: str) -> dict[str, Any]:
    raw = fetch_open_vm_cases(owner_id, org)
    cases = [_case_row(c, as_of) for c in raw]
    untriaged = [c for c in cases if not c["triaged"]]
    triaged = [c for c in cases if c["triaged"]]
    not_crystal = [c for c in cases if c.get("not_crystal_reason")]
    return {
        "report_kind": "open_voicemail_cases",
        "date_label": as_of.strftime("%A, %B %d, %Y"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M CST"),
        "owner_email": owner_email,
        "summary": {
            "total_open": len(cases),
            "untriaged": len(untriaged),
            "triaged": len(triaged),
            "not_crystal": len(not_crystal),
            "status_mix": _counts(cases, "status"),
            "intake_mix": _counts(cases, "intake"),
        },
        "not_crystal_note": ROUTE_NOTE,
        "untriaged": untriaged,
        "triaged": triaged,
        "not_crystal": not_crystal,
        "cases": cases,
    }


def _counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        label = str(row.get(key) or "Unknown")
        out[label] = out.get(label, 0) + 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Export open owned voicemail Cases")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today Chicago)")
    parser.add_argument("--org", default="vixxo")
    parser.add_argument("--owner-email", default=DEFAULT_OWNER)
    args = parser.parse_args()

    as_of = date.fromisoformat(args.date) if args.date else _chicago_today()
    owner_id = resolve_user_id(args.org, owner_email=args.owner_email)
    payload = build_payload(owner_id, args.org, as_of, args.owner_email)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"open-voicemail-{as_of.isoformat()}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "path": str(out),
                    "summary": payload["summary"],
                }
            )
        )
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
