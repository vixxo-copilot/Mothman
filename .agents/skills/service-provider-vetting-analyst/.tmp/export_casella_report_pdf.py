#!/usr/bin/env python3
"""Export Casella / Executive Doors / JC Doors vetting report to PDF."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fpdf import FPDF

BASE = Path(__file__).resolve().parent
MD_IN = BASE / "sp-vetting-report-casella-tx-20260629.md"
PDF_OUT = BASE / "sp-vetting-report-casella-tx-20260629.pdf"


class ReportPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, "Vixxo - Service Provider Vetting Report", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def safe_text(text: str) -> str:
    text = text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return text.encode("latin-1", errors="replace").decode("latin-1")


def write_block(pdf: ReportPDF, text: str, h: float = 5) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, safe_text(text))


def md_to_pdf_lines(md: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            lines.append(("blank", ""))
            continue
        if line.startswith("# "):
            lines.append(("h1", line[2:].strip()))
        elif line.startswith("## "):
            lines.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            lines.append(("h3", line[4:].strip()))
        elif line.startswith("| ") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            lines.append(("row", " | ".join(re.sub(r"\*\*", "", c) for c in cells)))
        elif line.startswith("- [x]"):
            lines.append(("bullet", "[x] " + line[6:].strip()))
        elif line.startswith("- [ ]"):
            lines.append(("bullet", "[ ] " + line[6:].strip()))
        elif line.startswith("- "):
            lines.append(("bullet", line[2:].strip()))
        elif line.startswith("**") and line.endswith("**"):
            lines.append(("bold", line.strip("*")))
        else:
            clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
            clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean)
            lines.append(("body", clean))
    return lines


def export_pdf(md: str) -> None:
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    for kind, text in md_to_pdf_lines(md):
        if kind == "blank":
            pdf.ln(2)
            continue
        if kind == "h1":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(10, 10, 10)
            write_block(pdf, text, 8)
            pdf.ln(2)
        elif kind == "h2":
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(20, 20, 20)
            write_block(pdf, text, 7)
            pdf.ln(1)
        elif kind == "h3":
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 6)
        elif kind == "bold":
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 5)
        elif kind == "row":
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(20, 20, 20)
            write_block(pdf, text, 4)
        elif kind == "bullet":
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, f"  - {text}", 4)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 4)
    pdf.output(str(PDF_OUT))


def main() -> None:
    md = MD_IN.read_text(encoding="utf-8")
    export_pdf(md)
    print(json.dumps({"markdown": str(MD_IN), "pdf": str(PDF_OUT)}, indent=2))


if __name__ == "__main__":
    main()
