"""Gateway + VixxoLink SP lookup helpers for sp-inbound-vetting."""

from __future__ import annotations

import re
from typing import Any

from entity_extraction import (
    caller_id_search_tokens,
    company_search_variants,
    email_domain_search_tokens,
    is_internal_email,
)
from mcp_http import mcp_call, mcp_result_text

GATEWAY_URL = "https://vixxonow.com/mcp/gateway"
VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"

# Skip city-only / overly broad Gateway searchString tokens (noise, huge result sets).
WEAK_GATEWAY_SEARCH_TOKENS = frozenset(
    {
        "youngstown",
        "cleveland",
        "columbus",
        "cincinnati",
        "toledo",
        "akron",
        "dayton",
        "dallas",
        "houston",
        "chicago",
        "phoenix",
        "austin",
    }
)


def _skip_gateway_search(term: str, *, last_name_only: bool = False) -> bool:
    """Skip bare city tokens in last-name fallback only; never skip full company strings."""
    norm = re.sub(r"[^\w\s]", "", (term or "").strip().lower())
    if not norm or len(norm) < 3:
        return True
    if last_name_only and norm in WEAK_GATEWAY_SEARCH_TOKENS:
        return True
    return False


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


def _normalize_company_key(name: str) -> str:
    return re.sub(r"[^\w\s]", "", (name or "").lower())


def pick_invoice_company_match(rows: list[dict], company: str) -> dict | None:
    """Pick invoice row whose SP name best matches the email-extracted company."""
    if not rows:
        return None

    company_key = _normalize_company_key(company)
    company_tokens = {t for t in company_key.split() if len(t) >= 3}
    best_row: dict | None = None
    best_score = 0

    for row in rows:
        sp_name = str(row.get("serviceProviderName") or "")
        sp_key = _normalize_company_key(sp_name)
        score = 0
        if company_key and (company_key in sp_key or sp_key in company_key):
            score += 5
        if company_tokens:
            overlap = sum(1 for token in company_tokens if token in sp_key)
            score += overlap
        if row.get("serviceProviderNumber"):
            score += 1
        if score > best_score:
            best_score = score
            best_row = row

    if best_row and best_score >= 2:
        return sp_from_invoice_row(
            best_row,
            f"gateway_search_invoices(company={company})",
        )
    if rows:
        return sp_from_invoice_row(rows[0], f"gateway_search_invoices(company={company})")
    return None


def gateway_swm_get_provider(sp_number: str) -> dict | None:
    """Resolve Siebel display name for a known SP / KS number."""
    if not sp_number:
        return None
    resp = mcp_call(
        GATEWAY_URL,
        "gateway_swm_get_provider",
        {"provider_number": sp_number, "sp_number": sp_number},
    )
    data = parse_json_blob(mcp_result_text(resp))
    if not isinstance(data, dict) or not data:
        return None
    name = data.get("name") or data.get("displayName") or data.get("providerName")
    num = data.get("number") or data.get("providerNumber") or sp_number
    if not num and not name:
        return None
    return {
        "sp_number": num,
        "name": name,
        "source": f"gateway_swm_get_provider({sp_number})",
    }


def _enrich_sp_hit(hit: dict | None) -> dict | None:
    if not hit:
        return None
    sp_num = hit.get("sp_number")
    if sp_num and (not hit.get("name") or str(sp_num).upper().startswith("KS")):
        detail = gateway_swm_get_provider(str(sp_num))
        if detail:
            hit = {**hit, **detail, "source": f"{hit.get('source')} + {detail.get('source')}"}
    return hit


def _company_candidates(entities: dict) -> list[str]:
    raw: list[str] = []
    for key in ("company", "signature_company"):
        value = entities.get(key) or ""
        if value and value not in ("Not stated", ""):
            raw.append(value)
    seen: set[str] = set()
    candidates: list[str] = []
    for name in raw:
        for variant in company_search_variants(name):
            key = variant.lower()
            if key not in seen:
                seen.add(key)
                candidates.append(variant)
    return candidates


def _gateway_find_sp_by_company(entities: dict) -> dict | None:
    """After email vetting, search Gateway by extracted company name for SP #."""
    candidates = _company_candidates(entities)
    if not candidates:
        return None

    for variant in candidates:
        if _skip_gateway_search(variant):
            continue
        rows = gateway_search_invoices(searchString=variant)
        hit = pick_invoice_company_match(rows, variant)
        hit = _enrich_sp_hit(hit)
        if hit and hit.get("sp_number"):
            return hit

    ks = entities.get("ks_number")
    if ks:
        return _enrich_sp_hit(gateway_swm_get_provider(ks))

    return None


def gateway_find_sp(entities: dict) -> dict | None:
    ks = entities.get("ks_number")
    sr = entities.get("sr_number")
    contact_name = entities.get("vetting_contact_name") or entities.get("contact_name") or ""
    contact_emails = list(entities.get("contact_emails") or [])
    requester = entities.get("requester_email") or ""
    if requester and requester != "Not stated" and requester.lower() not in contact_emails:
        contact_emails.insert(0, requester.lower())

    if sr:
        hit = _enrich_sp_hit(gateway_get_sr(sr))
        if hit:
            return hit
        hit = _enrich_sp_hit(vixxolink_get_sr_sp(sr))
        if hit:
            return hit

    if ks:
        rows = gateway_search_invoices(serviceProviderNumber=ks)
        hit = _enrich_sp_hit(
            sp_from_invoice_row(rows[0], f"gateway_search_invoices(KS={ks})") if rows else None
        )
        if hit:
            return hit
        hit = _enrich_sp_hit(gateway_swm_get_provider(ks))
        if hit:
            return hit

    for email in contact_emails:
        hit = _enrich_sp_hit(_gateway_find_sp_by_email(email))
        if hit:
            return hit

    if contact_name and contact_name not in ("Not stated", ""):
        search_tokens = caller_id_search_tokens(contact_name)
        if not search_tokens:
            search_tokens = [contact_name]
        for token in search_tokens:
            if _skip_gateway_search(token, last_name_only=len(token.split()) == 1):
                continue
            rows = gateway_search_invoices(searchString=token)
            hit = _enrich_sp_hit(
                pick_invoice_match(
                    rows,
                    name=contact_name,
                    email=requester if requester != "Not stated" else None,
                )
            )
            if hit:
                if token != contact_name:
                    hit["source"] = f"gateway_search_invoices(contact-token={token})"
                return hit

    return _gateway_find_sp_by_company(entities)


def gateway_health_check() -> dict:
    """Verify Gateway MCP search path before batch runs."""
    rows = gateway_search_invoices(serviceProviderNumber="KS69315")
    if rows:
        return {"ok": True, "probe": "gateway_search_invoices(KS69315)", "rows": len(rows)}
    rows = gateway_search_invoices(searchString="KS69315")
    if rows:
        return {"ok": True, "probe": "gateway_search_invoices(searchString=KS69315)", "rows": len(rows)}
    return {
        "ok": False,
        "error": "Gateway probe empty — use Cursor Gateway MCP (project-0-assistant-CGagner-gateway) or run enriched live_run --data",
    }


def _gateway_find_sp_by_email(email: str) -> dict | None:
    if not email or email == "Not stated" or is_internal_email(email):
        return None

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

    for token in email_domain_search_tokens(email):
        rows = gateway_search_invoices(searchString=token)
        hit = sp_from_invoice_row(rows[0], f"gateway_search_invoices(domain={token})") if rows else None
        if hit:
            return hit

    return None
