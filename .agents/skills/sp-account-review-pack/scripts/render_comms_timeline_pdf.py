#!/usr/bin/env python3
"""Render a communications timeline PDF from a JSON payload.

JSON schema (example):
{
  "title": "Ezzi Property Group — Email Communication Timeline",
  "subtitle": "Source: Outlook… SP#: KS69888",
  "access_note": "Optional HTML/plaintext note",
  "threads": [
    {
      "title": "Thread 1 — …",
      "people": "Subject / people line",
      "events": [
        {"date": "Mon Aug 10, 2026", "who": "Crystal → Maria", "text": "…"}
      ]
    }
  ],
  "takeaways": ["…"],
  "images": [
    {"path": "C:/…/phone.png", "caption": "Figure A — Office calls"}
  ]
}
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

GREEN = HexColor("#1B5E3B")
DARK = HexColor("#1A1A1A")
MUTED = HexColor("#555555")
LIGHT = HexColor("#F4F6F5")
LINE = HexColor("#C8D0CB")


def _styles():
    s = getSampleStyleSheet()
    s.add(
        ParagraphStyle(
            name="DocTitle",
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=GREEN,
            spaceAfter=4,
            leading=18,
        )
    )
    s.add(
        ParagraphStyle(
            name="DocSub",
            fontName="Helvetica",
            fontSize=9,
            textColor=MUTED,
            spaceAfter=10,
            leading=12,
        )
    )
    s.add(
        ParagraphStyle(
            name="SectionHead",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=GREEN,
            spaceBefore=12,
            spaceAfter=6,
            leading=14,
        )
    )
    s.add(
        ParagraphStyle(
            name="BodyText2",
            fontName="Helvetica",
            fontSize=9,
            textColor=DARK,
            leading=12,
            spaceAfter=4,
        )
    )
    s.add(
        ParagraphStyle(
            name="Meta",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=10,
            spaceAfter=4,
        )
    )
    s.add(
        ParagraphStyle(
            name="EventDate",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=GREEN,
            leading=11,
        )
    )
    s.add(
        ParagraphStyle(
            name="EventBody",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=DARK,
            leading=11,
        )
    )
    s.add(
        ParagraphStyle(
            name="EventWho",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=MUTED,
            leading=10,
        )
    )
    s.add(
        ParagraphStyle(
            name="BulletItem",
            fontName="Helvetica",
            fontSize=9,
            textColor=DARK,
            leading=12,
            leftIndent=10,
            spaceAfter=2,
        )
    )
    s.add(
        ParagraphStyle(
            name="Caption",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=MUTED,
            leading=10,
            spaceAfter=8,
            alignment=TA_CENTER,
        )
    )
    s.add(
        ParagraphStyle(
            name="FooterNote",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=MUTED,
            leading=9,
            alignment=TA_CENTER,
        )
    )
    return s


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _add_thread(story, styles, thread: dict) -> None:
    story.append(Paragraph(_esc(thread.get("title", "Thread")), styles["SectionHead"]))
    people = thread.get("people") or ""
    if people:
        story.append(Paragraph(_esc(people), styles["Meta"]))
    data = []
    for ev in thread.get("events") or []:
        data.append(
            [
                Paragraph(_esc(ev.get("date", "")), styles["EventDate"]),
                [
                    Paragraph(_esc(ev.get("text", "")), styles["EventBody"]),
                    Paragraph(_esc(ev.get("who", "")), styles["EventWho"]),
                ],
            ]
        )
    if not data:
        return
    table = Table(data, colWidths=[1.25 * inch, 5.75 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)


def _scaled_image(path: Path, max_w: float, max_h: float) -> Image:
    img = Image(str(path))
    scale = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth = img.imageWidth * scale
    img.drawHeight = img.imageHeight * scale
    img.hAlign = "CENTER"
    return img


def render(payload: dict, out: Path) -> None:
    styles = _styles()
    doc = SimpleDocTemplate(
        str(out),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    story = []
    title = payload.get("title") or "Communication Timeline"
    subtitle = payload.get("subtitle") or (
        f"Compiled {datetime.now().strftime('%B %d, %Y')}"
    )
    story.append(Paragraph(_esc(title), styles["DocTitle"]))
    story.append(Paragraph(_esc(subtitle), styles["DocSub"]))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN, spaceAfter=8))

    if payload.get("access_note"):
        story.append(Paragraph("Access note", styles["SectionHead"]))
        story.append(Paragraph(_esc(payload["access_note"]), styles["BodyText2"]))

    for thread in payload.get("threads") or []:
        _add_thread(story, styles, thread)

    takeaways = payload.get("takeaways") or []
    if takeaways:
        story.append(Paragraph("Key takeaways", styles["SectionHead"]))
        for item in takeaways:
            story.append(Paragraph(f"• {_esc(item)}", styles["BulletItem"]))

    images = payload.get("images") or []
    if images:
        story.append(PageBreak())
        story.append(Paragraph("Appendix — Screenshots", styles["SectionHead"]))
        for image in images:
            path = Path(image.get("path", "")).expanduser()
            if not path.exists():
                continue
            if image.get("label"):
                story.append(Paragraph(_esc(image["label"]), styles["BodyText2"]))
            story.append(_scaled_image(path, 4.8 * inch, 6.5 * inch))
            if image.get("caption"):
                story.append(Paragraph(_esc(image["caption"]), styles["Caption"]))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=6))
    story.append(
        Paragraph(
            "sp-account-review-pack · communications timeline",
            styles["FooterNote"],
        )
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", required=True, help="Path to timeline JSON")
    parser.add_argument("--out", required=True, help="Output PDF path")
    args = parser.parse_args()
    payload = json.loads(Path(args.json).expanduser().read_text(encoding="utf-8"))
    out = Path(args.out).expanduser()
    render(payload, out)
    print(f"Wrote {out.resolve()} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
