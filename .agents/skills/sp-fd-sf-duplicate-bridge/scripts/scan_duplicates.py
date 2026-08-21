#!/usr/bin/env python3
"""Scan Freshdesk vs Salesforce for duplicate intake pairs in a time window.

Requires a pre-exported SF Case JSON (MCP run_soql_query output saved to disk).

Usage
-----
    python scan_duplicates.py \\
      --window-start 2026-06-24T18:00:00Z \\
      --sf-cache .tmp/sf-cases-window-20260625.json \\
      --output .tmp/fd-sf-duplicate-scan.json
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DOMAIN = os.environ.get("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com").strip()
SPM_GROUP_ID = 159000485013
USER_AGENT = "sp-fd-sf-duplicate-bridge/1.0"


def _basic_auth(api_key: str) -> str:
    return "Basic " + base64.b64encode(f"{api_key}:X".encode()).decode()


def auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": _basic_auth(api_key), "User-Agent": USER_AGENT}


def load_credentials() -> str:
    api_key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    token_path = Path.home() / ".vixxo" / "freshdesk_token"
    if not api_key and token_path.is_file():
        api_key = token_path.read_text(encoding="utf-8").strip()
    if not api_key:
        raise SystemExit("FRESHDESK_API_KEY not set and ~/.vixxo/freshdesk_token missing")
    return api_key


def get_ticket(api_key: str, ticket_id: int) -> dict:
    url = f"https://{DOMAIN}/api/v2/tickets/{ticket_id}"
    req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())

FD_TICKET_RE = re.compile(r"Freshdesk\s*#(\d+)", re.I)
FEDERATED_COI_RE = re.compile(
    r"Certificate\s+Of\s+Insurance\s*-\s*(.+?)\s+(\d+-\d+-\d+)\s+Req\s+(\d+)"
    r"(?:~([^~]+))?(?:~(\d+))?",
    re.I,
)
FEDCOI_PREFIX_RE = re.compile(r"^(?:re|fw|fwd):\s*", re.I)
FEDCOI_AUTOREPLY_RE = re.compile(
    r"\s*-\s*Federated Insurance Auto Reply:.*$", re.I
)
FEDCERTS_SENDER = "fedcerts-donotreply@fedins.com"
HARTFORD_SENDER = "donotreplycommercial@thehartford.com"
CSR24_SENDER = "mail-server@csr24.email"
HARTFORD_ACCOUNT_RE = re.compile(r"Account\s*#\s*(\d+)\s*(.*)$", re.I)
INVOICE_SP_RE = re.compile(
    r"(?:invoice|overdue|past due|payment)[^·\n]*[·\-]\s*(.+?)\s*$", re.I
)
COI_SUBJECT_SP_RE = re.compile(
    r"(?:COI|certificate of insurance|insurance|proof of insurance)"
    r"[^A-Za-z0-9]*(?:for|regarding|-)\s*(.+?)"
    r"(?:\s+auto|\s+workers|\s+general|\s*$)",
    re.I,
)
GENERIC_SUBJECT_SP_RE = re.compile(
    r"^Re:\s*(?:FW:\s*)*(.+?)\s+(?:auto insurance COI|COI|certificate)",
    re.I,
)
VIXXO_SKIP = re.compile(
    r"@vixxo\.com$|@8x8\.com$|@notification\.intuit\.com$|@vixxo-helpdesk",
    re.I,
)


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.replace("+0000", "+00:00").replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def norm_email(e: str | None) -> str | None:
    if not e:
        return None
    e = e.strip().lower()
    if "@" not in e or VIXXO_SKIP.search(e):
        return None
    return e


def subject_tokens(subject: str) -> set[str]:
    s = re.sub(r"^(re|fw|fwd):\s*", "", (subject or ""), flags=re.I).strip().lower()
    return {w for w in re.findall(r"[a-z0-9]{4,}", s) if len(w) >= 4}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def format_search_query(expr: str) -> str:
    trimmed = expr.strip()
    if trimmed.startswith('"') and trimmed.endswith('"'):
        return trimmed
    return f'"{trimmed}"'


def clean_federated_coi_subject(subject: str) -> str:
    s = FEDCOI_PREFIX_RE.sub("", subject.strip())
    while FEDCOI_PREFIX_RE.match(s):
        s = FEDCOI_PREFIX_RE.sub("", s.strip())
    return FEDCOI_AUTOREPLY_RE.sub("", s).strip()


def extract_federated_coi_fields(subject: str | None) -> dict | None:
    """Return provider, policy_id, req_id, timestamp from Federated COI subject."""
    if not subject:
        return None
    m = FEDERATED_COI_RE.search(clean_federated_coi_subject(subject))
    if not m:
        return None
    return {
        "provider": m.group(1).strip(),
        "policy_id": m.group(2),
        "req_id": m.group(3),
        "timestamp": m.group(4) if m.lastindex and m.lastindex >= 4 else None,
        "suffix": m.group(5) if m.lastindex and m.lastindex >= 5 else None,
    }


def coi_req_key(fields: dict | None) -> tuple[str, str] | None:
    if not fields:
        return None
    return (fields["policy_id"], fields["req_id"])


def extract_federated_coi_provider(subject: str | None) -> str | None:
    """Return provider token from Federated COI subject, or None."""
    fields = extract_federated_coi_fields(subject)
    return fields["provider"] if fields else None


def normalize_coi_provider(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[,.'\"]", "", s)
    s = re.sub(
        r"\b(inc|llc|ltd|corp|corporation|company|co|services|service)\b",
        "",
        s,
    )
    return re.sub(r"\s+", " ", s).strip()


def is_federated_coi_subject(subject: str | None) -> bool:
    return extract_federated_coi_provider(subject) is not None


def is_fedcerts_requester(email: str | None) -> bool:
    return (email or "").strip().lower() == FEDCERTS_SENDER


def is_hartford_requester(email: str | None) -> bool:
    return (email or "").strip().lower() == HARTFORD_SENDER


def extract_hartford_account_subject(subject: str | None) -> tuple[str, str] | None:
    """Return (account_number, provider_tail) from Hartford batch COI subjects."""
    if not subject:
        return None
    m = HARTFORD_ACCOUNT_RE.search(subject.strip())
    if not m:
        return None
    return m.group(1), (m.group(2) or "").strip()


def extract_subject_sp_hint(subject: str | None, fd_meta: dict | None = None) -> str | None:
    """Best-effort SP name from subject (and FD coi_provider when present)."""
    if fd_meta and fd_meta.get("coi_provider"):
        return fd_meta["coi_provider"]
    if not subject:
        return None
    subj = subject.strip()
    fed = extract_federated_coi_provider(subj)
    if fed:
        return fed
    hart = extract_hartford_account_subject(subj)
    if hart:
        return hart[1] or None
    for pat in (GENERIC_SUBJECT_SP_RE, COI_SUBJECT_SP_RE, INVOICE_SP_RE):
        m = pat.search(subj)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return None


def is_csr24_requester(email: str | None) -> bool:
    return (email or "").strip().lower() == CSR24_SENDER


def classify_contact_collision_pairs(pairs: list[dict]) -> None:
    """Split contact collisions into COI-vet candidates vs subject-mismatch skips."""
    for pair in pairs:
        if pair.get("dup_type") != "contact_collision":
            continue
        reasons = pair.setdefault("match_reasons", [])
        fd = pair.get("freshdesk") or {}
        sf = pair.get("salesforce") or {}
        fd_subj = fd.get("subject") or ""
        sf_subj = sf.get("subject") or ""
        sim = float(pair.get("subject_similarity") or 0.0)

        fd_hint = extract_subject_sp_hint(fd_subj, fd)
        sf_hint = extract_subject_sp_hint(sf_subj, None)
        fd_norm = normalize_coi_provider(fd_hint or "")
        sf_norm = normalize_coi_provider(sf_hint or "")

        req = (fd.get("requester") or "").lower()
        sf_emails = {
            (sf.get("contact_email") or "").lower(),
            (sf.get("supplied_email") or "").lower(),
        }
        if is_csr24_requester(req) and CSR24_SENDER in sf_emails:
            if fd_norm and sf_norm and fd_norm != sf_norm:
                pair["dup_type"] = "subject_mismatch_skip"
                if "csr24_sender_mismatch" not in reasons:
                    reasons.append("csr24_sender_mismatch")
                continue
            if sim < 0.35:
                pair["dup_type"] = "subject_mismatch_skip"
                if "csr24_subject_mismatch" not in reasons:
                    reasons.append("csr24_subject_mismatch")
                continue

        if fd_norm and sf_norm and fd_norm != sf_norm:
            pair["dup_type"] = "subject_mismatch_skip"
            if "subject_sp_mismatch" not in reasons:
                reasons.append("subject_sp_mismatch")
            continue

        if sim < 0.25 and not (fd_norm and sf_norm and fd_norm == sf_norm):
            pair["dup_type"] = "subject_mismatch_skip"
            if "subject_low_overlap" not in reasons:
                reasons.append("subject_low_overlap")
            continue

        pair["dup_type"] = "coi_vet_required"
        if fd_norm and sf_norm and fd_norm == sf_norm:
            if "subject_sp_match_needs_coi" not in reasons:
                reasons.append("subject_sp_match_needs_coi")
        elif "shared_requester_needs_coi_vet" not in reasons:
            reasons.append("shared_requester_needs_coi_vet")


def _search_fd_filter(
    api_key: str,
    window_start: datetime,
    window_end: datetime,
    filter_expr: str,
) -> list[dict]:
    seen: set[int] = set()
    out: list[dict] = []
    day = window_start.date()
    end_day = window_end.date()
    while day <= end_day:
        next_day = day.fromordinal(day.toordinal() + 1)
        day_filter = (
            f"created_at:>'{day.isoformat()}' AND created_at:<'{next_day.isoformat()}' "
            f"AND ({filter_expr})"
        )
        for page in range(1, 11):
            params = {"query": format_search_query(day_filter), "page": str(page)}
            url = f"https://{DOMAIN}/api/v2/search/tickets?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    payload = json.loads(resp.read().decode())
            except urllib.error.HTTPError as exc:
                body = exc.read().decode()
                raise RuntimeError(
                    f"Freshdesk search failed day={day} page={page} body={body[:500]}"
                ) from exc
            batch = payload.get("results") or []
            if not batch:
                break
            for t in batch:
                created = parse_dt(t.get("created_at"))
                if not created or created < window_start or created > window_end:
                    continue
                tid = int(t["id"])
                if tid in seen:
                    continue
                seen.add(tid)
                out.append(t)
            if len(batch) < 30:
                break
        day = next_day
    return out


def search_fd_created_in_window(api_key: str, window_start: datetime, window_end: datetime) -> list[dict]:
    return _search_fd_filter(
        api_key,
        window_start,
        window_end,
        f"group_id:{SPM_GROUP_ID}",
    )


def search_fd_coi_in_window(api_key: str, window_start: datetime, window_end: datetime) -> list[dict]:
    """Pull Federated COI FD tickets by coi tag (SPM group). Subject filter applied client-side."""
    merged: list[dict] = []
    seen: set[int] = set()
    for tag in ("COI", "coi"):
        try:
            batch = _search_fd_filter(
                api_key,
                window_start,
                window_end,
                f"group_id:{SPM_GROUP_ID} AND tag:'{tag}'",
            )
        except RuntimeError:
            continue
        for t in batch:
            tid = int(t["id"])
            if tid in seen:
                continue
            subj = t.get("subject") or ""
            tags = [x.lower() for x in (t.get("tags") or [])]
            if "coi" not in tags and not is_federated_coi_subject(subj):
                continue
            seen.add(tid)
            merged.append(t)
    merged.sort(key=lambda x: x.get("created_at") or "")
    return merged


def get_conversations(api_key: str, ticket_id: int) -> list[dict]:
    url = f"https://{DOMAIN}/api/v2/tickets/{ticket_id}/conversations"
    req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def classify_queue(t: dict) -> str:
    ttype = (t.get("type") or "").lower()
    if "ksonboarding" in ttype:
        return "ksonboarding"
    if "invoice" in ttype:
        return "invoice-concerns"
    to_blob = " ".join(t.get("to_emails") or []).lower()
    if "aphelp" in to_blob:
        return "aphelp"
    return "spm-other"


def requester_from_summary(t: dict, api_key: str) -> str | None:
    rid = t.get("requester_id")
    if rid:
        url = f"https://{DOMAIN}/api/v2/contacts/{rid}"
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                c = json.loads(resp.read().decode())
            e = norm_email(c.get("email"))
            if e:
                return e
        except Exception:
            pass
    return None


def load_sf_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected SF cache shape in {path}")


def merge_fd_summaries(*batches: list[dict]) -> list[dict]:
    seen: set[int] = set()
    out: list[dict] = []
    for batch in batches:
        for t in batch:
            tid = int(t["id"])
            if tid in seen:
                continue
            seen.add(tid)
            out.append(t)
    out.sort(key=lambda x: x.get("created_at") or "")
    return out


def build_fd_meta(
    summary: dict,
    api_key: str,
    req_email: str | None,
    enrich: bool,
) -> dict:
    subject = summary.get("subject") or ""
    fd_meta: dict = {
        "id": int(summary["id"]),
        "subject": subject,
        "created_at": summary.get("created_at"),
        "status": summary.get("status"),
        "queue": classify_queue(summary),
        "requester": req_email,
    }
    provider = extract_federated_coi_provider(subject)
    if provider:
        fd_meta["coi_provider"] = provider
    coi_fields = extract_federated_coi_fields(subject)
    if coi_fields:
        fd_meta["coi_policy_id"] = coi_fields["policy_id"]
        fd_meta["coi_req_id"] = coi_fields["req_id"]
        if coi_fields.get("timestamp"):
            fd_meta["coi_req_timestamp"] = coi_fields["timestamp"]
    if enrich:
        ticket = get_ticket(api_key, int(summary["id"]))
        try:
            convs = get_conversations(api_key, int(summary["id"]))
        except Exception:
            convs = []
        fd_meta["attachment_count"] = len(ticket.get("attachments") or [])
        fd_meta["conversation_count"] = len(convs)
        fd_meta["inline_images"] = len(
            re.findall(r"<img\s", ticket.get("description") or "", re.I)
        )
        tags = ticket.get("tags") or []
        if tags:
            fd_meta["tags"] = tags
    return fd_meta


def pair_origin(summary: dict, sf: dict) -> str:
    fd_created = parse_dt(summary.get("created_at"))
    sf_created = parse_dt(sf.get("CreatedDate"))
    if not fd_created or not sf_created:
        return "unclear"
    if sf_created < fd_created:
        return "sf_first"
    if fd_created < sf_created:
        return "fd_first"
    return "same_time"


def make_pair_entry(
    summary: dict,
    sf: dict,
    reasons: list[str],
    dup_type: str,
    sim: float,
    api_key: str,
    req_email: str | None,
    enrich: bool,
) -> dict:
    subject = summary.get("subject") or ""
    sf_subj = sf.get("Subject") or ""
    desc = sf.get("Description") or ""
    return {
        "match_reasons": reasons,
        "dup_type": dup_type,
        "origin": pair_origin(summary, sf),
        "subject_similarity": round(sim, 3),
        "freshdesk": build_fd_meta(summary, api_key, req_email, enrich),
        "salesforce": {
            "id": sf["Id"],
            "case_number": sf.get("CaseNumber"),
            "subject": sf_subj,
            "created_at": sf.get("CreatedDate"),
            "status": sf.get("Status"),
            "contact_email": sf.get("ContactEmail"),
            "supplied_email": sf.get("SuppliedEmail"),
            "description_snippet": (desc[:300] + "...") if len(desc) > 300 else desc,
        },
    }


def reclassify_fedcerts_pairs(pairs: list[dict]) -> None:
    """Promote same-provider Federated pairs; suppress sender-only mismatches."""
    for pair in pairs:
        if "fd_id_in_sf_description" in pair.get("match_reasons", []):
            continue
        if "coi_req_id_match" in pair.get("match_reasons", []):
            continue
        fd = pair.get("freshdesk") or {}
        sf = pair.get("salesforce") or {}
        fd_fields = extract_federated_coi_fields(fd.get("subject") or "")
        sf_fields = extract_federated_coi_fields(sf.get("subject") or "")
        if coi_req_key(fd_fields) and coi_req_key(fd_fields) == coi_req_key(sf_fields):
            continue
        fd_provider = normalize_coi_provider(
            fd.get("coi_provider")
            or extract_federated_coi_provider(fd.get("subject") or "")
            or ""
        )
        sf_provider = normalize_coi_provider(
            extract_federated_coi_provider(sf.get("subject") or "") or ""
        )
        if fd_provider and sf_provider and fd_provider == sf_provider:
            pair["dup_type"] = "same_sp_duplicate"
            reasons = pair.setdefault("match_reasons", [])
            if "coi_provider_name_match" not in reasons:
                reasons.append("coi_provider_name_match")
            if "fedcerts_sender_collision" in reasons:
                reasons.remove("fedcerts_sender_collision")
            continue
        req = fd.get("requester")
        sf_emails = {
            (sf.get("contact_email") or "").lower(),
            (sf.get("supplied_email") or "").lower(),
        }
        if is_fedcerts_requester(req) and FEDCERTS_SENDER in sf_emails:
            pair["dup_type"] = "fedcerts_sender_noise"
            reasons = pair.setdefault("match_reasons", [])
            if "fedcerts_sender_collision" not in reasons:
                reasons.append("fedcerts_sender_collision")


def apply_fedcerts_downgrade(pairs: list[dict]) -> None:
    """Downgrade fedcerts-sender-only matches without Req-id or provider alignment."""
    for pair in pairs:
        if "coi_req_id_match" in pair["match_reasons"]:
            continue
        if "coi_provider_name_match" in pair["match_reasons"]:
            continue
        if "fd_id_in_sf_description" in pair["match_reasons"]:
            continue
        fd = pair["freshdesk"]
        sf = pair["salesforce"]
        fd_fields = extract_federated_coi_fields(fd.get("subject") or "")
        sf_fields = extract_federated_coi_fields(sf.get("subject") or "")
        if coi_req_key(fd_fields) and coi_req_key(fd_fields) == coi_req_key(sf_fields):
            continue
        fd_provider = normalize_coi_provider(fd.get("coi_provider") or "")
        sf_provider = normalize_coi_provider(
            extract_federated_coi_provider(sf.get("subject") or "") or ""
        )
        if fd_provider and sf_provider and fd_provider == sf_provider:
            continue
        req = fd.get("requester")
        sf_emails = {
            (sf.get("contact_email") or "").lower(),
            (sf.get("supplied_email") or "").lower(),
        }
        if is_fedcerts_requester(req) and FEDCERTS_SENDER in sf_emails:
            pair["dup_type"] = "fedcerts_sender_noise"
            if "fedcerts_sender_collision" not in pair["match_reasons"]:
                pair["match_reasons"].append("fedcerts_sender_collision")


def apply_hartford_downgrade(pairs: list[dict]) -> None:
    """Downgrade Hartford batch-sender matches when account # or SP name differs."""
    for pair in pairs:
        if pair["dup_type"] not in ("true_same_thread", "likely_same_thread"):
            continue
        if "fd_id_in_sf_description" in pair["match_reasons"]:
            continue
        if "coi_req_id_match" in pair["match_reasons"]:
            continue
        if "coi_provider_name_match" in pair["match_reasons"]:
            continue

        fd = pair["freshdesk"]
        sf = pair["salesforce"]
        fd_subj = fd.get("subject") or ""
        sf_subj = sf.get("subject") or ""
        fd_acct = extract_hartford_account_subject(fd_subj)
        sf_acct = extract_hartford_account_subject(sf_subj)

        if fd_acct and sf_acct:
            fd_num, fd_provider = fd_acct
            sf_num, sf_provider = sf_acct
            if fd_num != sf_num:
                pair["dup_type"] = "contact_collision"
                if "hartford_account_mismatch" not in pair["match_reasons"]:
                    pair["match_reasons"].append("hartford_account_mismatch")
                continue
            fd_name = normalize_coi_provider(fd_provider)
            sf_name = normalize_coi_provider(sf_provider)
            if fd_name and sf_name and fd_name != sf_name:
                pair["dup_type"] = "contact_collision"
                if "hartford_provider_mismatch" not in pair["match_reasons"]:
                    pair["match_reasons"].append("hartford_provider_mismatch")
                continue

        req = fd.get("requester")
        sf_emails = {
            (sf.get("contact_email") or "").lower(),
            (sf.get("supplied_email") or "").lower(),
        }
        if is_hartford_requester(req) and HARTFORD_SENDER in sf_emails:
            if fd_acct and sf_acct:
                continue
            pair["dup_type"] = "contact_collision"
            if "hartford_sender_collision" not in pair["match_reasons"]:
                pair["match_reasons"].append("hartford_sender_collision")


