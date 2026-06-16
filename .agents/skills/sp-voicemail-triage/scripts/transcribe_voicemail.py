#!/usr/bin/env python3
"""Download Freshdesk voicemail .wav attachments and transcribe via OpenAI Whisper.

Voicemail notification emails/tickets include metadata in the body (caller, phone,
duration) but NOT the spoken message — transcription must use the .wav attachment.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

WAV_NAME_RE = re.compile(r"\.wav$", re.I)
MAX_WAV_BYTES = 25 * 1024 * 1024
WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
TIMEOUT = 120


def pick_wav_attachment(ticket: dict) -> dict | None:
    for att in ticket.get("attachments") or []:
        name = (att.get("name") or "").lower()
        ctype = (att.get("content_type") or "").lower()
        if WAV_NAME_RE.search(name) or "wav" in ctype or ctype in ("audio/wav", "audio/x-wav"):
            return att
    return None


def download_attachment(url: str, api_key: str) -> bytes:
    import base64

    token = base64.b64encode(f"{api_key}:X".encode()).decode()
    req = Request(
        url,
        headers={
            "Authorization": f"Basic {token}",
            "User-Agent": "sp-voicemail-triage/1.0",
        },
        method="GET",
    )
    with urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
    if len(data) > MAX_WAV_BYTES:
        raise ValueError(f"WAV exceeds {MAX_WAV_BYTES} bytes")
    if not data.startswith(b"RIFF"):
        raise ValueError("Attachment is not a RIFF/WAV file")
    return data


def transcribe_wav_bytes(wav_bytes: bytes, filename: str = "voicemail.wav") -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    boundary = uuid.uuid4().hex
    body = bytearray()
    parts: list[tuple[str, bytes, str | None]] = [
        ("file", wav_bytes, filename),
        ("model", b"whisper-1", None),
        ("response_format", b"text", None),
    ]
    for name, payload, fname in parts:
        body.extend(f"--{boundary}\r\n".encode())
        if fname:
            body.extend(
                f'Content-Disposition: form-data; name="{name}"; filename="{fname}"\r\n'.encode()
            )
            body.extend(b"Content-Type: audio/wav\r\n\r\n")
        else:
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(payload)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    req = Request(
        WHISPER_URL,
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            text = resp.read().decode("utf-8").strip()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Whisper HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Whisper request failed: {exc.reason}") from exc

    if not text:
        raise RuntimeError("Whisper returned empty transcript")
    return text


def transcribe_ticket(ticket: dict, api_key: str) -> dict[str, Any]:
    att = pick_wav_attachment(ticket)
    if not att:
        return {"ok": False, "error": "no_wav_attachment", "transcript": ""}

    url = att.get("attachment_url")
    if not url:
        return {"ok": False, "error": "missing_attachment_url", "transcript": ""}

    try:
        wav = download_attachment(url, api_key)
        text = transcribe_wav_bytes(wav, att.get("name") or "voicemail.wav")
        return {
            "ok": True,
            "transcript": text,
            "attachment_name": att.get("name"),
            "bytes": len(wav),
            "source": "openai-whisper",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "transcript": ""}
