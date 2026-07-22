#!/usr/bin/env python3
"""SPM-Invoice Concerns resolution classifier (v1.9.2)."""

from __future__ import annotations

import re

from portal_support_routing import is_vixxolink_portal_blocker, primary_message_text
from voicemail_intake_routing import is_payment_or_past_due_inquiry, is_vixxolink_support_ask

try:
    from ap_intake_forward import is_ai_failure_ticket
except ImportError:  # pragma: no cover - optional when run standalone
    def is_ai_failure_ticket(*_args, **_kwargs) -> bool:
        return False

try:
    from freshdesk_client import extract_sr_candidates
except ImportError:  # pragma: no cover

    def extract_sr_candidates(subject: str, text: str) -> list:
        return []


def has_attachments(ticket: dict, conversations: list[dict]) -> bool:
    if ticket.get("attachments"):
        return True
    return any(c.get("attachments") for c in conversations)


def has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.I | re.M) is not None


URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
PAYMENT_PORTAL_LINK_RE = re.compile(
    r"\b(view and pay|complete payment|pay now|make a payment|pay online|"
    r"manage-my-wallet|automatic payments)\b",
    re.I,
)
INVOICE_LINK_CONTEXT_RE = re.compile(
    r"\b(view statement|statement is available|statement is ready|new statement|"
    r"view invoice|invoice is available|download invoice|access your invoice|"
    r"account statement|statement on (?:my|the|our)|click (?:the button|below|here))\b",
    re.I,
)


def extract_http_urls(ticket: dict, conversations: list[dict]) -> list[str]:
    parts = [
        ticket.get("description") or "",
        ticket.get("description_text") or "",
        ticket.get("subject") or "",
    ]
    for conv in conversations:
        parts.append(conv.get("body") or "")
        parts.append(conv.get("body_text") or "")
    return URL_RE.findall("\n".join(parts))


def is_invoice_document_link(subject: str, text: str, urls: list[str]) -> bool:
    """Document/statement download link — not payment-portal or remit action."""
    if not urls:
        return False
    combined = f"{subject}\n{text}"
    if PAYMENT_PORTAL_LINK_RE.search(combined):
        return False
    if has(r"\b(view and pay|complete payment)\b", combined):
        return False
    if INVOICE_LINK_CONTEXT_RE.search(combined):
        return True
    if has(r"\bstatement\b", combined) and any(
        "statement" in url.lower() or "/account" in url.lower() for url in urls
    ):
        return True
    return False


def is_misroute_or_marketing(text: str, subject: str, tags: str = "") -> bool:
    """Strong misroute/marketing signals — safe for No Action Required close."""
    combined = f"{subject} {text} {tags}"
    if has(
        r"\b(sorry|apologize|apologies|apologise)\b.{0,80}\b("
        r"wrong|mistake|not meant|sent in error|sent to the wrong|did not mean"
        r")\b",
        combined,
    ):
        return True
    if has(
        r"\b(unsubscribe|newsletter|marketing email|promotional|special offer|"
        r"limited time offer|view in browser|email preferences)\b",
        combined,
    ):
        return True
    if has(r"\b(cold outreach|webinar invite|product demo|schedule a demo)\b", combined):
        return True
    return False


def is_duplicate_resubmission(text: str, tags: str = "") -> bool:
    """Conservative duplicate detection — weak signals return False."""
    combined = f"{text} {tags}".lower()
    if "duplicate" in combined and re.search(
        r"\b(duplicate|dupe)\b.{0,40}\b(ticket|submission|invoice|request)\b",
        combined,
        re.I,
    ):
        return True
    if re.search(
        r"\b(already submitted|previously submitted|resubmission of the same|"
        r"same invoice (?:was )?already)\b",
        combined,
        re.I,
    ):
        return True
    if "duplicate-ticket" in combined.replace("_", "-") or "confirmed-duplicate" in combined:
        return True
    return False


def should_close_no_action_required(
    resolution: str,
    *,
    text: str,
    subject: str,
    ticket: dict,
) -> bool:
    tags = " ".join(ticket.get("tags") or [])
    if resolution in ("provider-acknowledgement", "security-risk"):
        return True
    if resolution == "duplicate-or-resubmission":
        return is_duplicate_resubmission(text, tags)
    if resolution == "manual-review":
        return is_misroute_or_marketing(text, subject, tags)
    return False


