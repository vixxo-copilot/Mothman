"""Entity extraction helpers for sp-inbound-vetting."""

from __future__ import annotations

import re

# Freemail / generic mailbox domains — skip Gateway domain search.
GENERIC_FREEMAIL_DOMAINS = frozenset(
    {
        "gmail",
        "googlemail",
        "yahoo",
        "ymail",
        "rocketmail",
        "aol",
        "hotmail",
        "outlook",
        "live",
        "msn",
        "icloud",
        "me",
        "mac",
        "protonmail",
        "proton",
        "zoho",
        "gmx",
        "mail",
        "inbox",
        "comcast",
        "verizon",
        "att",
        "sbcglobal",
        "bellsouth",
        "charter",
        "roadrunner",
        "earthlink",
        "fastmail",
        "yandex",
        "qq",
        "163",
        "126",
    }
)

GENERIC_MAILBOX_NAMES = frozenset(
    {
        "team",
        "support",
        "billing",
        "accounts",
        "accounts payable",
        "payable",
        "workorders",
        "workorder",
        "invoices",
        "invoice",
        "info",
        "admin",
        "office",
        "noreply",
        "no-reply",
        "not stated",
    }
)

COMPANY_SUFFIX = (
    r"(?:LLC|L\.L\.C\.|Inc\.?|Incorporated|Corp\.?|Corporation|"
    r"Co\.?,?\s*Inc\.?|Company|LP|L\.P\.|Ltd\.?|Limited|PLLC|P\.?C\.?)"
)

SIGNATURE_ROLE_FOR_RE = re.compile(
    rf"(?:Bookkeeper|Accountant|Billing|Accounts(?:\s+Payable)?|"
    rf"Manager|Owner|President|Representative|Agent)\s+for\s+"
    rf"(.+?{COMPANY_SUFFIX})\.?(?:\s|\d|$)",
    re.I,
)

SIGNATURE_LINE_RE = re.compile(rf"^(.{{3,80}}{COMPANY_SUFFIX})\.?\s*$", re.I | re.M)

SIGNATURE_BEFORE_PHONE_RE = re.compile(
    rf"(?:^|\n)\s*(.+?{COMPANY_SUFFIX})\.?\s*(?:\d{{3}}[-.\s]?\d{{3}}|www\.)",
    re.I | re.M,
)

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+", re.I)

SIGNATURE_PERSON_RE = re.compile(
    r"(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+?)?)"
    r"(Bookkeeper|Accountant|Billing|Accounts(?:\s+Payable)?|Manager|Owner|President)",
    re.M,
)

INTERNAL_EMAIL_MARKERS = ("@vixxo.com", "knowledgesync@vixxo.com")

INVALID_COMPANY_PHRASES = (
    "to whom it may concern",
    "hello can",
    "please let me know",
    "thanks again",
    "immediate attention",
    "past due",
)

VIXXO_CLIENT_SUBJECT_RE = re.compile(
    r"^(?:certificate|coi|insurance)\s*[-–—]\s*vixxo\b",
    re.I,
)

JOB_TITLE_PREFIX_RE = re.compile(
    r"^(?:Account|Office|Project|General|Regional|Service|Operations|Field|"
    r"Billing|Sales|Customer|Client|Program|Area|District|Senior|Junior|"
    r"Lead|Head)\s+[\w\s/]+?\s*[-–—]\s*",
    re.I,
)

SUBJECT_COI_FROM_RE = re.compile(
    r"COI(?:\s+(?:request|update|renewal))?\s+from\s+[\"']?([^\"'\n]+?)[\"']?\s*$",
    re.I,
)

BODY_COI_FROM_RE = re.compile(
    rf"(?:COI|Certificate of Insurance).*?\bfrom\s+([A-Z0-9][A-Za-z0-9\s,&.'-]*?{COMPANY_SUFFIX})\.?\b",
    re.I | re.S,
)

SIGNATURE_TITLE_DASH_RE = re.compile(
    rf"(?:Account|Office|Project|General|Regional|Service|Operations|Field|"
    rf"Billing|Sales|Customer|Program|Area|District)\s+[\w\s/]+?\s*[-–—]\s*"
    rf"(.+?{COMPANY_SUFFIX})\.?\s*$",
    re.I | re.M,
)


