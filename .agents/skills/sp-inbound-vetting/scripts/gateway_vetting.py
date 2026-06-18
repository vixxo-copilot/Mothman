"""Gateway + VixxoLink SP lookup helpers for sp-inbound-vetting."""

from __future__ import annotations

import re
from typing import Any

from entity_match import (
    FUZZY_THRESHOLD,
    company_similarity,
    contact_name_similarity,
    is_exact_company_match,
    match_confidence,
)
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


def _annotate_hit(
    hit: dict,
    *,
    match_type: str = "exact",
    confidence: str = "High",
    score: float | None = None,
    alternates: list[dict] | None = None,
) -> dict:
    hit["match_type"] = match_type
    hit["confidence"] = confidence
    if score is not None:
        hit["match_score"] = round(score, 3)
    if alternates:
        hit["alternates"] = alternates
    return hit


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
        hit = sp_from_sr_payload(data, f"gateway_get_service_request({sr})")
        if hit:
            return _annotate_hit(hit, match_type="exact", confidence="High")
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
        hit = {
            "sp_number": sp_num,
            "name": sp_name,
            "source": f"vixxolink_resolve_service_request({sr})",
            "sr_number": sr,
        }
        return _annotate_hit(hit, match_type="exact", confidence="High")
    return None


def _score_invoice_rows_by_company(rows: list[dict], company: str) -> list[tuple[dict, float]]:
    scored: list[tuple[dict, float]] = []
    for row in rows:
        sp_name = str(row.get("serviceProviderName") or "")
        if not sp_name:
            continue
        score = company_similarity(company, sp_name)
        if score > 0:
            scored.append((row, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _score_invoice_rows_by_contact(rows: list[dict], name: str) -> list[tuple[dict, float]]:
    scored: list[tuple[dict, float]] = []
    for row in rows:
        creator = str(row.get("createdByUsername") or "")
        sp_name = str(row.get("serviceProviderName") or "")
        creator_score = contact_name_similarity(name, creator) if creator else 0.0
        name_score = contact_name_similarity(name, sp_name) if sp_name else 0.0
        score = max(creator_score, name_score)
        if score > 0:
            scored.append((row, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _alternates_from_scored(scored: list[tuple[dict, float]], best_score: float) -> list[dict]:
    from entity_match import CLOSE_SCORE_DELTA

    alts: list[dict] = []
    for row, score in scored[1:]:
        if best_score - score <= CLOSE_SCORE_DELTA and score >= FUZZY_THRESHOLD:
            alt = sp_from_invoice_row(row, "alternate")
            if alt:
                alt["match_score"] = round(score, 3)
                alts.append(alt)
    return alts


def pick_invoice_match(
    rows: list[dict],
    *,
    email: str | None = None,
    name: str | None = None,
    company: str | None = None,
    source_prefix: str = "gateway_search_invoices",
) -> dict | None:
    if not rows:
        return None
    email_norm = (email or "").strip().lower()

    if email_norm:
        for row in rows:
            creator = str(row.get("createdByUsername") or "").lower()
            if creator == email_norm:
                hit = sp_from_invoice_row(row, f"{source_prefix}(email={email_norm})")
                if hit:
                    return _annotate_hit(hit, match_type="exact", confidence="High", score=1.0)

    if name and len(name.strip()) >= 3:
        scored = _score_invoice_rows_by_contact(rows, name)
        if scored:
            best_row, best_score = scored[0]
            exact = contact_name_similarity(name, str(best_row.get("createdByUsername") or "")) >= 0.95
            if best_score >= FUZZY_THRESHOLD:
                hit = sp_from_invoice_row(best_row, f"{source_prefix}(name={name})")
                if hit:
                    return _annotate_hit(
                        hit,
                        match_type="exact" if exact else "fuzzy",
                        confidence=match_confidence(exact, best_score),
                        score=best_score,
                        alternates=_alternates_from_scored(scored, best_score),
                    )

    if company and company not in ("Not stated", ""):
        scored = _score_invoice_rows_by_company(rows, company)
        if scored:
            best_row, best_score = scored[0]
            sp_name = str(best_row.get("serviceProviderName") or "")
            exact = is_exact_company_match(company, sp_name)
            if best_score >= FUZZY_THRESHOLD:
                hit = sp_from_invoice_row(best_row, f"{source_prefix}(company={company})")
                if hit:
                    return _annotate_hit(
                        hit,
                        match_type="exact" if exact else "fuzzy",
                        confidence=match_confidence(exact, best_score),
                        score=best_score,
                        alternates=_alternates_from_scored(scored, best_score),
                    )

    hit = sp_from_invoice_row(rows[0], f"{source_prefix}(first-hit)")
    if hit:
        return _annotate_hit(hit, match_type="fuzzy", confidence="Low", score=0.0)
    return None


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
            return _annotate_hit(hit, match_type="exact", confidence="High")

    if email and email != "Not stated" and not is_internal_email(email):
        rows = gateway_search_invoices(searchString=email)
        hit = pick_invoice_match(
            rows, email=email, name=contact_name, company=company, source_prefix="gateway_search_invoices"
        )
        if hit and (hit.get("match_type") == "exact" or hit.get("match_score", 0) >= FUZZY_THRESHOLD):
            return hit
        local = email.split("@", 1)[0]
        if local and len(local) >= 4:
            rows = gateway_search_invoices(searchString=local)
            hit = pick_invoice_match(
                rows,
                email=email,
                name=contact_name,
                company=company,
                source_prefix="gateway_search_invoices(local-part)",
            )
            if hit and (hit.get("match_type") == "exact" or hit.get("match_score", 0) >= FUZZY_THRESHOLD):
                hit["source"] = f"gateway_search_invoices(local-part={local})"
                return hit

    if contact_name and contact_name not in ("Not stated", ""):
        rows = gateway_search_invoices(searchString=contact_name)
        hit = pick_invoice_match(rows, name=contact_name, company=company, source_prefix="gateway_search_invoices")
        if hit and (hit.get("match_type") == "exact" or hit.get("match_score", 0) >= FUZZY_THRESHOLD):
            return hit
        parts = contact_name.split()
        if len(parts) >= 2:
            last = parts[-1]
            if len(last) >= 3:
                rows = gateway_search_invoices(searchString=last)
                hit = pick_invoice_match(
                    rows,
                    name=contact_name,
                    company=company,
                    source_prefix=f"gateway_search_invoices(last-name={last})",
                )
                if hit and (hit.get("match_type") == "exact" or hit.get("match_score", 0) >= FUZZY_THRESHOLD):
                    return hit

    if company and company != "Not stated":
        rows = gateway_search_invoices(searchString=company)
        hit = pick_invoice_match(
            rows, company=company, source_prefix=f"gateway_search_invoices(company={company})"
        )
        if hit and (hit.get("match_type") == "exact" or hit.get("match_score", 0) >= FUZZY_THRESHOLD):
            return hit
        tokens = [t for t in re.sub(r"[^\w\s]", " ", company).split() if len(t) >= 4]
        if tokens:
            rows = gateway_search_invoices(searchString=tokens[0])
            hit = pick_invoice_match(
                rows,
                company=company,
                source_prefix=f"gateway_search_invoices(company-token={tokens[0]})",
            )
            if hit and (hit.get("match_type") == "exact" or hit.get("match_score", 0) >= FUZZY_THRESHOLD):
                return hit

    if email and "@" in email and not is_internal_email(email):
        domain = email.split("@", 1)[1].split(".")[0]
        if domain and len(domain) >= 4 and domain not in ("gmail", "yahoo", "aol", "hotmail", "icloud"):
            rows = gateway_search_invoices(searchString=domain)
            hit = pick_invoice_match(
                rows, company=company, source_prefix=f"gateway_search_invoices(domain={domain})"
            )
            if hit and (hit.get("match_type") == "exact" or hit.get("match_score", 0) >= FUZZY_THRESHOLD):
                return hit

    return None
