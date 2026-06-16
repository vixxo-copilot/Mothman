#!/usr/bin/env python3
"""List open KSOnboarding Freshdesk tickets for sp-voicemail-triage batch runs."""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

QUERY = "group_id:159000485013 AND status:2 AND type:'KSOnboarding'"
DOMAIN = "vixxo-helpdesk.freshdesk.com"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and val and not os.environ.get(key):
            os.environ[key] = val


def load_secret(path: Path, target: str) -> None:
    if os.environ.get(target) or not path.is_file():
        return
    secret = path.read_text(encoding="utf-8").strip()
    if secret:
        os.environ[target] = secret


def auth_headers(api_key: str) -> dict[str, str]:
    token = base64.b64encode(f"{api_key}:X".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def search_tickets(api_key: str, query: str) -> list[dict]:
    url = (
        f"https://{DOMAIN}/api/v2/search/tickets?"
        + urllib.parse.urlencode({"query": f'"{query}"'})
    )
    req = urllib.request.Request(url, headers=auth_headers(api_key), method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data.get("results") or []


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    load_env_file(root / ".env")
    home = Path.home() / ".vixxo"
    load_secret(home / "freshdesk_token", "FRESHDESK_API_KEY")
    load_secret(home / "freshdesk_api_key", "FRESHDESK_API_KEY")
    if not os.environ.get("FRESHDESK_API_KEY") and os.environ.get("FRESHDESK_TOKEN"):
        os.environ["FRESHDESK_API_KEY"] = os.environ["FRESHDESK_TOKEN"]

    api_key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    if not api_key:
        print(
            "ERROR: FRESHDESK_API_KEY not configured (.env or ~/.vixxo/freshdesk_token)",
            file=sys.stderr,
        )
        return 2

    try:
        tickets = search_tickets(api_key, QUERY)
    except urllib.error.HTTPError as exc:
        print(f"ERROR: Freshdesk search failed HTTP {exc.code}", file=sys.stderr)
        return 1

    print(json.dumps({"count": len(tickets), "tickets": tickets}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
