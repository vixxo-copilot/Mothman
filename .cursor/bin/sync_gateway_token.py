#!/usr/bin/env python3
"""Persist Gateway bearer token to ~/.vixxo/gateway_api_token when available."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    GATEWAY_AUTH_ID,
    gateway_token_expiry,
    is_gateway_token_usable,
    load_oauth_access_token,
    load_token_file,
)


def pick_usable_gateway_token() -> str | None:
    candidates: list[str] = []
    oauth = load_oauth_access_token(GATEWAY_AUTH_ID)
    if oauth:
        candidates.append(oauth)
    file_token = load_token_file(Path.home() / ".vixxo" / "gateway_api_token")
    if file_token:
        candidates.append(file_token)
    for token in candidates:
        if is_gateway_token_usable(token):
            return token
    return None


def stale_gateway_expiry() -> str | None:
    candidates: list[str] = []
    oauth = load_oauth_access_token(GATEWAY_AUTH_ID)
    if oauth:
        candidates.append(oauth)
    file_token = load_token_file(Path.home() / ".vixxo" / "gateway_api_token")
    if file_token:
        candidates.append(file_token)
    for token in candidates:
        expiry = gateway_token_expiry(token)
        if expiry is not None:
            return expiry.isoformat(sep=" ", timespec="seconds")
    return None


def main() -> int:
    token = pick_usable_gateway_token()
    if not token:
        stale = stale_gateway_expiry()
        if stale:
            print(f"status=FAIL reason=expired_gateway_token expiry={stale}")
        else:
            print("status=FAIL reason=no_gateway_token")
        print("Run: .cursor\\bin\\refresh-gateway-bearer.cmd")
        print("Then restart gateway, business-objects, powerbi-prod, and vixxonow in Cursor MCP.")
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
