"""Parse voicemail Case descriptions and match open work-in-progress Cases."""

from __future__ import annotations

import re

from sf_case_buckets import (
    BUCKET_VOICEMAIL,
    classify_case,
    classify_voicemail_intent,
    extract_sp_name,
    normalize_sp_key,
    voicemail_may_route_to_target,
)
from sf_merge_primary import (
    has_activity_touch,
    is_actively_worked,
    is_open,
    is_user_assigned,
    last_touch_at,
)

FD_TICKET_RE = re.compile(r"Freshdesk\s*#(\d+)", re.I)
CALLER_RE = re.compile(r"Caller:\s*(.+?)(?:\n|$)", re.I)
COMPANY_RE = re.compile(r"Company:\s*(.+?)(?:\n|$)", re.I)
CALLBACK_RE = re.compile(r"Callback:\s*(.+?)(?:\n|$)", re.I)
CATEGORY_RE = re.compile(r"Category:\s*(.+?)(?:\n|$)", re.I)
ROUTE_RE = re.compile(r"Route:\s*(.+?)(?:\n|$)", re.I)
SPM_HEADER_RE = re.compile(r"SP Voicemail triage", re.I)
TRANSCRIPT_SKIP_RE = re.compile(
    r"^(Category|Caller|Company|Callback|Route|Freshdesk|SP Voicemail|--|\s)*$",
    re.I,
)

STOPWORDS = {
    "about", "after", "again", "also", "been", "call", "called", "calling",
    "from", "have", "help", "just", "like", "need", "please", "that", "their",
    "there", "this", "ticket", "vixxo", "voicemail", "with", "would", "your",
}


