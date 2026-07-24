#!/usr/bin/env python3
"""Post-run corrections for QSIAP MCP vet batch — fix names, wrong matches, tags."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/sp-inbound-vetting/scripts"))
sys.path.insert(0, str(ROOT / ".agents/skills/sp-voicemail-triage/scripts"))

from batch_process_freshdesk import http_json, load_credentials  # noqa: E402
from live_run_batch import build_note  # noqa: E402

FIXES = [
    {
        "ticket_id": 84639,
        "contact_name": "Kevin Goodson",
        "company": "Goodson Services",
        "posture": "Known SP",
        "cf_sp": "68402 - Goodson Services",
        "gateway_sp": {"sp_number": "68402", "name": "Goodson Services", "source": "Salesforce Account + Gateway SP#68402"},
        "sf_account": {"Id": "001TS00000en8uaYAA", "Name": "Goodson Services", "Service_Provider_Number__c": "68402"},
    },
    {
        "ticket_id": 84447,
        "contact_name": "Chris",
        "company": "Bear Creek Lock, Safe And Alarm Inc.",
        "posture": "Known SP",
        "cf_sp": "13166 - Bear Creek Lock, Safe And Alarm Inc.",
        "gateway_sp": {"sp_number": "13166", "name": "Bear Creek Lock, Safe And Alarm Inc.", "source": "Salesforce Account (corrected — prior last-name=Creek false positive)"},
        "sf_account": {"Id": "001TS00000en8T8YAI", "Name": "Bear Creek Lock, Safe And Alarm Inc.", "Service_Provider_Number__c": "13166"},
        "correction_reason": "Prior Gateway last-name=C Creek matched wrong SP 67679 Horizon Sign; corrected to Bear Creek Lock SP 13166.",
    },
    {
        "ticket_id": 84733,
        "contact_name": "John Craft",
        "company": "KS - Craft's Locksmith LLC",
        "posture": "Known SP",
        "cf_sp": "KS69853 - KS - Craft's Locksmith LLC",
        "gateway_sp": {"sp_number": "KS69853", "name": "KS - Craft's Locksmith LLC", "source": "Gateway KS69853 + Salesforce Account"},
        "sf_account": {"Id": "001TS00000en8NIYAY", "Name": "KS - Craft's Locksmith LLC", "Service_Provider_Number__c": "KS69853"},
    },
    {
        "ticket_id": 84714,
        "contact_name": "Annika",
        "company": "KS - CCONLY - Bosart Lock & Key Inc",
        "posture": "Known SP",
        "cf_sp": "KS101323 - KS - CCONLY - Bosart Lock & Key Inc",
        "gateway_sp": {"sp_number": "KS101323", "name": "KS - CCONLY - Bosart Lock & Key Inc", "source": "Gateway KS101323 + Salesforce Account"},
        "sf_account": {"Id": "001TS00000en8E8YAI", "Name": "KS - CCONLY - Bosart Lock & Key Inc", "Service_Provider_Number__c": "KS101323"},
    },
    {
        "ticket_id": 84652,
        "contact_name": "Paul Bowser",
        "company": "KS - Customers Choice LLC",
        "posture": "Known SP + SF Lead",
        "cf_sp": "KS69724 - KS - Customers Choice LLC",
        "gateway_sp": {"sp_number": "KS69724", "name": "KS - Customers Choice LLC", "source": "Gateway KS69724 + Salesforce Account"},
        "sf_account": {"Id": "001TS00000en8NqYAI", "Name": "KS - Customers Choice LLC", "Service_Provider_Number__c": "KS69724"},
        "sf_lead": {"Id": "00QTS00000aZtJY2A0", "Status": "Open"},
    },
    {
        "ticket_id": 84642,
        "contact_name": "Yann",
        "company": "KS - Bill's Key Shop and Locksmith Service LLC",
        "posture": "Known SP",
        "cf_sp": "KS69472 - KS - Bill's Key Shop and Locksmith Service LLC",
        "gateway_sp": {"sp_number": "KS69472", "name": "KS - Bill's Key Shop and Locksmith Service LLC", "source": "Gateway KS69472 + Salesforce Account"},
        "sf_account": {"Id": "001TS00000en8DjYAI", "Name": "KS - Bill's Key Shop and Locksmith Service LLC", "Service_Provider_Number__c": "KS69472"},
    },
    {
        "ticket_id": 84480,
        "contact_name": "Keith",
        "company": "KS - General Fix-it, LLC",
        "posture": "Known SP + SF Lead",
        "cf_sp": "KS101491 - KS - General Fix-it, LLC",
        "gateway_sp": {"sp_number": "KS101491", "name": "KS - General Fix-it, LLC", "source": "Gateway KS101491 + Salesforce Account"},
        "sf_account": {"Id": "001TS00000enKafYAE", "Name": "KS - General Fix-it, LLC", "Service_Provider_Number__c": "KS101491"},
        "sf_lead": {"Id": "00QTS00000f2Sm32AE", "Status": "Open"},
    },
    {
        "ticket_id": 84444,
        "contact_name": "Michelle Sussman",
        "company": "KS - Andrews Plumbing Services Inc",
        "posture": "Known SP",
        "cf_sp": "KS68663 - KS - Andrews Plumbing Services Inc",
        "gateway_sp": {"sp_number": "KS68663", "name": "KS - Andrews Plumbing Services Inc", "source": "Gateway KS68663 + Salesforce Account"},
        "sf_account": {"Id": "001TS00000en8T5YAI", "Name": "KS - Andrews Plumbing Services Inc", "Service_Provider_Number__c": "KS68663"},
    },
    {
        "ticket_id": 84903,
        "contact_name": "RAOUL R JACQUES",
        "company": "Not stated",
        "posture": "Unknown / Not in systems",
        "cf_sp": "Unknown",
        "gateway_sp": None,
    },
    {
        "ticket_id": 84793,
        "contact_name": "BFPE International",
        "company": "Not stated",
        "posture": "Unknown / Not in systems",
        "cf_sp": "Unknown",
        "gateway_sp": None,
        "correction_reason": "Prior Gateway last-name=International matched internal National Accounts SP 22489; no confident provider match — left Unknown pending operator review.",
    },
]


def posture_tag(posture: str) -> str:
    if posture.startswith("Known SP"):
        return "known-sp"
    if "SF Lead" in posture or posture.startswith("Prospect"):
        return "sf-lead-match"
    return "unknown-sp"


def main() -> int:
    api = load_credentials()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []

    for row in FIXES:
        tid = int(row["ticket_id"])
        posture = row["posture"]
        tag = posture_tag(posture)
        tags = sorted(set(["sp-vetted", tag, "qsiap-source", "voicemail-vetted"]))
        item = {
            "ticket_id": tid,
            "queue": "qsiap-voicemail",
            "inbox_label": "qsiap@vixxo.com",
            "requester": "no-reply@8x8.com",
            "contact_name": row["contact_name"],
            "vetting_contact_name": row["contact_name"],
            "contact_emails": ["no-reply@8x8.com"],
            "company": row["company"],
            "ks_number": (row.get("gateway_sp") or {}).get("sp_number"),
            "sr_number": None,
            "posture": posture,
            "cf_sp_target": row["cf_sp"],
            "gateway_sp": row.get("gateway_sp"),
            "sf_lead": row.get("sf_lead"),
            "sf_case": None,
            "sf_account": row.get("sf_account"),
        }
        note = build_note(tid, item, row["cf_sp"], tags, "N/A", "N/A")
        if row.get("correction_reason"):
            note = note.replace(
                "**Summary:**",
                f"**Correction note:** {row['correction_reason']}\n\n**Summary:**",
            )
        note = note.replace(
            "**Summary:** Automated sp-inbound-vetting live run.",
            f"**Summary:** QSIAP MCP vet correction pass ({ts}).",
        )

        out = {"ticket_id": tid, "posture": posture, "cf_sp": row["cf_sp"]}
        try:
            http_json("POST", f"/api/v2/tickets/{tid}/notes", api, {"body": note, "private": True})
            out["note"] = "posted"
        except Exception as exc:  # noqa: BLE001
            out["note"] = f"failed:{exc}"

        payload = {"tags": tags, "type": "Invoice Support", "custom_fields": {"cf_sp": row["cf_sp"]}}
        try:
            http_json("PUT", f"/api/v2/tickets/{tid}", api, payload)
            out["update"] = "ok"
            out["tags"] = tags
        except Exception as exc:  # noqa: BLE001
            out["update"] = f"failed:{exc}"

        results.append(out)
        print(f"#{tid} {posture} | {row['cf_sp']} | note={out['note']} update={out['update']}")

    known = sum(1 for r in FIXES if r["posture"].startswith("Known SP"))
    summary = {"run_at": ts, "known_sp": known, "vetted": len(FIXES), "results": results}
    out_path = ROOT / ".agents/skills/sp-inbound-vetting/.tmp" / f"qsiap-mcp-corrections-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"known_sp": known, "vetted": len(FIXES), "report": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
