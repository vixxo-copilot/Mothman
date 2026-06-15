"""Download Freshdesk ticket attachments for the VIXXO-coi-review skill.

Reads ``FRESHDESK_DOMAIN`` and ``FRESHDESK_API_KEY`` from the environment
(the same credentials the Freshdesk MCP server uses — see
``.cursor/mcp.json``), pulls a Freshdesk ticket plus its conversation
history, walks every attachment on the ticket and on each conversation
entry, downloads the binaries to a local working directory, and writes a
manifest JSON the agent can read.

The agent's ``Read`` tool auto-converts downloaded PDFs to text and
supports common image formats (PNG/JPG/GIF/WEBP), so once attachments are
on disk the COI fields can be extracted without any extra parsing here.

Usage
-----
    python fetch_coi_attachments.py --ticket-id 12345
    python fetch_coi_attachments.py --ticket-id 12345 --out-dir .tmp/coi/12345

Env
---
    FRESHDESK_DOMAIN   e.g. vixxo-helpdesk.freshdesk.com  (no scheme)
    FRESHDESK_API_KEY  Freshdesk personal API key

Output
------
Writes:
    <out-dir>/manifest.json           — ticket metadata + attachment index
    <out-dir>/<filename>              — each downloaded attachment

Prints (last line, parseable):
    MANIFEST: <absolute path to manifest.json>

Stdlib only — no pip dependencies.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30
USER_AGENT = "vixxo-coi-review/1.0 (+stdlib)"
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._\-]+")


def _die(message: str, *, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def _basic_auth_header(api_key: str) -> str:
    raw = f"{api_key}:X".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _http_get_json(url: str, headers: dict[str, str]) -> Any:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        _die(f"GET {url} failed with HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        _die(f"GET {url} failed: {exc.reason}")
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        _die(f"Could not parse JSON from {url}: {exc}")


def _http_get_bytes(url: str, headers: dict[str, str]) -> bytes:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        _die(f"GET {url} failed with HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        _die(f"GET {url} failed: {exc.reason}")


def _safe_filename(name: str, fallback: str) -> str:
    base = os.path.basename(name or "").strip()
    if not base:
        base = fallback
    base = SAFE_FILENAME_RE.sub("_", base)
    return base[:200] or fallback


def _normalise_attachment(att: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "id": att.get("id"),
        "name": att.get("name"),
        "content_type": att.get("content_type"),
        "size": att.get("size"),
        "created_at": att.get("created_at"),
        "attachment_url": att.get("attachment_url"),
        "source": source,
    }


def _collect_attachments(ticket: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for att in ticket.get("attachments") or []:
        out.append(_normalise_attachment(att, source="ticket"))
    for conv in ticket.get("conversations") or []:
        conv_id = conv.get("id")
        for att in conv.get("attachments") or []:
            out.append(_normalise_attachment(att, source=f"conv:{conv_id}"))
    return out


def _ensure_unique(out_dir: Path, filename: str) -> Path:
    candidate = out_dir / filename
    if not candidate.exists():
        return candidate
    stem, ext = os.path.splitext(filename)
    n = 1
    while True:
        candidate = out_dir / f"{stem}__{n}{ext}"
        if not candidate.exists():
            return candidate
        n += 1


def _download_attachments(
    attachments: list[dict[str, Any]], out_dir: Path
) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[dict[str, Any]] = []
    for att in attachments:
        url = att.get("attachment_url")
        if not url:
            saved.append({**att, "saved_path": None, "error": "no attachment_url"})
            continue
        fallback = f"attachment_{att.get('id') or len(saved)}"
        filename = _safe_filename(att.get("name") or "", fallback=fallback)
        target = _ensure_unique(out_dir, filename)
        try:
            blob = _http_get_bytes(url, headers={"User-Agent": USER_AGENT})
            target.write_bytes(blob)
            saved.append(
                {
                    **att,
                    "saved_path": str(target),
                    "saved_bytes": len(blob),
                    "error": None,
                }
            )
        except SystemExit:
            saved.append(
                {**att, "saved_path": None, "error": f"download failed for {url}"}
            )
    return saved


def _conversation_summary(conv: dict[str, Any]) -> dict[str, Any]:
    body = (conv.get("body_text") or conv.get("body") or "").strip()
    if len(body) > 4000:
        body = body[:4000] + "\n\n[…truncated to 4000 chars…]"
    return {
        "id": conv.get("id"),
        "incoming": conv.get("incoming"),
        "private": conv.get("private"),
        "from_email": conv.get("from_email"),
        "to_emails": conv.get("to_emails"),
        "cc_emails": conv.get("cc_emails"),
        "created_at": conv.get("created_at"),
        "user_id": conv.get("user_id"),
        "body_text_preview": body,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download Freshdesk ticket attachments for COI review.",
    )
    parser.add_argument(
        "--ticket-id",
        type=int,
        required=True,
        help="Freshdesk ticket ID (numeric).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory (default: .tmp/coi-review/<ticket-id>/).",
    )
    parser.add_argument(
        "--no-conversations",
        action="store_true",
        help="Skip pulling conversation history (faster but misses attachments on replies).",
    )
    args = parser.parse_args(argv)

    domain = os.environ.get("FRESHDESK_DOMAIN", "").strip()
    api_key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    if not domain:
        _die(
            "FRESHDESK_DOMAIN not set. Expected something like "
            "'vixxo-helpdesk.freshdesk.com'. See .cursor/mcp.json for the value "
            "this workspace already uses with the Freshdesk MCP."
        )
    if not api_key:
        _die("FRESHDESK_API_KEY not set. Pull from .cursor/mcp.json or your Freshdesk profile.")

    out_dir = (
        Path(args.out_dir).resolve()
        if args.out_dir
        else Path(".tmp/coi-review") / str(args.ticket_id)
    ).resolve()

    headers = {
        "Authorization": _basic_auth_header(api_key),
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    base = f"https://{domain}/api/v2"
    ticket_url = f"{base}/tickets/{args.ticket_id}"
    if not args.no_conversations:
        ticket_url += "?include=conversations"
    ticket = _http_get_json(ticket_url, headers=headers)

    requester_id = ticket.get("requester_id")
    requester: dict[str, Any] = {}
    if requester_id:
        try:
            requester = _http_get_json(f"{base}/contacts/{requester_id}", headers=headers)
        except SystemExit:
            requester = {"id": requester_id, "error": "lookup failed"}

    attachments = _collect_attachments(ticket)
    saved = _download_attachments(attachments, out_dir)

    conversations = [_conversation_summary(c) for c in (ticket.get("conversations") or [])]

    manifest = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "freshdesk_domain": domain,
        "ticket": {
            "id": ticket.get("id"),
            "subject": ticket.get("subject"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "group_id": ticket.get("group_id"),
            "responder_id": ticket.get("responder_id"),
            "tags": ticket.get("tags"),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at"),
            "url": f"https://{domain}/a/tickets/{ticket.get('id')}",
            "description_text": (ticket.get("description_text") or "")[:8000],
            "to_emails": ticket.get("to_emails"),
            "cc_emails": ticket.get("cc_emails"),
            "fr_escalated": ticket.get("fr_escalated"),
            "spam": ticket.get("spam"),
        },
        "requester": {
            "id": requester.get("id"),
            "name": requester.get("name"),
            "email": requester.get("email"),
            "company_id": requester.get("company_id"),
        },
        "conversations": conversations,
        "attachments": [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "content_type": s.get("content_type"),
                "size": s.get("size"),
                "source": s.get("source"),
                "saved_path": s.get("saved_path"),
                "saved_bytes": s.get("saved_bytes"),
                "error": s.get("error"),
            }
            for s in saved
        ],
        "summary": {
            "attachments_total": len(saved),
            "attachments_saved": sum(1 for s in saved if s.get("saved_path")),
            "attachments_failed": sum(1 for s in saved if not s.get("saved_path")),
        },
    }

    manifest_path = out_dir / "manifest.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Ticket {ticket.get('id')}: {ticket.get('subject')}")
    print(f"  Requester:    {requester.get('name')} <{requester.get('email')}>")
    print(f"  Conversations: {len(conversations)}")
    print(
        "  Attachments:  "
        f"{manifest['summary']['attachments_saved']} saved, "
        f"{manifest['summary']['attachments_failed']} failed"
    )
    for s in saved:
        path = s.get("saved_path") or "(failed)"
        print(f"    - {s.get('name')!r} [{s.get('content_type')}] -> {path}")
    print(f"MANIFEST: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
