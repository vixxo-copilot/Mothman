#!/usr/bin/env python3
"""Live sp-inbound-vetting batch — internal notes, cf_sp, tags, SF Tasks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import http_json, load_credentials  # noqa: E402
from queue_config import resolve_queues  # noqa: E402

OUT_DIR = SCRIPT_DIR.parent / ".tmp" / "live-run"
FD_LINK = "https://vixxo-helpdesk.freshdesk.com/a/tickets/{tid}"


def get_ticket(api_key: str, ticket_id: int) -> dict:
    return http_json("GET", f"/api/v2/tickets/{ticket_id}", api_key)


def sf_bin() -> str:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidate = Path(appdata) / "npm" / "sf.cmd"
            if candidate.is_file():
                return str(candidate)
    return "sf"


def posture_tag(posture: str) -> str:
    if posture.startswith("Known SP") or posture.startswith("Possible SP"):
        return "known-sp"
    if "SF Lead" in posture or posture.startswith("Prospect"):
        return "sf-lead-match"
    if "Case" in posture:
        return "sf-case-match"
    return "unknown-sp"


def gateway_row(item: dict) -> tuple[str, str]:
    gw = item.get("gateway_sp") or {}
    posture = item.get("posture") or ""
    if not gw:
        return "No", "No match"
    if posture.startswith("Possible SP"):
        score = gw.get("match_score")
        score_note = f" (similarity {score})" if score else ""
        alts = gw.get("alternates") or []
        alt_note = f"; alternates: {len(alts)}" if alts else ""
        return (
            "Possible",
            f"{gw.get('sp_number')} — {gw.get('name')}{score_note}{alt_note} ({gw.get('source', 'Gateway')})",
        )
    if posture.startswith("Known SP"):
        return "Yes", f"{gw.get('sp_number')} — {gw.get('name')} ({gw.get('source', 'Gateway')})"
    return "No", "No match"


def sf_lead_row(item: dict) -> tuple[str, str]:
    lead = item.get("sf_lead")
    if not lead:
        return "No", "No match"
    match_type = lead.get("match_type", "exact")
    label = "Yes" if match_type == "exact" else "Possible"
    score = lead.get("match_score")
    score_note = f" (similarity {score})" if score and match_type != "exact" else ""
    return label, f"{lead['Id']} — {lead.get('Status', 'Unknown')}{score_note}"


def sf_case_row(item: dict) -> tuple[str, str]:
    case = item.get("sf_case")
    if not case:
        return "No", "No match"
    match_type = case.get("match_type", "exact")
    label = "Yes" if match_type == "exact" else "Possible"
    score = case.get("match_score")
    score_note = f" (similarity {score})" if score and match_type != "exact" else ""
    case_num = case.get("CaseNumber") or case.get("Id")
    return label, f"{case_num} — {case.get('Status', 'Unknown')}{score_note}"


def is_lead_email_exact_match(item: dict, lead: dict) -> bool:
    requester = (item.get("requester") or "").strip().lower()
    lead_email = str(lead.get("Email") or "").strip().lower()
    if not requester or requester == "not stated" or not lead_email:
        return False
    return requester == lead_email or lead.get("match_kind") == "email"


def sf_task_allowed(record: dict | None, *, object_type: str, item: dict) -> tuple[bool, str | None]:
    """Return (allowed, skip_reason). Fuzzy or Medium/Low matches require human review."""
    if not record or not record.get("Id"):
        return False, None
    match_type = record.get("match_type", "fuzzy")
    confidence = record.get("confidence", "Low")
    if object_type == "lead" and is_lead_email_exact_match(item, record):
        return True, None
    if match_type == "fuzzy" or confidence in ("Medium", "Low"):
        return False, f"match_type={match_type}, confidence={confidence} — task skipped pending review"
    return True, None


def sf_match_review_entries(item: dict) -> list[dict]:
    entries: list[dict] = []
    for object_type, key in (("Lead", "sf_lead"), ("Case", "sf_case")):
        record = item.get(key)
        if not record or not record.get("Id"):
            continue
        allowed, reason = sf_task_allowed(record, object_type=key.split("_")[1], item=item)
        if not allowed and reason:
            entries.append(
                {
                    "object": object_type,
                    "id": record.get("Id"),
                    "match_type": record.get("match_type"),
                    "match_score": record.get("match_score"),
                    "confidence": record.get("confidence"),
                    "skip_reason": reason,
                }
            )
    return entries


def build_note(
    tid: int,
    item: dict,
    cf_sp_applied: str | None,
    tag_list: list[str],
    sf_lead_task: str,
    sf_case_task: str,
    review_entries: list[dict],
) -> str:
    gw_yes, gw_id = gateway_row(item)
    lead_yes, lead_id = sf_lead_row(item)
    case_yes, case_id = sf_case_row(item)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inbox = item.get("inbox_label") or "spm-intake"
    cf_line = cf_sp_applied if cf_sp_applied is not None else "(keep existing — not overwritten)"
    review_block = ""
    if review_entries:
        lines = ["**SF match — review required**", ""]
        for entry in review_entries:
            score = entry.get("match_score")
            score_note = f", score {score}" if score is not None else ""
            lines.append(
                f"- **{entry['object']}** `{entry['id']}` — "
                f"match_type={entry.get('match_type')}{score_note}, "
                f"confidence={entry.get('confidence')}. {entry['skip_reason']}."
            )
        lines.append("")
        review_block = "\n".join(lines) + "\n"
    return f"""**SP Inbound Vetting — Freshdesk #{tid}**

