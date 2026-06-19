#!/usr/bin/env python3
"""Summarize unread inbox items needing Crystal's response."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_CACHE = Path(__file__).resolve().parents[4] / ".cursor" / "bin" / "ms365-mcp" / "node_modules" / "@softeria" / "ms-365-mcp-server" / ".token-cache.json"
CLIENT_ID = "084a3e9f-a9f4-43f7-89f9-d229cf97853e"
TENANT_ID = "6971e9a1-0270-4452-ac45-b5023dc57b1b"
MY = {"crystal.gagner@vixxo.com"}


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
        url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    return payload["access_token"]


def load_access_token() -> str:
    data = _cache_data()
    for val in data.get("AccessToken", {}).values():
        if val.get("secret") and int(val.get("expires_on", 0)) > time.time() + 60:
            return val["secret"]
    refresh = next(iter((data.get("RefreshToken") or {}).values()), {}).get("secret")
    if refresh:
        return _refresh_token(refresh)
    raise RuntimeError("re-auth required")


def graph_get(path: str, token: str) -> dict:
    url = path if path.startswith("http") else f"https://graph.microsoft.com/v1.0{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def sender(msg: dict) -> str:
    return ((msg.get("from") or {}).get("emailAddress") or {}).get("address", "").lower()


def is_fyi(msg: dict) -> bool:
    subj = (msg.get("subject") or "").lower()
    frm = sender(msg)
    preview = (msg.get("bodyPreview") or "").lower()
    if frm in MY:
        return True
    fyi = [
        r"^canceled:",
        r"^accepted:",
        r"^declined:",
        r"^automatic reply",
        r"^undeliverable",
        r"new sign-in method",
        r"windows hello",
        r"here is the template",
        r"^re: sps catch up",
    ]
    if any(re.search(p, subj) for p in fyi):
        return True
    if "put all of this in an email" in preview and "salesforce-related requests" in preview:
        return True
    return False


def tag(msg: dict) -> str:
    subj = (msg.get("subject") or "").lower()
    preview = (msg.get("bodyPreview") or "").lower()
    if msg.get("importance") in ("high", "urgent") or "urgent" in subj:
        return "urgent"
    if "confirm" in preview or "please advise" in preview or "following up" in preview:
        return "today"
    if msg.get("flag") and (msg.get("flag") or {}).get("flagStatus") == "flagged":
        return "this-week"
    return "this-week"


def main() -> None:
    token = load_access_token()
    select = "id,subject,from,receivedDateTime,bodyPreview,isRead,importance,hasAttachments,flag,conversationId"
    path = "/me/mailFolders/inbox/messages?" + urllib.parse.urlencode(
        {"$filter": "isRead eq false", "$select": select, "$top": "50", "$orderby": "receivedDateTime desc"}
    )
    data = graph_get(path, token)
    unread = data.get("value") or []

    actionable = []
    fyi = []
    for msg in unread:
        item = {
            "subject": msg.get("subject"),
            "from_name": ((msg.get("from") or {}).get("emailAddress") or {}).get("name"),
            "from_email": sender(msg),
            "received": msg.get("receivedDateTime"),
            "importance": msg.get("importance"),
            "preview": (msg.get("bodyPreview") or "")[:280],
            "attachments": msg.get("hasAttachments"),
            "flagged": ((msg.get("flag") or {}).get("flagStatus") == "flagged"),
            "queue": tag(msg),
        }
        if is_fyi(msg):
            fyi.append(item)
        else:
            actionable.append(item)

    print(json.dumps({"unread_total": len(unread), "actionable_unread": actionable, "fyi_unread": fyi}, indent=2))


if __name__ == "__main__":
    main()
