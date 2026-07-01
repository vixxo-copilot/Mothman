#!/usr/bin/env python3
"""Query open SRs for a service provider by name via Gateway + VixxoLink MCP."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VETTING_SCRIPTS = SCRIPT_DIR.parents[1] / "sp-inbound-vetting" / "scripts"
sys.path.insert(0, str(VETTING_SCRIPTS))

from mcp_http import mcp_call, mcp_result_text  # noqa: E402

GATEWAY_URL = "https://vixxonow.com/mcp/gateway"
VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"
SP_NAME = "Crusaders Restoration"
WINDOW_MONTHS = 3


def parse_json_blob(text: str):
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


def invoice_rows(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    if isinstance(data.get("invoiceList"), list):
        return data["invoiceList"]
    nested = data.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("invoiceList"), list):
        return nested["invoiceList"]
    return []


def sr_rows(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    for key in ("serviceRequestList", "serviceRequests", "results", "items", "data"):
        val = data.get(key)
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            for inner in ("serviceRequestList", "serviceRequests", "results", "items"):
                nested = val.get(inner)
                if isinstance(nested, list):
                    return nested
    return []


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def resolve_sp_by_name(name: str) -> dict | None:
    variants = [
        name,
        name.replace(" Restoration", ""),
        "Crusaders",
    ]
    seen: set[str] = set()
    best: dict | None = None
    best_score = 0
    target = normalize_name(name)

    for variant in variants:
        key = variant.lower()
        if key in seen:
            continue
        seen.add(key)
        resp = mcp_call(GATEWAY_URL, "gateway_search_invoices", {"searchString": variant})
        text = mcp_result_text(resp)
        if text.startswith("HTTP ") or text.startswith("MCP stdio"):
            print(f"Gateway error ({variant}): {text[:300]}", file=sys.stderr)
            continue
        rows = invoice_rows(parse_json_blob(text))
        for row in rows:
            sp_num = row.get("serviceProviderNumber") or row.get("siebelServiceProviderNum")
            sp_name = row.get("serviceProviderName") or ""
            if not sp_num and not sp_name:
                continue
            score = 0
            norm = normalize_name(sp_name)
            if target in norm or norm in target:
                score += 5
            if "crusader" in norm:
                score += 3
            if sp_num:
                score += 1
            if score > best_score:
                best_score = score
                best = {
                    "sp_number": sp_num,
                    "name": sp_name,
                    "source": f"gateway_search_invoices(searchString={variant!r})",
                }
    return best


def fetch_open_srs(*, sp_number: str | None, sp_name: str) -> tuple[list[dict], str]:
    all_rows: list[dict] = []
    errors: list[str] = []
    search_args = [
        {"serviceProviderName": sp_name, "isOpen": True, "summary": True, "pageSize": 50},
    ]
    if sp_number:
        search_args.insert(0, {
            "serviceProviderNumber": sp_number,
            "isOpen": True,
            "summary": True,
            "pageSize": 50,
        })

    for base_args in search_args:
        page = 1
        while page <= 20:
            args = {**base_args, "pageNumber": page}
            resp = mcp_call(VIXXOLINK_URL, "vixxolink_search_service_requests", args)
            text = mcp_result_text(resp)
            if text.startswith("HTTP ") or text.startswith("MCP stdio"):
                errors.append(f"{args}: {text[:300]}")
                break
            data = parse_json_blob(text)
            rows = sr_rows(data)
            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < base_args["pageSize"]:
                break
            page += 1

    dedup: dict[str, dict] = {}
    for row in all_rows:
        num = row.get("number") or row.get("serviceRequestNumber")
        if num:
            dedup[str(num)] = row
    return list(dedup.values()), "; ".join(errors)


def parse_open_date(row: dict) -> datetime | None:
    for key in ("localCreatedDate", "createdDate", "openDate", "localOpenDate"):
        raw = row.get(key)
        if not raw:
            continue
        raw = str(raw).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(raw[:19], fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
    return None


def row_los(row: dict) -> str:
    for key in ("lineOfService", "lineOfServiceName", "los", "line_of_service"):
        val = row.get(key)
        if val:
            return str(val)
    nested = row.get("lineOfServiceObj") or row.get("lineOfServiceDetail") or {}
    if isinstance(nested, dict):
        return str(nested.get("name") or nested.get("description") or "")
    return ""


def main() -> int:
    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=WINDOW_MONTHS * 30)

    sp = resolve_sp_by_name(SP_NAME)
    if not sp:
        print(json.dumps({"error": f"Could not resolve SP by name: {SP_NAME}"}, indent=2))
        return 1

    rows, errors = fetch_open_srs(sp_number=str(sp.get("sp_number") or ""), sp_name=SP_NAME)
    filtered: list[dict] = []
    for row in rows:
        open_dt = parse_open_date(row)
        if open_dt and open_dt.tzinfo is None:
            open_dt = open_dt.replace(tzinfo=timezone.utc)
        if open_dt and open_dt < window_start:
            continue
        filtered.append({
            "sr_number": row.get("number") or row.get("serviceRequestNumber"),
            "open_date": (open_dt.isoformat() if open_dt else row.get("localCreatedDate") or row.get("createdDate")),
            "los": row_los(row),
            "short_description": row.get("shortDescription") or row.get("description") or row.get("summary"),
            "status": row.get("status") or row.get("statusName"),
            "sub_status": row.get("subStatus") or row.get("subStatusName"),
        })

    filtered.sort(key=lambda r: str(r.get("open_date") or ""), reverse=True)

    out = {
        "sp_name_query": SP_NAME,
        "sp_resolved": sp,
        "window_start": window_start.date().isoformat(),
        "window_end": window_end.date().isoformat(),
        "open_sr_count": len(filtered),
        "errors": errors or None,
        "rows": filtered,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
