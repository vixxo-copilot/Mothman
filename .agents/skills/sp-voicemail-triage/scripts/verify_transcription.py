#!/usr/bin/env python3
"""Verify faster-whisper and ffmpeg are ready for voicemail transcription."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe_voicemail import _audio_backend_ready, get_whisper_model, whisper_settings  # noqa: E402


def _pyav_available() -> bool:
    try:
        import av  # noqa: F401

        return True
    except ImportError:
        return False


def main() -> int:
    issues: list[str] = []
    if not _audio_backend_ready():
        issues.append(
            "No audio decoder — install ffmpeg on PATH or pip install faster-whisper (PyAV)"
        )

    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError:
        issues.append(
            "faster-whisper not installed — run: pip install -r "
            ".agents/skills/sp-voicemail-triage/scripts/requirements.txt"
        )

    if issues:
        print(json.dumps({"ok": False, "issues": issues}, indent=2))
        return 1

    model_size, device, compute_type = whisper_settings()
    load_model = "--load-model" in sys.argv
    result: dict = {
        "ok": True,
        "engine": "faster-whisper",
        "whisper_model": model_size,
        "whisper_device": device,
        "whisper_compute_type": compute_type,
        "ffmpeg": shutil.which("ffmpeg"),
        "pyav": _pyav_available(),
        "ready_for_automation": True,
    }

    if load_model:
        get_whisper_model()
        result["model_loaded"] = True
        result["note"] = "First run downloads model weights — may take a few minutes"

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
