#!/usr/bin/env python3
"""Launch vixxolink MCP via mcp-remote + VixxoLink bearer token (no OAuth fallback)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    VIXXOLINK_URL,
    ensure_vixxolink_bearer_for_url,
    launch_mcp_remote_with_bearer,
    vixxolink_bearer_failure_message,
)


def main() -> int:
    token = ensure_vixxolink_bearer_for_url(VIXXOLINK_URL)
    if not token:
        print(vixxolink_bearer_failure_message(VIXXOLINK_URL), file=sys.stderr)
        return 1
    return launch_mcp_remote_with_bearer(VIXXOLINK_URL, token)


if __name__ == "__main__":
    raise SystemExit(main())