def _clean_company(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "").strip(" \t\r\n.,;|\"'"))
    if not cleaned or len(cleaned) < 3:
        return ""
    cleaned = JOB_TITLE_PREFIX_RE.sub("", cleaned).strip()
    if cleaned.lower() in GENERIC_MAILBOX_NAMES:
        return ""
    return cleaned


def strip_company_suffix(name: str) -> str:
    return re.sub(rf"\s*,?\s*{COMPANY_SUFFIX}\.?\s*$", "", (name or "").strip(), flags=re.I).strip()


def company_search_variants(name: str) -> list[str]:
    """Gateway/SF search tokens for a extracted company string."""
    cleaned = _clean_company(name)
    if not cleaned:
        return []
    variants: list[str] = []
    for candidate in (cleaned, strip_company_suffix(cleaned)):
        norm = re.sub(r"\s+", " ", candidate).strip()
        if norm and norm.lower() not in {v.lower() for v in variants}:
            variants.append(norm)
    return variants


def extract_subject_company(subject: str) -> str | None:
    if not subject:
        return None
    for pattern in (
        SUBJECT_COI_FROM_RE,
        re.compile(r"COI\s*[-–—]\s*(.+?)\s*[-–—]\s*Vixxo", re.I),
        re.compile(r"Invoice \d+ from (.+)$", re.I),
        re.compile(r"Statement from (.+?)(?:\s|$)", re.I),
    ):
        match = pattern.search(subject.strip())
        if match:
            company = sanitize_company(match.group(1))
            if company:
                return company
    return None


def extract_body_company_mentions(body: str) -> list[str]:
    if not body:
        return []
    found: list[str] = []
    for match in BODY_COI_FROM_RE.finditer(body.replace("\r\n", "\n")):
        company = sanitize_company(match.group(1))
        if company and company not in found:
            found.append(company)
    for match in SIGNATURE_TITLE_DASH_RE.finditer(body.replace("\r\n", "\n")):
        company = sanitize_company(match.group(1))
        if company and company not in found:
            found.append(company)
    return found


def pick_best_company(candidates: list[str], email: str = "") -> str | None:
    """Choose the strongest SP company string from competing extractions."""
    cleaned: list[str] = []
    for raw in candidates:
        company = _clean_company(raw)
        if company and company not in cleaned:
            cleaned.append(company)
    if not cleaned:
        return None

    email_stem = ""
    if email and "@" in email:
        email_stem = email.split("@", 1)[1].lower().split(".")[0].replace("-", "")

    def score(name: str) -> tuple[int, str]:
        lower = name.lower()
        base = strip_company_suffix(name).lower()
        points = 0
        if re.search(COMPANY_SUFFIX, name, re.I):
            points += 2
        if JOB_TITLE_PREFIX_RE.search(name):
            points -= 4
        if email_stem and email_stem in lower.replace("-", "").replace(" ", ""):
            points += 3
        if email_stem and base.replace(" ", "") in email_stem:
            points += 2
        if name.isupper() and len(name.split()) <= 4:
            points += 1
        return (points, name)

    return max(cleaned, key=score)


def is_valid_company_string(name: str) -> bool:
    """Reject body paragraphs, boilerplate, and client-site subject lines."""
    cleaned = (name or "").strip()
    if len(cleaned) < 3 or len(cleaned) > 80:
        return False
    lower = cleaned.lower()
    if lower in GENERIC_MAILBOX_NAMES or is_generic_mailbox_name(cleaned):
        return False
    if any(phrase in lower for phrase in INVALID_COMPANY_PHRASES):
        return False
    if VIXXO_CLIENT_SUBJECT_RE.match(cleaned):
        return False
    if re.search(r"\b1-\d{9,10}\b", cleaned):
        return False
    if re.match(r"^(this was|re:|fw:|fwd:)", lower):
        return False
    if lower.count("?") >= 1 and len(cleaned) > 60:
        return False
    if cleaned.count(".") >= 3 and len(cleaned) > 50:
        return False
    return True


def sanitize_company(name: str | None) -> str | None:
    cleaned = _clean_company(name or "")
    if cleaned and is_valid_company_string(cleaned):
        return cleaned
    return None


def is_internal_email(email: str) -> bool:
    lower = (email or "").lower()
    return any(token in lower for token in INTERNAL_EMAIL_MARKERS)


