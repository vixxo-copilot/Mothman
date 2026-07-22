#!/usr/bin/env python3
"""Discover qsiap voicemails without Gateway/SF calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import http_json, is_voicemail_ticket, load_credentials  # noqa: E402
from live_run_qsiap_voicemails import (  # noqa: E402
    QSIAP,
    SKIP_DEFAULT,
    SPM_GROUP,
    blob,
    search_open,
)

OUT = SCRIPT_DIR.parent / ".tmp" / "live-run" / "qsiap-ticket-ids.json"


def main() -> int:
    api = load_credentials()
    by_id: dict[int, dict] = {}
    queries = (
        f"group_id:{SPM_GROUP} AND status:2 AND type:'Invoice Support'",
        f"group_id:{SPM_GROUP} AND status:2 AND type:null",
    )
    for q in queries:
        for row in search_open(api, q):
            tid = int(row["id"])
            if tid in by_id:
                continue
            if not is_voicemail_ticket(row):
                continue
            ticket = http_json("GET", f"/api/v2/tickets/{tid}?include=requester", api)
            if QSIAP not in blob(ticket):
                continue
            by_id[tid] = {
                "id": tid,
                "subject": ticket.get("subject"),
                "updated_at": ticket.get("updated_at"),
                "created_at": ticket.get("created_at"),
                "tags": ticket.get("tags") or [],
            }

    tickets = sorted(by_id.values(), key=lambda t: t.get("updated_at") or "", reverse=True)
    unvetted = [
        t
        for t in tickets
        if t["id"] not in SKIP_DEFAULT
        and "sp-vetted" not in t["tags"]
        and "vetting-complete" not in t["tags"]
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"tickets": tickets, "unvetted": unvetted}, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "discovered": len(tickets),
                "unvetted": len(unvetted),
                "skipped": sorted(SKIP_DEFAULT),
                "ids": [t["id"] for t in unvetted],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
