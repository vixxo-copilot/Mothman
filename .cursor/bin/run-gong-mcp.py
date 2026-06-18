#!/usr/bin/env python3
"""Windows launcher for gong-mcp (kenazk/gong-mcp)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import first_env, load_workspace_env, resolve_npx  # noqa: E402


def main() -> int:
    load_workspace_env()

    key = first_env("GONG_ACCESS_KEY")
    secret = first_env("GONG_ACCESS_KEY_SECRET")
    if not key or not secret:
        print("Gong MCP: GONG_ACCESS_KEY and GONG_ACCESS_KEY_SECRET required.", file=sys.stderr)
        print("Fix: set both in .env or ~/.vixxo/gong_access_key + gong_access_key_secret", file=sys.stderr)
        return 1

    os.environ["GONG_ACCESS_KEY"] = key
    os.environ["GONG_ACCESS_KEY_SECRET"] = secret
    npx = resolve_npx()
    return subprocess.call([npx, "-y", "github:kenazk/gong-mcp", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