def extract_body_emails(body: str, requester_email: str = "") -> list[str]:
    """Collect requester + signature/body emails for Gateway and Salesforce lookup."""
    seen: set[str] = set()
    ordered: list[str] = []

    def add(raw: str) -> None:
        addr = (raw or "").strip().lower()
        if not addr or "@" not in addr or is_internal_email(addr):
            return
        if addr not in seen:
            seen.add(addr)
            ordered.append(addr)

    if requester_email:
        add(requester_email)
    for match in EMAIL_RE.finditer(body or ""):
        add(match.group(0))
    return ordered


def extract_signature_contact_name(body: str) -> str | None:
    """Person name from signature (e.g. Monique Prinsen / Tom Wilson before title)."""
    if not body:
        return None
    text = body.replace("\r\n", "\n")
    match = SIGNATURE_PERSON_RE.search(text)
    if match:
        name = re.sub(r"\s+", " ", match.group(1)).strip()
        if name and not is_generic_mailbox_name(name):
            return name

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for idx, line in enumerate(lines):
        if re.search(
            r"(?:Manager|Director|Coordinator|Supervisor|Owner|President|Bookkeeper|"
            r"Accountant|Agent|Representative)\s*[-–—]",
            line,
            re.I,
        ):
            if idx > 0:
                prev = lines[idx - 1]
                if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$", prev):
                    return prev
    return None


def contact_search_name(
    requester_name: str,
    signature_contact_name: str | None = None,
) -> str | None:
    """Best contact name for Gateway/SF name search."""
    if signature_contact_name and not is_generic_mailbox_name(signature_contact_name):
        return signature_contact_name
    if requester_name and not is_generic_mailbox_name(requester_name):
        return requester_name.strip()
    return signature_contact_name or (requester_name.strip() if requester_name else None)


def is_probable_person_name(name: str) -> bool:
    """Two-token capitalized name without company suffix → not a company."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    if not cleaned or is_generic_mailbox_name(cleaned):
        return False
    if re.search(COMPANY_SUFFIX, cleaned, re.I):
        return False
    if re.search(r"\b(DBA|d/b/a)\b", cleaned, re.I):
        return False
    parts = cleaned.split()
    return len(parts) == 2 and all(p[0].isupper() for p in parts if p)


def is_generic_mailbox_name(name: str) -> bool:
    lower = (name or "").strip().lower()
    if not lower or lower in GENERIC_MAILBOX_NAMES:
        return True
    parts = lower.split()
    return bool(parts) and parts[-1] in GENERIC_MAILBOX_NAMES


def extract_signature_company(body: str, email: str = "") -> str | None:
    """Pull SP company name from email signature / closing lines."""
    if not body:
        return None

    text = body.replace("\r\n", "\n")
    candidates: list[str] = []

    for pattern in (SIGNATURE_ROLE_FOR_RE, SIGNATURE_BEFORE_PHONE_RE):
        for match in pattern.finditer(text):
            candidates.append(match.group(1))

    for match in SIGNATURE_LINE_RE.finditer(text):
        candidates.append(match.group(1))

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for idx, line in enumerate(lines):
        if re.search(
            r"(?:\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|www\.|https?://|maps\.google)",
            line,
            re.I,
        ):
            if idx > 0 and re.search(COMPANY_SUFFIX, lines[idx - 1], re.I):
                candidates.append(lines[idx - 1])

    cleaned: list[str] = []
    for raw in candidates:
        company = sanitize_company(raw)
        if company and company not in cleaned:
            cleaned.append(company)

    picked = pick_best_company(cleaned, email)
    if picked:
        return picked

    return cleaned[0] if cleaned else None


def email_domain_search_tokens(email: str) -> list[str]:
    """Gateway search tokens derived from a corporate email domain."""
    if not email or "@" not in email:
        return []

    domain = email.split("@", 1)[1].lower().strip()
    if not domain:
        return []

    labels = domain.split(".")
    registrable = labels[0] if len(labels) >= 2 else domain

    if registrable in GENERIC_FREEMAIL_DOMAINS:
        return []
    if domain in GENERIC_FREEMAIL_DOMAINS:
        return []

    tokens: list[str] = []
    for candidate in (domain, registrable):
        norm = candidate.strip(".")
        if norm and norm not in tokens and norm not in GENERIC_FREEMAIL_DOMAINS:
            tokens.append(norm)
    return tokens
