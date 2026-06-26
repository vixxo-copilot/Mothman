#!/usr/bin/env python3
"""Sync Freshdesk ticket attachments to a Salesforce Case.

Downloads FD attachments (ticket + conversations), applies a retention policy,
and uploads via Salesforce CLI (`sf data create file`).

Usage
-----
    python sync_attachments_to_sf.py --fd-ticket-id 57142 --sf-case-number 00005739
    python sync_attachments_to_sf.py --fd-ticket-id 57142 --sf-case-id 500TS00000nNAvbYAG --dry-run

Env: FRESHDESK_DOMAIN, FRESHDESK_API_KEY (same as Freshdesk MCP)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TMP = SKILL_DIR / ".tmp"

DEFAULT_TIMEOUT = 30
USER_AGENT = "sp-fd-sf-duplicate-bridge/1.0"


def _die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _basic_auth(api_key: str) -> str:
    return "Basic " + base64.b64encode(f"{api_key}:X".encode()).decode()


def _load_fd_creds() -> tuple[str, str]:
    domain = os.environ.get("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com").strip()
    api_key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    token_path = Path.home() / ".vixxo" / "freshdesk_token"
    if not api_key and token_path.is_file():
        api_key = token_path.read_text(encoding="utf-8").strip()
    if not api_key:
        _die("FRESHDESK_API_KEY not set and ~/.vixxo/freshdesk_token missing")
    return domain, api_key


def _http_json(url: str, headers: dict[str, str]) -> dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _fetch_ticket(domain: str, api_key: str, ticket_id: int) -> dict:
    headers = {"Authorization": _basic_auth(api_key), "User-Agent": USER_AGENT}
    url = f"https://{domain}/api/v2/tickets/{ticket_id}?include=conversations"
    return _http_json(url, headers)


def _fetch_conversations(domain: str, api_key: str, ticket_id: int) -> list[dict]:
    headers = {"Authorization": _basic_auth(api_key), "User-Agent": USER_AGENT}
    url = f"https://{domain}/api/v2/tickets/{ticket_id}/conversations"
    try:
        return _http_json(url, headers)
    except urllib.error.HTTPError:
        return []


def _norm_att(att: dict, source: str) -> dict:
    return {
        "id": att.get("id"),
        "name": att.get("name"),
        "content_type": att.get("content_type"),
        "size": att.get("size"),
        "attachment_url": att.get("attachment_url"),
        "source": source,
    }


def select_attachments(
    ticket: dict,
    conversations: list[dict],
    policy: str,
    include_original_packet: bool,
) -> list[dict]:
    out: list[dict] = []
    seen_ids: set[int] = set()

    def add(att: dict, source: str) -> None:
        aid = att.get("id")
        if aid is not None and aid in seen_ids:
            return
        if aid is not None:
            seen_ids.add(aid)
        out.append(_norm_att(att, source))

    if policy == "full":
        for att in ticket.get("attachments") or []:
            add(att, "ticket")
        for conv in conversations:
            for att in conv.get("attachments") or []:
                add(att, f"conv:{conv.get('id')}")
        return out

    if policy == "latest-reply-only":
        include_original_packet = False

    if include_original_packet and policy in ("ks-onboarding-reply", "latest-reply-only"):
        for att in ticket.get("attachments") or []:
            add(att, "ticket")

    if policy in ("ks-onboarding-reply", "latest-reply-only"):
        convs = sorted(
            conversations,
            key=lambda c: c.get("created_at") or "",
            reverse=True,
        )
        for conv in convs:
            if not conv.get("incoming"):
                continue
            atts = conv.get("attachments") or []
            if not atts:
                continue
            for att in atts:
                add(att, f"conv:{conv.get('id')}")
            break

    return out


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _safe_name(name: str, fallback: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._\-]+", "_", os.path.basename(name or fallback))
    return base[:200] or fallback


def _resolve_sf_cmd() -> str:
    npm_sf = Path(os.environ.get("APPDATA", "")) / "npm" / "sf.cmd"
    if npm_sf.is_file():
        return str(npm_sf)
    found = shutil.which("sf")
    if found:
        return found
    _die("Salesforce CLI (sf) not found on PATH or %APPDATA%\\npm\\sf.cmd")


def _sf_case_id(case_number: str | None, case_id: str | None, sf_cmd: str, org: str) -> str:
    if case_id:
        return case_id
    if not case_number:
        _die("Provide --sf-case-id or --sf-case-number")
    q = (
        "SELECT Id FROM Case WHERE CaseNumber = "
        f"'{case_number.lstrip('#')}' LIMIT 1"
    )
    proc = subprocess.run(
        [sf_cmd, "data", "query", "--query", q, "--target-org", org, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        _die(f"SF Case lookup failed: {proc.stderr or proc.stdout}")
    data = json.loads(proc.stdout)
    records = (data.get("result") or {}).get("records") or []
    if not records:
        _die(f"No Case found for CaseNumber {case_number}")
    return records[0]["Id"]


def _existing_titles(case_id: str, sf_cmd: str, org: str) -> dict[str, int]:
    q = (
        "SELECT ContentDocument.Title, ContentDocument.ContentSize "
        f"FROM ContentDocumentLink WHERE LinkedEntityId = '{case_id}'"
    )
    proc = subprocess.run(
        [sf_cmd, "data", "query", "--query", q, "--target-org", org, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {}
    data = json.loads(proc.stdout)
    out: dict[str, int] = {}
    for rec in (data.get("result") or {}).get("records") or []:
        doc = rec.get("ContentDocument") or {}
        title = doc.get("Title")
        size = doc.get("ContentSize")
        if title is not None and size is not None:
            out[title] = int(size)
    return out


def _upload_file(path: Path, title: str, case_id: str, sf_cmd: str, org: str) -> dict:
    proc = subprocess.run(
        [
            sf_cmd,
            "data",
            "create",
            "file",
            "--file",
            str(path),
            "--parent-id",
            case_id,
            "--title",
            title,
            "--target-org",
            org,
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr or proc.stdout}
    payload = json.loads(proc.stdout)
    return {"ok": True, "result": payload.get("result")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fd-ticket-id", type=int, required=True)
    parser.add_argument("--sf-case-id", type=str, default=None)
    parser.add_argument("--sf-case-number", type=str, default=None)
    parser.add_argument(
        "--policy",
        choices=("ks-onboarding-reply", "full", "latest-reply-only"),
        default="ks-onboarding-reply",
    )
    parser.add_argument(
        "--include-original-packet",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--target-org", default="vixxo")
    parser.add_argument("--out-dir", type=str, default=None)
    args = parser.parse_args(argv)

    domain, api_key = _load_fd_creds()
    ticket = _fetch_ticket(domain, api_key, args.fd_ticket_id)
    conversations = ticket.get("conversations")
    if conversations is None:
        conversations = _fetch_conversations(domain, api_key, args.fd_ticket_id)

    selected = select_attachments(
        ticket,
        conversations,
        args.policy,
        args.include_original_packet,
    )
    if not selected:
        print("No attachments selected for policy.")
        return 0

    out_dir = Path(args.out_dir) if args.out_dir else TMP / f"sync-{args.fd_ticket_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    sf_cmd = _resolve_sf_cmd()
    case_id = _sf_case_id(args.sf_case_number, args.sf_case_id, sf_cmd, args.target_org)
    existing = _existing_titles(case_id, sf_cmd, args.target_org) if args.skip_existing else {}

    results: list[dict] = []
    for att in selected:
        title = att.get("name") or f"attachment_{att.get('id')}"
        size = att.get("size")
        if args.skip_existing and title in existing and existing[title] == size:
            results.append({"title": title, "action": "skipped", "reason": "already on case"})
            continue
        url = att.get("attachment_url")
        if not url:
            results.append({"title": title, "action": "failed", "reason": "no attachment_url"})
            continue
        local = out_dir / _safe_name(title, f"att_{att.get('id')}")
        if args.dry_run:
            results.append(
                {
                    "title": title,
                    "action": "dry-run",
                    "source": att.get("source"),
                    "size": size,
                }
            )
            continue
        try:
            local.write_bytes(_download(url))
        except Exception as exc:  # noqa: BLE001
            results.append({"title": title, "action": "failed", "reason": str(exc)})
            continue
        up = _upload_file(local, title, case_id, sf_cmd, args.target_org)
        if up.get("ok"):
            results.append(
                {
                    "title": title,
                    "action": "uploaded",
                    "content_document_id": (up.get("result") or {}).get("ContentDocumentId"),
                }
            )
        else:
            results.append({"title": title, "action": "failed", "reason": up.get("error")})

    summary = {
        "fd_ticket_id": args.fd_ticket_id,
        "sf_case_id": case_id,
        "sf_case_number": args.sf_case_number,
        "policy": args.policy,
        "include_original_packet": args.include_original_packet,
        "dry_run": args.dry_run,
        "results": results,
    }
    report_path = out_dir / "sync-report.json"
    if not args.dry_run:
        report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    uploaded = sum(1 for r in results if r.get("action") == "uploaded")
    skipped = sum(1 for r in results if r.get("action") == "skipped")
    failed = sum(1 for r in results if r.get("action") == "failed")
    print(
        f"FD #{args.fd_ticket_id} -> SF Case {case_id}: "
        f"{uploaded} uploaded, {skipped} skipped, {failed} failed"
    )
    for r in results:
        print(f"  - {r.get('title')}: {r.get('action')} {r.get('reason') or ''}".rstrip())
    if not args.dry_run:
        print(f"REPORT: {report_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
