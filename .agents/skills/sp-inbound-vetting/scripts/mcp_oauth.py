#!/usr/bin/env python3
"""Read mcp-remote OAuth tokens cached by Cursor / npx mcp-remote."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def server_url_hash(server_url: str, headers: dict[str, str] | None = None) -> str:
    """Match mcp-remote getServerUrlHash (md5 of url [| headers-json])."""
    parts = [server_url]
    if headers:
        sorted_keys = sorted(headers)
        parts.append(json.dumps(headers, sort_keys=True))
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def oauth_access_token(server_url: str, headers: dict[str, str] | None = None) -> str | None:
    """Return cached OAuth access_token for a remote MCP URL, if present."""
    base = Path(os.environ.get("MCP_REMOTE_CONFIG_DIR", Path.home() / ".mcp-auth"))
    if not base.is_dir():
        return None

    url_hash = server_url_hash(server_url, headers)
    tokens_name = f"{url_hash}_tokens.json"

    version_dirs = sorted(
        (p for p in base.iterdir() if p.is_dir() and p.name.startswith("mcp-remote-")),
        reverse=True,
    )
    for version_dir in version_dirs:
        tokens_path = version_dir / tokens_name
        if not tokens_path.is_file():
            continue
        try:
            data = json.loads(tokens_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        token = str(data.get("access_token") or "").strip()
        if token:
            return token
    return None
