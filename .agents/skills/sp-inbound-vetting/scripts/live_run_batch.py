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
from gateway_vetting import gateway_health_check  # noqa: E402
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
    if posture.startswith("Known SP"):
        return "known-sp"
    if "SF Lead" in posture or posture.startswith("Prospect"):
        return "sf-lead-match"
    if "Case" in posture:
        return "sf-case-match"
    return "unknown-sp"


def gateway_row(item: dict) -> tuple[str, str]:
    gw = item.get("gateway_sp") or {}
    if item["posture"].startswith("Known SP") and gw:
        return "Yes", f"{gw.get('sp_number')} — {gw.get('name')} ({gw.get('source', 'Gateway')})"
    return "No", item.get("gateway_sp") or "No match"


def sf_lead_row(item: dict) -> tuple[str, str]:
    lead = item.get("sf_lead")
    if lead:
        return "Yes", f"{lead['Id']} — {lead.get('Status', 'Unknown')}"
    return "No", "No match"


def sf_case_row(item: dict) -> tuple[str, str]:
    case = item.get("sf_case")
    if case:
        identifier = case.get("CaseNumber") or case.get("Id") or "Unknown case"
        status = case.get("Status") or "Unknown"
        subject = case.get("Subject")
        detail = f"{identifier} — {status}"
        if subject:
            detail = f"{detail} — {subject}"
        return "Yes", detail
    return "No", "No match"


def build_note(
    tid: int,
    item: dict,
    cf_sp_applied: str | None,
    tag_list: list[str],
    lead_task: str,
    case_task: str,
) -> str:
    gw_yes, gw_id = gateway_row(item)
    lead_yes, lead_id = sf_lead_row(item)
    case_yes, case_id = sf_case_row(item)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inbox = item.get("inbox_label") or "spm-intake"
    cf_line = cf_sp_applied if cf_sp_applied is not None else "(keep existing — not overwritten)"
    return f"""**SP Inbound Vetting — Freshdesk #{tid}**

**Processed:** {ts}
**Inbox / queue:** {inbox}
**Requester:** {item.get('requester', 'Not stated')}
**Contact name:** {item.get('contact_name', 'Not stated')}
**Vetting contact:** {item.get('vetting_contact_name') or item.get('contact_name', 'Not stated')}
**Contact emails searched:** {', '.join(item.get('contact_emails') or [item.get('requester', 'Not stated')])}
**Extracted company:** {item.get('company', 'Not stated')}
**Reference IDs:** SR {item.get('sr_number') or 'none'} | KS {item.get('ks_number') or 'none'}

---

**Vetting results**

| System | Match | Identifier |
| --- | --- | --- |
| Gateway SP | {gw_yes} | {gw_id} |
| Salesforce Lead | {lead_yes} | {lead_id} |
| Salesforce Case | {case_yes} | {case_id} |

**Entity posture:** {item['posture']}

---

**Freshdesk field update**

- **cf_sp set to:** {cf_line}
- **Tags added:** {', '.join(tag_list)}

---

**Salesforce notes**

- **Lead Task:** {lead_task}
- **Case Task:** {case_task}

---

**Summary:** Automated sp-inbound-vetting live run. Posture: {item['posture']}.

**Open questions:** None beyond standard unknown-SP follow-up for unmatched items.
"""


def resolve_cf_sp(item: dict, current: str | None) -> str | None:
    target = item.get("cf_sp_target", "Unknown")
    if target == "(keep existing)":
        return None
    current_norm = (current or "").strip()
    if current_norm and current_norm not in ("Unknown", "") and target != current_norm:
        if item["posture"] == "Unknown / Not in systems":
            return None
    return target


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
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
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


def create_sf_case_task(tid: int, item: dict, case_id: str) -> str:
    inbox = item.get("inbox_label") or "spm-intake"
    case = item.get("sf_case") or {}
    case_number = case.get("CaseNumber") or case_id
    desc = (
        f"Freshdesk #{tid} ({inbox}). Case: {case_number}. Posture: {item['posture']}. "
        f"Company: {item.get('company')}. cf_sp target: {item.get('cf_sp_target')}. "
        f"Link: {FD_LINK.format(tid=tid)}. "
        f"Processed: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
    subject = f"SP Inbound Vetting — Case {case_number}"
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
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
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


def apply_item(api_key: str, item: dict) -> dict:
    tid = int(item["ticket_id"])
    out: dict = {
        "ticket_id": tid,
        "queue": item.get("queue"),
        "posture": item["posture"],
        "note": None,
        "cf_sp": None,
        "tags": None,
        "sf_task": "N/A",
        "sf_lead_task": "N/A",
        "sf_case_task": "N/A",
        "error": None,
    }
    try:
        ticket = get_ticket(api_key, tid)
    except urllib.error.HTTPError as exc:
        out["error"] = f"get_ticket:{exc.code}"
        return out

    existing_tags = list(ticket.get("tags") or [])
    current_cf = (ticket.get("custom_fields") or {}).get("cf_sp")
    positive_tag = posture_tag(item["posture"])
    new_tags = sorted(set(existing_tags + ["sp-vetted", positive_tag]))
    if positive_tag != "unknown-sp":
        new_tags = [t for t in new_tags if t != "unknown-sp"]
    cf_sp_value = resolve_cf_sp(item, current_cf)

    lead_task = "N/A"
    lead = item.get("sf_lead")
    if lead and lead.get("Id"):
        lead_task = create_sf_lead_task(tid, item, lead["Id"])

    case_task = "N/A"
    case = item.get("sf_case")
    if case and case.get("Id"):
        case_task = create_sf_case_task(tid, item, case["Id"])

    note_body = build_note(tid, item, cf_sp_value, new_tags, lead_task, case_task)
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

    out["sf_task"] = lead_task
    out["sf_lead_task"] = lead_task
    out["sf_case_task"] = case_task
    return out


def load_items(data_path: Path | None, queue_arg: str, re_vet: bool = False) -> list[dict]:
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
    parser.add_argument("--re-vet", action="store_true", help="Include tickets already tagged sp-vetted")
    parser.add_argument("--data", type=Path, help="Optional dry-run JSON (skip re-vetting)")
    args = parser.parse_args()

    api = load_credentials()
    gw_health = gateway_health_check()
    items = load_items(args.data, args.queue, re_vet=args.re_vet)
    results = [apply_item(api, item) for item in items]

    summary = {
        "mode": "live",
        "queue": args.queue,
        "re_vet": args.re_vet,
        "gateway_health": gw_health,
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
