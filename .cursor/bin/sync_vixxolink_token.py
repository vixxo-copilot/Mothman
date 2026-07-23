#!/usr/bin/env python3
"""Persist VixxoLink bearer token to ~/.vixxo/vixxolink_api_token when available."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import VIXXOLINK_AUTH_IDS, load_oauth_access_token, resolve_vixxolink_bearer_token  # noqa: E402


def main() -> int:
    token = None
    for auth_id in VIXXOLINK_AUTH_IDS:
        token = load_oauth_access_token(auth_id)
        if token:
            break
    token = token or resolve_vixxolink_bearer_token()
    if not token:
        print("status=FAIL reason=no_vixxolink_token")
        print(
            "Populate ~/.vixxo/vixxolink_api_token manually, or reconnect vixxolink "
            "in Cursor MCP so ~/.mcp-auth contains a VixxoLink access token."
        )
        return 1

    token_path = Path.home() / ".vixxo" / "vixxolink_api_token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    existing = token_path.read_text(encoding="utf-8").strip() if token_path.is_file() else None
    token_path.write_text(token, encoding="utf-8")
    print(f"wrote={token_path}")
    print(f"changed={existing != token}")
    print("status=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
