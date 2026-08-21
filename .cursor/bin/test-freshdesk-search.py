#!/usr/bin/env python3
"""Reproduce Freshdesk search API quoting behavior (no MCP)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def load_credentials() -> tuple[str, str]:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    if env_path.is_file():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and not os.environ.get(key):
                os.environ[key] = val

    home = Path.home() / ".vixxo"
    for name in ("freshdesk_token", "freshdesk_api_key"):
        path = home / name
        if not os.environ.get("FRESHDESK_API_KEY") and path.is_file():
            os.environ["FRESHDESK_API_KEY"] = path.read_text(encoding="utf-8").strip()

    api_key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    domain = os.environ.get("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com").strip()
    if not api_key:
        print("FRESHDESK_API_KEY not configured", file=sys.stderr)
        sys.exit(1)
    return api_key, domain


def search(domain: str, api_key: str, query_value: str, page: int = 1) -> tuple[int, object]:
    params = {"query": query_value, "page": str(page)}
    url = f"https://{domain}/api/v2/search/tickets?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Basic {__import__('base64').b64encode(f'{api_key}:X'.encode()).decode()}",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = body
        return exc.code, data


def main() -> int:
    api_key, domain = load_credentials()
    cases = [
        ("unquoted (MCP default)", "status:2"),
        ("quoted (skill scripts)", '"status:2"'),
        ("date unquoted", "created_at:>'2026-06-24'"),
        ("date quoted", '"created_at:>\'2026-06-24\'"'),
        ("group unquoted", "group_id:159000485013 AND status:2"),
        ("group quoted", '"group_id:159000485013 AND status:2"'),
    ]
    for label, query in cases:
        status, data = search(domain, api_key, query)
        count = len(data.get("results", [])) if isinstance(data, dict) else "n/a"
        print(f"{label}: HTTP {status} results={count}")
        if status != 200:
            print(f"  error: {json.dumps(data)[:300]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
