"""Account preflight audit for sf-case-email-sync (Phase 1 — audit only)."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

VETTING_DIR = Path(__file__).resolve().parents[2] / "sp-inbound-vetting" / "scripts"
sys.path.insert(0, str(VETTING_DIR))

from dry_run_batch import posture, salesforce_search  # noqa: E402
from entity_extraction import (  # noqa: E402
    extract_body_company_mentions,
    extract_body_emails,
    extract_signature_company,
    extract_subject_company,
    is_valid_company_string,
    pick_best_company,
    sanitize_company,
)
from gateway_vetting import gateway_find_sp, gateway_health_check  # noqa: E402
from sf_case_account import (  # noqa: E402
    PLACEHOLDER_ACCOUNT_IDS,
    account_label,
    should_update_case_account,
)

SR_RE = re.compile(r"\b(1-\d{10})\b")
KS_RE = re.compile(r"\b(KS\d+)\b", re.I)
SP_HASH_RE = re.compile(r"#(\d{4,6})\b")


def extract_case_entities(case: dict) -> dict[str, Any]:
    subject = case.get("Subject") or ""
    desc = case.get("Description") or ""
    blob = f"{subject}\n{desc}"
    email = (case.get("ContactEmail") or case.get("SuppliedEmail") or "").strip().lower()
    contact_emails = extract_body_emails(desc, email)

    company_candidates: list[str] = []
    subject_company = extract_subject_company(subject)
    if subject_company:
        company_candidates.append(subject_company)
    company_candidates.extend(extract_body_company_mentions(desc))
    signature_company = extract_signature_company(desc, email)
    if signature_company:
        company_candidates.append(signature_company)

    if not company_candidates and contact_emails:
        for addr in contact_emails:
            domain = addr.split("@", 1)[-1].split(".")[0]
            if len(domain) >= 4 and domain not in {"louisianashuttersblindsandshades"}:
                token = domain.replace("-", " ").title()
                if is_valid_company_string(token):
                    company_candidates.append(token)

    for pat in (
        r"^KS\d+\s*[-–—]\s*(.+)$",
        r"^(.+?)\s*[-–—]\s*KS\d+",
    ):
        match = re.search(pat, subject, re.I)
        if match:
            hit = sanitize_company(match.group(1))
            if hit:
                company_candidates.append(hit)

    company = pick_best_company(company_candidates, email) or "Not stated"
    if company != "Not stated" and not is_valid_company_string(company):
        company = "Not stated"
    if company != "Not stated" and SR_RE.search(company):
        company = "Not stated"

    ks_number = None
    ks_match = KS_RE.search(blob)
    if ks_match:
        ks_number = ks_match.group(1).upper()
    if not ks_number:
        hash_match = SP_HASH_RE.search(blob)
        if hash_match:
            ks_number = f"KS{hash_match.group(1)}"

    sr_match = SR_RE.search(blob)

    return {
        "company": company or "Not stated",
        "signature_company": signature_company,
        "contact_name": "Not stated",
        "vetting_contact_name": "Not stated",
        "contact_emails": contact_emails,
        "ks_number": ks_number,
        "sr_number": sr_match.group(1) if sr_match else None,
        "requester_email": email or "Not stated",
        "cf_sp_current": None,
    }


def lookup_account_by_sp(sp_number: str, sf_query) -> dict | None:
    if not sp_number:
        return None
    safe = str(sp_number).replace("'", "\\'")
    rows = sf_query(
        "SELECT Id, Name, Type, Service_Provider_Number__c FROM Account "
        f"WHERE Service_Provider_Number__c = '{safe}' LIMIT 1"
    )
    return rows[0] if rows else None


def resolve_target_account(
    gw: dict | None,
    sf: dict,
    sf_query,
) -> dict | None:
    candidates: list[dict] = []
    if sf.get("account"):
        candidates.append(sf["account"])
    if gw and gw.get("sp_number"):
        acct = lookup_account_by_sp(str(gw["sp_number"]), sf_query)
        if acct:
            candidates.append(acct)
    contact = sf.get("contact") or {}
    account_id = contact.get("AccountId")
    if account_id:
        safe = account_id.replace("'", "\\'")
        rows = sf_query(
            "SELECT Id, Name, Type, Service_Provider_Number__c FROM Account "
            f"WHERE Id = '{safe}' LIMIT 1"
        )
        if rows:
            candidates.append(rows[0])

    for acct in candidates:
        acct_id = (acct or {}).get("Id")
        if acct_id and acct_id not in PLACEHOLDER_ACCOUNT_IDS:
            sp = (acct or {}).get("Service_Provider_Number__c")
            if sp or (acct or {}).get("Type") == "Service Provider":
                return acct
            if gw:
                return acct
    return None


def account_update_status(
    posture_value: str,
    current_account_id: str | None,
    target_account: dict | None,
) -> str:
    target_id = (target_account or {}).get("Id")
    current = (current_account_id or "").strip()
    if not target_id:
        if current in PLACEHOLDER_ACCOUNT_IDS or not current:
            return "unresolved"
        return "not_applicable"
    if current == target_id:
        return "already_correct"
    if should_update_case_account(posture_value, current_account_id, target_id):
        return "recommended"
    if (posture_value or "").startswith("Known SP") and current and current not in PLACEHOLDER_ACCOUNT_IDS:
        return "review"
    if current in PLACEHOLDER_ACCOUNT_IDS or not current:
        return "unresolved"
    return "not_applicable"


def enriched_search_keys(entities: dict, gw: dict | None, target_account: dict | None) -> dict[str, list[str]]:
    keys = {
        "sr_numbers": [entities["sr_number"]] if entities.get("sr_number") else [],
        "ks_numbers": [],
        "emails": list(entities.get("contact_emails") or []),
        "company_tokens": [],
    }
    if entities.get("ks_number"):
        keys["ks_numbers"].append(entities["ks_number"])
    sp = (target_account or {}).get("Service_Provider_Number__c") or (gw or {}).get("sp_number")
    if sp and str(sp).upper() not in keys["ks_numbers"]:
        keys["ks_numbers"].append(str(sp).upper())
    company = entities.get("company")
    if company and company != "Not stated" and is_valid_company_string(company):
        keys["company_tokens"].append(company)
    return keys


def audit_case(case: dict, sf_query) -> dict[str, Any]:
    entities = extract_case_entities(case)
    gw = gateway_find_sp(entities)
    sf = salesforce_search(entities)
    if not gw and sf.get("account"):
        sp_num = str((sf["account"] or {}).get("Service_Provider_Number__c") or "").strip()
        if sp_num.upper().startswith("KS") and not entities.get("ks_number"):
            entities["ks_number"] = sp_num.upper()
            gw = gateway_find_sp(entities) or gw

    posture_value, _cf_target = posture(gw, sf, entities)
    target_account = resolve_target_account(gw, sf, sf_query)
    status = account_update_status(posture_value, case.get("AccountId"), target_account)

    current_account = case.get("Account") or {}
    return {
        "case_id": case.get("Id"),
        "case_number": str(case.get("CaseNumber") or "").lstrip("0"),
        "subject": (case.get("Subject") or "")[:100],
        "status": case.get("Status"),
        "posture": posture_value,
        "account_update": status,
        "current_account": {
            "id": case.get("AccountId"),
            "name": current_account.get("Name"),
            "sp_number": current_account.get("Service_Provider_Number__c"),
            "is_placeholder": (case.get("AccountId") or "") in PLACEHOLDER_ACCOUNT_IDS,
        },
        "resolved_account": {
            "id": (target_account or {}).get("Id"),
            "name": (target_account or {}).get("Name"),
            "sp_number": (target_account or {}).get("Service_Provider_Number__c"),
            "label": account_label(target_account) if target_account else None,
        },
        "gateway_sp": gw,
        "entities": {
            "company": entities.get("company"),
            "sr_number": entities.get("sr_number"),
            "ks_number": entities.get("ks_number"),
            "contact_emails": entities.get("contact_emails"),
        },
        "enriched_search_keys": enriched_search_keys(entities, gw, target_account),
        "sf_errors": sf.get("errors") or [],
    }


def summarize_audits(audits: list[dict]) -> dict[str, Any]:
    recommended = [a for a in audits if a["account_update"] == "recommended"]
    review = [a for a in audits if a["account_update"] == "review"]
    unresolved = [a for a in audits if a["account_update"] == "unresolved"]
    return {
        "cases_audited": len(audits),
        "recommended_updates": len(recommended),
        "review_mismatch": len(review),
        "unresolved": len(unresolved),
        "recommended": recommended,
        "review": review,
        "unresolved_cases": unresolved,
    }


def format_markdown(summary: dict) -> str:
    lines: list[str] = []
    if summary.get("recommended"):
        lines.append(
            f"**{summary['recommended_updates']} Case(s)** — Account update recommended:"
        )
        lines.append("")
        for row in summary["recommended"]:
            cur = row["current_account"].get("name") or "blank/placeholder"
            tgt = row["resolved_account"].get("label") or row["resolved_account"].get("name")
            lines.append(
                f"- **Case {row['case_number']}** — {cur} → {tgt} · {(row.get('subject') or '')[:60]}"
            )
            if row.get("case_id"):
                lines.append(f"  - https://vixxo.my.salesforce.com/{row['case_id']}")
    if summary.get("review"):
        if lines:
            lines.append("")
        lines.append(f"**{summary['review_mismatch']} Case(s)** — Known SP mismatch (manual review):")
        for row in summary["review"]:
            cur = row["current_account"].get("name") or "unknown"
            tgt = row["resolved_account"].get("label") or "unknown"
            lines.append(f"- **Case {row['case_number']}** — linked to {cur}; vetting says {tgt}")
    if summary.get("unresolved_cases"):
        placeholder = [
            r
            for r in summary["unresolved_cases"]
            if (r.get("current_account") or {}).get("is_placeholder")
        ]
        if placeholder:
            if lines:
                lines.append("")
            lines.append(
                f"**{len(placeholder)} Case(s)** on placeholder Account — needs Gateway vetting:"
            )
            for row in placeholder[:10]:
                sr = (row.get("entities") or {}).get("sr_number") or ""
                sr_note = f" · SR {sr}" if sr else ""
                lines.append(
                    f"- **Case {row['case_number']}**{sr_note} · {(row.get('subject') or '')[:55]}"
                )
    if not lines:
        return "No Case Account corrections recommended (audit-only)."
    return "\n".join(lines)
