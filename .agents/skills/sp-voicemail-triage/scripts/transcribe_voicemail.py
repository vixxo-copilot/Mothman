#!/usr/bin/env python3
"""Download Freshdesk voicemail audio attachments and transcribe via OpenAI Whisper.

Voicemail notification emails/tickets include metadata in the body (caller, phone,
duration) but NOT the spoken message — transcription must use the attached audio
file (.wav or .mp3).
"""

from __future__ import annotations

import os
import re
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

AUDIO_EXT_RE = re.compile(r"\.(wav|mp3)$", re.I)
MAX_AUDIO_BYTES = 25 * 1024 * 1024
WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
TIMEOUT = 120


def _attachment_kind(att: dict) -> str | None:
    name = (att.get("name") or "").lower()
    ctype = (att.get("content_type") or "").lower()
    if name.endswith(".wav") or "wav" in ctype or ctype in ("audio/wav", "audio/x-wav"):
        return "wav"
    if name.endswith(".mp3") or "mp3" in ctype or "mpeg" in ctype or ctype in (
        "audio/mpeg",
        "audio/mp3",
    ):
        return "mp3"
    if AUDIO_EXT_RE.search(name):
        return name.rsplit(".", 1)[-1]
    return None


def pick_audio_attachment(ticket: dict) -> dict | None:
    wav_att: dict | None = None
    mp3_att: dict | None = None
    for att in ticket.get("attachments") or []:
        kind = _attachment_kind(att)
        if kind == "wav" and wav_att is None:
            wav_att = att
        elif kind == "mp3" and mp3_att is None:
            mp3_att = att
    return wav_att or mp3_att


def pick_wav_attachment(ticket: dict) -> dict | None:
    """Backward-compatible alias — returns .wav or .mp3 attachment."""
    return pick_audio_attachment(ticket)


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
    if len(data) > MAX_AUDIO_BYTES:
        raise ValueError(f"Audio file exceeds {MAX_AUDIO_BYTES} bytes")
    return data


def _validate_audio_bytes(data: bytes, filename: str) -> None:
    lower = filename.lower()
    if lower.endswith(".wav"):
        if not data.startswith(b"RIFF"):
            raise ValueError("Attachment is not a RIFF/WAV file")
        return
    if lower.endswith(".mp3"):
        if data.startswith(b"ID3") or (len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
            return
        raise ValueError("Attachment is not a valid MP3 file")
    if data.startswith(b"RIFF"):
        return
    if data.startswith(b"ID3") or (len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return
    raise ValueError("Attachment is not a recognized audio file (.wav or .mp3)")


def _audio_content_type(filename: str) -> str:
    if filename.lower().endswith(".mp3"):
        return "audio/mpeg"
    return "audio/wav"


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "voicemail.wav") -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    _validate_audio_bytes(audio_bytes, filename)
    content_type = _audio_content_type(filename)

    boundary = uuid.uuid4().hex
    body = bytearray()
    parts: list[tuple[str, bytes, str | None]] = [
        ("file", audio_bytes, filename),
        ("model", b"whisper-1", None),
        ("response_format", b"text", None),
    ]
    for name, payload, fname in parts:
        body.extend(f"--{boundary}\r\n".encode())
        if fname:
            body.extend(
                f'Content-Disposition: form-data; name="{name}"; filename="{fname}"\r\n'.encode()
            )
            body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
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


def transcribe_wav_bytes(wav_bytes: bytes, filename: str = "voicemail.wav") -> str:
    """Backward-compatible alias."""
    return transcribe_audio_bytes(wav_bytes, filename)


def transcribe_ticket(ticket: dict, api_key: str) -> dict[str, Any]:
    att = pick_audio_attachment(ticket)
    if not att:
        return {"ok": False, "error": "no_audio_attachment", "transcript": ""}

    url = att.get("attachment_url")
    if not url:
        return {"ok": False, "error": "missing_attachment_url", "transcript": ""}

    filename = att.get("name") or "voicemail.wav"
    try:
        audio = download_attachment(url, api_key)
        text = transcribe_audio_bytes(audio, filename)
        return {
            "ok": True,
            "transcript": text,
            "attachment_name": att.get("name"),
            "bytes": len(audio),
            "source": "openai-whisper",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "transcript": ""}
