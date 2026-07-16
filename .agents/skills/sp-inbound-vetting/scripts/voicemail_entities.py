"""Shared entity enrichment for Freshdesk voicemail tickets."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import extract_metadata, strip_html  # noqa: E402
from entity_extraction import caller_id_search_tokens  # noqa: E402

SR_CTX_RE = re.compile(
    r"(?:SR|service request|work order)[^\d]{0,40}(1[-\d]{10,18})",
    re.I,
)
SR_RE = re.compile(r"\b(1[-\d]{10,18})\b")


def normalize_sr(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        core = digits[1:]
    elif len(digits) == 10:
        core = digits
    else:
        return None
    return f"1-{core}"


def ticket_blob(ticket: dict) -> str:
    parts = [
        ticket.get("subject") or "",
        ticket.get("description_text") or strip_html(ticket.get("description") or ""),
    ]
    for conv in ticket.get("conversations") or []:
        parts.append(conv.get("body_text") or strip_html(conv.get("body") or ""))
    return " ".join(parts)


def extract_srs(text: str, phone: str | None) -> list[str]:
    phone_digits = re.sub(r"\D", "", phone or "")[-10:]
    found: list[str] = []
    seen: set[str] = set()
    for match in SR_CTX_RE.finditer(text):
        sr = normalize_sr(match.group(1))
        if sr and sr not in seen:
            seen.add(sr)
            found.append(sr)
    for match in SR_RE.finditer(text):
        sr = normalize_sr(match.group(1))
        if not sr:
            continue
        if phone_digits and re.sub(r"\D", "", sr)[1:] == phone_digits:
            continue
        if sr not in seen:
            seen.add(sr)
            found.append(sr)
    return found


def enrich_voicemail_entities(ticket: dict, entities: dict[str, Any]) -> dict[str, Any]:
    """Map caller ID / transcript metadata into vetting entity fields."""
    meta = extract_metadata(ticket)
    caller = str(meta.get("caller") or "Not stated").strip()
    if caller not in ("Not stated", "Unknown", "WIRELESS CALLER"):
        entities["contact_name"] = caller
        tokens = caller_id_search_tokens(caller)
        entities["vetting_contact_name"] = tokens[0] if tokens else caller
        entities["caller_id_tokens"] = tokens

    text = ticket_blob(ticket)
    srs = extract_srs(text, meta.get("phone"))
    if srs and not entities.get("sr_number"):
        entities["sr_number"] = srs[0]

    phone = meta.get("phone")
    if phone and phone not in ("Not stated", ""):
        entities.setdefault("callback_phone", phone)

    return entities
