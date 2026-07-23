#!/usr/bin/env python3
"""Launch vixxolink MCP via mcp-remote + shared Gateway bearer token."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    VIXXOLINK_URL,
    auth_header_value,
    resolve_npx,
    resolve_vixxolink_bearer_token,
)


def main() -> int:
    token = resolve_vixxolink_bearer_token()
    if not token:
        print("vixxolink MCP: no VixxoLink bearer token found.", file=sys.stderr)
        print(
            "Fix: save a token to ~/.vixxo/vixxolink_api_token, or reconnect vixxolink "
            "in Cursor MCP so ~/.mcp-auth is populated, then run "
            ".cursor/bin/sync_vixxolink_token.py",
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
