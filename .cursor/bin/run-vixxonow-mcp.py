#!/usr/bin/env python3
"""Launch vixxonow MCP via mcp-remote + shared Gateway bearer token.

VixxoNow accepts the Gateway bearer (same family as business-objects). Using the
header avoids mcp-remote browser OAuth / localhost callback races that produce
'Authorization state is invalid or expired'.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    VIXXONOW_URL,
    auth_header_value,
    resolve_npx,
    resolve_vixxo_bearer_token,
)


def main() -> int:
    token = resolve_vixxo_bearer_token()
    if not token:
        print("vixxonow MCP: no Gateway bearer token found.", file=sys.stderr)
        print(
            "Fix: save a token to ~/.vixxo/gateway_api_token, or reconnect gateway "
            "in Cursor MCP so ~/.mcp-auth is populated, then run "
            ".cursor/bin/sync_gateway_token.py",
            file=sys.stderr,
        )
        return 1

    npx = resolve_npx()
    cmd = [
        npx,
        "-y",
        "mcp-remote",
        VIXXONOW_URL,
        "--header",
        f"Authorization:{auth_header_value(token)}",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
