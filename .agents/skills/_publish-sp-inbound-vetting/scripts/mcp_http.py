#!/usr/bin/env python3
"""Minimal HTTP MCP client for Vixxo remote MCP servers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = ROOT / ".env"
VIXXO_DIR = Path.home() / ".vixxo"


def _load_env() -> None:
    if ENV_PATH.is_file():
        for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and not os.environ.get(key):
                os.environ[key] = val
    if VIXXO_DIR.is_dir():
        for p in VIXXO_DIR.iterdir():
            if not p.is_file():
                continue
            secret = p.read_text(encoding="utf-8").strip()
            if not secret:
                continue
            # Lowercase ~/.vixxo filenames (vixxolink_api_token) and legacy uppercase.
            env_key = p.name.upper()
            if not os.environ.get(env_key):
                os.environ[env_key] = secret
            # Mirror common aliases used across launchers.
            aliases = {
                "FRESHDESK_TOKEN": "FRESHDESK_API_KEY",
                "FRESHDESK_API_KEY": "FRESHDESK_API_KEY",
                "VIXXOLINK_API_TOKEN": "VIXXOLINK_API_TOKEN",
                "GATEWAY_API_TOKEN": "GATEWAY_API_TOKEN",
                "VIXXONOW_API_TOKEN": "VIXXONOW_API_TOKEN",
            }
            alias = aliases.get(env_key)
            if alias and not os.environ.get(alias):
                os.environ[alias] = secret


def _token() -> str | None:
    for name in (
        "VIXXOLINK_API_TOKEN",
        "GATEWAY_API_TOKEN",
        "VIXXONOW_API_TOKEN",
        "MCP_AUTH_TOKEN",
    ):
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return None


def _stdio_fallback(base_url: str, tool_name: str, arguments: dict | None) -> Any:
    try:
        from mcp_stdio_client import mcp_stdio_call

        return mcp_stdio_call(base_url, tool_name, arguments)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"MCP stdio fallback failed: {exc}"}


def mcp_call(base_url: str, tool_name: str, arguments: dict | None = None) -> Any:
    _load_env()
    token = _token()
    if not token:
        # Shell scripts lack Cursor MCP OAuth; stdio fallback usually fails outside Cursor.
        return _stdio_fallback(base_url, tool_name, arguments)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments or {}},
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
    }
    req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        return {"error": f"HTTP {exc.code}: {body}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}

    # Streamable HTTP may return SSE; take last JSON object line.
    for line in reversed(raw.splitlines()):
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Non-JSON MCP response", "raw": raw[:500]}


def mcp_result_text(response: Any) -> str:
    if isinstance(response, dict) and response.get("error"):
        return str(response["error"])
    if not isinstance(response, dict):
        return str(response)
    result = response.get("result") or {}
    content = result.get("content") or []
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    if parts:
        return "\n".join(parts)
    structured = result.get("structuredContent")
    if structured is not None:
        return json.dumps(structured)
    if result:
        return json.dumps(result)[:2000]
    return json.dumps(response)[:2000]