def add_coi_req_id_pairs(
    fd_summaries: list[dict],
    sf_cases: list[dict],
    pairs: list[dict],
    seen_pair: set[tuple[int, str]],
    api_key: str,
    enrich: bool,
) -> None:
    """Match FD ↔ SF Federated COI tickets by (policy_id, req_id) in subject."""
    sf_by_req: dict[tuple[str, str], list[dict]] = {}
    for c in sf_cases:
        fields = extract_federated_coi_fields(c.get("Subject") or "")
        key = coi_req_key(fields)
        if not key:
            continue
        sf_by_req.setdefault(key, []).append(c)

    for summary in fd_summaries:
        subject = summary.get("subject") or ""
        fd_fields = extract_federated_coi_fields(subject)
        key = coi_req_key(fd_fields)
        if not key:
            continue
        tid = int(summary["id"])
        req_email = requester_from_summary(summary, api_key)
        policy_id, req_id = key
        for sf in sf_by_req.get(key, []):
            pair_key = (tid, sf["Id"])
            if pair_key in seen_pair:
                for existing in pairs:
                    if (
                        existing["freshdesk"]["id"] == tid
                        and existing["salesforce"]["id"] == sf["Id"]
                    ):
                        if "coi_req_id_match" not in existing["match_reasons"]:
                            existing["match_reasons"].append("coi_req_id_match")
                        existing["dup_type"] = "true_same_thread"
                        for tag in ("fedcerts_sender_collision",):
                            if tag in existing["match_reasons"]:
                                existing["match_reasons"].remove(tag)
                continue
            seen_pair.add(pair_key)
            sf_subj = sf.get("Subject") or ""
            sim = jaccard(subject_tokens(subject), subject_tokens(sf_subj))
            provider = fd_fields["provider"] if fd_fields else ""
            reasons = [
                "coi_req_id_match",
                f"req:{policy_id} Req {req_id}",
            ]
            if provider:
                reasons.append(f"provider:{provider}")
            pairs.append(
                make_pair_entry(
                    summary,
                    sf,
                    reasons,
                    "true_same_thread",
                    sim,
                    api_key,
                    req_email,
                    enrich,
                )
            )


