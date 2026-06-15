from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path


DEFAULT_COVERAGE_CHANGE = Path(
    "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage/"
    "CO Handyman_RFP Analysis_V3 Remove small markets 05 11 2026_Final for Claude.xlsx"
)
DEFAULT_SITES = Path(
    "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/Coverage/"
    "mcd-electrical-site-export-output-2026-05-11.csv"
)
DEFAULT_LOS_SD = Path(
    "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/"
    "LOS_SD_Export_of_Active_Accounts.xlsx"
)
DEFAULT_SIEBEL = Path(
    "/Users/mclavijo/Library/CloudStorage/OneDrive-Vixxo/Desktop/MCD/SLX to VixxoLink/"
    "Active Siebel 5-7.xlsm"
)
DEFAULT_EXISTING_COVERAGE = Path("/Users/mclavijo/Downloads/OPS 10502 Customer SC Relationships.xlsx")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def parse_args() -> argparse.Namespace:
    today = date.today().isoformat()
    default_dir = repo_root() / ".tmp" / "mcd-handyman-coverage"
    parser = argparse.ArgumentParser(description="Build Colorado Handyman CBSA coverage.")
    parser.add_argument("--coverage-change", type=Path, default=DEFAULT_COVERAGE_CHANGE)
    parser.add_argument("--sites", type=Path, default=DEFAULT_SITES)
    parser.add_argument("--los-sd", type=Path, default=DEFAULT_LOS_SD)
    parser.add_argument("--siebel", type=Path, default=DEFAULT_SIEBEL)
    parser.add_argument("--existing-coverage", type=Path, default=DEFAULT_EXISTING_COVERAGE)
    parser.add_argument(
        "--output",
        type=Path,
        default=default_dir / f"mcd-handyman-cbsa-coverage-{today}.xlsx",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=default_dir / f"mcd-handyman-cbsa-coverage-{today}-summary.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

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
        "Handyman",
        "--use-work-history-los-sd",
        "--default-area-sd",
        "ALL",
        "--coverage-change",
        str(args.coverage_change),
        "--sites",
        str(args.sites),
        "--los-sd",
        str(args.los_sd),
        "--siebel",
        str(args.siebel),
        "--existing-coverage",
        str(args.existing_coverage),
        "--output",
        str(args.output),
        "--summary",
        str(args.summary),
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
