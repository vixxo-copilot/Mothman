#!/usr/bin/env python3
"""Build PDF exports for state-law reference docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fpdf import FPDF

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
DESKTOP_SOPS = Path(
    r"C:\Users\CGagner\OneDrive - Vixxo\Desktop\Vixxo - Vendor Forms\Legacy SPS\Internal SOPs"
)

BUILDS = [
    {
        "md": SKILL_ROOT / "references" / "state-law-cancellation-wos.md",
        "pdf": ASSETS / "state-law-cancellation-wos.pdf",
        "header": "Vixxo COI - State Law Analysis (Cancellation & WC WOS)",
        "landscape": False,
        "compact": False,
        "desktop": DESKTOP_SOPS / "Vixxo COI State Law Analysis 2026.pdf",
    },
    {
        "md": SKILL_ROOT / "references" / "state-law-quick-reference.md",
        "pdf": ASSETS / "state-law-quick-reference.pdf",
        "header": "Vixxo COI - State Law Quick Reference",
        "landscape": True,
        "compact": True,
        "desktop": DESKTOP_SOPS / "Vixxo COI State Law Quick Reference 2026.pdf",
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


def _table_widths(pdf: ReferencePDF, header: list[str], compact: bool) -> list[float]:
    cols = len(header)
    if cols == 3 and header[0].lower() in {"situation", "tier"}:
        return [pdf.epw * 0.36, pdf.epw * 0.14, pdf.epw * 0.50]
    if cols == 3 and header[0].lower() == "states":
        return [pdf.epw * 0.22, pdf.epw * 0.78]
    if cols == 3:
        return [pdf.epw * 0.24, pdf.epw * 0.34, pdf.epw * 0.42]
    if cols == 2 and header[0].lower() in {"states", "state", "line", "provision"}:
        return [pdf.epw * 0.20, pdf.epw * 0.80]
    if cols == 2:
        return [pdf.epw * 0.30, pdf.epw * 0.70]
    if cols == 4:
        return [pdf.epw * 0.07, pdf.epw * 0.26, pdf.epw * 0.20, pdf.epw * 0.47]
    return [pdf.epw / cols] * cols


def _page_bottom(pdf: ReferencePDF, compact: bool) -> float:
    return pdf.h - (8 if compact else 16)


def _ensure_table_space(pdf: ReferencePDF, needed: float, compact: bool) -> None:
    if pdf.get_y() + needed > _page_bottom(pdf, compact):
        pdf.add_page()


def _draw_table_row(
    pdf: ReferencePDF,
    cells: list[str],
    widths: list[float],
    *,
    font_size: float,
    line_h: float,
    bold: bool,
    fill: bool,
) -> None:
    pdf.set_font("Helvetica", "B" if bold else "", font_size)
    if fill:
        pdf.set_fill_color(230, 230, 230)
    x0 = pdf.l_margin
    y0 = pdf.get_y()
    heights = []
    for i, cell in enumerate(cells):
        pdf.set_xy(x0 + sum(widths[:i]), y0)
        pdf.multi_cell(widths[i], line_h, safe_text(cell), border=0, fill=fill, align="L")
        heights.append(pdf.get_y() - y0)
    row_height = max(heights) if heights else line_h
    for i in range(len(cells)):
        pdf.rect(x0 + sum(widths[:i]), y0, widths[i], row_height)
    pdf.set_xy(x0, y0 + row_height)


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

    font_size = 6.5 if compact else 7
    line_h = 4.0 if compact else 5.5
    widths = _table_widths(pdf, header, compact)

    # Keep the whole header on one page. A near-bottom start used to
    # page-break after each header cell (blank pages with only "State").
    _ensure_table_space(pdf, line_h * 3, compact)

    old_auto, old_margin = pdf.auto_page_break, pdf.b_margin
    pdf.set_auto_page_break(auto=False)
    _draw_table_row(
        pdf, header, widths, font_size=font_size, line_h=line_h, bold=True, fill=True
    )
    pdf.set_auto_page_break(auto=old_auto, margin=old_margin)

    for row in rows:
        padded = list(row) + [""] * (col_count - len(row))
        padded = padded[:col_count]
        _ensure_table_space(pdf, line_h * 2, compact)
        pdf.set_auto_page_break(auto=False)
        _draw_table_row(
            pdf,
            padded,
            widths,
            font_size=font_size,
            line_h=3.2 if compact else 4.2,
            bold=False,
            fill=False,
        )
        pdf.set_auto_page_break(auto=old_auto, margin=old_margin)


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
    body_font = 6.5 if compact else 8.5
    title_font = 11 if compact else 16
    section_font = 8 if compact else 12

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
            write_block(pdf, "- " + line[2:].replace("**", ""), body)
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
    import shutil

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
        desktop = spec.get("desktop")
        if desktop and desktop.parent.is_dir():
            shutil.copy2(spec["pdf"], desktop)
            print(f"Copied {desktop}")
        elif desktop:
            print(f"Skipped desktop copy (folder missing): {desktop.parent}")


if __name__ == "__main__":
    main()
