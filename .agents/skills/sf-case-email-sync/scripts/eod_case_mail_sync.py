#!/usr/bin/env python3
"""EOD SF Case Email Sync automation runner.

Flow each run:
  1. Dry-run batch scan of open Cases (--owner-me) for today's mail (--days 1)
  2. Execute sync for high/medium matches only (manual_review stays for operator)
  3. Write a summary report under .tmp/sf-email-sync-eod-*.json

Examples
--------
    python eod_case_mail_sync.py
    python eod_case_mail_sync.py --days 1 --limit 25
    python eod_case_mail_sync.py --dry-run-only
    python eod_case_mail_sync.py --skip-email-message
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parents[2]  # .agents/skills/<skill> → repo root
SYNC_SCRIPT = SCRIPT_DIR / "sync_case_emails.py"
OUT_DIR = REPO_ROOT / ".tmp"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="EOD dry-run → execute high/medium Case email sync → report"
    )
    p.add_argument("--org", default=os.environ.get("SF_TARGET_ORG", "vixxo"))
    p.add_argument("--days", type=int, default=1, help="Mail lookback window (default: 1)")
    p.add_argument("--limit", type=int, default=25, help="Max open Cases to scan")
    p.add_argument(
        "--owner-email",
        help="Owner email override (default: SF org username via --owner-me)",
    )
    p.add_argument(
        "--dry-run-only",
        action="store_true",
        help="Stop after dry-run plan; do not execute uploads",
    )
    p.add_argument(
        "--skip-email-message",
        action="store_true",
        help="Files-only execute (skip EmailMessage create)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=OUT_DIR,
        help="Directory for eod report JSON files",
    )
    p.add_argument("--quiet", action="store_true", help="Suppress final JSON on stdout")
    return p.parse_args()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def run_sync(
    *,
    org: str,
    days: int,
    limit: int,
    owner_email: str | None,
    execute: bool,
    skip_email_message: bool,
    output: Path,
) -> dict:
    cmd = [
        sys.executable,
        str(SYNC_SCRIPT),
        "--owner-me",
        "--status",
        "open",
        "--days",
        str(days),
        "--limit",
        str(limit),
        "--org",
        org,
        "--output",
        str(output),
        "--quiet",
    ]
    if owner_email:
        cmd.extend(["--owner-email", owner_email])
    if execute:
        cmd.append("--execute")
    if skip_email_message:
        cmd.append("--skip-email-message")

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    payload: dict = {}
    if output.is_file():
        try:
            payload = json.loads(output.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"ok": False, "error": "Invalid JSON written by sync_case_emails.py"}

    if proc.returncode != 0 and not payload:
        err = (proc.stderr or proc.stdout or "").strip()
        payload = {
            "ok": False,
            "error": err or f"sync_case_emails.py exited {proc.returncode}",
            "returncode": proc.returncode,
        }
    elif proc.returncode != 0:
        payload.setdefault("ok", False)
        payload.setdefault("returncode", proc.returncode)
        if proc.stderr.strip():
            payload.setdefault("stderr", proc.stderr.strip()[:2000])
    else:
        payload.setdefault("ok", True)
    return payload


def summarize_plan(plan: dict) -> dict:
    cases = plan.get("cases") or []
    matched = 0
    manual = 0
    high = 0
    medium = 0
    case_rows = []
    for case in cases:
        msgs = case.get("matched_messages") or []
        revs = case.get("manual_review") or []
        matched += len(msgs)
        manual += len(revs)
        for m in msgs:
            conf = (m.get("confidence") or "").lower()
            if conf == "high":
                high += 1
            elif conf == "medium":
                medium += 1
        if msgs or revs:
            case_rows.append(
                {
                    "case_number": case.get("case_number"),
                    "subject": case.get("subject"),
                    "matched": len(msgs),
                    "manual_review": len(revs),
                    "status": case.get("status"),
                }
            )
    return {
        "cases_scanned": plan.get("cases_scanned", len(cases)),
        "cases_with_hits": len(case_rows),
        "matched_high_medium": matched,
        "matched_high": high,
        "matched_medium": medium,
        "manual_review_skipped": manual,
        "case_hits": case_rows,
        "plan_summary": plan.get("summary") or {},
    }


def summarize_execute(exec_report: dict) -> dict:
    summary = exec_report.get("summary") or {}
    errors = []
    synced_cases = []
    for case in exec_report.get("cases") or []:
        results = case.get("sync_results") or []
        case_errors = []
        actions = []
        for r in results:
            actions.extend(r.get("actions") or [])
            case_errors.extend(r.get("errors") or [])
        if results:
            synced_cases.append(
                {
                    "case_number": case.get("case_number"),
                    "subject": case.get("subject"),
                    "messages": len(results),
                    "actions": actions,
                    "errors": case_errors,
                }
            )
        errors.extend(case_errors)
    return {
        "matched_messages": summary.get("matched_messages", 0),
        "synced": summary.get("synced", 0),
        "errors": summary.get("errors", 0),
        "error_details": errors[:50],
        "synced_cases": synced_cases,
    }


def prerun_checks() -> list[str]:
    """Return human-readable blockers (empty if ready)."""
    blockers: list[str] = []
    # Salesforce CLI + authenticated target org
    from sf_helpers import sf_path  # local import — same skill helpers

    sf = sf_path()
    org = os.environ.get("SF_TARGET_ORG", "vixxo")
    try:
        proc = subprocess.run(
            [sf, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            blockers.append(
                f"Salesforce CLI not usable at '{sf}'. Install @salesforce/cli and "
                f"authenticate: sf org login web --alias {org}"
            )
        else:
            disp = subprocess.run(
                [sf, "org", "display", "--target-org", org, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            if disp.returncode != 0:
                blockers.append(
                    f"Salesforce org '{org}' not authenticated in this runtime. "
                    f"Run: sf org login web --alias {org}"
                )
    except FileNotFoundError:
        blockers.append(
            "Salesforce CLI (`sf`) not found on PATH. Install @salesforce/cli and "
            f"authenticate: sf org login web --alias {org}"
        )

    # M365 Graph token (same cache as outlook_mail.mjs)
    outlook = SCRIPT_DIR / "outlook_mail.mjs"
    try:
        proc = subprocess.run(
            ["node", str(outlook), "whoami"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0 or "No valid token" in (proc.stdout + proc.stderr):
            blockers.append(
                "Microsoft 365 Graph token missing/invalid. Sign in via the "
                "microsoft-365 MCP (device-code) so outlook_mail.mjs can reuse the cache."
            )
    except FileNotFoundError:
        blockers.append("Node.js not found — required for outlook_mail.mjs Graph access")

    return blockers


def main() -> int:
    args = parse_args()
    run_id = stamp()
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    plan_path = out_dir / f"sf-email-sync-eod-{run_id}-plan.json"
    exec_path = out_dir / f"sf-email-sync-eod-{run_id}-execute.json"
    report_path = out_dir / f"sf-email-sync-eod-{run_id}.json"

    report: dict = {
        "ok": False,
        "automation": "EOD SF Case Email Sync",
        "mode": "dry-run-only" if args.dry_run_only else "dry-run-then-execute",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timezone_note": "Cron 0 21 * * * = 16:00 America/Chicago (CDT/CST)",
        "scope": {
            "owner": "me",
            "status": "open",
            "days": args.days,
            "limit": args.limit,
            "org": args.org,
            "owner_email": args.owner_email,
        },
        "paths": {
            "plan": str(plan_path),
            "execute": str(exec_path) if not args.dry_run_only else None,
            "report": str(report_path),
        },
        "blockers": [],
        "dry_run": None,
        "execute": None,
        "operator_summary": {},
    }

    blockers = prerun_checks()
    report["blockers"] = blockers
    if blockers:
        report["operator_summary"] = {
            "verdict": "blocked",
            "message": (
                "Cloud/local runtime missing Salesforce CLI and/or M365 Graph auth. "
                "Run locally with cached tokens, or wire dashboard MCPs for SF/M365."
            ),
            "cases_scanned": 0,
            "matched_high_medium": 0,
            "manual_review_skipped": 0,
            "synced": 0,
            "errors": 0,
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if not args.quiet:
            print(json.dumps(report, indent=2))
        return 2

    plan = run_sync(
        org=args.org,
        days=args.days,
        limit=args.limit,
        owner_email=args.owner_email,
        execute=False,
        skip_email_message=False,
        output=plan_path,
    )
    report["dry_run"] = {
        "path": str(plan_path),
        "ok": bool(plan.get("ok", True)) and "error" not in plan,
        "plan_stats": summarize_plan(plan) if "cases" in plan else {},
        "error": plan.get("error"),
    }

    if plan.get("error") or plan.get("ok") is False:
        report["operator_summary"] = {
            "verdict": "dry_run_failed",
            "message": plan.get("error") or "Dry-run failed",
            "cases_scanned": 0,
            "matched_high_medium": 0,
            "manual_review_skipped": 0,
            "synced": 0,
            "errors": 1,
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if not args.quiet:
            print(json.dumps(report, indent=2))
        return 1

    stats = report["dry_run"]["plan_stats"]
    matched = int(stats.get("matched_high_medium") or 0)

    if args.dry_run_only or matched == 0:
        report["ok"] = True
        report["execute"] = {
            "skipped": True,
            "reason": "dry-run-only" if args.dry_run_only else "no high/medium matches",
        }
        report["operator_summary"] = {
            "verdict": "ok_no_execute" if matched == 0 else "ok_dry_run_only",
            "message": (
                "Dry-run complete; no high/medium matches to sync."
                if matched == 0
                else "Dry-run-only mode; execute skipped by flag."
            ),
            "cases_scanned": stats.get("cases_scanned", 0),
            "matched_high_medium": matched,
            "manual_review_skipped": stats.get("manual_review_skipped", 0),
            "synced": 0,
            "errors": 0,
            "case_hits": stats.get("case_hits") or [],
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if not args.quiet:
            print(json.dumps(report, indent=2))
        return 0

    exec_report = run_sync(
        org=args.org,
        days=args.days,
        limit=args.limit,
        owner_email=args.owner_email,
        execute=True,
        skip_email_message=args.skip_email_message,
        output=exec_path,
    )
    exec_stats = summarize_execute(exec_report) if "cases" in exec_report else {}
    report["execute"] = {
        "path": str(exec_path),
        "ok": bool(exec_report.get("ok", True)) and "error" not in exec_report,
        "stats": exec_stats,
        "error": exec_report.get("error"),
    }
    report["ok"] = bool(report["execute"]["ok"])
    report["operator_summary"] = {
        "verdict": "ok" if report["ok"] else "execute_failed",
        "message": (
            f"Executed high/medium syncs; skipped {stats.get('manual_review_skipped', 0)} "
            "manual_review message(s)."
        ),
        "cases_scanned": stats.get("cases_scanned", 0),
        "matched_high_medium": matched,
        "manual_review_skipped": stats.get("manual_review_skipped", 0),
        "synced": exec_stats.get("synced", 0),
        "errors": exec_stats.get("errors", 0),
        "case_hits": stats.get("case_hits") or [],
        "synced_cases": exec_stats.get("synced_cases") or [],
    }

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not args.quiet:
        print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
