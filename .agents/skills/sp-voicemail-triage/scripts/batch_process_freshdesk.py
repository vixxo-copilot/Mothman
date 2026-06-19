#!/usr/bin/env python3
"""Batch sp-voicemail-triage for Freshdesk KSOnboarding queue (REST)."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

from transcribe_voicemail import TRANSCRIPT_SOURCE, transcribe_ticket

DEFAULT_DOMAIN = "vixxo-helpdesk.freshdesk.com"
QUERY = "group_id:159000485013 AND status:2 AND type:'KSOnboarding'"
OUT_DIR = Path(__file__).resolve().parent.parent / ".tmp" / "batch-run"
TIMEOUT = 90

NEW_VOICEMAIL_SUBJECT_RE = re.compile(r"\bnew voicemail\b", re.I)
PHONE_RE = re.compile(r"\(\+1(\d{10})\)|\+1(\d{10})|(\d{3})[-. ](\d{3})[-. ](\d{4})")
DURATION_RE = re.compile(r"Duration:\s*(\d{2}:\d{2})", re.I)
CALLER_SUBJECT_RE = re.compile(
    r"voicemail from\s+(.+?)\s+via\s+", re.I
)
CALLER_BODY_RE = re.compile(
    r"New voicemail from\s*\n?\s*(.+?)\s*\(\+", re.I | re.S
)
SR_RE = re.compile(r"\b(?:SR|service request|work order)\s*#?\s*(\d{5,10})\b", re.I)

FOUL_LANGUAGE_TERMS = [
    "fuck",
    "fucker",
    "fucking",
    "fucked",
    "motherfucker",
    "shit",
    "bullshit",
    "shitty",
    "bitch",
    "bastard",
    "asshole",
    "cunt",
    "dickhead",
    "cock",
    "whore",
    "slut",
    "piss off",
]

MIN_FORWARD_DURATION_SECONDS = 10
MAX_FORWARD_SPEECH_WORDS = 2

SKIP_FORWARD_LABELS = {
    "foul-language": "Skipped (foul language detected in transcript)",
    "short-duration": "Skipped (voicemail under 10 seconds)",
    "minimal-speech": "Skipped (blank or minimal speech — one or two words)",
}

SKIP_FORWARD_CATEGORIES = {
    "foul-language": "Foul Language / Abusive",
    "short-duration": "Too Short (<10s)",
    "minimal-speech": "Blank / Minimal Speech",
}

SP_REVIEW_TAG = "sp-name-review-needed"
SP_CONTEXT_TAG = "sp-name-from-voicemail"

BUSINESS_NAME_TERMS = (
    "air",
    "automation",
    "clean",
    "company",
    "co",
    "construction",
    "electric",
    "electrical",
    "facility",
    "fire",
    "glass",
    "group",
    "handyman",
    "hvac",
    "inc",
    "llc",
    "lock",
    "locksmith",
    "maintenance",
    "mechanical",
    "plumbing",
    "refrigeration",
    "repair",
    "roofing",
    "security",
    "services",
    "sign",
    "solutions",
)

COMPANY_STOP_RE = re.compile(
    r"\s+(?:"
    r"my|i|i'm|i am|we|we're|we are|trying|calling|regarding|about|because|"
    r"and|need|needs|the system|to|for|on|with|this|that|can|could|please"
    r")\b.*$",
    re.I,
)

COMPANY_PATTERNS = [
    re.compile(
        r"\b(?:this is|it is|it's|my name is|name is)\s+"
        r"(?P<person>[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){0,3})\s+"
        r"(?:with|from|at)\s+(?P<company>[A-Z0-9][A-Za-z0-9&'.,/ -]{2,80})",
        re.I,
    ),
    re.compile(
        r"\b(?:calling\s+from|calling\s+with|with|from|at)\s+"
        r"(?P<company>[A-Z0-9][A-Za-z0-9&'.,/ -]{2,80})",
        re.I,
    ),
]

CATEGORY_RULES: list[tuple[str, list[str], str]] = [
    ("COI / Compliance", ["coi", "certificate of insurance", "insurance", "acord", "additional insured"], "COI@vixxo.com"),
    ("Payment Information", ["payment", "paid", "check", "remittance", "ach", "wire", "when paid", "haven't received payment"], "aphelp@vixxo.com"),
    ("Billing / Invoice Support", ["invoice", "billing", "rejected", "submit invoice", "resubmit"], "aphelp@vixxo.com"),
    ("VixxoLink Support", ["vixxolink", "portal", "login", "password", "app", "dispatch board", "accept work"], "service.providermanagement@vixxo.com"),
    ("Service Request / Dispatch", ["service request", "work order", "dispatch", "eta", "assigned", "technician", " sr "], "SR_BRANCH"),
    ("Coverage / Onboarding", ["onboard", "onboarding", "coverage", "enrollment", "new provider", "rate card", "activation"], "ONBOARDING_BRANCH"),
    ("Technical / Trade Support", ["warranty", "parts", "technical", "how to fix"], "service.providermanagement@vixxo.com"),
]


def freshdesk_domain() -> str:
    return (os.environ.get("FRESHDESK_DOMAIN") or DEFAULT_DOMAIN).strip() or DEFAULT_DOMAIN


def load_credentials() -> str:
    root = Path(__file__).resolve().parents[4]
    env_path = root / ".env"
    if env_path.is_file():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and not os.environ.get(k):
                os.environ[k] = v
    for name in ("freshdesk_token", "freshdesk_api_key"):
        p = Path.home() / ".vixxo" / name
        if p.is_file() and not os.environ.get("FRESHDESK_API_KEY"):
            os.environ["FRESHDESK_API_KEY"] = p.read_text(encoding="utf-8").strip()
    if not os.environ.get("FRESHDESK_API_KEY") and os.environ.get("FRESHDESK_TOKEN"):
        os.environ["FRESHDESK_API_KEY"] = os.environ["FRESHDESK_TOKEN"]
    key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    if not key:
        raise SystemExit("ERROR: FRESHDESK_API_KEY not configured")
    return key


def auth_headers(api_key: str) -> dict[str, str]:
    token = base64.b64encode(f"{api_key}:X".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def http_json(method: str, path: str, api_key: str, body: dict | None = None) -> Any:
    url = f"https://{freshdesk_domain()}{path}"
    data = None
    headers = auth_headers(api_key)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read()
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def search_tickets(api_key: str) -> list[dict]:
    results: list[dict] = []
    for page in range(1, 11):
        params = {"query": f'"{QUERY}"', "page": str(page)}
        url = f"https://{freshdesk_domain()}/api/v2/search/tickets?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        page_results = data.get("results") or []
        results.extend(page_results)
        if len(page_results) < 30:
            break
    return results


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def is_voicemail_subject(subject: str | None) -> bool:
    return bool(NEW_VOICEMAIL_SUBJECT_RE.search(subject or ""))


def is_voicemail_ticket(ticket: dict) -> bool:
    return is_voicemail_subject(ticket.get("subject"))


def search_voicemail_tickets(api_key: str) -> tuple[list[dict], list[dict]]:
    all_tickets = search_tickets(api_key)
    voicemail = [t for t in all_tickets if is_voicemail_ticket(t)]
    skipped = [t for t in all_tickets if not is_voicemail_ticket(t)]
    return voicemail, skipped


def normalize_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    m = PHONE_RE.search(raw)
    if not m:
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        return digits if len(digits) == 10 else raw.strip()
    groups = m.groups()
    if groups[0]:
        return groups[0]
    if groups[1]:
        return groups[1]
    if groups[2]:
        return f"{groups[2]}{groups[3]}{groups[4]}"
    return raw.strip()


def extract_metadata(ticket: dict) -> dict[str, str | None]:
    subject = ticket.get("subject") or ""
    desc_html = ticket.get("description") or ""
    desc_text = ticket.get("description_text") or strip_html(desc_html)
    blob = f"{subject}\n{desc_text}\n{desc_html}"

    caller = None
    m = CALLER_SUBJECT_RE.search(subject)
    if m:
        caller = m.group(1).strip()
    if not caller:
        m2 = CALLER_BODY_RE.search(desc_html) or CALLER_BODY_RE.search(desc_text)
        if m2:
            caller = re.sub(r"\s+", " ", m2.group(1)).strip()

    phone = normalize_phone(blob)
    duration = None
    dm = DURATION_RE.search(blob)
    if dm:
        duration = dm.group(1)

    return {
        "caller": caller or "Not stated",
        "phone": phone or "Not stated",
        "duration": duration or "Unknown",
        "company": caller if caller and caller.upper() != "WIRELESS CALLER" else "Not stated",
    }


@dataclass
class SpContext:
    name: str = "Unknown"
    source: str = "not-found"
    confidence: str = "none"
    review_required: bool = True

    @property
    def known(self) -> bool:
        return bool(self.name and self.name != "Unknown" and not self.review_required)


def clean_company_candidate(candidate: str | None) -> str:
    value = re.sub(r"\s+", " ", (candidate or "").strip(" ,.-"))
    if not value:
        return ""
    value = COMPANY_STOP_RE.sub("", value).strip(" ,.-")
    value = re.sub(r"\b(?:called|calling)$", "", value, flags=re.I).strip(" ,.-")
    return value


def looks_like_company(candidate: str) -> bool:
    value = clean_company_candidate(candidate)
    if not value or value.lower() in {"vixxo", "vendor relations", "wireless caller"}:
        return False
    if "," in value and not any(term in value.lower() for term in BUSINESS_NAME_TERMS):
        return False
    lower = value.lower()
    if any(re.search(rf"\b{re.escape(term)}\b", lower) for term in BUSINESS_NAME_TERMS):
        return True
    tokens = value.split()
    return len(tokens) >= 2 and any(ch.isdigit() for ch in value)


def infer_sp_context(meta: dict, spoken_text: str) -> SpContext:
    """Use voicemail spoken context before falling back to caller metadata."""
    for pattern in COMPANY_PATTERNS:
        for match in pattern.finditer(spoken_text or ""):
            company = clean_company_candidate(match.group("company"))
            if looks_like_company(company):
                return SpContext(
                    name=company,
                    source="voicemail transcript",
                    confidence="medium",
                    review_required=False,
                )

    caller_company = clean_company_candidate(str(meta.get("company") or ""))
    if looks_like_company(caller_company):
        return SpContext(
            name=caller_company,
            source="caller metadata",
            confidence="low",
            review_required=False,
        )

    return SpContext()


def resolve_cf_sp_value(ticket: dict, sp_context: SpContext) -> str:
    current = ((ticket.get("custom_fields") or {}).get("cf_sp") or "").strip()
    if current and current != "Unknown":
        return current
    if sp_context.known:
        return sp_context.name
    return "Unknown"


def voicemail_summary(
    meta: dict,
    category: str,
    route: str,
    callback: str,
    sr: str,
    spoken_text: str,
    sp_context: SpContext,
) -> str:
    caller = meta.get("caller") or "Unknown caller"
    sp_name = sp_context.name if sp_context.known else "SP name not confirmed"
    reference = f" Reference ID: {sr}." if sr else ""
    route_text = route if "@" in route else "no email route"
    message = re.sub(r"\s+", " ", (spoken_text or "").strip())
    if len(message) > 220:
        message = message[:217].rstrip() + "..."
    return (
        f"{caller} called for {sp_name}; classified as {category} and routed to "
        f"{route_text}. Callback: {callback}.{reference} Message: {message or 'No spoken message captured.'}"
    )


def format_stt_transcript(stt: dict[str, Any], meta: dict, ticket: dict) -> str:
    subject = ticket.get("subject") or ""
    lines = [
        f"Transcript source: {stt.get('source', TRANSCRIPT_SOURCE)}",
        f"Subject: {subject}",
        f"Attachment: {stt.get('attachment_name', 'voicemail.wav')}",
        f"Caller ID: {meta['caller']}",
        f"Callback number: {meta['phone']}",
        f"Duration: {meta['duration']}",
        "",
        stt["transcript"],
    ]
    return "\n".join(lines)


def build_transcript(meta: dict, ticket: dict) -> str:
    subject = ticket.get("subject") or ""
    att_names = [a.get("name") for a in ticket.get("attachments") or [] if a.get("name")]
    lines = [
        f"[Voicemail notification — audio attachment (.wav or .mp3) required; email body has no spoken content]",
        f"Subject: {subject}",
        f"Caller ID: {meta['caller']}",
        f"Callback number: {meta['phone']}",
        f"Duration: {meta['duration']}",
    ]
    if att_names:
        lines.append(f"Attachments: {', '.join(att_names)}")
    lines.append(
        "[Note: Spoken content is only in the audio attachment (.wav or .mp3). Transcribe before triage.]"
    )
    return "\n".join(lines)


def _keyword_in_text(keyword: str, text: str) -> bool:
    if " " in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def detect_foul_language(transcript: str) -> tuple[bool, list[str]]:
    text = transcript.lower()
    hits = [term for term in FOUL_LANGUAGE_TERMS if _keyword_in_text(term, text)]
    return bool(hits), hits


def parse_duration_to_seconds(duration: str | None) -> int | None:
    if not duration or str(duration).strip().lower() == "unknown":
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})$", str(duration).strip())
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def resolve_duration_seconds(meta: dict, stt: dict[str, Any]) -> int | None:
    from_meta = parse_duration_to_seconds(meta.get("duration"))
    if from_meta is not None:
        return from_meta
    raw = stt.get("duration_seconds")
    if raw is None:
        return None
    try:
        return int(round(float(raw)))
    except (TypeError, ValueError):
        return None


def count_speech_words(text: str) -> int:
    cleaned = re.sub(r"[^\w\s'-]", " ", text or "")
    return len([word for word in cleaned.split() if word.strip()])


def detect_skip_forward(
    meta: dict, stt: dict[str, Any], spoken_text: str
) -> tuple[bool, str]:
    foul, _hits = detect_foul_language(spoken_text)
    if foul:
        return True, "foul-language"

    duration_seconds = resolve_duration_seconds(meta, stt)
    if duration_seconds is not None and duration_seconds < MIN_FORWARD_DURATION_SECONDS:
        return True, "short-duration"

    if count_speech_words(spoken_text) <= MAX_FORWARD_SPEECH_WORDS:
        return True, "minimal-speech"

    return False, ""


def classify(transcript: str, meta: dict) -> tuple[str, str, str]:
    text = transcript.lower()
    sr = None
    sm = SR_RE.search(transcript)
    if sm:
        sr = sm.group(1)
    if "audio attachment only" in text or "[inaudible]" in text:
        return "General Inquiry", "service.providermanagement@vixxo.com", sr or ""
    for category, keywords, route in CATEGORY_RULES:
        if any(_keyword_in_text(k, text) for k in keywords):
            if route == "SR_BRANCH" and sr:
                return category, route, sr
            if route == "SR_BRANCH":
                return category, "service.providermanagement@vixxo.com", ""
            if route == "ONBOARDING_BRANCH":
                return category, "spm-recruitment@vixxo.com", ""
            return category, route, sr or ""
    if meta.get("caller", "").upper() == "WIRELESS CALLER":
        return "General Inquiry", "service.providermanagement@vixxo.com", sr or ""
    return "General Inquiry", "service.providermanagement@vixxo.com", sr or ""


def callback_decision(transcript: str) -> tuple[str, str]:
    t = transcript.lower()
    yes_signals = ["call me back", "return my call", "need someone to call", "urgent", "third time"]
    if any(s in t for s in yes_signals):
        return "Yes", "High"
    if "audio attachment only" in t or "wireless caller" in t:
        return "Recommended", "Normal"
    return "Recommended", "Normal"


def internal_note(
    ticket_id: int,
    meta: dict,
    category: str,
    callback: str,
    urgency: str,
    route: str,
    transcript: str,
    sr: str,
    *,
    no_email: bool = False,
    skip_vetting: bool = False,
    transcript_source: str = "metadata-only",
    stt_error: str = "",
    skip_forward_reason: str = "",
    spoken_word_count: int | None = None,
    sp_context: SpContext | None = None,
    summary: str = "",
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sr_line = f"**Reference IDs:** {sr}" if sr else "**Reference IDs:** none"
    sp_context = sp_context or SpContext()
    sp_line = (
        f"**SP name:** {sp_context.name} "
        f"({sp_context.source}, confidence: {sp_context.confidence})"
        if sp_context.known
        else "**SP name:** Unknown - review/update required"
    )
    if skip_forward_reason:
        skip_label = SKIP_FORWARD_LABELS.get(
            skip_forward_reason, f"Skipped ({skip_forward_reason})"
        )
        routing_action = (
            f"- **Forward to:** {skip_label}\n"
            "- **Email forward sent:** No\n"
            "- **Disposition:** Resolve without forward"
        )
    elif no_email:
        routing_action = (
            f"- **Recommended forward to:** {route}\n"
            f"- **Email forward sent:** No (no-email skill)\n"
            f"- **Disposition:** Resolve after internal note"
        )
    else:
        routing_action = (
            f"- **Forward to:** {route}\n"
            f"- **Disposition:** Resolve after forward"
        )
    if skip_vetting:
        vetting_block = (
            "**Company vetting:** Skipped (fast skill - no Gateway/Salesforce MCP lookups)\n\n"
            f"{sp_line}\n\n"
            "**Entity posture:** Unknown (external vetting skipped)"
        )
    else:
        vetting_block = f"""**Company vetting**

