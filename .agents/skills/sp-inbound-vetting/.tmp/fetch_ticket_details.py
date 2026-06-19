#!/usr/bin/env python3
"""Fetch detail for priority Freshdesk tickets."""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request
from html import unescape
from pathlib import Path

TICKET_IDS = [40938, 33370, 46743, 36120, 35389, 32767, 54479, 53949, 49246, 48736]


def get_token() -> str:
    for src in (os.environ.get("FRESHDESK_API_KEY", ""), os.environ.get("FRESHDESK_TOKEN", "")):
        if src.strip():
            return src.strip()
    return Path.home().joinpath(".vixxo", "freshdesk_token").read_text(encoding="ascii").strip()


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    token = get_token()
    domain = os.environ.get("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com")
    auth = base64.b64encode(f"{token}:X".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

    out = []
    for tid in TICKET_IDS:
        url = f"https://{domain}/api/v2/tickets/{tid}?include=conversations,requester"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            t = json.loads(resp.read().decode())
        convs = t.get("conversations") or []
        public = [c for c in convs if not c.get("private")]
        latest = public[-1] if public else (convs[-1] if convs else None)
        out.append(
            {
                "id": tid,
                "subject": t.get("subject"),
                "description_snip": strip_html(t.get("description_text") or t.get("description") or "")[:400],
                "latest_note": strip_html((latest or {}).get("body_text") or (latest or {}).get("body") or "")[:500]
                if latest
                else None,
                "latest_at": (latest or {}).get("created_at"),
                "latest_private": (latest or {}).get("private"),
                "requester": (t.get("requester") or {}).get("email"),
            }
        )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
