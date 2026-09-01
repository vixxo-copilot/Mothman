#!/usr/bin/env python3
"""Launch chatfpt MCP via mcp-remote + Gateway bearer (no OAuth fallback)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    ensure_gateway_bearer_for_url,
    gateway_bearer_failure_message,
    launch_mcp_remote_with_bearer,
)

CHATFPT_URL = "https://vixxonow.com/mcp/chatfpt"


def main() -> int:
    token = ensure_gateway_bearer_for_url(CHATFPT_URL)
    if not token:
        print(gateway_bearer_failure_message(CHATFPT_URL), file=sys.stderr)
        return 1
    return launch_mcp_remote_with_bearer(CHATFPT_URL, token)


if __name__ == "__main__":
    raise SystemExit(main())
