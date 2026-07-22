#!/usr/bin/env python3
"""Merge Gateway MCP lookup responses into cache for live_run_qsiap_voicemails_mcp.py."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import gateway_vetting as gv  # noqa: E402


def cache_key(tool: str, args: dict | None) -> str:
    return f"{tool}:{json.dumps(args or {}, sort_keys=True)}"


def invoice_list(raw: Any) -> list[dict]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return gv.invoice_list_from_response(raw)
    return []


def invoices_for_sr(responses: dict[str, Any], sr: str, sp_number: str | None) -> list[dict]:
    sr = str(sr or "").strip()
    for kwargs in (
        {"serviceRequestNumber": sr},
        {"service_request_number": sr},
        {"searchString": sr},
    ):
        key = cache_key("gateway_search_invoices", kwargs)
        matched = gv._invoices_matching_sr(invoice_list(responses.get(key)), sr)
        if matched:
            return matched
    if sp_number:
        key = cache_key("gateway_search_invoices", {"serviceProviderNumber": str(sp_number)})
        matched = gv._invoices_matching_sr(invoice_list(responses.get(key)), sr)
        if matched:
            return matched
    return []


def build_cache(plan_path: Path, mcp_results_path: Path, out_path: Path) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    mcp = json.loads(mcp_results_path.read_text(encoding="utf-8"))
    responses: dict[str, Any] = {}

    for entry in mcp.get("results") or []:
        tool = entry.get("tool")
        args = entry.get("arguments") or {}
        raw = entry.get("response")
        if tool and raw is not None:
            responses[cache_key(tool, args)] = raw

    invoices_for_sr_map: dict[str, list[dict]] = {}
    sr_status_map: dict[str, dict] = {}

    for sr in plan.get("sr_numbers") or []:
        sp = None
        sr_args = {"service_request_number": sr, "number": sr, "sr_number": sr}
        sr_key = cache_key("gateway_get_service_request", sr_args)
        sr_raw = responses.get(sr_key)
        if isinstance(sr_raw, dict):
            sp_hit = gv.sp_from_sr_payload(sr_raw, sr_key)
            sp = (sp_hit or {}).get("sp_number")

        inv = invoices_for_sr(responses, sr, sp)
        inv_key = cache_key("gateway_invoices_for_sr", {"sr": sr, "sp_number": sp})
        invoices_for_sr_map[inv_key] = inv

        sr_data = sr_raw if isinstance(sr_raw, dict) else {}
        sr_row = gv._sr_row_from_payload(sr_data) if sr_data else None
        latest = gv._pick_latest_invoice_row(inv)
        status_key = cache_key("gateway_sr_invoice_status", {"sr": sr, "sp_number": sp})
        sr_status_map[status_key] = {
            "sr_number": sr,
            "sr_status": gv._nested_get(sr_row, "status", "statusName") or None,
            "sr_sub_status": gv._nested_get(sr_row, "subStatus", "subStatusName") or None,
            "invoice_count": len(inv),
            "latest_invoice": (
                {
                    "viid": latest.get("viid"),
                    "status": latest.get("status"),
                    "consolidated_status": latest.get("consolidatedStatus"),
                    "sp_amount": latest.get("serviceProviderTotalAmount"),
                    "customer_amount": latest.get("customerTotalAmount"),
                    "payment_date": latest.get("paymentDate"),
                    "accepted_date": latest.get("acceptedDate"),
                    "last_updated": latest.get("lastUpdatedDate"),
                    "sp_invoice_number": latest.get("serviceProviderInvoiceNumber"),
                }
                if latest
                else None
            ),
            "source": "gateway_mcp_cache",
        }

    cache = {
        "built_at": mcp.get("built_at"),
        "responses": responses,
        "invoices_for_sr": invoices_for_sr_map,
        "sr_invoice_status": sr_status_map,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cache, indent=2, default=str), encoding="utf-8")
    return {
        "responses": len(responses),
        "sr_invoice_status": len(sr_status_map),
        "output": str(out_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mcp-results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    meta = build_cache(args.plan, args.mcp_results, args.out)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