def add_coi_provider_pairs(
    fd_summaries: list[dict],
    sf_cases: list[dict],
    pairs: list[dict],
    seen_pair: set[tuple[int, str]],
    api_key: str,
    enrich: bool,
) -> None:
    """Match FD ↔ SF Federated COI tickets by provider name in subject."""
    sf_by_provider: dict[str, list[dict]] = {}
    for c in sf_cases:
        provider = extract_federated_coi_provider(c.get("Subject") or "")
        if not provider:
            continue
        key = normalize_coi_provider(provider)
        sf_by_provider.setdefault(key, []).append(c)

    for summary in fd_summaries:
        subject = summary.get("subject") or ""
        fd_provider = extract_federated_coi_provider(subject)
        if not fd_provider:
            continue
        tid = int(summary["id"])
        req_email = requester_from_summary(summary, api_key)
        key = normalize_coi_provider(fd_provider)
        for sf in sf_by_provider.get(key, []):
            pair_key = (tid, sf["Id"])
            if pair_key in seen_pair:
                for existing in pairs:
                    if (
                        existing["freshdesk"]["id"] == tid
                        and existing["salesforce"]["id"] == sf["Id"]
                    ):
                        if "coi_provider_name_match" not in existing["match_reasons"]:
                            existing["match_reasons"].append("coi_provider_name_match")
                        existing["dup_type"] = "same_sp_duplicate"
                        if "fedcerts_sender_collision" in existing["match_reasons"]:
                            existing["match_reasons"].remove("fedcerts_sender_collision")
                continue
            seen_pair.add(pair_key)
            sf_subj = sf.get("Subject") or ""
            sim = jaccard(subject_tokens(subject), subject_tokens(sf_subj))
            reasons = ["coi_provider_name_match", f"provider:{fd_provider}"]
            pairs.append(
                make_pair_entry(
                    summary,
                    sf,
                    reasons,
                    "same_sp_duplicate",
                    sim,
                    api_key,
                    req_email,
                    enrich,
                )
            )


