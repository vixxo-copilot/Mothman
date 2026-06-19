#!/usr/bin/env python3
"""Scan inbox for urgent/high-importance items."""
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


def _cache_data() -> dict:
    return json.loads(json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))["data"])


def _refresh_token(refresh_token: str) -> str:
    body = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": CLIENT_ID,
         "scope": "https://graph.microsoft.com/.default offline_access"}
    ).encode()
    req = urllib.request.Request(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())["access_token"]


def load_access_token() -> str:
    data = _cache_data()
    for val in data.get("AccessToken", {}).values():
        if val.get("secret") and int(val.get("expires_on", 0)) > time.time() + 60:
            return val["secret"]
    refresh = next(iter((data.get("RefreshToken") or {}).values()), {}).get("secret")
    return _refresh_token(refresh)


def graph_get(path: str, token: str) -> dict:
    url = path if path.startswith("http") else f"https://graph.microsoft.com/v1.0{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def slim(msg: dict) -> dict:
    frm = (msg.get("from") or {}).get("emailAddress") or {}
    return {
        "subject": msg.get("subject"),
        "from": frm.get("name"),
        "email": frm.get("address"),
        "received": msg.get("receivedDateTime"),
        "isRead": msg.get("isRead"),
        "importance": msg.get("importance"),
        "preview": (msg.get("bodyPreview") or "")[:240],
        "attachments": msg.get("hasAttachments"),
    }


def main() -> None:
    token = load_access_token()
    select = "subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,importance,flag"

    unread = graph_get(
        "/me/mailFolders/inbox/messages?"
        + urllib.parse.urlencode({"$filter": "isRead eq false", "$select": select, "$top": "50", "$orderby": "receivedDateTime desc"}),
        token,
    ).get("value", [])

    flagged = graph_get(
        "/me/messages?" + urllib.parse.urlencode({"$filter": "flag/flagStatus eq 'flagged'", "$select": select, "$top": "50"}),
        token,
    ).get("value", [])

    urgent = []
    for msg in unread + flagged:
        subj = (msg.get("subject") or "").lower()
        preview = (msg.get("bodyPreview") or "").lower()
        imp = msg.get("importance", "normal")
        is_flag = (msg.get("flag") or {}).get("flagStatus") == "flagged"
        score = 0
        if imp in ("high", "urgent"):
            score += 3
        if re.search(r"\burgent\b|\basap\b|\bimmediate\b|\bp1\b|\bp2\b", subj + " " + preview):
            score += 2
        if "confirm" in preview and "please" in preview:
            score += 1
        if score >= 2:
            item = slim(msg)
            item["score"] = score
            item["flagged"] = is_flag
            urgent.append(item)

    # dedupe by subject+received
    seen = set()
    deduped = []
    for item in sorted(urgent, key=lambda x: (-x["score"], x["received"] or ""), reverse=False):
        key = (item["subject"], item["email"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    print(json.dumps({"unread_count": len(unread), "urgent_items": deduped[:15]}, indent=2))


if __name__ == "__main__":
    main()
