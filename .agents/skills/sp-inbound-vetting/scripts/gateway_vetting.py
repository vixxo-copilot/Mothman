"""Gateway + VixxoLink SP lookup helpers for sp-inbound-vetting."""

from __future__ import annotations

import re
from typing import Any

from entity_extraction import company_search_variants, email_domain_search_tokens, is_internal_email
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


def _invoice_username_fields(row: dict) -> list[str]:
    """Usernames on an invoice row — not only the original creator."""
    out: list[str] = []
    for key in (
        "createdByUsername",
        "lastUpdatedByUsername",
        "createInvoiceBy",
        "submittedByUsername",
        "serviceProviderUsername",
    ):
        val = str(row.get(key) or "").strip().lower()
        if val and val not in out:
            out.append(val)
    return out


def pick_invoice_match(
    rows: list[dict],
    *,
    email: str | None = None,
    name: str | None = None,
    allow_first_hit: bool = True,
) -> dict | None:
    """Pick an invoice SP hit.

    Email-scoped searches match **any** username field (creator/updater/etc.),
    then SP name vs email local-part tokens. They do **not** fall through to an
    arbitrary first row — that mis-attributes agent/Vixxo-created invoices.
    """
    if not rows:
        return None
    email_norm = (email or "").strip().lower()
    name_norm = re.sub(r"[^\w\s]", "", (name or "").lower())
    local = email_norm.split("@", 1)[0] if email_norm and "@" in email_norm else ""
    local_tokens = [t for t in re.split(r"[^a-z0-9]+", local) if len(t) >= 4]

    if email_norm:
        for row in rows:
            if email_norm in _invoice_username_fields(row):
                hit = sp_from_invoice_row(
                    row, f"gateway_search_invoices(username={email_norm})"
                )
                if hit:
                    return hit
        # Local-part tokens in SP name (opendoorlockout → Open Door Lockout)
        if local_tokens:
            for row in rows:
                sp_name = re.sub(r"[^\w\s]", "", str(row.get("serviceProviderName") or "").lower())
                if sp_name and all(tok in sp_name.replace(" ", "") or tok in sp_name for tok in local_tokens[:2]):
                    hit = sp_from_invoice_row(
                        row, f"gateway_search_invoices(email-local→sp-name={local})"
                    )
                    if hit:
                        return hit
        # Email was requested but no confident row — do not guess first invoice
        return None

    if name_norm and len(name_norm) >= 3:
        for row in rows:
            for uname in _invoice_username_fields(row):
                uname_clean = re.sub(r"[^\w\s]", "", uname)
                if name_norm in uname_clean or uname_clean in name_norm:
                    hit = sp_from_invoice_row(row, f"gateway_search_invoices(name={name})")
                    if hit:
                        return hit

    if allow_first_hit:
        return sp_from_invoice_row(rows[0], "gateway_search_invoices(first-hit)")
    return None


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
        rows = gateway_search_invoices(searchString=contact_name)
        hit = _enrich_sp_hit(
            pick_invoice_match(rows, name=contact_name, email=requester if requester != "Not stated" else None)
        )
        if hit:
            return hit
        parts = contact_name.split()
        if len(parts) >= 2:
            last = parts[-1]
            if len(last) >= 3 and not _skip_gateway_search(last, last_name_only=True):
                rows = gateway_search_invoices(searchString=last)
                hit = _enrich_sp_hit(pick_invoice_match(rows, name=contact_name))
                if hit:
                    hit["source"] = f"gateway_search_invoices(last-name={last})"
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
        "error": (
            "Gateway probe empty. Ensure ~/.vixxo/gateway_api_token exists or run "
            ".cursor/bin/sync_gateway_token.py, then restart gateway MCP."
        ),
    }


def vixxolink_find_sp_by_email(email: str) -> dict | None:
    """Primary email→SP path: VixxoLink user record (who the login belongs to).

    Prefer this over invoice createdByUsername — invoices are often created by
    aiinvoicing / Vixxo staff, while the Case Contact email is the SP user.
    """
    if not email or email == "Not stated" or is_internal_email(email):
        return None
    resp = mcp_call(
        VIXXOLINK_URL,
        "vixxolink_get_user_site_access",
        {"email": email.strip()},
    )
    data = parse_json_blob(mcp_result_text(resp))
    if not isinstance(data, dict):
        return None
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    if payload.get("ok") is False:
        return None
    inner = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not inner.get("found"):
        return None
    sp_nums = inner.get("service_provider_numbers") or []
    if not isinstance(sp_nums, list) or not sp_nums:
        return None
    sp_num = str(sp_nums[0]).strip()
    if not sp_num:
        return None
    first = (inner.get("first_name") or "").strip()
    last = (inner.get("last_name") or "").strip()
    contact = f"{first} {last}".strip() or None
    return {
        "sp_number": sp_num,
        "name": None,
        "source": f"vixxolink_get_user_site_access(email={email.strip().lower()})",
        "contact_name": contact,
        "vixxolink_user_id": inner.get("user_id"),
        "access_type": inner.get("access_type"),
    }


def _gateway_find_sp_by_email(email: str) -> dict | None:
    """Resolve SP from requester email — VixxoLink user first, invoices second."""
    if not email or email == "Not stated" or is_internal_email(email):
        return None

    # 1) VixxoLink user ↔ SP# (correct identity for Case Contact / VL login)
    hit = vixxolink_find_sp_by_email(email)
    if hit:
        return hit

    # 2) Invoice search — match username fields / SP name, never random first row
    rows = gateway_search_invoices(searchString=email)
    hit = pick_invoice_match(rows, email=email, allow_first_hit=False)
    if hit:
        return hit

    local = email.split("@", 1)[0]
    if local and len(local) >= 4:
        rows = gateway_search_invoices(searchString=local)
        hit = pick_invoice_match(rows, email=email, allow_first_hit=False)
        if hit:
            hit["source"] = f"gateway_search_invoices(local-part={local})"
            return hit
        # Split local-part: opendoorlockout → try meaningful chunks via SP name
        chunks = [t for t in re.split(r"[^a-z0-9]+", local.lower()) if len(t) >= 5]
        if len(local) >= 8 and not chunks:
            # camel/run-on: opendoorlockout → opendoor, lockout (heuristic halves)
            mid = len(local) // 2
            chunks = [local[:mid], local[mid:]] if mid >= 4 else [local]
        for chunk in chunks[:3]:
            if _skip_gateway_search(chunk):
                continue
            rows = gateway_search_invoices(searchString=chunk)
            hit = pick_invoice_match(rows, email=email, allow_first_hit=False)
            if hit:
                hit["source"] = f"gateway_search_invoices(local-chunk={chunk})"
                return hit

    # 3) Business-domain only (never gmail/yahoo/etc. — email_domain_search_tokens filters)
    for token in email_domain_search_tokens(email):
        rows = gateway_search_invoices(searchString=token)
        # Domain search may return many SPs — require company-like alignment via local tokens
        hit = pick_invoice_match(rows, email=email, allow_first_hit=False)
        if hit:
            hit["source"] = f"gateway_search_invoices(domain={token})"
            return hit

    return None
