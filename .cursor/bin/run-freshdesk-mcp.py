#!/usr/bin/env python3
"""Windows launcher for freshdesk-mcp — loads credentials then starts stdio server."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import load_workspace_env, resolve_npx  # noqa: E402


def main() -> int:
    load_workspace_env()
    if not os.environ.get("FRESHDESK_API_KEY") and os.environ.get("FRESHDESK_TOKEN"):
        os.environ["FRESHDESK_API_KEY"] = os.environ["FRESHDESK_TOKEN"]

    os.environ.setdefault("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com")
    os.environ.setdefault("NODE_ENV", "production")

    if not os.environ.get("FRESHDESK_API_KEY"):
        print(
            "Freshdesk MCP: FRESHDESK_API_KEY not set — server will start but API tools will fail until configured.",
            file=sys.stderr,
        )
        print(
            "Fix: set FRESHDESK_API_KEY in .env or save key to ~/.vixxo/freshdesk_token, then restart MCP.",
            file=sys.stderr,
        )

    npx = resolve_npx()
    return subprocess.call([npx, "-y", "freshdesk-mcp", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