def phone_last10(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits[-10:] if len(digits) >= 10 else None


def parse_voicemail_description(description: str | None) -> dict:
    desc = description or ""
    out: dict = {
        "fd_ticket": None,
        "caller": None,
        "company": None,
        "callback": None,
        "callback_last10": None,
        "category": None,
        "route": None,
        "transcript": "",
        "search_tokens": [],
        "intent_bucket": BUCKET_VOICEMAIL,
    }
    m = FD_TICKET_RE.search(desc)
    if m:
        out["fd_ticket"] = m.group(1)
    for key, pattern in (
        ("caller", CALLER_RE),
        ("company", COMPANY_RE),
        ("callback", CALLBACK_RE),
        ("category", CATEGORY_RE),
        ("route", ROUTE_RE),
    ):
        m = pattern.search(desc)
        if m:
            out[key] = m.group(1).strip()
    out["callback_last10"] = phone_last10(out.get("callback"))

    lines = desc.splitlines()
    transcript_lines: list[str] = []
    past_header = not SPM_HEADER_RE.search(desc)
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if transcript_lines:
                past_header = True
            continue
        if re.match(r"^(Category|Caller|Company|Callback|Route|Freshdesk)\s*:", stripped, re.I):
            past_header = True
            continue
        if SPM_HEADER_RE.search(stripped):
            past_header = True
            continue
        if stripped.startswith("—") or stripped.startswith("--"):
            past_header = True
            continue
        if past_header and not TRANSCRIPT_SKIP_RE.match(stripped):
            transcript_lines.append(stripped)
    out["transcript"] = " ".join(transcript_lines).strip()
    out["search_tokens"] = transcript_tokens(out["transcript"])
    out["intent_bucket"] = classify_voicemail_intent(out.get("category"), out["transcript"])
    return out


def transcript_tokens(text: str, min_len: int = 4) -> list[str]:
    words = re.findall(r"[a-z0-9]{4,}", (text or "").lower())
    return [w for w in words if w not in STOPWORDS][:40]


def case_search_blob(case: dict) -> str:
    parts = [
        case.get("subject") or "",
        case.get("description") or "",
        case.get("account") or "",
        case.get("sp_name") or "",
    ]
    return " ".join(parts).lower()


def match_score(signals: dict, case: dict, *, intent_bucket: str) -> tuple[int, list[str]]:
    if not is_open(case):
        return 0, []

    target_bucket = classify_case(case.get("subject"), case.get("description"))
    if not voicemail_may_route_to_target(intent_bucket, target_bucket):
        return 0, ["context_mismatch"]

    if not is_actively_worked(case):
        return 0, ["not_actively_worked"]

    blob = case_search_blob(case)
    reasons: list[str] = ["context_match"]
    score = 0

    company_key = normalize_sp_key(signals.get("company"))
    caller_key = normalize_sp_key(signals.get("caller"))
    norm_blob = normalize_sp_key(blob) or ""

    if company_key and len(company_key) >= 4:
        if company_key in norm_blob or company_key.replace(" ", "") in blob.replace(" ", ""):
            score += 4
            reasons.append("company")
        elif company_key.split()[0] in norm_blob if company_key.split() else False:
            score += 2
            reasons.append("company_partial")

    if caller_key and len(caller_key) >= 4 and caller_key in blob:
        score += 2
        reasons.append("caller")

    phone = signals.get("callback_last10")
    if phone and phone in re.sub(r"\D", "", blob):
        score += 5
        reasons.append("callback_phone")

    shared = set(signals.get("search_tokens") or []) & set(
        transcript_tokens(blob, min_len=4)
    )
    if len(shared) >= 3:
        score += 3
        reasons.append(f"transcript:{len(shared)}_tokens")
    elif len(shared) >= 1 and score > 0:
        score += 1
        reasons.append(f"transcript:{len(shared)}_token")

    if signals.get("fd_ticket") and signals["fd_ticket"] in blob:
        score += 6
        reasons.append("freshdesk_id")

    reasons.append("actively_worked")

    if is_user_assigned(case):
        score += 1
        reasons.append("user_assigned")

    if has_activity_touch(case):
        score += 2
        reasons.append("recent_activity")

    return score, reasons


def status_key(status: str | None) -> str:
    return (status or "").strip().lower()


def find_open_work_targets(
    source_case: dict,
    all_cases: list[dict],
    *,
    min_score: int = 4,
    exclude_ids: set[str] | None = None,
) -> list[dict]:
    """Find open, actively-worked Cases matching voicemail context + SP identity.

    Cross-bucket routing requires voicemail intent (Category/transcript) to match
    the target Case bucket — e.g. VixxoLink vm → VixxoLink Case only, not rate
    negotiation.
    """
    desc = source_case.get("description") or source_case.get("Description") or ""
    signals = parse_voicemail_description(desc)
    intent_bucket = signals.get("intent_bucket") or BUCKET_VOICEMAIL

    if intent_bucket == BUCKET_VOICEMAIL:
        return []

    if not any(
        [
            signals.get("company"),
            signals.get("caller"),
            signals.get("callback_last10"),
            signals.get("search_tokens"),
            signals.get("fd_ticket"),
        ]
    ):
        return []

    exclude = exclude_ids or set()
    source_id = source_case.get("id")
    if source_id:
        exclude.add(source_id)

    hits: list[dict] = []
    for case in all_cases:
        cid = case.get("id") or case.get("Id")
        if cid in exclude:
            continue
        if not is_open(case):
            continue

        row = case if case.get("subject") else {
            "id": case.get("Id"),
            "case_number": case.get("CaseNumber"),
            "subject": case.get("Subject") or "",
            "description": case.get("Description") or "",
            "status": case.get("Status") or "",
            "account": (case.get("Account") or {}).get("Name")
            if isinstance(case.get("Account"), dict)
            else case.get("account"),
            "owner": (case.get("Owner") or {}).get("Username")
            if isinstance(case.get("Owner"), dict)
            else case.get("owner"),
            "owner_type": (case.get("Owner") or {}).get("Type")
            if isinstance(case.get("Owner"), dict)
            else case.get("owner_type"),
            "created_at": case.get("CreatedDate") or case.get("created_at"),
            "last_touch_at": case.get("last_touch_at"),
            "last_touch_sources": case.get("last_touch_sources"),
            "sp_name": extract_sp_name(case.get("Subject"), case.get("Description")),
        }

        target_bucket = classify_case(row.get("subject"), row.get("description"))
        score, reasons = match_score(signals, row, intent_bucket=intent_bucket)
        if score < min_score:
            continue
        hits.append(
            {
                "case": row,
                "score": score,
                "match_reasons": reasons,
                "target_bucket": target_bucket,
                "intent_bucket": intent_bucket,
                "actively_worked": is_actively_worked(row),
                "signals": {
                    "category": signals.get("category"),
                    "intent_bucket": intent_bucket,
                    "company": signals.get("company"),
                    "caller": signals.get("caller"),
                    "callback": signals.get("callback"),
                    "transcript_excerpt": (signals.get("transcript") or "")[:120],
                },
            }
        )

    hits.sort(
        key=lambda h: (
            h["actively_worked"],
            is_user_assigned(h["case"]),
            has_activity_touch(h["case"]),
            last_touch_at(h["case"]),
            h["score"],
        ),
        reverse=True,
    )
    return hits
