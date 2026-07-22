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
  python live_run_ksonboarding_voicemails.py --revet-errors --dry-run
  python live_run_ksonboarding_voicemails.py --revet-errors --re-vet
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
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
from gateway_vetting import gateway_health_check, vixxolink_get_sr_sp  # noqa: E402
from live_run_batch import OUT_DIR, apply_item  # noqa: E402
from voicemail_entities import enrich_voicemail_entities  # noqa: E402

DOMAIN = "vixxo-helpdesk.freshdesk.com"
SPM_GROUP = "159000485013"
QUERY_OPEN = f"group_id:{SPM_GROUP} AND status:2 AND type:'KSOnboarding'"
VETTING_DEFERRED_RE = re.compile(
    r"vetting deferred|vetting skipped|Entity posture:\*\* Unknown",
    re.I,
)


def search_tickets(api_key: str, query: str, max_pages: int = 11) -> list[dict]:
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


def fetch_ticket(api_key: str, ticket_id: int) -> dict:
    return http_json(
        "GET",
        f"/api/v2/tickets/{ticket_id}?include=requester,conversations",
        api_key,
    )


def is_unknown_sp_ticket(ticket: dict) -> bool:
    tags = {str(t).lower() for t in (ticket.get("tags") or [])}
    cf_sp = str((ticket.get("custom_fields") or {}).get("cf_sp") or "").strip()
    if "unknown-sp" in tags:
        return True
    if cf_sp.lower() in ("unknown", ""):
        return True
    return False


def note_indicates_deferred_vetting(ticket: dict) -> bool:
    parts = [
        ticket.get("description_text") or strip_html(ticket.get("description") or ""),
    ]
    for conv in ticket.get("conversations") or []:
        if conv.get("private"):
            parts.append(conv.get("body_text") or strip_html(conv.get("body") or ""))
    blob = "\n".join(parts)
    return bool(VETTING_DEFERRED_RE.search(blob))


def discover_ksonboarding_voicemails(api_key: str, *, include_resolved: bool = False) -> list[dict]:
    queries = [QUERY_OPEN]
    if include_resolved:
        since = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
        queries.append(
            f"group_id:{SPM_GROUP} AND status:5 AND type:'KSOnboarding' AND updated_at:>'{since}'"
        )
    by_id: dict[int, dict] = {}
    for query in queries:
        for row in search_tickets(api_key, query):
            if not is_voicemail_ticket(row):
                continue
            tid = int(row["id"])
            if tid not in by_id:
                by_id[tid] = fetch_ticket(api_key, tid)
    return list(by_id.values())


def discover_revet_error_candidates(api_key: str) -> list[dict]:
    """Voicemails likely mis-vetted: unknown-sp tag, cf_sp Unknown, or deferred vetting note."""
    since = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
    queries = [
        f"group_id:{SPM_GROUP} AND type:'KSOnboarding' AND tag:'unknown-sp' AND updated_at:>'{since}'",
        QUERY_OPEN,
        f"group_id:{SPM_GROUP} AND status:5 AND type:'KSOnboarding' AND updated_at:>'{since}'",
    ]
    by_id: dict[int, dict] = {}
    for query in queries:
        for row in search_tickets(api_key, query):
            if not is_voicemail_ticket(row):
                continue
            tid = int(row["id"])
            if tid in by_id:
                continue
            ticket = fetch_ticket(api_key, tid)
            if is_unknown_sp_ticket(ticket) or note_indicates_deferred_vetting(ticket):
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
        ticket = fetch_ticket(api_key, tid)
        if not is_voicemail_ticket(ticket):
            raise SystemExit(f"ERROR: #{tid} is not a New voicemail KSOnboarding ticket")
        tickets.append(ticket)
    return tickets


