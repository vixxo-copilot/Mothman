#!/usr/bin/env python3
"""List Crystal-owned Salesforce voicemail Cases that still have generic subjects.

Used by mothman-good-morning Phase 2.4 and sp-voicemail-triage. A Case is
"generic" when it has not been rewritten to `Voicemail — {SP} — {request}`
and matches either intake:

- 8x8 Email-to-Case: Subject contains `New voicemail`
- Amazon Connect / SP Support: RecordType = Service Provider Support and
  Subject is (or contains) `Vixxo Voicemail`

New assignment window (default 3 days): CreatedDate in LAST_N_DAYS, plus every
generic-subject Case still in Status = New (assigned, not yet vetted/renamed).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SF = os.path.expandvars(r"%APPDATA%\npm\sf.cmd")
ORG_DEFAULT = "vixxo"
OWNER_EMAIL = "Crystal.Gagner@vixxo.com"
RENAMED_PREFIXES = ("voicemail —", "voicemail -", "vm triage —", "vm triage -")


def sf_query(soql: str, org: str) -> list[dict]:
    proc = subprocess.run(
        [SF, "data", "query", "--query", soql, "--target-org", org, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    data = json.loads(proc.stdout or "{}")
    if proc.returncode != 0 and not (data.get("result") or {}).get("records"):
        raise SystemExit(
            f"SOQL failed ({proc.returncode}): {(data.get('message') or proc.stderr or '')[:400]}"
        )
    return ((data.get("result") or {}).get("records")) or []


def resolve_owner_id(org: str, email: str) -> str:
    rows = sf_query(
        "SELECT Id, Name, Email FROM User "
        f"WHERE Email = '{email}' AND IsActive = true LIMIT 1",
        org,
    )
    if not rows:
        raise SystemExit(f"No active User for {email}")
    return rows[0]["Id"]


def intake_kind(subject: str, record_type: str) -> str | None:
    text = (subject or "").strip()
    if not text:
        return None
    lowered = text.lower()
    if any(lowered.startswith(p) for p in RENAMED_PREFIXES):
        return None
    if "new voicemail" in lowered:
        return "8x8"
    if "vixxo voicemail" in lowered and (
        not record_type or record_type == "Service Provider Support"
    ):
        return "vixxo_voicemail"
    return None


def parse_sf_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.replace("+0000", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--org", default=ORG_DEFAULT)
    p.add_argument("--owner-email", default=OWNER_EMAIL)
    p.add_argument(
        "--new-days",
        type=int,
        default=3,
        help="CreatedDate window for newly assigned Cases (default 3)",
    )
    p.add_argument(
        "--all-generic",
        action="store_true",
        help="Include every generic-subject open VM Case Crystal owns (not only new/New)",
    )
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path (in addition to stdout when --json)",
    )
    args = p.parse_args()

    owner_id = resolve_owner_id(args.org, args.owner_email)
    soql = (
        "SELECT Id, CaseNumber, Subject, Status, CreatedDate, LastModifiedDate, "
        "RecordType.Name, Account.Name, Account.Service_Provider_Number__c "
        "FROM Case "
        f"WHERE OwnerId = '{owner_id}' AND IsClosed = false "
        "AND (Subject LIKE '%New voicemail%' "
        "OR (RecordType.Name = 'Service Provider Support' "
        "AND Subject LIKE '%Vixxo Voicemail%')) "
        "ORDER BY CreatedDate DESC"
    )
    rows = sf_query(soql, args.org)
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.new_days)

    cases: list[dict] = []
    for rec in rows:
        subject = rec.get("Subject") or ""
        record_type = ((rec.get("RecordType") or {}).get("Name")) or ""
        kind = intake_kind(subject, record_type)
        if not kind:
            continue
        created = parse_sf_dt(rec.get("CreatedDate"))
        created_iso = (rec.get("CreatedDate") or "")[:10]
        is_new_status = (rec.get("Status") or "") == "New"
        newly_created = bool(created and created >= cutoff)
        if not args.all_generic and not (is_new_status or newly_created):
            continue
        account = rec.get("Account") or {}
        cases.append(
            {
                "id": rec.get("Id"),
                "case_number": str(rec.get("CaseNumber") or "").lstrip("0") or rec.get("CaseNumber"),
                "subject": subject,
                "status": rec.get("Status"),
                "record_type": record_type,
                "intake": kind,
                "created": created_iso,
                "new_status": is_new_status,
                "newly_created": newly_created,
                "account_name": account.get("Name"),
                "sp_number": account.get("Service_Provider_Number__c"),
            }
        )

    payload = {
        "ok": True,
        "owner_email": args.owner_email,
        "owner_id": owner_id,
        "new_days": args.new_days,
        "all_generic": args.all_generic,
        "generic_open": len(rows),
        "in_scope": len(cases),
        "cases": cases,
    }
    text = json.dumps(payload, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.json or args.output:
        print(text)
    else:
        print(f"{len(cases)} Crystal-owned generic voicemail Case(s) in scope")
        for row in cases:
            flags = []
            if row["new_status"]:
                flags.append("New")
            if row["newly_created"]:
                flags.append(f"created≤{args.new_days}d")
            print(
                f"  {row['case_number']}  {row['created']}  {row.get('intake')}  "
                f"{'/'.join(flags) or row['status']}  {row['subject'][:80]}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
