#!/usr/bin/env python3
"""Phase 1: re-vet initial Unknown cohort. Phase 2: vet new qsiap queue."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import http_json  # noqa: E402
from gateway_vetting import gateway_health_check  # noqa: E402
from live_run_qsiap_voicemails import (  # noqa: E402
    OUT_DIR,
    SPM_GROUP,
    apply_qsiap_item,
    build_item,
    ensure_qsiap_transcript,
    is_voicemail_ticket,
    load_credentials,
    qsiap_gate,
    search_open,
)

INITIAL_UNKNOWN = [
    60490, 60595, 60636, 60911, 60991, 61001, 61057, 61531, 61569, 61580,
    61619, 61688, 61717, 61816, 61823, 62299, 65687, 66684, 66705, 67090,
    74059, 75266,
]


def discover_qsiap_open_all(api_key: str) -> list[dict]:
    """All open SPM qsiap voicemails across common types."""
    by_id: dict[int, dict] = {}
    queries = (
        f"group_id:{SPM_GROUP} AND status:2 AND type:'Invoice Support'",
        f"group_id:{SPM_GROUP} AND status:2 AND type:null",
        f"group_id:{SPM_GROUP} AND status:2 AND type:'No Action Required'",
        f"group_id:{SPM_GROUP} AND status:2 AND type:'VixxoLink Support'",
    )
    for q in queries:
        for row in search_open(api_key, q, max_pages=15):
            tid = int(row["id"])
            if tid in by_id:
                continue
            if not is_voicemail_ticket(row):
                continue
            ticket = http_json(
                "GET",
                f"/api/v2/tickets/{tid}?include=requester,conversations",
                api_key,
            )
            if not qsiap_gate(ticket):
                continue
            by_id[tid] = ticket
    return list(by_id.values())


def process_ticket(api_key: str, tid: int, dry_run: bool = False) -> dict:
    ticket = http_json(
        "GET",
        f"/api/v2/tickets/{tid}?include=requester,conversations",
        api_key,
    )
    if not qsiap_gate(ticket):
        return {"ticket_id": tid, "skipped": "not-qsiap"}
    if ticket.get("status") != 2:
        return {"ticket_id": tid, "skipped": f"status-{ticket.get('status')}"}
    if not dry_run:
        ticket = ensure_qsiap_transcript(api_key, ticket)
    item = build_item(ticket)
    if dry_run:
        return {
            "ticket_id": tid,
            "posture": item["posture"],
            "company": item.get("company"),
            "sr_number": item.get("sr_number"),
            "dry_run": True,
        }
    convs = ticket.get("conversations") or []
    row = apply_qsiap_item(api_key, item, ticket, convs)
    return {
        "ticket_id": tid,
        "posture": item["posture"],
        "routing": row.get("voicemail_routing"),
        "type": row.get("qsiap_update"),
        "tags": row.get("qsiap_tags"),
        "error": row.get("error") or row.get("qsiap_update"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--phase", choices=("1", "2", "both"), default="both")
    parser.add_argument("--skip-phase1-if-done", action="store_true", default=True)
    args = parser.parse_args()

    api = load_credentials()
    health = gateway_health_check()
    if not health.get("ok") and not args.dry_run:
        print(json.dumps({"error": "Gateway unavailable", "health": health}, indent=2), flush=True)
        return 1

    results: list[dict] = []
    processed: set[int] = set()

    run_phase1 = args.phase in ("1", "both")
    if run_phase1 and args.skip_phase1_if_done:
        done = 0
        for tid in INITIAL_UNKNOWN:
            t = http_json("GET", f"/api/v2/tickets/{tid}", api)
            tags = set(t.get("tags") or [])
            if "voicemail-vetted" in tags or "open-hold" in tags:
                done += 1
        if done >= len(INITIAL_UNKNOWN):
            print(f"Phase 1: skip — {done}/{len(INITIAL_UNKNOWN)} already re-vetted", flush=True)
            run_phase1 = False
            processed.update(INITIAL_UNKNOWN)

    if run_phase1 and args.phase in ("1", "both"):
        print(f"Phase 1: re-vet {len(INITIAL_UNKNOWN)} initial Unknown tickets", flush=True)
        for tid in INITIAL_UNKNOWN:
            try:
                row = process_ticket(api, tid, dry_run=args.dry_run)
                results.append({"phase": 1, **row})
                processed.add(tid)
                print(f"  #{tid} {row.get('posture')} {row.get('routing', '')}", flush=True)
            except Exception as exc:
                results.append({"phase": 1, "ticket_id": tid, "error": str(exc)})
                print(f"  #{tid} ERROR {exc}", flush=True)
            time.sleep(0.5)

    if args.phase in ("2", "both"):
        tickets = discover_qsiap_open_all(api)
        new_work = [
            t
            for t in tickets
            if int(t["id"]) not in processed
            and int(t["id"]) not in INITIAL_UNKNOWN
            and "vetting-complete" not in (t.get("tags") or [])
        ]
        print(f"Phase 2: vet {len(new_work)} new-queue tickets (of {len(tickets)} open qsiap)", flush=True)
        for ticket in sorted(new_work, key=lambda x: int(x["id"])):
            tid = int(ticket["id"])
            try:
                row = process_ticket(api, tid, dry_run=args.dry_run)
                results.append({"phase": 2, **row})
                print(f"  #{tid} {row.get('posture')} {row.get('routing', '')}", flush=True)
            except Exception as exc:
                results.append({"phase": 2, "ticket_id": tid, "error": str(exc)})
                print(f"  #{tid} ERROR {exc}", flush=True)
            time.sleep(0.5)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = OUT_DIR / f"re-vet-qsiap-phases-{stamp}.json"
    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "gateway_health": health,
        "phase1_count": sum(1 for r in results if r.get("phase") == 1),
        "phase2_count": sum(1 for r in results if r.get("phase") == 2),
        "known_sp": sum(1 for r in results if str(r.get("posture", "")).startswith("Known SP")),
        "unknown": sum(1 for r in results if r.get("posture") == "Unknown / Not in systems"),
        "errors": [r for r in results if r.get("error")],
        "results": results,
    }
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("phase1_count", "phase2_count", "known_sp", "unknown", "run_at")}, indent=2), flush=True)
    print(f"Wrote {out}", flush=True)
    return 0 if not summary["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
