#!/usr/bin/env python3
"""Render license-scope appendix PDF for one or more states.

MA uses the complete CSL citation pack. Other states render as stubs from
reference/license-scope-appendices.md until completed.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

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

REF = Path(__file__).resolve().parents[1] / "reference"
MA_CSL = REF / "ma-csl-scope.md"
STUBS = REF / "license-scope-appendices.md"


def _styles():
    s = getSampleStyleSheet()
    s.add(
        ParagraphStyle(
            name="H1",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=GREEN,
            leading=16,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    s.add(
        ParagraphStyle(
            name="H2",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=GREEN,
            leading=14,
            spaceBefore=10,
            spaceAfter=5,
        )
    )
    s.add(
        ParagraphStyle(
            name="Body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=DARK,
            leading=12,
            spaceAfter=5,
        )
    )
    s.add(
        ParagraphStyle(
            name="Quote",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=DARK,
            leading=12,
            leftIndent=10,
            rightIndent=6,
            spaceAfter=5,
        )
    )
    s.add(
        ParagraphStyle(
            name="LinkNote",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=11,
            spaceAfter=3,
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


def _md_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font face='Courier' size='8'>\1</font>", text)
    return text


def _flow_from_markdown(md: str, st) -> list:
    story = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            story.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            story.append(Paragraph(_md_inline(line[2:]), st["H1"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=GREEN, spaceAfter=6))
            continue
        if line.startswith("## "):
            story.append(Paragraph(_md_inline(line[3:]), st["H2"]))
            continue
        if line.startswith("### "):
            story.append(Paragraph(_md_inline(line[4:]), st["H2"]))
            continue
        if line.startswith("> "):
            story.append(Paragraph(_md_inline(line[2:]), st["Quote"]))
            continue
        if line.startswith("http://") or line.startswith("https://"):
            story.append(Paragraph(_md_inline(line), st["LinkNote"]))
            continue
        if line.startswith("|") or line.startswith("---") or line.startswith("```"):
            continue
        if line.startswith("- "):
            story.append(Paragraph("• " + _md_inline(line[2:]), st["Body"]))
            continue
        story.append(Paragraph(_md_inline(line), st["Body"]))
    return story


def _ma_section(st) -> list:
    if not MA_CSL.exists():
        return [Paragraph("MA CSL reference missing.", st["Body"])]
    return _flow_from_markdown(MA_CSL.read_text(encoding="utf-8"), st)


def _stub_section(state: str, st) -> list:
    story = [
        Paragraph(f"{state} — License Scope Note (Stub)", st["H1"]),
        HRFlowable(width="100%", thickness=0.8, color=GREEN, spaceAfter=6),
        Paragraph(
            f"<b>Status:</b> Stub — needs official citation pass before use as "
            f"authoritative guidance for {state}.",
            st["Body"],
        ),
        Paragraph(
            "A general contractor / construction supervisor / building credential typically "
            "authorizes oversight or general building contracting. It does <b>not</b> by itself "
            "prove authority to self-perform separately licensed trades (electrical, plumbing, "
            "HVAC, sheet metal, etc.) where those trades have their own boards.",
            st["Body"],
        ),
        Paragraph("Complete before promoting out of stub", st["H2"]),
        Paragraph(
            "1. Official scope definition for the construction credential (.gov)<br/>"
            "2. Official statement that specialty trades require separate licenses<br/>"
            "3. Electrical and plumbing (or mechanical) lookup URLs<br/>"
            "4. Reviewed date + suggested account-note language",
            st["Body"],
        ),
        Paragraph(
            "Pull candidate URLs from "
            "<font face='Courier' size='8'>service-provider-vetting-analyst/reference/"
            "contractor-licensing-us-states-territories.md</font> and "
            "<font face='Courier' size='8'>license-scope-appendices.md</font>.",
            st["Body"],
        ),
        Paragraph(
            f"<b>Draft language (verify):</b> A {state} general construction credential "
            "authorizes covered building oversight/contracting. Separately licensed trades "
            "remain under their boards. Holding the construction credential alone is not "
            "evidence the company may self-perform those trades without applicable trade and "
            "business licenses.",
            st["Body"],
        ),
    ]
    return story


def build_appendix_pdf(states: list[str]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.6 * inch,
    )
    st = _styles()
    story: list = [
        Paragraph("Appendix — License Scope Notes", st["H1"]),
        Paragraph(
            "State-specific notes on construction credentials vs self-perform licensed trades. "
            f"Generated {datetime.now().strftime('%Y-%m-%d')}.",
            st["Body"],
        ),
        HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=8),
    ]

    normalized = []
    for s in states:
        code = s.strip().upper()
        if code and code not in normalized:
            normalized.append(code)

    for i, code in enumerate(normalized):
        if i:
            story.append(Spacer(1, 12))
            story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=4, spaceAfter=8))
        if code == "MA":
            story.extend(_ma_section(st))
        else:
            story.extend(_stub_section(code, st))

    story.extend(
        [
            Spacer(1, 10),
            HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=6),
            Paragraph(
                "sp-account-review-pack · license-scope appendix",
                st["Footer"],
            ),
        ]
    )
    doc.build(story)
    return buf.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--states",
        required=True,
        help="Comma-separated state codes, e.g. MA or MA,TX,FL",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Output PDF path (default: ./license-scope-appendix.pdf)",
    )
    args = parser.parse_args()
    states = [s.strip() for s in args.states.split(",") if s.strip()]
    pdf = build_appendix_pdf(states)
    out = Path(args.out).expanduser() if args.out else Path("license-scope-appendix.pdf")
    out.write_bytes(pdf)
    print(f"Wrote {out.resolve()} ({len(pdf)} bytes)")


if __name__ == "__main__":
    main()
