#!/usr/bin/env python3
"""Build or refresh exports/vixxo-sr-status-reference.xlsx.

Attempts live Gateway MCP sampling when GATEWAY_API_TOKEN / VIXXOLINK_API_TOKEN
is available; otherwise uses workspace-documented values.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports" / "vixxo-sr-status-reference.xlsx"
SCRIPTS = ROOT / ".agents" / "skills" / "sp-inbound-vetting" / "scripts"
TODAY = date.today().isoformat()

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)
META_FILL = PatternFill("solid", fgColor="FFF2CC")
LIVE_FILL = PatternFill("solid", fgColor="E2EFDA")
DOC_FILL = PatternFill("solid", fgColor="FCE4D6")


def style_header(ws, row: int) -> None:
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)


def autosize(ws, max_width: int = 60) -> None:
    from openpyxl.utils import get_column_letter

    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        width = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[letter].width = min(max(width + 2, 12), max_width)


def gateway_live_invoice_statuses() -> list[dict]:
    """Sample Gateway invoice.status values via MCP when credentials exist."""
    sys.path.insert(0, str(SCRIPTS))
    try:
        from gateway_vetting import gateway_search_invoices
        from mcp_http import _load_env, _token
    except ImportError:
        return []

    _load_env()
    if not _token():
        return []

    probes = [
        {"serviceProviderNumber": "KS69315"},
        {"serviceProviderNumber": "KS101031"},
        {"serviceProviderNumber": "KS101347"},
        {"searchString": "KS69315", "pageSize": 50},
        {"searchString": "invoice", "pageSize": 50},
    ]

    seen: dict[str, dict] = {}
    for kwargs in probes:
        try:
            rows = gateway_search_invoices(**kwargs)
        except Exception:
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            status = (
                row.get("status")
                or row.get("invoiceStatus")
                or row.get("invoice_status")
            )
            if not status:
                continue
            key = str(status).strip()
            if not key or key in seen:
                continue
            seen[key] = {
                "status": key,
                "sample_sr": row.get("serviceRequestNumber"),
                "sample_sp": row.get("serviceProviderNumber") or row.get("serviceProviderName"),
                "probe": json.dumps(kwargs, sort_keys=True),
            }
    return [seen[k] for k in sorted(seen)]


def documented_gateway_invoice_statuses() -> list[tuple]:
  return [
    ("Accepted", "Payment lifecycle", "Invoice accepted in billing workflow", "vixxo-freshdesk-invoice-review/SKILL.md"),
    ("Billed", "Payment lifecycle", "Invoice billed to customer/AP", "vixxo-freshdesk-invoice-review/SKILL.md"),
    ("Paid", "Payment lifecycle", "Invoice paid", "vixxo-freshdesk-invoice-review/SKILL.md"),
    ("UnderARInvestigation", "AP review / hold", "AR investigation hold", "vixxo-freshdesk-invoice-review/SKILL.md; vixxo-spm-invoice-concerns/SKILL.md"),
    ("ReviewByAP", "AP review / hold", "Accounts payable review required", "vixxo-freshdesk-invoice-review/SKILL.md; vixxo-spm-invoice-concerns/SKILL.md"),
    ("VisualAudit", "AP review / hold", "Visual audit review", "vixxo-freshdesk-invoice-review/SKILL.md; vixxo-spm-invoice-concerns/SKILL.md"),
    ("Invoice Review", "AP review / hold", "Invoice in AP line-item review (also appears as SR Substatus)", "vixxo-freshdesk-invoice-review/SKILL.md; sub-status-decoder.md"),
    ("PaidOnlyPending", "AP review / hold", "Paid-only pending state", "vixxo-freshdesk-invoice-review/SKILL.md; vixxo-spm-invoice-concerns/SKILL.md"),
    ("Invoice Creation Pending", "AP review / hold", "Invoice creation pending in billing system", "vixxo-freshdesk-invoice-review/SKILL.md; vixxo-spm-invoice-concerns/SKILL.md"),
    ("RejectedDoNotProcess", "Rejection", "Rejected; do not process payment", "vixxo-freshdesk-invoice-review/SKILL.md; starbucks-completed-sr-report/SKILL.md"),
    ("Delinquent SC Invoice", "Delinquent / vendor billing", "SP missed Service Channel invoice SLA (also SR Substatus)", "vixxo-freshdesk-invoice-review/SKILL.md; sub-status-decoder.md"),
    ("Invoice Required for SR", "SR billing overlap", "Work complete; SP invoice not yet uploaded (SR Substatus in VixxoLink)", "sub-status-decoder.md; vixxo-spm-invoice-concerns/SKILL.md"),
    ("AR Successful", "SR billing overlap", "AR booked invoice successfully (SR Substatus)", "sub-status-decoder.md"),
    ("No Invoice Pending", "SR billing overlap", "No invoice expected on SR", "sub-status-decoder.md"),
  ]


def build_invoice_tab_rows(live_rows: list[dict]) -> list[list]:
    rows: list[list] = []
    live_statuses = {r["status"] for r in live_rows}

    for live in live_rows:
        rows.append([
            live["status"],
            "invoice.status",
            "Gateway live sample",
            "",
            f"Observed via gateway_search_invoices ({live['probe']})",
            live.get("sample_sr") or "",
            live.get("sample_sp") or "",
            "Gateway MCP",
        ])

    for value, category, meaning, source in documented_gateway_invoice_statuses():
        if value in live_statuses:
            continue
        rows.append([
            value,
            "invoice.status",
            category,
            meaning,
            source,
            "",
            "",
            "Workspace documented (Gateway not queried or value not in sample)",
        ])

    rows.sort(key=lambda r: (r[2], r[0]))
    return rows


def ensure_invoice_tab(wb: Workbook, live_rows: list[dict]) -> None:
    title = "SP Invoice Status (Gateway)"
    if title in wb.sheetnames:
        del wb[title]
    ws = wb.create_sheet(title)

    ws["A1"] = f"Gateway SP invoice status reference — compiled {TODAY}"
    ws.merge_cells("A1:H1")
    ws["A1"].font = Font(bold=True, size=12)

    if live_rows:
        note = (
            "Source: live Gateway MCP sampling via gateway_search_invoices / "
            "gateway_get_invoice. Green rows were observed in this run; "
            "orange rows are workspace-documented values not seen in the sample."
        )
    else:
        note = (
            "Source: workspace-documented Gateway invoice.status values only. "
            "Gateway MCP bearer token was not available in this environment — "
            "re-run with GATEWAY_API_TOKEN or ~/.vixxo/gateway_api_token to "
            "refresh from live Gateway."
        )
    ws["A2"] = note
    ws.merge_cells("A2:H2")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws["A2"].fill = META_FILL
    ws.row_dimensions[2].height = 50

    headers = [
        "Invoice Status",
        "Gateway Field",
        "Category",
        "Meaning / AP Notes",
        "Source Reference",
        "Sample SR",
        "Sample SP",
        "Data Origin",
    ]
    ws.append([])
    ws.append(headers)
    header_row = ws.max_row
    style_header(ws, header_row)

    for row in build_invoice_tab_rows(live_rows):
        ws.append(row)
        origin_cell = ws.cell(row=ws.max_row, column=8)
        if "live sample" in str(origin_cell.value).lower():
            for col in range(1, 9):
                ws.cell(row=ws.max_row, column=col).fill = LIVE_FILL
        elif "documented" in str(origin_cell.value).lower():
            for col in range(1, 9):
                ws.cell(row=ws.max_row, column=col).fill = DOC_FILL

    autosize(ws)


def main() -> int:
    live_rows = gateway_live_invoice_statuses()
    if OUT.exists():
        wb = load_workbook(OUT)
    else:
        wb = Workbook()
    ensure_invoice_tab(wb, live_rows)
    wb.save(OUT)
    print(f"Updated {OUT}")
    print(f"Live Gateway invoice statuses sampled: {len(live_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
