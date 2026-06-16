#!/usr/bin/env python3
"""Close remaining KSOnboarding voicemail tickets (resolve step only)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch_process_freshdesk import (  # noqa: E402
    OUT_DIR,
    http_json,
    load_credentials,
    search_tickets,
)


def main() -> int:
    api_key = load_credentials()
    tickets = search_tickets(api_key)
    closed: list[int] = []
    failed: list[dict] = []

    for t in tickets:
        tid = int(t["id"])
        try:
            http_json(
                "PUT",
                f"/api/v2/tickets/{tid}",
                api_key,
                {
                    "status": 5,
                    "type": "KSOnboarding",
                    "custom_fields": {"cf_sp": "Unknown"},
                },
            )
            closed.append(tid)
        except Exception as exc:  # noqa: BLE001
            failed.append({"ticket_id": tid, "error": str(exc)})

    summary = {
        "closed": len(closed),
        "failed": len(failed),
        "closed_ids": closed,
        "failures": failed,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"close-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"closed": len(closed), "failed": len(failed), "summary": str(out)}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
