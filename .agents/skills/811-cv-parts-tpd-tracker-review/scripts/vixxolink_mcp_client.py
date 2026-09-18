#!/usr/bin/env python3
"""Direct VixxoLink MCP HTTP client for batch skill pipelines."""

from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"

BIN = Path(__file__).resolve().parents[4] / ".cursor" / "bin"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from mcp_env import (  # noqa: E402
    auth_header_value,
    load_workspace_env,
    resolve_bearer_token_for_url,
)


def ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        import certifi

        ctx.load_verify_locations(certifi.where())
    except ImportError:
        pass
    return ctx


def get_token(*, script_dir: Path | None = None) -> str:
    del script_dir
    load_workspace_env()
    token = resolve_bearer_token_for_url(VIXXOLINK_URL)
    if not token:
        raise RuntimeError(
            "Could not acquire VixxoLink MCP bearer token. "
            "Run .cursor/bin/refresh-vixxolink-bearer.cmd once, then retry."
        )
    return token


def mcp_call(token: str, tool: str, arguments: dict[str, Any], *, timeout: int = 120) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    req = urllib.request.Request(
        VIXXOLINK_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_header_value(token),
            "Accept": "application/json, text/event-stream",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36 MothmanMCP/1.0"
            ),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
        body = json.loads(resp.read().decode())
    if "error" in body:
        raise RuntimeError(body["error"].get("message", str(body["error"])))
    result = body.get("result", {})
    if isinstance(result, dict) and result.get("isError"):
        raise RuntimeError(str(result.get("content", result)))
    if isinstance(result, dict) and "structuredContent" in result:
        sc = result["structuredContent"]
        return sc if isinstance(sc, dict) else {"data": sc}
    if isinstance(result, dict) and "data" in result:
        return result
    if isinstance(result, list) and result:
        text = result[0].get("text", "") if isinstance(result[0], dict) else ""
        if text:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"data": parsed}
    return result if isinstance(result, dict) else {"data": result}


def unwrap_list(resp: dict[str, Any]) -> list[dict[str, Any]]:
    data = resp.get("data", resp)
    if isinstance(data, dict):
        inner = data.get("data", data.get("results"))
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            for key in ("results", "notes", "timeEvents", "time_events"):
                if isinstance(inner.get(key), list):
                    return inner[key]
    if isinstance(data, list):
        return data
    return []


def unwrap_resolve(resp: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    data = resp.get("data", resp)
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    if not isinstance(data, dict):
        return {}, [], []

    sr = (
        data.get("serviceRequest")
        or data.get("service_request")
        or data.get("details")
        or {}
    )
    if not isinstance(sr, dict):
        sr = {}

    notes = data.get("notes")
    if not isinstance(notes, list):
        notes = unwrap_list({"data": notes}) if notes else []

    times = data.get("timeEvents") or data.get("time_events")
    if not isinstance(times, list):
        times = unwrap_list({"data": times}) if times else []

    if not notes and not sr:
        listed = unwrap_list(resp)
        if listed and isinstance(listed[0], dict) and ("text" in listed[0] or "type" in listed[0]):
            notes = listed

    return sr, notes, times
