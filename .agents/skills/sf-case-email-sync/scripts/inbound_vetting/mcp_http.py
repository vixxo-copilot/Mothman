#!/usr/bin/env python3
"""HTTP MCP client for Vixxo remote servers via shared mcp_env bearer refresh."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BIN = Path(__file__).resolve().parents[5] / ".cursor" / "bin"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from mcp_env import auth_header_value, load_workspace_env, resolve_bearer_token_for_url  # noqa: E402

GATEWAY_TOKEN_HELP = (
    "No Gateway bearer token. Save ~/.vixxo/gateway_api_token or run "
    ".cursor/bin/sync_gateway_token.py after Gateway auth."
)
VIXXOLINK_TOKEN_HELP = (
    "No VixxoLink bearer token. Save ~/.vixxo/vixxolink_api_token or run "
    ".cursor/bin/refresh-vixxolink-bearer.cmd after VixxoLink auth."
)


def _stdio_fallback(base_url: str, tool_name: str, arguments: dict | None) -> Any:
    try:
        from mcp_stdio_client import mcp_stdio_call

        return mcp_stdio_call(base_url, tool_name, arguments)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"MCP stdio fallback failed: {exc}"}


def mcp_call(base_url: str, tool_name: str, arguments: dict | None = None) -> Any:
    load_workspace_env()
    token = resolve_bearer_token_for_url(base_url)
    if not token:
        fallback = _stdio_fallback(base_url, tool_name, arguments)
        if isinstance(fallback, dict) and fallback.get("error"):
            help_text = VIXXOLINK_TOKEN_HELP if "/vixxolink" in base_url else GATEWAY_TOKEN_HELP
            return {"error": f"{help_text} ({fallback['error']})"}
        return fallback

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
        "Authorization": auth_header_value(token),
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36 MothmanMCP/1.0"
        ),
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
