#!/usr/bin/env python3
"""Launch business-objects MCP via mcp-remote + shared Gateway bearer token."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    BO_UNIVERSE_URL,
    ensure_gateway_bearer_for_url,
    gateway_bearer_failure_message,
    launch_mcp_remote_with_bearer,
)


def main() -> int:
    token = ensure_gateway_bearer_for_url(BO_UNIVERSE_URL)
    if not token:
        print(gateway_bearer_failure_message(BO_UNIVERSE_URL), file=sys.stderr)
        return 1
    return launch_mcp_remote_with_bearer(BO_UNIVERSE_URL, token)


if __name__ == "__main__":
    raise SystemExit(main())
