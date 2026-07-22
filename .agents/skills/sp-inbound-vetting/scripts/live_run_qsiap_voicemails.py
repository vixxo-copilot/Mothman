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
import re
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
    extract_metadata,
    format_stt_transcript,
    http_json,
    is_voicemail_ticket,
    load_credentials,
    strip_html,
)
from transcribe_voicemail import transcribe_ticket  # noqa: E402
from dry_run_batch import (  # noqa: E402
    extract_company,
    gateway_find_sp,
    get_ticket,
    posture,
    salesforce_search,
)
from entity_extraction import is_valid_company_string  # noqa: E402
from gateway_vetting import gateway_health_check, gateway_get_sr  # noqa: E402
from live_run_batch import OUT_DIR, apply_item, posture_tag  # noqa: E402
from voicemail_intake_routing import (  # noqa: E402
    classify_voicemail_intake,
    routing_note,
)

DOMAIN = "vixxo-helpdesk.freshdesk.com"
SPM_GROUP = "159000485013"
QSIAP = "qsiap@vixxo.com"
SKIP_DEFAULT = {74250}  # manually vetted 2026-07-13

SR_CTX_RE = re.compile(
    r"(?:SR|service request|work order)[^\d]{0,40}(1[-\d]{10,18})",
    re.I,
)
SR_RE = re.compile(r"\b(1[-\d]{10,18})\b")
TRANSCRIPT_MARKER = "Transcript source:"
COMPANY_FROM_SPOKEN_RE = re.compile(
    r"\b(?:this is|i'?m|i am|my name is)\s+[\w'.-]+(?:\s+[\w'.-]+){0,3}"
    r"\s+with\s+([A-Za-z0-9 &.'/-]+?)(?:\.|,|$|\s+(?:i'?m|i am|calling|trying))",
    re.I,
)


def normalize_sr(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        core = digits[1:]
    elif len(digits) == 10:
        core = digits
    else:
        return None
    return f"1-{core}"


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


def extract_srs(text: str, phone: str | None) -> list[str]:
    phone_digits = re.sub(r"\D", "", phone or "")[-10:]
    found: list[str] = []
    seen: set[str] = set()
    for m in SR_CTX_RE.finditer(text):
        sr = normalize_sr(m.group(1))
        if sr and sr not in seen:
            seen.add(sr)
            found.append(sr)
    for m in SR_RE.finditer(text):
        sr = normalize_sr(m.group(1))
        if not sr:
            continue
        if phone_digits and re.sub(r"\D", "", sr)[1:] == phone_digits:
            continue
        if sr not in seen:
            seen.add(sr)
            found.append(sr)
    return found


def attachment_context(ticket: dict) -> str:
    names: list[str] = []
    for att in ticket.get("attachments") or []:
        name = str(att.get("name") or att.get("file_name") or "").strip()
        if name:
            names.append(name)
    for conv in ticket.get("conversations") or []:
        for att in conv.get("attachments") or []:
            name = str(att.get("name") or att.get("file_name") or "").strip()
            if name:
                names.append(name)
    return ", ".join(dict.fromkeys(names))


def has_transcript_note(conversations: list[dict]) -> bool:
    return any(
        TRANSCRIPT_MARKER in (c.get("body_text") or c.get("body") or "")
        for c in conversations
    )


def ensure_qsiap_transcript(api_key: str, ticket: dict) -> dict:
    """Transcribe voicemail audio before vetting/routing when missing."""
    convos = ticket.get("conversations") or []
    if has_transcript_note(convos):
        return ticket
    stt = transcribe_ticket(ticket, api_key)
    if not stt.get("ok"):
        return ticket
    meta = extract_metadata(ticket)
    att_ctx = attachment_context(ticket)
    body_lines = [
        "**SP Voicemail transcript (qsiap vetting)**",
        "",
        format_stt_transcript(stt, meta, ticket),
    ]
    if att_ctx:
        body_lines.extend(["", f"**Attachments on ticket:** {att_ctx}"])
    http_json(
        "POST",
        f"/api/v2/tickets/{int(ticket['id'])}/notes",
        api_key,
        {"body": "\n".join(body_lines), "private": True},
    )
    return get_ticket(api_key, int(ticket["id"]))


def company_from_spoken(text: str) -> str | None:
    m = COMPANY_FROM_SPOKEN_RE.search(text)
    if not m:
        return None
    name = m.group(1).strip(" .,-")
    return name if is_valid_company_string(name) else None


def enrich_voicemail_entities(ticket: dict, entities: dict) -> dict:
    meta = extract_metadata(ticket)
    caller = meta.get("caller") or "Not stated"
    if caller not in ("Not stated", "Unknown", "WIRELESS CALLER"):
        entities["contact_name"] = caller
        entities["vetting_contact_name"] = caller
    text = blob(ticket)
    spoken_company = company_from_spoken(text)
    if spoken_company and not entities.get("company"):
        entities["company"] = spoken_company
    srs = extract_srs(text, meta.get("phone"))
    if srs and not entities.get("sr_number"):
        entities["sr_number"] = srs[0]
    return entities


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
        f"group_id:{SPM_GROUP} AND status:2 AND type:'No Action Required'",
        f"group_id:{SPM_GROUP} AND status:2 AND type:'VixxoLink Support'",
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
    if entities.get("cf_sp_current") not in (None, "", "Unknown") and post == "Unknown / Not in systems":
        current_cf = str(entities.get("cf_sp_current") or "")
        if is_valid_company_string(current_cf):
            cf_target = "(keep existing)"
        elif is_valid_company_string(str(cf_target)):
            pass  # overwrite invalid human/bot cf_sp with good extraction
        else:
            cf_target = "(keep existing)" if current_cf else "Unknown"
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
        "errors": sf.get("errors", []),
    }