def scan(
    fd_summaries: list[dict],
    sf_cases: list[dict],
    api_key: str,
    enrich: bool,
) -> list[dict]:
    sf_by_email: dict[str, list[dict]] = {}
    sf_by_fd_id: dict[str, list[dict]] = {}
    for c in sf_cases:
        for field in ("Description", "Subject"):
            for m in FD_TICKET_RE.finditer(c.get(field) or ""):
                sf_by_fd_id.setdefault(m.group(1), []).append(c)
        for field in ("ContactEmail", "SuppliedEmail"):
            e = norm_email(c.get(field))
            if e:
                sf_by_email.setdefault(e, []).append(c)

    pairs: list[dict] = []
    seen_pair: set[tuple[int, str]] = set()

    for summary in fd_summaries:
        tid = int(summary["id"])
        subject = summary.get("subject") or ""
        req_email = requester_from_summary(summary, api_key)

        candidates: dict[str, dict] = {}
        for c in sf_by_fd_id.get(str(tid), []):
            candidates[c["Id"]] = c
        if req_email:
            for c in sf_by_email.get(req_email, []):
                candidates[c["Id"]] = c

        for sf in candidates.values():
            key = (tid, sf["Id"])
            if key in seen_pair:
                continue
            seen_pair.add(key)

            sf_subj = sf.get("Subject") or ""
            sim = jaccard(subject_tokens(subject), subject_tokens(sf_subj))
            reasons: list[str] = []
            desc = sf.get("Description") or ""
            if any(
                m.group(1) == str(tid)
                for field in (desc, sf_subj)
                for m in FD_TICKET_RE.finditer(field)
            ):
                reasons.append("fd_id_in_sf_description")
            if req_email and norm_email(sf.get("ContactEmail")) == req_email:
                reasons.append("contact_email")
            if req_email and norm_email(sf.get("SuppliedEmail")) == req_email:
                reasons.append("supplied_email")
            if sim >= 0.35:
                reasons.append(f"subject_overlap:{sim:.2f}")
            if not reasons:
                continue

            dup_type = "contact_collision"
            if "fd_id_in_sf_description" in reasons:
                dup_type = "true_same_thread"
            elif sim >= 0.5:
                dup_type = "true_same_thread"
            elif sim >= 0.25:
                dup_type = "likely_same_thread"

            pairs.append(
                make_pair_entry(
                    summary,
                    sf,
                    reasons,
                    dup_type,
                    sim,
                    api_key,
                    req_email,
                    enrich,
                )
            )

    apply_fedcerts_downgrade(pairs)
    apply_hartford_downgrade(pairs)
    add_coi_req_id_pairs(fd_summaries, sf_cases, pairs, seen_pair, api_key, enrich)
    add_coi_provider_pairs(fd_summaries, sf_cases, pairs, seen_pair, api_key, enrich)
    reclassify_fedcerts_pairs(pairs)
    classify_contact_collision_pairs(pairs)
    return pairs


