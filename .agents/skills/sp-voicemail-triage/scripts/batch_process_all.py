#!/usr/bin/env python3
"""Run sp-voicemail-triage batch intake (Outlook ext 4046; optional Freshdesk)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR.parent / ".tmp" / "batch-run"


def run_script(name: str, extra_args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(SCRIPT_DIR / name), *extra_args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def main() -> int:
    argv = sys.argv[1:]
    dry_run = "--dry-run" in argv
    include_freshdesk = "--freshdesk" in argv
    since_last_batch = "--since-last-batch" in argv

    passthrough = [a for a in argv if a not in {"--freshdesk"}]
    exit_code = 0
    sections: dict[str, object] = {}

    print(f"# SP Voicemail batch — combined — {datetime.now(timezone.utc).date()}")
    print()
    print("## Outlook — extension 4046 (primary)")
    outlook_code, outlook_out = run_script("batch_process_outlook.py", passthrough)
    print(outlook_out)
    sections["outlook"] = {"exit_code": outlook_code, "output": outlook_out}
    if outlook_code != 0:
        exit_code = outlook_code

    if include_freshdesk:
        print()
        print("## Freshdesk — KSOnboarding (legacy, optional)")
        fd_code, fd_out = run_script("batch_process_freshdesk.py", passthrough)
        print(fd_out)
        sections["freshdesk"] = {"exit_code": fd_code, "output": fd_out}
        if fd_code != 0 and exit_code == 0:
            exit_code = fd_code
    else:
        sections["freshdesk"] = {"skipped": True, "reason": "pass --freshdesk to include KSOnboarding queue"}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = OUT_DIR / f"batch-all-{ts}.json"
    payload = {
        "generated_at": ts,
        "dry_run": dry_run,
        "since_last_batch": since_last_batch,
        "include_freshdesk": include_freshdesk,
        "sections": sections,
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest = OUT_DIR / "batch-all-latest.json"
    latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print()
    print(f"**Combined report:** {summary_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
