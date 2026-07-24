#!/usr/bin/env python3
"""Live MCP-path QSIAP vetting for known open ticket IDs."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/sp-inbound-vetting/scripts"))
sys.path.insert(0, str(ROOT / ".agents/skills/sp-voicemail-triage/scripts"))

from batch_process_freshdesk import http_json, load_credentials  # noqa: E402
from dry_run_batch import gateway_find_sp, posture, salesforce_search  # noqa: E402
from gateway_vetting import gateway_health_check  # noqa: E402
from live_run_qsiap_voicemails import (  # noqa: E402
    SKIP_DEFAULT,
    apply_qsiap_item,
    build_item,
    discover_qsiap_voicemails,
)

OUT = ROOT / ".agents/skills/sp-inbound-vetting/.tmp"


def main() -> int:
    api = load_credentials()
    gw = gateway_health_check()
    tickets = discover_qsiap_voicemails(api)
    skip = set(SKIP_DEFAULT)
    items = []
    for ticket in tickets:
        tid = int(ticket["id"])
        if tid in skip:
            continue
        items.append(build_item(ticket, api, transcribe=True))

    results = [apply_qsiap_item(api, item) for item in items]
    known = sum(1 for i in items if str(i["posture"]).startswith("Known SP"))
    summary = {
        "mode": "live-mcp-path",
        "discovered": len(tickets),
        "vetted": len(items),
        "known_sp": known,
        "gateway_health": gw,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "postures": [
            {
                "ticket_id": i["ticket_id"],
                "posture": i["posture"],
                "cf_sp_target": i.get("cf_sp_target"),
                "company": i.get("company"),
                "contact_name": i.get("vetting_contact_name") or i.get("contact_name"),
                "gateway_sp": i.get("gateway_sp"),
                "sf_lead": (i.get("sf_lead") or {}).get("Id"),
                "sf_account": (i.get("sf_account") or {}).get("Id"),
            }
            for i in items
        ],
        "results": results,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"live-run-qsiap-voicemails-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("discovered", "vetted", "known_sp", "run_at")}, indent=2))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