def collect_intra_system_req_duplicates(
    fd_summaries: list[dict],
    sf_cases: list[dict],
) -> dict:
    """Group FD and SF records sharing the same Federated (policy_id, req_id)."""
    fd_groups: dict[tuple[str, str], list[dict]] = {}
    sf_groups: dict[tuple[str, str], list[dict]] = {}

    for summary in fd_summaries:
        fields = extract_federated_coi_fields(summary.get("subject") or "")
        key = coi_req_key(fields)
        if not key:
            continue
        fd_groups.setdefault(key, []).append(
            {
                "id": int(summary["id"]),
                "subject": summary.get("subject"),
                "created_at": summary.get("created_at"),
                "status": summary.get("status"),
                "provider": fields["provider"] if fields else None,
            }
        )

    for c in sf_cases:
        fields = extract_federated_coi_fields(c.get("Subject") or "")
        key = coi_req_key(fields)
        if not key:
            continue
        sf_groups.setdefault(key, []).append(
            {
                "case_number": c.get("CaseNumber"),
                "id": c.get("Id"),
                "subject": c.get("Subject"),
                "created_at": c.get("CreatedDate"),
                "status": c.get("Status"),
                "provider": fields["provider"] if fields else None,
            }
        )

    fd_dupes = {k: v for k, v in fd_groups.items() if len(v) > 1}
    sf_dupes = {k: v for k, v in sf_groups.items() if len(v) > 1}
    return {
        "fd_intra_duplicates": [
            {
                "policy_id": k[0],
                "req_id": k[1],
                "tickets": v,
            }
            for k, v in sorted(fd_dupes.items(), key=lambda x: (x[0][0], int(x[0][1])))
        ],
        "sf_intra_duplicates": [
            {
                "policy_id": k[0],
                "req_id": k[1],
                "cases": v,
            }
            for k, v in sorted(sf_dupes.items(), key=lambda x: (x[0][0], int(x[0][1])))
        ],
    }


