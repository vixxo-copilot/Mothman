#!/usr/bin/env python3
"""Batch sp-voicemail-triage for Freshdesk KSOnboarding queue (REST)."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

DOMAIN = "vixxo-helpdesk.freshdesk.com"
QUERY = "group_id:159000485013 AND status:2 AND type:'KSOnboarding'"
OUT_DIR = Path(__file__).resolve().parent.parent / ".tmp" / "batch-run"
TIMEOUT = 90

NEW_VOICEMAIL_SUBJECT_RE = re.compile(r"\bnew voicemail\b", re.I)
PHONE_RE = re.compile(r"\(\+1(\d{10})\)|\+1(\d{10})|(\d{3})[-. ](\d{3})[-. ](\d{4})")
DURATION_RE = re.compile(r"Duration:\s*(\d{2}:\d{2})", re.I)
CALLER_SUBJECT_RE = re.compile(
    r"voicemail from\s+(.+?)\s+via\s+", re.I
)
CALLER_BODY_RE = re.compile(
    r"New voicemail from\s*\n?\s*(.+?)\s*\(\+", re.I | re.S
)
SR_RE = re.compile(r"\b(?:SR|service request|work order)\s*#?\s*(\d{5,10})\b", re.I)
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
AUDIO_CONTENT_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/webm",
    "application/octet-stream",
}
TRANSCRIPTION_DIR = OUT_DIR / "audio"

CATEGORY_RULES: list[tuple[str, list[str], str]] = [
    ("COI / Compliance", ["coi", "certificate of insurance", "insurance", "acord", "additional insured"], "COI@vixxo.com"),
    ("Payment Information", ["payment", "paid", "check", "remittance", "ach", "wire", "when paid", "haven't received payment"], "aphelp@vixxo.com"),
    ("Billing / Invoice Support", ["invoice", "billing", "rejected", "submit invoice", "resubmit"], "aphelp@vixxo.com"),
    ("VixxoLink Support", ["vixxolink", "portal", "login", "password", "app", "dispatch board", "accept work"], "service.providermanagement@vixxo.com"),
    ("Service Request / Dispatch", ["service request", "work order", "dispatch", "eta", "assigned", "technician", " sr "], "SR_BRANCH"),
    ("Coverage / Onboarding", ["onboard", "onboarding", "coverage", "enrollment", "new provider", "rate card", "activation"], "ONBOARDING_BRANCH"),
    ("Technical / Trade Support", ["warranty", "parts", "technical", "how to fix"], "service.providermanagement@vixxo.com"),
]


def load_credentials() -> str:
    root = Path(__file__).resolve().parents[4]
    env_path = root / ".env"
    if env_path.is_file():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and not os.environ.get(k):
                os.environ[k] = v
    for name in ("freshdesk_token", "freshdesk_api_key"):
        p = Path.home() / ".vixxo" / name
        if p.is_file() and not os.environ.get("FRESHDESK_API_KEY"):
            os.environ["FRESHDESK_API_KEY"] = p.read_text(encoding="utf-8").strip()
    if not os.environ.get("FRESHDESK_API_KEY") and os.environ.get("FRESHDESK_TOKEN"):
        os.environ["FRESHDESK_API_KEY"] = os.environ["FRESHDESK_TOKEN"]
    key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    if not key:
        raise SystemExit("ERROR: FRESHDESK_API_KEY not configured")
    return key


def load_optional_file_secret(path: Path) -> str | None:
    if path.is_file():
        value = path.read_text(encoding="utf-8").strip()
        return value or None
    return None


def load_transcription_api_key() -> str | None:
    """Load an OpenAI-compatible transcription API key without printing it."""
    key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENAI_TOKEN")
        or load_optional_file_secret(Path.home() / ".vixxo" / "openai_api_key")
    )
    return key.strip() if key else None


def auth_headers(api_key: str) -> dict[str, str]:
    token = base64.b64encode(f"{api_key}:X".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def http_json(method: str, path: str, api_key: str, body: dict | None = None) -> Any:
    url = f"https://{DOMAIN}{path}"
    data = None
    headers = auth_headers(api_key)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read()
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def http_download(url: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        path.write_bytes(resp.read())
    return path


def search_tickets(api_key: str) -> list[dict]:
    results: list[dict] = []
    for page in range(1, 11):
        params = {"query": f'"{QUERY}"', "page": str(page)}
        url = f"https://{DOMAIN}/api/v2/search/tickets?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        page_results = data.get("results") or []
        results.extend(page_results)
        if len(page_results) < 30:
            break
    return results


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def is_voicemail_subject(subject: str | None) -> bool:
    return bool(NEW_VOICEMAIL_SUBJECT_RE.search(subject or ""))


def is_voicemail_ticket(ticket: dict) -> bool:
    return is_voicemail_subject(ticket.get("subject"))


def search_voicemail_tickets(api_key: str) -> tuple[list[dict], list[dict]]:
    all_tickets = search_tickets(api_key)
    voicemail = [t for t in all_tickets if is_voicemail_ticket(t)]
    skipped = [t for t in all_tickets if not is_voicemail_ticket(t)]
    return voicemail, skipped


def normalize_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    m = PHONE_RE.search(raw)
    if not m:
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        return digits if len(digits) == 10 else raw.strip()
    groups = m.groups()
    if groups[0]:
        return groups[0]
    if groups[1]:
        return groups[1]
    if groups[2]:
        return f"{groups[2]}{groups[3]}{groups[4]}"
    return raw.strip()


def extract_metadata(ticket: dict) -> dict[str, str | None]:
    subject = ticket.get("subject") or ""
    desc_html = ticket.get("description") or ""
    desc_text = ticket.get("description_text") or strip_html(desc_html)
    blob = f"{subject}\n{desc_text}\n{desc_html}"

    caller = None
    m = CALLER_SUBJECT_RE.search(subject)
    if m:
        caller = m.group(1).strip()
    if not caller:
        m2 = CALLER_BODY_RE.search(desc_html) or CALLER_BODY_RE.search(desc_text)
        if m2:
            caller = re.sub(r"\s+", " ", m2.group(1)).strip()

    phone = normalize_phone(blob)
    duration = None
    dm = DURATION_RE.search(blob)
    if dm:
        duration = dm.group(1)

    return {
        "caller": caller or "Not stated",
        "phone": phone or "Not stated",
        "duration": duration or "Unknown",
        "company": caller if caller and caller.upper() != "WIRELESS CALLER" else "Not stated",
    }


@dataclass
class TranscriptResult:
    text: str
    source: str
    status: str
    error: str = ""
    attachment_name: str = ""


def is_audio_attachment(attachment: dict) -> bool:
    name = str(attachment.get("name") or "")
    content_type = str(attachment.get("content_type") or "").lower()
    suffix = Path(name).suffix.lower()
    return suffix in AUDIO_EXTENSIONS or content_type in AUDIO_CONTENT_TYPES


def audio_attachments(ticket: dict) -> list[dict]:
    return [a for a in ticket.get("attachments") or [] if is_audio_attachment(a)]


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or f"attachment-{uuid.uuid4().hex}.wav"


def download_attachment(ticket_id: int, attachment: dict) -> Path:
    url = attachment.get("attachment_url")
    if not url:
        raise RuntimeError("attachment has no attachment_url")
    name = safe_filename(str(attachment.get("name") or "voicemail.wav"))
    return http_download(str(url), TRANSCRIPTION_DIR / str(ticket_id) / name)


def run_transcription_command(audio_path: Path) -> str | None:
    command_template = os.environ.get("SP_VOICEMAIL_TRANSCRIPTION_COMMAND")
    if not command_template:
        return None
    if "{audio}" in command_template:
        command = command_template.format(audio=str(audio_path))
        args = shlex.split(command)
    else:
        args = [*shlex.split(command_template), str(audio_path)]
    completed = subprocess.run(args, check=True, capture_output=True, text=True, timeout=TIMEOUT)
    return completed.stdout.strip()


def transcribe_with_whisper_cli(audio_path: Path) -> str | None:
    whisper = shutil.which("whisper")
    if not whisper:
        return None
    out_dir = audio_path.parent / "whisper-output"
    out_dir.mkdir(parents=True, exist_ok=True)
    model = os.environ.get("SP_VOICEMAIL_WHISPER_MODEL", "base")
    subprocess.run(
        [
            whisper,
            str(audio_path),
            "--model",
            model,
            "--language",
            "English",
            "--output_format",
            "txt",
            "--output_dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=max(TIMEOUT, 300),
    )
    transcript_path = out_dir / f"{audio_path.stem}.txt"
    if not transcript_path.is_file():
        raise RuntimeError("whisper CLI completed without producing a transcript")
    return transcript_path.read_text(encoding="utf-8").strip()


def build_multipart_form(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----sp-voicemail-{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    body.extend(file_path.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def transcribe_with_openai(audio_path: Path) -> str | None:
    api_key = load_transcription_api_key()
    if not api_key:
        return None
    model = os.environ.get("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")
    url = os.environ.get("OPENAI_TRANSCRIPTION_URL", "https://api.openai.com/v1/audio/transcriptions")
    fields = {"model": model}
    language = os.environ.get("OPENAI_TRANSCRIPTION_LANGUAGE")
    if language:
        fields["language"] = language
    data, content_type = build_multipart_form(fields, "file", audio_path)
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        },
    )
    with urllib.request.urlopen(req, timeout=max(TIMEOUT, 300)) as resp:
        raw = resp.read().decode("utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip()
    text = payload.get("text")
    if not text:
        raise RuntimeError("transcription response did not include text")
    return str(text).strip()


def transcribe_audio_file(audio_path: Path) -> str:
    for provider in (run_transcription_command, transcribe_with_openai, transcribe_with_whisper_cli):
        text = provider(audio_path)
        if text:
            return text
    raise RuntimeError(
        "no transcription provider configured; set OPENAI_API_KEY, "
        "SP_VOICEMAIL_TRANSCRIPTION_COMMAND, or install whisper CLI"
    )


def transcribe_ticket_audio(ticket_id: int, ticket: dict) -> TranscriptResult:
    attachments = audio_attachments(ticket)
    if not attachments:
        return TranscriptResult(
            text="",
            source="none",
            status="no-audio",
            error="no audio attachment found",
        )
    attachment = attachments[0]
    try:
        audio_path = download_attachment(ticket_id, attachment)
        text = transcribe_audio_file(audio_path)
    except Exception as exc:  # noqa: BLE001
        return TranscriptResult(
            text="",
            source="audio transcription",
            status="failed",
            error=str(exc),
            attachment_name=str(attachment.get("name") or ""),
        )
    return TranscriptResult(
        text=text,
        source="audio transcription",
        status="transcribed",
        attachment_name=str(attachment.get("name") or ""),
    )


def require_audio_transcription() -> bool:
    value = os.environ.get("SP_VOICEMAIL_REQUIRE_TRANSCRIPTION", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def build_transcript(meta: dict, ticket: dict, api_key: str | None = None) -> TranscriptResult:
    subject = ticket.get("subject") or ""
    att_names = [a.get("name") for a in ticket.get("attachments") or [] if a.get("name")]
    ticket_id = int(ticket.get("id") or 0)
    if api_key and audio_attachments(ticket):
        audio_result = transcribe_ticket_audio(ticket_id, ticket)
        if audio_result.status == "transcribed":
            lines = [
                "[Transcript source: audio transcription]",
                f"Subject: {subject}",
                f"Caller ID: {meta['caller']}",
                f"Callback number: {meta['phone']}",
                f"Duration: {meta['duration']}",
            ]
            if audio_result.attachment_name:
                lines.append(f"Attachment transcribed: {audio_result.attachment_name}")
            lines.extend(["", audio_result.text])
            audio_result.text = "\n".join(lines)
        return audio_result

    lines = [
        f"[Voicemail notification — audio attachment only; no email body transcript]",
        f"Subject: {subject}",
        f"Caller ID: {meta['caller']}",
        f"Callback number: {meta['phone']}",
        f"Duration: {meta['duration']}",
    ]
    if att_names:
        lines.append(f"Attachments: {', '.join(att_names)}")
    lines.append(
        "[Note: Full message content is in the WAV attachment; triage based on "
        "caller metadata pending audio transcription. Callback Recommended.]"
    )
    return TranscriptResult(
        text="\n".join(lines),
        source="notification metadata",
        status="fallback",
        error="audio transcription was not attempted",
    )


def _keyword_in_text(keyword: str, text: str) -> bool:
    if " " in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def classify(transcript: str, meta: dict) -> tuple[str, str, str]:
    text = transcript.lower()
    sr = None
    sm = SR_RE.search(transcript)
    if sm:
        sr = sm.group(1)
    if "audio attachment only" in text or "[inaudible]" in text:
        return "General Inquiry", "service.providermanagement@vixxo.com", sr or ""
    for category, keywords, route in CATEGORY_RULES:
        if any(_keyword_in_text(k, text) for k in keywords):
            if route == "SR_BRANCH" and sr:
                return category, route, sr
            if route == "SR_BRANCH":
                return category, "service.providermanagement@vixxo.com", ""
            if route == "ONBOARDING_BRANCH":
                return category, "spm-recruitment@vixxo.com", ""
            return category, route, sr or ""
    if meta.get("caller", "").upper() == "WIRELESS CALLER":
        return "General Inquiry", "service.providermanagement@vixxo.com", sr or ""
    return "General Inquiry", "service.providermanagement@vixxo.com", sr or ""


def callback_decision(transcript: str) -> tuple[str, str]:
    t = transcript.lower()
    yes_signals = ["call me back", "return my call", "need someone to call", "urgent", "third time"]
    if any(s in t for s in yes_signals):
        return "Yes", "High"
    if "audio attachment only" in t or "wireless caller" in t:
        return "Recommended", "Normal"
    return "Recommended", "Normal"


def internal_note(ticket_id: int, meta: dict, category: str, callback: str, urgency: str,
                    route: str, transcript: str, sr: str, *, no_email: bool = False,
                    transcription_status: str = "") -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sr_line = f"**Reference IDs:** {sr}" if sr else "**Reference IDs:** none"
    transcribed = transcription_status == "transcribed"
    vetting_note = "Unknown (external system vetting unavailable in this batch script)"
    summary = "KSOnboarding voicemail audio was transcribed by automation and routed from the transcript."
    callback_rationale = "Callback decision based on the transcribed voicemail content."
    if not transcribed:
        vetting_note = "Unknown (audio-only intake; vetting deferred)"
        summary = "KSOnboarding voicemail processed by sp-voicemail-triage batch. Audio attachment retained on ticket; recipient should listen and callback if needed."
        callback_rationale = "Voicemail left on KS onboarding line; no text transcript in notification email."
    if no_email:
        routing_action = (
            f"- **Recommended forward to:** {route}\n"
            f"- **Email forward sent:** No (no-email skill)\n"
            f"- **Disposition:** Resolve after internal note"
        )
    else:
        routing_action = (
            f"- **Forward to:** {route}\n"
            f"- **Disposition:** Resolve after forward"
        )
    return f"""**SP Voicemail Triage — Freshdesk #{ticket_id}**

