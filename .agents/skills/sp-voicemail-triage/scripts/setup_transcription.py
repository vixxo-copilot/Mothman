#!/usr/bin/env python3
"""One-time bootstrap for voicemail transcription (automation + local runs)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REQ = SCRIPTS / "requirements.txt"
VERIFY = SCRIPTS / "verify_transcription.py"


def main() -> int:
    print("Installing faster-whisper dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REQ)],
    )
    print("Verifying transcription stack and preloading model...")
    subprocess.check_call(
        [sys.executable, str(VERIFY), "--load-model"],
    )
    print("Transcription setup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
