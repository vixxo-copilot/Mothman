#!/usr/bin/env python3
"""Dry-run ksonboarding-inbound-routing — classify + vet, no Freshdesk writes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
VETTING_SCRIPTS = SCRIPT_DIR.parents[1] / "sp-inbound-vetting" / "scripts"
VM_SCRIPTS = SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(VETTING_SCRIPTS))
sys.path.insert(0, str(VM_SCRIPTS))

from batch_process_freshdesk import auth_headers, load_credentials, strip_html  # noqa: E402
from classify import classify_ticket, routing_cf_sp, VOICEMAIL_RE  # noqa: E402
from exclusions import EXCLUDED, is_excluded  # noqa: E402
from dry_run_batch import (  # noqa: E402
    extract_company,
    get_ticket as vetting_get_ticket,
    posture,
    salesforce_search,
    search_all,
)
from gateway_vetting import gateway_find_sp  # noqa: E402

try:
    from mcp_http import _token as mcp_token  # noqa: E402
except ImportError:
    def mcp_token() -> str | None:  # noqa: E402
        return None

DOMAIN = "vixxo-helpdesk.freshdesk.com"
QUERY = "group_id:159000485013 AND status:2 AND type:'KSOnboarding'"
ROUTED_TAG = "ks-inbound-routed"


def _urlopen_with_retry(req: urllib.request.Request, *, timeout: int = 90, retries: int = 5) -> Any:
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(min(30, 2 ** attempt * 2))
                continue
            raise


def list_attachments(api_key: str, ticket_id: int) -> list[str]:
    names: list[str] = []
    url = f"https://{DOMAIN}/api/v2/tickets/{ticket_id}?include=conversations"
    req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
    try:
        with _urlopen_with_retry(req) as resp:
            ticket = json.loads(resp.read().decode())
    except urllib.error.HTTPError:
        url = f"https://{DOMAIN}/api/v2/tickets/{ticket_id}"
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        with _urlopen_with_retry(req) as resp:
            ticket = json.loads(resp.read().decode())
    for att in ticket.get("attachments") or []:
        name = att.get("name") or att.get("attachment_url") or ""
        if name:
            names.append(str(name))
    for conv in ticket.get("conversations") or []:
        for att in conv.get("attachments") or []:
            name = att.get("name") or ""
            if name:
                names.append(str(name))
    return names


def collect_item(
    api_key: str, summary: dict, *, re_route: bool, skip_vetting: bool
) -> dict | None:
    tid = int(summary["id"])
    tags = summary.get("tags") or []
    if not re_route and ROUTED_TAG in tags:
        return None
    subject = summary.get("subject") or ""
    if VOICEMAIL_RE.search(subject):
        return None

    ticket = vetting_get_ticket(api_key, tid)
    ticket["description_text"] = ticket.get("description_text") or strip_html(
        ticket.get("description") or ""
    )
    attachment_names = list_attachments(api_key, tid)
    classification = classify_ticket(ticket, attachment_names=attachment_names)

    entities = extract_company(ticket)
    vetting_errors: list[str] = []
    if skip_vetting:
        gw = None
        sf: dict = {"lead": None, "case": None, "errors": ["vetting skipped"]}
        post, _, confidence = "Unknown / Not in systems (vetting skipped)", "Unknown", "Low"
    else:
        gw = gateway_find_sp(entities)
        sf = salesforce_search(entities)
        post, _, confidence = posture(gw, sf)
        vetting_errors = sf.get("errors", [])
    cf_sp = routing_cf_sp(post, confidence, gw)
    if entities.get("cf_sp_current") not in (None, ""):
        cf_sp_note = f"existing: {entities['cf_sp_current']}"
    elif cf_sp:
        cf_sp_note = cf_sp
    else:
        cf_sp_note = "left blank"

    return {
        "ticket_id": tid,
        "subject": subject,
        "requester": entities["requester_email"],
        "contact_name": entities["contact_name"],
        "company": entities["company"],
        "tags_current": tags,
        "classification": classification["classification"],
        "new_type": classification["new_type"],
        "type_change": classification["type_change"],
        "retain_type": classification["retain_type"],
        "cf_type_of_request": classification["cf_type_of_request"],
        "route_tags": classification["route_tags"],
        "signals": classification["signals"],
        "posture": post,
        "confidence": confidence,
        "cf_sp": cf_sp,
        "cf_sp_note": cf_sp_note,
        "gateway_sp": gw,
        "sf_lead": sf.get("lead"),
        "sf_case": sf.get("case"),
        "attachment_names": attachment_names[:10],
        "errors": vetting_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run ksonboarding-inbound-routing")
    parser.add_argument("--re-route", action="store_true", help="Include tickets tagged ks-inbound-routed")
    parser.add_argument("--limit", type=int, default=0, help="Max tickets to process (0 = all)")
    parser.add_argument(
        "--skip-vetting",
        action="store_true",
        help="Classification only — skip Gateway/Salesforce (faster when MCP unavailable)",
    )
    args = parser.parse_args()

    skip_vetting = args.skip_vetting or not mcp_token()
    if skip_vetting and not args.skip_vetting:
        print(
            "NOTE: No Vixxo MCP token — skipping Gateway vetting. "
            "Use --skip-vetting explicitly or configure .env / ~/.vixxo.",
            file=sys.stderr,
        )

    api = load_credentials()
    summaries = search_all(api, QUERY)
    items: list[dict] = []
    skipped = {"routed": 0, "voicemail": 0, "excluded": 0}

    for summary in summaries:
        if args.limit and len(items) >= args.limit:
            break
        tid = int(summary["id"])
        if is_excluded(tid):
            skipped["excluded"] += 1
            continue
        tags = summary.get("tags") or []
        if not args.re_route and ROUTED_TAG in tags:
            skipped["routed"] += 1
            continue
        if VOICEMAIL_RE.search(summary.get("subject") or ""):
            skipped["voicemail"] += 1
            continue
        row = collect_item(api, summary, re_route=args.re_route, skip_vetting=skip_vetting)
        if row:
            items.append(row)

    counts: dict[str, int] = {}
    for item in items:
        key = item["classification"]
        counts[key] = counts.get(key, 0) + 1

    out = {
        "mode": "dry-run",
        "skill": "ksonboarding-inbound-routing",
        "query": QUERY,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "search_total": len(summaries),
        "skipped": skipped,
        "excluded_ticket_ids": sorted(EXCLUDED),
        "vetting_skipped": skip_vetting,
        "in_scope_count": len(items),
        "counts_by_classification": counts,
        "items": items,
    }
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = SCRIPT_DIR.parent / ".tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"dry-run-{ts}.json"
    latest = out_dir / "dry-run-latest.json"
    payload = json.dumps(out, indent=2)
    out_path.write_text(payload, encoding="utf-8")
    latest.write_text(payload, encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
