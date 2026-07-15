"""Classify SF Cases into merge/routing buckets for duplicate consolidation."""

from __future__ import annotations

import re

from scan_duplicates import (
    FD_TICKET_RE,
    extract_federated_coi_fields,
    is_federated_coi_subject,
    norm_email,
)

BUCKET_COI_FEDERATED = "coi_federated"
BUCKET_COI_UPDATE = "coi_update"
BUCKET_RATE_CHANGE = "rate_change"
BUCKET_VIXXOLINK = "vixxolink_support"
BUCKET_VOICEMAIL = "voicemail"
BUCKET_ONBOARDING = "onboarding"
BUCKET_INVOICE = "invoice_reminder"
BUCKET_PAYMENT = "payment_ap"
BUCKET_OTHER = "other"

ALL_BUCKETS = {
    BUCKET_COI_FEDERATED,
    BUCKET_COI_UPDATE,
    BUCKET_RATE_CHANGE,
    BUCKET_VIXXOLINK,
    BUCKET_VOICEMAIL,
    BUCKET_ONBOARDING,
    BUCKET_INVOICE,
    BUCKET_PAYMENT,
    BUCKET_OTHER,
}

AUTO_MERGE_BUCKETS = {
    BUCKET_COI_FEDERATED,
    BUCKET_COI_UPDATE,
    BUCKET_VIXXOLINK,
    BUCKET_VOICEMAIL,
    BUCKET_RATE_CHANGE,
    BUCKET_PAYMENT,
}

COI_SUBJECT_RE = re.compile(
    r"\b(coi|certificate of insurance|proof of insurance|renewal certificate)\b",
    re.I,
)
RATE_SUBJECT_RE = re.compile(
    r"\b(rate negotiation|rate change|update pricing|pricing update)\b",
    re.I,
)
KS_SP_RE = re.compile(r"^ks\s*-\s*(.+?)\s*-\s*", re.I)
VIXXOLINK_RE = re.compile(
    r"\b(vixxolink|vixxo link|vixo link|portal login|login information)\b",
    re.I,
)
VOICEMAIL_SUBJECT_RE = re.compile(r"\bvixxo voicemail\b", re.I)
ONBOARDING_RE = re.compile(
    r"\b(onboarding|ksonboarding|vendor onboarding|new vendor)\b",
    re.I,
)
INVOICE_REMINDER_RE = re.compile(r"^reminder:\s*invoice\b", re.I)
PAYMENT_RE = re.compile(r"\b(payment status|when will i be paid|remittance)\b", re.I)
SPM_VOICEMAIL_RE = re.compile(r"sp voicemail triage\s*—\s*freshdesk\s*#(\d+)", re.I)
CALLER_RE = re.compile(r"Caller:\s*(.+?)(?:\n|$)", re.I)

# Voicemail triage category labels → merge bucket (see sp-voicemail-triage categories.md)
VOICEMAIL_CATEGORY_TO_BUCKET: dict[str, str] = {
    "vixxolink support": BUCKET_VIXXOLINK,
    "billing / invoice support": BUCKET_INVOICE,
    "payment information": BUCKET_PAYMENT,
    "coi / compliance": BUCKET_COI_UPDATE,
    "coverage / onboarding": BUCKET_ONBOARDING,
    "account update": BUCKET_ONBOARDING,
    "technical / trade support": BUCKET_OTHER,
    "general inquiry": BUCKET_OTHER,
    "sourcing / account team": BUCKET_OTHER,
    "service request / dispatch": BUCKET_OTHER,
    "quote / estimate": BUCKET_OTHER,
}

# Transcript signals when Category line is missing (priority ≈ categories.md)
VM_COI_RE = re.compile(
    r"\b(coi|certificate of insurance|additional insured|acord|compliance hold)\b",
    re.I,
)
VM_VIXXOLINK_RE = re.compile(
    r"\b(vixxolink|portal|login|password|dispatch board|accept work|mobile app|"
    r"can't see jobs|time in/out)\b",
    re.I,
)
VM_RATE_RE = re.compile(
    r"\b(rate negotiation|rate change|rate card|update pricing|pricing update)\b",
    re.I,
)
VM_PAYMENT_RE = re.compile(
    r"\b(when will i get paid|payment status|remittance|haven't received payment|ach|wire)\b",
    re.I,
)
VM_INVOICE_RE = re.compile(
    r"\b(invoice rejected|submit invoice|invoice status|billing workflow|resubmit invoice)\b",
    re.I,
)
VM_ONBOARDING_RE = re.compile(
    r"\b(onboarding|new provider|enrollment|coverage area|activation|vendor setup)\b",
    re.I,
)

