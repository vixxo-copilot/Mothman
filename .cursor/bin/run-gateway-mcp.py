#!/usr/bin/env python3
"""Launch gateway MCP via mcp-remote + shared Gateway bearer token."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    GATEWAY_URL,
    auth_header_value,
    gateway_token_expiry,
    load_token_file,
    resolve_npx,
    resolve_vixxo_bearer_token,
)


def main() -> int:
    token = resolve_vixxo_bearer_token()
    if not token:
        raw = load_token_file(Path.home() / ".vixxo" / "gateway_api_token")
        expiry = gateway_token_expiry(raw) if raw else None
        if expiry is not None:
            print(
                f"gateway MCP: bearer token expired at {expiry.isoformat(sep=' ', timespec='seconds')}.",
                file=sys.stderr,
            )
            print(
                "Fix: .cursor/bin/refresh-gateway-bearer.cmd (one browser sign-in), "
                "then restart gateway in Cursor MCP.",
                file=sys.stderr,
            )
        else:
            print("gateway MCP: no Gateway bearer token found.", file=sys.stderr)
            print(
                "Fix: .cursor/bin/refresh-gateway-bearer.cmd, or save a token to "
                "~/.vixxo/gateway_api_token, then restart gateway.",
                file=sys.stderr,
            )
        return 1

    npx = resolve_npx()
    cmd = [
        npx,
        "-y",
        "mcp-remote",
        GATEWAY_URL,
        "--header",
        f"Authorization:{auth_header_value(token)}",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
