"""Transcript-first entity extraction for qsiap@vixxo.com voicemails."""

from __future__ import annotations

import re
from typing import Any

from entity_extraction import (
    extract_body_company_mentions,
    extract_signature_company,
    is_probable_person_name,
    is_valid_company_string,
    pick_best_company,
    sanitize_company,
)

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


def is_caller_id_label(caller: str | None) -> bool:
    """True when 8x8 caller ID should not be used as company name."""
    raw = (caller or "").strip()
    if not raw or raw.upper() in {"NOT STATED", "UNKNOWN", "WIRELESS CALLER"}:
        return True
    if CALLER_ID_USER_RE.match(raw):
        return True
    if "," in raw and not re.search(r"LLC|Inc|Corp|Company|Services|Lock", raw, re.I):
        return True
    if is_probable_person_name(raw.replace(",", " ")):
        return True
    # Truncated / generic mailbox-style labels from 8x8
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
    if m:
        name = re.sub(r"\s+", " ", m.group(1)).strip(" .,")
        if name and not is_caller_id_label(name):
            return name
    return None


def extract_company_from_transcript(transcript: str) -> str | None:
    if not transcript:
        return None
    candidates: list[str] = []
    candidates.extend(extract_body_company_mentions(transcript))
    sig = extract_signature_company(transcript)
    if sig:
        candidates.append(sig)
    for m in WITH_FROM_COMPANY_RE.finditer(transcript):
        hit = sanitize_company(m.group(1))
        if hit:
            candidates.append(hit)
    picked = pick_best_company(candidates)
    if picked and is_valid_company_string(picked):
        return picked
    return None


def extract_phone_from_transcript(transcript: str) -> str | None:
    m = PHONE_IN_TRANSCRIPT_RE.search(transcript or "")
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    if len(digits) >= 10:
        return digits[-10:]
    return None


def merge_transcript_entities(
    entities: dict[str, Any],
    transcript: str,
    meta: dict[str, str | None],
) -> dict[str, Any]:
    """Overlay transcript-derived contact/company/SR hints onto ticket entities."""
    out = dict(entities)
    spoken_contact = extract_contact_from_transcript(transcript)
    spoken_company = extract_company_from_transcript(transcript)

    caller = meta.get("caller")
    if spoken_contact:
        out["contact_name"] = spoken_contact
        out["vetting_contact_name"] = spoken_contact
    elif is_caller_id_label(caller):
        normalized = normalize_caller_id_name(caller)
        if normalized and is_probable_person_name(normalized):
            out["contact_name"] = normalized
            out["vetting_contact_name"] = normalized

    if spoken_company:
        out["company"] = spoken_company
        if spoken_company != "Not stated":
            out["signature_company"] = spoken_company
    elif is_caller_id_label(out.get("company")) or is_caller_id_label(caller):
        # Drop misleading caller-ID-as-company from ticket metadata path.
        if out.get("company") == caller or is_caller_id_label(out.get("company")):
            out["company"] = "Not stated"

    phone = extract_phone_from_transcript(transcript) or meta.get("phone")
    if phone and phone != "Not stated":
        out["callback_phone"] = phone

    out["transcript"] = transcript.strip() if transcript else None
    return out


def transcribe_ticket_text(ticket: dict, api_key: str) -> tuple[str | None, str | None]:
    """Return (spoken_text, error)."""
    try:
        from transcribe_voicemail import transcribe_ticket  # noqa: WPS433

        stt = transcribe_ticket(ticket, api_key)
        if not stt.get("ok"):
            return None, stt.get("error") or "transcription failed"
        spoken = (stt.get("transcript") or "").strip()
        return spoken or None, None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
