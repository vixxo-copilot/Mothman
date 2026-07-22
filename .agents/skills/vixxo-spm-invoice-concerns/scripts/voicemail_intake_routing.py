#!/usr/bin/env python3
"""Voicemail intake routing for SPM / qsiap AP voicemails."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

SPM_GROUP_ID = 159000485013
VINT_GROUP_ID = 159000486559
INVOICE_SUPPORT_TYPE = "Invoice Support"
VIXXOLINK_SUPPORT_TYPE = "VixxoLink Support"
INVOICES_AP = "invoices@vixxo.com"

INVOICE_ATTACHMENT_RE = re.compile(
    r"\.(pdf|xlsx?|csv|docx?|tif{1,2})\b",
    re.I,
)
INVOICE_ATTACHMENT_NAME_RE = re.compile(
    r"\b(invoice|inv[_-]|bill|statement|receipt)\b",
    re.I,
)


@dataclass
class VoicemailRouting:
    resolution: str
    reason: str
    group_id: int
    ticket_type: str
    status: int  # 2 = Open
    tags: tuple[str, ...]
    forward_to: str | None  # invoices@vixxo.com only when vetted
    gateway_invoice_check: str  # n/a | skipped | passed | blocked-existing-invoice


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.I | re.M) is not None


def transcript_text(ticket: dict, conversations: list[dict] | None = None) -> str:
    parts = [
        ticket.get("subject") or "",
        ticket.get("description_text") or "",
        ticket.get("description") or "",
    ]
    for conv in conversations or []:
        parts.append(conv.get("body_text") or conv.get("body") or "")
    return "\n".join(parts)


def is_vixxolink_support_ask(text: str) -> bool:
    combined = text.lower()
    if _has(r"\bvixxolink support\b", combined):
        return True
    if _has(r"\b(vixxolink|portal)\b", combined) and _has(
        r"\b("
        r"support|log ?in|login|password|access|account setup|set up|setup|"
        r"cannot submit|can't submit|dispatch board|accept work|app\b"
        r")\b",
        combined,
    ):
        return True
    return False


def is_payment_or_past_due_inquiry(text: str) -> bool:
    return _has(
        r"\b("
        r"payment status|when will (?:i|we) (?:be )?paid|when paid|"
        r"past due|past-due|overdue|outstanding invoice|aging|"
        r"haven't received payment|have not received payment|"
        r"check number|remittance|ach\b|wire transfer|"
        r"inquire on payment|inquiry on payment|payment inquiry|"
        r"status of (?:my )?payment|paid yet"
        r")\b",
        text,
    )


def has_invoice_attachments(ticket: dict, conversations: list[dict] | None = None) -> bool:
    blobs: list[dict] = []
    for att in ticket.get("attachments") or []:
        blobs.append(att)
    for conv in conversations or []:
        for att in conv.get("attachments") or []:
            blobs.append(att)
    for att in blobs:
        name = str(att.get("name") or att.get("file_name") or "")
        content = str(att.get("content_type") or "")
        if INVOICE_ATTACHMENT_RE.search(name):
            if INVOICE_ATTACHMENT_NAME_RE.search(name):
                return True
            if "pdf" in content.lower() or "excel" in content.lower():
                return True
        if INVOICE_ATTACHMENT_NAME_RE.search(name):
            return True
    return False


def wants_invoice_submission(text: str) -> bool:
    return _has(
        r"\b("
        r"submit(?:ting)? invoice|invoice attached|attached invoice|"
        r"please process (?:the )?invoice|manual entry|manual-entry|"
        r"upload invoice|invoice for sr|add(?:ing)? invoice"
        r")\b",
        text,
    )


def sr_has_gateway_invoice(
    sr: str | None,
    sp_number: str | None,
    gateway_lookup: Callable[[str], dict | None] | None = None,
) -> bool:
    sr = str(sr or "").strip()
    if not sr or not gateway_lookup:
        return False
    try:
        from gateway_vetting import gateway_sr_invoice_status

        status = gateway_sr_invoice_status(sr, sp_number=sp_number)
        return int(status.get("invoice_count") or 0) > 0
    except Exception:
        row = gateway_lookup(sr) if gateway_lookup else None
        if not row:
            return False
        invs = row.get("invoiceList") or row.get("invoices") or []
        return len(invs) > 0


def classify_voicemail_intake(
    ticket: dict,
    *,
    conversations: list[dict] | None = None,
    sr_number: str | None = None,
    sp_number: str | None = None,
    gateway_lookup: Callable[[str], dict | None] | None = None,
) -> VoicemailRouting:
    text = transcript_text(ticket, conversations)

    if is_vixxolink_support_ask(text):
        return VoicemailRouting(
            resolution="vixxolink-portal-support",
            reason="Voicemail mentions VixxoLink / portal support",
            group_id=VINT_GROUP_ID,
            ticket_type=VIXXOLINK_SUPPORT_TYPE,
            status=2,
            tags=("vixxolink-portal-support", "vint-routed", "voicemail-vetted", "open-hold"),
            forward_to=None,
            gateway_invoice_check="n/a",
        )

    if is_payment_or_past_due_inquiry(text):
        return VoicemailRouting(
            resolution="payment-inquiry",
            reason="Payment status or past-due inquiry — stay SPM",
            group_id=SPM_GROUP_ID,
            ticket_type=INVOICE_SUPPORT_TYPE,
            status=2,
            tags=("payment-inquiry", "voicemail-vetted", "open-hold"),
            forward_to=None,
            gateway_invoice_check="n/a",
        )

    if has_invoice_attachments(ticket, conversations) and wants_invoice_submission(text):
        gw_check = "skipped"
        forward = INVOICES_AP
        if sr_number:
            if sr_has_gateway_invoice(sr_number, sp_number, gateway_lookup):
                gw_check = "blocked-existing-invoice"
                forward = None
            else:
                gw_check = "passed"
        return VoicemailRouting(
            resolution="invoice-attachment-forward" if forward else "invoice-already-on-sr",
            reason=(
                "Invoice attachment + submit ask; Gateway shows invoice on SR"
                if gw_check == "blocked-existing-invoice"
                else "Invoice attachment needs AP intake — Gateway has no invoice on SR"
            ),
            group_id=SPM_GROUP_ID,
            ticket_type=INVOICE_SUPPORT_TYPE,
            status=2,
            tags=(
                ("invoice-on-sr", "voicemail-vetted", "open-hold")
                if not forward
                else ("invoice-intake-forward", "voicemail-vetted", "open-hold")
            ),
            forward_to=forward,
            gateway_invoice_check=gw_check,
        )

    return VoicemailRouting(
        resolution="vetting-only",
        reason="Identity vetting; no auto-forward",
        group_id=SPM_GROUP_ID,
        ticket_type=INVOICE_SUPPORT_TYPE,
        status=2,
        tags=("voicemail-vetted", "open-hold"),
        forward_to=None,
        gateway_invoice_check="n/a",
    )


def routing_note(routing: VoicemailRouting, *, sr: str | None = None) -> str:
    lines = [
        f"**Voicemail routing:** {routing.resolution}",
        f"**Reason:** {routing.reason}",
        f"**Group:** {routing.group_id}",
        f"**Type:** {routing.ticket_type}",
        f"**Status:** Open",
    ]
    if sr:
        lines.append(f"**SR:** {sr}")
    if routing.gateway_invoice_check not in ("n/a", "skipped"):
        lines.append(f"**Gateway invoice check:** {routing.gateway_invoice_check}")
    if routing.forward_to:
        lines.append(
            f"**AP forward candidate:** {routing.forward_to} "
            "(operator approval required before forward)"
        )
    else:
        lines.append("**AP forward:** No — do not forward to aphelp or invoices@")
    return "\n".join(lines)
