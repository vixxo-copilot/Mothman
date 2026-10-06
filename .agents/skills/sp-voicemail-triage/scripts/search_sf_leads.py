#!/usr/bin/env python3
"""Search Salesforce Leads for voicemail triage — include Closed and converted.

Does not filter Status or IsConverted. Matches Phone, MobilePhone, Company,
and Name. Use after STT (and after a web identity lookup when the caller is
first-name-only).

  python .agents/skills/sp-voicemail-triage/scripts/search_sf_leads.py \\
    --phone 7162093703 --company Turnkey --name "Tom" --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
HELPERS = SCRIPT_DIR.parents[1] / "sf-case-email-sync" / "scripts"
sys.path.insert(0, str(HELPERS))

from sf_helpers import sf_query  # noqa: E402

LEAD_FIELDS = (
    "Id, Name, FirstName, LastName, Company, Status, IsConverted, "
    "ConvertedAccountId, Phone, MobilePhone, Email, LastModifiedDate"
)


def last10(raw: str | None) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else digits


def soql_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _norm_company(value: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", value or "", flags=re.I)
    cleaned = re.sub(
        r"\b(llc|inc|incorporated|ltd|co|company|corp|corporation)\b",
        " ",
        cleaned,
        flags=re.I,
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def _row(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": rec.get("Id"),
        "name": rec.get("Name"),
        "first_name": rec.get("FirstName"),
        "last_name": rec.get("LastName"),
        "company": rec.get("Company"),
        "status": rec.get("Status"),
        "is_converted": bool(rec.get("IsConverted")),
        "converted_account_id": rec.get("ConvertedAccountId"),
        "phone": rec.get("Phone"),
        "mobile_phone": rec.get("MobilePhone"),
        "email": rec.get("Email"),
        "last_modified": rec.get("LastModifiedDate"),
        "closed_or_converted": (rec.get("Status") or "").lower() == "closed"
        or bool(rec.get("IsConverted")),
    }


def search_leads(
    *,
    phone: str = "",
    company: str = "",
    name: str = "",
    org: str = "vixxo",
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    digits = last10(phone)
    if digits and len(digits) >= 7:
        clauses.append(f"Phone LIKE '%{digits}%'")
        clauses.append(f"MobilePhone LIKE '%{digits}%'")
    company_q = _norm_company(company)
    if len(company_q) >= 3:
        like = soql_escape(company_q.split()[0] if company_q else "")
        if like:
            clauses.append(f"Company LIKE '%{like}%'")
    name_q = (name or "").strip()
    if name_q and " " in name_q:
        last = soql_escape(name_q.split()[-1])
        if len(last) >= 3:
            clauses.append(f"LastName LIKE '%{last}%'")
            clauses.append(f"Name LIKE '%{soql_escape(name_q)}%'")
    elif name_q and len(name_q) >= 3 and company_q:
        # First-name-only: require company in the same query via AND later
        pass

    if not clauses:
        return []

    soql = (
        f"SELECT {LEAD_FIELDS} FROM Lead WHERE "
        + " OR ".join(clauses)
        + " ORDER BY LastModifiedDate DESC LIMIT 25"
    )
    seen: dict[str, dict[str, Any]] = {}
    for rec in sf_query(soql, org=org):
        rid = rec.get("Id")
        if rid:
            seen[rid] = _row(rec)

    first = name_q.lower() if name_q and " " not in name_q else ""
    if first and len(first) >= 2:
        for row in seen.values():
            fn = (row.get("first_name") or "").lower()
            full = (row.get("name") or "").lower()
            if first in fn or full.startswith(first) or fn.startswith(first):
                row["first_name_company_hit"] = True

    def _rank(row: dict[str, Any]) -> tuple[int, str]:
        score = 0
        if row.get("first_name_company_hit"):
            score -= 20
        if company_q and company_q.lower().split()[0] in (row.get("company") or "").lower():
            score -= 10
        if (row.get("status") or "").lower() != "closed":
            score -= 1
        return (score, row.get("last_modified") or "")

    return sorted(seen.values(), key=_rank)


def main() -> int:
    p = argparse.ArgumentParser(description="Search all SF Leads (incl. Closed)")
    p.add_argument("--phone", default="")
    p.add_argument("--company", default="")
    p.add_argument("--name", default="")
    p.add_argument("--org", default="vixxo")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rows = search_leads(
        phone=args.phone, company=args.company, name=args.name, org=args.org
    )
    payload = {
        "ok": True,
        "count": len(rows),
        "includes_closed_and_converted": True,
        "leads": rows,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{len(rows)} Lead(s) (Closed/converted included)")
        for row in rows:
            flags = []
            if (row.get("status") or "").lower() == "closed":
                flags.append("Closed")
            if row.get("is_converted"):
                flags.append("Converted")
            extra = f" [{', '.join(flags)}]" if flags else ""
            print(
                f"  {row['id']}  {row['name']}  {row['company']}  "
                f"{row['status']}  {row.get('phone') or '—'}{extra}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
