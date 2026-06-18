#!/usr/bin/env python3
"""Windows launcher for github-mcp-server — resolves token then starts stdio server."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import load_workspace_env, first_env  # noqa: E402


def resolve_github_token() -> str | None:
    token = first_env("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token:
        return token

    try:
        proc = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if proc.returncode != 0:
        return None
    token = proc.stdout.strip()
    return token or None


def main() -> int:
    load_workspace_env()

    binary = Path(__file__).resolve().parent / "github-mcp-server.exe"
    if not binary.is_file():
        print(f"github-mcp-server binary missing at {binary}", file=sys.stderr)
        print("Download: https://github.com/github/github-mcp-server/releases/latest", file=sys.stderr)
        return 1

    token = resolve_github_token()
    if not token:
        print(
            "GitHub MCP: set GITHUB_PERSONAL_ACCESS_TOKEN in .env or run 'gh auth login'",
            file=sys.stderr,
        )
        return 1

    os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
    return subprocess.call([str(binary), "stdio", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
