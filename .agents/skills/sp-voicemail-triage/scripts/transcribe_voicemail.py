#!/usr/bin/env python3
"""Download Freshdesk voicemail audio attachments and transcribe via faster-whisper.

Voicemail notification emails/tickets include metadata in the body (caller, phone,
duration) but NOT the spoken message — transcription must use the attached audio
file (.wav or .mp3). Local inference; no OpenAI API key required.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

AUDIO_EXT_RE = re.compile(r"\.(wav|mp3)$", re.I)
MAX_AUDIO_BYTES = 25 * 1024 * 1024
TIMEOUT = 120
TRANSCRIPT_SOURCE = "faster-whisper"

_WHISPER_MODEL = None


def whisper_settings() -> tuple[str, str, str]:
    model = (os.environ.get("WHISPER_MODEL") or "small").strip() or "small"
    device = (os.environ.get("WHISPER_DEVICE") or "cpu").strip() or "cpu"
    compute = (os.environ.get("WHISPER_COMPUTE_TYPE") or "int8").strip() or "int8"
    return model, device, compute


def _audio_backend_ready() -> bool:
    if shutil.which("ffmpeg"):
        return True
    try:
        import av  # noqa: F401
    except ImportError:
        return False
    return True


def get_whisper_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper not installed — run: python "
                ".agents/skills/sp-voicemail-triage/scripts/setup_transcription.py"
            ) from exc
        if not _audio_backend_ready():
            raise RuntimeError(
                "No audio decoder available — install ffmpeg on PATH or reinstall "
                "faster-whisper (includes PyAV)"
            )
        model_size, device, compute_type = whisper_settings()
        _WHISPER_MODEL = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _WHISPER_MODEL


def _attachment_kind(att: dict) -> str | None:
    name = (att.get("name") or att.get("file_name") or "").lower()
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


def _attachment_url(att: dict) -> str | None:
    return att.get("attachment_url") or att.get("content_url")


def collect_audio_attachments(ticket: dict) -> list[dict]:
    """Collect .wav/.mp3 attachments from ticket body and conversation thread."""
    seen: set[int | str] = set()
    collected: list[dict] = []

    def add(att: dict, source: str) -> None:
        att_id = att.get("id")
        key = att_id if att_id is not None else (_attachment_url(att), att.get("name"))
        if key in seen:
            return
        if not _attachment_kind(att):
            return
        seen.add(key)
        collected.append({**att, "_source": source})

    for att in ticket.get("attachments") or []:
        add(att, "ticket")
    for conv in ticket.get("conversations") or []:
        conv_id = conv.get("id")
        for att in conv.get("attachments") or []:
            add(att, f"conversation:{conv_id}")

    wav = [a for a in collected if _attachment_kind(a) == "wav"]
    mp3 = [a for a in collected if _attachment_kind(a) == "mp3"]
    return wav + mp3


def pick_audio_attachment(ticket: dict) -> dict | None:
    attachments = collect_audio_attachments(ticket)
    return attachments[0] if attachments else None


def pick_wav_attachment(ticket: dict) -> dict | None:
    """Backward-compatible alias — returns .wav or .mp3 attachment."""
    return pick_audio_attachment(ticket)


def download_attachment(url: str, api_key: str) -> bytes:
    """Download attachment bytes. Freshdesk attachment_url values are presigned S3 URLs."""
    headers = {"User-Agent": "sp-voicemail-triage/1.0"}
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
    except HTTPError as exc:
        if exc.code in (401, 403) and api_key:
            import base64

            token = base64.b64encode(f"{api_key}:X".encode()).decode()
            req_auth = Request(
                url,
                headers={**headers, "Authorization": f"Basic {token}"},
                method="GET",
            )
            with urlopen(req_auth, timeout=TIMEOUT) as resp:
                data = resp.read()
        else:
            raise
    if len(data) > MAX_AUDIO_BYTES:
        raise ValueError(f"Audio file exceeds {MAX_AUDIO_BYTES} bytes")
    return data


def _suffix_for_filename(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".mp3"):
        return ".mp3"
    if lower.endswith(".wav"):
        return ".wav"
    return ".wav"


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "voicemail.wav") -> str:
    if not audio_bytes:
        raise RuntimeError("Downloaded audio file is empty")

    model = get_whisper_model()
    suffix = _suffix_for_filename(filename)
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        segments, _info = model.transcribe(
            tmp_path,
            language="en",
            vad_filter=False,
            condition_on_previous_text=False,
        )
        parts = [segment.text.strip() for segment in segments if segment.text.strip()]
        text = " ".join(parts).strip()
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            os.unlink(tmp_path)

    if not text:
        raise RuntimeError(
            "faster-whisper returned empty transcript (silent or unintelligible audio)"
        )
    return text


def transcribe_wav_bytes(wav_bytes: bytes, filename: str = "voicemail.wav") -> str:
    """Backward-compatible alias."""
    return transcribe_audio_bytes(wav_bytes, filename)


def transcribe_ticket(ticket: dict, api_key: str) -> dict[str, Any]:
    att = pick_audio_attachment(ticket)
    if not att:
        return {"ok": False, "error": "no_audio_attachment", "transcript": ""}

    url = _attachment_url(att)
    if not url:
        return {"ok": False, "error": "missing_attachment_url", "transcript": ""}

    filename = att.get("name") or att.get("file_name") or "voicemail.wav"
    model_size, device, compute_type = whisper_settings()
    try:
        audio = download_attachment(url, api_key)
        text = transcribe_audio_bytes(audio, filename)
        return {
            "ok": True,
            "transcript": text,
            "attachment_name": filename,
            "attachment_source": att.get("_source"),
            "bytes": len(audio),
            "source": TRANSCRIPT_SOURCE,
            "model": model_size,
            "device": device,
            "compute_type": compute_type,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "transcript": ""}
