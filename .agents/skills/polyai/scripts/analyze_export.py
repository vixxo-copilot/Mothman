#!/usr/bin/env python3
"""Analyze a PolyAI CSV export — hang-ups, funnel, phone/time breakdowns."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import polyai_client  # noqa: E402

KNOWN_PHONES = {
    "+18887744950": "Tech24",
    "+12033334112": "Liberty Auto & Electric",
    "+18004233872": "The ICEE Company",
    "+17082331472": "ABS & Taylor Enterprises",
    "+18603493921": "L & I Refrigeration",
}


def default_csv_path(project: str | None = None) -> Path:
    from polyai_projects import config_for_project, export_csv_path

    polyai_client.load_dotenv()
    cfg = config_for_project(project)
    return export_csv_path(cfg["POLYAI_PROJECT_ID"])


def load_all_exports(outbound_only: bool) -> list[dict]:
    root = polyai_client.repo_root() / "exports" / "polyai"
    rows: list[dict] = []
    for path in sorted(root.glob("*-conversations.csv")):
        rows.extend(load_rows(path, outbound_only=False))
    if outbound_only:
        rows = [row for row in rows if row.get("direction") == "outbound"]
    return rows


def load_rows(path: Path, outbound_only: bool) -> list[dict]:
    if not path.is_file():
        raise SystemExit(
            f"Export not found: {path}\n"
            "Run: python3 .agents/skills/polyai/scripts/export_conversations.py"
        )
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if outbound_only:
        rows = [row for row in rows if row.get("direction") == "outbound"]
    return rows


def has_flag(row: dict, key: str) -> bool:
    return row.get(f"has_{key}") == "Y"


def human_answered(row: dict) -> bool:
    if has_flag(row, "HUMAN_ENCOUNTERED"):
        return True
    return "HUMAN" in (row.get("metric_CALL_ANSWERED_BY") or "")


def human_hangup(row: dict) -> bool:
    return has_flag(row, "USER_HANGUP") and human_answered(row)


def voicemail_only(row: dict) -> bool:
    answered = row.get("metric_CALL_ANSWERED_BY") or ""
    return "VOICEMAIL" in answered and not human_answered(row)


def local_hour(row: dict, tz_name: str) -> int:
    started = row.get("started_at") or ""
    if not started:
        return -1
    dt = datetime.fromisoformat(started).replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo(tz_name)).hour


def phone_label(phone: str) -> str:
    return KNOWN_PHONES.get(phone, phone)


def cmd_summary(rows: list[dict]) -> None:
    total = len(rows)
    connected = sum(1 for row in rows if float(row.get("duration_sec") or 0) > 0)
    human = sum(1 for row in rows if human_answered(row))
    eta_start = sum(1 for row in rows if has_flag(row, "UPDATE_ETA_START"))
    eta_ok = sum(1 for row in rows if has_flag(row, "UPDATE_ETA_SUCCESSFUL"))
    api_ok = sum(1 for row in rows if has_flag(row, "API_OK"))
    vm = sum(1 for row in rows if voicemail_only(row))
    user_hang = sum(1 for row in rows if human_hangup(row))
    out_of_scope = sum(1 for row in rows if has_flag(row, "OUT_OF_SCOPE_SR"))

    print("## PolyAI export summary\n")
    print(f"Rows: {total}")
    if rows:
        dates = [row.get("started_date") for row in rows if row.get("started_date")]
        print(f"Date range: {min(dates)} → {max(dates)}")
        project_ids = {row.get("project_id") for row in rows if row.get("project_id")}
        if len(project_ids) > 1:
            print("\n### By project")
            for project_id in sorted(project_ids):
                subset = [row for row in rows if row.get("project_id") == project_id]
                print(f"- {project_id}: {len(subset)} rows")
    print()
    print("| Stage | Count | Rate |")
    print("| --- | ---: | ---: |")
    for label, count in [
        ("Dialed", total),
        ("Connected (>0s)", connected),
        ("Human reached", human),
        ("Voicemail only", vm),
        ("Human hang-up (USER_HANGUP)", user_hang),
        ("ETA collection started", eta_start),
        ("API_OK", api_ok),
        ("Out of scope SR", out_of_scope),
        ("ETA posted", eta_ok),
    ]:
        rate = 100 * count / total if total else 0
        print(f"| {label} | {count} | {rate:.1f}% |")

    print("\n### Hangup categories")
    for category, count in Counter(row.get("hangup_category") or "" for row in rows).most_common(10):
        print(f"- {category}: {count} ({100 * count / total:.1f}%)")


def cmd_hangups(rows: list[dict]) -> None:
    total = len(rows)
    buckets = Counter(row.get("hangup_category") or "(empty)" for row in rows)
    print("## Hang-up / outcome categories\n")
    for category, count in buckets.most_common():
        print(f"- **{category}**: {count} ({100 * count / total:.1f}%)")


def cmd_fixable(rows: list[dict]) -> None:
    total = len(rows)
    intro_30 = sum(
        1
        for row in rows
        if human_answered(row)
        and float(row.get("duration_sec") or 0) <= 30
        and not has_flag(row, "UPDATE_ETA_START")
    )
    intro_45 = sum(
        1
        for row in rows
        if human_answered(row)
        and float(row.get("duration_sec") or 0) <= 45
        and not has_flag(row, "UPDATE_ETA_START")
        and not voicemail_only(row)
    )
    confirmed_not_posted = sum(
        1
        for row in rows
        if has_flag(row, "UPDATE_ETA_DETAILS_CONFIRMED")
        and not has_flag(row, "UPDATE_ETA_SUCCESSFUL")
    )
    started_not_posted = sum(
        1
        for row in rows
        if has_flag(row, "UPDATE_ETA_START")
        and not has_flag(row, "UPDATE_ETA_SUCCESSFUL")
    )
    vm = sum(1 for row in rows if voicemail_only(row))

    print("## Fixable buckets (from export)\n")
    print("| Bucket | Count | % | Fix |")
    print("| --- | ---: | ---: | --- |")
    print(f"| Intro hang-up ≤30s (human, no ETA flow) | {intro_30} | {100*intro_30/total:.1f}% | Tighten intro / ASR |")
    print(f"| Intro hang-up ≤45s (human, no VM) | {intro_45} | {100*intro_45/total:.1f}% | Script + silence handling |")
    print(f"| ETA confirmed, not posted (`UPDATE_ETA_DETAILS_CONFIRMED`) | {confirmed_not_posted} | {100*confirmed_not_posted/total:.1f}% | Integration write path |")
    print(f"| ETA started, not posted | {started_not_posted} | {100*started_not_posted/total:.1f}% | Mix of human drop + backend |")
    print(f"| Voicemail only | {vm} | {100*vm/total:.1f}% | Track VM → redial → ETA funnel |")


def cmd_recent(rows: list[dict], limit: int) -> None:
    ordered = sorted(rows, key=lambda row: row.get("started_at") or "", reverse=True)
    print(f"## Most recent {limit} call(s)\n")
    for row in ordered[:limit]:
        print(f"- **{row.get('conversation_id')}**")
        print(f"  - Started: {row.get('started_at')}")
        print(f"  - To: {phone_label(row.get('to_number') or '')}")
        print(f"  - Duration: {row.get('duration_sec')}s | Category: {row.get('hangup_category')}")
        print(f"  - ETA posted: {'yes' if has_flag(row, 'UPDATE_ETA_SUCCESSFUL') else 'no'}")


def cmd_top_phones(rows: list[dict], metric: str, limit: int) -> None:
    counts: Counter[str] = Counter()
    for row in rows:
        phone = row.get("to_number") or "(unknown)"
        if metric == "hangups":
            if human_hangup(row):
                counts[phone] += 1
        else:
            counts[phone] += 1

    title = "human hang-ups" if metric == "hangups" else "outbound calls"
    print(f"## Top {limit} numbers by {title}\n")
    print("| Phone | Provider hint | Count |")
    print("| --- | --- | ---: |")
    for phone, count in counts.most_common(limit):
        print(f"| {phone} | {KNOWN_PHONES.get(phone, '—')} | {count} |")


def cmd_phone(rows: list[dict], phone: str, tz_name: str) -> None:
    if not phone.startswith("+"):
        phone = f"+{phone}"
    subset = [row for row in rows if row.get("to_number") == phone]
    if not subset:
        raise SystemExit(f"No rows for {phone}")

    label = phone_label(phone)
    hangups = [row for row in subset if human_hangup(row)]
    print(f"## {label} ({phone})\n")
    print(f"Outbound calls: {len(subset)}")
    print(f"Human hang-ups: {len(hangups)}")
    if subset:
        dates = [row.get("started_date") for row in subset if row.get("started_date")]
        print(f"Date range: {min(dates)} → {max(dates)}")
    print()

    by_hour = Counter(local_hour(row, tz_name) for row in hangups)
    by_hour_all = Counter(local_hour(row, tz_name) for row in subset)
    print(f"### By hour ({tz_name})\n")
    print("| Hour | Hang-ups | Calls | Rate |")
    print("| --- | ---: | ---: | ---: |")
    for hour in range(24):
        if by_hour[hour] or by_hour_all[hour]:
            h12 = hour % 12 or 12
            ampm = "AM" if hour < 12 else "PM"
            calls = by_hour_all[hour]
            hangs = by_hour[hour]
            rate = 100 * hangs / calls if calls else 0
            print(f"| {h12}:00 {ampm} | {hangs} | {calls} | {rate:.0f}% |")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze PolyAI CSV export")
    parser.add_argument("--csv", type=Path, default=None, help="Path to export CSV")
    parser.add_argument("--project", help="Project id — resolves default CSV path")
    parser.add_argument(
        "--all-projects",
        action="store_true",
        help="Load and merge every exports/polyai/*-conversations.csv",
    )
    parser.add_argument("--inbound", action="store_true", help="Include inbound (default: outbound only)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", help="Funnel + category breakdown")
    sub.add_parser("hangups", help="Outcome category counts")
    sub.add_parser("fixable-buckets", help="Three fixable bucket sizes")

    recent = sub.add_parser("recent", help="Most recent calls")
    recent.add_argument("--limit", type=int, default=5)

    top = sub.add_parser("top-phones", help="Top destination numbers")
    top.add_argument("--metric", choices=["calls", "hangups"], default="hangups")
    top.add_argument("--limit", type=int, default=15)

    phone = sub.add_parser("phone", help="Deep dive one destination number")
    phone.add_argument("number", help="E.164 phone, e.g. +18004233872")
    phone.add_argument("--timezone", default="America/Chicago")

    args = parser.parse_args()
    if args.all_projects:
        rows = load_all_exports(outbound_only=not args.inbound)
    else:
        csv_path = args.csv or default_csv_path(args.project)
        rows = load_rows(csv_path, outbound_only=not args.inbound)

    if args.command == "summary":
        cmd_summary(rows)
    elif args.command == "hangups":
        cmd_hangups(rows)
    elif args.command == "fixable-buckets":
        cmd_fixable(rows)
    elif args.command == "recent":
        cmd_recent(rows, args.limit)
    elif args.command == "top-phones":
        cmd_top_phones(rows, args.metric, args.limit)
    elif args.command == "phone":
        cmd_phone(rows, args.number, args.timezone)
    else:
        raise SystemExit(f"Unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
