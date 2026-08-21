#!/usr/bin/env python3
"""Persist Gateway bearer token to ~/.vixxo/gateway_api_token when available."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import GATEWAY_AUTH_ID, load_oauth_access_token, resolve_vixxo_bearer_token  # noqa: E402


def main() -> int:
    # Prefer fresh OAuth cache over stale ~/.vixxo file tokens (same as first BO setup).
    token = load_oauth_access_token(GATEWAY_AUTH_ID) or resolve_vixxo_bearer_token()
    if not token:
        print("status=FAIL reason=no_gateway_token")
        print(
            "Populate ~/.vixxo/gateway_api_token manually, or sign in once so "
            "~/.mcp-auth contains a Gateway access token."
        )
        return 1

    token_path = Path.home() / ".vixxo" / "gateway_api_token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    existing = token_path.read_text(encoding="utf-8").strip() if token_path.is_file() else None
    token_path.write_text(token, encoding="utf-8")
    print(f"wrote={token_path}")
    print(f"changed={existing != token}")
    print("status=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
