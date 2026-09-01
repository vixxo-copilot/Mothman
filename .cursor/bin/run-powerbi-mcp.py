#!/usr/bin/env python3
"""Launch Power BI MCP via mcp-remote + shared Gateway bearer token."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    POWERBI_URL,
    ensure_gateway_bearer_for_url,
    gateway_bearer_failure_message,
    launch_mcp_remote_with_bearer,
)


def main() -> int:
    token = ensure_gateway_bearer_for_url(POWERBI_URL)
    if not token:
        print(gateway_bearer_failure_message(POWERBI_URL), file=sys.stderr)
        return 1
    return launch_mcp_remote_with_bearer(POWERBI_URL, token)


if __name__ == "__main__":
    raise SystemExit(main())
