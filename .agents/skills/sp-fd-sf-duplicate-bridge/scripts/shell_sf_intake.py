#!/usr/bin/env python3
"""Full-thread SF Case intake for shell duplicate-bridge vetting (sp-inbound-vetting parity)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
VETTING = SKILL_ROOT.parent / "sp-inbound-vetting" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(VETTING))

from entity_extraction import email_domain_search_tokens, is_internal_email, pick_best_company
from gateway_vetting import gateway_find_sp
from sf_vetting import (
    build_case_intake_text,
    extract_sf_case_entities,
    is_autoreply_noise,
    pull_attachment_names,
    pull_email_messages,
)

_email_cache: dict[str, list[dict]] = {}
_attach_cache: dict[str, list[str]] = {}

BODY_CLIENT_RE = re.compile(
    r"our client,?\s+(.+?(?:LLC|L\.L\.C\.|Inc\.?|Incorporated|Corp\.?|Corporation|Company|Ltd\.?|Limited))",
    re.I,
)
BODY_DUE_FROM_RE = re.compile(r"due from\s+(.+?)(?:,|\s+Invoice|\s*$)", re.I)
CERT_FOR_RE = re.compile(
    r"certificate(?: of insurance)? for\s+(.+?)(?:\s*-|\s*$|\.)",
    re.I,
)


def clear_intake_cache() -> None:
    _email_cache.clear()
    _attach_cache.clear()


def to_sf_case(case: dict, sf_rec: dict | None = None) -> dict:
    """Normalize shell vet row or SF export record to Case shape."""
    rec = sf_rec or {}
    if case.get("Subject") is not None:
        base = dict(case)
    else:
        base = {
            "Id": case.get("id") or case.get("case_id"),
            "CaseNumber": case.get("case_number") or rec.get("CaseNumber"),
            "Subject": case.get("subject") or rec.get("Subject") or "",
            "Description": rec.get("Description") or case.get("description") or "",
            "ContactEmail": case.get("contact_email") or rec.get("ContactEmail") or rec.get("SuppliedEmail") or "",
            "SuppliedEmail": rec.get("SuppliedEmail") or "",
        }
    if case.get("subject"):
        base["Subject"] = case["subject"]
    if case.get("contact_email"):
        base["ContactEmail"] = case["contact_email"]
    return base


def supplement_company_from_body(entities: dict, intake_text: str) -> None:
    """Broker/carrier COI emails often name the insured SP in the body, not Description."""
    if entities.get("company") and entities["company"] != "Not stated":
        return
    candidates: list[str] = []
    for pat in (BODY_CLIENT_RE, BODY_DUE_FROM_RE, CERT_FOR_RE):
        m = pat.search(intake_text or "")
        if m:
            candidates.append(re.sub(r"\s+", " ", m.group(1).strip(" -.,;")))
    if not candidates:
        return
    email = entities.get("requester_email") if entities.get("requester_email") != "Not stated" else ""
    company = pick_best_company(candidates, email)
    if company:
        entities["company"] = company
        entities.setdefault("intake_sources", {})["broker_body"] = True
        hit = gateway_find_sp(entities)
        if hit:
            entities["gateway_precheck"] = hit


def load_case_intake(
    case: dict,
    *,
    queue: str = "coi",
    sf_rec: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, str, list[dict], list[str]]:
    """Pull EmailMessage thread + attachments; return entities and merged intake text."""
    sf_case = to_sf_case(case, sf_rec)
    cid = sf_case.get("Id")
    if not cid:
        raise ValueError("case missing Id")

    if use_cache and cid in _email_cache:
        emails = _email_cache[cid]
    else:
        emails = pull_email_messages(cid)
        if use_cache:
            _email_cache[cid] = emails

    if use_cache and cid in _attach_cache:
        attachments = _attach_cache[cid]
    else:
        attachments = pull_attachment_names(cid)
        if use_cache:
            _attach_cache[cid] = attachments

    intake_text = build_case_intake_text(
        sf_case, email_messages=emails, attachment_names=attachments
    )
    entities = extract_sf_case_entities(
        sf_case,
        queue,
        email_messages=emails,
        attachment_names=attachments,
    )
    supplement_company_from_body(entities, intake_text)
    return entities, intake_text, emails, attachments


def norm_email_domain(email: str | None) -> str | None:
    if not email or email == "Not stated" or "@" not in email:
        return None
    if is_internal_email(email):
        return None
    dom = email.split("@", 1)[1].lower().strip()
    skip = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com"}
    if dom in skip:
        return None
    return dom


def hints_from_entities(case: dict, entities: dict, *, fallback_company: str | None = None) -> dict:
    """Map sp-inbound-vetting entities to shell vet hints dict."""
    import scan_duplicates as sd

    subject = case.get("Subject") or case.get("subject") or ""
    coi_fields = sd.extract_federated_coi_fields(subject)
    provider = coi_fields["provider"] if coi_fields else None

    company = entities.get("company")
    if not company or company == "Not stated":
        company = fallback_company or sd.extract_subject_sp_hint(subject) or provider

    email = entities.get("requester_email")
    if not email or email == "Not stated":
        email = sd.norm_email(case.get("ContactEmail") or case.get("contact_email") or case.get("SuppliedEmail"))

    ks_number = entities.get("ks_number")
    if ks_number and not str(ks_number).upper().startswith("KS"):
        ks_m = re.search(r"\b(KS[\dA-Z]+)\b", str(ks_number), re.I)
        if ks_m:
            ks_number = ks_m.group(1).upper()

    domain_tokens = list(entities.get("email_domain_tokens") or [])
    email_domain = norm_email_domain(email)
    if email_domain:
        stem = email_domain.split(".")[0]
        if stem and stem not in domain_tokens:
            domain_tokens.insert(0, stem)
        for token in email_domain_search_tokens(email):
            if token not in domain_tokens:
                domain_tokens.append(token)

    blob = f"{subject} {case.get('Description') or case.get('description') or ''}"
    onboarding_re = re.compile(r"ksonboarding|onboarding|prosite|coverage application|new provider", re.I)

    return {
        "coi_fields": coi_fields,
        "provider": provider,
        "company": company if company and company != "Not stated" else None,
        "ks_number": ks_number,
        "sr_number": entities.get("sr_number"),
        "contact_email": email if email and email != "Not stated" else None,
        "email_domain": email_domain,
        "email_domain_tokens": domain_tokens,
        "contact_name": entities.get("contact_name"),
        "is_federated_coi": coi_fields is not None,
        "is_onboarding": bool(onboarding_re.search(blob) or ks_number),
        "gateway_precheck": entities.get("gateway_precheck"),
        "intake_sources": entities.get("intake_sources"),
        "entities": entities,
    }


def company_candidates_from_intake(entities: dict, intake_text: str) -> list[str]:
    """Company names for account / gateway search (priority order)."""
    names: list[str] = []
    seen: set[str] = set()

    def add(name: str | None) -> None:
        n = re.sub(r"\s+", " ", (name or "").strip())
        if len(n) < 3:
            return
        key = n.lower()
        if key not in seen and key != "not stated":
            seen.add(key)
            names.append(n)

    add(entities.get("company"))
    vl = entities.get("vl_sr_sp") or {}
    add(vl.get("name"))
    gw = entities.get("gateway_precheck") or {}
    add(gw.get("name"))
    return names