**Processed:** {ts}
**Inbox / queue:** {inbox}
**Requester:** {item.get('requester', 'Not stated')}
**Contact name:** {item.get('contact_name', 'Not stated')}
**Extracted company:** {item.get('company', 'Not stated')}
**Reference IDs:** SR {item.get('sr_number') or 'none'} | KS {item.get('ks_number') or 'none'}

---

**Vetting results**

| System | Match | Identifier |
| --- | --- | --- |
| Gateway SP | {gw_yes} | {gw_id} |
| Salesforce Lead | {lead_yes} | {lead_id} |
| Salesforce Case | {case_yes} | {case_id} |

**Entity posture:** {item['posture']} (confidence: {item.get('confidence', 'n/a')})

---

{review_block}**Freshdesk field update**

- **cf_sp set to:** {cf_line}
- **Tags added:** {', '.join(tag_list)}

---

**Salesforce notes**

- **Lead Task:** {sf_lead_task}
- **Case Task:** {sf_case_task}

---

**Summary:** Automated sp-inbound-vetting live run. Posture: {item['posture']}.

**Open questions:** {"SF Lead/Case match uncertain — confirm correct record before posting Task." if review_entries else "None beyond standard unknown-SP follow-up for unmatched items."}
"""


def resolve_cf_sp(item: dict, current: str | None) -> str | None:
    target = item.get("cf_sp_target", "Unknown")
    if target == "(keep existing)":
        return None
    current_norm = (current or "").strip()
    if current_norm and current_norm not in ("Unknown", "") and target != current_norm:
        if item["posture"].startswith("Known SP") and item.get("ticket_id") == 54635:
            return None
        if item["posture"] == "Unknown / Not in systems":
            return None
    return target


def create_sf_case_task(tid: int, item: dict, case_id: str) -> str:
    inbox = item.get("inbox_label") or "spm-intake"
    gw = item.get("gateway_sp") or {}
    gw_note = ""
    if gw.get("sp_number"):
        gw_note = f" Gateway SP: {gw.get('sp_number')} — {gw.get('name')}."
    desc = (
        f"Freshdesk #{tid} ({inbox}). Posture: {item['posture']}. "
        f"Company: {item.get('company')}. cf_sp target: {item.get('cf_sp_target')}.{gw_note} "
        f"Link: {FD_LINK.format(tid=tid)}. "
        f"Processed: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
    subject = f"Freshdesk inbound vetting — FD #{tid}"
    cmd = [
        sf_bin(),
        "data",
        "create",
        "record",
        "--sobject",
        "Task",
        "--target-org",
        "vixxo",
        "--json",
        "--values",
        f"Subject='{subject}' Description='{desc}' WhatId='{case_id}' Status='Completed' Priority='Normal'",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except FileNotFoundError:
        return "failed — sf CLI not found"
    if proc.returncode != 0:
        return f"failed — {(proc.stderr or proc.stdout or '')[:200].strip()}"
    try:
        payload = json.loads(proc.stdout)
        rec = (payload.get("result") or {}).get("id") or payload.get("result")
        return f"{case_id} — posted (Task {rec})"
    except json.JSONDecodeError:
        return f"{case_id} — posted"


def create_sf_lead_task(tid: int, item: dict, lead_id: str) -> str:
    inbox = item.get("inbox_label") or "spm-intake"
    desc = (
        f"Freshdesk #{tid} ({inbox}). Posture: {item['posture']}. "
        f"Company: {item.get('company')}. cf_sp target: {item.get('cf_sp_target')}. "
        f"Link: {FD_LINK.format(tid=tid)}. "
        f"Processed: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
    subject = f"Freshdesk inbound vetting — FD #{tid}"
    cmd = [
        sf_bin(),
        "data",
        "create",
        "record",
        "--sobject",
        "Task",
        "--target-org",
        "vixxo",
        "--json",
        "--values",
        f"Subject='{subject}' Description='{desc}' WhoId='{lead_id}' Status='Completed' Priority='Normal'",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except FileNotFoundError:
        return "failed — sf CLI not found"
    if proc.returncode != 0:
        return f"failed — {(proc.stderr or proc.stdout or '')[:200].strip()}"
    try:
        payload = json.loads(proc.stdout)
        rec = (payload.get("result") or {}).get("id") or payload.get("result")
        return f"{lead_id} — posted (Task {rec})"
    except json.JSONDecodeError:
        return f"{lead_id} — posted"


def apply_item(api_key: str, item: dict) -> dict:
    tid = int(item["ticket_id"])
    out: dict = {
        "ticket_id": tid,
        "queue": item.get("queue"),
        "posture": item["posture"],
        "note": None,
        "cf_sp": None,
        "tags": None,
        "sf_lead_task": "N/A",
        "sf_case_task": "N/A",
        "sf_task": "N/A",
        "sf_match_review": False,
        "error": None,
    }
    try:
        ticket = get_ticket(api_key, tid)
    except urllib.error.HTTPError as exc:
        out["error"] = f"get_ticket:{exc.code}"
        return out

    existing_tags = list(ticket.get("tags") or [])
    current_cf = (ticket.get("custom_fields") or {}).get("cf_sp")
    new_tags = sorted(set(existing_tags + ["sp-vetted", posture_tag(item["posture"])]))
    cf_sp_value = resolve_cf_sp(item, current_cf)

    review_entries = sf_match_review_entries(item)
    if review_entries:
        new_tags = sorted(set(new_tags + ["sf-match-review"]))
        out["sf_match_review"] = True

    sf_lead_task = "N/A"
    lead = item.get("sf_lead")
    if lead and lead.get("Id"):
        allowed, skip_reason = sf_task_allowed(lead, object_type="lead", item=item)
        if allowed:
            sf_lead_task = create_sf_lead_task(tid, item, lead["Id"])
        else:
            sf_lead_task = f"skipped — {skip_reason}"

    sf_case_task = "N/A"
    case = item.get("sf_case")
    if case and case.get("Id"):
        allowed, skip_reason = sf_task_allowed(case, object_type="case", item=item)
        if allowed:
            sf_case_task = create_sf_case_task(tid, item, case["Id"])
        else:
            sf_case_task = f"skipped — {skip_reason}"

    note_body = build_note(tid, item, cf_sp_value, new_tags, sf_lead_task, sf_case_task, review_entries)
    try:
        http_json("POST", f"/api/v2/tickets/{tid}/notes", api_key, {"body": note_body, "private": True})
        out["note"] = "posted"
    except urllib.error.HTTPError as exc:
        out["note"] = f"failed:{exc.code}"
        out["error"] = f"note:{exc.reason}"

    update_payload: dict = {"tags": new_tags}
    if cf_sp_value is not None:
        update_payload["custom_fields"] = {"cf_sp": cf_sp_value}
        out["cf_sp"] = cf_sp_value
    else:
        out["cf_sp"] = f"(keep: {current_cf})"

    try:
        http_json("PUT", f"/api/v2/tickets/{tid}", api_key, update_payload)
        out["tags"] = new_tags
    except urllib.error.HTTPError as exc:
        if not out["error"]:
            out["error"] = f"update:{exc.reason}"
        out["tags"] = f"failed:{exc.code}"

    out["sf_lead_task"] = sf_lead_task
    out["sf_case_task"] = sf_case_task
    out["sf_task"] = sf_lead_task
    return out


def load_items(data_path: Path | None, queue_arg: str, *, re_vet: bool = False) -> list[dict]:
    if data_path:
        data = json.loads(data_path.read_text(encoding="utf-8"))
        return data.get("items") or []

    from dry_run_batch import collect_queue  # noqa: WPS433

    api = load_credentials()
    items: list[dict] = []
    seen: set[int] = set()
    for queue in resolve_queues(queue_arg):
        for item in collect_queue(api, queue, re_vet=re_vet):
            tid = int(item["ticket_id"])
            if tid in seen:
                continue
            seen.add(tid)
            items.append(item)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Live sp-inbound-vetting batch")
    parser.add_argument("--queue", default="all", help="ksonboarding | invoice-concerns | aphelp | all")
    parser.add_argument("--data", type=Path, help="Optional dry-run JSON (skip re-vetting)")
    parser.add_argument("--re-vet", action="store_true", help="Include tickets already tagged sp-vetted")
    args = parser.parse_args()

    api = load_credentials()
    items = load_items(args.data, args.queue, re_vet=args.re_vet)
    results = [apply_item(api, item) for item in items]

    summary = {
        "mode": "live",
        "re_vet": args.re_vet,
        "queue": args.queue,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "notes_posted": sum(1 for r in results if r.get("note") == "posted"),
        "errors": [r for r in results if r.get("error")],
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"live-run-{args.queue}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if not summary["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
