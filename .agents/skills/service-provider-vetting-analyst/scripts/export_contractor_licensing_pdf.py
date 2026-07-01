#!/usr/bin/env python3
"""Export contractor licensing reference guide + quick lookup table to PDF."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fpdf import FPDF

BASE = Path(__file__).resolve().parent.parent / "reference"
TABLE_MD = BASE / "contractor-licensing-quick-lookup-table.md"
GUIDE_MD = BASE / "contractor-licensing-us-states-territories.md"
SPECIALTY_MD = BASE / "contractor-licensing-specialty-trades.md"
PDF_OUT = BASE / "contractor-licensing-us-states-territories.pdf"


class GuidePDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(80, 80, 80)
        self.cell(
            0,
            7,
            "Vixxo - US Contractor Licensing Reference",
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(1)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def safe_text(text: str) -> str:
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u2192": "->",
        "\u2265": ">=",
        "\u00b7": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def write_block(pdf: GuidePDF, text: str, h: float = 5) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, safe_text(text))


def md_to_pdf_lines(md: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    in_code = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            lines.append(("code", line))
            continue
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


def render_lines(pdf: GuidePDF, lines: list[tuple[str, str]]) -> None:
    for kind, text in lines:
        if kind == "blank":
            pdf.ln(2)
            continue
        if kind == "h1":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_text_color(10, 10, 10)
            write_block(pdf, text, 7)
            pdf.ln(2)
        elif kind == "h2":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(20, 20, 20)
            write_block(pdf, text, 6)
            pdf.ln(1)
        elif kind == "h3":
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 5)
        elif kind == "bold":
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 4)
        elif kind == "row":
            pdf.set_font("Courier", "", 7)
            pdf.set_text_color(20, 20, 20)
            write_block(pdf, text, 3.5)
        elif kind == "code":
            pdf.set_font("Courier", "", 7)
            pdf.set_text_color(40, 40, 40)
            write_block(pdf, text, 3.5)
        elif kind == "bullet":
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, f"  - {text}", 4)
        else:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 4)


def export_pdf() -> None:
    table_md = TABLE_MD.read_text(encoding="utf-8")
    guide_md = GUIDE_MD.read_text(encoding="utf-8")
    specialty_md = SPECIALTY_MD.read_text(encoding="utf-8")

    combined = (
        "# US Contractor Licensing Reference Guide\n\n"
        "**Includes quick lookup table + specialty trades + full jurisdiction detail**\n\n"
        "---\n\n"
        + table_md
        + "\n\n---\n\n"
        + specialty_md
        + "\n\n---\n\n"
        + guide_md
    )

    pdf = GuidePDF(orientation="L", unit="mm", format="Letter")
    pdf.alias_nb_pages()
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    render_lines(pdf, md_to_pdf_lines(combined))
    pdf.output(str(PDF_OUT))


def main() -> None:
    export_pdf()
    print(
        json.dumps(
            {
                "table_md": str(TABLE_MD),
                "specialty_md": str(SPECIALTY_MD),
                "guide_md": str(GUIDE_MD),
                "pdf": str(PDF_OUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
