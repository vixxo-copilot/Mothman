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
        "accounting",
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

# Soft SP endings (Services/Group/…) before a phone line — e.g. Cook's Locksmith Services.
SIGNATURE_SOFT_BEFORE_PHONE_RE = re.compile(
    r"(?:^|\n)\s*([A-Z0-9][A-Za-z0-9 &.'/-]{2,70}?"
    r"(?:Services|Group|Associates|Partners|Solutions|Enterprises))"
    r"\.?\s*(?:\d{3}[-.\s]?\d{3}|www\.)",
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
    "vixxolink",
    "vixxo voicemail",
    "rate changes",
    "rate change",
    "notice of cancellation",
    "live certificate",
    "certificate holder",
    "risk management department",
)

# Internal Vixxo / certificate-holder names — never treat as the SP company.
VIXXO_INTERNAL_COMPANY_NAMES = frozenset(
    {
        "vixxo",
        "vixxo corporation",
        "vixxo corp",
        "vixxo facility solutions",
        "vixxo facility solution",
        "vixxolink",
        "risk management department vixxo corporation",
        "spm emails",
        "vendor relations",
    }
)

VIXXO_CLIENT_SUBJECT_RE = re.compile(
    r"^(?:certificate|coi|insurance)\s*[-–—]\s*vixxo\b",
    re.I,
)

SUBJECT_APPROVED_FOR_RE = re.compile(
    r"\b(?:approved|notice)\s+for\s+(.+?)\s*$",
    re.I,
)

SUBJECT_SP_NUMBER_TAIL_RE = re.compile(
    r"\s*[-–—]\s*Service Provider number(?:\s+KS?\d+)?.*$",
    re.I,
)

SUBJECT_YOUR_ACCOUNT_VIXXO_RE = re.compile(
    r"\s*[-–—]\s*Your account\s+Vixxo.*$",
    re.I,
)

