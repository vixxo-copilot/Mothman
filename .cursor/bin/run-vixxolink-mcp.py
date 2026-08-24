#!/usr/bin/env python3
"""Launch vixxolink MCP via mcp-remote + VixxoLink bearer token (no OAuth fallback)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    VIXXOLINK_URL,
    auth_header_value,
    ensure_vixxolink_access_token,
    resolve_npx,
)


def main() -> int:
    token = ensure_vixxolink_access_token()
    if not token:
        print("vixxolink MCP: no VixxoLink bearer token found.", file=sys.stderr)
        print(
            "Fix: python .cursor/bin/sync_vixxolink_token.py after Gateway OAuth, "
            "or save a token to ~/.vixxo/vixxolink_api_token, then restart vixxolink.",
            file=sys.stderr,
        )
        return 1

    npx = resolve_npx()
    cmd = [
        npx,
        "-y",
        "mcp-remote",
        VIXXOLINK_URL,
        "--header",
        f"Authorization:{auth_header_value(token)}",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