# Cross-bucket voicemail routing: intent bucket → allowed open Case buckets
VOICEMAIL_ROUTING_TARGETS: dict[str, set[str]] = {
    BUCKET_VIXXOLINK: {BUCKET_VIXXOLINK},
    BUCKET_RATE_CHANGE: {BUCKET_RATE_CHANGE},
    BUCKET_COI_UPDATE: {BUCKET_COI_FEDERATED, BUCKET_COI_UPDATE, BUCKET_ONBOARDING},
    BUCKET_COI_FEDERATED: {BUCKET_COI_FEDERATED, BUCKET_COI_UPDATE, BUCKET_ONBOARDING},
    BUCKET_ONBOARDING: {BUCKET_ONBOARDING, BUCKET_COI_UPDATE},
    BUCKET_PAYMENT: {BUCKET_PAYMENT, BUCKET_INVOICE},
    BUCKET_INVOICE: {BUCKET_INVOICE, BUCKET_PAYMENT},
    BUCKET_OTHER: set(),
    BUCKET_VOICEMAIL: set(),
}


def classify_case(subject: str | None, description: str | None = None) -> str:
    subj = subject or ""
    desc = description or ""
    blob = f"{subj}\n{desc}"

    if is_federated_coi_subject(subj):
        return BUCKET_COI_FEDERATED
    if COI_SUBJECT_RE.search(subj):
        return BUCKET_COI_UPDATE
    if VOICEMAIL_SUBJECT_RE.search(subj) or SPM_VOICEMAIL_RE.search(desc):
        return BUCKET_VOICEMAIL
    if VIXXOLINK_RE.search(blob):
        return BUCKET_VIXXOLINK
    if RATE_SUBJECT_RE.search(subj) or (
        KS_SP_RE.match(subj) and "rate" in subj.lower()
    ):
        return BUCKET_RATE_CHANGE
    if ONBOARDING_RE.search(blob):
        return BUCKET_ONBOARDING
    if INVOICE_REMINDER_RE.search(subj):
        return BUCKET_INVOICE
    if PAYMENT_RE.search(blob):
        return BUCKET_PAYMENT
    return BUCKET_OTHER


def classify_voicemail_intent(category: str | None, transcript: str | None) -> str:
    """Map voicemail Category + transcript to a request-type bucket."""
    cat = (category or "").strip().lower()
    for label, bucket in VOICEMAIL_CATEGORY_TO_BUCKET.items():
        if label in cat or cat.startswith(label.split("/")[0].strip()):
            return bucket

    text = (transcript or "").lower()
    if not text:
        return BUCKET_VOICEMAIL

    # Multi-topic priority (categories.md): COI > payment > invoice > rate > vixxolink > onboarding
    if VM_COI_RE.search(text):
        return BUCKET_COI_UPDATE
    if VM_PAYMENT_RE.search(text):
        return BUCKET_PAYMENT
    if VM_INVOICE_RE.search(text):
        return BUCKET_INVOICE
    if VM_RATE_RE.search(text):
        return BUCKET_RATE_CHANGE
    if VM_VIXXOLINK_RE.search(text):
        return BUCKET_VIXXOLINK
    if VM_ONBOARDING_RE.search(text):
        return BUCKET_ONBOARDING
    return BUCKET_VOICEMAIL


def voicemail_may_route_to_target(intent_bucket: str, target_bucket: str) -> bool:
    """True when voicemail request context matches the open Case bucket."""
    if intent_bucket in {BUCKET_VOICEMAIL, BUCKET_OTHER}:
        return False
    allowed = VOICEMAIL_ROUTING_TARGETS.get(intent_bucket, set())
    return target_bucket in allowed


