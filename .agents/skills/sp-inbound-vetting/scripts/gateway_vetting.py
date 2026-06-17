"""Gateway + VixxoLink SP lookup helpers for sp-inbound-vetting."""

from __future__ import annotations

import re
from typing import Any

from mcp_http import mcp_call, mcp_result_text

GATEWAY_URL = "https://vixxonow.com/mcp/gateway"
VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"

INTERNAL_EMAIL_DOMAINS = (
    "@vixxo.com",
    "knowledgesync@vixxo.com",
)


def parse_json_blob(text: str) -> Any:
    import json

    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}|\[.*\]", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def invoice_list_from_response(data: Any) -> list[dict]:
    if not isinstance(data, dict):
        return []
    if isinstance(data.get("invoiceList"), list):
        return data["invoiceList"]
    nested = data.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("invoiceList"), list):
        return nested["invoiceList"]
    return []


def sp_from_invoice_row(row: dict, source: str) -> dict | None:
    sp_num = row.get("serviceProviderNumber")
    sp_name = row.get("serviceProviderName")
    if not sp_num and not sp_name:
        return None
    return {
        "sp_number": sp_num,
        "name": sp_name,
        "source": source,
        "sr_number": row.get("serviceRequestNumber"),
        "created_by": row.get("createdByUsername"),
    }


def sp_from_sr_payload(data: dict, source: str) -> dict | None:
    rows = data.get("serviceRequestList")
    if isinstance(rows, list) and rows:
        row = rows[0]
    else:
        row = data
    if not isinstance(row, dict):
        return None
    sp_num = row.get("siebelServiceProviderNum") or row.get("serviceProviderNumber")
    sp_name = row.get("serviceProviderName")
    if not sp_num and not sp_name:
        return None
    return {
        "sp_number": sp_num,
        "name": sp_name,
        "source": source,
        "sr_number": row.get("serviceRequestNumber"),
    }


def gateway_search_invoices(**kwargs: Any) -> list[dict]:
    resp = mcp_call(GATEWAY_URL, "gateway_search_invoices", kwargs)
    return invoice_list_from_response(parse_json_blob(mcp_result_text(resp)))


def gateway_get_sr(sr: str) -> dict | None:
    args = {"service_request_number": sr, "number": sr, "sr_number": sr}
    resp = mcp_call(GATEWAY_URL, "gateway_get_service_request", args)
    data = parse_json_blob(mcp_result_text(resp))
    if isinstance(data, dict):
        return sp_from_sr_payload(data, f"gateway_get_service_request({sr})")
    return None


def vixxolink_get_sr_sp(sr: str) -> dict | None:
    args = {"service_request_number": sr, "include": ["notes"]}
    resp = mcp_call(VIXXOLINK_URL, "vixxolink_resolve_service_request", args)
    data = parse_json_blob(mcp_result_text(resp))
    if not isinstance(data, dict):
        return None
    sp = data.get("serviceProvider") or {}
    sp_num = (
        data.get("serviceProviderNumber")
        or sp.get("number")
        or data.get("siebelServiceProviderNum")
    )
    sp_name = data.get("serviceProviderName") or sp.get("name")
    if not sp_num and not sp_name:
        nested = data.get("data") or data.get("serviceRequest") or {}
        if isinstance(nested, dict):
            sp_num = nested.get("serviceProviderNumber") or nested.get("siebelServiceProviderNum")
            sp_name = nested.get("serviceProviderName")
    if sp_num or sp_name:
        return {
            "sp_number": sp_num,
            "name": sp_name,
            "source": f"vixxolink_resolve_service_request({sr})",
            "sr_number": sr,
        }
    return None


def pick_invoice_match(rows: list[dict], *, email: str | None = None, name: str | None = None) -> dict | None:
    if not rows:
        return None
    email_norm = (email or "").strip().lower()
    name_norm = re.sub(r"[^\w\s]", "", (name or "").lower())

    if email_norm:
        for row in rows:
            creator = str(row.get("createdByUsername") or "").lower()
            if creator == email_norm:
                hit = sp_from_invoice_row(row, f"gateway_search_invoices(email={email_norm})")
                if hit:
                    return hit

    if name_norm and len(name_norm) >= 3:
        for row in rows:
            creator = re.sub(r"[^\w\s]", "", str(row.get("createdByUsername") or "").lower())
            if name_norm in creator or creator in name_norm:
                hit = sp_from_invoice_row(row, f"gateway_search_invoices(name={name})")
                if hit:
                    return hit

    return sp_from_invoice_row(rows[0], "gateway_search_invoices(first-hit)")


def is_internal_email(email: str) -> bool:
    lower = (email or "").lower()
    return any(token in lower for token in INTERNAL_EMAIL_DOMAINS)


def gateway_find_sp(entities: dict) -> dict | None:
    ks = entities.get("ks_number")
    sr = entities.get("sr_number")
    company = entities.get("company") or ""
    email = entities.get("requester_email") or ""
    contact_name = entities.get("contact_name") or ""

    if sr:
        hit = gateway_get_sr(sr)
        if hit:
            return hit
        hit = vixxolink_get_sr_sp(sr)
        if hit:
            return hit

    if ks:
        rows = gateway_search_invoices(serviceProviderNumber=ks)
        hit = sp_from_invoice_row(rows[0], f"gateway_search_invoices(KS={ks})") if rows else None
        if hit:
            return hit

    if email and email != "Not stated" and not is_internal_email(email):
        rows = gateway_search_invoices(searchString=email)
        hit = pick_invoice_match(rows, email=email)
        if hit:
            return hit
        local = email.split("@", 1)[0]
        if local and len(local) >= 4:
            rows = gateway_search_invoices(searchString=local)
            hit = pick_invoice_match(rows, email=email)
            if hit:
                hit["source"] = f"gateway_search_invoices(local-part={local})"
                return hit

    if contact_name and contact_name not in ("Not stated", ""):
        rows = gateway_search_invoices(searchString=contact_name)
        hit = pick_invoice_match(rows, name=contact_name)
        if hit:
            return hit
        parts = contact_name.split()
        if len(parts) >= 2:
            last = parts[-1]
            if len(last) >= 3:
                rows = gateway_search_invoices(searchString=last)
                hit = pick_invoice_match(rows, name=contact_name)
                if hit:
                    hit["source"] = f"gateway_search_invoices(last-name={last})"
                    return hit

    if company and company != "Not stated":
        rows = gateway_search_invoices(searchString=company)
        hit = sp_from_invoice_row(rows[0], f"gateway_search_invoices(company={company})") if rows else None
        if hit:
            return hit

    if email and "@" in email and not is_internal_email(email):
        domain = email.split("@", 1)[1].split(".")[0]
        if domain and len(domain) >= 4 and domain not in ("gmail", "yahoo", "aol", "hotmail", "icloud"):
            rows = gateway_search_invoices(searchString=domain)
            hit = sp_from_invoice_row(rows[0], f"gateway_search_invoices(domain={domain})") if rows else None
            if hit:
                return hit

    return None
