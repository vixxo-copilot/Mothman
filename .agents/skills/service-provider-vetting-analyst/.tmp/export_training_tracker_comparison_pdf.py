#!/usr/bin/env python3
"""Export KS provider list vs Training Tracker comparison to PDF."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

BASE = Path(__file__).resolve().parent
TRACKER_JSON = Path(
    r"C:\Users\CGagner\.cursor\projects\c-Users-CGagner-source-assistant-CGagner\agent-tools\882d5389-60a2-4f12-b20c-328bf2129293.txt"
)
PDF_OUT = BASE / "training-tracker-provider-comparison-20260629.pdf"

PROVIDERS = {
    "16925": "KS - AC Professional Handymen LLC",
    "KS69136": "KS - DAT Repair LLC",
    "KS69673": "KS - Tim-s Handywork LLC",
    "KS69903": "KS - GS Flook Inc",
    "KS69060": "KS - Priority Cabling Services",
    "KS69845": "KS - Commercial Maintenance & Repair Inc",
    "KS101029": "KS - Allegiant LLC",
    "17786": "KS - Handyman Al",
    "KS68797": "Commercial Services LLC",
    "KS69073": "KS - SBE Handyman and Construction Services LLC",
    "KS69286": "KS - Upstate Maintenance & Improvements",
    "KS69771": "KS - Ace Handyman Services",
}

SOURCE = (
    "VixxoLink Transition Master Training Tracker v2.5.xlsx "
    "(Training Tracker - removed Dups sheet)"
)


def norm(code: str) -> str:
    code = str(code).strip().upper()
    if code.startswith("KS"):
        return code[2:]
    return code


def load_tracker() -> dict[str, dict]:
    data = json.loads(TRACKER_JSON.read_text(encoding="utf-8"))
    values = data["values"]
    col_map = {"name": 5, "su": 6, "sp": 7, "email": 8, "status": 9, "notes": 10}

    tracker: dict[str, dict] = {}
    for row in values[1:]:
        if not row or all((c is None or str(c).strip() == "") for c in row):
            continue
        sp = row[col_map["sp"]]
        sp = str(sp).strip() if sp is not None else ""
        if not sp:
            continue
        tracker[norm(sp)] = {
            "sp_raw": sp,
            "name": str(row[col_map["name"]] or "").strip(),
            "su": str(row[col_map["su"]] or "").strip(),
            "email": str(row[col_map["email"]] or "").strip(),
            "status": str(row[col_map["status"]] or "").strip() or "(blank)",
            "notes": str(row[col_map["notes"]] or "").strip(),
        }
    return tracker


def build_rows(tracker: dict[str, dict]) -> list[dict]:
    rows = []
    for code, list_name in PROVIDERS.items():
        t = tracker.get(norm(code))
        if not t:
            rows.append(
                {
                    "sp": code,
                    "list_name": list_name,
                    "tracker_name": "NOT ON TRACKER",
                    "su": "",
                    "status": "Missing",
                    "email": "",
                    "notes": "",
                }
            )
            continue
        rows.append(
            {
                "sp": code,
                "list_name": list_name,
                "tracker_name": t["name"],
                "su": t["su"],
                "status": t["status"],
                "email": t["email"],
                "notes": t["notes"],
            }
        )
    return rows


def safe(text: str) -> str:
    text = (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("&", "and")
    )
    return text.encode("latin-1", errors="replace").decode("latin-1")


class ComparisonPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(90, 90, 90)
        self.cell(0, 8, safe("Vixxo - Training Tracker Provider Comparison"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, safe(f"Page {self.page_no()}/{{nb}}"), align="C")

    def section_title(self, title: str) -> None:
        self.ln(3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(20, 20, 20)
        self.cell(0, 7, safe(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text: str) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, safe(text))
        self.ln(1)

    def summary_line(self, label: str, value: str) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(30, 30, 30)
        self.cell(45, 5, safe(label))
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, safe(value), new_x="LMARGIN", new_y="NEXT")


def status_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row["status"]
        counts[status] = counts.get(status, 0) + 1
    return counts


def write_table(pdf: ComparisonPDF, rows: list[dict]) -> None:
    headers = ["SP#", "Provider (list)", "Tracker name", "Status", "Email", "Notes"]
    widths = [18, 42, 42, 20, 38, 30]
    line_h = 4

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(20, 20, 20)
    for i, header in enumerate(headers):
        pdf.cell(widths[i], 6, safe(header), border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 6.5)
    for row in rows:
        cells = [
            row["sp"],
            row["list_name"],
            row["tracker_name"],
            row["status"],
            row["email"],
            row["notes"] or "-",
        ]
        wrapped = [pdf.multi_cell(w, line_h, safe(c), split_only=True) for w, c in zip(widths, cells)]
        row_h = max(len(w) for w in wrapped) * line_h
        if pdf.get_y() + row_h > pdf.page_break_trigger:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(230, 230, 230)
            for i, header in enumerate(headers):
                pdf.cell(widths[i], 6, safe(header), border=1, fill=True)
            pdf.ln()
            pdf.set_font("Helvetica", "", 6.5)

        x0 = pdf.get_x()
        y0 = pdf.get_y()
        for i, parts in enumerate(wrapped):
            x = x0 + sum(widths[:i])
            pdf.set_xy(x, y0)
            pdf.multi_cell(widths[i], line_h, safe("\n".join(parts)), border=1)
        pdf.set_xy(x0, y0 + row_h)


def export_pdf(rows: list[dict]) -> None:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = status_counts(rows)
    matched = sum(1 for r in rows if r["status"] != "Missing")
    follow_up = [r for r in rows if r["status"] in {"Pending", "Unresponsive", "(blank)"}]

    pdf = ComparisonPDF(orientation="L", unit="mm", format="Letter")
    pdf.alias_nb_pages()
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(10, 10, 10)
    pdf.cell(0, 10, safe("Training Tracker Provider Comparison"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.section_title("Source")
    pdf.body_text(SOURCE)
    pdf.body_text(f"Generated: {generated}")

    pdf.section_title("Summary")
    pdf.summary_line("Providers compared:", str(len(rows)))
    pdf.summary_line("Matched on tracker:", f"{matched} of {len(rows)}")
    pdf.summary_line("Missing from tracker:", str(len(rows) - matched))
    pdf.ln(1)
    for status, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        pdf.summary_line(f"{status}:", str(count))

    pdf.section_title("Follow-up required")
    if follow_up:
        for row in follow_up:
            note = f" - {row['notes']}" if row["notes"] else ""
            pdf.body_text(f"{row['sp']} | {row['list_name']} | Status: {row['status']}{note}")
    else:
        pdf.body_text("None.")

    pdf.section_title("Provider detail")
    write_table(pdf, rows)

    pdf.output(str(PDF_OUT))


def main() -> None:
    tracker = load_tracker()
    rows = build_rows(tracker)
    export_pdf(rows)
    print(json.dumps({"pdf": str(PDF_OUT), "providers": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
