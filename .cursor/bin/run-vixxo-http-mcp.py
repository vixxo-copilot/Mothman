#!/usr/bin/env python3
"""Windows stdio bridge for Vixxo remote HTTP MCP servers (via mcp-remote)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import first_env, load_workspace_env, resolve_npx  # noqa: E402

# server_key -> (url, token_env_vars, secret_filenames under ~/.vixxo)
SERVERS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "gateway": (
        "https://vixxonow.com/mcp/gateway",
        ("GATEWAY_API_TOKEN", "VIXXONOW_API_TOKEN", "VIXXOLINK_API_TOKEN"),
        ("gateway_api_token", "gateway_token", "vixxonow_api_token", "vixxolink_api_token"),
    ),
    "vixxolink": (
        "https://vixxonow.com/mcp/vixxolink",
        ("VIXXOLINK_API_TOKEN", "VIXXONOW_API_TOKEN", "GATEWAY_API_TOKEN"),
        ("vixxolink_api_token", "vixxolink_token", "vixxonow_api_token"),
    ),
    "vixxonow": (
        "https://vixxonow.com/mcp/vixxonow",
        ("VIXXONOW_API_TOKEN", "VIXXOLINK_API_TOKEN", "GATEWAY_API_TOKEN"),
        ("vixxonow_api_token", "vixxonow_token", "vixxolink_api_token"),
    ),
    "business-objects": (
        "https://vixxonow.com/mcp/bo-universe",
        ("VIXXONOW_API_TOKEN", "GATEWAY_API_TOKEN", "VIXXOLINK_API_TOKEN"),
        ("vixxonow_api_token", "gateway_api_token", "vixxolink_api_token"),
    ),
    "powerbi-prod": (
        "https://vixxonow.com/mcp/powerbi",
        ("VIXXONOW_API_TOKEN", "POWERBI_API_TOKEN"),
        ("vixxonow_api_token", "powerbi_api_token"),
    ),
    "gong-transact": (
        "https://transact.vixxo.com/mcp/gong",
        ("GONG_ACCESS_KEY", "VIXXONOW_API_TOKEN", "VIXXOLINK_API_TOKEN"),
        ("gong_access_key", "vixxonow_api_token", "vixxolink_api_token"),
    ),
    "chatfpt": (
        "https://vixxonow.com/mcp/chatfpt",
        ("CHATFPT_API_TOKEN", "VIXXONOW_API_TOKEN"),
        ("chatfpt_api_token", "vixxonow_api_token"),
    ),
    "dynamics365": (
        "https://vixxonow.com/mcp/dynamics365",
        ("VIXXONOW_API_TOKEN", "DYNAMICS_CLIENT_SECRET"),
        ("vixxonow_api_token", "dynamics_client_secret"),
    ),
}


def resolve_token(env_names: tuple[str, ...], secret_names: tuple[str, ...]) -> str | None:
    token = first_env(*env_names)
    if token:
        return token
    home_vixxo = Path.home() / ".vixxo"
    for secret in secret_names:
        path = home_vixxo / secret
        if path.is_file():
            val = path.read_text(encoding="utf-8").strip()
            if val:
                return val
    return None


def auth_header_value(token: str) -> str:
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: run-vixxo-http-mcp.py <server-key>", file=sys.stderr)
        return 2

    server_key = sys.argv[1].strip().lower()
    if server_key not in SERVERS:
        print(f"Unknown Vixxo HTTP MCP server key: {server_key}", file=sys.stderr)
        return 2

    url, env_names, secret_names = SERVERS[server_key]
    load_workspace_env()

    token = resolve_token(env_names, secret_names)
    npx = resolve_npx()
    if not token:
        print(
            f"{server_key} MCP: API token not set — refusing to start (OAuth cannot complete headless in Cursor).",
            file=sys.stderr,
        )
        print(
            f"Fix: save token to ~/.vixxo/{secret_names[0]} or set {env_names[0]} in .env, then restart MCP.",
            file=sys.stderr,
        )
        return 1

    cmd = [npx, "-y", "mcp-remote", url, "--header", f"Authorization:{auth_header_value(token)}"]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
