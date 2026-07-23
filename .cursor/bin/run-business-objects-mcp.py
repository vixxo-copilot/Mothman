#!/usr/bin/env python3
"""Launch business-objects MCP via mcp-remote + shared Gateway bearer token."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    BO_UNIVERSE_URL,
    auth_header_value,
    resolve_npx,
    resolve_vixxo_bearer_token,
)


def main() -> int:
    token = resolve_vixxo_bearer_token()
    if not token:
        print(
            "business-objects MCP: no Gateway bearer token found.",
            file=sys.stderr,
        )
        print(
            "Fix: complete Gateway MCP OAuth first, or save a token to "
            "~/.vixxo/gateway_api_token, then restart business-objects.",
            file=sys.stderr,
        )
        return 1

    npx = resolve_npx()
    cmd = [
        npx,
        "-y",
        "mcp-remote",
        BO_UNIVERSE_URL,
        "--header",
        f"Authorization:{auth_header_value(token)}",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
