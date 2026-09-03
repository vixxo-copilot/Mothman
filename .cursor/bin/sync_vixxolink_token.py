#!/usr/bin/env python3
"""Persist a bearer VixxoLink actually accepts. Prefer Gateway only when it works."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    GATEWAY_URL,
    VIXXOLINK_URL,
    auth_header_value,
    ensure_gateway_bearer_for_url,
    ensure_vixxolink_bearer_for_url,
    gateway_bearer_failure_message,
    mirror_gateway_bearer_to_vixxolink,
    seed_mcp_remote_token_cache,
    vixxolink_bearer_acceptable_for_launch,
    vixxolink_bearer_failure_message,
)


def main() -> int:
    gateway_token = ensure_gateway_bearer_for_url(GATEWAY_URL)
    if gateway_token and vixxolink_bearer_acceptable_for_launch(VIXXOLINK_URL, gateway_token):
        token_path = mirror_gateway_bearer_to_vixxolink(gateway_token)
        header = auth_header_value(gateway_token)
        seed_mcp_remote_token_cache(VIXXOLINK_URL, gateway_token, {"Authorization": header})
        print(f"wrote={token_path}")
        print("source=gateway_api_token")
        print("status=OK")
        return 0

    token = ensure_vixxolink_bearer_for_url(VIXXOLINK_URL)
    if not token:
        print("status=FAIL reason=no_vixxolink_bearer")
        if gateway_token:
            print("note=gateway_ok_but_vixxolink_rejected")
        print(gateway_bearer_failure_message(GATEWAY_URL))
        print(vixxolink_bearer_failure_message(VIXXOLINK_URL))
        return 1

    token_path = Path.home() / ".vixxo" / "vixxolink_api_token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    existing = token_path.read_text(encoding="utf-8").strip() if token_path.is_file() else None
    token_path.write_text(token, encoding="utf-8")
    header = auth_header_value(token)
    seed_mcp_remote_token_cache(VIXXOLINK_URL, token, {"Authorization": header})
    print(f"wrote={token_path}")
    print(f"changed={existing != token}")
    print("source=vixxolink_oauth")
    print("status=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
