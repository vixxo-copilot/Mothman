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
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INBOUND_VETTING = SCRIPT_DIR.parents[1] / "sp-inbound-vetting" / "scripts"
VOICEMAIL = SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"
sys.path.insert(0, str(INBOUND_VETTING))
sys.path.insert(0, str(VOICEMAIL))

from batch_process_freshdesk import auth_headers, load_credentials  # noqa: E402
from dry_run_batch import get_ticket, DOMAIN  # noqa: E402
from queue_config import SPM_GROUP_ID  # noqa: E402

FD_TICKET_RE = re.compile(r"Freshdesk\s*#(\d+)", re.I)
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


def search_fd_created_in_window(api_key: str, window_start: datetime, window_end: datetime) -> list[dict]:
    seen: set[int] = set()
    out: list[dict] = []
    day = window_start.date()
    end_day = window_end.date()
    while day <= end_day:
        next_day = day.fromordinal(day.toordinal() + 1)
        filter_expr = (
            f"created_at:>'{day.isoformat()}' AND created_at:<'{next_day.isoformat()}' "
            f"AND group_id:{SPM_GROUP_ID}"
        )
        for page in range(1, 11):
            params = {"query": format_search_query(filter_expr), "page": str(page)}
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
    out.sort(key=lambda x: x.get("created_at") or "")
    return out


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


def scan(
    fd_summaries: list[dict],
    sf_cases: list[dict],
    api_key: str,
    enrich: bool,
) -> list[dict]:
    sf_by_email: dict[str, list[dict]] = {}
    sf_by_fd_id: dict[str, dict] = {}
    for c in sf_cases:
        for m in FD_TICKET_RE.finditer(c.get("Description") or ""):
            sf_by_fd_id[m.group(1)] = c
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
        if str(tid) in sf_by_fd_id:
            candidates[sf_by_fd_id[str(tid)]["Id"]] = sf_by_fd_id[str(tid)]
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
            if f"Freshdesk #{tid}" in desc:
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

            fd_meta: dict = {
                "id": tid,
                "subject": subject,
                "created_at": summary.get("created_at"),
                "status": summary.get("status"),
                "queue": classify_queue(summary),
                "requester": req_email,
            }
            if enrich:
                ticket = get_ticket(api_key, tid)
                try:
                    convs = get_conversations(api_key, tid)
                except Exception:
                    convs = []
                fd_meta["attachment_count"] = len(ticket.get("attachments") or [])
                fd_meta["conversation_count"] = len(convs)
                fd_meta["inline_images"] = len(
                    re.findall(r"<img\s", ticket.get("description") or "", re.I)
                )

            fd_created = parse_dt(summary.get("created_at"))
            sf_created = parse_dt(sf.get("CreatedDate"))
            origin = "unclear"
            if fd_created and sf_created:
                if sf_created < fd_created:
                    origin = "sf_first"
                elif fd_created < sf_created:
                    origin = "fd_first"
                else:
                    origin = "same_time"

            pairs.append(
                {
                    "match_reasons": reasons,
                    "dup_type": dup_type,
                    "origin": origin,
                    "subject_similarity": round(sim, 3),
                    "freshdesk": fd_meta,
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
            )
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-start", required=True, help="ISO8601 UTC, e.g. 2026-06-24T18:00:00Z")
    parser.add_argument("--window-end", default=None, help="ISO8601 UTC; default now")
    parser.add_argument("--sf-cache", required=True, type=Path, help="SF Cases JSON export")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--no-enrich", action="store_true", help="Skip per-ticket FD API enrichment")
    args = parser.parse_args(argv)

    window_start = parse_dt(args.window_start)
    if not window_start:
        raise SystemExit(f"Invalid --window-start: {args.window_start}")
    window_end = parse_dt(args.window_end) if args.window_end else datetime.now(timezone.utc)

    api_key = load_credentials()
    sf_cases = load_sf_cases(args.sf_cache)
    fd_summaries = search_fd_created_in_window(api_key, window_start, window_end)
    pairs = scan(fd_summaries, sf_cases, api_key, enrich=not args.no_enrich)

    result = {
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "fd_count": len(fd_summaries),
        "sf_count": len(sf_cases),
        "pair_count": len(pairs),
        "true_same_thread": sum(1 for p in pairs if p["dup_type"] == "true_same_thread"),
        "likely_same_thread": sum(1 for p in pairs if p["dup_type"] == "likely_same_thread"),
        "contact_collision": sum(1 for p in pairs if p["dup_type"] == "contact_collision"),
        "pairs": pairs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if k != "pairs"}, indent=2))
    print(f"OUTPUT: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
