#!/usr/bin/env python3
"""Batch sp-voicemail-triage-fast — transcription + routing, no external vetting."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PARENT_SCRIPTS = Path(__file__).resolve().parents[2] / "sp-voicemail-triage" / "scripts"
sys.path.insert(0, str(PARENT_SCRIPTS))

from batch_process_freshdesk import main  # noqa: E402


def _preflight() -> int:
    if "--skip-preflight" in sys.argv:
        return 0
    verify = PARENT_SCRIPTS / "verify_transcription.py"
    proc = subprocess.run(
        [sys.executable, str(verify)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout or "")
        sys.stderr.write(proc.stderr or "")
        sys.stderr.write(
            "Preflight failed. Run: python "
            ".agents/skills/sp-voicemail-triage/scripts/setup_transcription.py\n"
        )
        return proc.returncode
    return 0


if __name__ == "__main__":
    if "--skip-vetting" not in sys.argv:
        sys.argv.append("--skip-vetting")
    code = _preflight()
    if code != 0:
        raise SystemExit(code)
    raise SystemExit(main())