| System | Match | ID |
| --- | --- | --- |
| Siebel / Gateway SP | Unknown | — |
| Gateway / VixxoLink Customer | Unknown | — |
| JDE Vendor | Unknown | — |
| Salesforce Lead/Account | Unknown | — |

{sp_line}

**Entity posture:** Unknown (batch REST — vetting deferred; run parent skill with MCP for full vetting)"""

    stt_line = f"**Transcript source:** {transcript_source}"
    if stt_error:
        stt_line += f"\n**Transcription error:** {stt_error}"
    if skip_forward_reason == "foul-language":
        stt_line += "\n**Foul language detected:** Yes — forward skipped per policy"
    elif skip_forward_reason == "short-duration":
        stt_line += (
            f"\n**Duration:** {meta.get('duration', 'Unknown')} "
            f"(under {MIN_FORWARD_DURATION_SECONDS}s — forward skipped)"
        )
    elif skip_forward_reason == "minimal-speech":
        word_count = spoken_word_count if spoken_word_count is not None else 0
        stt_line += (
            f"\n**Speech content:** {word_count} word(s) — forward skipped "
            "(blank or one/two words only)"
        )

    callback_rationales = {
        "foul-language": "Voicemail contained foul language; ticket closed without forward per policy.",
        "short-duration": (
            f"Voicemail under {MIN_FORWARD_DURATION_SECONDS} seconds; "
            "ticket closed without forward per policy."
        ),
        "minimal-speech": (
            "Voicemail blank or only one/two words; "
            "ticket closed without forward per policy."
        ),
    }
    callback_rationale = callback_rationales.get(
        skip_forward_reason,
        (
            "Voicemail left on KS onboarding line; spoken content transcribed from audio attachment."
            if transcript_source == TRANSCRIPT_SOURCE
            else "Voicemail left on KS onboarding line; no audio transcript available."
        ),
    )

    return f"""**SP Voicemail Triage — Freshdesk #{ticket_id}**

