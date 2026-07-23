#!/usr/bin/env python3
"""Verify EmailMessage and Files coverage for synced Cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sf_helpers import case_file_titles, case_message_identifiers, resolve_user_id, sf_query


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify SF case email sync state")
    p.add_argument("--org", default="vixxo")
    p.add_argument("--case-id")
    p.add_argument("--case-number")
    p.add_argument("--owner-me", action="store_true")
    p.add_argument("--limit", type=int, default=25)
    return p.parse_args()


def fetch_case(org: str, case_id: str | None, case_number: str | None) -> dict | None:
    fields = "Id, CaseNumber, Subject, Status"
    if case_id:
        rows = sf_query(f"SELECT {fields} FROM Case WHERE Id = '{case_id}' LIMIT 1", org=org)
    elif case_number:
        num = case_number.lstrip("0")
        rows = sf_query(
            f"SELECT {fields} FROM Case WHERE CaseNumber = '{num}' "
            f"OR CaseNumber = '{case_number.zfill(8)}' LIMIT 1",
            org=org,
        )
    else:
        return None
    return rows[0] if rows else None


def fetch_open_cases(org: str, owner_id: str, limit: int) -> list[dict]:
    fields = "Id, CaseNumber, Subject, Status"
    return sf_query(
        f"SELECT {fields} FROM Case WHERE OwnerId = '{owner_id}' AND IsClosed = false "
        f"ORDER BY LastModifiedDate DESC LIMIT {limit}",
        org=org,
    )


def verify_case(case: dict, org: str) -> dict:
    case_id = case["Id"]
    emails = sf_query(
        "SELECT Id, Subject, FromAddress, MessageDate, MessageIdentifier "
        f"FROM EmailMessage WHERE ParentId = '{case_id}' ORDER BY MessageDate",
        org=org,
    )
    titles = sorted(case_file_titles(case_id, org=org))
    msg_ids = sorted(case_message_identifiers(case_id, org=org))
    eml_files = [t for t in titles if " - RE" in t or " - FW" in t or t.endswith(".eml")]
    return {
        "case_number": case.get("CaseNumber"),
        "case_id": case_id,
        "subject": case.get("Subject"),
        "status": case.get("Status"),
        "email_message_count": len(emails),
        "file_count": len(titles),
        "eml_like_files": len(eml_files),
        "message_identifiers": len(msg_ids),
        "recent_emails": [
            {
                "subject": e.get("Subject"),
                "from": e.get("FromAddress"),
                "date": e.get("MessageDate"),
            }
            for e in emails[-5:]
        ],
    }


def main() -> int:
    args = parse_args()
    cases: list[dict] = []
    if args.case_id or args.case_number:
        case = fetch_case(args.org, args.case_id, args.case_number)
        if not case:
            print(json.dumps({"ok": False, "error": "Case not found"}, indent=2))
            return 1
        cases = [case]
    elif args.owner_me:
        owner_id = resolve_user_id(args.org, None)
        cases = fetch_open_cases(args.org, owner_id, args.limit)
    else:
        print("Provide --case-id, --case-number, or --owner-me", file=sys.stderr)
        return 2

    report = {"cases": [verify_case(c, args.org) for c in cases]}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
