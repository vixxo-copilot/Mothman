"""Transcript-first entity helpers for qsiap@vixxo.com voicemails."""

from __future__ import annotations

import re
from typing import Any

MY_NAME_RE = re.compile(
    r"(?:my name is|this is|i'?m|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z'\-]+){0,3})",
    re.I,
)
WITH_FROM_COMPANY_RE = re.compile(
    r"(?:with|from|at|for)\s+([A-Z0-9][A-Za-z0-9&'\.,\-\s]{2,60}?)"
    r"(?:\.|,|\s+(?:and|i'?m|i am|my|phone|calling|we|our)\b|$)",
    re.I,
)
CALLER_ID_USER_RE = re.compile(r"^user\s+\d+$", re.I)
PHONE_IN_TRANSCRIPT_RE = re.compile(
    r"(?:call(?:\s+me\s+)?back\s+(?:at\s+)?|phone(?:\s+number)?(?:\s+is)?\s+)"
    r"((?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
    re.I,
)
LEGAL_SUFFIX_RE = re.compile(
    r"\b(LLC|L\.L\.C\.|Inc\.?|Incorporated|Corp\.?|Corporation|Co\.|Company|"
    r"Services|Service|Electric|Plumbing|HVAC|Locksmith|Mechanical)\b",
    re.I,
)


def is_caller_id_label(caller: str | None) -> bool:
    """True when 8x8 caller ID should not be used as company name."""
    raw = (caller or "").strip()
    if not raw or raw.upper() in {"NOT STATED", "UNKNOWN", "WIRELESS CALLER"}:
        return True
    if CALLER_ID_USER_RE.match(raw):
        return True
    if "," in raw and not LEGAL_SUFFIX_RE.search(raw):
        return True
    tokens = [t for t in re.split(r"[\s,]+", raw) if t]
    if 1 <= len(tokens) <= 3 and all(t[:1].isupper() for t in tokens) and not LEGAL_SUFFIX_RE.search(raw):
        # Person-like "FIRST LAST" / "LAST,FIRST" without company cues
        if "," in raw or (len(tokens) == 2 and all(t.isalpha() for t in tokens)):
            return True
    if raw.upper() in {"LOCKSMITH", "GENERAL FIX-IT", "ANDREWS REFRIGE"}:
        return True
    return False


def normalize_caller_id_name(caller: str | None) -> str | None:
    """Convert LAST,FIRST caller ID to a person name when possible."""
    raw = (caller or "").strip()
    if not raw or "," not in raw:
        return raw or None
    last, first = [p.strip() for p in raw.split(",", 1)]
    if last and first:
        return f"{first} {last}"
    return raw


def extract_contact_from_transcript(transcript: str) -> str | None:
    m = MY_NAME_RE.search(transcript or "")
    if not m:
        return None
    name = re.sub(r"\s+", " ", m.group(1)).strip(" .,")
    if name and not is_caller_id_label(name):
        return name
    return None


def extract_company_from_transcript(transcript: str) -> str | None:
    if not transcript:
        return None
    candidates: list[str] = []
    for m in WITH_FROM_COMPANY_RE.finditer(transcript):
        hit = re.sub(r"\s+", " ", m.group(1)).strip(" .,")
        if hit and not is_caller_id_label(hit) and len(hit) >= 3:
            candidates.append(hit)
    # Prefer candidates with legal/trade suffixes
    scored = sorted(
        candidates,
        key=lambda c: (1 if LEGAL_SUFFIX_RE.search(c) else 0, len(c)),
        reverse=True,
    )
    return scored[0] if scored else None


def extract_phone_from_transcript(transcript: str) -> str | None:
    m = PHONE_IN_TRANSCRIPT_RE.search(transcript or "")
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    if len(digits) >= 10:
        return digits[-10:]
    return None


def merge_transcript_entities(
    meta: dict[str, Any],
    transcript: str,
) -> dict[str, str | None]:
    """Overlay transcript-derived contact/company/phone onto 8x8 metadata."""
    spoken_contact = extract_contact_from_transcript(transcript)
    spoken_company = extract_company_from_transcript(transcript)
    caller = meta.get("caller")

    contact = spoken_contact
    if not contact and not is_caller_id_label(caller):
        contact = str(caller) if caller else None
    elif not contact:
        contact = normalize_caller_id_name(caller)

    company = spoken_company
    if not company:
        if caller and not is_caller_id_label(caller) and LEGAL_SUFFIX_RE.search(str(caller)):
            company = str(caller)
        else:
            company = "Not stated"

    phone = extract_phone_from_transcript(transcript) or meta.get("phone")
    return {
        "caller": contact or str(caller or "Not stated"),
        "company": company,
        "phone": phone if phone and phone != "Not stated" else meta.get("phone"),
    }
