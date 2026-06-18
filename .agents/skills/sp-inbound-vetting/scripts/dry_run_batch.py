#!/usr/bin/env python3
"""Dry-run sp-inbound-vetting for configured Freshdesk queues."""

from __future__ import annotations

import argparse
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
from entity_match import (  # noqa: E402
    FUZZY_THRESHOLD,
    company_similarity,
    contact_name_similarity,
    is_exact_company_match,
    match_confidence,
    normalize_company,
)
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
        cmd = [sf_bin, "data", "query", "--query", soql, "--target-org", "vixxo", "--json"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
        except FileNotFoundError:
            continue
        if proc.returncode != 0 or not proc.stdout:
            continue
        try:
            return json.loads(proc.stdout).get("result", {}).get("records", [])
        except json.JSONDecodeError:
            continue
    return [{"_error": "Salesforce CLI unavailable"}]


def _annotate_sf_record(record: dict, *, match_type: str, confidence: str, score: float) -> dict:
    out = dict(record)
    out["match_type"] = match_type
    out["confidence"] = confidence
    out["match_score"] = round(score, 3)
    return out


def _company_search_tokens(company: str) -> list[str]:
    norm = normalize_company(company)
    tokens = [t for t in norm.split() if len(t) >= 3]
    if not tokens:
        return [company.strip()]
    # Prefer longest token for broader SOQL, plus full normalized string.
    tokens.sort(key=len, reverse=True)
    return list(dict.fromkeys(tokens[:3]))


def _rank_sf_leads(
    leads: list[dict],
    *,
    company: str,
    contact_name: str,
    email: str,
) -> list[tuple[dict, float, str]]:
    """Return (lead, score, match_kind) sorted by priority then score."""
    ranked: list[tuple[dict, float, str]] = []
    for lead in leads:
        if lead.get("_error"):
            continue
        lead_email = str(lead.get("Email") or "").lower()
        if email not in ("Not stated", "") and lead_email == email.lower():
            ranked.append((lead, 1.0, "email"))
            continue
        lead_company = str(lead.get("Company") or "")
        if company not in ("Not stated", "") and lead_company:
            score = company_similarity(company, lead_company)
            kind = "company_exact" if is_exact_company_match(company, lead_company) else "company_fuzzy"
            if score >= FUZZY_THRESHOLD:
                ranked.append((lead, score, kind))
                continue
        lead_name = str(lead.get("Name") or "")
        if contact_name not in ("Not stated", "") and lead_name:
            score = contact_name_similarity(contact_name, lead_name)
            if score >= FUZZY_THRESHOLD:
                ranked.append((lead, score, "name_fuzzy"))
                continue
        if company not in ("Not stated", "") and lead_name:
            score = company_similarity(company, lead_name)
            if score >= FUZZY_THRESHOLD:
                ranked.append((lead, score, "company_fuzzy"))
    kind_order = {"email": 0, "company_exact": 1, "company_fuzzy": 2, "name_fuzzy": 3}
    ranked.sort(key=lambda x: (kind_order.get(x[2], 9), -x[1]))
    return ranked


def salesforce_search(entities: dict) -> dict:
    out: dict = {"lead": None, "case": None, "errors": []}
    company = entities.get("company") or ""
    email = entities.get("requester_email") or ""
    contact_name = entities.get("contact_name") or ""

    lead_candidates: list[dict] = []
    if company != "Not stated":
        for token in _company_search_tokens(company):
            esc = token.replace("'", "\\'")
            leads = sf_query(
                "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
                f"WHERE Company LIKE '%{esc}%' OR Name LIKE '%{esc}%' "
                "ORDER BY LastModifiedDate DESC LIMIT 10"
            )
            if leads and leads[0].get("_error"):
                out["errors"].append(leads[0]["_error"])
            else:
                lead_candidates.extend(leads)

    if contact_name not in ("Not stated", ""):
        esc = contact_name.replace("'", "\\'")
        leads = sf_query(
            "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
            f"WHERE Name LIKE '%{esc}%' ORDER BY LastModifiedDate DESC LIMIT 10"
        )
        if leads and leads[0].get("_error"):
            out["errors"].append(leads[0]["_error"])
        else:
            lead_candidates.extend(leads)

    if email not in ("Not stated", ""):
        esc = email.replace("'", "\\'")
        leads = sf_query(
            f"SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead WHERE Email = '{esc}' LIMIT 3"
        )
        if leads and leads[0].get("_error"):
            out["errors"].append(leads[0]["_error"])
        else:
            lead_candidates.extend(leads)

    seen_ids: set[str] = set()
    deduped: list[dict] = []
    for lead in lead_candidates:
        lid = lead.get("Id")
        if not lid or lid in seen_ids:
            continue
        seen_ids.add(lid)
        deduped.append(lead)

    ranked = _rank_sf_leads(deduped, company=company, contact_name=contact_name, email=email)
    if ranked:
        best, score, kind = ranked[0]
        exact = kind in ("email", "company_exact")
        out["lead"] = _annotate_sf_record(
            best,
            match_type="exact" if exact else "fuzzy",
            confidence=match_confidence(exact, score),
            score=score,
        )
        alternates = []
        for alt, alt_score, alt_kind in ranked[1:4]:
            if alt_score >= FUZZY_THRESHOLD:
                alternates.append(
                    {
                        "Id": alt.get("Id"),
                        "Company": alt.get("Company"),
                        "Name": alt.get("Name"),
                        "match_score": round(alt_score, 3),
                        "match_kind": alt_kind,
                    }
                )
        if alternates:
            out["lead_alternates"] = alternates

    if email not in ("Not stated", ""):
        esc = email.replace("'", "\\'")
        cases = sf_query(
            "SELECT Id, CaseNumber, Subject, Status FROM Case "
            f"WHERE ContactEmail = '{esc}' ORDER BY CreatedDate DESC LIMIT 3"
        )
        if cases and not cases[0].get("_error"):
            out["case"] = _annotate_sf_record(
                cases[0], match_type="exact", confidence="High", score=1.0
            )
        elif cases and cases[0].get("_error"):
            out["errors"].append(cases[0]["_error"])

    if not out.get("case") and company != "Not stated":
        esc = company.replace("'", "\\'")
        cases = sf_query(
            "SELECT Id, CaseNumber, Subject, Status FROM Case "
            f"WHERE Subject LIKE '%{esc}%' ORDER BY CreatedDate DESC LIMIT 5"
        )
        if cases and not cases[0].get("_error"):
            best_case = None
            best_score = 0.0
            for case in cases:
                score = company_similarity(company, str(case.get("Subject") or ""))
                if score > best_score:
                    best_score = score
                    best_case = case
            if best_case and best_score >= FUZZY_THRESHOLD:
                exact = is_exact_company_match(company, str(best_case.get("Subject") or ""))
                out["case"] = _annotate_sf_record(
                    best_case,
                    match_type="exact" if exact else "fuzzy",
                    confidence=match_confidence(exact, best_score),
                    score=best_score,
                )

    return out


def posture(gw: dict | None, sf: dict) -> tuple[str, str, str]:
    """Return (posture, cf_sp_target, confidence)."""
    gw_fuzzy = gw and gw.get("match_type") == "fuzzy"
    sf_lead = sf.get("lead")
    sf_fuzzy = sf_lead and sf_lead.get("match_type") == "fuzzy"

    if gw and sf_lead and not gw_fuzzy:
        return "Known SP + SF Lead", f"{gw.get('sp_number')} - {gw.get('name')}", "High"
    if gw and sf_lead and gw_fuzzy:
        return "Possible SP (Gateway) + SF Lead", f"{gw.get('sp_number')} - {gw.get('name')}", "Medium"
    if gw and not gw_fuzzy:
        num, name = gw.get("sp_number"), gw.get("name")
        return "Known SP", f"{num} - {name}" if num else str(name or "Unknown"), gw.get("confidence", "High")
    if gw and gw_fuzzy:
        num, name = gw.get("sp_number"), gw.get("name")
        return "Possible SP (Gateway)", f"{num} - {name}" if num else str(name or "Unknown"), "Medium"
    if sf_lead and not sf_fuzzy:
        return "Prospect (SF Lead only)", (sf_lead or {}).get("Company") or "Unknown", "High"
    if sf_lead and sf_fuzzy:
        return "Prospect (SF Lead — possible match)", (sf_lead or {}).get("Company") or "Unknown", "Medium"
    if sf.get("case"):
        case_conf = (sf["case"] or {}).get("confidence", "High")
        label = "Open SF Case" if case_conf == "High" else "Open SF Case (possible match)"
        return label, "Unknown", case_conf
    return "Unknown / Not in systems", "Unknown", "Low"


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
        post, cf_target, confidence = posture(gw, sf)
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
                "confidence": confidence,
                "cf_sp_target": cf_target,
                "gateway_sp": gw,
                "sf_lead": sf.get("lead"),
                "sf_lead_alternates": sf.get("lead_alternates"),
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
