#!/usr/bin/env python3
"""Batch sp-voicemail-triage for Outlook (Graph API via outlook_graph_helper.mjs)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from batch_process_freshdesk import (  # noqa: E402
    CALLER_BODY_RE,
    CALLER_SUBJECT_RE,
    DURATION_RE,
    MIN_FORWARD_DURATION_SECONDS,
    NEW_VOICEMAIL_SUBJECT_RE,
    PHONE_RE,
    SKIP_FORWARD_CATEGORIES,
    TRANSCRIPT_SOURCE,
    callback_decision,
    classify,
    count_speech_words,
    detect_skip_forward,
    format_stt_transcript,
    is_voicemail_subject,
    normalize_phone,
    resolve_duration_seconds,
)
from transcribe_voicemail import get_whisper_model, transcribe_audio_bytes  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent
HELPER = SCRIPT_DIR / "outlook_graph_helper.mjs"
OUT_DIR = SCRIPT_DIR.parent / ".tmp" / "outlook-batch-run"
LOOKBACK_DAYS = int(os.environ.get("VM_LOOKBACK_DAYS", "7"))


def load_skip_message_ids(report_path: Path | None = None) -> set[str]:
    """Skip message IDs already routed or closed without forward in prior batches."""
    skip_prefixes = (
        "not-sent:short-duration",
        "not-sent:minimal-speech",
        "not-sent:foul-language",
        "not-sent:manual-closed",
    )
    skip: set[str] = set()

    def ingest_report(path: Path) -> None:
        if not path.is_file():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("dry_run"):
            return
        for row in data.get("results") or []:
            forward = str(row.get("forward") or "")
            if "@" in forward or any(forward.startswith(prefix) for prefix in skip_prefixes):
                skip.update(row.get("message_ids") or [])

    if report_path:
        ingest_report(report_path)
        return skip

    for path in sorted(OUT_DIR.glob("outlook-batch-*.json")):
        if path.name == "outlook-batch-latest.json":
            continue
        ingest_report(path)
    ingest_report(OUT_DIR / "outlook-batch-latest.json")
    return skip


def run_helper(*args: str, binary: bool = False) -> Any:
    env = os.environ.copy()
    cmd = ["node", str(HELPER), *args]
    if binary:
        proc = subprocess.run(cmd, check=True, capture_output=True, env=env)
        return proc.stdout
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    return json.loads(proc.stdout)


def search_voicemail_messages() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = run_helper("scan-voicemails")
    folder = data.get("folder") or {}
    items = list(data.get("value") or [])
    items.sort(key=lambda m: m.get("receivedDateTime") or "", reverse=True)
    return items, folder


def extract_metadata_message(msg: dict[str, Any]) -> dict[str, str | None]:
    subject = msg.get("subject") or ""
    preview = msg.get("bodyPreview") or ""
    blob = f"{subject}\n{preview}"

    caller = None
    m = CALLER_SUBJECT_RE.search(subject)
    if m:
        caller = m.group(1).strip()
    if not caller:
        m2 = CALLER_BODY_RE.search(preview)
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


def pick_audio_attachment(message_id: str) -> dict[str, Any] | None:
    data = run_helper("list-attachments", "--message-id", message_id)
    attachments = data.get("value") or []
    wav = [a for a in attachments if str(a.get("name", "")).lower().endswith(".wav")]
    mp3 = [a for a in attachments if str(a.get("name", "")).lower().endswith(".mp3")]
    chosen = (wav + mp3)[:1]
    return chosen[0] if chosen else None


def download_attachment(message_id: str, attachment_id: str) -> bytes:
    return run_helper(
        "download-attachment",
        "--message-id",
        message_id,
        "--attachment-id",
        attachment_id,
        binary=True,
    )


def contact_key(meta: dict[str, str | None]) -> str:
    phone = meta.get("phone") or ""
    if phone and phone != "Not stated":
        return f"phone:{phone}"
    caller = str(meta.get("caller") or "").strip().lower()
    return f"caller:{caller}" if caller else "unknown"


def combine_group(messages: list[dict[str, Any]]) -> dict[str, Any]:
    metas = [extract_metadata_message(m) for m in messages]
    transcripts: list[str] = []
    stt_results: list[dict[str, Any]] = []
    for msg, meta in zip(messages, metas):
        att = pick_audio_attachment(msg["id"])
        if not att:
            stt_results.append({"ok": False, "error": "no_audio_attachment", "transcript": ""})
            continue
        audio = download_attachment(msg["id"], att["id"])
        text, duration_seconds = transcribe_audio_bytes(audio, att.get("name") or "voicemail.wav")
        stt = {
            "ok": True,
            "transcript": text,
            "duration_seconds": duration_seconds,
            "source": TRANSCRIPT_SOURCE,
            "attachment_name": att.get("name") or "voicemail.wav",
        }
        stt_results.append(stt)
        pseudo_ticket = {"subject": msg.get("subject") or ""}
        transcripts.append(format_stt_transcript(stt, meta, pseudo_ticket))

    combined_transcript = "\n\n---\n\n".join(transcripts)
    primary_meta = metas[0]
    primary_msg = messages[0]
    successful_stt = [r for r in stt_results if r.get("ok")]
    if not successful_stt:
        return {
            "messages": messages,
            "meta": primary_meta,
            "stt": stt_results[0] if stt_results else {"ok": False, "transcript": ""},
            "transcript": combined_transcript,
            "spoken_text": "",
            "transcription_ok": False,
            "error": "transcription failed for all messages in group",
        }

    spoken_text = " ".join(str(r.get("transcript") or "") for r in successful_stt)
    primary_stt = successful_stt[0]
    if not spoken_text.strip():
        duration_seconds = None
        for stt in successful_stt:
            duration_seconds = resolve_duration_seconds(primary_meta, stt)
            if duration_seconds is not None:
                break
        if duration_seconds is not None and duration_seconds < MIN_FORWARD_DURATION_SECONDS:
            return {
                "messages": messages,
                "meta": primary_meta,
                "primary_message": primary_msg,
                "stt": primary_stt,
                "transcript": combined_transcript,
                "spoken_text": spoken_text,
                "transcription_ok": True,
                "skip_forward": True,
                "skip_reason": "short-duration",
                "category": SKIP_FORWARD_CATEGORIES["short-duration"],
                "route": "—",
                "callback": "No",
                "urgency": "Normal",
                "forward_subject": None,
            }
        return {
            "messages": messages,
            "meta": primary_meta,
            "primary_message": primary_msg,
            "stt": primary_stt,
            "transcript": combined_transcript,
            "spoken_text": spoken_text,
            "transcription_ok": True,
            "skip_forward": True,
            "skip_reason": "minimal-speech",
            "category": SKIP_FORWARD_CATEGORIES["minimal-speech"],
            "route": "—",
            "callback": "No",
            "urgency": "Normal",
            "forward_subject": None,
        }

    skip_forward, skip_reason = detect_skip_forward(primary_meta, primary_stt, spoken_text)
    category, route, sr = classify(combined_transcript, primary_meta)
    if skip_forward:
        category = SKIP_FORWARD_CATEGORIES.get(skip_reason, category)
        route = "—"
    callback, urgency = callback_decision(combined_transcript)
    if skip_forward:
        callback, urgency = "No", "Normal"

    forward_subject = None
    if category == "Service Request / Dispatch" and sr and not skip_forward:
        route = "service.providermanagement@vixxo.com"
        forward_subject = f"{sr}, Need Assistance"

    return {
        "messages": messages,
        "meta": primary_meta,
        "primary_message": primary_msg,
        "stt": primary_stt,
        "transcript": combined_transcript,
        "spoken_text": spoken_text,
        "transcription_ok": True,
        "skip_forward": skip_forward,
        "skip_reason": skip_reason,
        "category": category,
        "route": route,
        "callback": callback,
        "urgency": urgency,
        "forward_subject": forward_subject,
    }


def forward_group(group: dict[str, Any], dry_run: bool = False) -> str:
    if group.get("skip_forward"):
        return f"not-sent:{group.get('skip_reason')}"
    route = str(group.get("route") or "")
    if "@" not in route:
        return "skipped:no-route"
    if dry_run:
        return f"dry-run:{route}"

    comment = (
        f"SP Voicemail triage — Outlook ({len(group['messages'])} message(s))\n\n"
        f"Category: {group['category']}\n"
        f"Caller: {group['meta']['caller']}\n"
        f"Callback: {group['meta']['phone']}\n"
        f"Callback required: {group['callback']}\n"
        f"Urgency: {group['urgency']}\n\n"
        f"{group['transcript']}\n\n"
        f"— Automated triage (sp-voicemail-triage / Outlook)."
    )
    args = [
        "forward-message",
        "--message-id",
        group["primary_message"]["id"],
        "--to",
        route,
        "--comment",
        comment,
    ]
    if group.get("forward_subject"):
        args.extend(["--subject", group["forward_subject"]])
    run_helper(*args)
    return route


@dataclass
class Result:
    message_ids: list[str]
    caller: str
    phone: str
    category: str
    route: str
    callback: str
    forward: str = ""
    error: str = ""
    count: int = 1


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    since_last_batch = "--since-last-batch" in sys.argv
    try:
        get_whisper_model()
    except RuntimeError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    messages, vm_folder = search_voicemail_messages()
    skipped_prior = 0
    if since_last_batch:
        skip_ids = load_skip_message_ids()
        before = len(messages)
        messages = [m for m in messages if m.get("id") not in skip_ids]
        skipped_prior = before - len(messages)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for msg in messages:
        meta = extract_metadata_message(msg)
        key = contact_key(meta)
        grouped.setdefault(key, []).append(msg)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[Result] = []
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"outlook-batch-{ts}.json"

    folder_label = vm_folder.get("displayName") or "VM"
    print(f"# SP Voicemail batch — Outlook — {datetime.now(timezone.utc).date()}")
    print(f"**Folder:** {folder_label} ({vm_folder.get('source', 'unknown')})")
    if since_last_batch:
        print(f"**Incremental:** skipped {skipped_prior} already-processed message(s) from prior batch")
    print()
    print("| # | Messages | Caller | Category | Callback | Route to | Status |")
    print("| --- | --- | --- | --- | --- | --- | --- |")

    if not grouped:
        payload = {
            "generated_at": ts,
            "lookback_days": LOOKBACK_DAYS,
            "vm_folder": vm_folder,
            "since_last_batch": since_last_batch,
            "skipped_prior_count": skipped_prior,
            "dry_run": dry_run,
            "candidate_count": len(messages),
            "group_count": 0,
            "results": [],
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        latest = OUT_DIR / "outlook-batch-latest.json"
        latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("_No new voicemail items to process._")
        print()
        print(
            f"**Counts:** {len(messages)} candidates | 0 groups | "
            f"0 routed | 0 failed | dry_run={dry_run}"
        )
        print(f"**Report:** {out_path}")
        return 0

    for idx, (_key, group_msgs) in enumerate(grouped.items(), start=1):
        group_msgs.sort(key=lambda m: m.get("receivedDateTime") or "", reverse=True)
        try:
            group = combine_group(group_msgs)
            if not group.get("transcription_ok"):
                status = "failed:transcription"
                forward = "not-sent:transcription-required"
                meta = group.get("meta") or extract_metadata_message(group_msgs[0])
                results.append(
                    Result(
                        message_ids=[m["id"] for m in group_msgs],
                        caller=str(meta.get("caller") or "—"),
                        phone=str(meta.get("phone") or "—"),
                        category="Skipped",
                        route="—",
                        callback="—",
                        forward=forward,
                        error=str(group.get("error") or "transcription required"),
                        count=len(group_msgs),
                    )
                )
            else:
                forward = forward_group(group, dry_run=dry_run)
                status = "routed" if forward and not forward.startswith("not-sent") and not forward.startswith("dry-run") else forward
                results.append(
                    Result(
                        message_ids=[m["id"] for m in group_msgs],
                        caller=str(group["meta"].get("caller") or "—"),
                        phone=str(group["meta"].get("phone") or "—"),
                        category=str(group["category"]),
                        route=str(group["route"]),
                        callback=str(group["callback"]),
                        forward=forward,
                        count=len(group_msgs),
                    )
                )
            r = results[-1]
            print(
                f"| {idx} | {r.count} | {r.caller} | {r.category} | {r.callback} | {r.route} | {status} |"
            )
        except Exception as exc:  # noqa: BLE001
            meta = extract_metadata_message(group_msgs[0])
            results.append(
                Result(
                    message_ids=[m["id"] for m in group_msgs],
                    caller=str(meta.get("caller") or "—"),
                    phone=str(meta.get("phone") or "—"),
                    category="Failed",
                    route="—",
                    callback="—",
                    forward="failed",
                    error=str(exc),
                    count=len(group_msgs),
                )
            )
            print(
                f"| {idx} | {len(group_msgs)} | {meta.get('caller')} | Failed | — | — | failed |"
            )

    payload = {
        "generated_at": ts,
        "lookback_days": LOOKBACK_DAYS,
        "vm_folder": vm_folder,
        "since_last_batch": since_last_batch,
        "skipped_prior_count": skipped_prior,
        "dry_run": dry_run,
        "candidate_count": len(messages),
        "group_count": len(grouped),
        "results": [r.__dict__ for r in results],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest = OUT_DIR / "outlook-batch-latest.json"
    latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    routed = sum(1 for r in results if r.forward and "@" in r.forward)
    failed = sum(1 for r in results if r.error or r.forward.startswith("failed"))
    print()
    print(
        f"**Counts:** {len(messages)} candidates | {len(grouped)} groups | "
        f"{routed} routed | {failed} failed | dry_run={dry_run}"
    )
    print(f"**Report:** {out_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
