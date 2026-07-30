#!/usr/bin/env python3
"""Batch sp-voicemail-triage for qsiap@vixxo.com Freshdesk voicemails."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from batch_process_freshdesk import (
    SKIP_FORWARD_CATEGORIES,
    TRANSCRIPT_SOURCE,
    auth_headers,
    callback_decision,
    classify,
    detect_skip_forward,
    extract_metadata,
    format_stt_transcript,
    freshdesk_domain,
    http_json,
    is_voicemail_ticket,
    load_credentials,
    strip_html,
)
from qsiap_voicemail_entities import merge_transcript_entities  # noqa: E402
from transcribe_voicemail import get_whisper_model, transcribe_ticket  # noqa: E402

SPM_GROUP = "159000485013"
QSIAP = "qsiap@vixxo.com"
OUT_DIR = Path(__file__).resolve().parent.parent / ".tmp" / "qsiap-batch-run"
TIMEOUT = 90

AP_CATEGORIES = {"Billing / Invoice Support", "Payment Information"}
AP_ROUTES = {"aphelp@vixxo.com"}


def ticket_blob(ticket: dict) -> str:
    parts = [
        ticket.get("subject") or "",
        ticket.get("description_text") or strip_html(ticket.get("description") or ""),
    ]
    for field in ("to_emails", "cc_emails", "support_email"):
        val = ticket.get(field)
        if isinstance(val, list):
            parts.extend(str(x) for x in val)
        elif val:
            parts.append(str(val))
    for conv in ticket.get("conversations") or []:
        parts.append(conv.get("body_text") or strip_html(conv.get("body") or ""))
    return " ".join(parts).lower()


def qsiap_gate(ticket: dict) -> bool:
    return QSIAP in ticket_blob(ticket)


def search_open(api_key: str, query: str, max_pages: int = 12) -> list[dict]:
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        params = {"query": f'"{query}"', "page": str(page)}
        url = f"https://{freshdesk_domain()}/api/v2/search/tickets?" + urllib.parse.urlencode(
            params
        )
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError:
            break
        rows = data.get("results") or []
        out.extend(rows)
        if len(rows) < 30:
            break
    return out


def discover_qsiap_voicemails(api_key: str) -> list[dict]:
    by_id: dict[int, dict] = {}
    queries = (
        f"group_id:{SPM_GROUP} AND status:2 AND type:'Invoice Support'",
        f"group_id:{SPM_GROUP} AND status:2 AND type:null",
    )
    for q in queries:
        for row in search_open(api_key, q):
            tid = int(row["id"])
            if tid in by_id or not is_voicemail_ticket(row):
                continue
            ticket = http_json(
                "GET",
                f"/api/v2/tickets/{tid}?include=requester,conversations",
                api_key,
            )
            if not qsiap_gate(ticket):
                continue
            by_id[tid] = ticket
    return list(by_id.values())


def internal_note_qsiap(
    tid: int,
    meta: dict[str, Any],
    category: str,
    callback: str,
    urgency: str,
    route: str,
    transcript: str,
    *,
    disposition: str,
    company: str,
    transcript_source: str,
    skip_forward_reason: str | None,
) -> str:
    skip_line = (
        f"\n**Forward skipped:** {skip_forward_reason}" if skip_forward_reason else ""
    )
    return f"""**SP Voicemail Triage — Freshdesk #{tid} (QSIAP)**

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
**Inbox:** {QSIAP}
**Category:** {category}
**Callback required:** {callback} ({urgency})
**Caller:** {meta.get("caller") or "Not stated"} | **Company:** {company}
**Callback #:** {meta.get("phone") or "Not stated"}
**Disposition:** {disposition}
**Route:** {route}{skip_line}
**Transcript source:** {transcript_source}

---

**Transcript**

{transcript}

---

