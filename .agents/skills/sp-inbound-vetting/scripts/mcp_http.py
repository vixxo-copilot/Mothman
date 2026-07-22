#!/usr/bin/env python3
"""Minimal HTTP MCP client for Vixxo remote MCP servers."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = ROOT / ".env"
VIXXO_DIR = Path.home() / ".vixxo"
GATEWAY_MCP_URL = "https://vixxonow.com/mcp/gateway"
_TOKEN_ENV_KEYS = (
    "VIXXOLINK_API_TOKEN",
    "GATEWAY_API_TOKEN",
    "VIXXONOW_API_TOKEN",
    "MCP_AUTH_TOKEN",
)


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


def _load_mcp_oauth_bearer(mcp_url: str = GATEWAY_MCP_URL) -> str | None:
    """Bearer from Cursor/mcp-remote OAuth cache (~/.mcp-auth)."""
    auth_root = Path.home() / ".mcp-auth"
    if not auth_root.is_dir():
        return None
    key = hashlib.md5(mcp_url.encode()).hexdigest()
    token_name = f"{key}_tokens.json"
    for version_dir in sorted(auth_root.glob("mcp-remote-*"), reverse=True):
        token_path = version_dir / token_name
        if not token_path.is_file():
            continue
        try:
            data = json.loads(token_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        token = str(data.get("access_token") or "").strip()
        if token:
            return token
    return None


def _clear_gateway_tokens() -> None:
    for name in _TOKEN_ENV_KEYS:
        os.environ.pop(name, None)


def _token(*, prefer_oauth: bool = False) -> str | None:
    if prefer_oauth:
        oauth = _load_mcp_oauth_bearer()
        if oauth:
            return oauth
    for name in _TOKEN_ENV_KEYS:
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return _load_mcp_oauth_bearer()


def _mcp_post(base_url: str, token: str, payload: dict) -> tuple[Any, int | None]:
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
        return {"error": f"HTTP {exc.code}: {body}"}, exc.code
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}, None

    for line in reversed(raw.splitlines()):
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            try:
                return json.loads(line), None
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return {"error": "Non-JSON MCP response", "raw": raw[:500]}, None


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
        return _stdio_fallback(base_url, tool_name, arguments)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments or {}},
    }
    response, status = _mcp_post(base_url, token, payload)
    if status == 401:
        _clear_gateway_tokens()
        oauth = _token(prefer_oauth=True)
        if oauth and oauth != token:
            response, _ = _mcp_post(base_url, oauth, payload)
    if isinstance(response, dict) and response.get("error"):
        err = str(response["error"])
        if "HTTP 401" in err or "invalid_token" in err.lower():
            return response
    return response


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
