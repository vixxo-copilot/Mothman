#!/usr/bin/env python3
"""Call Vixxo remote MCP tools via npx mcp-remote (stdio), matching .cursor/mcp.json."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from typing import Any

MCP_URLS = {
    "gateway": "https://vixxonow.com/mcp/gateway",
    "vixxolink": "https://vixxonow.com/mcp/vixxolink",
    "vixxonow": "https://vixxonow.com/mcp/vixxonow",
}


def _npx_cmd() -> list[str]:
    npx = os.environ.get("NPX")
    if npx:
        return [npx, "-y", "mcp-remote"]
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\nodejs\npx.cmd",
            shutil.which("npx.cmd"),
            shutil.which("npx"),
        ):
            if candidate:
                return [candidate, "-y", "mcp-remote"]
    found = shutil.which("npx")
    if found:
        return [found, "-y", "mcp-remote"]
    return ["npx", "-y", "mcp-remote"]


def _parse_response_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("data:"):
        line = line[5:].strip()
    if not line.startswith("{"):
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def mcp_stdio_call(
    base_url: str,
    tool_name: str,
    arguments: dict | None = None,
    *,
    wait_timeout: float = 45.0,
) -> Any:
    """One-shot MCP tools/call over mcp-remote stdio."""
    cmd = _npx_cmd() + [base_url]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin and proc.stdout

    responses: list[dict] = []
    stderr_chunks: list[str] = []
    done = threading.Event()

    def reader() -> None:
        for raw in proc.stdout:
            msg = _parse_response_line(raw)
            if msg:
                responses.append(msg)
                if msg.get("id") == 2:
                    done.set()

    def err_reader() -> None:
        assert proc.stderr
        for raw in proc.stderr:
            stderr_chunks.append(raw)

    t_out = threading.Thread(target=reader, daemon=True)
    t_err = threading.Thread(target=err_reader, daemon=True)
    t_out.start()
    t_err.start()

    def send(payload: dict) -> None:
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()

    send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "sp-inbound-vetting", "version": "1.0"},
            },
        }
    )
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
        }
    )
    proc.stdin.close()

    done.wait(timeout=wait_timeout)
    proc.wait(timeout=10)
    t_out.join(timeout=5)
    t_err.join(timeout=5)

    for msg in responses:
        if msg.get("id") == 2:
            if msg.get("error"):
                return {"error": msg["error"]}
            return msg

    err = "".join(stderr_chunks).strip()
    if err:
        return {"error": err[:500]}
    return {"error": "No MCP response from mcp-remote"}


def mcp_stdio_result_text(response: Any) -> str:
    if isinstance(response, dict) and response.get("error"):
        err = response["error"]
        if isinstance(err, dict):
            return json.dumps(err)
        return str(err)
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
    return json.dumps(result)[:4000]
