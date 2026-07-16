#!/usr/bin/env python3
"""Live vet KSOnboarding voicemails — Gateway + VixxoLink + SF + FD notes.

Use when batch REST triage marked Unknown SP but caller ID / contact name
should resolve a known provider (e.g. Hemmert → KS101094).

Requires:
  - FRESHDESK_API_KEY (.env or ~/.vixxo/freshdesk_token)
  - Gateway MCP token or GATEWAY_API_TOKEN for shell runs
  - sf CLI target-org vixxo (optional SF bootstrap)

Examples:
  python live_run_ksonboarding_voicemails.py --ticket 74473 --dry-run
  python live_run_ksonboarding_voicemails.py --ticket 74473 --re-vet
"""

from __future__ import annotations

import argparse
import json
import sys
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
)
from dry_run_batch import (  # noqa: E402
    extract_company,
    gateway_find_sp,
    get_ticket,
    posture,
    salesforce_search,
)
from gateway_vetting import gateway_health_check, vixxolink_get_sr_sp  # noqa: E402
from live_run_batch import OUT_DIR, apply_item  # noqa: E402
from voicemail_entities import enrich_voicemail_entities  # noqa: E402

DOMAIN = "vixxo-helpdesk.freshdesk.com"
QUERY = "group_id:159000485013 AND status:2 AND type:'KSOnboarding'"


def search_open(api_key: str, query: str, max_pages: int = 11) -> list[dict]:
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        params = {"query": f'"{query}"', "page": str(page)}
        url = f"https://{DOMAIN}/api/v2/search/tickets?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        rows = data.get("results") or []
        out.extend(rows)
        if len(rows) < 30:
            break
    return out


def discover_ksonboarding_voicemails(api_key: str) -> list[dict]:
    tickets: list[dict] = []
    for row in search_open(api_key, QUERY):
        if not is_voicemail_ticket(row):
            continue
        tid = int(row["id"])
        tickets.append(
            http_json(
                "GET",
                f"/api/v2/tickets/{tid}?include=requester,conversations",
                api_key,
            )
        )
    return tickets


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

    vixxolink_sp = None
    sr = entities.get("sr_number")
    if sr and (not gw or not gw.get("sp_number")):
        vixxolink_sp = vixxolink_get_sr_sp(sr)
        if vixxolink_sp and not gw:
            gw = vixxolink_sp

    post, cf_target = posture(gw, sf, entities)
    return {
        "ticket_id": tid,
        "queue": "ksonboarding-voicemail",
        "subject": ticket.get("subject"),
        "company": entities.get("company"),
        "contact_name": entities.get("contact_name"),
        "vetting_contact_name": entities.get("vetting_contact_name"),
        "caller_id_tokens": entities.get("caller_id_tokens"),
        "callback_phone": entities.get("callback_phone"),
        "ks_number": entities.get("ks_number"),
        "sr_number": sr,
        "requester": entities.get("requester_email"),
        "cf_sp_current": entities.get("cf_sp_current"),
        "posture": post,
        "cf_sp_target": cf_target,
        "gateway_sp": gw,
        "vixxolink_sp": vixxolink_sp,
        "sf_lead": sf.get("lead"),
        "sf_case": sf.get("case"),
        "sf_contact": sf.get("contact"),
        "sf_account": sf.get("account"),
        "errors": sf.get("errors", []),
    }


def load_tickets(api_key: str, ticket_ids: list[int]) -> list[dict]:
    tickets: list[dict] = []
    for tid in ticket_ids:
        ticket = http_json(
            "GET",
            f"/api/v2/tickets/{tid}?include=requester,conversations",
            api_key,
        )
        if not is_voicemail_ticket(ticket):
            raise SystemExit(f"ERROR: #{tid} is not a New voicemail KSOnboarding ticket")
        tickets.append(ticket)
    return tickets


def main() -> int:
    parser = argparse.ArgumentParser(description="Vet KSOnboarding voicemails with contact-name search")
    parser.add_argument("--ticket", type=int, action="append", dest="tickets", help="Freshdesk ticket id(s)")
    parser.add_argument("--re-vet", action="store_true", help="Include sp-vetted tickets in batch mode")
    parser.add_argument("--dry-run", action="store_true", help="Vet only; no Freshdesk writes")
    args = parser.parse_args()

    api = load_credentials()
    gw_health = gateway_health_check()
    if not gw_health.get("ok"):
        print(json.dumps({"error": "Gateway unavailable", "health": gw_health}, indent=2))
        return 1

    if args.tickets:
        tickets = load_tickets(api, args.tickets)
    else:
        tickets = discover_ksonboarding_voicemails(api)
        if not args.re_vet:
            tickets = [
                t
                for t in tickets
                if "sp-vetted" not in (t.get("tags") or [])
                and "vetting-complete" not in (t.get("tags") or [])
            ]

    items = [build_item(ticket) for ticket in tickets]
    results: list[dict] = []
    if args.dry_run:
        for item in items:
            print(
                f"#{item['ticket_id']} {item['posture']} "
                f"contact={item.get('vetting_contact_name')} "
                f"tokens={item.get('caller_id_tokens')} "
                f"gw={((item.get('gateway_sp') or {}).get('sp_number'))}"
            )
            results.append(
                {
                    "ticket_id": item["ticket_id"],
                    "posture": item["posture"],
                    "cf_sp_target": item["cf_sp_target"],
                    "gateway_sp": item.get("gateway_sp"),
                    "sf_account": item.get("sf_account"),
                    "sf_contact": item.get("sf_contact"),
                    "dry_run": True,
                }
            )
    else:
        for item in items:
            result = apply_item(api, item)
            results.append(result)
            print(f"#{item['ticket_id']} {item['posture']} cf_sp={result.get('cf_sp')}")

    known = sum(1 for item in items if str(item["posture"]).startswith("Known SP"))
    summary = {
        "mode": "dry-run" if args.dry_run else "live",
        "ticket_ids": [int(t["id"]) for t in tickets],
        "vetted": len(items),
        "known_sp": known,
        "gateway_health": gw_health,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = OUT_DIR / f"live-run-ksonboarding-voicemails-{stamp}.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("mode", "ticket_ids", "vetted", "known_sp", "run_at")}, indent=2))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
