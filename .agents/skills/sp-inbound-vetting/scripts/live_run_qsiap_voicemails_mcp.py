#!/usr/bin/env python3
"""Live qsiap voicemail vetting using Freshdesk API + Gateway MCP cache.

Shell Gateway token in ~/.vixxo/ may be expired; populate gateway cache via
Cursor MCP (project-0-assistant-CGagner-gateway) then run apply.

  python .../live_run_qsiap_voicemails_mcp.py prepare-lookups
  # Agent fills .tmp/live-run/gateway-mcp-cache.json via MCP
  python .../live_run_qsiap_voicemails_mcp.py apply --gateway-cache .tmp/live-run/gateway-mcp-cache.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

import gateway_vetting as gv  # noqa: E402
from batch_process_freshdesk import load_credentials  # noqa: E402
from live_run_batch import OUT_DIR, apply_item, posture_tag  # noqa: E402
from live_run_qsiap_voicemails import (  # noqa: E402
    QSIAP,
    SKIP_DEFAULT,
    apply_qsiap_item,
    build_item,
    discover_qsiap_voicemails,
)
from voicemail_intake_routing import classify_voicemail_intake, routing_note  # noqa: E402

CACHE: dict[str, Any] = {}


def cache_key(tool: str, args: dict | None) -> str:
    return f"{tool}:{json.dumps(args or {}, sort_keys=True)}"


def install_gateway_cache(cache_path: Path | None) -> None:
    global CACHE
    if not cache_path or not cache_path.is_file():
        CACHE = {}
        return
    CACHE = json.loads(cache_path.read_text(encoding="utf-8"))

    def cached_search(**kwargs: Any) -> list[dict]:
        key = cache_key("gateway_search_invoices", kwargs)
        raw = CACHE.get("responses", {}).get(key)
        if raw is None:
            return []
        if isinstance(raw, list):
            return raw
        return gv.invoice_list_from_response(raw)

    def cached_get_sr(sr: str) -> dict | None:
        args = {"service_request_number": sr, "number": sr, "sr_number": sr}
        key = cache_key("gateway_get_service_request", args)
        raw = CACHE.get("responses", {}).get(key)
        if raw is None:
            return None
        data = raw if isinstance(raw, dict) else gv.parse_json_blob(str(raw))
        if isinstance(data, dict):
            return gv.sp_from_sr_payload(data, f"gateway_get_service_request({sr})")
        return None

    def cached_sr_invoice_status(sr: str, sp_number: str | None = None) -> dict:
        key = cache_key("gateway_sr_invoice_status", {"sr": sr, "sp_number": sp_number})
        hit = CACHE.get("sr_invoice_status", {}).get(key)
        if hit:
            return hit
        invoices_key = cache_key(
            "gateway_invoices_for_sr",
            {"sr": sr, "sp_number": sp_number},
        )
        invoices = CACHE.get("invoices_for_sr", {}).get(invoices_key, [])
        sr_args = {"service_request_number": sr, "number": sr, "sr_number": sr}
        sr_key = cache_key("gateway_get_service_request", sr_args)
        sr_raw = CACHE.get("responses", {}).get(sr_key)
        sr_data = sr_raw if isinstance(sr_raw, dict) else {}
        sr_row = gv._sr_row_from_payload(sr_data) if isinstance(sr_data, dict) else None
        latest = gv._pick_latest_invoice_row(invoices)
        return {
            "sr_number": sr,
            "sr_status": gv._nested_get(sr_row, "status", "statusName") or None,
            "sr_sub_status": gv._nested_get(sr_row, "subStatus", "subStatusName") or None,
            "invoice_count": len(invoices),
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

    gv.gateway_search_invoices = cached_search  # type: ignore[assignment]
    gv.gateway_get_sr = cached_get_sr  # type: ignore[assignment]
    gv.gateway_sr_invoice_status = cached_sr_invoice_status  # type: ignore[assignment]
    gv.vixxolink_get_sr_sp = lambda sr: None  # type: ignore[assignment]
    gv.gateway_swm_get_provider = lambda sp: None  # type: ignore[assignment]


def collect_work(
    skip: set[int],
    re_vet: bool,
    ticket_ids: list[int] | None = None,
) -> tuple[list[dict], list[tuple[dict, dict]]]:
    from batch_process_freshdesk import http_json  # noqa: WPS433

    api = load_credentials()
    if ticket_ids:
        tickets: list[dict] = []
        for tid in ticket_ids:
            if tid in skip:
                continue
            ticket = http_json(
                "GET",
                f"/api/v2/tickets/{tid}?include=requester,conversations",
                api,
            )
            tags = ticket.get("tags") or []
            if not re_vet and ("sp-vetted" in tags or "vetting-complete" in tags):
                continue
            tickets.append(ticket)
    else:
        tickets = discover_qsiap_voicemails(api)
        filtered: list[dict] = []
        for ticket in sorted(
            tickets,
            key=lambda t: t.get("updated_at") or t.get("created_at") or "",
            reverse=True,
        ):
            tid = int(ticket["id"])
            if tid in skip:
                continue
            tags = ticket.get("tags") or []
            if not re_vet and ("sp-vetted" in tags or "vetting-complete" in tags):
                continue
            filtered.append(ticket)
        tickets = filtered

    work: list[tuple[dict, dict]] = [(ticket, build_item(ticket)) for ticket in tickets]
    return tickets, work


def prepare_lookups(skip: set[int], re_vet: bool) -> dict:
    install_gateway_cache(None)
    tickets, work = collect_work(skip, re_vet)
    lookups: list[dict] = []
    sr_invoice_keys: set[str] = set()

    for ticket, item in work:
        entities = {
            "ks_number": item.get("ks_number"),
            "sr_number": item.get("sr_number"),
            "contact_name": item.get("contact_name"),
            "vetting_contact_name": item.get("vetting_contact_name"),
            "requester_email": item.get("requester"),
            "contact_emails": item.get("contact_emails") or [],
            "company": item.get("company"),
            "signature_company": item.get("signature_company"),
        }
        sr = entities.get("sr_number")
        ks = entities.get("ks_number")
        if sr:
            args = {"service_request_number": sr, "number": sr, "sr_number": sr}
            lookups.append({"tool": "gateway_get_service_request", "arguments": args})
            for inv_args in (
                {"serviceRequestNumber": sr},
                {"service_request_number": sr},
                {"searchString": sr},
            ):
                lookups.append({"tool": "gateway_search_invoices", "arguments": inv_args})
            sr_invoice_keys.add(sr)
        if ks:
            lookups.append(
                {
                    "tool": "gateway_search_invoices",
                    "arguments": {"serviceProviderNumber": str(ks)},
                }
            )
        requester = entities.get("requester_email") or ""
        if requester and requester != "Not stated":
            lookups.append(
                {
                    "tool": "gateway_search_invoices",
                    "arguments": {"searchString": requester},
                }
            )
        company = entities.get("company") or ""
        if company and company not in ("Not stated", ""):
            lookups.append(
                {
                    "tool": "gateway_search_invoices",
                    "arguments": {"searchString": company},
                }
            )

    dedup: dict[str, dict] = {}
    for row in lookups:
        key = cache_key(row["tool"], row["arguments"])
        dedup[key] = row

    return {
        "discovered": len(tickets),
        "unvetted": len(work),
        "ticket_ids": [int(item["ticket_id"]) for _, item in work],
        "lookups": list(dedup.values()),
        "sr_numbers": sorted(sr_invoice_keys),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def apply_run(
    skip: set[int],
    re_vet: bool,
    cache_path: Path,
    ticket_ids: list[int] | None = None,
    skip_sf: bool = False,
) -> dict:
    install_gateway_cache(cache_path)
    if skip_sf:
        import dry_run_batch as drb  # noqa: WPS433
        import live_run_qsiap_voicemails as lrq  # noqa: WPS433

        def _empty_sf(_entities):  # noqa: ANN001
            return {
                "lead": None,
                "case": None,
                "contact": None,
                "account": None,
                "errors": [],
            }

        drb.salesforce_search = _empty_sf  # type: ignore[assignment]
        lrq.salesforce_search = _empty_sf  # type: ignore[attr-defined]
    from batch_process_freshdesk import http_json  # noqa: WPS433

    api = load_credentials()
    if ticket_ids:
        id_list = [tid for tid in ticket_ids if tid not in skip]
    else:
        discovered, work_pairs = collect_work(skip, re_vet, ticket_ids=None)
        id_list = [int(ticket["id"]) for ticket, _ in work_pairs]

    results: list[dict] = []
    forward_candidates: list[dict] = []
    failures: list[dict] = []
    known = 0
    processed = 0

    for tid in id_list:
        ticket = http_json(
            "GET",
            f"/api/v2/tickets/{tid}?include=requester,conversations",
            api,
        )
        tags = ticket.get("tags") or []
        if not re_vet and ("sp-vetted" in tags or "vetting-complete" in tags):
            continue
        item = build_item(ticket)
        if item["posture"].startswith("Known SP"):
            known += 1
        convs = ticket.get("conversations") or []
        routing = classify_voicemail_intake(
            ticket,
            conversations=convs,
            sr_number=item.get("sr_number"),
            sp_number=(item.get("gateway_sp") or {}).get("sp_number"),
            gateway_lookup=lambda sr: gv.gateway_get_sr(sr),
        )
        row = apply_qsiap_item(api, item, ticket, convs)
        processed += 1
        row["posture"] = item["posture"]
        row["voicemail_routing"] = routing.resolution
        row["forward_candidate"] = routing.forward_to
        row["gateway_invoice_check"] = routing.gateway_invoice_check
        results.append(row)
        if routing.forward_to:
            forward_candidates.append(
                {
                    "ticket_id": item["ticket_id"],
                    "forward_to": routing.forward_to,
                    "sr": item.get("sr_number"),
                    "gateway_invoice_check": routing.gateway_invoice_check,
                }
            )
        if row.get("error") or str(row.get("qsiap_update", "")).startswith("failed"):
            failures.append(row)
        print(f"#{item['ticket_id']} {item['posture']} -> {routing.resolution}", flush=True)

    tickets_count = len(id_list)
    summary = {
        "mode": "live-mcp",
        "discovered": tickets_count,
        "processed": processed,
        "skipped_ids": sorted(skip),
        "known_sp": known,
        "gateway_cache": str(cache_path),
        "gateway_health": {"ok": True, "source": "cursor_mcp_cache"},
        "skip_sf": skip_sf,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "forward_candidates": forward_candidates,
        "failures": failures,
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"live-run-qsiap-voicemails-MCP-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    summary["output_path"] = str(out)
    print(json.dumps({k: summary[k] for k in ("mode", "discovered", "processed", "known_sp", "run_at", "output_path")}, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="QSIAP voicemail vetting via Gateway MCP cache")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_prep = sub.add_parser("prepare-lookups")
    p_prep.add_argument("--skip", type=int, nargs="*", default=sorted(SKIP_DEFAULT))
    p_prep.add_argument("--re-vet", action="store_true")
    p_prep.add_argument("--out", type=Path, default=OUT_DIR / "qsiap-gateway-lookup-plan.json")

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--gateway-cache", type=Path, required=True)
    p_apply.add_argument(
        "--ticket-ids-file",
        type=Path,
        help="Optional qsiap-ticket-ids.json or plain id list JSON",
    )
    p_apply.add_argument("--skip", type=int, nargs="*", default=sorted(SKIP_DEFAULT))
    p_apply.add_argument("--re-vet", action="store_true")
    p_apply.add_argument("--skip-sf", action="store_true", help="Skip Salesforce CLI lookups")

    args = parser.parse_args()
    skip = set(args.skip or [])

    if args.cmd == "prepare-lookups":
        plan = prepare_lookups(skip, args.re_vet)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        print(json.dumps({k: plan[k] for k in ("discovered", "unvetted", "ticket_ids")}, indent=2))
        print(f"Lookups: {len(plan['lookups'])} -> {args.out}")
        return 0

    ticket_ids: list[int] | None = None
    if args.ticket_ids_file and args.ticket_ids_file.is_file():
        raw = json.loads(args.ticket_ids_file.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            ticket_ids = [int(x) for x in raw]
        elif isinstance(raw, dict):
            if raw.get("unvetted"):
                ticket_ids = [int(t["id"]) for t in raw["unvetted"]]
            elif raw.get("ticket_ids"):
                ticket_ids = [int(x) for x in raw["ticket_ids"]]
    summary = apply_run(
        skip,
        args.re_vet,
        args.gateway_cache,
        ticket_ids=ticket_ids,
        skip_sf=args.skip_sf,
    )
    return 0 if not summary["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
