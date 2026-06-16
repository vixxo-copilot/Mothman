#!/usr/bin/env python3
"""Dry-run sp-inbound-vetting for KSOnboarding Freshdesk queue."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sp-voicemail-triage" / "scripts"))
from batch_process_freshdesk import (  # noqa: E402
    auth_headers,
    load_credentials,
    strip_html,
)

DOMAIN = "vixxo-helpdesk.freshdesk.com"
QUERY = "group_id:159000485013 AND status:2 AND type:'KSOnboarding'"
KSONBOARDING = "ksonboarding@vixxo.com"
VOICEMAIL_RE = re.compile(r"\bnew voicemail\b", re.I)
SP_NUM_RE = re.compile(r"\b(?:SP\s*#?\s*|SP-)(\d{4,8})\b", re.I)
SR_RE = re.compile(r"\b(?:SR|service request|work order)\s*#?\s*(\d{5,12})\b", re.I)
COMPANY_SUFFIXES = re.compile(r"\b(LLC|INC|CORP|CO\.|LTD|LP|LLP)\.?\b", re.I)


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


def recipient_matches_ksonboarding(ticket: dict) -> bool:
    blob_parts = [
        str(ticket.get("to_emails") or ""),
        str(ticket.get("cc_emails") or ""),
        ticket.get("description_text") or "",
        strip_html(ticket.get("description") or ""),
        str(ticket.get("support_email") or ""),
    ]
    blob = "\n".join(blob_parts).lower()
    return KSONBOARDING in blob or ticket.get("type") == "KSOnboarding"


def normalize_company(name: str | None) -> str:
    if not name:
        return ""
    s = re.sub(r"[^\w\s&'-]", " ", name or "")
    return re.sub(r"\s+", " ", s).strip()


def extract_entities(ticket: dict) -> dict:
    subject = ticket.get("subject") or ""
    desc = ticket.get("description_text") or strip_html(ticket.get("description") or "")
    blob = f"{subject}\n{desc}"
    requester = ticket.get("requester") or {}
    email = requester.get("email") or ticket.get("email") or ""
    name = requester.get("name") or ticket.get("name") or ""

    sp_num = None
    sm = SP_NUM_RE.search(blob)
    if sm:
        sp_num = sm.group(1)
    sr = None
    srm = SR_RE.search(blob)
    if srm:
        sr = srm.group(1)

    company = None
    # subject patterns
    for pat in [
        r"from\s+(.+?)\s+via",
        r"voicemail from\s+(.+?)\s+via",
        r"^(.+?)\s+-\s+",
    ]:
        m = re.search(pat, subject, re.I)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in {"wireless caller", "new voicemail"}:
                company = candidate
                break
    if not company and name and "@" not in name:
        company = name
    cf = ticket.get("custom_fields") or {}
    if not company and cf.get("cf_sp") and cf.get("cf_sp") not in {"Unknown", ""}:
        company = str(cf.get("cf_sp"))

    return {
        "company": company or "Not stated",
        "company_norm": normalize_company(company),
        "sp_number": sp_num,
        "sr_number": sr,
        "requester_name": name or "Not stated",
        "requester_email": email or "Not stated",
        "cf_sp_current": cf.get("cf_sp"),
        "tags": ticket.get("tags") or [],
    }


def sf_query(soql: str) -> list[dict]:
    cmd = ["sf", "data", "query", "--query", soql, "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        return [{"_error": "sf CLI not found"}]
    if proc.returncode != 0:
        return [{"_error": proc.stderr.strip() or proc.stdout.strip()}]
    try:
        payload = json.loads(proc.stdout)
        return payload.get("result", {}).get("records", [])
    except json.JSONDecodeError:
        return [{"_error": proc.stdout[:500]}]


def gateway_list_providers() -> list[dict]:
    """Best-effort via npx/mcp not available — return empty; caller uses SP# path."""
    return []


