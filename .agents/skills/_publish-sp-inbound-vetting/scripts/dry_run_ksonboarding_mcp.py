#!/usr/bin/env python3
"""Dry-run sp-inbound-vetting for KSOnboarding with Gateway + Salesforce MCP/CLI."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import auth_headers, load_credentials, strip_html  # noqa: E402
from mcp_http import mcp_call, mcp_result_text  # noqa: E402

DOMAIN = "vixxo-helpdesk.freshdesk.com"
QUERY = "group_id:159000485013 AND status:2 AND type:'KSOnboarding'"
GATEWAY_URL = "https://vixxonow.com/mcp/gateway"
VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"
VOICEMAIL_RE = re.compile(r"\bnew voicemail\b", re.I)
KS_RE = re.compile(r"\b(KS\d+)\b", re.I)
SR_RE = re.compile(r"\b(1-\d{9,10})\b")


def search_all(api_key: str, query: str) -> list[dict]:
    results: list[dict] = []
    for page in range(1, 11):
        params = {"query": f'"{query}"', "page": str(page)}
        url = f"https://{DOMAIN}/api/v2/search/tickets?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        page_results = data.get("results") or []
        results.extend(page_results)
        if len(page_results) < 30:
            break
    return results


def get_ticket(api_key: str, ticket_id: int) -> dict:
    url = f"https://{DOMAIN}/api/v2/tickets/{ticket_id}?include=requester"
    req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def extract_company(ticket: dict) -> dict:
    subject = ticket.get("subject") or ""
    desc = ticket.get("description_text") or strip_html(ticket.get("description") or "")
    requester = ticket.get("requester") or {}
    email = requester.get("email") or ""
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
    if not company and "ashleymechanical.com" in email.lower():
        company = "Ashley Mechanical"
    if not company and "glassdoctor" in email.lower():
        company = "Glass Doctor"
    if not company and "golterman.com" in email.lower():
        company = "Golterman and Sabo"
    if not company and "fastsigns.com" in email.lower():
        company = "FastSigns"
    if not company and "e3construction.net" in email.lower():
        company = "E3 Construction"

    ks = KS_RE.search(f"{subject} {cf_sp or ''}")
    sr = SR_RE.search(f"{subject} {desc}")

    return {
        "company": company or "Not stated",
        "ks_number": ks.group(1).upper() if ks else None,
        "sr_number": sr.group(1) if sr else None,
        "requester_email": email or "Not stated",
        "cf_sp_current": cf_sp,
    }


def sf_query(soql: str) -> list[dict]:
    import os
    from pathlib import Path

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
            payload = json.loads(proc.stdout)
            return payload.get("result", {}).get("records", [])
        except json.JSONDecodeError:
            continue
    return [{"_error": "Salesforce CLI unavailable — enable salesforce MCP or run sf org login web"}]


def parse_json_blob(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}|\[.*\]", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def gateway_find_sp(entities: dict) -> dict | None:
    ks = entities.get("ks_number")
    sr = entities.get("sr_number")
    company = entities.get("company") or ""

    if sr:
        for url, tool in ((VIXXOLINK_URL, "vixxolink_resolve_service_request"), (GATEWAY_URL, "gateway_get_service_request")):
            args = {"service_request_number": sr, "number": sr, "sr_number": sr}
            resp = mcp_call(url, tool, args)
            text = mcp_result_text(resp)
            data = parse_json_blob(text)
            if isinstance(data, dict):
                sp_num = (
                    data.get("serviceProviderNumber")
                    or data.get("spNumber")
                    or data.get("providerNumber")
                    or (data.get("serviceProvider") or {}).get("number")
                )
                sp_name = (
                    data.get("serviceProviderName")
                    or (data.get("serviceProvider") or {}).get("name")
                    or data.get("providerName")
                )
                if sp_num or sp_name:
                    return {"sp_number": sp_num, "name": sp_name, "source": f"{tool}({sr})"}

    if ks:
        resp = mcp_call(GATEWAY_URL, "gateway_swm_get_provider", {"provider_number": ks, "sp_number": ks})
        text = mcp_result_text(resp)
        data = parse_json_blob(text)
        if isinstance(data, dict) and data:
            name = data.get("name") or data.get("displayName") or data.get("providerName")
            num = data.get("number") or data.get("providerNumber") or ks
            return {"sp_number": num, "name": name, "source": "gateway_swm_get_provider"}

    if company and company != "Not stated":
        resp = mcp_call(GATEWAY_URL, "gateway_swm_list_providers", {})
        text = mcp_result_text(resp)
        data = parse_json_blob(text)
        rows = data if isinstance(data, list) else (data or {}).get("providers") or (data or {}).get("items") or []
        norm = re.sub(r"[^\w\s]", "", company.lower())
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("displayName") or "")
            if norm and norm in re.sub(r"[^\w\s]", "", name.lower()):
                return {
                    "sp_number": row.get("number") or row.get("providerNumber"),
                    "name": name,
                    "source": "gateway_swm_list_providers",
                }
    return None


def salesforce_search(entities: dict) -> dict:
    out: dict = {"lead": None, "case": None, "account": None, "errors": []}
    company = entities.get("company") or ""
    email = entities.get("requester_email") or ""

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

    if email not in ("Not stated", "") and not out["lead"]:
        esc = email.replace("'", "\\'")
        leads = sf_query(
            "SELECT Id, Name, Company, Status, Email FROM Lead "
            f"WHERE Email = '{esc}' LIMIT 3"
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
        co = (sf["lead"] or {}).get("Company") or "Unknown"
        return "Prospect (SF Lead only)", co
    if sf.get("case"):
        return "Open SF Case", "Unknown"
    return "Unknown / Not in systems", "Unknown"


def main() -> int:
    api = load_credentials()
    tickets = search_all(api, QUERY)
    items: list[dict] = []
    mcp_health = mcp_call(GATEWAY_URL, "gateway_swm_list_providers", {})

    for summary in tickets:
        tid = int(summary["id"])
        if "sp-vetted" in (summary.get("tags") or []):
            continue
        if VOICEMAIL_RE.search(summary.get("subject") or ""):
            continue
        ticket = get_ticket(api, tid)
        entities = extract_company(ticket)
        gw = gateway_find_sp(entities)
        sf = salesforce_search(entities)
        post, cf_target = posture(gw, sf)
        if entities.get("cf_sp_current") not in (None, "", "Unknown") and post == "Unknown / Not in systems":
            cf_target = "(keep existing)"

        items.append(
            {
                "ticket_id": tid,
                "subject": summary.get("subject"),
                "company": entities["company"],
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

    out = {
        "mode": "dry-run",
        "queue": "KSOnboarding",
        "mcp_gateway_probe": mcp_result_text(mcp_health)[:300],
        "in_scope_count": len(items),
        "items": items,
    }
    out_path = SCRIPT_DIR.parent / ".tmp" / f"dry-run-ksonboarding-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
