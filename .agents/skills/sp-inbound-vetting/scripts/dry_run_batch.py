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
from entity_extraction import (  # noqa: E402
    contact_search_name,
    company_search_variants,
    extract_body_company_mentions,
    extract_body_emails,
    extract_signature_company,
    extract_signature_contact_name,
    extract_subject_company,
    is_generic_mailbox_name,
    is_internal_email,
    is_probable_person_name,
    parse_sf_case_subject,
    pick_best_company,
    sanitize_company,
    is_valid_company_string,
    strip_company_suffix,
)
from gateway_vetting import gateway_find_sp, gateway_sr_invoice_status  # noqa: E402
from queue_config import VettingQueue, resolve_queues  # noqa: E402

DOMAIN = "vixxo-helpdesk.freshdesk.com"
VOICEMAIL_RE = re.compile(r"\bnew voicemail\b", re.I)
KS_RE = re.compile(r"\b(KS\d+)\b", re.I)
SP_HASH_RE = re.compile(r"#(\d{4,6})\b")
SR_RE = re.compile(r"\b(1-\d{9,10})\b")

INTERNAL_LEAD_COMPANIES = frozenset({"vixxo", "knowledge sync", "knowledge sync inc"})


def _normalize_company_key(name: str) -> str:
    key = strip_company_suffix(name or "").lower()
    key = re.sub(r"[^\w\s]", "", key)
    return re.sub(r"\s+", " ", key).strip()


def _companies_materially_differ(a: str, b: str) -> bool:
    if not a or not b or a in ("Not stated", "") or b in ("Not stated", ""):
        return False
    ka = _normalize_company_key(a)
    kb = _normalize_company_key(b)
    if not ka or not kb:
        return True
    if ka == kb or ka in kb or kb in ka:
        return False
    if set(ka.split()) & set(kb.split()):
        return False
    return True


def _is_stale_internal_lead(lead: dict | None, extracted_company: str) -> bool:
    if not lead:
        return False
    lead_co = (lead.get("Company") or "").strip()
    if lead_co.lower() not in INTERNAL_LEAD_COMPANIES:
        return False
    return _companies_materially_differ(lead_co, extracted_company)


def _account_aligns_with_company(account: dict | None, company: str) -> bool:
    if not account or company in ("Not stated", ""):
        return False
    return not _companies_materially_differ(account.get("Name") or "", company)


def _cf_from_sf_account(account: dict) -> str:
    sp_num = str(account.get("Service_Provider_Number__c") or "").strip()
    acct_name = (account.get("Name") or "").strip()
    if sp_num and acct_name:
        return f"{sp_num} - {acct_name}"
    return sp_num or acct_name or "Unknown"


def _cf_from_sf_case(case: dict, account: dict | None, entities: dict) -> str:
    parsed = parse_sf_case_subject(case.get("Subject") or "")
    ks = parsed.get("ks_number") or entities.get("ks_number")
    company = parsed.get("company") or entities.get("company")
    if account and (account.get("Service_Provider_Number__c") or account.get("Name")):
        return _cf_from_sf_account(account)
    if ks and company and company not in ("Not stated", ""):
        return f"{ks} - {company}"
    if company and company not in ("Not stated", "") and is_valid_company_string(str(company)):
        return str(company)
    return "Unknown"


def apply_sf_case_entities(entities: dict, sf: dict) -> None:
    case = sf.get("case")
    if not case:
        return
    parsed = parse_sf_case_subject(case.get("Subject") or "")
    if parsed.get("ks_number") and not entities.get("ks_number"):
        entities["ks_number"] = parsed["ks_number"]
    case_company = parsed.get("company")
    if not case_company:
        return
    current = entities.get("company") or ""
    if current in ("Not stated", "") or not is_valid_company_string(str(current)):
        entities["company"] = case_company


def apply_sf_account_sp_number(entities: dict, sf: dict) -> None:
    account = sf.get("account")
    if not account:
        return
    sp_num = str(account.get("Service_Provider_Number__c") or "").strip()
    if sp_num and not entities.get("ks_number"):
        entities["ks_number"] = sp_num


