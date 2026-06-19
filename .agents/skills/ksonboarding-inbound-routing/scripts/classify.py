"""Content classification for ksonboarding-inbound-routing."""

from __future__ import annotations

import re
from typing import Any

VOICEMAIL_RE = re.compile(r"\bnew voicemail\b", re.I)

COI_BODY_PATTERNS = (
    re.compile(r"\bcoi\b", re.I),
    re.compile(r"certificate of insurance", re.I),
    re.compile(r"insurance certificate", re.I),
    re.compile(r"additional insured", re.I),
    re.compile(r"\bacord\b", re.I),
    re.compile(r"coverage certificate", re.I),
    re.compile(r"compliance certificate", re.I),
)
COI_ATTACHMENT_RE = re.compile(
    r"(coi|certificate|acord|insurance|cert)[^/\\]*\.(pdf|jpg|jpeg|png|tif|tiff)$",
    re.I,
)

PORTAL_KEYWORDS = (
    "vixxolink",
    "vixxo link",
    "provider portal",
    "sp portal",
    "dispatch board",
    "accept work",
    "decline job",
    "can't see jobs",
    "cant see jobs",
    "log in",
    "login",
    "password reset",
    "reset password",
    "locked out",
    "mobile app",
    "time in",
    "time out",
    "upload photo",
)
CLIENT_PORTAL_KEYWORDS = (
    "client portal",
    "customer portal",
    "store portal",
    "facilities portal",
    "client support portal",
)

INVOICE_KEYWORDS = (
    "past due",
    "past-due",
    "pastdue",
    "overdue",
    "delinquent",
    "aging",
    "unpaid invoice",
    "outstanding balance",
    "payment status",
    "when will this be paid",
    "when will i be paid",
    "when will we be paid",
    "account statement",
    "statement of account",
    "open invoices",
    "balance notice",
    "ar statement",
)
STATEMENT_ATTACHMENT_RE = re.compile(
    r"(statement|aging|pastdue|past_due|open.?invoice|ar)[^/\\]*\.(pdf|xlsx|xls|csv|doc|docx)$",
    re.I,
)

ONBOARDING_COI_INSTRUCTION_RE = re.compile(
    r"(send (us )?your coi|submit (your )?coi|provide (your )?coi|need (your )?coi)",
    re.I,
)


def _blob(ticket: dict, attachment_names: list[str] | None = None) -> str:
    subject = (ticket.get("subject") or "").lower()
    desc = (ticket.get("description_text") or ticket.get("description") or "").lower()
    names = " ".join(attachment_names or []).lower()
    return f"{subject} {desc} {names}"


def _has_keyword(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [kw for kw in keywords if kw in text]


def _match_coi_body(text: str) -> list[str]:
    hits: list[str] = []
    for pat in COI_BODY_PATTERNS:
        if pat.search(text):
            hits.append(pat.pattern.replace("\\b", "").replace("(?i)", "").strip("^$"))
    if re.search(r"acord\s*25", text, re.I):
        hits.append("acord 25")
    return hits


def classify_ticket(ticket: dict, *, attachment_names: list[str] | None = None) -> dict[str, Any]:
    """Return classification outcome for a KSOnboarding email ticket."""
    blob = _blob(ticket, attachment_names)
    subject = ticket.get("subject") or ""
    signals: list[str] = []

    # Priority 1 — COI
    coi_attachments = [
        n for n in (attachment_names or []) if COI_ATTACHMENT_RE.search(n or "")
    ]
    coi_kw = _match_coi_body(blob)
    has_coi_attachment = bool(coi_attachments)
    has_coi_body = bool(coi_kw)
    onboarding_coi_only = (
        not has_coi_attachment
        and ONBOARDING_COI_INSTRUCTION_RE.search(blob)
        and not has_coi_body
    )

    if (has_coi_attachment or has_coi_body) and not onboarding_coi_only:
        if coi_attachments:
            signals.extend(f"attachment:{n}" for n in coi_attachments[:3])
        if coi_kw:
            signals.extend(f"keyword:{kw}" for kw in coi_kw[:5])
        return {
            "classification": "COI",
            "new_type": "COIs",
            "type_change": "KSOnboarding → COIs",
            "retain_type": False,
            "cf_type_of_request": None,
            "route_tags": ["ks-inbound-routed", "coi", "risk-compliance-routed"],
            "signals": signals,
        }

    # Priority 2 — Portal (exclude client portal)
    client_kw = _has_keyword(blob, CLIENT_PORTAL_KEYWORDS)
    portal_kw = _has_keyword(blob, PORTAL_KEYWORDS)
    if portal_kw and not client_kw:
        signals.extend(f"keyword:{kw}" for kw in portal_kw[:5])
        return {
            "classification": "VixxoLink Support",
            "new_type": "VixxoLink Support",
            "type_change": "KSOnboarding → VixxoLink Support",
            "retain_type": False,
            "cf_type_of_request": None,
            "route_tags": ["ks-inbound-routed", "vixxolink-routed"],
            "signals": signals,
        }
    if client_kw:
        signals.extend(f"client-portal:{kw}" for kw in client_kw[:3])
        return {
            "classification": "KSOnboarding retained",
            "new_type": None,
            "type_change": "none — client portal flag",
            "retain_type": True,
            "cf_type_of_request": None,
            "route_tags": ["ks-inbound-routed", "ks-onboarding-retained", "client-portal-review"],
            "signals": signals,
        }

    # Priority 3 — Invoice / statement
    stmt_attachments = [
        n for n in (attachment_names or []) if STATEMENT_ATTACHMENT_RE.search(n or "")
    ]
    inv_kw = _has_keyword(blob, INVOICE_KEYWORDS)
    has_statement_word = "statement" in blob and (
        "account" in blob or "invoice" in blob or stmt_attachments
    )
    if inv_kw or stmt_attachments or has_statement_word:
        if stmt_attachments:
            signals.extend(f"attachment:{n}" for n in stmt_attachments[:3])
        if inv_kw:
            signals.extend(f"keyword:{kw}" for kw in inv_kw[:5])
        if has_statement_word and "keyword:statement" not in signals:
            signals.append("keyword:statement")
        return {
            "classification": "Invoice Support",
            "new_type": "Invoice Support",
            "type_change": "KSOnboarding → Invoice Support",
            "retain_type": False,
            "cf_type_of_request": "Follow up on an Unpaid Invoice",
            "route_tags": ["ks-inbound-routed", "invoice-routed"],
            "signals": signals,
        }

    # Priority 4 — Retain
    return {
        "classification": "KSOnboarding retained",
        "new_type": None,
        "type_change": "none",
        "retain_type": True,
        "cf_type_of_request": None,
        "route_tags": ["ks-inbound-routed", "ks-onboarding-retained"],
        "signals": signals or ["no retype signals"],
    }


def routing_cf_sp(posture: str, confidence: str, gateway: dict | None) -> str | None:
    """Return cf_sp value when Known SP / High confidence; else None (leave blank)."""
    if not posture.startswith("Known SP") or "Possible" in posture:
        return None
    if confidence != "High":
        return None
    if gateway and gateway.get("match_type") == "fuzzy":
        return None
    if not gateway:
        return None
    num, name = gateway.get("sp_number"), gateway.get("name")
    if num and name:
        return f"{num} - {name}"
    if name:
        return str(name)
    return None
