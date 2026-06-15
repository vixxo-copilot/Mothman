from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from datetime import date
from pathlib import Path


DEFAULT_COVERAGE_CHANGE = Path("/Users/mclavijo/Downloads/FL HVACR Bid Analysis_for Claude.xlsx")
DEFAULT_SITES = Path("/Users/mclavijo/Downloads/output (3).csv")
DEFAULT_LOS_SD = Path(
    "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/"
    "LOS_SD_Export_of_Active_Accounts.xlsx"
)
DEFAULT_SIEBEL = Path(
    "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/"
    "5.19ActiveSiebelSPs.xlsm"
)
DEFAULT_COVERAGE_DIR = Path("/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def decode_site_export(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "latin-1"):
        try:
            text = data.decode(encoding)
            if "\x00" not in text[:1000]:
                return text
        except UnicodeDecodeError:
            continue
    return data.decode("utf-16", errors="ignore")


def sanitize_site_export(path: Path, output_dir: Path) -> tuple[Path, int]:
    text = decode_site_export(path)
    delimiter = "\t" if "\t" in text.splitlines()[0] else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    cleaned_path = output_dir / "HVACR_sites_cleaned.csv"
    removed = 0
    rows = []
    for row in reader:
        customer = str(row.get("Customer #") or "").strip()
        if customer.startswith("=") or " OR " in customer:
            removed += 1
            continue
        rows.append(row)
    with cleaned_path.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=reader.fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return cleaned_path, removed


def parse_args() -> argparse.Namespace:
    today = date.today().isoformat()
    parser = argparse.ArgumentParser(description="Build Florida HVACR CBSA coverage.")
    parser.add_argument("--coverage-change", type=Path, default=DEFAULT_COVERAGE_CHANGE)
    parser.add_argument("--sites", type=Path, default=DEFAULT_SITES)
    parser.add_argument("--los-sd", type=Path, default=DEFAULT_LOS_SD)
    parser.add_argument("--siebel", type=Path, default=DEFAULT_SIEBEL)
    parser.add_argument("--coverage-dir", type=Path, default=DEFAULT_COVERAGE_DIR)
    parser.add_argument("--existing-coverage", type=Path, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_COVERAGE_DIR / f"HVACR_CBSA_Coverage_{today}.xlsx",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_COVERAGE_DIR / f"HVACR_CBSA_Coverage_{today}_summary.md",
    )
    parser.add_argument(
        "--skip-site-sanitize",
        action="store_true",
        help="Use the site export as-is instead of excluding formula-like compound customer rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.coverage_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    site_path = args.sites
    removed_site_rows = 0
    if not args.skip_site_sanitize:
        site_path, removed_site_rows = sanitize_site_export(args.sites, args.coverage_dir)

    shared_builder = (
        repo_root()
        / ".cursor"
        / "skills"
        / "VIXXO-electrical-cbsa-coverage-builder"
        / "scripts"
        / "build_electrical_cbsa_coverage.py"
    )
    cmd = [
        sys.executable,
        str(shared_builder),
        "--area",
        "HVAC",
        "--use-work-history-los-sd",
        "--default-area-sd",
        "HVACR",
        "--coverage-change",
        str(args.coverage_change),
        "--sites",
        str(site_path),
        "--los-sd",
        str(args.los_sd),
        "--siebel",
        str(args.siebel),
        "--output",
        str(args.output),
        "--summary",
        str(args.summary),
    ]
    if args.existing_coverage:
        cmd.extend(["--existing-coverage", str(args.existing_coverage)])
    subprocess.run(cmd, check=True)

    if removed_site_rows:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n\n## HVACR Site Export Cleanup\n"
                f"- Excluded formula-like compound customer rows before build: {removed_site_rows:,}\n"
                f"- Cleaned site export: `{site_path}`\n"
            )


if __name__ == "__main__":
    main()