def resolve_vetting(entities: dict) -> tuple[dict | None, dict, dict]:
    """Salesforce lookup, entity enrichment, and Gateway SP resolution."""
    sf = salesforce_search(entities)
    if _is_stale_internal_lead(sf.get("lead"), entities.get("company") or ""):
        sf = {**sf, "lead": None}
    apply_sf_case_entities(entities, sf)
    gw = gateway_find_sp(entities)
    if not gw:
        apply_sf_account_sp_number(entities, sf)
        gw = gateway_find_sp(entities)
    return gw, sf, entities


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
    company_candidates: list[str] = []

    subject_company = extract_subject_company(subject)
    if subject_company:
        company_candidates.append(subject_company)

    patterns = [
        r"COI - (.+?) - Vixxo",
        r"Your service with[\s\u00a0]*(.+?)[\s\u00a0]*-",
        r"^(KS\d+)\s*-",
        r"from (.+?) via",
        r"Onboarding setup for (.+?)$",
        r"receipt from (.+?)(?:\.|$)",
        r"FlyLock Security Solutions",
        r"Invoice (.+?) from",
        r"Invoice \d+ from (.+)$",
        r"Your Invoice from (.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, subject, re.I)
        if m:
            hit = m.group(1).strip() if m.lastindex else m.group(0).strip()
            hit = sanitize_company(hit)
            if hit:
                company_candidates.append(hit)
            break

    company_candidates.extend(extract_body_company_mentions(desc))

    signature_company = extract_signature_company(desc, email)
    if signature_company:
        company_candidates.append(signature_company)

    company = pick_best_company(company_candidates, email)
    if company:
        company = re.sub(r"\s*[-–—]\s*KS\d+\s*$", "", company, flags=re.I).strip()
        company = re.sub(r"\s*,?\s*#\d{4,6}\s*$", "", company).strip()
        company = re.sub(r"\s*-\s*KS\d+\s*$", "", company, flags=re.I).strip()
    company = sanitize_company(company) or (company if company and is_valid_company_string(company) else None)

    if not company and cf_sp and cf_sp not in ("Unknown", "") and is_valid_company_string(str(cf_sp)):
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

    signature_contact_name = extract_signature_contact_name(desc)
    contact_emails = extract_body_emails(desc, email)
    vetting_contact_name = contact_search_name(contact_name, signature_contact_name)
    if not company and signature_company:
        company = signature_company
    elif signature_company and is_generic_mailbox_name(contact_name):
        company = signature_company

    if (
        not company
        and contact_name
        and not is_generic_mailbox_name(contact_name)
        and not is_probable_person_name(contact_name)
    ):
        company = contact_name

    ks_match = KS_RE.search(f"{subject} {desc} {company or ''} {cf_sp or ''}")
    ks_number = ks_match.group(1).upper() if ks_match else None
    if not ks_number:
        hash_match = SP_HASH_RE.search(f"{subject} {desc} {company or ''} {cf_sp or ''}")
        if hash_match:
            ks_number = f"KS{hash_match.group(1)}"

    if company:
        company = re.sub(r"\s*[-–—]\s*KS\d+\s*$", "", company, flags=re.I).strip()
        company = re.sub(r"\s*,?\s*#\d{4,6}\s*$", "", company).strip()
        company = sanitize_company(company) or (
            company if is_valid_company_string(company) else None
        )

    sr_match = SR_RE.search(f"{subject} {desc}")

    return {
        "company": company or "Not stated",
        "signature_company": signature_company,
        "contact_name": contact_name or "Not stated",
        "signature_contact_name": signature_contact_name,
        "vetting_contact_name": vetting_contact_name or "Not stated",
        "contact_emails": contact_emails,
        "ks_number": ks_number,
        "sr_number": sr_match.group(1) if sr_match else None,
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
    out: dict = {"lead": None, "case": None, "contact": None, "account": None, "errors": []}
    company = entities.get("company") or ""
    email = entities.get("requester_email") or ""
    contact_name = entities.get("vetting_contact_name") or entities.get("contact_name") or ""
    contact_emails = [
        addr.lower()
        for addr in (entities.get("contact_emails") or [])
        if addr and not is_internal_email(addr)
    ]
    if email and email != "Not stated" and not is_internal_email(email):
        lower = email.lower()
        if lower not in contact_emails:
            contact_emails = [lower] + contact_emails

    def _first_records(records: list[dict]) -> list[dict]:
        if records and records[0].get("_error"):
            out["errors"].append(records[0]["_error"])
            return []
        return records

    def _lead_by_email(addr: str) -> dict | None:
        esc = addr.replace("'", "\\'")
        rows = _first_records(
            sf_query(
                "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
                f"WHERE Email = '{esc}' ORDER BY LastModifiedDate DESC LIMIT 3"
            )
        )
        return rows[0] if rows else None

    def _contact_by_email(addr: str) -> dict | None:
        esc = addr.replace("'", "\\'")
        rows = _first_records(
            sf_query(
                "SELECT Id, Name, Email, AccountId FROM Contact "
                f"WHERE Email = '{esc}' LIMIT 3"
            )
        )
        return rows[0] if rows else None

    def _case_by_email(addr: str) -> dict | None:
        esc = addr.replace("'", "\\'")
        rows = _first_records(
            sf_query(
                "SELECT Id, CaseNumber, Subject, Status FROM Case "
                f"WHERE ContactEmail = '{esc}' ORDER BY CreatedDate DESC LIMIT 3"
            )
        )
        return rows[0] if rows else None

    # Email-first: every requester + signature/body address.
    for addr in contact_emails:
        if out.get("lead"):
            break
        out["lead"] = _lead_by_email(addr)

    for addr in contact_emails:
        if out.get("contact"):
            break
        out["contact"] = _contact_by_email(addr)

    for addr in contact_emails:
        if out.get("case"):
            break
        out["case"] = _case_by_email(addr)

    # Corporate email domain → Lead rows on same domain.
    if not out.get("lead"):
        from entity_extraction import email_domain_search_tokens  # noqa: WPS433

        seen_domains: set[str] = set()
        for addr in contact_emails:
            for token in email_domain_search_tokens(addr):
                if token in seen_domains:
                    continue
                seen_domains.add(token)
                esc = token.replace("'", "\\'")
                rows = _first_records(
                    sf_query(
                        "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
                        f"WHERE Email LIKE '%@{esc}' OR Email LIKE '%@{esc}.%' "
                        f"ORDER BY LastModifiedDate DESC LIMIT 3"
                    )
                )
                if rows:
                    out["lead"] = rows[0]
                    break
            if out.get("lead"):
                break

    if company != "Not stated" and not out.get("lead"):
        seen_company: set[str] = set()
        for variant in company_search_variants(company):
            key = variant.lower()
            if key in seen_company:
                continue
            seen_company.add(key)
            esc = variant.replace("'", "\\'")
            leads = _first_records(
                sf_query(
                    "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
                    f"WHERE Company LIKE '%{esc}%' ORDER BY LastModifiedDate DESC LIMIT 3"
                )
            )
            if leads:
                out["lead"] = leads[0]
                break

    if contact_name not in ("Not stated", "") and not out.get("lead"):
        esc = contact_name.replace("'", "\\'")
        leads = _first_records(
            sf_query(
                "SELECT Id, Name, Company, Status, Email, LastModifiedDate FROM Lead "
                f"WHERE Name LIKE '%{esc}%' ORDER BY LastModifiedDate DESC LIMIT 3"
            )
        )
        if leads:
            out["lead"] = leads[0]

    if company != "Not stated" and not out.get("account"):
        seen_account: set[str] = set()
        for variant in company_search_variants(company):
            key = variant.lower()
            if key in seen_account:
                continue
            seen_account.add(key)
            esc = variant.replace("'", "\\'")
            accounts = _first_records(
                sf_query(
                    "SELECT Id, Name, Type, Service_Provider_Number__c FROM Account "
                    f"WHERE Name LIKE '%{esc}%' AND Type = 'Service Provider' "
                    f"ORDER BY LastModifiedDate DESC LIMIT 3"
                )
            )
            if accounts:
                out["account"] = accounts[0]
                break

    return out


def posture(gw: dict | None, sf: dict, entities: dict | None = None) -> tuple[str, str]:
    entities = entities or {}
    company = entities.get("company") or ""
    lead = sf.get("lead")
    account = sf.get("account")
    account_aligned = _account_aligns_with_company(account, company)

    if lead and _is_stale_internal_lead(lead, company):
        lead = None

    if gw and lead and not account_aligned:
        return "Known SP + SF Lead", f"{gw.get('sp_number')} - {gw.get('name')}"
    if gw:
        num, name = gw.get("sp_number"), gw.get("name")
        return "Known SP", f"{num} - {name}" if num else str(name or "Unknown")
    if lead and not account_aligned:
        return "Prospect (SF Lead only)", (lead or {}).get("Company") or "Unknown"
    if account_aligned and account:
        cf = _cf_from_sf_account(account)
        if sf.get("case"):
            return "Open SF Case", cf
        if company and is_valid_company_string(company):
            return "Unknown / Not in systems", cf
    if sf.get("case"):
        return "Open SF Case", _cf_from_sf_case(sf["case"], account, entities)
    if company and is_valid_company_string(company):
        return "Unknown / Not in systems", company
    return "Unknown / Not in systems", "Unknown"


def queue_search_query(
    queue: VettingQueue,
    created_after: str | None = None,
    created_before: str | None = None,
) -> str:
    q = queue.query
    if created_after:
        q = f"{q} AND created_at:>'{created_after}'"
    if created_before:
        q = f"{q} AND created_at:<'{created_before}'"
    return q


def collect_queue(api_key: str, queue: VettingQueue, re_vet: bool, created_after: str | None = None, created_before: str | None = None) -> list[dict]:
    seen: set[int] = set()
    items: list[dict] = []
    query = queue_search_query(queue, created_after, created_before)
    for summary in search_all(api_key, query):
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
        gw, sf, entities = resolve_vetting(entities)
        post, cf_target = posture(gw, sf, entities)
        if entities.get("cf_sp_current") not in (None, "", "Unknown") and post == "Unknown / Not in systems":
            current_cf = str(entities.get("cf_sp_current") or "")
            if is_valid_company_string(current_cf):
                cf_target = "(keep existing)"
            elif is_valid_company_string(str(cf_target)):
                pass  # overwrite invalid human/bot cf_sp with good extraction
            else:
                cf_target = "(keep existing)" if current_cf else "Unknown"
        item: dict = {
                "ticket_id": tid,
                "queue": queue.key,
                "inbox_label": queue.inbox_label,
                "subject": summary.get("subject"),
                "company": entities["company"],
                "signature_company": entities.get("signature_company"),
                "contact_name": entities["contact_name"],
                "vetting_contact_name": entities.get("vetting_contact_name"),
                "contact_emails": entities.get("contact_emails"),
                "ks_number": entities["ks_number"],
                "sr_number": entities["sr_number"],
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
        if queue.key == "invoice-concerns" and entities.get("sr_number"):
            sp_num = (gw or {}).get("sp_number") or entities.get("ks_number")
            item["gateway_sr_invoice"] = gateway_sr_invoice_status(
                entities["sr_number"],
                sp_number=sp_num,
            )
        items.append(item)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run sp-inbound-vetting batch")
    parser.add_argument(
        "--queue",
        default="all",
        help="ksonboarding | invoice-concerns | aphelp | all (default: all)",
    )
    parser.add_argument("--re-vet", action="store_true", help="Include tickets already tagged sp-vetted")
    parser.add_argument("--created-after", help="Freshdesk created_at lower bound YYYY-MM-DD")
    parser.add_argument("--created-before", help="Freshdesk created_at upper bound YYYY-MM-DD")
    args = parser.parse_args()

    api = load_credentials()
    queues = resolve_queues(args.queue)
    all_items: list[dict] = []
    by_queue: dict[str, int] = {}
    for queue in queues:
        batch = collect_queue(api, queue, args.re_vet, args.created_after, args.created_before)
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
