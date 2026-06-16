#!/usr/bin/env python3
"""Re-run triage on explicit ticket IDs (for closed/misrouted voicemails)."""

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
    process_ticket,
)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: rerun_ticket_ids.py <batch-summary.json> [--reroute-spm]", file=sys.stderr)
        return 2

    batch_path = Path(sys.argv[1])
    reroute = "--reroute-spm" in sys.argv
    payload = json.loads(batch_path.read_text(encoding="utf-8"))
    ticket_ids = [int(r["ticket_id"]) for r in payload.get("results") or []]
    api_key = load_credentials()

    reopened = 0
    results = []
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
            reopened += 1
        except Exception as exc:  # noqa: BLE001
            results.append({"ticket_id": tid, "phase": "reopen", "error": str(exc)})
            continue

        ticket = http_json("GET", f"/api/v2/tickets/{tid}", api_key)
        try:
            results.append(
                process_ticket(
                    api_key,
                    ticket,
                    reroute_correction=reroute,
                ).__dict__
            )
        except Exception as exc:  # noqa: BLE001
            results.append({"ticket_id": tid, "phase": "process", "error": str(exc)})

    summary = {
        "reopened": reopened,
        "processed": len([r for r in results if r.get("note") == "posted"]),
        "routed": len([r for r in results if r.get("forward") and not str(r.get("forward")).startswith("failed")]),
        "closed": len([r for r in results if r.get("resolve") == "closed"]),
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"rerun-spm-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("reopened", "processed", "routed", "closed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
