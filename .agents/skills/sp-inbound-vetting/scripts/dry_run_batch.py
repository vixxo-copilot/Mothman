#!/usr/bin/env python3
"""Dry-run sp-inbound-vetting for configured Freshdesk queues."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import http_json, load_credentials, strip_html  # noqa: E402
from gateway_vetting import gateway_find_sp  # noqa: E402
from queue_config import VettingQueue, resolve_queues  # noqa: E402

DOMAIN = "vixxo-helpdesk.freshdesk.com"
VOICEMAIL_RE = re.compile(r"\bnew voicemail\b", re.I)
KS_RE = re.compile(r"\b(KS\d+)\b", re.I)
SR_RE = re.compile(r"\b(1-\d{9,10})\b")


def search_all(api_key: str, query: str) -> list[dict]:
    results: list[dict] = []
    for page in range(1, 11):
        params = {"query": f'"{query}"', "page": str(page)}
        path = "/api/v2/search/tickets?" + urllib.parse.urlencode(params)
        data = http_json("GET", path, api_key)
        page_results = data.get("results") or []
        results.extend(page_results)
        if len(page_results) < 30:
            break
    return results


def get_ticket(api_key: str, ticket_id: int) -> dict:
    return http_json("GET", f"/api/v2/tickets/{ticket_id}?include=requester", api_key)


def ticket_text_blob(ticket: dict) -> str:
    desc = ticket.get("description_text") or strip_html(ticket.get("description") or "")
    return f"{ticket.get('subject') or ''} {desc}".lower()


def passes_recipient_gate(ticket: dict, gate: tuple[str, ...]) -> bool:
    blob = ticket_text_blob(ticket)
    for addr in gate:
        if addr.lower() in blob:
            return True
    for field in ("to_emails", "cc_emails"):
        for entry in ticket.get(field) or []:
            if any(addr.lower() in str(entry).lower() for addr in gate):
                return True
    requester = ticket.get("requester") or {}
    email = (requester.get("email") or "").lower()
    return any(addr.split("@")[0] in email or addr.lower() in email for addr in gate)


def extract_company(ticket: dict) -> dict:
    subject = ticket.get("subject") or ""
    desc = ticket.get("description_text") or strip_html(ticket.get("description") or "")
    requester = ticket.get("requester") or {}
    email = requester.get("email") or ""
    contact_name = (requester.get("name") or "").strip()
    cf = ticket.get("custom_fields") or {}
    cf_sp = cf.get("cf_sp")

    company = None
    patterns = [
        r"Invoice \d+ from (.+)$",
        r"COI - (.+?) - Vixxo",
        r"Your service with[\s\u00a0]*(.+?)[\s\u00a0]*-",
        r"^(KS\d+)\s*-",
        r"from (.+?) via",
        r"Statement from (.+?)(?:\s|$)",
        r"Onboarding setup for (.+?)$",
        r"receipt from (.+?)(?:\.|$)",
        r"FlyLock Security Solutions",
        r"Invoice (.+?) from",
    ]
    for pat in patterns:
        m = re.search(pat, subject, re.I)
        if m:
            company = m.group(1).strip() if m.lastindex else m.group(0).strip()
            break
    if not company and cf_sp and cf_sp not in ("Unknown", ""):
        company = str(cf_sp)
    if not company and "locksmith" in email.lower():
        company = "Texas Premier Locksmith"
    if not company and "flylock.com" in email.lower():
        company = "FlyLock Security Solutions"
    if not company and "glassdoctor" in email.lower():
        company = "Glass Doctor"
    if not company and "golterman.com" in email.lower():
        company = "Golterman and Sabo"
    if not company and "fastsigns.com" in email.lower():
        company = "FastSigns"

    if not company and contact_name and contact_name.lower() not in ("team", "not stated"):
        company = contact_name

    ks = KS_RE.search(f"{subject} {cf_sp or ''}")
    sr = SR_RE.search(f"{subject} {desc}")

    return {
        "company": company or "Not stated",
        "contact_name": contact_name or "Not stated",
        "ks_number": ks.group(1).upper() if ks else None,
        "sr_number": sr.group(1) if sr else None,
        "requester_email": email or "Not stated",
        "cf_sp_current": cf_sp,
    }


def sf_query(soql: str) -> list[dict]:
    import os

    sf_candidates = ["sf"]
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            sf_candidates.insert(0, str(Path(appdata) / "npm" / "sf.cmd"))
    for sf_bin in sf_candidates:
        cmd = [sf_bin, "data", "query", "--query", soql, "--json"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            continue
        if proc.returncode != 0:
            continue
        try:
            return json.loads(proc.stdout).get("result", {}).get("records", [])
        except json.JSONDecodeError:
            continue
    return [{"_error": "Salesforce CLI unavailable"}]


def salesforce_search(entities: dict) -> dict:
    out: dict = {"lead": None, "case": None, "errors": []}
    company = entities.get("company") or ""
    email = entities.get("requester_email") or ""
    contact_name = entities.get("contact_name") or ""

    if company != "Not stated":
        esc = company.replace("'", "\\'")
        leads = sf_query(
            "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
            f"WHERE Company LIKE '%{esc}%' ORDER BY LastModifiedDate DESC LIMIT 3"
        )
        if leads and not leads[0].get("_error"):
            out["lead"] = leads[0]
        elif leads and leads[0].get("_error"):
            out["errors"].append(leads[0]["_error"])

    if contact_name not in ("Not stated", "") and not out.get("lead"):
        esc = contact_name.replace("'", "\\'")
        leads = sf_query(
            "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
            f"WHERE Name LIKE '%{esc}%' ORDER BY LastModifiedDate DESC LIMIT 3"
        )
        if leads and not leads[0].get("_error"):
            out["lead"] = leads[0]

    if email not in ("Not stated", "") and not out.get("lead"):
        esc = email.replace("'", "\\'")
        leads = sf_query(
            f"SELECT Id, Name, Company, Status, Email FROM Lead WHERE Email = '{esc}' LIMIT 3"
        )
        if leads and not leads[0].get("_error"):
            out["lead"] = leads[0]

    if email not in ("Not stated", ""):
        esc = email.replace("'", "\\'")
        cases = sf_query(
            "SELECT Id, CaseNumber, Subject, Status FROM Case "
            f"WHERE ContactEmail = '{esc}' ORDER BY CreatedDate DESC LIMIT 3"
        )
        if cases and not cases[0].get("_error"):
            out["case"] = cases[0]

    return out


def posture(gw: dict | None, sf: dict) -> tuple[str, str]:
    if gw and sf.get("lead"):
        return "Known SP + SF Lead", f"{gw.get('sp_number')} - {gw.get('name')}"
    if gw:
        num, name = gw.get("sp_number"), gw.get("name")
        return "Known SP", f"{num} - {name}" if num else str(name or "Unknown")
    if sf.get("lead"):
        return "Prospect (SF Lead only)", (sf["lead"] or {}).get("Company") or "Unknown"
    if sf.get("case"):
        return "Open SF Case", "Unknown"
    return "Unknown / Not in systems", "Unknown"


def collect_queue(api_key: str, queue: VettingQueue, re_vet: bool) -> list[dict]:
    seen: set[int] = set()
    items: list[dict] = []
    for summary in search_all(api_key, queue.query):
        tid = int(summary["id"])
        if tid in seen:
            continue
        seen.add(tid)
        if not re_vet and "sp-vetted" in (summary.get("tags") or []):
            continue
        if VOICEMAIL_RE.search(summary.get("subject") or ""):
            continue
        ticket = get_ticket(api_key, tid)
        if queue.recipient_gate and not passes_recipient_gate(ticket, queue.recipient_gate):
            continue
        entities = extract_company(ticket)
        gw = gateway_find_sp(entities)
        sf = salesforce_search(entities)
        post, cf_target = posture(gw, sf)
        if entities.get("cf_sp_current") not in (None, "", "Unknown") and post == "Unknown / Not in systems":
            cf_target = "(keep existing)"
        items.append(
            {
                "ticket_id": tid,
                "queue": queue.key,
                "inbox_label": queue.inbox_label,
                "subject": summary.get("subject"),
                "company": entities["company"],
                "contact_name": entities["contact_name"],
                "ks_number": entities["ks_number"],
                "sr_number": entities["sr_number"],
                "requester": entities["requester_email"],
                "cf_sp_current": entities["cf_sp_current"],
                "posture": post,
                "cf_sp_target": cf_target,
                "gateway_sp": gw,
                "sf_lead": sf.get("lead"),
                "sf_case": sf.get("case"),
                "errors": sf.get("errors", []),
            }
        )
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run sp-inbound-vetting batch")
    parser.add_argument(
        "--queue",
        default="all",
        help="ksonboarding | invoice-concerns | aphelp | all (default: all)",
    )
    parser.add_argument("--re-vet", action="store_true", help="Include tickets already tagged sp-vetted")
    args = parser.parse_args()

    api = load_credentials()
    queues = resolve_queues(args.queue)
    all_items: list[dict] = []
    by_queue: dict[str, int] = {}
    for queue in queues:
        batch = collect_queue(api, queue, args.re_vet)
        by_queue[queue.key] = len(batch)
        all_items.extend(batch)

    deduped: list[dict] = []
    seen_ids: set[int] = set()
    for item in all_items:
        tid = int(item["ticket_id"])
        if tid in seen_ids:
            continue
        seen_ids.add(tid)
        deduped.append(item)

    out = {
        "mode": "dry-run",
        "queue": args.queue,
        "queues_scanned": [q.key for q in queues],
        "counts_by_queue": by_queue,
        "in_scope_count": len(deduped),
        "items": deduped,
    }
    out_path = SCRIPT_DIR.parent / ".tmp" / f"dry-run-{args.queue}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
