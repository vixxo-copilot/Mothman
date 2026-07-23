#!/usr/bin/env python3
"""Compact morning scan: open SF Cases with Outlook mail not yet synced.

Dry-run only. Wraps sync_case_emails.py and prints a briefing-friendly summary.

Usage
-----
    python morning_case_mail_scan.py
    python morning_case_mail_scan.py --days 7 --limit 15 --output .tmp/sf-email-sync-morning.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SYNC = SKILL_DIR / "scripts" / "sync_case_emails.py"
REPO_ROOT = SKILL_DIR.parents[2]
DEFAULT_OUT = REPO_ROOT / ".tmp" / "sf-email-sync-morning.json"

PENDING_ACTIONS = {
    "would_upload_eml",
    "would_create_email_message",
    "would_upload_attachment",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Morning dry-run scan for case email sync")
    p.add_argument("--org", default="vixxo")
    p.add_argument("--owner-email", help="Override SF case owner email")
    p.add_argument("--days", type=int, default=7, help="Mail lookback window")
    p.add_argument("--limit", type=int, default=15, help="Max open Cases to scan")
    p.add_argument("--output", type=Path, default=DEFAULT_OUT)
    p.add_argument("--from-plan", type=Path, help="Summarize an existing plan JSON without re-scanning")
    p.add_argument("--json-only", action="store_true", help="Print JSON summary only")
    return p.parse_args()


def read_json(path: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    return json.loads(text)


def summarize_case(plan: dict) -> dict | None:
    sync_results = plan.get("sync_results") or []
    pending_eml = 0
    pending_att = 0
    pending_em = 0
    already = 0
    for row in sync_results:
        actions = set(row.get("actions") or [])
        if actions & {"skip_file_exists", "would_skip_email_message_exists"}:
            already += 1
        if "would_upload_eml" in actions:
            pending_eml += 1
        if "would_create_email_message" in actions:
            pending_em += 1
        pending_att += sum(1 for a in actions if a.startswith("would_upload_attachment:"))

    if pending_eml == 0 and pending_att == 0 and pending_em == 0:
        return None

    matched = len(plan.get("matched_messages") or [])
    manual = len(plan.get("manual_review") or [])
    cn = str(plan.get("case_number") or "").lstrip("0")
    return {
        "case_number": cn,
        "case_id": plan.get("case_id"),
        "subject": (plan.get("subject") or "")[:80],
        "status": plan.get("status"),
        "matched_messages": matched,
        "pending_eml": pending_eml,
        "pending_attachments": pending_att,
        "pending_email_messages": pending_em,
        "manual_review": manual,
        "sr_numbers": (plan.get("search_keys") or {}).get("sr_numbers") or [],
        "case_url": f"https://vixxo.my.salesforce.com/{plan.get('case_id')}",
    }


def build_summary(report: dict) -> dict:
    cases = []
    for plan in report.get("cases") or []:
        entry = summarize_case(plan)
        if entry:
            cases.append(entry)
    cases.sort(key=lambda c: (-c["pending_eml"], -c["pending_attachments"], c["case_number"]))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": report.get("lookback_days"),
        "cases_scanned": report.get("cases_scanned", 0),
        "cases_needing_sync": len(cases),
        "total_pending_eml": sum(c["pending_eml"] for c in cases),
        "cases": cases,
    }


def format_markdown(summary: dict) -> str:
    if not summary["cases"]:
        return "No open Cases with new Outlook mail to sync (last {} days).".format(
            summary.get("lookback_days", 7)
        )
    lines = [
        f"**{summary['cases_needing_sync']} Case(s)** with mail to sync "
        f"({summary['total_pending_eml']} .eml pending, {summary['lookback_days']}-day lookback):",
        "",
    ]
    for c in summary["cases"]:
        sr = f" · SR {c['sr_numbers'][0]}" if c["sr_numbers"] else ""
        lines.append(
            f"- **Case {c['case_number']}**{sr} — {c['pending_eml']} eml, "
            f"{c['pending_attachments']} att · {c['subject']}"
        )
        if c["manual_review"]:
            lines.append(f"  - manual review: {c['manual_review']} low-confidence message(s)")
        lines.append(f"  - {c['case_url']}")
    lines.extend(
        [
            "",
            "Execute after review:",
            "```",
            "python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \\",
            "  --case-number {cn} --execute",
            "```".format(cn=summary["cases"][0]["case_number"]),
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    plan_path = args.from_plan or args.output

    if args.from_plan:
        if not plan_path.is_file():
            print(json.dumps({"ok": False, "error": f"Missing plan file: {plan_path}"}, indent=2))
            return 1
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(SYNC),
            "--owner-me",
            "--days",
            str(args.days),
            "--limit",
            str(args.limit),
            "--output",
            str(args.output),
            "--quiet",
        ]
        if args.org:
            cmd.extend(["--org", args.org])
        if args.owner_email:
            cmd.extend(["--owner-email", args.owner_email])

        proc = subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            err = (proc.stderr or "").strip() or f"sync_case_emails.py exited {proc.returncode}"
            print(json.dumps({"ok": False, "error": err}, indent=2))
            return proc.returncode

        if not args.output.is_file():
            print(json.dumps({"ok": False, "error": f"Missing plan file: {args.output}"}, indent=2))
            return 1
        plan_path = args.output

    report = read_json(plan_path)
    summary = build_summary(report)
    summary_path = plan_path.with_name(plan_path.stem + "-summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if args.json_only:
        print(json.dumps(summary, indent=2))
    else:
        print(format_markdown(summary))
        print("")
        print(f"Full plan: {plan_path}")
        print(f"Summary:   {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
