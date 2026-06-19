#!/usr/bin/env python3
"""Live ksonboarding-inbound-routing — internal notes + type reclassification."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import http_json, load_credentials  # noqa: E402
from exclusions import EXCLUDED, is_excluded  # noqa: E402

OUT_DIR = SCRIPT_DIR.parent / ".tmp" / "live-run"
FD_LINK = "https://vixxo-helpdesk.freshdesk.com/a/tickets/{tid}"


def build_note(tid: int, item: dict, *, tags_applied: list[str], cf_sp_applied: str | None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    gw = item.get("gateway_sp") or {}
    gw_line = "No match"
    if gw:
        gw_line = f"{gw.get('sp_number')} — {gw.get('name')} ({gw.get('source', 'Gateway')})"
    signals = ", ".join(item.get("signals") or []) or "none"
    cf_line = cf_sp_applied if cf_sp_applied else "left blank"
    type_line = item.get("type_change") or "none"
    return f"""**KS Onboarding Inbound Routing — Freshdesk #{tid}**

**Processed:** {ts}
**Queue:** ksonboarding@vixxo.com (KSOnboarding)
**Requester:** {item.get('requester', 'Not stated')}
**Subject:** {item.get('subject', '')}

---

**Classification**

| Field | Value |
| --- | --- |
| **Outcome** | {item.get('classification')} |
| **Type change** | {type_line} |
| **Signals** | {signals} |

---

**Vetting results**

**Entity posture:** {item.get('posture')} (confidence: {item.get('confidence', 'n/a')})
**Gateway SP:** {gw_line}

---

**Field updates**

- **cf_sp:** {cf_line}
- **cf_type_of_request:** {item.get('cf_type_of_request') or 'n/a'}
- **Tags added:** {', '.join(tags_applied)}

---

**Summary:** Automated ksonboarding-inbound-routing live run. Classification: {item.get('classification')}.
"""


def merge_tags(existing: list[str], new_tags: list[str]) -> list[str]:
    merged = list(existing or [])
    for tag in new_tags:
        if tag not in merged:
            merged.append(tag)
    return merged


def apply_item(api_key: str, item: dict) -> dict:
    tid = int(item["ticket_id"])
    result: dict = {
        "ticket_id": tid,
        "classification": item.get("classification"),
        "note": None,
        "type_update": None,
        "cf_sp": None,
        "status": "failed",
    }

    ticket = http_json("GET", f"/api/v2/tickets/{tid}", api_key)
    existing_tags = ticket.get("tags") or []
    route_tags = item.get("route_tags") or ["ks-inbound-routed"]
    tag_list = merge_tags(existing_tags, route_tags)

    cf_sp = item.get("cf_sp")
    current_cf = (ticket.get("custom_fields") or {}).get("cf_sp")
    cf_sp_applied = None
    custom_fields: dict = {}
    if cf_sp and not (current_cf and str(current_cf).strip()):
        custom_fields["cf_sp"] = cf_sp
        cf_sp_applied = cf_sp
    elif current_cf:
        cf_sp_applied = None

    if item.get("cf_type_of_request"):
        custom_fields["cf_type_of_request"] = item["cf_type_of_request"]

    note_body = build_note(tid, item, tags_applied=route_tags, cf_sp_applied=cf_sp_applied or "left blank")
    try:
        http_json(
            "POST",
            f"/api/v2/tickets/{tid}/notes",
            api_key,
            {"body": note_body, "private": True},
        )
        result["note"] = "posted"
    except Exception as exc:  # noqa: BLE001
        result["note"] = f"failed — {exc}"

    update_body: dict = {"tags": tag_list}
    if custom_fields:
        update_body["custom_fields"] = custom_fields
    if item.get("new_type") and not item.get("retain_type"):
        update_body["type"] = item["new_type"]

    try:
        http_json("PUT", f"/api/v2/tickets/{tid}", api_key, update_body)
        result["type_update"] = update_body.get("type") or "KSOnboarding retained"
        result["cf_sp"] = cf_sp_applied or "left blank"
        result["tags"] = tag_list
        result["status"] = "complete"
    except Exception as exc:  # noqa: BLE001
        result["type_update"] = f"failed — {exc}"
        result["status"] = "partial" if result["note"] == "posted" else "failed"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Live ksonboarding-inbound-routing batch")
    parser.add_argument("--re-route", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run-json", type=str, help="Apply from prior dry-run JSON path")
    args = parser.parse_args()

    if args.dry_run_json:
        dry_path = Path(args.dry_run_json)
        items = json.loads(dry_path.read_text(encoding="utf-8")).get("items") or []
    else:
        cmd = [sys.executable, str(SCRIPT_DIR / "dry_run_batch.py")]
        if args.re_route:
            cmd.append("--re-route")
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            return proc.returncode
        items = json.loads(proc.stdout).get("items") or []

    items = [item for item in items if not is_excluded(int(item["ticket_id"]))]
    excluded_applied = sorted(EXCLUDED.keys())

    api = load_credentials()
    results = [apply_item(api, item) for item in items]

    out = {
        "mode": "live",
        "skill": "ksonboarding-inbound-routing",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "excluded_ticket_ids": excluded_applied,
        "processed": len(results),
        "complete": sum(1 for r in results if r["status"] == "complete"),
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"live-run-{ts}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
