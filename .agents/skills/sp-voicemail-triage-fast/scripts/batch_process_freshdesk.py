#!/usr/bin/env python3
"""Batch sp-voicemail-triage-fast — transcription + routing, no external vetting."""

from __future__ import annotations

import sys
from pathlib import Path

PARENT_SCRIPTS = Path(__file__).resolve().parents[2] / "sp-voicemail-triage" / "scripts"
sys.path.insert(0, str(PARENT_SCRIPTS))

from batch_process_freshdesk import main  # noqa: E402


if __name__ == "__main__":
    if "--skip-vetting" not in sys.argv:
        sys.argv.append("--skip-vetting")
    raise SystemExit(main())
