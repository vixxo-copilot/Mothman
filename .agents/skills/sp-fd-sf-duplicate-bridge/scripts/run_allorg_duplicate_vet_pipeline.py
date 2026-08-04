#!/usr/bin/env python3
"""Export SF cases, unified triage + duplicate scan + shell vet + HTML report.

Single efficient pass:
  1. Seed duplicate clusters from Case metadata
  2. Full EmailMessage + attachment intake for shell cases + duplicate members
  3. Re-cluster duplicates using body/attachment context clues
  4. sp-inbound-vetting identity resolution on shell cases
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
TMP = SKILL_ROOT / ".tmp"
DATE = os.environ.get("RUN_DATE", datetime.now(timezone.utc).strftime("%Y%m%d"))
SF = os.path.expandvars(r"%APPDATA%\npm\sf.cmd")
ORG = "vixxo"

SF_CACHE = TMP / f"sf-cases-window-allorg-{DATE}.json"
SCAN_JSON = TMP / f"sf-intra-duplicate-scan-allorg-{DATE}.json"
SCAN_MD = TMP / f"sf-intra-duplicate-report-allorg-{DATE}.md"
VET_JSON = TMP / f"shell-account-vet-allorg-{DATE}.json"
VET_MD = TMP / f"shell-account-vet-report-allorg-{DATE}.md"
VETTED_JSON = TMP / f"sf-intra-duplicate-scan-allorg-vetted-{DATE}.json"
VETTED_MD = TMP / f"sf-intra-duplicate-report-allorg-vetted-{DATE}.md"
VETTED_HTML = TMP / f"sf-intra-duplicate-scan-allorg-vetted-{DATE}.html"

SOQL = (
    "SELECT Id, CaseNumber, Subject, Status, Description, ContactEmail, SuppliedEmail, "
    "CreatedDate, Account.Name, Owner.Username, Owner.Name, RecordType.Name "
    "FROM Case WHERE CreatedDate >= 2026-06-26T00:00:00Z ORDER BY CreatedDate ASC"
)


def sf_query_json() -> dict:
    proc = subprocess.run(
        [SF, "data", "query", "--query", SOQL, "--target-org", ORG, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"sf query failed: {proc.stderr or proc.stdout}")
    data = json.loads(proc.stdout)
    result = data.get("result") or data
    records = result.get("records") or []
    # Normalize relationship fields to nested dicts expected by scanners
    for r in records:
        if "Account" not in r and r.get("Account.Name") is not None:
            r["Account"] = {"Name": r.pop("Account.Name", None)}
        if "Owner" not in r and (r.get("Owner.Username") or r.get("Owner.Name")):
            r["Owner"] = {
                "Username": r.pop("Owner.Username", None),
                "Name": r.pop("Owner.Name", None),
            }
        if "RecordType" not in r and r.get("RecordType.Name") is not None:
            r["RecordType"] = {"Name": r.pop("RecordType.Name", None)}
    return {
        "records": records,
        "totalSize": result.get("totalSize", len(records)),
        "done": result.get("done", True),
    }


def export_sf_cache() -> None:
    print(f"Exporting SF cases ({SOQL[:60]}...)", flush=True)
    payload = sf_query_json()
    SF_CACHE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {payload['totalSize']} cases -> {SF_CACHE}", flush=True)


def main() -> int:
    print(f"=== SF duplicate review & vetting (all org) — {DATE} ===", flush=True)
    export_sf_cache()
    env = os.environ.copy()
    env.update(
        {
            "RUN_DATE": DATE,
            "SF_CACHE_PATH": str(SF_CACHE),
            "SCAN_JSON_PATH": str(SCAN_JSON),
            "PRIOR_SCAN_PATH": str(SCAN_JSON),
            "VET_JSON_PATH": str(VET_JSON),
            "VET_MD_PATH": str(VET_MD),
            "VETTED_JSON_PATH": str(VETTED_JSON),
            "VETTED_MD_PATH": str(VETTED_MD),
            "VETTED_HTML_PATH": str(VETTED_HTML),
            "SCAN_SCOPE": "CreatedDate >= 2026-06-26 (all org)",
        }
    )
    print("Phase: unified triage + duplicate scan + shell vet + report", flush=True)
    subprocess.run(
        [sys.executable, str(SCRIPTS / "vet_shell_accounts_allorg.py")],
        check=True,
        env=env,
    )
    print(f"DONE HTML: {VETTED_HTML.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
