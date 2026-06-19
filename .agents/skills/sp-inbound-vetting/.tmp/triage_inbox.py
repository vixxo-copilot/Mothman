#!/usr/bin/env python3
"""Triage Crystal Gagner inbox via Microsoft Graph (cached MS365 MCP token)."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN_CACHE = Path(__file__).resolve().parents[4] / ".cursor" / "bin" / "ms365-mcp" / "node_modules" / "@softeria" / "ms-365-mcp-server" / ".token-cache.json"
CLIENT_ID = "084a3e9f-a9f4-43f7-89f9-d229cf97853e"
TENANT_ID = "6971e9a1-0270-4452-ac45-b5023dc57b1b"
MY_EMAILS = {"crystal.gagner@vixxo.com", "Crystal.Gagner@vixxo.com"}


def _cache_data() -> dict:
    raw = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
    return json.loads(raw["data"])


def _refresh_token(refresh_token: str) -> str:
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "scope": "https://graph.microsoft.com/.default offline_access",
        }
    ).encode()
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token refresh failed: {payload}")
    return token


def load_access_token() -> str:
    data = _cache_data()
    for val in data.get("AccessToken", {}).values():
        secret = val.get("secret")
        expires = int(val.get("expires_on", 0))
        if secret and expires > time.time() + 60:
            return secret
    refresh_entries = data.get("RefreshToken") or {}
    if refresh_entries:
        refresh = next(iter(refresh_entries.values())).get("secret")
        if refresh:
            return _refresh_token(refresh)
    raise RuntimeError("No valid access token in cache; re-auth MS365 MCP required")


def graph_get(path: str, token: str) -> dict:
    url = path if path.startswith("http") else f"https://graph.microsoft.com/v1.0{path}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def sender_email(msg: dict) -> str:
    frm = (msg.get("from") or {}).get("emailAddress") or {}
    return (frm.get("address") or "").lower()


def is_noise(msg: dict) -> bool:
    subj = (msg.get("subject") or "").lower()
    sender = sender_email(msg)
    preview = (msg.get("bodyPreview") or "").lower()
    noise_patterns = [
        r"^automatic reply",
        r"^undeliverable",
        r"^delivery status notification",
        r"^read:",
        r"teams?$",
        r"notification",
        r"newsletter",
        r"github",
        r"cursor",
        r"meraki",
        r"no-reply",
        r"noreply",
        r"donotreply",
        r"mailer-daemon",
    ]
    if any(re.search(p, subj) for p in noise_patterns):
        return True
    if any(x in sender for x in ("noreply", "no-reply", "donotreply", "notifications")):
        return True
    if "trying to reach you" in preview and "teams" in sender:
        return True
    return False


def needs_response(msg: dict) -> bool:
    if is_noise(msg):
        return False
    subj = (msg.get("subject") or "").lower()
    preview = (msg.get("bodyPreview") or "").lower()
    importance = msg.get("importance", "normal")
    if msg.get("flag") and (msg.get("flag") or {}).get("flagStatus") == "flagged":
        return True
    if importance in ("high", "urgent"):
        return True
    ask_signals = [
        r"\?",
        r"\bplease\b",
        r"\bcan you\b",
        r"\bcould you\b",
        r"\bneed\b",
        r"\bhelp\b",
        r"\basap\b",
        r"\burgent\b",
        r"\bfollow up\b",
        r"\bwaiting\b",
        r"\bconfirm\b",
        r"\bapprove\b",
        r"\blet me know\b",
        r"\breply\b",
        r"\bwhen can\b",
    ]
    text = f"{subj} {preview}"
    return any(re.search(p, text, re.I) for p in ask_signals)


def slim(msg: dict) -> dict:
    frm = (msg.get("from") or {}).get("emailAddress") or {}
    return {
        "id": msg.get("id"),
        "subject": msg.get("subject"),
        "from_name": frm.get("name"),
        "from_email": frm.get("address"),
        "received": msg.get("receivedDateTime"),
        "isRead": msg.get("isRead"),
        "importance": msg.get("importance"),
        "hasAttachments": msg.get("hasAttachments"),
        "preview": (msg.get("bodyPreview") or "")[:320],
        "conversationId": msg.get("conversationId"),
        "flagged": ((msg.get("flag") or {}).get("flagStatus") == "flagged"),
    }


def fetch_messages(token: str, path: str, max_pages: int = 3) -> list[dict]:
    items: list[dict] = []
    url = path
    pages = 0
    while url and pages < max_pages:
        data = graph_get(url, token)
        items.extend(data.get("value") or [])
        url = data.get("@odata.nextLink")
        pages += 1
    return items


def main() -> None:
    token = load_access_token()
    select = "id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,importance,conversationId,flag,toRecipients,ccRecipients"

    unread_path = (
        "/me/mailFolders/inbox/messages?"
        + urllib.parse.urlencode(
            {
                "$filter": "isRead eq false",
                "$select": select,
                "$top": "50",
                "$orderby": "receivedDateTime desc",
            }
        )
    )
    unread = fetch_messages(token, unread_path, max_pages=2)

    flagged_path = (
        "/me/messages?"
        + urllib.parse.urlencode(
            {
                "$filter": "flag/flagStatus eq 'flagged'",
                "$select": select,
                "$top": "25",
            }
        )
    )
    flagged = fetch_messages(token, flagged_path, max_pages=2)

    # Recent read inbox (last 3 days) for threads user may not have answered
    recent_path = (
        "/me/mailFolders/inbox/messages?"
        + urllib.parse.urlencode(
            {
                "$filter": "receivedDateTime ge 2026-06-14T00:00:00Z",
                "$select": select,
                "$top": "40",
                "$orderby": "receivedDateTime desc",
            }
        )
    )
    recent = fetch_messages(token, recent_path, max_pages=2)

    seen_ids: set[str] = set()
    candidates: list[dict] = []
    for msg in unread + flagged + recent:
        mid = msg.get("id")
        if not mid or mid in seen_ids:
            continue
        seen_ids.add(mid)
        if needs_response(msg):
            candidates.append(msg)

    candidates.sort(key=lambda m: m.get("receivedDateTime") or "", reverse=True)

    # Dedupe by conversation — keep newest per thread
    by_conv: dict[str, dict] = {}
    for msg in candidates:
        cid = msg.get("conversationId") or msg.get("id")
        if cid not in by_conv:
            by_conv[cid] = msg

    threads = sorted(by_conv.values(), key=lambda m: m.get("receivedDateTime") or "", reverse=True)

    out = {
        "mailbox": "Crystal.Gagner@vixxo.com",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "unread_inbox_count": len(unread),
        "flagged_count": len(flagged),
        "actionable_threads": [slim(m) for m in threads[:25]],
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
