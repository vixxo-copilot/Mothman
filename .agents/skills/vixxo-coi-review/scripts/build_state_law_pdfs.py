#!/usr/bin/env python3
"""Build PDF exports for state-law reference docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fpdf import FPDF

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"

BUILDS = [
    {
        "md": SKILL_ROOT / "references" / "state-law-cancellation-wos.md",
        "pdf": ASSETS / "state-law-cancellation-wos.pdf",
        "header": "Vixxo COI - State Law Analysis (Cancellation & WC WOS)",
        "landscape": False,
        "compact": False,
    },
    {
        "md": SKILL_ROOT / "references" / "state-law-quick-reference.md",
        "pdf": ASSETS / "state-law-quick-reference.pdf",
        "header": "Vixxo COI - State Law Quick Reference",
        "landscape": True,
        "compact": True,
    },
]


def safe_text(text: str) -> str:
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2019", "'")
        .replace("\u2192", "->")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


class ReferencePDF(FPDF):
    def __init__(self, header_title: str, landscape: bool = False) -> None:
        super().__init__(orientation="L" if landscape else "P")
        self.header_title = header_title

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, safe_text(self.header_title), align="L")
        self.ln(3)

    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, safe_text(f"Page {self.page_no()}"), align="C")


def write_block(pdf: ReferencePDF, text: str, h: float) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, safe_text(text))


def parse_table_row(line: str) -> list[str]:
    return [c.strip().replace("**", "") for c in line.strip().strip("|").split("|")]


def render_table(
    pdf: ReferencePDF,
    header: list[str],
    rows: list[list[str]],
    *,
    compact: bool,
) -> None:
    col_count = len(header)
    if col_count == 0:
        return

    font_size = 5.5 if compact else 7
    row_h = 3.6 if compact else 5.5
    cell_h = 2.8 if compact else 4.2

    widths = [pdf.epw / col_count] * col_count
    if col_count == 4:
        widths = [pdf.epw * 0.07, pdf.epw * 0.26, pdf.epw * 0.20, pdf.epw * 0.47]
    elif col_count == 3:
        widths = [pdf.epw * 0.18, pdf.epw * 0.22, pdf.epw * 0.60]
    elif col_count == 2:
        widths = [pdf.epw * 0.28, pdf.epw * 0.72]

    pdf.set_font("Helvetica", "B", font_size)
    pdf.set_fill_color(230, 230, 230)
    x0 = pdf.l_margin
    y0 = pdf.get_y()
    for i, cell in enumerate(header):
        pdf.set_xy(x0 + sum(widths[:i]), y0)
        pdf.multi_cell(widths[i], row_h, safe_text(cell), border=1, fill=True, align="L")

    pdf.set_font("Helvetica", "", font_size)
    for row in rows:
        if pdf.get_y() > pdf.h - 14:
            pdf.add_page()
        y_start = pdf.get_y()
        x_start = pdf.l_margin
        heights = []
        for i, cell in enumerate(row):
            pdf.set_xy(x_start + sum(widths[:i]), y_start)
            pdf.multi_cell(widths[i], cell_h, safe_text(cell), border=0, align="L")
            heights.append(pdf.get_y() - y_start)
        row_height = max(heights) if heights else row_h
        for i in range(col_count):
            pdf.rect(x_start + sum(widths[:i]), y_start, widths[i], row_height)
        pdf.set_xy(x_start, y_start + row_height)


def build_pdf(
    md_text: str,
    pdf_path: Path,
    *,
    header_title: str,
    landscape: bool = False,
    compact: bool = False,
) -> None:
    pdf = ReferencePDF(header_title, landscape=landscape)
    margin = 6 if compact else 12
    pdf.set_margins(margin, margin, margin)
    pdf.set_auto_page_break(auto=True, margin=8 if compact else 16)
    pdf.add_page()

    h1 = 5 if compact else 7
    h2 = 4 if compact else 6
    h3 = 3.5 if compact else 5
    body = 3 if compact else 4.2
    body_font = 6 if compact else 8.5
    title_font = 10 if compact else 16
    section_font = 7 if compact else 12

    lines = md_text.splitlines()
    i = 0
    in_code = False
    table_header: list[str] | None = None
    table_rows: list[list[str]] = []

    def flush_table() -> None:
        nonlocal table_header, table_rows
        if table_header and table_rows:
            render_table(pdf, table_header, table_rows, compact=compact)
            pdf.ln(1 if compact else 2)
        table_header = None
        table_rows = []

    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("```"):
            in_code = not in_code
            i += 1
            continue

        if in_code:
            pdf.set_font("Courier", "", 6 if compact else 7)
            write_block(pdf, line, 3.2 if compact else 3.8)
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
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", title_font)
            pdf.set_text_color(10, 10, 10)
            write_block(pdf, line[2:], h1)
            pdf.ln(1)
        elif line.startswith("## "):
            pdf.ln(1.5 if compact else 3)
            pdf.set_font("Helvetica", "B", section_font)
            write_block(pdf, line[3:], h2)
        elif line.startswith("### "):
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 7 if compact else 10)
            write_block(pdf, line[4:], h3)
        elif line.startswith("> "):
            pdf.set_font("Helvetica", "I", body_font)
            write_block(pdf, line[2:], body)
        elif line.startswith("- "):
            pdf.set_font("Helvetica", "", body_font)
            write_block(pdf, "  * " + line[2:].replace("**", ""), body)
        elif line.strip() == "---":
            pdf.ln(1)
        elif line.strip() == "":
            pdf.ln(0.8 if compact else 1.5)
        else:
            pdf.set_font("Helvetica", "", body_font)
            write_block(pdf, line.replace("**", ""), body)

        i += 1

    flush_table()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(pdf_path))


def main() -> None:
    for spec in BUILDS:
        md_text = spec["md"].read_text(encoding="utf-8")
        build_pdf(
            md_text,
            spec["pdf"],
            header_title=spec["header"],
            landscape=spec["landscape"],
            compact=spec["compact"],
        )
        print(f"Wrote {spec['pdf']}")


if __name__ == "__main__":
    main()
