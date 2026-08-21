#!/usr/bin/env python3
"""Fast local assembly of qsiap-gateway-enriched.json using MCP session caches."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PENDING = SCRIPT_DIR / "qsiap-gateway-enrich-pending.json"
OUTPUT = SCRIPT_DIR / "qsiap-gateway-enriched.json"

SKIP_CALLERS = frozenset(
    {"UNKNOWN", "WIRELESS CALLER", "NOT STATED", "VIXXO SERVICE C", ""}
)
NON_SP_NUMBERS = frozenset({"CCPAY_USD"})

# Gateway MCP SR cache (2026-07-16)
SR_CACHE = {
    "1-6583068442": {
        "sp_number": "KS101537",
        "name": "KS - Rapid Locksmith Solutions, Ltd.",
        "source": "gateway_get_service_request(1-6583068442)",
        "sr_number": "1-6583068442",
    },
}

# Salesforce MCP targeted matches (phone / company)
SF_ACCOUNT_BY_PHONE = {
    "4057207107": {
        "Id": "001TS00000enDgfYAE",
        "Name": "Doortech Garage Doors",
        "Type": "Service Provider",
        "Service_Provider_Number__c": "6691",
        "Phone": "4057207107",
    },
    "5184217487": {
        "Id": "001TS00000enJthYAE",
        "Name": "KS - Four Star Service of Albany, Inc",
        "Type": "Service Provider",
        "Service_Provider_Number__c": "F3267711",
        "Phone": "5184217487",
    },
}

SF_ACCOUNT_BY_COMPANY_TOKEN = {
    "doortec": SF_ACCOUNT_BY_PHONE["4057207107"],
    "four star": SF_ACCOUNT_BY_PHONE["5184217487"],
    "mesko glass": {
        "Id": "001TS00000en901YAA",
        "Name": "KS - Mesko Glass & Mirror Company",
        "Type": "Service Provider",
        "Service_Provider_Number__c": "10789",
        "Phone": "5703460777",
    },
    "arrow locksmith": {
        "Id": "001TS00000en85JYAQ",
        "Name": "KS - Arrow Locksmith Co",
        "Type": "Service Provider",
        "Service_Provider_Number__c": "13224",
        "Phone": "4078552080",
    },
    "rapid locksmith": {
        "Id": "001TS00000en9FzYAI",
        "Name": "KS - Rapid Locksmith Solutions, Ltd.",
        "Type": "Service Provider",
        "Service_Provider_Number__c": "KS101537",
        "Phone": None,
    },
}


def clean(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def phone_digits(value: str | None) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return digits[-10:] if len(digits) >= 10 else digits


def normalize_company_key(name: str) -> str:
    return re.sub(r"[^\w\s]", "", (name or "").lower())


def sf_lookup(item: dict) -> dict:
    out = {"lead": None, "case": None, "account": None}
    phone = phone_digits(item.get("phone"))
    if len(phone) >= 10 and phone in SF_ACCOUNT_BY_PHONE:
        out["account"] = SF_ACCOUNT_BY_PHONE[phone]

    company = normalize_company_key(clean(item.get("company")))
    if not out["account"]:
        for token, acct in SF_ACCOUNT_BY_COMPANY_TOKEN.items():
            if token in company:
                out["account"] = acct
                break
    return out


def gateway_lookup(item: dict) -> dict | None:
    tid = item["ticket_id"]
    if tid == 74250:
        return SR_CACHE["1-6583068442"]

    for sr in item.get("sr_numbers") or []:
        hit = SR_CACHE.get(sr)
        if hit and hit.get("sp_number") not in NON_SP_NUMBERS:
            return hit

    return None


def gw_from_account(acct: dict) -> dict | None:
    sp = str(acct.get("Service_Provider_Number__c") or "").strip()
    if not sp:
        return None
    return {
        "sp_number": sp,
        "name": acct.get("Name"),
        "source": "salesforce_account.Service_Provider_Number__c",
    }


def posture(gw: dict | None, sf: dict, company: str, cf_current: str | None) -> tuple[str, str]:
    if gw and sf.get("lead"):
        num, name = gw.get("sp_number"), gw.get("name")
        return "Known SP + SF Lead", f"{num} - {name}" if num else str(name or "Unknown")
    if gw:
        num, name = gw.get("sp_number"), gw.get("name")
        return "Known SP", f"{num} - {name}" if num else str(name or "Unknown")
    if sf.get("account") and sf["account"].get("Service_Provider_Number__c"):
        acct = sf["account"]
        sp = acct["Service_Provider_Number__c"]
        return "Known SP (SF Account)", f"{sp} - {acct.get('Name')}"
    if sf.get("lead"):
        return "Prospect (SF Lead only)", (sf["lead"] or {}).get("Company") or "Unknown"
    if sf.get("case"):
        return "Open SF Case", "Unknown"
    if company and company.upper() not in SKIP_CALLERS:
        return "Unknown / Not in systems", company
    return "Unknown / Not in systems", "Unknown"


def enrich(item: dict) -> dict:
    company = clean(item.get("company")) or "Not stated"
    sf = sf_lookup(item)
    gw = gateway_lookup(item)
    if not gw and sf.get("account"):
        gw = gw_from_account(sf["account"])

    post, cf_target = posture(gw, sf, company, item.get("cf_sp_current"))
    if item.get("cf_sp_current") and post == "Unknown / Not in systems":
        cf_target = "(keep existing)"

    caller = clean(item.get("contact_name") or "").upper()
    if post == "Unknown / Not in systems" and caller in SKIP_CALLERS:
        cf_target = "Unknown"

    return {
        **item,
        "posture": post,
        "cf_sp_target": cf_target,
        "gateway_sp": gw,
        "sf_lead": sf.get("lead"),
        "sf_case": sf.get("case"),
        "sf_account": sf.get("account"),
        "enriched_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    items = [enrich(i) for i in pending["items"]]
    known = sum(1 for i in items if str(i.get("posture", "")).startswith("Known SP"))

    out = {
        **{k: v for k, v in pending.items() if k != "items"},
        "mode": "gateway-enriched",
        "data_sources": {
            "gateway": "project-0-mothman-gateway MCP (51 invoice searches + 3 SR lookups)",
            "salesforce": "project-0-mothman-salesforce MCP (batched SOQL, org: vixxo)",
        },
        "enriched_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(items),
            "known_sp": known,
            "known_sp_sf_account": sum(1 for i in items if i.get("posture") == "Known SP (SF Account)"),
            "prospect_sf_lead": sum(1 for i in items if i.get("posture") == "Prospect (SF Lead only)"),
            "open_sf_case": sum(1 for i in items if i.get("posture") == "Open SF Case"),
            "unknown": sum(1 for i in items if i.get("posture") == "Unknown / Not in systems"),
            "pending_remaining": 0,
        },
        "items": items,
    }
    OUTPUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    for i in items:
        gw = i.get("gateway_sp") or {}
        print(f"#{i['ticket_id']} {i['posture']} SP={gw.get('sp_number','—')} cf_sp={i['cf_sp_target']}")
    print(f"\nWrote {OUTPUT} — {len(items)} items, {known} Known SP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
