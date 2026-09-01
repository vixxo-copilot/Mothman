#!/usr/bin/env python3
"""Launch Dynamics 365 MCP via bearer only (no browser OAuth fallback)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    ensure_gateway_bearer_for_url,
    ensure_vixxolink_access_token,
    gateway_bearer_failure_message,
    launch_mcp_remote_with_bearer,
    mcp_tools_list_ok,
)

DYNAMICS_URL = "https://vixxonow.com/mcp/dynamics365"


def main() -> int:
    candidates: list[str] = []
    seen: set[str] = set()
    for token in (ensure_vixxolink_access_token(), ensure_gateway_bearer_for_url(DYNAMICS_URL)):
        if token and token not in seen:
            seen.add(token)
            candidates.append(token)

    token = next((t for t in candidates if mcp_tools_list_ok(DYNAMICS_URL, t)), None)
    if not token:
        print(gateway_bearer_failure_message(DYNAMICS_URL), file=sys.stderr)
        return 1
    return launch_mcp_remote_with_bearer(DYNAMICS_URL, token)


if __name__ == "__main__":
    raise SystemExit(main())
