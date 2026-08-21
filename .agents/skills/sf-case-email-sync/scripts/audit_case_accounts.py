#!/usr/bin/env python3
"""Audit-only Case Account preflight using sp-inbound-vetting identity resolution.

Examples
--------
    python audit_case_accounts.py --owner-me --limit 25
    python audit_case_accounts.py --case-number 6911
    python audit_case_accounts.py --owner-me --output .tmp/sf-account-audit.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from account_audit import audit_case, format_markdown, summarize_audits  # noqa: E402
from sf_helpers import resolve_user_id, sf_query  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
DEFAULT_OUT = REPO_ROOT / ".tmp" / "sf-account-audit.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit SF Case Account linkage (no writes)")
    p.add_argument("--org", default=os.environ.get("SF_TARGET_ORG", "vixxo"))
    p.add_argument("--owner-me", action="store_true")
    p.add_argument("--owner-email")
    p.add_argument("--case-id")
    p.add_argument("--case-number")
    p.add_argument("--status", default="open", choices=["open", "all"])
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--output", type=Path, default=DEFAULT_OUT)
    p.add_argument("--json-only", action="store_true")
    p.add_argument("--skip-gateway-check", action="store_true")
    return p.parse_args()


def fetch_cases(
    org: str,
    *,
    owner_id: str | None,
    case_id: str | None,
    case_number: str | None,
    status: str,
    limit: int,
) -> list[dict]:
    fields = (
        "Id, CaseNumber, Subject, Description, Status, ContactEmail, SuppliedEmail, "
        "AccountId, Account.Name, Account.Service_Provider_Number__c, Account.Type, "
        "LastModifiedDate"
    )
    if case_id:
        soql = f"SELECT {fields} FROM Case WHERE Id = '{case_id}' LIMIT 1"
    elif case_number:
        num = case_number.lstrip("0")
        soql = (
            f"SELECT {fields} FROM Case WHERE CaseNumber = '{num}' "
            f"OR CaseNumber = '{case_number.zfill(8)}' LIMIT 1"
        )
    else:
        if not owner_id:
            raise RuntimeError("--owner-me required for batch audit")
        status_clause = " AND IsClosed = false" if status == "open" else ""
        soql = (
            f"SELECT {fields} FROM Case WHERE OwnerId = '{owner_id}'{status_clause} "
            f"ORDER BY LastModifiedDate DESC LIMIT {limit}"
        )
    return sf_query(soql, org=org)


def main() -> int:
    args = parse_args()
    owner_id = None
    if args.owner_me or (not args.case_id and not args.case_number):
        owner_id = resolve_user_id(args.org, args.owner_email)

    if not args.skip_gateway_check:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sp-inbound-vetting" / "scripts"))
        from gateway_vetting import gateway_health_check  # noqa: WPS433

        health = gateway_health_check()
        if not health.get("ok"):
            print(
                "Warning: Gateway bearer probe failed — run "
                "python .cursor/bin/sync_gateway_token.py then restart gateway MCP. "
                "Audit continues with Salesforce-only signals.",
                file=sys.stderr,
            )

    cases = fetch_cases(
        args.org,
        owner_id=owner_id,
        case_id=args.case_id,
        case_number=args.case_number,
        status=args.status,
        limit=args.limit,
    )
    if not cases:
        print(json.dumps({"ok": False, "error": "No cases found"}, indent=2))
        return 1

    query_fn = lambda soql: sf_query(soql, org=args.org)  # noqa: E731
    audits = [audit_case(case, query_fn) for case in cases]
    summary = summarize_audits(audits)
    report = {
        "mode": "audit-only",
        "org": args.org,
        "cases_audited": len(audits),
        "summary": summary,
        "cases": audits,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.json_only:
        print(json.dumps(summary, indent=2))
    else:
        print(format_markdown(summary))
        print("")
        print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
