#!/usr/bin/env python3
"""Batch sp-voicemail-triage-fast — transcription + routing for voicemail queues."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[2]
PARENT_SCRIPTS = SKILLS_DIR / "sp-voicemail-triage" / "scripts"
INBOUND_VETTING_SCRIPTS = SKILLS_DIR / "sp-inbound-vetting" / "scripts"
FAST_OUT_DIR = SKILLS_DIR / "sp-voicemail-triage" / ".tmp" / "batch-run"
sys.path.insert(0, str(PARENT_SCRIPTS))

from batch_process_freshdesk import main as ksonboarding_main  # noqa: E402

FAST_ONLY_FLAGS = {"--no-qsiap", "--qsiap-only", "--qsiap-re-vet"}


def _parent_argv(args: list[str]) -> list[str]:
    """Remove wrapper-only flags before delegating to the KSOnboarding batch."""
    return [arg for arg in args if arg not in FAST_ONLY_FLAGS]


def _qsiap_enabled(args: list[str]) -> bool:
    return "--no-qsiap" not in args


def _qsiap_only(args: list[str]) -> bool:
    return "--qsiap-only" in args


def _qsiap_re_vet(args: list[str]) -> bool:
    return "--qsiap-re-vet" in args


def _build_qsiap_summary(args: list[str]) -> dict:
    """Run QSIAP voicemail vetting with the compatible fast-wrapper flags."""
    sys.path.insert(0, str(INBOUND_VETTING_SCRIPTS))
    from live_run_qsiap_voicemails import (  # noqa: PLC0415
        SKIP_DEFAULT,
        run_qsiap_voicemails,
        write_summary,
    )

    summary = run_qsiap_voicemails(
        skip=set(SKIP_DEFAULT),
        re_vet=_qsiap_re_vet(args),
        dry_run="--dry-run" in args,
        transcribe=True,
    )
    summary_path = write_summary(summary)
    return {"summary_path": str(summary_path), **summary}


def _latest_summary_path(before: set[Path]) -> Path | None:
    candidates = sorted(
        (path for path in FAST_OUT_DIR.glob("batch-*.json") if path not in before),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _read_summary(path: Path | None) -> dict | None:
    if not path:
        return None
    return {"summary_path": str(path), **json.loads(path.read_text(encoding="utf-8"))}


def _write_combined_summary(summary: dict) -> Path:
    FAST_OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FAST_OUT_DIR / f"fast-combined-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out_path


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
    if "--no-transcribe" in sys.argv:
        sys.argv.remove("--no-transcribe")
    code = _preflight()
    if code != 0:
        raise SystemExit(code)
    if "--skip-preflight" in sys.argv:
        sys.argv.remove("--skip-preflight")

    original_argv = sys.argv[:]
    before = set(FAST_OUT_DIR.glob("batch-*.json"))
    ksonboarding_code = 0
    ksonboarding_summary = None
    if not _qsiap_only(original_argv[1:]):
        sys.argv = [original_argv[0], *_parent_argv(original_argv[1:])]
        ksonboarding_code = ksonboarding_main()
        ksonboarding_summary = _read_summary(_latest_summary_path(before))

    qsiap_summary = None
    qsiap_error = None
    if _qsiap_enabled(original_argv[1:]):
        try:
            qsiap_summary = _build_qsiap_summary(original_argv[1:])
        except Exception as exc:  # noqa: BLE001
            qsiap_error = str(exc)

    combined = {
        "mode": "fast-combined",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "ksonboarding": ksonboarding_summary,
        "qsiap": qsiap_summary,
        "qsiap_error": qsiap_error,
    }
    combined_path = _write_combined_summary(combined)
    print(
        json.dumps(
            {
                "summary_path": str(combined_path),
                "ksonboarding_processed": (ksonboarding_summary or {}).get("processed", 0),
                "ksonboarding_transcribed": (ksonboarding_summary or {}).get("transcribed", 0),
                "ksonboarding_transcription_failed": (ksonboarding_summary or {}).get("transcription_failed", 0),
                "ksonboarding_routed": (ksonboarding_summary or {}).get("routed", 0),
                "ksonboarding_closed": (ksonboarding_summary or {}).get("closed", 0),
                "qsiap_discovered": (qsiap_summary or {}).get("discovered", 0),
                "qsiap_vetted": (qsiap_summary or {}).get("vetted", 0),
                "qsiap_known_sp": (qsiap_summary or {}).get("known_sp", 0),
                "qsiap_error": qsiap_error,
            },
            indent=2,
        )
    )
    sys.argv = original_argv
    raise SystemExit(1 if qsiap_error else ksonboarding_code)
