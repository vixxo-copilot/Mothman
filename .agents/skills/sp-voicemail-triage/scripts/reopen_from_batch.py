#!/usr/bin/env python3
"""Reopen Freshdesk tickets listed in a batch summary JSON file."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch_process_freshdesk import OUT_DIR, http_json, load_credentials  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: reopen_from_batch.py <batch-summary.json>", file=sys.stderr)
        return 2

    batch_path = Path(sys.argv[1])
    payload = json.loads(batch_path.read_text(encoding="utf-8"))
    ticket_ids = [int(r["ticket_id"]) for r in payload.get("results") or []]
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

    summary = {"reopened": len(reopened), "failed": len(failed), "failures": failed}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"reopen-rerun-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"reopened": len(reopened), "failed": len(failed), "summary": str(out)}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
