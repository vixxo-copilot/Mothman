#!/usr/bin/env python3
"""Launch vixxolink MCP via mcp-remote + VixxoLink bearer token (no OAuth fallback)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    VIXXOLINK_URL,
    ensure_vixxolink_access_token,
    launch_mcp_remote_with_bearer,
    mcp_tools_list_ok,
)


def main() -> int:
    token = ensure_vixxolink_access_token()
    if not token or not mcp_tools_list_ok(VIXXOLINK_URL, token):
        print("vixxolink MCP: bearer missing or rejected (no browser fallback).", file=sys.stderr)
        print(
            "Run: python .cursor/bin/sync_vixxolink_token.py after Gateway refresh, "
            "then restart vixxolink in Cursor MCP.",
            file=sys.stderr,
        )
        return 1
    return launch_mcp_remote_with_bearer(VIXXOLINK_URL, token)


if __name__ == "__main__":
    raise SystemExit(main())
