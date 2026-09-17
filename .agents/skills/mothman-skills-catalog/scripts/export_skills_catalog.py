#!/usr/bin/env python3
"""Scan .agents/skills/*/SKILL.md and write a regenerable catalog PDF.

  python export_skills_catalog.py
  python export_skills_catalog.py --developed-only
  python export_skills_catalog.py --out path/to/catalog.pdf
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
PLANNED_CONFIG = Path(__file__).resolve().parents[1] / "planned-skills.json"
DEFAULT_PDF = Path.home() / "Downloads" / "Mothman Skills Catalog.pdf"
DESKTOP_PDF = Path.home() / "Desktop" / "Mothman Skills Catalog.pdf"
WORKSPACE_PDF = REPO_ROOT / ".tmp" / "mothman-skills-catalog" / "Mothman Skills Catalog.pdf"
SNAPSHOT_JSON = REPO_ROOT / ".tmp" / "mothman-skills-catalog" / "catalog.json"

GREEN = HexColor("#1B5E3B")
DARK = HexColor("#1A1A1A")
MUTED = HexColor("#555555")
LIGHT = HexColor("#F4F6F5")
LINE = HexColor("#C8D0CB")
HEADER_BG = HexColor("#1B5E3B")
WHITE = HexColor("#FFFFFF")

CRYSTAL_AUTHOR_RE = re.compile(
    r"gagner|crysgagner|\{\{employee_name\}\}",
    re.IGNORECASE,
)
META_FIELD_RE = re.compile(
    r"^(author|provenance|created_by):\s*(.+)$",
    re.MULTILINE | re.IGNORECASE,
)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
DESC_BLOCK_RE = re.compile(
    r"^description:\s*>-\s*\n((?:[ \t]+.+\n?)+)",
    re.MULTILINE,
)
DESC_INLINE_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


def _unescape(value: str) -> str:
    return value.strip().strip("'").strip('"').replace("\\n", " ").strip()


def parse_skill_md(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {
            "name": path.parent.name,
            "description": "(no frontmatter description)",
        }
    fm = match.group(1)
    name_m = NAME_RE.search(fm)
    name = _unescape(name_m.group(1)) if name_m else path.parent.name

    desc = ""
    block = DESC_BLOCK_RE.search(fm)
    if block:
        lines = [line.strip() for line in block.group(1).splitlines()]
        desc = " ".join(part for part in lines if part)
    else:
        inline = DESC_INLINE_RE.search(fm)
        if inline:
            desc = _unescape(inline.group(1))
            if desc in {">-", "|", ">"}:
                desc = ""

    desc = re.sub(r"\s+", " ", desc).strip()
    if not desc:
        desc = "(no description in SKILL.md)"
    return {"name": name, "description": desc}


def load_planned_config() -> dict:
    if not PLANNED_CONFIG.is_file():
        return {"extra": set(), "exclude": set()}
    data = json.loads(PLANNED_CONFIG.read_text(encoding="utf-8"))
    extra = {str(x).strip() for x in data.get("extra", []) if str(x).strip()}
    exclude = {str(x).strip() for x in data.get("exclude", []) if str(x).strip()}
    return {"extra": extra, "exclude": exclude}


def parse_metadata(folder: Path) -> dict[str, str]:
    meta_path = folder / "metadata.yaml"
    if not meta_path.is_file():
        return {}
    text = meta_path.read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    for match in META_FIELD_RE.finditer(text):
        fields[match.group(1).lower()] = _unescape(match.group(2))
    return fields


def is_planned_skill(folder_name: str, meta: dict[str, str], config: dict) -> bool:
    if folder_name in config["exclude"] or folder_name.startswith("_"):
        return False
    if folder_name in config["extra"]:
        return True
    if folder_name.startswith("mothman-"):
        return True
    provenance = (meta.get("provenance") or "").lower()
    if provenance == "mothman":
        return True
    for key in ("author", "created_by"):
        if CRYSTAL_AUTHOR_RE.search(meta.get(key) or ""):
            return True
    return False


def classify(folder_name: str, meta: dict[str, str], config: dict) -> str:
    if folder_name.startswith("bmad-"):
        return "inherited-bmad"
    if is_planned_skill(folder_name, meta, config):
        return "planned"
    return "other"


def load_skills() -> list[dict]:
    rows: list[dict] = []
    if not SKILLS_DIR.is_dir():
        raise SystemExit(f"Skills directory not found: {SKILLS_DIR}")

    config = load_planned_config()
    for child in sorted(SKILLS_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir() or child.name.startswith(".") or child.name.startswith("_"):
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        parsed = parse_skill_md(skill_md)
        meta = parse_metadata(child)
        origin = classify(child.name, meta, config)
        rows.append(
            {
                "folder": child.name,
                "name": parsed["name"],
                "description": parsed["description"],
                "origin": origin,
                "provenance": meta.get("provenance", ""),
                "author": meta.get("author") or meta.get("created_by", ""),
                "path": str(skill_md.relative_to(REPO_ROOT)).replace("\\", "/"),
            }
        )
    return rows


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=GREEN,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=22,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocSub",
            fontName="Helvetica",
            fontSize=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=8,
            leading=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHead",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=GREEN,
            spaceBefore=10,
            spaceAfter=6,
            leading=15,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Intro",
            fontName="Helvetica",
            fontSize=9,
            textColor=DARK,
            leading=12,
            spaceAfter=8,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CellName",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=DARK,
            leading=11,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CellDesc",
            fontName="Helvetica",
            fontSize=8,
            textColor=DARK,
            leading=11,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Th",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=WHITE,
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FooterNote",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=10,
        )
    )
    return styles


def skill_table(skills: list[dict], styles) -> Table:
    header = [
        Paragraph("Skill", styles["Th"]),
        Paragraph("Purpose", styles["Th"]),
    ]
    data = [header]
    for skill in skills:
        data.append(
            [
                Paragraph(xml_escape(skill["name"]), styles["CellName"]),
                Paragraph(xml_escape(skill["description"]), styles["CellDesc"]),
            ]
        )

    table = Table(data, colWidths=[1.7 * inch, 5.3 * inch], repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    table.setStyle(TableStyle(style_cmds))
    return table


def add_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        0.7 * inch,
        0.45 * inch,
        "Mothman skills catalog  ·  regenerate: python .agents/skills/mothman-skills-catalog/scripts/export_skills_catalog.py",
    )
    canvas.drawRightString(letter[0] - 0.7 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(skills: list[dict], out_path: Path, developed_only: bool) -> None:
    styles = build_styles()
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    planned = [s for s in skills if s["origin"] == "planned"]
    other = [s for s in skills if s["origin"] == "other"]
    bmad = [s for s in skills if s["origin"] == "inherited-bmad"]

    counts = f"{len(planned)} planned  ·  {len(other)} other workspace"
    if not developed_only:
        counts += f"  ·  {len(bmad)} BMAD inherited"

    planned_block = (
        skill_table(planned, styles)
        if planned
        else Paragraph(
            "No planned skills matched. Check planned-skills.json.",
            styles["Intro"],
        )
    )
    other_block = (
        skill_table(other, styles) if other else Paragraph("None.", styles["Intro"])
    )

    story = [
        Paragraph("Mothman Skills Catalog", styles["DocTitle"]),
        Paragraph(
            f"Crystal Gagner  ·  Vixxo  ·  generated {generated}  ·  {counts}",
            styles["DocSub"],
        ),
        HRFlowable(width="100%", thickness=1, color=GREEN, spaceAfter=10),
        Paragraph(
            "This PDF is rebuilt from top-level <font face='Courier'>.agents/skills/*/SKILL.md</font> "
            "frontmatter. Nested copies inside a skill folder are ignored. "
            "Re-run the export script whenever skills are added or descriptions change. "
            "Edit <font face='Courier'>planned-skills.json</font> to add or drop Crystal-planned skills.",
            styles["Intro"],
        ),
        Paragraph(f"Planned specifically ({len(planned)})", styles["SectionHead"]),
        Paragraph(
            "Skills Crystal planned and built for Mothman: morning/afternoon ops, "
            "SP inbound vetting, voicemail triage, Case mail sync, account review packs, "
            "travel rate cards, and related SPM workflows. This is the featured set — "
            "not the full installed catalog.",
            styles["Intro"],
        ),
        planned_block,
        Spacer(1, 14),
        Paragraph(f"Other workspace skills ({len(other)})", styles["SectionHead"]),
        Paragraph(
            "Installed or customized skills in this workspace that are not BMAD and "
            "were not Crystal-planned (Vixxo copilot catalog, other authors, template productivity).",
            styles["Intro"],
        ),
        other_block,
    ]

    if not developed_only and bmad:
        story.extend(
            [
                Spacer(1, 14),
                Paragraph(f"Inherited BMAD ({len(bmad)})", styles["SectionHead"]),
                Paragraph(
                    "Installed from the assistants-template BMAD set. Not authored as Mothman "
                    "custom skills; listed so the inventory stays complete.",
                    styles["Intro"],
                ),
                skill_table(bmad, styles),
            ]
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.7 * inch,
        title="Mothman Skills Catalog",
        author="Mothman for Crystal Gagner",
    )
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


def write_snapshot(skills: list[dict], pdf_path: Path) -> None:
    SNAPSHOT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "pdf": str(pdf_path),
        "copies": [str(DEFAULT_PDF), str(DESKTOP_PDF), str(WORKSPACE_PDF)],
        "counts": {
            "total": len(skills),
            "planned": sum(1 for s in skills if s["origin"] == "planned"),
            "other": sum(1 for s in skills if s["origin"] == "other"),
            "inherited_bmad": sum(1 for s in skills if s["origin"] == "inherited-bmad"),
        },
        "skills": skills,
    }
    SNAPSHOT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Mothman skills catalog PDF")
    parser.add_argument("--out", type=Path, default=DEFAULT_PDF, help="PDF output path")
    parser.add_argument(
        "--developed-only",
        action="store_true",
        help="Omit inherited BMAD skills from the PDF",
    )
    args = parser.parse_args()

    skills = load_skills()
    if not skills:
        raise SystemExit("No SKILL.md files found under .agents/skills/")

    build_pdf(skills, args.out, args.developed_only)
    copies = []
    for dest in (DESKTOP_PDF, WORKSPACE_PDF):
        if dest.resolve() == args.out.resolve():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.out, dest)
        copies.append(dest)
    write_snapshot(skills, args.out)

    planned = sum(1 for s in skills if s["origin"] == "planned")
    other = sum(1 for s in skills if s["origin"] == "other")
    bmad = sum(1 for s in skills if s["origin"] == "inherited-bmad")
    print(f"Wrote {args.out}")
    for copy in copies:
        print(f"Copy  {copy}")
    print(f"Snapshot {SNAPSHOT_JSON}")
    print(f"Planned: {planned}  Other: {other}  BMAD: {bmad}  Total: {len(skills)}")


if __name__ == "__main__":
    main()