INSURED_BUSINESS_RE = re.compile(
    r"(?:Insured business|YOUR BUSINESS DETAILS)\s*:?\s*\n\s*([^\n]{3,100})",
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
    cleaned = re.sub(r"^>+\s*", "", cleaned).strip()
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


def extract_body_company_mentions(body: str) -> list[str]:
    if not body:
        return []
    text = body.replace("\r\n", "\n")
    found: list[str] = []
    for match in INSURED_BUSINESS_RE.finditer(text):
        company = sanitize_company(match.group(1))
        if company and company not in found:
            found.append(company)
    for match in BODY_COI_FROM_RE.finditer(text):
        company = sanitize_company(match.group(1))
        if company and company not in found:
            found.append(company)
    for match in SIGNATURE_TITLE_DASH_RE.finditer(text):
        company = sanitize_company(match.group(1))
        if company and company not in found:
            found.append(company)
    return found


def is_vixxo_internal_company(name: str | None) -> bool:
    """True when the string is Vixxo (certificate holder / email signature), not an SP."""
    lower = re.sub(r"\s+", " ", (name or "").strip().lower())
    if not lower:
        return False
    if lower in VIXXO_INTERNAL_COMPANY_NAMES:
        return True
    if lower.startswith("vixxo ") or lower.endswith(" vixxo"):
        return True
    if "vixxo corporation" in lower or "vixxo facility" in lower:
        return True
    return False


def pick_best_company(candidates: list[str], email: str = "") -> str | None:
    """Choose the strongest SP company string from competing extractions."""
    cleaned: list[str] = []
    for raw in candidates:
        company = sanitize_company(raw)
        if not company or is_vixxo_internal_company(company):
            continue
        if company not in cleaned:
            cleaned.append(company)
    if not cleaned:
        return None

    email_stem = ""
    if email and "@" in email:
        email_stem = email.split("@", 1)[1].lower().split(".")[0].replace("-", "")

    def score(name: str) -> tuple:
        lower = name.lower()
        base = strip_company_suffix(name).lower()
        points = 0
        if re.search(COMPANY_SUFFIX, name, re.I):
            points += 2
        if JOB_TITLE_PREFIX_RE.search(name):
            points -= 4
        if is_vixxo_internal_company(name):
            points -= 20
        if email_stem and email_stem in lower.replace("-", "").replace(" ", ""):
            points += 3
        if email_stem and base.replace(" ", "") in email_stem:
            points += 2
        # Prefer compact SP names over subject boilerplate leftovers.
        if len(name) > 60:
            points -= 3
        if name.isupper() and len(name.split()) <= 4:
            points += 1
        # On ties keep earlier candidate (subject before signature).
        try:
            order = -cleaned.index(name)
        except ValueError:
            order = -99
        return (points, order, -len(name), name)

    return max(cleaned, key=score)


def is_valid_company_string(name: str) -> bool:
    """Reject body paragraphs, boilerplate, and client-site subject lines."""
    cleaned = (name or "").strip()
    if len(cleaned) < 3 or len(cleaned) > 80:
        return False
    if re.match(r"^[>&]", cleaned):
        return False
    lower = cleaned.lower()
    if lower in GENERIC_MAILBOX_NAMES or is_generic_mailbox_name(cleaned):
        return False
    if is_vixxo_internal_company(cleaned):
        return False
    if any(phrase in lower for phrase in INVALID_COMPANY_PHRASES):
        return False
    if VIXXO_CLIENT_SUBJECT_RE.match(cleaned):
        return False
    if re.match(r"^new\s+\d+\s+days?\s+notice\b", lower):
        return False
    if re.search(r"\b1-\d{9,10}\b", cleaned):
        return False
    if re.match(r"^(this was|re:|fw:|fwd:)", lower):
        return False
    if is_voicemail_noise_subject(cleaned):
        return False
    if re.search(r"\bnew voicemail\b", lower):
        return False
    if re.search(r"\bvia\s+v(?:endor|ixxo)", lower):
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
        if re.search(r"@(01[a-f0-9]{4,}\.|cid:|image\d)", addr, re.I):
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


# Words that appear in SP trade names — not first/last person names.
_PERSON_NAME_TRADE_BLOCKLIST = frozenset(
    {
        "open", "door", "lock", "lockout", "locks", "key", "keys",
        "repair", "repairs", "service", "services", "commercial",
        "food", "foodservice", "electric", "electrical", "plumbing",
        "hvac", "mechanical", "security", "signs", "sign", "glass",
        "janitorial", "cleaning", "ventures", "solutions", "group",
        "company", "industries", "systems", "contractors", "contractor",
    }
)


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
    if len(parts) != 2 or not all(p[0].isupper() for p in parts if p):
        return False
    # "Open Door" / "Atlantic Foodservice" are companies, not people
    if any(p.lower().rstrip(".,") in _PERSON_NAME_TRADE_BLOCKLIST for p in parts):
        return False
    return True


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

    for pattern in (
        SIGNATURE_ROLE_FOR_RE,
        SIGNATURE_BEFORE_PHONE_RE,
        SIGNATURE_SOFT_BEFORE_PHONE_RE,
    ):
        for match in pattern.finditer(text):
            candidates.append(match.group(1))

    for match in SIGNATURE_LINE_RE.finditer(text):
        candidates.append(match.group(1))

    # Prefer body lines that align with the requester email domain (cookslocksmith.com).
    if email and "@" in email:
        stem = email.split("@", 1)[1].lower().split(".")[0].replace("-", "")
        if stem and len(stem) >= 4:
            for line in text.split("\n"):
                compact = re.sub(r"[^a-z0-9]", "", line.lower())
                if stem in compact and 3 <= len(line.strip()) <= 80:
                    candidates.append(line.strip())

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    # Name / Company / phone closings (e.g. Justin Shaw\nOpen Door\n9709036185)
    for idx in range(len(lines) - 2):
        line = re.sub(r"^>+\s*", "", lines[idx]).strip()
        nxt = re.sub(r"^>+\s*", "", lines[idx + 1]).strip()
        phone_ln = re.sub(r"^>+\s*", "", lines[idx + 2]).strip()
        if (
            is_probable_person_name(line)
            and nxt
            and 2 <= len(nxt) <= 60
            and not re.search(r"[@]|https?://", nxt)
            and not is_probable_person_name(nxt)
            and re.search(r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}", phone_ln)
        ):
            candidates.append(nxt)
    for idx in range(len(lines) - 1):
        line = re.sub(r"^>+\s*", "", lines[idx]).strip()
        nxt = re.sub(r"^>+\s*", "", lines[idx + 1]).strip()
        if (
            re.match(r"^[A-Z][A-Z\s.'-]{2,40}$", line)
            and not re.search(r"[@\d]", line)
            and re.match(r"^[A-Z]", nxt)
            and not re.search(r"[@]|https?://|\d{3}[-.\s]\d{3}", nxt)
            and not re.search(COMPANY_SUFFIX, nxt, re.I)
        ):
            candidates.append(nxt)
    for idx, line in enumerate(lines):
        if re.search(
            r"(?:\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|www\.|https?://|maps\.google)",
            line,
            re.I,
        ):
            if idx > 0 and re.search(COMPANY_SUFFIX, lines[idx - 1], re.I):
                candidates.append(lines[idx - 1])

    for idx in range(len(lines) - 1):
        line1 = re.sub(r"^>+\s*", "", lines[idx]).strip()
        line2 = re.sub(r"^>+\s*", "", lines[idx + 1]).strip()
        if line2.startswith("&") and line1 and not re.search(COMPANY_SUFFIX, line1, re.I):
            combined = f"{line1.rstrip(',')} {line2}".strip()
            candidates.append(combined)

    cleaned: list[str] = []
    for raw in candidates:
        company = sanitize_company(raw)
        if company and company not in cleaned:
            cleaned.append(company)

    picked = pick_best_company(cleaned, email)
    if picked:
        return picked

    return cleaned[0] if cleaned else None


CASE_SUBJECT_KS_RE = re.compile(r"\b(KS\d+)\b", re.I)
CASE_SUBJECT_TAIL_RE = re.compile(
    r"\s+(?:Rate Change|Onboarding|COI(?:\s+Request)?|Update|Renewal|Invoice)\s*$",
    re.I,
)

SUBJECT_PREFIX_RE = re.compile(r"^(?:re|fw|fwd)\s*:\s*", re.I)

SUBJECT_SPM_OPERATIONAL_TAIL_RE = re.compile(
    r"(?:"
    r"\s*[-–—]\s*(?:"
    r"SP Touchpoint|Global Customer Run SP|Customer Run SC#?|"
    r"Purchase Order|Portal Inquiry|VixxoLink(?:\s+Support)?|"
    r"Onboarding(?:\s+Setup)?|Rate Change|COI(?:\s+Request)?|"
    r"Update|Renewal|Invoice Support|Vixxo(?:\s+profile)?"
    r")"
    r"|\s+Vixxo(?:\s+profile)?\s*$"
    r"|(?:\s+VixxoLink)?\s+Training Reminder(?:\s*[-–—]\s*Final Notice)?"
    r")\s*$",
    re.I,
)

SUBJECT_KS_PREFIX_RE = re.compile(r"^KS\s*[-–—]\s*", re.I)

SUBJECT_KS_DASH_COMPANY_RE = re.compile(
    r"^KS\s*[-–—]\s*(.+?)\s*[-–—]\s*.+$",
    re.I,
)

SUBJECT_PURCHASE_ORDER_RE = re.compile(
    r"^(.+?)\s+Purchase Order\s*$",
    re.I,
)

SUBJECT_COMPANY_BEFORE_DASH_RE = re.compile(
    r"^(.+?)\s*[-–—]\s*(?:Global Customer Run SP|SP Touchpoint|Customer Run SC#?)\s*$",
    re.I,
)

SERVICE_CONTRACTOR_RE = re.compile(
    r"Service Contractor:\s*(\d{4,6})\s+(.+?)(?:\s*\n|\s*Fax|$)",
    re.I | re.M,
)

SP_NUMBER_BODY_RE = re.compile(
    r"(?:SP Number|Service Provider(?:\s+Number)?|SP#?)\s*[:#]?\s*(KS\d+|\d{4,6}|F\d+)",
    re.I,
)

SP_HASH_SUBJECT_RE = re.compile(r"#(\d{4,6})\b")

AMAZON_CONNECT_ANI_RE = re.compile(r"\bAni:\s*\n?\s*(\+?\d[\d\s().-]{7,18})", re.I | re.M)
AMAZON_CONNECT_MESSAGE_RE = re.compile(
    r"\bMessage:\s*\n?\s*(.+?)(?:\n\n|\Z)",
    re.I | re.S,
)
VOICEMAIL_TRIAGE_COMPANY_RE = re.compile(r"^Company:\s*(.+?)\s*$", re.I | re.M)
VOICEMAIL_TRIAGE_CALLBACK_RE = re.compile(r"^Callback:\s*([\d\s().+-]+)\s*$", re.I | re.M)
VOICEMAIL_TRIAGE_CALLER_RE = re.compile(r"^Caller:\s*(.+?)\s*$", re.I | re.M)

COMPANY_FROM_SPOKEN_RE = re.compile(
    r"\b(?:this is|i'?m|i am|my name is)\s+[\w'.-]+(?:\s+[\w'.-]+){0,3}"
    r"\s+(?:with|from)\s+([A-Za-z0-9 &.'/-]+?)"
    r"(?:\.|,|$|\s+(?:i'?m|i am|calling|trying|phone|and))",
    re.I,
)

VOICEMAIL_NOISE_SUBJECT_RE = re.compile(
    r"^(?:"
    r"vixxo voicemail|new voicemail|certificates of insurance|"
    r"caller left \d+ minutes?"
    r")",
    re.I,
)

SR_STANDARD_RE = re.compile(r"\b(1-\d{10})\b")
SR_EXPLICIT_RE = re.compile(
    r"\bSR[-\s#:]*1[-\s.]*(\d{3})[-\s.]*(\d{3})[-\s.]*(\d{4})\b",
    re.I,
)
SR_NUMBER_LABEL_RE = re.compile(
    r"\bSR\s*(?:Number|#)\s*:?\s*(1[-\d\s.]{12,22})",
    re.I,
)
ANI_BLOCK_RE = re.compile(r"\bAni:\s*\n?\s*\+?\d[\d\s().-]{7,18}", re.I | re.M)


def _strip_subject_prefix(subject: str) -> str:
    text = (subject or "").strip()
    while SUBJECT_PREFIX_RE.match(text):
        text = SUBJECT_PREFIX_RE.sub("", text, count=1).strip()
    return text


def _strip_subject_operational_tails(text: str) -> str:
    cleaned = CASE_SUBJECT_TAIL_RE.sub("", text).strip()
    cleaned = SUBJECT_SPM_OPERATIONAL_TAIL_RE.sub("", cleaned).strip()
    cleaned = SUBJECT_YOUR_ACCOUNT_VIXXO_RE.sub("", cleaned).strip()
    cleaned = SUBJECT_SP_NUMBER_TAIL_RE.sub("", cleaned).strip()
    cleaned = SUBJECT_KS_PREFIX_RE.sub("", cleaned).strip()
    return cleaned


def _subject_company_candidates(subject: str) -> list[str]:
    """Ordered company-name candidates mined from a Case/email subject."""
    text = _strip_subject_prefix(subject)
    if not text:
        return []

    candidates: list[str] = []
    for pattern in (
        SUBJECT_KS_DASH_COMPANY_RE,
        SUBJECT_COMPANY_BEFORE_DASH_RE,
        SUBJECT_PURCHASE_ORDER_RE,
        SUBJECT_APPROVED_FOR_RE,
    ):
        match = pattern.search(text) if pattern is SUBJECT_APPROVED_FOR_RE else pattern.match(text)
        if match:
            hit = sanitize_company(match.group(1).strip())
            if hit:
                candidates.append(hit)

    stripped = _strip_subject_operational_tails(text)
    if stripped and stripped != text:
        hit = sanitize_company(stripped)
        if hit:
            candidates.append(hit)

    ks_match = CASE_SUBJECT_KS_RE.search(text)
    if ks_match:
        prefix = _strip_subject_operational_tails(text[: ks_match.start()].strip(" -–—"))
        if prefix:
            hit = sanitize_company(prefix)
            if hit:
                candidates.append(hit)
        suffix = _strip_subject_operational_tails(text[ks_match.end() :].strip(" -–—"))
        if suffix and not is_vixxo_internal_company(suffix):
            hit = sanitize_company(suffix)
            if hit:
                candidates.append(hit)
    elif stripped and stripped != text:
        pass  # already added stripped variant above
    else:
        hit = sanitize_company(_strip_subject_operational_tails(text))
        if hit:
            candidates.append(hit)

    # Preserve first-match priority; drop duplicates while keeping order.
    ordered: list[str] = []
    seen: set[str] = set()
    for name in candidates:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(name)
    return ordered


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

    for candidate in _subject_company_candidates(subject):
        return candidate
    return None


def parse_sf_case_subject(subject: str) -> dict[str, str | None]:
    """Mine KS number and SP company name from a Salesforce Case Subject."""
    if not subject:
        return {"ks_number": None, "company": None}
    text = _strip_subject_prefix(subject)
    ks_match = CASE_SUBJECT_KS_RE.search(text)
    ks_number = ks_match.group(1).upper() if ks_match else None

    company = extract_subject_company(subject)
    if not company and ks_match:
        company_text = text[: ks_match.start()].strip(" -–—")
        company_text = _strip_subject_operational_tails(company_text).strip()
        company = sanitize_company(company_text) if company_text else None

    return {"ks_number": ks_number, "company": company}


def extract_service_contractor(text: str) -> dict[str, str | None]:
    """Mine SP number + company from dispatch/cancellation emails."""
    if not text:
        return {"sp_number": None, "company": None}
    match = SERVICE_CONTRACTOR_RE.search(text.replace("\r\n", "\n"))
    if not match:
        return {"sp_number": None, "company": None}
    sp_number = match.group(1).strip()
    company = sanitize_company(match.group(2))
    return {"sp_number": sp_number, "company": company}


def extract_sp_numbers(text: str, *, attachment_names: list[str] | None = None) -> list[str]:
    """Collect Siebel/Gateway SP numbers from body, subject, and attachment names."""
    found: list[str] = []
    seen: set[str] = set()
    blob = text or ""
    for names in (attachment_names or []):
        blob = f"{blob}\n{names}"

    for pattern in (CASE_SUBJECT_KS_RE, SP_NUMBER_BODY_RE, SP_HASH_SUBJECT_RE):
        for match in pattern.finditer(blob):
            token = match.group(1).upper()
            if token.startswith("KS") or token.isdigit():
                if token not in seen:
                    seen.add(token)
                    found.append(token)
    return found


def normalize_sr_number(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        core = digits[1:]
    elif len(digits) == 10:
        core = digits
    else:
        return None
    return f"1-{core}"


def _sr_scan_text(text: str) -> str:
    """Remove ANI/phone lines so callback numbers are not mistaken for SRs."""
    scrubbed = ANI_BLOCK_RE.sub("", text or "")
    scrubbed = re.sub(
        r"\bphone number is\s+\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",
        "",
        scrubbed,
        flags=re.I,
    )
    return scrubbed


def extract_sr_numbers(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    blob = _sr_scan_text(text)

    for match in SR_EXPLICIT_RE.finditer(blob):
        sr = f"1-{match.group(1)}{match.group(2)}{match.group(3)}"
        if sr not in seen:
            seen.add(sr)
            found.append(sr)

    for match in SR_NUMBER_LABEL_RE.finditer(blob):
        sr = normalize_sr_number(match.group(1))
        if sr and sr not in seen:
            seen.add(sr)
            found.append(sr)

    for match in SR_STANDARD_RE.finditer(blob):
        sr = match.group(1)
        if sr not in seen:
            seen.add(sr)
            found.append(sr)

    return found


def extract_amazon_connect_voicemail(body: str) -> dict[str, str | None]:
    """Parse Amazon Connect voicemail block in SF Case Description."""
    if not body or "amazon connect" not in body.lower():
        return {
            "ani": None,
            "message": None,
            "callback_phone": None,
            "spoken_company": None,
            "caller_name": None,
            "sr_number": None,
        }
    text = body.replace("\r\n", "\n")
    ani = None
    ani_match = AMAZON_CONNECT_ANI_RE.search(text)
    if ani_match:
        ani = re.sub(r"\D", "", ani_match.group(1))[-10:] or None

    message = None
    msg_match = AMAZON_CONNECT_MESSAGE_RE.search(text)
    if msg_match:
        message = re.sub(r"\s+", " ", msg_match.group(1)).strip()

    spoken_company = None
    if message:
        spoken_match = COMPANY_FROM_SPOKEN_RE.search(message)
        if spoken_match:
            spoken_company = sanitize_company(spoken_match.group(1))
        if not spoken_company:
            business_match = re.search(
                r"\bmy business is\s+([A-Za-z0-9 &.'/-]+?)(?:\.|,|$|\s+in\b)",
                message,
                re.I,
            )
            if business_match:
                spoken_company = sanitize_company(business_match.group(1))

    callback_phone = ani
    caller_name = None
    sr_number = None
    if message:
        phones = re.findall(r"\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b", message)
        if phones:
            callback_phone = re.sub(r"\D", "", phones[-1])[-10:]
        name_match = re.search(r"\bmy name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", message, re.I)
        if name_match:
            caller_name = name_match.group(1).strip()
        sr_hits = extract_sr_numbers(message)
        if sr_hits:
            sr_number = sr_hits[0]

    return {
        "ani": ani,
        "message": message,
        "callback_phone": callback_phone,
        "spoken_company": spoken_company,
        "caller_name": caller_name,
        "sr_number": sr_number,
    }


def extract_voicemail_triage_block(body: str) -> dict[str, str | None]:
    """Parse structured SP Voicemail triage header from QSIAP/FD bridge Cases."""
    if not body or "SP Voicemail triage" not in body:
        return {"caller": None, "company": None, "callback": None, "transcript": None}
    text = body.replace("\r\n", "\n")
    caller = None
    company = None
    callback = None
    transcript = None

    caller_match = VOICEMAIL_TRIAGE_CALLER_RE.search(text)
    if caller_match:
        caller = caller_match.group(1).strip()
    company_match = VOICEMAIL_TRIAGE_COMPANY_RE.search(text)
    if company_match:
        company = sanitize_company(company_match.group(1))
    callback_match = VOICEMAIL_TRIAGE_CALLBACK_RE.search(text)
    if callback_match:
        callback = re.sub(r"\D", "", callback_match.group(1))[-10:] or None

    transcript_match = re.search(r"\bTranscript:\s*\n(.+?)(?:\n\n|\Z)", text, re.I | re.S)
    if transcript_match:
        transcript = transcript_match.group(1).strip()

    return {
        "caller": caller,
        "company": company,
        "callback": callback,
        "transcript": transcript,
    }


def is_voicemail_noise_subject(subject: str) -> bool:
    return bool(VOICEMAIL_NOISE_SUBJECT_RE.match(_strip_subject_prefix(subject or "")))


def company_from_spoken_text(text: str) -> str | None:
    if not text:
        return None
    match = COMPANY_FROM_SPOKEN_RE.search(text)
    if match:
        return sanitize_company(match.group(1))
    return None


def extract_email_domains_from_messages(
    email_messages: list[dict],
    *,
    skip_internal: bool = True,
) -> list[str]:
    """Gateway search tokens from EmailMessage FromAddress/ToAddress."""
    tokens: list[str] = []
    seen: set[str] = set()
    for msg in email_messages or []:
        for field in ("FromAddress", "ToAddress", "CcAddress"):
            raw = msg.get(field) or ""
            for addr in EMAIL_RE.findall(str(raw)):
                addr = addr.strip().lower()
                if skip_internal and is_internal_email(addr):
                    continue
                for token in email_domain_search_tokens(addr):
                    if token not in seen:
                        seen.add(token)
                        tokens.append(token)
    return tokens


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
