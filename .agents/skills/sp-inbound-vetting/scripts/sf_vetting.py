#!/usr/bin/env python3
"""Reusable Salesforce Case vetting helpers for sp-inbound-vetting."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Callable

from entity_extraction import (
    contact_search_name,
    extract_amazon_connect_voicemail,
    extract_body_company_mentions,
    extract_body_emails,
    extract_email_domains_from_messages,
    extract_service_contractor,
    extract_signature_company,
    extract_signature_contact_name,
    extract_sp_numbers,
    extract_sr_numbers,
    extract_subject_company,
    extract_voicemail_triage_block,
    email_domain_search_tokens,
    is_internal_email,
    is_voicemail_noise_subject,
    is_vixxo_internal_company,
    parse_sf_case_subject,
    pick_best_company,
    company_from_spoken_text,
)
from gateway_vetting import gateway_find_sp, vixxolink_get_sr_sp

SF_CLI = os.path.expandvars(r"%APPDATA%\npm\sf.cmd")
SPM_OWNER_ID = "00GTS00000MmfvS2AR"
COI_OWNER_ID = "005TS000009gWazYAE"

AUTOREPLY_PATTERNS = [
    re.compile(r"service desk submitted", re.I),
    re.compile(r"quickbooks.*past due", re.I),
    re.compile(r"past due invoice.*quickbooks", re.I),
]

PAYMENT_PATTERNS = [
    re.compile(r"payment status|status of payment|haven'?t received (?:my )?check", re.I),
    re.compile(r"remittance|check #|check number", re.I),
    re.compile(r"invoice.*(?:still )?in review|past due invoice", re.I),
    re.compile(r"AP hold|duplicate payment|billing correction", re.I),
    re.compile(r"portal inquiry.*status", re.I),
]

COI_PATTERNS = [
    re.compile(r"\bcoi\b|certificate of insurance|acord|additional insured", re.I),
]

EMAIL_MESSAGE_SOQL = (
    "SELECT Id, Subject, TextBody, HtmlBody, FromAddress, ToAddress, CcAddress, "
    "MessageDate, Incoming FROM EmailMessage WHERE RelatedToId = '{case_id}' "
    "ORDER BY MessageDate ASC"
)

EMAIL_MESSAGE_BATCH_SOQL = (
    "SELECT Id, RelatedToId, Subject, TextBody, HtmlBody, FromAddress, ToAddress, CcAddress, "
    "MessageDate, Incoming FROM EmailMessage WHERE RelatedToId IN ({ids}) "
    "ORDER BY RelatedToId, MessageDate ASC"
)

ATTACHMENT_SOQL = (
    "SELECT ContentDocument.Title, ContentDocument.FileExtension "
    "FROM ContentDocumentLink WHERE LinkedEntityId = '{case_id}'"
)

ATTACHMENT_BATCH_SOQL = (
    "SELECT LinkedEntityId, ContentDocument.Title, ContentDocument.FileExtension "
    "FROM ContentDocumentLink WHERE LinkedEntityId IN ({ids})"
)


def sf_query(query: str, *, sf_cli: str = SF_CLI, target_org: str = "vixxo") -> list[dict]:
    timeout_s = float(os.environ.get("SF_QUERY_TIMEOUT_S", "60"))
    try:
        result = subprocess.run(
            [sf_cli, "data", "query", "--query", query, "--target-org", target_org, "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"sf query timed out after {timeout_s}s") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout[:500])
    payload = json.loads(result.stdout)
    return payload.get("result", {}).get("records", [])


def _soql_id_list(case_ids: list[str]) -> str:
    return ", ".join(f"'{cid}'" for cid in case_ids if cid)


def pull_email_messages(case_id: str, *, query_fn: Callable[[str], list[dict]] | None = None) -> list[dict]:
    runner = query_fn or sf_query
    return runner(EMAIL_MESSAGE_SOQL.format(case_id=case_id))


def pull_attachment_names(case_id: str, *, query_fn: Callable[[str], list[dict]] | None = None) -> list[str]:
    """Filenames linked to the Case **and** its EmailMessages (COI PDFs often land on email only)."""
    runner = query_fn or sf_query
    names: list[str] = []
    seen: set[str] = set()

    def _add_rows(rows: list[dict]) -> None:
        for row in rows:
            name = _attachment_name_from_row(row)
            if name and name not in seen:
                seen.add(name)
                names.append(name)

    _add_rows(runner(ATTACHMENT_SOQL.format(case_id=case_id)))
    # Email-to-Case: ContentDocumentLink is frequently on EmailMessage, not Case
    try:
        emails = runner(
            "SELECT Id FROM EmailMessage WHERE ParentId = '{case_id}' OR RelatedToId = '{case_id}' "
            "ORDER BY MessageDate DESC LIMIT 10".format(case_id=case_id)
        )
    except RuntimeError:
        emails = []
    for em in emails:
        eid = em.get("Id")
        if not eid:
            continue
        try:
            _add_rows(runner(ATTACHMENT_SOQL.format(case_id=eid)))
        except RuntimeError:
            continue
    return names


def _attachment_name_from_row(row: dict) -> str | None:
    doc = row.get("ContentDocument") or {}
    title = str(doc.get("Title") or "").strip()
    ext = str(doc.get("FileExtension") or "").strip()
    if not title:
        return None
    return f"{title}.{ext}" if ext and not title.endswith(f".{ext}") else title


def pull_email_messages_batch(
    case_ids: list[str],
    *,
    batch_size: int = 15,
    query_fn: Callable[[str], list[dict]] | None = None,
) -> dict[str, list[dict]]:
    """Pull EmailMessage threads for many Cases in fewer SF CLI round-trips."""
    runner = query_fn or sf_query
    out: dict[str, list[dict]] = {cid: [] for cid in case_ids if cid}
    ids = [cid for cid in case_ids if cid]
    for i in range(0, len(ids), batch_size):
        chunk = ids[i : i + batch_size]
        id_list = _soql_id_list(chunk)
        if not id_list:
            continue
        try:
            rows = runner(EMAIL_MESSAGE_BATCH_SOQL.format(ids=id_list))
        except RuntimeError:
            # Fall back to per-case if batch query is too large / rejected
            for cid in chunk:
                try:
                    out[cid] = runner(EMAIL_MESSAGE_SOQL.format(case_id=cid))
                except RuntimeError:
                    out[cid] = []
            continue
        for row in rows:
            cid = row.get("RelatedToId")
            if cid in out:
                out[cid].append(row)
    return out


def pull_attachment_names_batch(
    case_ids: list[str],
    *,
    batch_size: int = 40,
    query_fn: Callable[[str], list[dict]] | None = None,
) -> dict[str, list[str]]:
    """Pull attachment filenames for many Cases in fewer SF CLI round-trips."""
    runner = query_fn or sf_query
    out: dict[str, list[str]] = {cid: [] for cid in case_ids if cid}
    ids = [cid for cid in case_ids if cid]
    for i in range(0, len(ids), batch_size):
        chunk = ids[i : i + batch_size]
        id_list = _soql_id_list(chunk)
        if not id_list:
            continue
        try:
            rows = runner(ATTACHMENT_BATCH_SOQL.format(ids=id_list))
        except RuntimeError:
            for cid in chunk:
                try:
                    out[cid] = pull_attachment_names(cid, query_fn=runner)
                except RuntimeError:
                    out[cid] = []
            continue
        for row in rows:
            cid = row.get("LinkedEntityId")
            name = _attachment_name_from_row(row)
            if cid in out and name:
                out[cid].append(name)
    return out


def build_case_intake_text(
    case: dict,
    *,
    email_messages: list[dict] | None = None,
    attachment_names: list[str] | None = None,
) -> str:
    """Merge Case Description, EmailMessage bodies, and attachment filenames."""
    parts = [
        case.get("Subject") or "",
        case.get("Description") or "",
    ]
    for msg in email_messages or []:
        parts.extend(
            [
                msg.get("Subject") or "",
                msg.get("TextBody") or "",
                msg.get("HtmlBody") or "",
                msg.get("FromAddress") or "",
                msg.get("ToAddress") or "",
            ]
        )
    if attachment_names:
        parts.append("\n".join(attachment_names))
    return "\n".join(p for p in parts if p)


def is_autoreply_noise(case: dict, intake_text: str | None = None) -> str | None:
    text = intake_text or f"{case.get('Subject') or ''} {case.get('Description') or ''}"
    for pat in AUTOREPLY_PATTERNS:
        if pat.search(text):
            return pat.pattern
    return None


def classify_routing(queue: str, subject: str, description: str) -> tuple[str, str]:
    text = f"{subject} {description}"
    if any(p.search(text) for p in PAYMENT_PATTERNS):
        return (
            "Recommend forward to AP Help",
            "Recommended routing (requires operator approval): Forward payment/AP portion to aphelp@vixxo.com. Draft only — do not send until approved.",
        )
    if queue == "coi" and any(p.search(text) for p in COI_PATTERNS):
        return ("Stay in SF", "Routing: Stay in SF — COI/compliance; use vixxo-coi-review for certificate fields.")
    return ("Stay in SF", "Routing: Stay in SF — SPM operational support.")


def extract_sf_case_entities(
    case: dict,
    queue: str,
    *,
    email_messages: list[dict] | None = None,
    attachment_names: list[str] | None = None,
    resolve_sr_sp: bool = True,
) -> dict:
    """Full-thread entity extraction for a Salesforce Case."""
    subject = case.get("Subject") or ""
    description = case.get("Description") or ""
    attachment_names = attachment_names or []
    intake_text = build_case_intake_text(case, email_messages=email_messages, attachment_names=attachment_names)

    contact_email = case.get("ContactEmail") or case.get("SuppliedEmail") or ""
    if contact_email and is_internal_email(contact_email):
        contact_email = ""

    subject_parsed = parse_sf_case_subject(subject)
    requester_email = contact_email if contact_email else "Not stated"
    body_emails = extract_body_emails(intake_text, requester_email if requester_email != "Not stated" else "")

    # Prefer external sender from EmailMessage thread over internal forwarder.
    for msg in email_messages or []:
        if msg.get("Incoming") is True:
            from_addr = (msg.get("FromAddress") or "").strip().lower()
            if from_addr and not is_internal_email(from_addr):
                requester_email = from_addr
                break
    if requester_email == "Not stated" and body_emails:
        requester_email = body_emails[0]

    sig_company = extract_signature_company(intake_text, requester_email if requester_email != "Not stated" else "")
    subj_company = extract_subject_company(subject)
    sig_contact = extract_signature_contact_name(intake_text)
    body_companies = extract_body_company_mentions(intake_text)

    company_candidates: list[str] = []
    # Subject + insured-business body beats Vixxo signature / certificate-holder text.
    for candidate in (
        subject_parsed.get("company"),
        subj_company,
        *body_companies,
        sig_company,
    ):
        if candidate:
            company_candidates.append(candidate)

    contractor = extract_service_contractor(intake_text)
    if contractor.get("company"):
        company_candidates.append(contractor["company"])

    vm_block = extract_voicemail_triage_block(description)
    if vm_block.get("company"):
        company_candidates.append(vm_block["company"])

    connect = extract_amazon_connect_voicemail(description)
    if connect.get("spoken_company"):
        company_candidates.append(connect["spoken_company"])

    transcript_blob = " ".join(
        x for x in (vm_block.get("transcript"), connect.get("message")) if x
    )
    spoken = company_from_spoken_text(transcript_blob)
    if spoken:
        company_candidates.append(spoken)

    company = pick_best_company(company_candidates, requester_email if requester_email != "Not stated" else "")
    if company and is_vixxo_internal_company(company):
        company = None
    # Never treat an email address as the SP company name
    if company and "@" in company:
        company = None
    if not company and is_voicemail_noise_subject(subject):
        company = None
    company = company or "Not stated"

    ks_number = subject_parsed.get("ks_number")
    sp_numbers = extract_sp_numbers(intake_text, attachment_names=attachment_names)
    if not ks_number and sp_numbers:
        ks_number = sp_numbers[0]

    if contractor.get("sp_number") and not ks_number:
        ks_number = contractor["sp_number"]

    sr_numbers = extract_sr_numbers(intake_text)
    if connect.get("sr_number") and connect["sr_number"] not in sr_numbers:
        sr_numbers.insert(0, connect["sr_number"])
    sr_number = sr_numbers[0] if sr_numbers else None

    contact_name = contact_search_name(
        "",
        sig_contact or vm_block.get("caller") or connect.get("caller_name"),
    )
    phone = vm_block.get("callback") or connect.get("callback_phone") or connect.get("ani")

    domain_tokens = extract_email_domains_from_messages(email_messages or [])
    for email in body_emails:
        for token in email_domain_search_tokens(email):
            if token not in domain_tokens:
                domain_tokens.append(token)

    entities = {
        "queue": queue,
        "case_number": case.get("CaseNumber"),
        "case_id": case.get("Id"),
        "requester_email": requester_email,
        "contact_emails": body_emails,
        "email_domain_tokens": domain_tokens,
        "company": company,
        "ks_number": ks_number,
        "sr_number": sr_number,
        "contact_name": contact_name or "Not stated",
        "vetting_contact_name": contact_name or "Not stated",
        "phone": phone,
        "subject": subject,
        "intake_sources": {
            "description": bool(description),
            "email_messages": len(email_messages or []),
            "attachments": len(attachment_names),
            "service_contractor": bool(contractor.get("company")),
            "amazon_connect": bool(connect.get("message")),
            "voicemail_triage": bool(vm_block.get("transcript") or vm_block.get("company")),
        },
    }

    gateway_hit = gateway_find_sp(entities)
    if not gateway_hit and resolve_sr_sp and sr_number:
        vl_hit = vixxolink_get_sr_sp(sr_number)
        if vl_hit:
            entities["vl_sr_sp"] = vl_hit
            if vl_hit.get("sp_number") and not entities.get("ks_number"):
                entities["ks_number"] = str(vl_hit["sp_number"])
            if vl_hit.get("name") and entities.get("company") in ("Not stated", ""):
                entities["company"] = vl_hit["name"]
            gateway_hit = gateway_find_sp(entities) or vl_hit

    entities["gateway_precheck"] = gateway_hit
    return entities


def determine_posture(entities: dict, gateway_hit: dict | None) -> str:
    if gateway_hit and gateway_hit.get("sp_number"):
        return "Known SP"
    if entities.get("company") and entities.get("company") != "Not stated":
        return "Unknown / Not in systems"
    return "Unknown / Not in systems"


def build_task_description(
    entities: dict,
    posture: str,
    gateway_hit: dict | None,
    routing_label: str,
    routing_note: str,
    ask_summary: str,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"Queue: {entities['queue']}",
        f"Case: {entities['case_number']}",
        f"Posture: {posture}",
    ]
    if gateway_hit and gateway_hit.get("sp_number"):
        name = gateway_hit.get("name") or "Unknown"
        lines.append(f"Gateway SP: {gateway_hit['sp_number']} - {name}")
        if gateway_hit.get("source"):
            lines.append(f"Match source: {gateway_hit['source']}")
    elif entities.get("company") and entities["company"] != "Not stated":
        lines.append(f"Extracted company: {entities['company']}")
    if entities.get("sr_number"):
        lines.append(f"SR: {entities['sr_number']}")
    if entities.get("requester_email") and entities["requester_email"] != "Not stated":
        lines.append(f"Contact email: {entities['requester_email']}")
    if entities.get("phone"):
        lines.append(f"Callback: {entities['phone']}")
    lines.append(f"Ask: {ask_summary}")
    lines.append(routing_note)
    lines.append(f"Processed: {ts}")
    return " | ".join(lines)


def summarize_ask(subject: str, description: str) -> str:
    subj = (subject or "").strip()[:120]
    if subj:
        return subj
    return (description or "").strip()[:120] or "Inbound SP request"


def pull_open_cases(*, query_fn: Callable[[str], list[dict]] | None = None) -> tuple[list[dict], list[dict]]:
    runner = query_fn or sf_query
    spm_q = (
        "SELECT Id, CaseNumber, Subject, Status, ContactEmail, ContactId, AccountId, "
        "Description, CreatedDate, SuppliedEmail FROM Case "
        f"WHERE OwnerId = '{SPM_OWNER_ID}' AND IsClosed = false "
        "ORDER BY CreatedDate ASC LIMIT 50"
    )
    coi_q = (
        "SELECT Id, CaseNumber, Subject, Status, ContactEmail, ContactId, AccountId, "
        "Description, CreatedDate, SuppliedEmail FROM Case "
        f"WHERE OwnerId = '{COI_OWNER_ID}' AND IsClosed = false "
        "ORDER BY CreatedDate ASC LIMIT 50"
    )
    return runner(spm_q), runner(coi_q)


def vetted_case_ids(case_ids: list[str], *, query_fn: Callable[[str], list[dict]] | None = None) -> set[str]:
    runner = query_fn or sf_query
    vetted: set[str] = set()
    for i in range(0, len(case_ids), 200):
        chunk = case_ids[i : i + 200]
        ids = "','".join(chunk)
        tasks = runner(
            f"SELECT WhatId FROM Task WHERE WhatId IN ('{ids}') AND Subject LIKE 'SP Inbound Vetting%'"
        )
        vetted.update(t["WhatId"] for t in tasks)
    return vetted
