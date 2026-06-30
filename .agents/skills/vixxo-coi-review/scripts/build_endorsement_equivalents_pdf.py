#!/usr/bin/env python3
"""Build PDF export of references/endorsement-equivalents.md."""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

SKILL_ROOT = Path(__file__).resolve().parents[1]
MD_PATH = SKILL_ROOT / "references" / "endorsement-equivalents.md"
PDF_PATH = SKILL_ROOT / "assets" / "endorsement-equivalents.pdf"


def safe_text(text: str) -> str:
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2019", "'")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


class ReferencePDF(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, safe_text("Vixxo COI - Endorsement Equivalents Reference"), align="L")
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, safe_text(f"Page {self.page_no()}"), align="C")


def write_block(pdf: ReferencePDF, text: str, h: float = 4.5) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, safe_text(text))


def parse_table_row(line: str) -> list[str]:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def render_table(pdf: ReferencePDF, header: list[str], rows: list[list[str]]) -> None:
    col_count = len(header)
    if col_count == 0:
        return

    widths = [pdf.epw / col_count] * col_count
    if col_count == 4:
        widths = [pdf.epw * 0.06, pdf.epw * 0.28, pdf.epw * 0.22, pdf.epw * 0.44]
    elif col_count == 3:
        widths = [pdf.epw * 0.22, pdf.epw * 0.22, pdf.epw * 0.56]
    elif col_count == 2:
        widths = [pdf.epw * 0.34, pdf.epw * 0.66]

    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(230, 230, 230)
    x0 = pdf.l_margin
    y0 = pdf.get_y()
    row_h = 5.5
    for i, cell in enumerate(header):
        pdf.set_xy(x0 + sum(widths[:i]), y0)
        pdf.multi_cell(widths[i], row_h, safe_text(cell), border=1, fill=True, align="L")
    pdf.ln(0)

    pdf.set_font("Helvetica", "", 7)
    for row in rows:
        if pdf.get_y() > pdf.h - 20:
            pdf.add_page()
        y_start = pdf.get_y()
        x_start = pdf.l_margin
        heights = []
        for i, cell in enumerate(row):
            pdf.set_xy(x_start + sum(widths[:i]), y_start)
            pdf.multi_cell(widths[i], 4.2, safe_text(cell), border=0, align="L")
            heights.append(pdf.get_y() - y_start)
        row_height = max(heights) if heights else row_h
        for i in range(col_count):
            pdf.rect(x_start + sum(widths[:i]), y_start, widths[i], row_height)
        pdf.set_xy(x_start, y_start + row_height)


def build_pdf(md_text: str, pdf_path: Path) -> None:
    pdf = ReferencePDF()
    pdf.set_margins(12, 14, 12)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    lines = md_text.splitlines()
    i = 0
    in_code = False
    table_header: list[str] | None = None
    table_rows: list[list[str]] = []

    def flush_table() -> None:
        nonlocal table_header, table_rows
        if table_header and table_rows:
            render_table(pdf, table_header, table_rows)
            pdf.ln(2)
        table_header = None
        table_rows = []

    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("```"):
            in_code = not in_code
            i += 1
            continue

        if in_code:
            pdf.set_font("Courier", "", 7)
            write_block(pdf, line, 3.8)
            i += 1
            continue

        if line.startswith("|"):
            if re.match(r"^\|\s*-+", line):
                i += 1
                continue
            cells = parse_table_row(line)
            if table_header is None:
                table_header = cells
            else:
                table_rows.append(cells)
            i += 1
            continue

        flush_table()

        if line.startswith("# "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(10, 10, 10)
            write_block(pdf, line[2:], 7)
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(20, 20, 20)
            write_block(pdf, line[3:], 6)
            pdf.ln(1)
        elif line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            write_block(pdf, line[4:], 5)
            pdf.ln(1)
        elif line.startswith("> "):
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(40, 40, 40)
            write_block(pdf, line[2:], 4.2)
            pdf.set_text_color(0, 0, 0)
        elif line.startswith("- "):
            pdf.set_font("Helvetica", "", 8.5)
            write_block(pdf, "  * " + line[2:].replace("**", ""), 4.2)
        elif line.strip() == "---":
            pdf.ln(2)
        elif line.strip() == "":
            pdf.ln(1.5)
        else:
            pdf.set_font("Helvetica", "", 8.5)
            write_block(pdf, line.replace("**", ""), 4.2)

        i += 1

    flush_table()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(pdf_path))


def main() -> None:
    md_text = MD_PATH.read_text(encoding="utf-8")
    build_pdf(md_text, PDF_PATH)
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()
