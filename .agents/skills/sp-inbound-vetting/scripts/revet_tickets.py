#!/usr/bin/env python3
"""Re-vet specific Freshdesk tickets — dry-run vet + optional live apply."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import load_credentials  # noqa: E402
from dry_run_batch import (  # noqa: E402
    extract_company,
    gateway_sr_invoice_status,
    get_ticket,
    is_valid_company_string,
    posture,
    resolve_vetting,
)
from queue_config import QUEUES  # noqa: E402

TICKET_QUEUES = {
    57050: "aphelp",
    56604: "invoice-concerns",
    54727: "ksonboarding",
}


def vet_ticket(api_key: str, ticket_id: int, queue_key: str) -> dict:
    queue = QUEUES[queue_key]
    ticket = get_ticket(api_key, ticket_id)
    entities = extract_company(ticket)
    gw, sf, entities = resolve_vetting(entities)
    post, cf_target = posture(gw, sf, entities)
    if entities.get("cf_sp_current") not in (None, "", "Unknown") and post == "Unknown / Not in systems":
        current_cf = str(entities.get("cf_sp_current") or "")
        if is_valid_company_string(current_cf):
            cf_target = "(keep existing)"
        elif is_valid_company_string(str(cf_target)):
            pass
        else:
            cf_target = "(keep existing)" if current_cf else "Unknown"
    item: dict = {
        "ticket_id": ticket_id,
        "queue": queue.key,
        "inbox_label": queue.inbox_label,
        "subject": ticket.get("subject"),
        "company": entities["company"],
        "signature_company": entities.get("signature_company"),
        "contact_name": entities["contact_name"],
        "vetting_contact_name": entities.get("vetting_contact_name"),
        "contact_emails": entities.get("contact_emails"),
        "ks_number": entities["ks_number"],
        "sr_number": entities["sr_number"],
        "requester": entities["requester_email"],
        "cf_sp_current": entities["cf_sp_current"],
        "posture": post,
        "cf_sp_target": cf_target,
        "gateway_sp": gw,
        "sf_lead": sf.get("lead"),
        "sf_case": sf.get("case"),
        "sf_account": sf.get("account"),
        "errors": sf.get("errors", []),
    }
    if queue.key == "invoice-concerns" and entities.get("sr_number"):
        sp_num = (gw or {}).get("sp_number") or entities.get("ks_number")
        item["gateway_sr_invoice"] = gateway_sr_invoice_status(
            entities["sr_number"],
            sp_number=sp_num,
        )
    return item


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-vet specific Freshdesk ticket IDs")
    parser.add_argument("ticket_ids", nargs="+", type=int)
    parser.add_argument(
        "--queue-map",
        help="JSON map of ticket_id -> queue key (default: built-in sf-match-review set)",
    )
    args = parser.parse_args()

    queue_map = TICKET_QUEUES.copy()
    if args.queue_map:
        queue_map.update({int(k): v for k, v in json.loads(args.queue_map).items()})

    api = load_credentials()
    items = []
    for tid in args.ticket_ids:
        qk = queue_map.get(tid)
        if not qk:
            raise SystemExit(f"No queue mapping for ticket {tid}")
        items.append(vet_ticket(api, tid, qk))

    out_dir = SCRIPT_DIR.parent / ".tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"revet-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    payload = {"mode": "revet", "items": items}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"path": str(out_path), "items": items}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
