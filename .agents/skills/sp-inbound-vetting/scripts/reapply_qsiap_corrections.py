#!/usr/bin/env python3
"""Re-vet QSIAP voicemails with transcript-enriched entities + Gateway SP lookup."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "sp-voicemail-triage" / "scripts"))

from batch_process_freshdesk import http_json, load_credentials  # noqa: E402
from live_run_batch import build_note  # noqa: E402

# Corrected after manual review — transcript company/contact + Gateway SP #
CORRECTIONS: list[dict] = [
    {
        "ticket_id": 84639,
        "contact_name": "Kevin Goodson",
        "vetting_contact_name": "Kevin Goodson",
        "company": "Goodson Services",
        "phone": "214-536-3294",
        "ks_number": "68402",
        "sp_name": "Goodson Services",
        "sr_number": None,
    },
    {
        "ticket_id": 84652,
        "contact_name": "Paul Bowser",
        "vetting_contact_name": "Paul Bowser",
        "company": "KS - Customers Choice LLC",
        "phone": None,
        "ks_number": "KS69724",
        "sp_name": "KS - Customers Choice LLC",
        "sr_number": "1-6527807745",
    },
    {
        "ticket_id": 84733,
        "contact_name": "John Craft",
        "vetting_contact_name": "John Craft",
        "company": "KS - Craft's Locksmith LLC",
        "phone": None,
        "ks_number": "KS69853",
        "sp_name": "KS - Craft's Locksmith LLC",
        "sr_number": None,
    },
    {
        "ticket_id": 84714,
        "contact_name": "Annika",
        "vetting_contact_name": "Annika",
        "company": "KS - CCONLY - Bosart Lock & Key Inc",
        "phone": None,
        "ks_number": "KS101323",
        "sp_name": "KS - CCONLY - Bosart Lock & Key Inc",
        "sr_number": None,
    },
    {
        "ticket_id": 84480,
        "contact_name": "Keith",
        "vetting_contact_name": "Keith",
        "company": "KS - General Fix-it, LLC",
        "phone": "541-680-8890",
        "ks_number": "KS101491",
        "sp_name": "KS - General Fix-it, LLC",
        "sr_number": None,
    },
    {
        "ticket_id": 84444,
        "contact_name": "Michelle Sussman",
        "vetting_contact_name": "Michelle Sussman",
        "company": "KS - Andrews Plumbing Services Inc",
        "phone": None,
        "ks_number": "KS68663",
        "sp_name": "KS - Andrews Plumbing Services Inc",
        "sr_number": "1-6562006262",
    },
]


def to_item(row: dict) -> dict:
    sp_num = row["ks_number"]
    sp_name = row["sp_name"]
    cf_sp = f"{sp_num} - {sp_name}" if sp_name else sp_num
    return {
        "ticket_id": row["ticket_id"],
        "queue": "qsiap-voicemail",
        "inbox_label": "qsiap@vixxo.com",
        "subject": None,
        "company": row["company"],
        "contact_name": row["contact_name"],
        "vetting_contact_name": row["vetting_contact_name"],
        "contact_emails": ["no-reply@8x8.com"],
        "ks_number": sp_num,
        "sr_number": row.get("sr_number"),
        "requester": "no-reply@8x8.com",
        "cf_sp_current": None,
        "posture": "Known SP",
        "cf_sp_target": cf_sp,
        "gateway_sp": {
            "sp_number": sp_num,
            "name": sp_name,
            "source": "Gateway (manual correction + MCP verify)",
        },
        "sf_lead": None,
        "sf_case": None,
        "sf_account": None,
        "phone": row.get("phone"),
        "correction": True,
        "correction_reason": (
            "Prior run used 8x8 caller-ID labels and skipped Gateway lookup; "
            "re-vetted from audio transcript company/contact names."
        ),
    }


def main() -> int:
    api = load_credentials()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []

    for row in CORRECTIONS:
        tid = int(row["ticket_id"])
        item = to_item(row)
        cf_sp = item["cf_sp_target"]
        tags = ["known-sp", "sp-vetted", "qsiap-source", "voicemail-vetted", "vetting-corrected"]
        note_body = build_note(tid, item, cf_sp, tags, "N/A", "N/A")
        phone_line = f"**Callback #:** {row['phone']}\n" if row.get("phone") else ""
        note_body = note_body.replace(
            "**Summary:**",
            f"**Correction note:** {item['correction_reason']}\n{phone_line}\n**Summary:**",
        )

        out: dict = {"ticket_id": tid, "cf_sp": cf_sp}
        try:
            http_json(
                "POST",
                f"/api/v2/tickets/{tid}/notes",
                api,
                {"body": note_body, "private": True},
            )
            out["note"] = "posted"
        except Exception as exc:  # noqa: BLE001
            out["note"] = f"failed:{exc}"

        try:
            http_json(
                "PUT",
                f"/api/v2/tickets/{tid}",
                api,
                {
                    "tags": tags,
                    "type": "Invoice Support",
                    "custom_fields": {"cf_sp": cf_sp},
                },
            )
            out["update"] = "ok"
        except Exception as exc:  # noqa: BLE001
            out["update"] = f"failed:{exc}"

        results.append(out)
        print(f"#{tid} {item['contact_name']} | {cf_sp} | note={out['note']} update={out['update']}")

    out_dir = SKILL_DIR / ".tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"qsiap-vet-corrections-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps({"run_at": ts, "results": results}, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
