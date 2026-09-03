#!/usr/bin/env python3
"""Persist Gateway bearer token to ~/.vixxo/gateway_api_token when available."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    GATEWAY_URL,
    auth_header_value,
    clear_gateway_oauth_in_progress,
    collect_gateway_bearer_candidates,
    ensure_gateway_bearer_for_url,
    gateway_bearer_failure_message,
    gateway_token_expiry,
    is_gateway_token_usable,
    load_token_file,
    mirror_gateway_bearer_to_vixxolink,
    mcp_tools_list_ok,
    seed_mcp_remote_token_cache,
    vixxolink_bearer_acceptable_for_launch,
    VIXXOLINK_URL,
)


def pick_sync_gateway_token() -> str | None:
    working = ensure_gateway_bearer_for_url(GATEWAY_URL)
    if working:
        return working
    for token in collect_gateway_bearer_candidates():
        if mcp_tools_list_ok(GATEWAY_URL, token):
            return token
    return None


def stale_gateway_expiry() -> str | None:
    raw = load_token_file(Path.home() / ".vixxo" / "gateway_api_token")
    if not raw:
        return None
    expiry = gateway_token_expiry(raw)
    if expiry is None:
        return None
    return expiry.isoformat(sep=" ", timespec="seconds")


def main() -> int:
    token = pick_sync_gateway_token()
    if not token:
        stale = stale_gateway_expiry()
        if stale:
            print(f"status=FAIL reason=rejected_or_expired_gateway_token expiry={stale}")
        else:
            print("status=FAIL reason=no_gateway_token")
        print(gateway_bearer_failure_message(GATEWAY_URL))
        return 1

    token_path = Path.home() / ".vixxo" / "gateway_api_token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    existing = token_path.read_text(encoding="utf-8").strip() if token_path.is_file() else None
    token_path.write_text(token, encoding="utf-8")
    removed = clear_gateway_oauth_in_progress()
    header = auth_header_value(token)
    seed_mcp_remote_token_cache(GATEWAY_URL, token, {"Authorization": header})
    mirror_gateway_bearer_to_vixxolink(token)
    if vixxolink_bearer_acceptable_for_launch(VIXXOLINK_URL, token):
        seed_mcp_remote_token_cache(VIXXOLINK_URL, token, {"Authorization": header})
        print("vixxolink_seed=ok")
    else:
        print("vixxolink_seed=skipped reason=vixxolink_rejected_bearer")
    print(f"wrote={token_path}")
    print(f"changed={existing != token}")
    print(f"oauth_pkce_cleared={removed}")
    print("status=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
