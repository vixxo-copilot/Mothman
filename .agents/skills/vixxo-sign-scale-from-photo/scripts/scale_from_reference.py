#!/usr/bin/env python3
"""Scale sign dimensions from pixel measurements using a known reference size."""

from __future__ import annotations

import argparse
import json
import re
import sys


def inches_from_feet(value: str) -> float:
    """Parse feet/inches strings like 7, 7', 7ft, 7'-6\", 84\", 84in."""
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
    feet = int(inches // 12)
    rem = inches % 12
    if feet:
        return f"{feet}'-{rem:.1f}\" ({inches:.1f}\")"
    return f'{inches:.1f}"'


def parse_target(raw: str) -> tuple[str, float]:
    if ":" not in raw:
        raise ValueError(f"Target must be name:pixels, got {raw!r}")
    name, pixels = raw.split(":", 1)
    name = name.strip()
    pixels = float(pixels.strip())
    if not name:
        raise ValueError(f"Target name missing in {raw!r}")
    if pixels <= 0:
        raise ValueError(f"Target pixels must be positive in {raw!r}")
    return name, pixels


def scale_dimension(ref_pixels: float, ref_inches: float, target_pixels: float) -> float:
    if ref_pixels <= 0:
        raise ValueError("ref_pixels must be positive")
    if ref_inches <= 0:
        raise ValueError("ref_inches must be positive")
    return target_pixels * (ref_inches / ref_pixels)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scale real-world sign dimensions from pixel measurements."
    )
    parser.add_argument("--ref-pixels", type=float, required=True, help="Reference length in pixels")
    parser.add_argument(
        "--ref-size",
        required=True,
        help="Known reference size (examples: 7, 7', 84\", 6'-8\")",
    )
    parser.add_argument(
        "--target",
        action="append",
        required=True,
        help="Dimension to scale as name:pixels (repeatable)",
    )
    parser.add_argument(
        "--tolerance-pct",
        type=float,
        default=8.0,
        help="Symmetric uncertainty band in percent (default 8)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    ref_inches = inches_from_feet(args.ref_size)
    targets = [parse_target(item) for item in args.target]

    results = []
    for name, pixels in targets:
        inches = scale_dimension(args.ref_pixels, ref_inches, pixels)
        tol = inches * (args.tolerance_pct / 100.0)
        results.append(
            {
                "name": name,
                "pixels": pixels,
                "inches": round(inches, 1),
                "feet_inches": fmt_dim(inches),
                "low_inches": round(inches - tol, 1),
                "high_inches": round(inches + tol, 1),
            }
        )

    payload = {
        "reference": {
            "pixels": args.ref_pixels,
            "inches": ref_inches,
            "size_input": args.ref_size,
        },
        "tolerance_pct": args.tolerance_pct,
        "targets": results,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Reference: {args.ref_pixels:.1f} px = {fmt_dim(ref_inches)}")
    print(f"Tolerance: +/- {args.tolerance_pct:.1f}%")
    print()
    for row in results:
        print(f"{row['name']}")
        print(f"  measured: {row['pixels']:.1f} px")
        print(f"  scaled:   {row['feet_inches']}")
        print(
            f"  range:    {fmt_dim(row['low_inches'])} to {fmt_dim(row['high_inches'])}"
        )
        print()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
