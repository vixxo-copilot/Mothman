#!/usr/bin/env python3
"""Perspective-correct sign measurements on a building facade plane.

Uses a known rectangular reference on the same wall plane (typically a door
opening) to compute a homography from image pixels to real inches on the
facade. Works on angled / non-straight-on photos when the reference
quadrilateral is on the same plane as the sign.

Requires opencv-python-headless.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Iterable

import cv2
import numpy as np


def parse_point(raw: str) -> tuple[float, float]:
    parts = raw.split(",")
    if len(parts) != 2:
        raise ValueError(f"Point must be x,y not {raw!r}")
    return float(parts[0]), float(parts[1])


def parse_quad(values: Iterable[str]) -> np.ndarray:
    pts = [parse_point(v) for v in values]
    if len(pts) != 4:
        raise ValueError("Quad requires exactly four x,y points (TL, TR, BR, BL)")
    return np.float32(pts)


def inches_from_feet(value: str) -> float:
    raw = value.strip().lower().replace("ft", "'").replace("'", "'")
    if raw.endswith("in"):
        return float(raw.replace("in", ""))
    if "'" in raw:
        feet, _, inches = raw.partition("'")
        return float(feet) * 12 + float(inches or 0)
    return float(value)


def fmt_inches(inches: float) -> str:
    feet = int(inches // 12)
    rem = inches % 12
    if feet:
        return f"{feet}'-{rem:.1f}\" ({inches:.1f}\")"
    return f'{inches:.1f}"'


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Path to site photo")
    parser.add_argument(
        "--door",
        nargs=4,
        metavar="X,Y",
        required=True,
        help="Door/opening corners TL TR BR BL in pixels",
    )
    parser.add_argument("--door-width", required=True, help="Opening width (e.g. 6', 72in)")
    parser.add_argument("--door-height", required=True, help="Opening height (e.g. 7', 84in)")
    parser.add_argument(
        "--sign",
        nargs=4,
        metavar="X,Y",
        required=True,
        help="Sign span corners: left-top, right-top, left-bottom, right-bottom",
    )
    parser.add_argument("--logo-top", help="Optional logo top center x,y")
    parser.add_argument("--logo-bottom", help="Optional logo bottom center x,y")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    door_px = parse_quad(args.door)
    door_w = inches_from_feet(args.door_width)
    door_h = inches_from_feet(args.door_height)
    door_world = np.float32([[0, 0], [door_w, 0], [door_w, door_h], [0, door_h]])

    H = cv2.getPerspectiveTransform(door_px, door_world)

    def to_world(pt: tuple[float, float]) -> tuple[float, float]:
        v = np.array([pt[0], pt[1], 1.0], dtype=np.float64)
        p = H @ v
        return float(p[0] / p[2]), float(p[1] / p[2])

    sign_pts = [parse_point(v) for v in args.sign]
    lt, rt, lb, rb = sign_pts
    w_lt, w_rt, w_lb, w_rb = map(to_world, sign_pts)

    payload = {
        "method": "facade_homography",
        "reference": {
            "width_in": door_w,
            "height_in": door_h,
            "recovered_width_in": round(dist(to_world(tuple(door_px[0])), to_world(tuple(door_px[1]))), 2),
            "recovered_height_in": round(dist(to_world(tuple(door_px[0])), to_world(tuple(door_px[3]))), 2),
        },
        "sign_overall_width_in": round(dist(w_lt, w_rt), 1),
        "letter_height_in": round((dist(w_lt, w_lb) + dist(w_rt, w_rb)) / 2, 1),
        "letter_height_left_in": round(dist(w_lt, w_lb), 1),
        "letter_height_right_in": round(dist(w_rt, w_rb), 1),
    }

    if args.logo_top and args.logo_bottom:
        logo_h = dist(to_world(parse_point(args.logo_top)), to_world(parse_point(args.logo_bottom)))
        payload["logo_height_in"] = round(logo_h, 1)

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print("Facade homography (perspective-corrected)")
    print(f"Reference opening: {fmt_inches(door_w)} x {fmt_inches(door_h)}")
    print(
        "Recovered opening:",
        fmt_inches(payload["reference"]["recovered_width_in"]),
        "x",
        fmt_inches(payload["reference"]["recovered_height_in"]),
    )
    print()
    print("Sign overall width:", fmt_inches(payload["sign_overall_width_in"]))
    print("Letter cap height:", fmt_inches(payload["letter_height_in"]))
    if "logo_height_in" in payload:
        print("Logo height:", fmt_inches(payload["logo_height_in"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