**Processed:** {now}
**Category:** {category}
**Callback required:** {callback} ({urgency})
**Caller:** {meta['caller']} | **Company:** {meta['company']}
**Callback #:** {meta['phone']}
{sr_line}
{sp_line}
{stt_line}

---

{vetting_block}

---

**Transcript**

{transcript}

---

**Routing action**

{routing_action}

---

**Summary:** KSOnboarding voicemail processed by sp-voicemail-triage batch. Audio attachment retained on ticket; recipient should listen and callback if needed.

**Voicemail summary:** {summary or 'No summary generated.'}

**Callback rationale:** {callback_rationale}
"""


@dataclass
class Result:
    ticket_id: int
    caller: str
    phone: str
    category: str
    route: str
    callback: str
    sp_name: str = "Unknown"
    sp_name_source: str = "not-found"
    sp_review_required: bool = True
    note: str = ""
    forward: str = ""
    resolve: str = ""
    error: str = ""
    transcribed: str = "no"
    transcript_source: str = "metadata-only"


def process_ticket(
    api_key: str,
    ticket_summary: dict,
    dry_run: bool = False,
    reroute_correction: bool = False,
    no_email: bool = False,
    transcribe: bool = True,
    skip_vetting: bool = False,
) -> Result:
    tid = int(ticket_summary["id"])
    if not is_voicemail_ticket(ticket_summary):
        return Result(
            ticket_id=tid,
            caller="—",
            phone="—",
            category="Skipped",
            route="—",
            callback="—",
            note="skipped:non-voicemail",
        )
    ticket = http_json("GET", f"/api/v2/tickets/{tid}?include=conversations", api_key)
    meta = extract_metadata(ticket)
    transcript_source = "metadata-only"
    stt_error = ""
    transcription_ok = False
    stt: dict[str, Any] = {}
    if transcribe:
        stt = transcribe_ticket(ticket, api_key)
        if stt.get("ok"):
            transcript = format_stt_transcript(stt, meta, ticket)
            transcript_source = str(stt.get("source") or TRANSCRIPT_SOURCE)
            transcription_ok = True
        else:
            stt_error = str(stt.get("error") or "transcription failed")
            transcript = ""
    else:
        stt_error = "transcription disabled (--no-transcribe)"
        transcript = build_transcript(meta, ticket) if dry_run else ""

    if not transcription_ok:
        result = Result(
            ticket_id=tid,
            caller=str(meta["caller"]),
            phone=str(meta["phone"]),
            category="Skipped",
            route="—",
            callback="—",
            transcribed="no",
            transcript_source="failed",
            note="dry-run:transcription-required" if dry_run else "skipped:transcription-required",
            forward="not-sent:transcription-required",
            resolve="not-closed:transcription-required",
            error=stt_error or "transcription required",
        )
        return result

    spoken_text = str(stt.get("transcript") or "")
    spoken_word_count = count_speech_words(spoken_text)
    sp_context = infer_sp_context(meta, spoken_text)
    skip_forward, skip_forward_reason = detect_skip_forward(meta, stt, spoken_text)

    category, route, sr = classify(transcript, meta)
    if skip_forward:
        category = SKIP_FORWARD_CATEGORIES.get(skip_forward_reason, category)
        route = "—"
    callback, urgency = callback_decision(transcript)
    if skip_forward:
        callback, urgency = "No", "Normal"

    if category == "Service Request / Dispatch" and sr and not skip_forward:
        route = "service.providermanagement@vixxo.com"
        forward_subject = f"{sr}, Need Assistance"
    else:
        forward_subject = None
    summary = voicemail_summary(meta, category, route, callback, sr, spoken_text, sp_context)

    note_body = internal_note(
        tid,
        meta,
        category,
        callback,
        urgency,
        route,
        transcript,
        sr,
        no_email=no_email,
        skip_vetting=skip_vetting,
        transcript_source=transcript_source,
        stt_error=stt_error,
        skip_forward_reason=skip_forward_reason,
        spoken_word_count=spoken_word_count,
        sp_context=sp_context,
        summary=summary,
    )
    result = Result(
        ticket_id=tid,
        caller=str(meta["caller"]),
        phone=str(meta["phone"]),
        category=category,
        route=route,
        callback=callback,
        sp_name=sp_context.name,
        sp_name_source=sp_context.source,
        sp_review_required=sp_context.review_required,
        transcribed="yes" if transcript_source == TRANSCRIPT_SOURCE else "no",
        transcript_source=transcript_source,
    )

    if dry_run:
        result.note = f"dry-run:{skip_forward_reason}" if skip_forward_reason else "dry-run"
        return result

    try:
        http_json(
            "POST",
            f"/api/v2/tickets/{tid}/notes",
            api_key,
            {"body": note_body, "private": True},
        )
        result.note = "posted"
    except urllib.error.HTTPError as exc:
        result.note = f"failed:{exc.code}"
        result.error = f"note:{exc.reason}"

    if skip_forward:
        result.forward = f"not-sent:{skip_forward_reason}"
    elif no_email:
        result.forward = "not-sent:no-email"
    else:
        forward_body = (
            f"SP Voicemail triage — Freshdesk #{tid}\n\n"
            f"Category: {category}\n"
            f"SP name: {sp_context.name if sp_context.known else 'Unknown - review/update required'}\n"
            f"Caller: {meta['caller']}\n"
            f"Callback: {meta['phone']}\n"
            f"Callback required: {callback}\n"
            f"Summary: {summary}\n\n"
            f"{transcript}\n\n"
            f"— Automated triage (sp-voicemail-triage). Please listen to the attached "
            f"voicemail for full message content."
        )
        if sp_context.review_required:
            forward_body += (
                "\n\nSP name review needed: voicemail context did not identify a service "
                "provider name. Please update Freshdesk cf_sp if known."
            )
        if reroute_correction:
            forward_body += (
                "\nNote: Prior misroute to AP (keyword false match) — corrected forward to SPM."
            )
        if forward_subject:
            forward_body = f"Requested subject: {forward_subject}\n\n{forward_body}"
        fwd_payload: dict[str, Any] = {
            "body": forward_body,
            "to_emails": [route] if "@" in route else [],
        }

        try:
            if fwd_payload.get("to_emails"):
                http_json("POST", f"/api/v2/tickets/{tid}/forward", api_key, fwd_payload)
                result.forward = route
            else:
                result.forward = "skipped"
        except urllib.error.HTTPError as exc:
            result.forward = f"failed:{exc.code}"
            if not result.error:
                result.error = f"forward:{exc.reason}"

    try:
        existing_tags = list(ticket.get("tags") or [])
        tags = existing_tags
        if sp_context.known:
            tags = sorted(set(existing_tags + [SP_CONTEXT_TAG]))
        elif "@" in str(result.forward):
            tags = sorted(set(existing_tags + [SP_REVIEW_TAG]))
        update_payload: dict[str, Any] = {
            "status": 5,
            "type": "KSOnboarding",
            "custom_fields": {"cf_sp": resolve_cf_sp_value(ticket, sp_context)},
        }
        if tags != existing_tags:
            update_payload["tags"] = tags
        http_json(
            "PUT",
            f"/api/v2/tickets/{tid}",
            api_key,
            update_payload,
        )
        result.resolve = "closed"
    except urllib.error.HTTPError as exc:
        result.resolve = f"failed:{exc.code}"
        if not result.error:
            result.error = f"resolve:{exc.reason}"

    return result


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    reroute_correction = "--reroute-spm" in sys.argv
    no_email = "--no-email" in sys.argv
    skip_vetting = "--skip-vetting" in sys.argv
    transcribe = "--no-transcribe" not in sys.argv
    api_key = load_credentials()
    if transcribe:
        from transcribe_voicemail import get_whisper_model  # noqa: PLC0415

        try:
            get_whisper_model()
        except RuntimeError as exc:
            raise SystemExit(f"ERROR: {exc}") from exc
    tickets, skipped = search_voicemail_tickets(api_key)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[Result] = []
    for t in tickets:
        try:
            results.append(
                process_ticket(
                    api_key,
                    t,
                    dry_run=dry_run,
                    reroute_correction=reroute_correction,
                    no_email=no_email,
                    transcribe=transcribe,
                    skip_vetting=skip_vetting,
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                Result(
                    ticket_id=int(t.get("id", 0)),
                    caller="?",
                    phone="?",
                    category="?",
                    route="?",
                    callback="?",
                    error=str(exc),
                )
            )

    summary = {
        "processed": len(results),
        "skipped_non_voicemail": len(skipped),
        "skipped_ids": [int(t["id"]) for t in skipped],
        "dry_run": dry_run,
        "skip_vetting": skip_vetting,
        "transcribe": transcribe,
        "transcribed": sum(1 for r in results if r.transcribed == "yes"),
        "transcription_failed": sum(
            1 for r in results if str(r.note).startswith("skipped:transcription-required")
        ),
        "transcription_failed_ids": [
            r.ticket_id
            for r in results
            if str(r.note).startswith("skipped:transcription-required")
        ],
        "transcription_errors": {
            str(r.ticket_id): r.error
            for r in results
            if str(r.note).startswith("skipped:transcription-required") and r.error
        },
        "routed": sum(
            1
            for r in results
            if r.forward
            and not str(r.forward).startswith("failed")
            and not str(r.forward).startswith("not-sent:")
        ),
        "foul_language_closed": sum(
            1 for r in results if str(r.forward) == "not-sent:foul-language" and r.resolve == "closed"
        ),
        "short_duration_closed": sum(
            1 for r in results if str(r.forward) == "not-sent:short-duration" and r.resolve == "closed"
        ),
        "minimal_speech_closed": sum(
            1 for r in results if str(r.forward) == "not-sent:minimal-speech" and r.resolve == "closed"
        ),
        "no_email": no_email,
        "closed": sum(1 for r in results if r.resolve == "closed"),
        "sp_inferred": sum(1 for r in results if r.sp_name != "Unknown"),
        "sp_review_required": sum(
            1 for r in results if r.transcribed == "yes" and r.sp_review_required
        ),
        "sp_review_required_ids": [
            r.ticket_id for r in results if r.transcribed == "yes" and r.sp_review_required
        ],
        "forwarded_without_sp_ids": [
            r.ticket_id for r in results if r.sp_review_required and "@" in str(r.forward)
        ],
        "failed": [r.ticket_id for r in results if r.error or str(r.note).startswith("failed")],
        "results": [r.__dict__ for r in results],
    }
    out_path = OUT_DIR / f"batch-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary_path": str(out_path),
                **{
                    k: summary[k]
                    for k in (
                        "processed",
                        "transcribed",
                        "transcription_failed",
                        "foul_language_closed",
                        "short_duration_closed",
                        "minimal_speech_closed",
                        "routed",
                        "closed",
                        "sp_inferred",
                        "sp_review_required",
                        "sp_review_required_ids",
                        "forwarded_without_sp_ids",
                        "failed",
                    )
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
