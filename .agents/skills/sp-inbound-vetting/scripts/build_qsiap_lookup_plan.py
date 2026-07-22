#!/usr/bin/env python3
"""Build Gateway MCP lookup plan from discovered qsiap ticket IDs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import http_json, load_credentials  # noqa: E402
from dry_run_batch import extract_company  # noqa: E402
from entity_extraction import company_search_variants  # noqa: E402
from live_run_qsiap_voicemails import enrich_voicemail_entities  # noqa: E402
from live_run_qsiap_voicemails_mcp import cache_key, prepare_lookups  # noqa: E402

IDS_PATH = SCRIPT_DIR.parent / ".tmp" / "live-run" / "qsiap-ticket-ids.json"
OUT = SCRIPT_DIR.parent / ".tmp" / "live-run" / "qsiap-gateway-lookup-plan.json"


def main() -> int:
    data = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    unvetted = data.get("unvetted") or []
    api = load_credentials()
    lookups: dict[str, dict] = {}
    sr_numbers: set[str] = set()

    for meta in unvetted:
        tid = int(meta["id"])
        ticket = http_json(
            "GET",
            f"/api/v2/tickets/{tid}?include=requester,conversations",
            api,
        )
        entities = enrich_voicemail_entities(ticket, extract_company(ticket))
        sr = entities.get("sr_number")
        ks = entities.get("ks_number")
        requester = entities.get("requester_email") or ""
        if sr:
            sr_numbers.add(sr)
            args = {"service_request_number": sr, "number": sr, "sr_number": sr}
            lookups[cache_key("gateway_get_service_request", args)] = {
                "tool": "gateway_get_service_request",
                "arguments": args,
            }
            for inv_args in (
                {"serviceRequestNumber": sr},
                {"service_request_number": sr},
                {"searchString": sr},
            ):
                lookups[cache_key("gateway_search_invoices", inv_args)] = {
                    "tool": "gateway_search_invoices",
                    "arguments": inv_args,
                }
        if ks:
            args = {"serviceProviderNumber": str(ks)}
            lookups[cache_key("gateway_search_invoices", args)] = {
                "tool": "gateway_search_invoices",
                "arguments": args,
            }
        if requester and requester != "Not stated":
            args = {"searchString": requester}
            lookups[cache_key("gateway_search_invoices", args)] = {
                "tool": "gateway_search_invoices",
                "arguments": args,
            }
        company = entities.get("company") or ""
        if company and company not in ("Not stated", ""):
            for variant in company_search_variants(company)[:2]:
                args = {"searchString": variant}
                lookups[cache_key("gateway_search_invoices", args)] = {
                    "tool": "gateway_search_invoices",
                    "arguments": args,
                }

    plan = {
        "ticket_count": len(unvetted),
        "ticket_ids": [int(t["id"]) for t in unvetted],
        "lookups": list(lookups.values()),
        "sr_numbers": sorted(sr_numbers),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(json.dumps({"tickets": len(unvetted), "lookups": len(plan["lookups"]), "srs": len(sr_numbers)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