def vet_item(entities: dict) -> dict:
    result = {
        "gateway_sp": None,
        "sf_lead": None,
        "sf_case": None,
        "sf_account": None,
        "posture": "Unknown / Not in systems",
        "cf_sp_target": "Unknown",
        "errors": [],
    }

    company = entities["company_norm"]
    email = entities["requester_email"]
    phone_digits = re.sub(r"\D", "", entities.get("phone") or "")[-10:]

    # Salesforce Lead
    if company and company != "Not stated":
        esc = company.replace("'", "\\'")
        leads = sf_query(
            "SELECT Id, Name, Company, Status, Phone, Email, LastModifiedDate "
            f"FROM Lead WHERE Company LIKE '%{esc}%' OR Name LIKE '%{esc}%' "
            "ORDER BY LastModifiedDate DESC LIMIT 5"
        )
        if leads and not leads[0].get("_error"):
            result["sf_lead"] = leads[0]
        elif leads and leads[0].get("_error"):
            result["errors"].append(f"SF Lead: {leads[0]['_error'][:200]}")
    if email and email != "Not stated" and not result["sf_lead"]:
        esc_email = email.replace("'", "\\'")
        leads = sf_query(
            "SELECT Id, Name, Company, Status, Phone, Email, LastModifiedDate "
            f"FROM Lead WHERE Email = '{esc_email}' "
            "ORDER BY LastModifiedDate DESC LIMIT 3"
        )
        if leads and not leads[0].get("_error"):
            result["sf_lead"] = leads[0]

    # Salesforce Case
    if email and email != "Not stated":
        esc_email = email.replace("'", "\\'")
        cases = sf_query(
            "SELECT Id, CaseNumber, Subject, Status, ContactEmail, CreatedDate "
            f"FROM Case WHERE ContactEmail = '{esc_email}' "
            "ORDER BY CreatedDate DESC LIMIT 3"
        )
        if cases and not cases[0].get("_error"):
            result["sf_case"] = cases[0]
        elif cases and cases[0].get("_error") and "SF Lead" not in str(result["errors"]):
            result["errors"].append(f"SF Case: {cases[0]['_error'][:200]}")

    # Salesforce Account
    if company and company != "Not stated":
        esc = company.replace("'", "\\'")
        accounts = sf_query(
            f"SELECT Id, Name, Type, Phone FROM Account WHERE Name LIKE '%{esc}%' LIMIT 3"
        )
        if accounts and not accounts[0].get("_error"):
            result["sf_account"] = accounts[0]

    # Gateway via sf is N/A — try sf org only for now; gateway noted separately
    sp_num = entities.get("sp_number")
    gateway_note = "Gateway MCP unavailable in this run — SP# path not resolved via API"
    if sp_num:
        gateway_note = f"SP# {sp_num} cited in ticket — Gateway lookup pending MCP"
        result["gateway_sp"] = {"sp_number": sp_num, "name": None, "match": "Possible"}
        result["posture"] = "Known SP (SP# cited, name unverified)"
        result["cf_sp_target"] = f"{sp_num} - (verify in Gateway)"

    if result["sf_lead"] and result["gateway_sp"]:
        result["posture"] = "Known SP + SF Lead"
    elif result["sf_lead"] and not result["gateway_sp"]:
        result["posture"] = "Prospect (SF Lead only)"
        lead_co = result["sf_lead"].get("Company") or entities["company"]
        result["cf_sp_target"] = lead_co if lead_co != "Not stated" else "Unknown"
    elif result["sf_case"]:
        result["posture"] = "Open SF Case"
        result["cf_sp_target"] = entities["company"] if entities["company"] != "Not stated" else "Unknown"
    elif result["gateway_sp"]:
        pass
    else:
        result["cf_sp_target"] = "Unknown" if not entities.get("cf_sp_current") else "(keep existing)"

    result["gateway_note"] = gateway_note
    return result


def main() -> int:
    api = load_credentials()
    tickets = search_all(api, QUERY)
    skipped = {"voicemail": [], "sp_vetted": [], "not_ksonboarding": []}
    in_scope: list[dict] = []

    for summary in tickets:
        tid = int(summary["id"])
        if "sp-vetted" in (summary.get("tags") or []):
            skipped["sp_vetted"].append(tid)
            continue
        if VOICEMAIL_RE.search(summary.get("subject") or ""):
            skipped["voicemail"].append(tid)
            continue
        ticket = get_ticket(api, tid)
        if not recipient_matches_ksonboarding(ticket):
            skipped["not_ksonboarding"].append(tid)
            continue
        entities = extract_entities(ticket)
        vet = vet_item(entities)
        in_scope.append(
            {
                "ticket_id": tid,
                "subject": summary.get("subject"),
                "created_at": summary.get("created_at"),
                "requester": entities["requester_email"],
                "company": entities["company"],
                "sp_number_extracted": entities["sp_number"],
                "sr_number": entities["sr_number"],
                "cf_sp_current": entities["cf_sp_current"],
                "tags": entities["tags"],
                "posture": vet["posture"],
                "cf_sp_target": vet["cf_sp_target"],
                "gateway_sp": vet["gateway_sp"],
                "sf_lead": (
                    {
                        "Id": vet["sf_lead"].get("Id"),
                        "Company": vet["sf_lead"].get("Company"),
                        "Status": vet["sf_lead"].get("Status"),
                    }
                    if vet["sf_lead"]
                    else None
                ),
                "sf_case": (
                    {
                        "Id": vet["sf_case"].get("Id"),
                        "CaseNumber": vet["sf_case"].get("CaseNumber"),
                        "Subject": vet["sf_case"].get("Subject"),
                        "Status": vet["sf_case"].get("Status"),
                    }
                    if vet["sf_case"]
                    else None
                ),
                "sf_account": (
                    {"Id": vet["sf_account"].get("Id"), "Name": vet["sf_account"].get("Name")}
                    if vet["sf_account"]
                    else None
                ),
                "errors": vet["errors"],
                "gateway_note": vet["gateway_note"],
                "dry_run_actions": {
                    "internal_note": "would post",
                    "cf_sp_update": vet["cf_sp_target"],
                    "tags": ["sp-vetted"],
                    "sf_lead_task": "would post" if vet["sf_lead"] else "N/A",
                    "sf_case_task": "would post" if vet["sf_case"] else "N/A",
                },
            }
        )

    out = {
        "mode": "dry-run",
        "queue": "KSOnboarding",
        "query": QUERY,
        "total_open_ks_onboarding": len(tickets),
        "in_scope_count": len(in_scope),
        "skipped": {k: {"count": len(v), "ids": v[:20]} for k, v in skipped.items()},
        "items": in_scope,
    }
    out_path = Path(__file__).resolve().parent.parent / ".tmp" / "dry-run-ksonboarding.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
