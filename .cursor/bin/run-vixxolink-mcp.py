#!/usr/bin/env python3
"""Launch vixxolink MCP via mcp-remote + shared VixxoLink bearer token.

If no bearer token is available, falls back to mcp-remote OAuth so Cursor can
reconnect and populate ~/.mcp-auth. After a successful reconnect, run
`.cursor/bin/sync_vixxolink_token.py` and restart the server.
"""

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
    npx = resolve_npx()
    cmd = [
        npx,
        "-y",
        "mcp-remote",
        VIXXOLINK_URL,
    ]
    if token:
        cmd.extend(
            [
                "--header",
                f"Authorization:{auth_header_value(token)}",
            ]
        )
    else:
        print(
            "vixxolink MCP: no bearer token; launching mcp-remote OAuth path.",
            file=sys.stderr,
        )
        print(
            "Complete browser sign-in if prompted, then run "
            ".cursor/bin/sync_vixxolink_token.py and restart vixxolink.",
            file=sys.stderr,
        )

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