def apply_qsiap_item(api_key: str, item: dict, ticket: dict, conversations: list[dict]) -> dict:
    """apply_item + qsiap routing (VINT / SPM payment / invoice-forward vetting)."""
    routing = classify_voicemail_intake(
        ticket,
        conversations=conversations,
        sr_number=item.get("sr_number"),
        sp_number=(item.get("gateway_sp") or {}).get("sp_number"),
        gateway_lookup=lambda sr: gateway_get_sr(sr),
    )
    item = {
        **item,
        "voicemail_routing": routing.resolution,
        "voicemail_routing_reason": routing.reason,
    }
    result = apply_item(api_key, item)
    tid = int(item["ticket_id"])
    try:
        route_block = routing_note(routing, sr=item.get("sr_number"))
        http_json(
            "POST",
            f"/api/v2/tickets/{tid}/notes",
            api_key,
            {"body": route_block, "private": True},
        )
    except urllib.error.HTTPError:
        pass
    try:
        ticket = get_ticket(api_key, tid)
        intended = result.get("tags")
        if isinstance(intended, list):
            base_tags = intended
        else:
            existing_tags = list(ticket.get("tags") or [])
            positive_tag = posture_tag(item["posture"])
            base_tags = sorted(set(existing_tags + ["sp-vetted", positive_tag]))
            if positive_tag != "unknown-sp":
                base_tags = [t for t in base_tags if t != "unknown-sp"]
        tags = sorted(set(base_tags + list(routing.tags) + ["qsiap-source", "vetting-complete"]))
        payload: dict = {
            "tags": tags,
            "group_id": routing.group_id,
            "type": routing.ticket_type,
            "status": routing.status,
        }
        cf = result.get("cf_sp")
        if cf and not str(cf).startswith("(keep"):
            payload.setdefault("custom_fields", {})["cf_sp"] = cf
        http_json("PUT", f"/api/v2/tickets/{tid}", api_key, payload)
        result["qsiap_tags"] = tags
        result["voicemail_routing"] = routing.resolution
        result["forward_candidate"] = routing.forward_to
        result["gateway_invoice_check"] = routing.gateway_invoice_check
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
    work: list[tuple[dict, dict]] = []
    for ticket in tickets:
        tid = int(ticket["id"])
        if tid in skip:
            continue
        tags = ticket.get("tags") or []
        if not args.re_vet and ("sp-vetted" in tags or "vetting-complete" in tags):
            continue
        if not args.dry_run:
            ticket = ensure_qsiap_transcript(api, ticket)
        work.append((ticket, build_item(ticket)))

    results: list[dict] = []
    if args.dry_run:
        for ticket, item in work:
            routing = classify_voicemail_intake(
                ticket,
                conversations=ticket.get("conversations") or [],
                sr_number=item.get("sr_number"),
                sp_number=(item.get("gateway_sp") or {}).get("sp_number"),
                gateway_lookup=lambda sr: gateway_get_sr(sr),
            )
            results.append(
                {
                    "ticket_id": item["ticket_id"],
                    "posture": item["posture"],
                    "voicemail_routing": routing.resolution,
                    "forward_candidate": routing.forward_to,
                    "gateway_invoice_check": routing.gateway_invoice_check,
                    "dry_run": True,
                }
            )
    else:
        for ticket, item in work:
            convs = ticket.get("conversations") or []
            row = apply_qsiap_item(api, item, ticket, convs)
            results.append(row)
            print(
                f"#{item['ticket_id']} {item['posture']} -> {row.get('voicemail_routing')}"
            )

    known = sum(1 for _, item in work if item["posture"].startswith("Known SP"))
    summary = {
        "mode": "dry-run" if args.dry_run else "live",
        "discovered": len(tickets),
        "vetted": len(work),
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
    errors = [
        r
        for r in results
        if r.get("error") or str(r.get("qsiap_update", "")).startswith("failed")
    ]
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