def print_item_line(item: dict, *, prefix: str = "") -> None:
    gw = item.get("gateway_sp") or {}
    print(
        f"{prefix}#{item['ticket_id']} {item['posture']} "
        f"contact={item.get('vetting_contact_name')} "
        f"tokens={item.get('caller_id_tokens')} "
        f"gw={gw.get('sp_number')} "
        f"cf_sp→{item.get('cf_sp_target')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Vet KSOnboarding voicemails with contact-name search")
    parser.add_argument("--ticket", type=int, action="append", dest="tickets", help="Freshdesk ticket id(s)")
    parser.add_argument(
        "--revet-errors",
        action="store_true",
        help="Re-vet voicemails tagged unknown-sp, cf_sp Unknown, or with deferred vetting notes",
    )
    parser.add_argument("--re-vet", action="store_true", help="Apply writes (required with --revet-errors live apply)")
    parser.add_argument("--dry-run", action="store_true", help="Vet only; no Freshdesk writes")
    args = parser.parse_args()

    if args.revet_errors and not args.dry_run and not args.re_vet:
        print("ERROR: --revet-errors live apply requires --re-vet", file=sys.stderr)
        return 2

    api = load_credentials()
    gw_health = gateway_health_check()
    if not gw_health.get("ok"):
        print(json.dumps({"error": "Gateway unavailable", "health": gw_health}, indent=2))
        return 1

    if args.tickets:
        tickets = load_tickets(api, args.tickets)
    elif args.revet_errors:
        tickets = discover_revet_error_candidates(api)
    else:
        tickets = discover_ksonboarding_voicemails(api, include_resolved=False)
        if not args.re_vet:
            tickets = [
                t
                for t in tickets
                if "sp-vetted" not in (t.get("tags") or [])
                and "vetting-complete" not in (t.get("tags") or [])
            ]

    items = [build_item(ticket) for ticket in tickets]
    corrected = [
        item
        for item in items
        if str(item["posture"]).startswith("Known SP")
        and (
            str(item.get("cf_sp_current") or "").lower() in ("unknown", "")
            or "unknown-sp" in [str(t).lower() for t in (ticket_tags(tickets, item["ticket_id"]))]
        )
    ]
    still_unknown = [item for item in items if item["posture"] == "Unknown / Not in systems"]

    results: list[dict] = []
    if args.dry_run:
        print(f"=== Re-vet dry-run — {len(items)} voicemail(s) ===")
        for item in items:
            print_item_line(item)
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
        if corrected:
            print(f"\n=== Corrections available ({len(corrected)}) ===")
            for item in corrected:
                print_item_line(item, prefix="FIX ")
    else:
        for item in items:
            result = apply_item(api, item)
            results.append(result)
            print(f"#{item['ticket_id']} {item['posture']} cf_sp={result.get('cf_sp')}")

    known = sum(1 for item in items if str(item["posture"]).startswith("Known SP"))
    summary = {
        "mode": "dry-run" if args.dry_run else "live",
        "revet_errors": args.revet_errors,
        "ticket_ids": [int(t["id"]) for t in tickets],
        "vetted": len(items),
        "known_sp": known,
        "corrected_candidates": [i["ticket_id"] for i in corrected],
        "still_unknown": [i["ticket_id"] for i in still_unknown],
        "gateway_health": gw_health,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = "revet-errors" if args.revet_errors else "ksonboarding-voicemails"
    out = OUT_DIR / f"live-run-{label}-{stamp}.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "mode",
                    "revet_errors",
                    "vetted",
                    "known_sp",
                    "corrected_candidates",
                    "still_unknown",
                    "run_at",
                )
            },
            indent=2,
        )
    )
    print(f"Wrote {out}")
    return 0


def ticket_tags(tickets: list[dict], ticket_id: int) -> list[str]:
    for ticket in tickets:
        if int(ticket.get("id") or 0) == int(ticket_id):
            return list(ticket.get("tags") or [])
    return []


if __name__ == "__main__":
    raise SystemExit(main())
