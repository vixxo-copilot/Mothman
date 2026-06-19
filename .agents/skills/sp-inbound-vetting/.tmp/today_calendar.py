#!/usr/bin/env python3
"""Today's calendar events via Graph."""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN_CACHE = Path(__file__).resolve().parents[4] / ".cursor" / "bin" / "ms365-mcp" / "node_modules" / "@softeria" / "ms-365-mcp-server" / ".token-cache.json"
CLIENT_ID = "084a3e9f-a9f4-43f7-89f9-d229cf97853e"
TENANT_ID = "6971e9a1-0270-4452-ac45-b5023dc57b1b"


def load_access_token() -> str:
    data = json.loads(json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))["data"])
    for val in data.get("AccessToken", {}).values():
        if val.get("secret") and int(val.get("expires_on", 0)) > time.time() + 60:
            return val["secret"]
    refresh = next(iter((data.get("RefreshToken") or {}).values()), {}).get("secret")
    body = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": refresh, "client_id": CLIENT_ID,
         "scope": "https://graph.microsoft.com/.default offline_access"}
    ).encode()
    req = urllib.request.Request(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())["access_token"]


def main() -> None:
    token = load_access_token()
    start = "2026-06-18T00:00:00"
    end = "2026-06-19T00:00:00"
    path = (
        f"/me/calendarView?startDateTime={start}&endDateTime={end}"
        + "&" + urllib.parse.urlencode({"$select": "subject,start,end,isAllDay,showAs,location,organizer", "$orderby": "start/dateTime", "$top": "30"})
    )
    req = urllib.request.Request(
        f"https://graph.microsoft.com/v1.0{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "Prefer": 'outlook.timezone="Central Standard Time"'},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        events = json.loads(resp.read().decode()).get("value", [])
    out = []
    for e in events:
        org = ((e.get("organizer") or {}).get("emailAddress") or {}).get("name")
        out.append({
            "subject": e.get("subject"),
            "start": (e.get("start") or {}).get("dateTime"),
            "end": (e.get("end") or {}).get("dateTime"),
            "showAs": e.get("showAs"),
            "location": (e.get("location") or {}).get("displayName"),
            "organizer": org,
        })
    print(json.dumps({"date": "2026-06-18", "events": out}, indent=2))


if __name__ == "__main__":
    main()
