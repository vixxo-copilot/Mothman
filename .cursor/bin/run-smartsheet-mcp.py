#!/usr/bin/env python3
"""Windows launcher for Smartsheet MCP via mcp-remote."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import load_workspace_env, resolve_npx  # noqa: E402


def main() -> int:
    load_workspace_env()
    token_path = Path.home() / ".vixxo" / "smartsheet_api_token"
    token = os.environ.get("SMARTSHEET_API_TOKEN", "").strip()
    if not token and token_path.is_file():
        token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        print("Smartsheet MCP: SMARTSHEET_API_TOKEN not set.", file=sys.stderr)
        print("Fix: set in .env or ~/.vixxo/smartsheet_api_token, then restart MCP.", file=sys.stderr)
        return 1

    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"

    npx = resolve_npx()
    return subprocess.call(
        [npx, "-y", "mcp-remote", "https://mcp.smartsheet.com", "--header", f"Authorization:{token}"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