**Processed:** {now}
**Category:** {category}
**Callback required:** {callback} ({urgency})
**Caller:** {meta['caller']} | **Company:** {meta['company']}
**Callback #:** {meta['phone']}
{sr_line}

---

**Company vetting**

| System | Match | ID |
| --- | --- | --- |
| Siebel / Gateway SP | Unknown | — |
| Gateway / VixxoLink Customer | Unknown | — |
| JDE Vendor | Unknown | — |
| Salesforce Lead/Account | Unknown | — |

**Entity posture:** {vetting_note}

---

**Transcript**

{transcript}

---

**Routing action**

{routing_action}

---

**Summary:** {summary}

**Callback rationale:** {callback_rationale}
"""


def transcription_failure_note(ticket_id: int, meta: dict, result: TranscriptResult) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    attachment = result.attachment_name or "Not identified"
    error = result.error or "Unknown transcription failure"
    return f"""**SP Voicemail Triage — Freshdesk #{ticket_id}**

**Processed:** {now}
**Category:** Not triaged — audio transcription failed
**Callback required:** Recommended (Normal)
**Caller:** {meta['caller']} | **Company:** {meta['company']}
**Callback #:** {meta['phone']}
**Reference IDs:** none

---

**Transcription failure**

Automation found an audio voicemail attachment but could not transcribe it.
Because transcription is required for this workflow, the ticket was left open
and was not forwarded or resolved.

