#!/usr/bin/env python3
"""Export Crystal's open Salesforce Tasks overview (read-only).

Used by mothman-good-morning Phase 2 cascade:

  python .agents/skills/mothman-good-morning/scripts/export_sf_task_overview.py --json

Outputs:
  .tmp/mothman-good-morning/Crystal-SF-Tasks-YYYY-MM-DD.json
  .tmp/mothman-good-morning/Crystal-SF-Tasks-YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[2]
HELPERS = SKILL_ROOT.parent / "sf-case-email-sync" / "scripts"
sys.path.insert(0, str(HELPERS))

from sf_helpers import resolve_user_id, sf_query  # noqa: E402


def _chicago_tz():
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("America/Chicago")
    except Exception:
        return timezone(timedelta(hours=-5), name="America/Chicago")


TZ = _chicago_tz()
DEFAULT_OWNER_EMAIL = "Crystal.Gagner@vixxo.com"
OUTPUT_DIR = REPO_ROOT / ".tmp" / "mothman-good-morning"
LIGHTNING_TASK = "https://vixxo.lightning.force.com/lightning/r/Task"
LIGHTNING_CASE = "https://vixxo.lightning.force.com/lightning/r/Case"

# Bucket open Tasks by subject prefix / keyword for a scannable overview
BUCKET_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Voicemail / 4046", re.compile(r"voicemail|4046|vendor relations", re.I)),
    ("COI / insurance", re.compile(r"\bcoi\b|certificate|insurance|federated", re.I)),
    ("Rate / negotiation", re.compile(r"rate|negotiation|rbat|ror", re.I)),
    ("Duplicate / merge", re.compile(r"duplicate|merge|dupe", re.I)),
    ("Onboarding / vetting", re.compile(r"onboard|vetting|inbound", re.I)),
    ("Follow-up / callback", re.compile(r"follow[- ]?up|callback|call back", re.I)),
    ("AP / payment", re.compile(r"\bap\b|payment|invoice|remit", re.I)),
]


def _parse_date(val: Any) -> date | None:
    if not val:
        return None
    s = str(val)[:10]
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _bucket(subject: str) -> str:
    for label, pat in BUCKET_RULES:
        if pat.search(subject or ""):
            return label
    return "Other"


def fetch_open_tasks(owner_id: str, org: str) -> list[dict]:
    soql = (
        "SELECT Id, Subject, Status, Priority, ActivityDate, CreatedDate, "
        "LastModifiedDate, WhatId, What.Type, What.Name, "
        "Description "
        f"FROM Task WHERE OwnerId = '{owner_id}' AND IsClosed = false "
        "ORDER BY ActivityDate ASC NULLS LAST, CreatedDate ASC"
    )
    return sf_query(soql, org=org)


def build_overview(tasks: list[dict], as_of: date) -> dict[str, Any]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    overdue: list[dict] = []
    due_today: list[dict] = []
    no_due: list[dict] = []
    by_what: Counter[str] = Counter()

    rows: list[dict] = []
    for t in tasks:
        subj = (t.get("Subject") or "").strip() or "(no subject)"
        due = _parse_date(t.get("ActivityDate"))
        what = t.get("What") or {}
        what_type = what.get("Type") or (
            "Case" if str(t.get("WhatId") or "").startswith("500") else ""
        )
        what_name = what.get("Name") or ""
        bucket = _bucket(subj)
        row = {
            "id": t.get("Id"),
            "subject": subj,
            "status": t.get("Status"),
            "priority": t.get("Priority"),
            "activity_date": str(due) if due else None,
            "created_date": str(t.get("CreatedDate") or "")[:10] or None,
            "what_id": t.get("WhatId"),
            "what_type": what_type,
            "what_name": what_name,
            "bucket": bucket,
            "url": f"{LIGHTNING_TASK}/{t.get('Id')}/view" if t.get("Id") else None,
            "case_url": (
                f"{LIGHTNING_CASE}/{t.get('WhatId')}/view"
                if what_type == "Case" and t.get("WhatId")
                else None
            ),
            "overdue": bool(due and due < as_of),
            "due_today": bool(due and due == as_of),
        }
        rows.append(row)
        buckets[bucket].append(row)
        by_what[what_type or "Unrelated"] += 1
        if row["overdue"]:
            overdue.append(row)
        elif row["due_today"]:
            due_today.append(row)
        elif not due:
            no_due.append(row)

    bucket_counts = {k: len(v) for k, v in sorted(buckets.items(), key=lambda x: -len(x[1]))}
    return {
        "as_of": str(as_of),
        "total_open": len(rows),
        "overdue_count": len(overdue),
        "due_today_count": len(due_today),
        "no_due_date_count": len(no_due),
        "bucket_counts": bucket_counts,
        "related_object_counts": dict(by_what),
        "overdue": overdue[:25],
        "due_today": due_today[:25],
        "buckets": {k: v[:15] for k, v in buckets.items()},
        "tasks": rows,
        "note": "Read-only overview — no Task updates during Good Morning cascade.",
    }


def render_md(data: dict[str, Any]) -> str:
    lines = [
        "# SF Task Overview — Crystal",
        "",
        f"**As of:** {data['as_of']} (America/Chicago)",
        f"**Open Tasks:** {data['total_open']}",
        f"**Overdue:** {data['overdue_count']} · **Due today:** {data['due_today_count']} · "
        f"**No due date:** {data['no_due_date_count']}",
        "",
        "## By bucket",
        "",
        "| Bucket | Count |",
        "| --- | ---: |",
    ]
    for label, count in (data.get("bucket_counts") or {}).items():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "## Overdue (top 25)", ""])
    if not data.get("overdue"):
        lines.append("_None._")
    else:
        for t in data["overdue"]:
            lines.append(
                f"- **{t.get('activity_date')}** — {t.get('subject')} "
                f"({t.get('status')})"
            )
    lines.extend(["", "## Due today", ""])
    if not data.get("due_today"):
        lines.append("_None._")
    else:
        for t in data["due_today"]:
            lines.append(f"- {t.get('subject')} ({t.get('status')})")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Crystal open SF Task overview")
    parser.add_argument("--org", default="vixxo")
    parser.add_argument("--owner-email", default=DEFAULT_OWNER_EMAIL)
    parser.add_argument("--json", action="store_true", help="Print summary JSON to stdout")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for dated JSON/MD artifacts",
    )
    args = parser.parse_args()

    as_of = datetime.now(TZ).date()
    owner_id = resolve_user_id(args.org, args.owner_email)
    tasks = fetch_open_tasks(owner_id, args.org)
    data = build_overview(tasks, as_of)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = as_of.isoformat()
    json_path = args.output_dir / f"Crystal-SF-Tasks-{stamp}.json"
    md_path = args.output_dir / f"Crystal-SF-Tasks-{stamp}.md"
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    md_path.write_text(render_md(data), encoding="utf-8")

    summary = {
        "total_open": data["total_open"],
        "overdue_count": data["overdue_count"],
        "due_today_count": data["due_today_count"],
        "bucket_counts": data["bucket_counts"],
        "json": str(json_path),
        "md": str(md_path),
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Wrote {json_path}")
        print(f"Wrote {md_path}")
        print(
            f"Open={data['total_open']} overdue={data['overdue_count']} "
            f"due_today={data['due_today_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
