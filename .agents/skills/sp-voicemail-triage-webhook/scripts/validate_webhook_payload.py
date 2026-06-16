#!/usr/bin/env python3
"""Validate sp-voicemail-triage-webhook JSON payloads (Option B encoding)."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

MAX_BYTES = 25 * 1024 * 1024
ALLOWED_TYPES = {"audio/wav", "audio/x-wav"}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("dry_run") is not True:
        audio_b64 = payload.get("audio_base64")
        if not audio_b64:
            errors.append("missing audio_base64 (required for JSON payloads)")
            return errors

        content_type = payload.get("audio_content_type", "")
        if content_type not in ALLOWED_TYPES:
            errors.append(
                f"audio_content_type must be one of {sorted(ALLOWED_TYPES)}"
            )

        try:
            raw = base64.b64decode(audio_b64, validate=True)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"audio_base64 decode failed: {exc}")
            return errors

        if len(raw) > MAX_BYTES:
            errors.append(f"audio exceeds max size ({MAX_BYTES} bytes)")
        if not raw.startswith(b"RIFF"):
            errors.append("audio is not a RIFF/WAV file")

    ticket_id = payload.get("freshdesk_ticket_id")
    if ticket_id is not None and (
        not isinstance(ticket_id, int) or ticket_id <= 0
    ):
        errors.append("freshdesk_ticket_id must be a positive integer")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_webhook_payload.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(payload)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