- **Attachment:** {attachment}
- **Failure:** {error}

---

**Routing action**

- **Forward to:** Not sent
- **Disposition:** Open — transcription required before triage

---

**Summary:** Voicemail intake requires audio transcription before classification and routing.

**Callback rationale:** Callback is recommended until the spoken voicemail content is available.
"""


@dataclass
class Result:
    ticket_id: int
    caller: str
    phone: str
    category: str
    route: str
    callback: str
    note: str = ""
    forward: str = ""
    resolve: str = ""
    error: str = ""
    transcription: str = ""


def process_ticket(
    api_key: str,
    ticket_summary: dict,
    dry_run: bool = False,
    reroute_correction: bool = False,
    no_email: bool = False,
) -> Result:
    tid = int(ticket_summary["id"])
    if not is_voicemail_ticket(ticket_summary):
        return Result(
            ticket_id=tid,
            caller="—",
            phone="—",
            category="Skipped",
            route="—",
            callback="—",
            note="skipped:non-voicemail",
        )
    ticket = http_json("GET", f"/api/v2/tickets/{tid}", api_key)
    meta = extract_metadata(ticket)
    transcript_result = build_transcript(meta, ticket, api_key=api_key)
    if transcript_result.status == "failed" and require_audio_transcription():
        result = Result(
            ticket_id=tid,
            caller=str(meta["caller"]),
            phone=str(meta["phone"]),
            category="Not triaged",
            route="—",
            callback="Recommended",
            forward="skipped:transcription_failed",
            resolve="open",
            error=f"transcription:{transcript_result.error}",
            transcription=transcript_result.status,
        )
        if dry_run:
            result.note = "dry-run"
            return result
        try:
            http_json(
                "POST",
                f"/api/v2/tickets/{tid}/notes",
                api_key,
                {"body": transcription_failure_note(tid, meta, transcript_result), "private": True},
            )
            result.note = "posted"
        except urllib.error.HTTPError as exc:
            result.note = f"failed:{exc.code}"
            result.error = f"{result.error}; note:{exc.reason}"
        return result

    transcript = transcript_result.text
    category, route, sr = classify(transcript, meta)
    callback, urgency = callback_decision(transcript)

    if category == "Service Request / Dispatch" and sr:
        route = "service.providermanagement@vixxo.com"
        forward_subject = f"{sr}, Need Assistance"
    else:
        forward_subject = None

    note_body = internal_note(
        tid,
        meta,
        category,
        callback,
        urgency,
        route,
        transcript,
        sr,
        no_email=no_email,
        transcription_status=transcript_result.status,
    )
    result = Result(
        ticket_id=tid,
        caller=str(meta["caller"]),
        phone=str(meta["phone"]),
        category=category,
        route=route,
        callback=callback,
        transcription=transcript_result.status,
    )

    if dry_run:
        result.note = "dry-run"
        return result

    try:
        http_json(
            "POST",
            f"/api/v2/tickets/{tid}/notes",
            api_key,
            {"body": note_body, "private": True},
        )
        result.note = "posted"
    except urllib.error.HTTPError as exc:
        result.note = f"failed:{exc.code}"
        result.error = f"note:{exc.reason}"

    if no_email:
        result.forward = "not-sent:no-email"
    else:
        forward_body = (
            f"SP Voicemail triage — Freshdesk #{tid}\n\n"
            f"Category: {category}\n"
            f"Caller: {meta['caller']}\n"
            f"Callback: {meta['phone']}\n"
            f"Callback required: {callback}\n\n"
            f"{transcript}\n\n"
            f"— Automated triage (sp-voicemail-triage)."
        )
        if reroute_correction:
            forward_body += (
                "\nNote: Prior misroute to AP (keyword false match) — corrected forward to SPM."
            )
        fwd_payload: dict[str, Any] = {
            "body": forward_body,
            "to_emails": [route] if "@" in route else [],
        }
        if forward_subject:
            fwd_payload["subject"] = forward_subject

        try:
            if fwd_payload.get("to_emails"):
                http_json("POST", f"/api/v2/tickets/{tid}/forward", api_key, fwd_payload)
                result.forward = route
            else:
                result.forward = "skipped"
        except urllib.error.HTTPError as exc:
            result.forward = f"failed:{exc.code}"
            if not result.error:
                result.error = f"forward:{exc.reason}"

    try:
        http_json(
            "PUT",
            f"/api/v2/tickets/{tid}",
            api_key,
            {
                "status": 5,
                "type": "KSOnboarding",
                "custom_fields": {"cf_sp": "Unknown"},
            },
        )
        result.resolve = "closed"
    except urllib.error.HTTPError as exc:
        result.resolve = f"failed:{exc.code}"
        if not result.error:
            result.error = f"resolve:{exc.reason}"

    return result


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    reroute_correction = "--reroute-spm" in sys.argv
    no_email = "--no-email" in sys.argv
    api_key = load_credentials()
    tickets, skipped = search_voicemail_tickets(api_key)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[Result] = []
    for t in tickets:
        try:
            results.append(
                process_ticket(
                    api_key,
                    t,
                    dry_run=dry_run,
                    reroute_correction=reroute_correction,
                    no_email=no_email,
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                Result(
                    ticket_id=int(t.get("id", 0)),
                    caller="?",
                    phone="?",
                    category="?",
                    route="?",
                    callback="?",
                    error=str(exc),
                )
            )

    summary = {
        "processed": len(results),
        "skipped_non_voicemail": len(skipped),
        "skipped_ids": [int(t["id"]) for t in skipped],
        "dry_run": dry_run,
        "routed": sum(
            1
            for r in results
            if r.forward and not str(r.forward).startswith("failed") and r.forward != "not-sent:no-email"
        ),
        "no_email": no_email,
        "closed": sum(1 for r in results if r.resolve == "closed"),
        "failed": [r.ticket_id for r in results if r.error or str(r.note).startswith("failed")],
        "results": [r.__dict__ for r in results],
    }
    out_path = OUT_DIR / f"batch-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"summary_path": str(out_path), **{k: summary[k] for k in ('processed','routed','closed','failed')}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
