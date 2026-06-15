#!/usr/bin/env python3
"""Measure fascia panel sign mockups from photos and emit dimension overlays."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: pip install pillow") from exc

import numpy as np


def inches_from_feet(value: str) -> float:
    raw = value.strip().lower().replace("inches", "in").replace("inch", "in")
    raw = raw.replace("feet", "'").replace("foot", "'").replace("ft", "'")
    raw = raw.replace('"', "in").replace(" ", "")

    feet_inches = re.fullmatch(r"(?P<feet>\d+(?:\.\d+)?)'(?:-?(?P<inches>\d+(?:\.\d+)?)in)?", raw)
    if feet_inches:
        feet = float(feet_inches.group("feet"))
        inches = float(feet_inches.group("inches") or 0)
        return feet * 12 + inches

    inches_only = re.fullmatch(r"(?P<inches>\d+(?:\.\d+)?)in?", raw)
    if inches_only:
        return float(inches_only.group("inches"))

    return float(value)


def fmt_dim(inches: float) -> str:
    inches = round(inches * 2) / 2
    feet = int(inches // 12)
    rem = inches % 12
    whole = int(rem)
    half = abs(rem - whole - 0.5) < 0.01
    if feet:
        if half:
            return f"{feet}'-{whole}\u00bd\""
        return f"{feet}'-{whole}\"" if whole else f"{feet}'-0\""
    return f'{whole}\u00bd"' if half else f'{whole}"'


@dataclass
class PanelBounds:
    top: int
    bot: int
    left: int
    right: int

    @property
    def height_px(self) -> int:
        return self.bot - self.top + 1

    @property
    def width_px(self) -> int:
        return self.right - self.left + 1


@dataclass
class ElementBox:
    name: str
    x0: int
    x1: int
    y0: int
    y1: int

    @property
    def height_px(self) -> int:
        return self.y1 - self.y0

    @property
    def width_px(self) -> int:
        return self.x1 - self.x0


def detect_panel(arr: np.ndarray) -> PanelBounds:
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    white = (r > 220) & (g > 230) & (b > 240)
    white[: int(arr.shape[0] * 0.15), :] = False
    white[int(arr.shape[0] * 0.45) :, :] = False
    white[:, : int(arr.shape[1] * 0.15)] = False
    white[:, int(arr.shape[1] * 0.75) :] = False

    ys, xs = np.where(white)
    if len(xs) < 500:
        raise ValueError("Could not detect white panel mockup in photo")

    return PanelBounds(ys.min(), ys.max(), xs.min(), xs.max())


def collect_ink(arr: np.ndarray, panel: PanelBounds) -> tuple[np.ndarray, np.ndarray]:
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    in_panel = np.zeros(arr.shape[:2], bool)
    in_panel[panel.top : panel.bot + 1, panel.left : panel.right + 1] = True
    white = (r > 220) & (g > 230) & (b > 240)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    ink = in_panel & (~white) & (lum < 200)
    brand = ink & (r < 50) & (g > 60) & (b > 50) & (g > r + 40)
    return np.column_stack(np.where(ink)), np.column_stack(np.where(brand))


def split_lines(ink_pts: np.ndarray, panel: PanelBounds) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    rows: dict[int, int] = {}
    for y, _ in ink_pts:
        rows[y] = rows.get(y, 0) + 1
    active = sorted(rows)
    gaps = [(active[i], active[i + 1], active[i + 1] - active[i]) for i in range(len(active) - 1) if active[i + 1] - active[i] >= 3]
    if not gaps:
        mid = (panel.top + panel.bot) // 2
        return ink_pts[ink_pts[:, 0] <= mid], ink_pts[ink_pts[:, 0] > mid], (mid, mid + 1)

    y_start = panel.top + int(panel.height_px * 0.35)
    y_end = panel.top + int(panel.height_px * 0.70)
    candidates = [g for g in gaps if y_start <= g[0] <= y_end]
    gap = max(candidates or gaps, key=lambda g: g[2])
    top = ink_pts[ink_pts[:, 0] <= gap[0]]
    bot = ink_pts[ink_pts[:, 0] >= gap[1]]
    return top, bot, (gap[0], gap[1])


def x_runs(pts: np.ndarray, x_min: int, x_max: int, min_width: int = 4) -> list[tuple[int, int]]:
    occ = np.zeros(x_max + 1, int)
    for _, x in pts:
        occ[x] += 1
    runs: list[tuple[int, int]] = []
    i = x_min
    while i <= x_max:
        if occ[i] > 0:
            j = i
            while j <= x_max and occ[j] > 0:
                j += 1
            if j - i >= min_width:
                runs.append((i, j - 1))
            i = j
        else:
            i += 1
    return runs


def split_elements(
    line1: np.ndarray,
    line2: np.ndarray,
    brand1: np.ndarray,
    panel: PanelBounds,
) -> list[ElementBox]:
    elements: list[ElementBox] = []

    if len(brand1):
        logo_runs = x_runs(brand1, panel.left, panel.right, min_width=8)
        if logo_runs:
            lr = logo_runs[0]
            logo = brand1[(brand1[:, 1] >= lr[0]) & (brand1[:, 1] <= lr[1])]
            if len(logo):
                elements.append(
                    ElementBox("Logo", logo[:, 1].min(), logo[:, 1].max(), logo[:, 0].min(), logo[:, 0].max())
                )
            select = brand1[brand1[:, 1] > lr[1] + 6]
        else:
            select = brand1
    else:
        select = np.empty((0, 2), int)

    if len(select):
        elements.append(
            ElementBox(
                "Primary line (top)",
                select[:, 1].min(),
                select[:, 1].max(),
                select[:, 0].min(),
                select[:, 0].max(),
            )
        )
        split_x = select[:, 1].max() + 10
    elif len(line1):
        split_x = line1[:, 1].min() + int((line1[:, 1].max() - line1[:, 1].min()) * 0.55)
    else:
        split_x = panel.left

    tag_top = line1[line1[:, 1] > split_x] if len(line1) else np.empty((0, 2), int)
    if len(tag_top):
        elements.append(
            ElementBox(
                "Tagline (top)",
                tag_top[:, 1].min(),
                tag_top[:, 1].max(),
                tag_top[:, 0].min(),
                tag_top[:, 0].max(),
            )
        )

    if len(line2):
        runs = x_runs(line2, line2[:, 1].min(), line2[:, 1].max(), min_width=8)
        if len(runs) >= 2:
            xgaps = [(runs[i][1], runs[i + 1][0], runs[i + 1][0] - runs[i][1]) for i in range(len(runs) - 1)]
            mx = max(xgaps, key=lambda g: g[2])
            split = mx[0] + mx[2] // 2
            left = line2[line2[:, 1] <= split]
            right = line2[line2[:, 1] > split + 4]
        else:
            split = line2[:, 1].min() + int((line2[:, 1].max() - line2[:, 1].min()) * 0.42)
            left = line2[line2[:, 1] <= split]
            right = line2[line2[:, 1] > split + 4]

        if len(left):
            elements.append(
                ElementBox(
                    "Primary line (bottom)",
                    left[:, 1].min(),
                    left[:, 1].max(),
                    left[:, 0].min(),
                    left[:, 0].max(),
                )
            )
        if len(right):
            elements.append(
                ElementBox(
                    "Tagline (bottom)",
                    right[:, 1].min(),
                    right[:, 1].max(),
                    right[:, 0].min(),
                    right[:, 0].max(),
                )
            )

    return elements


def draw_overlay(
    img: Image.Image,
    panel: PanelBounds,
    elements: list[ElementBox],
    panel_w_in: float,
    panel_h_in: float,
    ppi_h: float,
    ppi_w: float,
    highlight: str | None,
) -> Image.Image:
    out = img.copy()
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    red = (220, 20, 20)

    draw.rectangle([panel.left, panel.top, panel.right, panel.bot], outline=red, width=2)

    def hdim(x0: int, x1: int, y: int, label: str) -> None:
        y2 = y + 8
        draw.line([(x0, y), (x1, y)], fill=red, width=2)
        for x in (x0, x1):
            draw.line([(x, y), (x, y2)], fill=red, width=2)
        tw, th = draw.textbbox((0, 0), label, font=font)[2:]
        tx = (x0 + x1 - tw) // 2
        draw.rectangle([tx - 2, y2 - th - 3, tx + tw + 2, y2 + 1], fill=(255, 255, 255))
        draw.text((tx, y2 - th - 1), label, fill=red, font=font)

    def vdim(x: int, y0: int, y1: int, label: str) -> None:
        x2 = x + 8
        draw.line([(x, y0), (x, y1)], fill=red, width=2)
        for y in (y0, y1):
            draw.line([(x, y), (x2, y)], fill=red, width=2)
        tw, th = draw.textbbox((0, 0), label, font=font)[2:]
        draw.rectangle([x2 + 2, (y0 + y1 - th) // 2 - 2, x2 + tw + 6, (y0 + y1 + th) // 2 + 2], fill=(255, 255, 255))
        draw.text((x2 + 4, (y0 + y1 - th) // 2), label, fill=red, font=font)

    hdim(panel.left, panel.right, panel.bot + 6, fmt_dim(panel_w_in))
    vdim(panel.right + 6, panel.top, panel.bot, fmt_dim(panel_h_in))

    for el in elements:
        if highlight and el.name != highlight:
            continue
        if el.height_px <= 0:
            continue
        vdim(el.x1 + 4, el.y0, el.y1, fmt_dim(el.height_px / ppi_h))

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--panel-height", required=True, help='Panel height anchor, e.g. 4\'-3"')
    parser.add_argument("--panel-width", required=True, help='Panel width anchor, e.g. 10\'-0"')
    parser.add_argument("--out-png", default="tmp/sign-dimensions.png")
    parser.add_argument("--out-pdf")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    img = Image.open(args.image).convert("RGB")
    arr = np.array(img)
    panel = detect_panel(arr)
    ink_pts, brand_pts = collect_ink(arr, panel)
    brand1 = brand_pts[(brand_pts[:, 0] >= panel.top) & (brand_pts[:, 0] <= panel.bot)]
    line1, line2, gap = split_lines(ink_pts, panel)
    elements = split_elements(line1, line2, brand1, panel)

    panel_h_in = inches_from_feet(args.panel_height)
    panel_w_in = inches_from_feet(args.panel_width)
    ppi_v = panel.height_px / panel_h_in
    ppi_h = panel.width_px / panel_w_in

    rows = [
        {
            "element": "Panel (overall)",
            "height": fmt_dim(panel_h_in),
            "width": fmt_dim(panel_w_in),
        }
    ]
    for el in elements:
        rows.append(
            {
                "element": el.name,
                "height": fmt_dim(el.height_px / ppi_v),
                "width": fmt_dim(el.width_px / ppi_h),
            }
        )
    rows.append({"element": "Line-to-line gap", "height": fmt_dim((gap[1] - gap[0]) / ppi_v), "width": "—"})

    os.makedirs(os.path.dirname(args.out_png) or ".", exist_ok=True)
    overlay = draw_overlay(img, panel, elements, panel_w_in, panel_h_in, ppi_v, ppi_h, None)
    overlay.save(args.out_png)
    if args.out_pdf:
        os.makedirs(os.path.dirname(args.out_pdf) or ".", exist_ok=True)
        overlay.save(args.out_pdf, "PDF")

    if args.json:
        print(json.dumps({"panel_px": [panel.width_px, panel.height_px], "rows": rows}, indent=2))
    else:
        print(f"Scale: panel {fmt_dim(panel_w_in)} W x {fmt_dim(panel_h_in)} H\n")
        for row in rows:
            print(f"{row['element']:22} H {row['height']:>8}  W {row['width']:>8}")
        print(f"\nSaved {args.out_png}")
        if args.out_pdf:
            print(f"Saved {args.out_pdf}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
