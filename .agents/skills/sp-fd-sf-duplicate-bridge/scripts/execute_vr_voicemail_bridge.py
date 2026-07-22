#!/usr/bin/env python3
"""Attachment sync + SF bridge Tasks for Vendor Relations voicemail FD/SF pairs."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TMP = SKILL_DIR / ".tmp"
PAIRS_JSON = TMP / "fd-sf-duplicate-scan-ap-qsiap-20260722.json"
SYNC_SCRIPT = SKILL_DIR / "scripts" / "sync_attachments_to_sf.py"
ORG = "vixxo"


def sf_cmd() -> str:
    import os
    import shutil

    npm_sf = Path(os.environ.get("APPDATA", "")) / "npm" / "sf.cmd"
    if npm_sf.is_file():
        return str(npm_sf)
    found = shutil.which("sf")
    if not found:
        raise SystemExit("sf CLI not found")
    return found


def sf_query(sf: str, soql: str) -> list[dict]:
    proc = subprocess.run(
        [sf, "data", "query", "--query", soql, "--target-org", ORG, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    data = json.loads(proc.stdout)
    return ((data.get("result") or {}).get("records") or [])


def sf_create_task(sf: str, case_id: str, fd_id: int, case_number: str, sync_summary: str) -> bool:
    desc = (
        f"VR voicemail dual-intake bridge — Freshdesk #{fd_id} ↔ SF Case #{case_number}.\\n"
        f"SF is primary (KS onboarding). FD ticket closed after triage.\\n"
        f"{sync_summary}\\n"
        f"Cross-ref: sp-fd-sf-duplicate-bridge VR cleanup 2026-07-22."
    )
    values = (
        f"Subject='FD attachment sync — Freshdesk #{fd_id}' "
        f"WhatId='{case_id}' Status='Completed' Priority='Normal' "
        f"Description='{desc}'"
    )
    proc = subprocess.run(
        [sf, "data", "create", "record", "--sobject", "Task", "--values", values, "--target-org", ORG, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"  TASK FAIL #{fd_id}: {proc.stderr[:200]}")
        return False
    return True


def run_sync(fd_id: int, case_number: str) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(SYNC_SCRIPT),
            "--fd-ticket-id",
            str(fd_id),
            "--sf-case-number",
            case_number,
            "--policy",
            "full",
            "--include-original-packet",
            "--skip-existing",
            "--target-org",
            ORG,
            "--out-dir",
            str(TMP / f"sync-vr-{fd_id}"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    report_path = TMP / f"sync-vr-{fd_id}" / "sync-report.json"
    report = {}
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip()[:300],
        "report": report,
    }


def main() -> int:
    pairs_data = json.loads(PAIRS_JSON.read_text(encoding="utf-8"))
    pairs = pairs_data.get("pairs_ap_qsiap") or []
    sf = sf_cmd()

    numbers = [p["sf_case"] for p in pairs]
    in_clause = ",".join(f"'{n}'" for n in numbers)
    case_rows = sf_query(sf, f"SELECT Id, CaseNumber, Status FROM Case WHERE CaseNumber IN ({in_clause})")
    by_number = {r["CaseNumber"]: r for r in case_rows}

    results: list[dict] = []
    for p in pairs:
        fd_id = int(p["fd_id"])
        case_number = str(p["sf_case"])
        row = by_number.get(case_number)
        if not row:
            results.append({"fd_id": fd_id, "sf_case": case_number, "error": "case_not_found"})
            print(f"SKIP #{fd_id} — SF Case {case_number} not found")
            continue

        case_id = row["Id"]
        print(f"=== FD #{fd_id} -> SF {case_number} ({row['Status']}) ===")
        sync = run_sync(fd_id, case_number)
        rep = sync.get("report") or {}
        sync_results = rep.get("results") or []
        uploaded = [r for r in sync_results if r.get("action") == "uploaded"]
        skipped = [r for r in sync_results if r.get("action") == "skipped"]
        failed = [r for r in sync_results if r.get("action") == "failed"]
        sync_summary = (
            f"Sync: {len(uploaded)} uploaded, {len(skipped)} skipped, {len(failed)} failed."
        )
        if uploaded:
            sync_summary += " Files: " + ", ".join(r.get("title", "?") for r in uploaded)
        task_ok = sf_create_task(sf, case_id, fd_id, case_number, sync_summary)
        entry = {
            "fd_id": fd_id,
            "sf_case": case_number,
            "sf_case_id": case_id,
            "sf_status": row["Status"],
            "sync": sync_summary,
            "uploaded": [r.get("title") for r in uploaded],
            "skipped": [r.get("title") for r in skipped],
            "failed": failed,
            "task_posted": task_ok,
        }
        results.append(entry)
        print(f"  {sync_summary} task={'ok' if task_ok else 'fail'}")

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "pair_count": len(pairs),
        "processed": len(results),
        "tasks_posted": sum(1 for r in results if r.get("task_posted")),
        "files_uploaded": sum(len(r.get("uploaded") or []) for r in results),
        "results": results,
    }
    out = TMP / f"vr-voicemail-bridge-run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("pair_count", "processed", "tasks_posted", "files_uploaded")}, indent=2))
    print(f"Wrote {out}")
    return 0 if all(not r.get("failed") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
