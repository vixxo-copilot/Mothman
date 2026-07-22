#!/usr/bin/env python3
"""Live vet all open qsiap@vixxo.com voicemails — Gateway + SF + FD notes.

Requires:
  - FRESHDESK_API_KEY ( .env or ~/.vixxo/freshdesk_token )
  - GATEWAY_API_TOKEN or VIXXONOW_API_TOKEN ( .env or ~/.vixxo/ )
  - sf CLI target-org vixxo (optional SF Tasks)

Run from repo root:
  python .agents/skills/sp-inbound-vetting/scripts/live_run_qsiap_voicemails.py
  python .agents/skills/sp-inbound-vetting/scripts/live_run_qsiap_voicemails.py --skip 74250
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import (  # noqa: E402
    auth_headers,
    http_json,
    is_voicemail_ticket,
    load_credentials,
    strip_html,
)
from dry_run_batch import (  # noqa: E402
    extract_company,
    gateway_find_sp,
    get_ticket,
    posture,
    salesforce_search,
)
from gateway_vetting import gateway_health_check  # noqa: E402
from live_run_batch import OUT_DIR, apply_item  # noqa: E402
from voicemail_entities import enrich_voicemail_entities  # noqa: E402

DOMAIN = "vixxo-helpdesk.freshdesk.com"
SPM_GROUP = "159000485013"
QSIAP = "qsiap@vixxo.com"
SKIP_DEFAULT = {74250}  # manually vetted 2026-07-13


def blob(ticket: dict) -> str:
    parts = [
        ticket.get("subject") or "",
        ticket.get("description_text") or strip_html(ticket.get("description") or ""),
    ]
    for field in ("to_emails", "cc_emails", "support_email"):
        val = ticket.get(field)
        if isinstance(val, list):
            parts.extend(str(x) for x in val)
        elif val:
            parts.append(str(val))
    for conv in ticket.get("conversations") or []:
        parts.append(conv.get("body_text") or strip_html(conv.get("body") or ""))
    return " ".join(parts).lower()


def qsiap_gate(ticket: dict) -> bool:
    return QSIAP in blob(ticket)


def search_open(api_key: str, query: str, max_pages: int = 12) -> list[dict]:
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        params = {"query": f'"{query}"', "page": str(page)}
        url = f"https://{DOMAIN}/api/v2/search/tickets?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError:
            break
        rows = data.get("results") or []
        out.extend(rows)
        if len(rows) < 30:
            break
    return out


def discover_qsiap_voicemails(api_key: str) -> list[dict]:
    """Bypass Freshdesk 300-cap by scanning type slices."""
    by_id: dict[int, dict] = {}
    queries = (
        f"group_id:{SPM_GROUP} AND status:2 AND type:'Invoice Support'",
        f"group_id:{SPM_GROUP} AND status:2 AND type:null",
    )
    for q in queries:
        for row in search_open(api_key, q):
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


def build_item(ticket: dict) -> dict:
    tid = int(ticket["id"])
    entities = enrich_voicemail_entities(ticket, extract_company(ticket))
    gw = gateway_find_sp(entities)
    sf = salesforce_search(entities)
    if not gw and sf.get("account"):
        sp_num = str((sf["account"] or {}).get("Service_Provider_Number__c") or "").strip()
        if sp_num.upper().startswith("KS") and not entities.get("ks_number"):
            entities["ks_number"] = sp_num.upper()
            gw = gateway_find_sp(entities) or gw
    post, cf_target = posture(gw, sf, entities)
    return {
        "ticket_id": tid,
        "queue": "qsiap-voicemail",
        "inbox_label": QSIAP,
        "subject": ticket.get("subject"),
        "company": entities["company"],
        "signature_company": entities.get("signature_company"),
        "contact_name": entities["contact_name"],
        "vetting_contact_name": entities.get("vetting_contact_name"),
        "contact_emails": entities.get("contact_emails"),
        "ks_number": entities["ks_number"],
        "sr_number": entities.get("sr_number"),
        "requester": entities["requester_email"],
        "cf_sp_current": entities["cf_sp_current"],
        "posture": post,
        "cf_sp_target": cf_target,
        "gateway_sp": gw,
        "sf_lead": sf.get("lead"),
        "sf_case": sf.get("case"),
        "sf_account": sf.get("account"),
        "sf_contact": sf.get("contact"),
        "errors": sf.get("errors", []),
    }


def apply_qsiap_item(api_key: str, item: dict) -> dict:
    """apply_item + qsiap tags and Invoice Support type when missing."""
    result = apply_item(api_key, item)
    tid = int(item["ticket_id"])
    if result.get("error") and "type" in str(result.get("error", "")):
        pass
    try:
        ticket = get_ticket(api_key, tid)
        tags = sorted(
            set((ticket.get("tags") or []) + ["qsiap-source", "voicemail-vetted"])
        )
        payload: dict = {"tags": tags}
        if not ticket.get("type"):
            payload["type"] = "Invoice Support"
        cf = result.get("cf_sp")
        if cf and not str(cf).startswith("(keep"):
            payload.setdefault("custom_fields", {})["cf_sp"] = cf
        http_json("PUT", f"/api/v2/tickets/{tid}", api_key, payload)
        result["qsiap_tags"] = tags
    except urllib.error.HTTPError as exc:
        result["qsiap_update"] = f"failed:{exc.code}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Vet open qsiap AP voicemails")
    parser.add_argument(
        "--skip",
        type=int,
        nargs="*",
        default=sorted(SKIP_DEFAULT),
        help="Ticket IDs to skip (default: 74250)",
    )
    parser.add_argument("--re-vet", action="store_true", help="Include sp-vetted tickets")
    parser.add_argument("--dry-run", action="store_true", help="Vet only; no FD writes")
    args = parser.parse_args()
    skip = set(args.skip or [])

    api = load_credentials()
    gw_health = gateway_health_check()
    if not gw_health.get("ok"):
        print(json.dumps({"error": "Gateway unavailable", "health": gw_health}, indent=2))
        return 1

    tickets = discover_qsiap_voicemails(api)
    items: list[dict] = []
    for ticket in tickets:
        tid = int(ticket["id"])
        if tid in skip:
            continue
        tags = ticket.get("tags") or []
        if not args.re_vet and ("sp-vetted" in tags or "vetting-complete" in tags):
            continue
        items.append(build_item(ticket))

    results = []
    if args.dry_run:
        for item in items:
            results.append({"ticket_id": item["ticket_id"], "posture": item["posture"], "dry_run": True})
    else:
        for item in items:
            results.append(apply_qsiap_item(api, item))
            print(f"#{item['ticket_id']} {item['posture']}")

    known = sum(1 for i in items if i["posture"].startswith("Known SP"))
    summary = {
        "mode": "dry-run" if args.dry_run else "live",
        "discovered": len(tickets),
        "vetted": len(items),
        "skipped_ids": sorted(skip),
        "known_sp": known,
        "gateway_health": gw_health,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"live-run-qsiap-voicemails-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("mode", "discovered", "vetted", "known_sp", "run_at")}, indent=2))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