def classify_resolution(
    ticket: dict, conversations: list[dict], text: str
) -> tuple[str, str, str]:
    subject = ticket.get("subject") or ""
    tags = " ".join(ticket.get("tags") or [])
    urls = extract_http_urls(ticket, conversations)

    if has(r"\b(update|change|new)\b.{0,80}\b(bank|banking|ach|wire|routing|remit)\b", text):
        return "security-risk", "Banking/remit change language", "Internal security hold; no forward"

    if is_ai_failure_ticket(ticket, conversations, text):
        if "ai-failure-reprocess" in (ticket.get("tags") or []):
            return (
                "ai-failure-reprocess",
                "AI upload failure — reprocess",
                "Route VINT AI Failures bucket; private note; leave Open",
            )
        return (
            "ai-failure-intake",
            "AI upload failure / VixxoNow invoice",
            "Route VINT AI Failures bucket; private note; leave Open",
        )

    if is_vixxolink_portal_blocker(subject, text) or is_vixxolink_support_ask(text):
        return (
            "vixxolink-portal-support",
            "VixxoLink portal login/access/setup",
            "Route VINT; type VixxoLink Support; no invoices@ forward",
        )

    primary = primary_message_text(text)
    if is_payment_or_past_due_inquiry(f"{subject}\n{primary}"):
        return (
            "payment-inquiry",
            "Payment status or past-due inquiry",
            "Stay SPM; type Invoice Support; Open; no aphelp/invoices@ forward",
        )

    if has(r"^(automatic reply|auto-reply|out of office):", subject):
        return "provider-acknowledgement", "Auto-reply/OOO", "Private note + close"

    if re.sub(r"\s+", " ", text).strip().lower() in {"thanks", "thank you", "thank you!", "appreciate it"}:
        return "provider-acknowledgement", "Courtesy-only", "Private note + close"

    if has(
        r"\bupload to wo\b|\binvoice submission\b|please see attached invoice|invoice attached|invoice entry|manual entry|manual-entry|manually enter\b",
        text,
    ):
        return "invoice-intake-forward", "Invoice intake / manual entry", "Forward invoices@ + ack + close"

    if has(r"\b(SR#?\s*:?\s*1-\d{7,12}|WO#?\s*1-\d{7,12})\b", text) and has_attachments(ticket, conversations):
        if has(r"\binvoice required\b", text) or has(
            r"\bplease see attached\b|\battached invoice\b|\binvoice for sr\b", text
        ):
            return "invoice-intake-forward", "SR + invoice attachment", "Forward invoices@ + ack + close"

    if is_invoice_document_link(subject, text, urls):
        return (
            "invoice-link-forward",
            "Invoice/statement document link",
            "Forward invoices@ + close (link intake)",
        )

    if has(r"\bview and pay\b|\bcomplete payment\b", text) and not has(r"\binvoice attached\b", text):
        return "manual-review", "Payment portal link", "Open-hold payment-link-caution"

    if has(
        r"\baccount statement\b|\bstatement of (?:your )?account\b",
        f"{subject}\n{text}",
    ):
        if has_attachments(ticket, conversations):
            return (
                "invoice-intake-forward",
                "Account statement PDF — AP intake",
                "Forward invoices@ + close (no Gateway)",
            )
        if is_invoice_document_link(subject, text, urls):
            return (
                "invoice-link-forward",
                "Account statement link — AP intake",
                "Forward invoices@ + close (link intake)",
            )
        return "manual-review", "Account statement without attachment", "Open-hold manual-review"

    if has(
        r"\bstatement\b|\bpast due\b|\boverdue\b|\boutstanding invoice\b|\baging\b|\bpayment status\b|\bwhen will.*paid\b|\bpayment for invoice\b",
        text,
    ):
        if not extract_sr_candidates(subject, text):
            return "manual-review", "Bulk/past-due statement without clear SR", "Open-hold manual-review"
        return "pending-payment", "Payment follow-up / past due", "Draft status reply; stay Open"

    if has(r"\breject(?:ed)? invoice\b|\binvoice rejected\b", text) and not has(r"\bplease reject\b", text):
        return "rejected-correctable", "Rejected invoice language", "Draft correction path"

    if has(r"\bpaid on\b|\bwe were paid\b|\bpayment received\b", text):
        return "paid-confirmation", "Provider claims paid", "Verify Gateway payment; draft confirmation"

    if has(r"\bportal\b|\bvixxolink\b|\bbuild quote\b|\bnte\b|\brate tier\b|\bcannot submit\b", text):
        return "vixxolink-portal-support", "Portal/account blocker", "Route VINT; type VixxoLink support"

    if extract_sr_candidates(subject, text):
        if has_attachments(ticket, conversations):
            return "invoice-intake-forward", "SR present with attachments", "Forward invoices@ if Gateway validates"
        return "pending-payment", "SR without clear intake wording", "Gateway status reply"

    if has(r"\binvoice\b", text) and has_attachments(ticket, conversations):
        return "manual-review", "Invoice attachment without SR", "Open-hold; extract SR from PDF"

    if is_duplicate_resubmission(text, tags):
        return (
            "duplicate-or-resubmission",
            "Duplicate/resubmission language",
            "Close No Action Required when signal is strong",
        )

    if is_misroute_or_marketing(text, subject, tags):
        return "manual-review", "Misroute/marketing", "Close No Action Required"

    return "manual-review", "Ambiguous / missing identifiers", "Open-hold manual-review"