**Summary:** QSIAP AP voicemail processed by sp-voicemail-triage. Audio attachment retained on ticket.
"""


@dataclass
class Result:
    ticket_id: int
    caller: str
    phone: str
    company: str
    category: str
    route: str
    callback: str
    note: str = ""
    forward: str = ""
    resolve: str = ""
    error: str = ""
    transcribed: str = "no"


def process_qsiap_ticket(
    api_key: str,
    ticket: dict,
    *,
    dry_run: bool = False,
) -> Result:
    tid = int(ticket["id"])
    meta = extract_metadata(ticket)
    stt = transcribe_ticket(ticket, api_key)
    if not stt.get("ok"):
        return Result(
            ticket_id=tid,
            caller=str(meta.get("caller") or "—"),
            phone=str(meta.get("phone") or "—"),
            company="—",
            category="Skipped",
            route="—",
            callback="—",
            note="skipped:transcription-required",
            forward="not-sent:transcription-required",
            resolve="not-closed:transcription-required",
            error=str(stt.get("error") or "transcription failed"),
        )

    spoken = str(stt.get("transcript") or "")
    entities = merge_transcript_entities(meta, spoken)
    enriched_meta = {
        **meta,
        "caller": entities.get("caller") or meta.get("caller"),
        "phone": entities.get("phone") or meta.get("phone"),
        "company": entities.get("company") or "Not stated",
    }
    transcript = format_stt_transcript(stt, enriched_meta, ticket)
    skip_forward, skip_reason = detect_skip_forward(enriched_meta, stt, spoken)
    category, route, sr = classify(transcript, enriched_meta)
    if skip_forward:
        category = SKIP_FORWARD_CATEGORIES.get(skip_reason, category)
        route = "—"
    callback, urgency = callback_decision(transcript)
    if skip_forward:
        callback, urgency = "No", "Normal"

    # Already on QSIAP — do not forward AP categories back to aphelp
    stay_on_qsiap = (not skip_forward) and (
        category in AP_CATEGORIES or route in AP_ROUTES
    )
    if stay_on_qsiap:
        route = QSIAP
        disposition = "stay-on-qsiap:note+tags; leave open unless no-forward branch"
        do_forward = False
        do_resolve = False
    elif skip_forward:
        disposition = f"no-forward:{skip_reason}; resolve"
        do_forward = False
        do_resolve = True
    else:
        disposition = f"misroute-off-qsiap → {route}; forward+resolve"
        do_forward = "@" in route
        do_resolve = True
        if category == "Service Request / Dispatch" and sr:
            route = "service.providermanagement@vixxo.com"

    company = str(enriched_meta.get("company") or "Not stated")
    result = Result(
        ticket_id=tid,
        caller=str(enriched_meta.get("caller") or "—"),
        phone=str(enriched_meta.get("phone") or "—"),
        company=company,
        category=category,
        route=route,
        callback=callback,
        transcribed="yes",
    )

    if dry_run:
        result.note = "dry-run"
        result.forward = "dry-run" if do_forward else f"not-sent:{'stay-qsiap' if stay_on_qsiap else skip_reason or 'none'}"
        result.resolve = "dry-run-resolve" if do_resolve else "dry-run-leave-open"
        return result

    note_body = internal_note_qsiap(
        tid,
        enriched_meta,
        category,
        callback,
        urgency,
        route,
        transcript,
        disposition=disposition,
        company=company,
        transcript_source=str(stt.get("source") or TRANSCRIPT_SOURCE),
        skip_forward_reason=skip_reason,
    )
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

    tags = sorted(set((ticket.get("tags") or []) + ["qsiap-source", "voicemail-triaged"]))
    update: dict[str, Any] = {
        "tags": tags,
        "custom_fields": {"cf_sp": "Unknown"},
    }
    if not ticket.get("type"):
        update["type"] = "Invoice Support"

    if do_forward:
        forward_body = (
            f"SP Voicemail triage — Freshdesk #{tid} (from QSIAP)\n\n"
            f"Category: {category}\n"
            f"Caller: {enriched_meta.get('caller')}\n"
            f"Company: {company}\n"
            f"Callback: {enriched_meta.get('phone')}\n"
            f"Callback required: {callback}\n\n"
            f"{transcript}\n\n"
            f"— Automated triage (sp-voicemail-triage / QSIAP)."
        )
        fwd_payload: dict[str, Any] = {
            "body": forward_body,
            "to_emails": [route],
        }
        if category == "Service Request / Dispatch" and sr:
            fwd_payload["subject"] = f"{sr}, Need Assistance"
        try:
            http_json("POST", f"/api/v2/tickets/{tid}/forward", api_key, fwd_payload)
            result.forward = route
        except urllib.error.HTTPError as exc:
            result.forward = f"failed:{exc.code}"
            if not result.error:
                result.error = f"forward:{exc.reason}"
    else:
        result.forward = (
            "not-sent:stay-on-qsiap" if stay_on_qsiap else f"not-sent:{skip_reason or 'none'}"
        )

    if do_resolve:
        update["status"] = 5
        if not ticket.get("type") and category not in AP_CATEGORIES:
            update["type"] = ticket.get("type") or "Invoice Support"
        try:
            http_json("PUT", f"/api/v2/tickets/{tid}", api_key, update)
            result.resolve = "closed"
        except urllib.error.HTTPError as exc:
            result.resolve = f"failed:{exc.code}"
            if not result.error:
                result.error = f"resolve:{exc.reason}"
    else:
        try:
            http_json("PUT", f"/api/v2/tickets/{tid}", api_key, update)
            result.resolve = "left-open"
        except urllib.error.HTTPError as exc:
            result.resolve = f"failed:{exc.code}"
            if not result.error:
                result.error = f"update:{exc.reason}"

    return result


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    api_key = load_credentials()
    try:
        get_whisper_model()
    except RuntimeError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    tickets = discover_qsiap_voicemails(api_key)
    results: list[Result] = []
    for ticket in tickets:
        tags = ticket.get("tags") or []
        if "voicemail-triaged" in tags and "--re-triage" not in sys.argv:
            continue
        try:
            results.append(process_qsiap_ticket(api_key, ticket, dry_run=dry_run))
        except Exception as exc:  # noqa: BLE001
            results.append(
                Result(
                    ticket_id=int(ticket.get("id", 0)),
                    caller="?",
                    phone="?",
                    company="?",
                    category="?",
                    route="?",
                    callback="?",
                    error=str(exc),
                )
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "source": "qsiap@vixxo.com",
        "discovered": len(tickets),
        "processed": len(results),
        "dry_run": dry_run,
        "routed_off_qsiap": sum(1 for r in results if r.forward and "@" in r.forward and QSIAP not in r.forward),
        "stayed_on_qsiap": sum(1 for r in results if r.forward == "not-sent:stay-on-qsiap"),
        "closed": sum(1 for r in results if r.resolve == "closed"),
        "left_open": sum(1 for r in results if r.resolve == "left-open"),
        "failed": [r.ticket_id for r in results if r.error],
        "results": [r.__dict__ for r in results],
        "run_at": datetime.now(timezone.utc).isoformat(),
    }
    out = OUT_DIR / f"qsiap-batch-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary_path": str(out),
                **{
                    k: summary[k]
                    for k in (
                        "discovered",
                        "processed",
                        "routed_off_qsiap",
                        "stayed_on_qsiap",
                        "closed",
                        "left_open",
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
