#!/usr/bin/env python3
"""Reopen backlogged KSOnboarding tickets closed without triage."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch_process_freshdesk import OUT_DIR, http_json, load_credentials  # noqa: E402

BACKLOG_CLOSE = (
    Path(__file__).resolve().parent.parent
    / ".tmp"
    / "batch-run"
    / "close-20260616T164726Z.json"
)


def main() -> int:
    if not BACKLOG_CLOSE.is_file():
        print(f"ERROR: missing {BACKLOG_CLOSE}", file=sys.stderr)
        return 2

    payload = json.loads(BACKLOG_CLOSE.read_text(encoding="utf-8"))
    ticket_ids = [int(x) for x in payload.get("closed_ids") or []]
    api_key = load_credentials()

    reopened: list[int] = []
    failed: list[dict] = []

    for tid in ticket_ids:
        try:
            http_json(
                "PUT",
                f"/api/v2/tickets/{tid}",
                api_key,
                {
                    "status": 2,
                    "type": "KSOnboarding",
                    "custom_fields": {"cf_sp": "Unknown"},
                },
            )
            reopened.append(tid)
        except Exception as exc:  # noqa: BLE001
            failed.append({"ticket_id": tid, "error": str(exc)})

    summary = {
        "reopened": len(reopened),
        "failed": len(failed),
        "reopened_ids": reopened,
        "failures": failed,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"reopen-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"reopened": len(reopened), "failed": len(failed), "summary": str(out)}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