def write_report_markdown(result: dict, path: Path) -> None:
    pairs = result["pairs"]
    coi_req_pairs = [
        p
        for p in pairs
        if "coi_req_id_match" in p["match_reasons"]
        and p["dup_type"] == "true_same_thread"
    ]
    coi_pairs = [
        p
        for p in pairs
        if p.get("dup_type") == "same_sp_duplicate"
        and "coi_provider_name_match" in p["match_reasons"]
    ]
    reportable = [
        p
        for p in pairs
        if p.get("dup_type") not in ("fedcerts_sender_noise", "subject_mismatch_skip")
    ]
    coi_vet_pairs = [p for p in pairs if p.get("dup_type") == "coi_vet_required"]
    skip_pairs = [p for p in pairs if p.get("dup_type") == "subject_mismatch_skip"]
    lines = [
        "# Freshdesk ↔ Salesforce Duplicate Scan (COI widened)",
        "",
        f"**Window:** {result['window_start']} → {result['window_end']}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| FD inbound | {result['fd_count']} |",
        f"| SF Cases | {result['sf_count']} |",
        f"| Reportable pairs | {result.get('reportable_pair_count', len(reportable))} |",
        f"| True same-thread | {result['true_same_thread']} |",
        f"| Same SP (Federated subject) | {result.get('same_sp_duplicate', len(coi_pairs))} |",
        f"| COI vet required | {result.get('coi_vet_required', len(coi_vet_pairs))} |",
        f"| Likely same-thread | {result['likely_same_thread']} |",
        f"| Contact collision (residual) | {result['contact_collision']} |",
        f"| Subject mismatch (suppressed) | {result.get('subject_mismatch_skip', len(skip_pairs))} |",
        f"| Fedcerts sender-only (suppressed) | {result.get('fedcerts_sender_noise', 0)} |",
        f"| COI Req-id matched | {result.get('coi_req_id_matched', 0)} |",
        "",
    ]
    intra = result.get("intra_system_req_duplicates") or {}
    fd_intra = intra.get("fd_intra_duplicates") or []
    sf_intra = intra.get("sf_intra_duplicates") or []
    if fd_intra or sf_intra:
        lines.extend(
            [
                "## Intra-system Req-id duplicates (route, do not re-create)",
                "",
            ]
        )
        if fd_intra:
            lines.extend(["### Freshdesk — same Req id, multiple tickets", ""])
            for g in fd_intra:
                lines.append(
                    f"**{g['policy_id']} Req {g['req_id']}** "
                    f"({g['tickets'][0].get('provider') or '—'})"
                )
                for t in g["tickets"]:
                    lines.append(
                        f"- #{t['id']} — {t.get('status')} — "
                        f"{(t.get('subject') or '')[:70]}"
                    )
                lines.append("")
        if sf_intra:
            lines.extend(["### Salesforce — same Req id, multiple Cases", ""])
            for g in sf_intra:
                lines.append(
                    f"**{g['policy_id']} Req {g['req_id']}** "
                    f"({g['cases'][0].get('provider') or '—'})"
                )
                for c in g["cases"]:
                    lines.append(
                        f"- {c.get('case_number')} — {c.get('status')} — "
                        f"{(c.get('subject') or '')[:70]}"
                    )
                lines.append("")
    if coi_req_pairs:
        lines.extend(
            [
                "## Federated COI Req-id matched pairs (FD ↔ SF)",
                "",
                "| FD | Req id | Provider | SF Case | Origin |",
                "|----|--------|----------|---------|--------|",
            ]
        )
        for p in sorted(coi_req_pairs, key=lambda x: x["freshdesk"]["id"]):
            fd = p["freshdesk"]
            sf = p["salesforce"]
            req_label = f"{fd.get('coi_policy_id')} Req {fd.get('coi_req_id')}"
            provider = fd.get("coi_provider") or "—"
            lines.append(
                f"| [#{fd['id']}](https://{DOMAIN}/a/tickets/{fd['id']}) "
                f"| {req_label} | {provider} | {sf.get('case_number')} | {p['origin']} |"
            )
        lines.append("")
    if coi_pairs:
        lines.extend(
            [
                "## Same SP duplicates — Federated COI (subject provider match)",
                "",
                "Vet before merge: parse insured name / DBA from COI attachment, then "
                "cross-check SP name in Gateway or SF Account.",
                "",
                "| FD | Provider (subject) | SF Case | Origin |",
                "|----|--------------------|---------|--------|",
            ]
        )
        for p in sorted(coi_pairs, key=lambda x: x["freshdesk"]["id"]):
            fd = p["freshdesk"]
            sf = p["salesforce"]
            provider = fd.get("coi_provider") or extract_federated_coi_provider(
                fd.get("subject") or ""
            ) or "—"
            lines.append(
                f"| [#{fd['id']}](https://{DOMAIN}/a/tickets/{fd['id']}) "
                f"| {provider} | {sf.get('case_number')} | {p['origin']} |"
            )
        lines.append("")

    if coi_vet_pairs:
        lines.extend(
            [
                "## COI vet required (shared requester, subject unclear)",
                "",
                "Review COI insured name / DBA; cross-check Gateway and SF Account. "
                "See [coi-vetting.md](coi-vetting.md).",
                "",
                "| FD | SF Case | FD subject | SF subject | Signals |",
                "|----|---------|------------|------------|---------|",
            ]
        )
        for p in coi_vet_pairs[:30]:
            fd = p["freshdesk"]
            sf = p["salesforce"]
            sig = ", ".join(p.get("match_reasons") or [])[:60]
            lines.append(
                f"| [#{fd['id']}](https://{DOMAIN}/a/tickets/{fd['id']}) "
                f"| {sf.get('case_number')} "
                f"| {(fd.get('subject') or '')[:45]} "
                f"| {(sf.get('subject') or '')[:45]} | {sig} |"
            )
        if len(coi_vet_pairs) > 30:
            lines.append(f"| … | +{len(coi_vet_pairs) - 30} more | | | |")
        lines.append("")

    fedcerts_noise = result.get("fedcerts_sender_noise") or sum(
        1 for p in pairs if p.get("dup_type") == "fedcerts_sender_noise"
    )
    if fedcerts_noise:
        lines.extend(
            [
                "## Fedcerts sender-only pairs (suppressed from report)",
                "",
                f"{fedcerts_noise} FD↔SF pair(s) shared only `fedcerts-donotreply@fedins.com` "
                "with mismatched provider names in subject — not listed as contact collisions. "
                "Review individually only when COI insured name / DBA aligns after cert scan.",
                "",
            ]
        )

    if skip_pairs:
        lines.extend(
            [
                "## Subject mismatch (suppressed)",
                "",
                f"{len(skip_pairs)} pair(s) share requester email but subject SP names "
                "or overlap indicate different threads — skipped unless COI review overrides.",
                "",
            ]
        )

    contact_pairs = [p for p in pairs if p.get("dup_type") == "contact_collision"]
    if contact_pairs:
        lines.extend(
            [
                "## Contact collisions (non-Fedcerts batch sender)",
                "",
                "| FD | SF Case | FD subject | SF subject |",
                "|----|---------|------------|------------|",
            ]
        )
        for p in contact_pairs[:25]:
            fd = p["freshdesk"]
            sf = p["salesforce"]
            lines.append(
                f"| [#{fd['id']}](https://{DOMAIN}/a/tickets/{fd['id']}) "
                f"| {sf.get('case_number')} "
                f"| {(fd.get('subject') or '')[:50]} "
                f"| {(sf.get('subject') or '')[:50]} |"
            )
        if len(contact_pairs) > 25:
            lines.append(f"| … | +{len(contact_pairs) - 25} more | | |")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-start", required=True, help="ISO8601 UTC, e.g. 2026-06-24T18:00:00Z")
    parser.add_argument("--window-end", default=None, help="ISO8601 UTC; default now")
    parser.add_argument("--sf-cache", required=True, type=Path, help="SF Cases JSON export")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path, default=None, help="Markdown report path (default: output .md)")
    parser.add_argument("--include-coi", action="store_true", help="Also pull FD COI tickets by subject/tag")
    parser.add_argument("--no-enrich", action="store_true", help="Skip per-ticket FD API enrichment")
    args = parser.parse_args(argv)

    window_start = parse_dt(args.window_start)
    if not window_start:
        raise SystemExit(f"Invalid --window-start: {args.window_start}")
    window_end = parse_dt(args.window_end) if args.window_end else datetime.now(timezone.utc)
    if not window_end:
        raise SystemExit(f"Invalid --window-end: {args.window_end}")

    api_key = load_credentials()
    sf_cases = load_sf_cases(args.sf_cache)
    fd_spm = search_fd_created_in_window(api_key, window_start, window_end)
    if args.include_coi:
        fd_coi = search_fd_coi_in_window(api_key, window_start, window_end)
        fd_summaries = merge_fd_summaries(fd_spm, fd_coi)
    else:
        fd_summaries = fd_spm
    pairs = scan(fd_summaries, sf_cases, api_key, enrich=not args.no_enrich)
    intra = collect_intra_system_req_duplicates(fd_summaries, sf_cases)

    result = {
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "include_coi": args.include_coi,
        "fd_count": len(fd_summaries),
        "sf_count": len(sf_cases),
        "pair_count": len(pairs),
        "reportable_pair_count": sum(
            1
            for p in pairs
            if p["dup_type"]
            not in ("fedcerts_sender_noise", "subject_mismatch_skip")
        ),
        "true_same_thread": sum(1 for p in pairs if p["dup_type"] == "true_same_thread"),
        "likely_same_thread": sum(1 for p in pairs if p["dup_type"] == "likely_same_thread"),
        "same_sp_duplicate": sum(1 for p in pairs if p["dup_type"] == "same_sp_duplicate"),
        "coi_vet_required": sum(1 for p in pairs if p["dup_type"] == "coi_vet_required"),
        "subject_mismatch_skip": sum(1 for p in pairs if p["dup_type"] == "subject_mismatch_skip"),
        "contact_collision": sum(1 for p in pairs if p["dup_type"] == "contact_collision"),
        "fedcerts_sender_noise": sum(
            1 for p in pairs if p["dup_type"] == "fedcerts_sender_noise"
        ),
        "coi_req_id_matched": sum(
            1 for p in pairs if "coi_req_id_match" in p["match_reasons"]
        ),
        "coi_provider_matched": sum(
            1 for p in pairs if p["dup_type"] == "same_sp_duplicate"
        ),
        "intra_system_req_duplicates": intra,
        "pairs": pairs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report_path = args.report or args.output.with_suffix(".md")
    write_report_markdown(result, report_path)
    print(json.dumps({k: result[k] for k in result if k != "pairs"}, indent=2))
    print(f"OUTPUT: {args.output.resolve()}")
    print(f"REPORT: {report_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
