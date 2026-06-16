#!/usr/bin/env python3
"""Windows launcher for Smartsheet MCP via mcp-remote."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val and not os.environ.get(key):
            os.environ[key] = val


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")
    token_path = Path.home() / ".vixxo" / "smartsheet_api_token"
    if not os.environ.get("SMARTSHEET_API_TOKEN") and token_path.is_file():
        os.environ["SMARTSHEET_API_TOKEN"] = token_path.read_text(encoding="utf-8").strip()

    token = os.environ.get("SMARTSHEET_API_TOKEN", "").strip()
    if not token:
        print("Smartsheet MCP: SMARTSHEET_API_TOKEN not set.", file=sys.stderr)
        print("Fix: set in .env or ~/.vixxo/smartsheet_api_token, then restart MCP.", file=sys.stderr)
        return 1

    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"

    npx = os.environ.get("NPX", "npx")
    return subprocess.call(
        [npx, "-y", "mcp-remote", "https://mcp.smartsheet.com", "--header", f"Authorization:{token}"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
