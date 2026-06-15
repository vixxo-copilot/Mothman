#!/usr/bin/env python3
"""Render a Vixxo project history brief into the combined PDF deliverable.

The renderer consumes a JSON manifest with absolute paths for the markdown
brief, output PDF, optional latest-artwork PDF, and optional completion photos.
It writes a single PDF in the canonical order:

1. Section A: markdown history brief rendered to PDF.
2. Section B: latest artwork PDF appended verbatim.
3. Section C: completion photo thumbnails, four per page.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image as PilImage
from PIL import ImageOps
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DEFAULT_SECTION_A_HEADER = (
    "Section A - Project history brief (from markdown). "
    "Section B: latest artwork PDF. "
    "Section C: completion photo thumbnails (4 per page)."
)


def _die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        _die(f"Could not read manifest {path}: {exc}")
    except json.JSONDecodeError as exc:
        _die(f"Could not parse manifest {path}: {exc}")
    if not isinstance(data, dict):
        _die("Manifest root must be a JSON object.")
    return data


def _manifest_path(data: dict[str, Any], key: str, *, required: bool = False) -> Path | None:
    value = data.get(key)
    if value in (None, ""):
        if required:
            _die(f"Manifest is missing required key: {key}")
        return None
    path = Path(str(value)).expanduser()
    if required and not path.exists():
        _die(f"Manifest path for {key} does not exist: {path}")
    return path


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "banner": ParagraphStyle(
            "Banner",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=18,
            leading=22,
            spaceBefore=6,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontSize=9,
            leading=12,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontSize=9,
            leading=12,
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            leftIndent=8,
            backColor=colors.whitesmoke,
            spaceAfter=5,
        ),
        "table": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontSize=8,
            leading=9,
            alignment=TA_LEFT,
        ),
        "label": ParagraphStyle(
            "PhotoLabel",
            parent=base["BodyText"],
            fontSize=7,
            leading=9,
            alignment=TA_LEFT,
        ),
    }


def _inline_markdown(text: str) -> str:
    escaped = html.escape(text)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = match.group(2)
        return f'<a href="{href}"><font color="#0563C1"><u>{label}</u></font></a>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', escaped)
    return escaped


def _split_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def _is_table_separator(line: str) -> bool:
    cells = _split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _consume_table(lines: list[str], start: int, styles: dict[str, ParagraphStyle]) -> tuple[Table, int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].lstrip().startswith("|"):
        if not _is_table_separator(lines[index]):
            rows.append(_split_table_row(lines[index]))
        index += 1
    width = max(len(row) for row in rows) if rows else 1
    normalized = [row + [""] * (width - len(row)) for row in rows]
    data = [
        [Paragraph(_inline_markdown(cell), styles["table"]) for cell in row]
        for row in normalized
    ]
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table, index


def _markdown_story(markdown_path: Path, header: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    story: list[Any] = [Paragraph(_inline_markdown(header), styles["banner"])]
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(_inline_markdown(" ".join(paragraph)), styles["body"]))
            paragraph.clear()

    def flush_code() -> None:
        if code_lines:
            escaped = "<br/>".join(html.escape(line) for line in code_lines)
            story.append(Paragraph(escaped, styles["code"]))
            code_lines.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not stripped:
            flush_paragraph()
            story.append(Spacer(1, 4))
            index += 1
            continue
        if line.lstrip().startswith("|"):
            flush_paragraph()
            table, index = _consume_table(lines, index, styles)
            story.append(table)
            story.append(Spacer(1, 6))
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            story.append(Paragraph(_inline_markdown(heading.group(2)), styles[f"h{level}"]))
            index += 1
            continue
        bullet = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            indent = min(len(bullet.group(1)), 8)
            style = ParagraphStyle(
                f"Bullet{index}",
                parent=styles["bullet"],
                leftIndent=14 + indent * 3,
                firstLineIndent=-8,
            )
            story.append(Paragraph(f"&bull; {_inline_markdown(bullet.group(2))}", style))
            index += 1
            continue
        paragraph.append(stripped)
        index += 1
    flush_paragraph()
    flush_code()
    return story


def _build_section_a(markdown_path: Path, header: str, temp_dir: Path) -> Path:
    out_path = temp_dir / "section_a.pdf"
    styles = _styles()
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    doc.build(_markdown_story(markdown_path, header, styles))
    return out_path


def _photo_flowable(photo_path: Path, max_width: float, max_height: float, temp_dir: Path) -> list[Any]:
    styles = _styles()
    with PilImage.open(photo_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((int(max_width * 2), int(max_height * 2)))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        converted = temp_dir / f"photo_{abs(hash(str(photo_path)))}.jpg"
        image.save(converted, "JPEG", quality=85)
        width, height = image.size
    scale = min(max_width / width, max_height / height, 1.0)
    rendered = Image(str(converted), width=width * scale, height=height * scale)
    label = Paragraph(html.escape(photo_path.name), styles["label"])
    return [rendered, Spacer(1, 4), label]


def _build_photo_section(photo_paths: list[Path], temp_dir: Path) -> Path | None:
    if not photo_paths:
        return None
    out_path = temp_dir / "section_c_photos.pdf"
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    cell_width = (letter[0] - inch) / 2
    cell_height = (letter[1] - inch - 0.2 * inch) / 2
    max_image_width = cell_width - 0.15 * inch
    max_image_height = cell_height - 0.35 * inch
    story: list[Any] = []
    for start in range(0, len(photo_paths), 4):
        batch = photo_paths[start : start + 4]
        cells = [
            _photo_flowable(path, max_image_width, max_image_height, temp_dir)
            for path in batch
        ]
        while len(cells) < 4:
            cells.append([Spacer(1, 1)])
        table = Table(
            [cells[:2], cells[2:]],
            colWidths=[cell_width, cell_width],
            rowHeights=[cell_height, cell_height],
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        if story:
            story.append(PageBreak())
        story.append(table)
    doc.build(story)
    return out_path


def _append_pdf(writer: PdfWriter, path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    reader = PdfReader(str(path))
    count = len(reader.pages)
    for page in reader.pages:
        writer.add_page(page)
    return count


def render(manifest_path: Path) -> dict[str, Any]:
    manifest = _read_manifest(manifest_path)
    markdown_path = _manifest_path(manifest, "markdown", required=True)
    output_path = _manifest_path(manifest, "output", required=False)
    if output_path is None:
        _die("Manifest is missing required key: output")
    artwork_pdf = _manifest_path(manifest, "artwork_pdf", required=False)
    if artwork_pdf is not None and not artwork_pdf.exists():
        artwork_pdf = None
    photos = [
        Path(str(path)).expanduser()
        for path in (manifest.get("completion_photos") or [])
        if Path(str(path)).expanduser().exists()
    ]
    section_a_header = manifest.get("section_a_header") or DEFAULT_SECTION_A_HEADER

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vixxo_history_pdf_") as temp_name:
        temp_dir = Path(temp_name)
        section_a_pdf = _build_section_a(markdown_path, str(section_a_header), temp_dir)
        section_c_pdf = _build_photo_section(photos, temp_dir)
        writer = PdfWriter()
        page_counts = {
            "section_a": _append_pdf(writer, section_a_pdf),
            "artwork": _append_pdf(writer, artwork_pdf),
            "section_c": _append_pdf(writer, section_c_pdf),
        }
        page_counts["total"] = sum(page_counts.values())
        with output_path.open("wb") as handle:
            writer.write(handle)

    return {
        "output": str(output_path),
        "page_counts": page_counts,
        "inputs": {
            "markdown": str(markdown_path),
            "artwork_pdf": str(artwork_pdf) if artwork_pdf else None,
            "completion_photos": [str(path) for path in photos],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(render(args.manifest), ensure_ascii=False))


if __name__ == "__main__":
    main()
