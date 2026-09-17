#!/usr/bin/env python3
"""Export open SF Case window for Crystal-queue duplicate scans.

Morning Good Morning must refresh this daily (do not reuse prior-day cache).
Writes:
  .tmp/sf-cases-window-crystal-queue-YYYYMMDD.json

Scope:
  IsClosed = false AND (
    RecordType in Rate Negotiation / Service Provider Support /
      Provider Onboarding / Coverage Change / Recruitment Request
      AND CreatedDate = LAST_N_DAYS:100
    OR OwnerId = Crystal
  )

Usage:
  python export_crystal_queue_case_window.py
  python export_crystal_queue_case_window.py --date 20260826
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_TMP = SCRIPTS.parent / ".tmp"
sys.path.insert(0, str(SCRIPTS))

from sf_cli import sf_path  # noqa: E402

# Central without tzdata dependency (Windows). CST/CDT approx is fine for date stamp.
CENTRAL = timezone(timedelta(hours=-5))

FIELDS = (
    "Id, CaseNumber, Subject, Status, Description, CreatedDate, "
    "OwnerId, Owner.Id, Owner.Name, Owner.Username, "
    "Account.Name, ContactEmail, SuppliedEmail, RecordType.Name"
)

RECORD_TYPES = (
    "Rate Negotiation",
    "Service Provider Support",
    "Provider Onboarding",
    "Coverage Change",
    # Reassigned twins often land here (e.g. Case 6472 → Shelby).
    "Recruitment Request",
)

CRYSTAL_OWNER_ID = "005TS000009gWazYAE"


def today_yyyymmdd() -> str:
    return datetime.now(CENTRAL).strftime("%Y%m%d")


def build_window_soql(*, lookback_days: int) -> str:
    rt_list = ", ".join(f"'{n}'" for n in RECORD_TYPES)
    return (
        f"SELECT {FIELDS} FROM Case "
        "WHERE IsClosed = false "
        f"AND RecordType.Name IN ({rt_list}) "
        f"AND CreatedDate = LAST_N_DAYS:{lookback_days} "
        "ORDER BY CreatedDate ASC"
    )


def build_crystal_open_soql() -> str:
    """Any open Case Crystal still owns (any RecordType / age)."""
    return (
        f"SELECT {FIELDS} FROM Case "
        f"WHERE IsClosed = false AND OwnerId = '{CRYSTAL_OWNER_ID}' "
        "ORDER BY CreatedDate ASC"
    )


def query_all(soql: str, org: str = "vixxo") -> list[dict]:
    cmd = [
        sf_path(),
        "data",
        "query",
        "--query",
        soql,
        "--target-org",
        org,
        "--json",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"sf query JSON parse failed ({exc}): {(proc.stdout or '')[:500]}"
        ) from exc
    if proc.returncode != 0 or payload.get("status", 0) != 0:
        raise SystemExit(
            f"sf query failed: {payload.get('message') or proc.stderr or proc.stdout}"
        )
    result = payload.get("result") or {}
    return list(result.get("records") or [])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        default=today_yyyymmdd(),
        help="YYYYMMDD stamp for output filename (default: today Central)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=100,
        help="CreatedDate LAST_N_DAYS window (default 100)",
    )
    parser.add_argument("--org", default="vixxo")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    out = args.output or (
        SKILL_TMP / f"sf-cases-window-crystal-queue-{args.date}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    soql_window = build_window_soql(lookback_days=args.lookback_days)
    soql_mine = build_crystal_open_soql()
    print(f"Querying {args.org} window …", flush=True)
    window = query_all(soql_window, org=args.org)
    print(f"Querying {args.org} Crystal open …", flush=True)
    mine = query_all(soql_mine, org=args.org)
    by_id: dict[str, dict] = {}
    for rec in [*window, *mine]:
        rid = rec.get("Id")
        if rid:
            by_id[rid] = rec
    records = sorted(by_id.values(), key=lambda r: r.get("CreatedDate") or "")
    payload = {
        "records": records,
        "totalSize": len(records),
        "done": True,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "soql_window": soql_window,
        "soql_crystal_open": soql_mine,
        "org": args.org,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "path": str(out),
                "totalSize": len(records),
                "date": args.date,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
