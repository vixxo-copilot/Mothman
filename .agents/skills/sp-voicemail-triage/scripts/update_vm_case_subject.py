#!/usr/bin/env python3
"""Rewrite a Salesforce voicemail Case Subject to SP name + request.

Canonical form:

    Voicemail — {SP Name} ({SP#}) — {request}

Omit ({SP#}) when unknown. Strip apostrophes for `sf --values`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

SF = os.path.expandvars(r"%APPDATA%\npm\sf.cmd")
ORG_DEFAULT = "vixxo"


def clean(s: str) -> str:
    return (s or "").replace("'", "").replace("\r", " ").replace("\n", " ").strip()


def format_vm_subject(sp_name: str, request: str, sp_number: str | None = None) -> str:
    name = clean(sp_name) or "Unknown"
    ask = clean(request) or "callback requested"
    number = clean(sp_number or "")
    if number:
        return f"Voicemail — {name} ({number}) — {ask}"
    return f"Voicemail — {name} — {ask}"


def update_case(case_id: str, subject: str, org: str) -> dict:
    proc = subprocess.run(
        [
            SF,
            "data",
            "update",
            "record",
            "--sobject",
            "Case",
            "--record-id",
            case_id,
            "--target-org",
            org,
            "--json",
            "--values",
            f"Subject='{clean(subject)}'",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        data = {"raw": proc.stdout, "stderr": proc.stderr}
    success = proc.returncode == 0 and data.get("name") != "ERROR"
    result = data.get("result")
    if isinstance(result, dict) and result.get("success") is False:
        success = False
    return {"ok": success, "code": proc.returncode, "subject": subject, "data": data}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--org", default=ORG_DEFAULT)
    p.add_argument("--case-id", required=True)
    p.add_argument("--sp-name", required=True, help="Vetted SP / company name")
    p.add_argument("--request", required=True, help="Plain-English ask / sub-reason")
    p.add_argument("--sp-number", default="", help="KS / Siebel SP number when known")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    subject = format_vm_subject(args.sp_name, args.request, args.sp_number)
    if args.dry_run:
        payload = {"ok": True, "dry_run": True, "case_id": args.case_id, "subject": subject}
        print(json.dumps(payload, indent=2) if args.json else f"DRY {args.case_id} -> {subject}")
        return 0

    res = update_case(args.case_id, subject, args.org)
    res["case_id"] = args.case_id
    if args.json:
        print(json.dumps(res, indent=2, default=str))
    elif res["ok"]:
        print(f"OK {args.case_id} -> {subject}")
    else:
        print(f"FAIL {args.case_id}: {json.dumps(res.get('data'))[:400]}", file=sys.stderr)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