def extract_sp_name(subject: str | None, description: str | None = None) -> str | None:
    subj = subject or ""
    desc = description or ""

    if VOICEMAIL_SUBJECT_RE.search(subj) and not desc.strip():
        return None

    fields = extract_federated_coi_fields(subj)
    if fields:
        return fields["provider"]

    m = KS_SP_RE.match(subj)
    if m:
        return m.group(1).strip()

    m = re.search(r"proof of insurance for\s+(.+?)(?:\s+-|\s*$)", subj, re.I)
    if m:
        return m.group(1).strip()

    m = re.search(r"coi(?:\s+insurance)?\s*[-–]\s*(.+?)(?:\s*$)", subj, re.I)
    if m:
        return m.group(1).strip()

    m = CALLER_RE.search(desc)
    if m:
        caller = m.group(1).strip()
        if caller.lower() not in {"unknown", "anonymous", "wireless caller"}:
            return caller

    if VOICEMAIL_SUBJECT_RE.search(subj):
        return None

    if len(subj) <= 100 and not subj.lower().startswith("re:"):
        return subj.strip() or None
    return None


def normalize_sp_key(name: str | None) -> str | None:
    if not name:
        return None
    s = name.lower()
    s = re.sub(r"[,.'\"]", "", s)
    s = re.sub(
        r"\b(inc|llc|ltd|corp|corporation|company|co|services|service)\b",
        "",
        s,
    )
    return re.sub(r"\s+", " ", s).strip() or None


def case_requester_email(case: dict) -> str | None:
    return norm_email(case.get("ContactEmail")) or norm_email(case.get("SuppliedEmail"))


def voicemail_sp_captured(subject: str | None, description: str | None = None) -> bool:
    """True when voicemail triage captured a usable SP identity."""
    desc = description or ""
    subj = subject or ""
    if not (VOICEMAIL_SUBJECT_RE.search(subj) or SPM_VOICEMAIL_RE.search(desc)):
        return False
    sp = normalize_sp_key(extract_sp_name(subj, desc))
    if sp and sp not in {"vixxo voicemail", "voicemail"}:
        return True
    fd = FD_TICKET_RE.search(desc)
    if fd and sp:
        return True
    if fd and CALLER_RE.search(desc):
        return True
    return False


def merge_group_key(case: dict) -> tuple[str, str, str] | None:
    """Return (bucket, sp_key, email) for bucket-based grouping."""
    subj = case.get("Subject") or ""
    desc = case.get("Description") or ""
    bucket = classify_case(subj, desc)
    email = case_requester_email(case) or ""

    if bucket == BUCKET_COI_FEDERATED:
        fields = extract_federated_coi_fields(subj)
        if fields:
            pid, rid = fields["policy_id"], fields["req_id"]
            sp = normalize_sp_key(fields["provider"]) or ""
            return (bucket, f"{pid}|{rid}", sp)
        return None

    if bucket == BUCKET_VOICEMAIL:
        if not voicemail_sp_captured(subj, desc):
            return None
        sp = normalize_sp_key(extract_sp_name(subj, desc)) or ""
        fd = FD_TICKET_RE.search(desc)
        fd_part = fd.group(1) if fd else ""
        if not sp and not fd_part:
            return None
        return (bucket, sp or f"fd-{fd_part}", email)

    if bucket in {BUCKET_VIXXOLINK, BUCKET_RATE_CHANGE, BUCKET_PAYMENT}:
        sp = normalize_sp_key(extract_sp_name(subj, desc)) or ""
        if not email and not sp:
            return None
        return (bucket, sp, email)

    if bucket == BUCKET_COI_UPDATE:
        sp = normalize_sp_key(extract_sp_name(subj, desc)) or ""
        if not sp:
            return None
        return (bucket, sp, email)

    if bucket == BUCKET_ONBOARDING:
        sp = normalize_sp_key(extract_sp_name(subj, desc)) or ""
        return (bucket, sp, email)

    return None


def coi_routing_soql(sp_name: str) -> str:
    """SOQL to find open onboarding Case or Lead for COI merge target."""
    safe = sp_name.replace("'", "\\'")
    return (
        "SELECT Id, CaseNumber, Subject, Status, CreatedDate, Owner.Username "
        "FROM Case "
        f"WHERE IsClosed = false AND (Subject LIKE '%{safe}%' "
        f"OR Subject LIKE '%KS - {safe}%') "
        "AND (Subject LIKE '%onboarding%' OR Subject LIKE '%KSOnboarding%' "
        "OR Subject LIKE '%KS - %') "
        "ORDER BY CreatedDate ASC LIMIT 5"
    )
