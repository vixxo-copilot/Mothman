#!/usr/bin/env python3
"""Combine SP account-review PDFs into one pack with cover, TOC, and bookmarks.

Example:
  python combine_account_review_pdf.py \\
    --sp-name "Ezzi Property Group" \\
    --sp-number KS69888 \\
    --section "Full SP Vetting Report=/path/vetting.pdf" \\
    --section "Email Timeline=/path/timeline.pdf" \\
    --appendix-states MA \\
    --vetting-bypassed \\
    --out "~/Downloads/Account Review - Ezzi Property Group KS69888.pdf"
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

GREEN = HexColor("#1B5E3B")
DARK = HexColor("#1A1A1A")
MUTED = HexColor("#555555")
LINE = HexColor("#C8D0CB")

SKILL_ROOT = Path(__file__).resolve().parents[1]


def _styles():
    s = getSampleStyleSheet()
    s.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=GREEN,
            leading=22,
            spaceAfter=8,
            alignment=TA_CENTER,
        )
    )
    s.add(
        ParagraphStyle(
            name="CoverSub",
            fontName="Helvetica",
            fontSize=11,
            textColor=DARK,
            leading=14,
            spaceAfter=4,
            alignment=TA_CENTER,
        )
    )
    s.add(
        ParagraphStyle(
            name="CoverMeta",
            fontName="Helvetica",
            fontSize=9,
            textColor=MUTED,
            leading=12,
            spaceAfter=3,
            alignment=TA_CENTER,
        )
    )
    s.add(
        ParagraphStyle(
            name="H1",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=GREEN,
            leading=16,
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    s.add(
        ParagraphStyle(
            name="Body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=DARK,
            leading=13,
            spaceAfter=6,
        )
    )
    s.add(
        ParagraphStyle(
            name="TOCLine",
            fontName="Helvetica",
            fontSize=10,
            textColor=DARK,
            leading=14,
            spaceAfter=4,
        )
    )
    s.add(
        ParagraphStyle(
            name="Footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=10,
            alignment=TA_CENTER,
        )
    )
    return s


def _parse_section(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(
            f"Section must be Title=path, got: {raw!r}"
        )
    title, path_s = raw.split("=", 1)
    path = Path(path_s).expanduser().resolve()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"PDF not found: {path}")
    return title.strip(), path


def _safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\\\|?*]+', " ", name).strip()


def _build_cover(
    sp_name: str,
    sp_number: str,
    toc: list[tuple[str, int]],
    vetting_bypassed: bool,
    contacts: str,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.65 * inch,
    )
    st = _styles()
    story = [
        Spacer(1, 0.55 * inch),
        Paragraph("Account Review", st["CoverTitle"]),
        Paragraph(_escape(sp_name), st["CoverTitle"]),
        Spacer(1, 0.12 * inch),
        Paragraph(f"SP Number: <b>{_escape(sp_number)}</b>", st["CoverSub"]),
        Paragraph(
            "Service Provider — Vetting, Communications &amp; Licensing Pack",
            st["CoverSub"],
        ),
        Spacer(1, 0.15 * inch),
        HRFlowable(
            width="60%",
            thickness=1,
            color=GREEN,
            spaceBefore=4,
            spaceAfter=10,
            hAlign="CENTER",
        ),
        Paragraph(
            f"Compiled {datetime.now().strftime('%B %d, %Y')}",
            st["CoverMeta"],
        ),
    ]
    if contacts:
        story.append(Paragraph(_escape(contacts), st["CoverMeta"]))
    if vetting_bypassed:
        story.append(
            Paragraph(
                "<b>Vetting: bypassed at operator request</b>",
                st["CoverMeta"],
            )
        )
    story.extend(
        [
            Spacer(1, 0.3 * inch),
            Paragraph("Table of Contents", st["H1"]),
            HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=8),
        ]
    )
    for title, page in toc:
        story.append(
            Paragraph(f"{_escape(title)} ………………… {page}", st["TOCLine"])
        )
    story.extend(
        [
            Spacer(1, 0.25 * inch),
            Paragraph(
                "This pack consolidates SP vetting (unless bypassed), communications "
                "timeline materials, license artifacts, and state license-scope notes "
                "for account review.",
                st["Body"],
            ),
            Spacer(1, 0.35 * inch),
            HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=6),
            Paragraph(
                "Internal work product · Not for external distribution without approval",
                st["Footer"],
            ),
        ]
    )
    doc.build(story)
    return buf.getvalue()


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _render_appendix_for_states(states: list[str]) -> bytes | None:
    if not states:
        return None
    from render_license_scope_appendix import build_appendix_pdf

    return build_appendix_pdf(states)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sp-name", required=True)
    parser.add_argument("--sp-number", required=True)
    parser.add_argument(
        "--section",
        action="append",
        default=[],
        type=_parse_section,
        help='Repeatable Title=path.pdf',
    )
    parser.add_argument(
        "--appendix-states",
        default="",
        help="Comma-separated state codes for license-scope appendix (e.g. MA,TX)",
    )
    parser.add_argument("--vetting-bypassed", action="store_true")
    parser.add_argument("--contacts", default="")
    parser.add_argument(
        "--out",
        default="",
        help="Output PDF path (default: ~/Downloads/Account Review - {name} {sp#}.pdf)",
    )
    args = parser.parse_args()

    sections: list[tuple[str, Path]] = list(args.section)
    states = [s.strip().upper() for s in args.appendix_states.split(",") if s.strip()]

    appendix_bytes = _render_appendix_for_states(states) if states else None

    cover_pages = 1
    page_cursor = cover_pages + 1
    toc: list[tuple[str, int]] = []
    for title, path in sections:
        toc.append((title, page_cursor))
        page_cursor += len(PdfReader(str(path)).pages)
    if appendix_bytes:
        toc.append(("Appendix — License Scope Notes", page_cursor))

    cover_bytes = _build_cover(
        args.sp_name,
        args.sp_number,
        toc,
        args.vetting_bypassed,
        args.contacts,
    )

    writer = PdfWriter()
    cover_reader = PdfReader(BytesIO(cover_bytes))
    for page in cover_reader.pages:
        writer.add_page(page)
    writer.add_outline_item("Cover & Table of Contents", 0)

    page_index = len(cover_reader.pages)
    for title, path in sections:
        reader = PdfReader(str(path))
        writer.add_outline_item(title, page_index)
        for page in reader.pages:
            writer.add_page(page)
        page_index += len(reader.pages)

    if appendix_bytes:
        appendix_reader = PdfReader(BytesIO(appendix_bytes))
        writer.add_outline_item("Appendix — License Scope Notes", page_index)
        for page in appendix_reader.pages:
            writer.add_page(page)

    if args.out:
        out = Path(args.out).expanduser().resolve()
    else:
        out = (
            Path.home()
            / "Downloads"
            / f"Account Review - {_safe_name(args.sp_name)} {args.sp_number}.pdf"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        writer.write(f)

    print(f"Wrote {out}")
    print(f"Total pages: {len(writer.pages)}")
    for title, page in toc:
        print(f"  p.{page}: {title}")


if __name__ == "__main__":
    main()
