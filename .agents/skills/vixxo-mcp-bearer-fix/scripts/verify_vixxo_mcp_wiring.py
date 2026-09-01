#!/usr/bin/env python3
"""Verify Vixxo HTTP MCP bearer wiring (no token values printed)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MCP_JSON = ROOT / ".cursor" / "mcp.json"
SYNC_STATE = ROOT / ".cursor" / "mcp-sync-state.json"
BIN = ROOT / ".cursor" / "bin"

sys.path.insert(0, str(BIN))
from mcp_env import (  # noqa: E402
    GATEWAY_URL,
    ensure_gateway_bearer_for_url,
    gateway_token_expiry,
    load_token_file,
    resolve_vixxolink_bearer_token,
)

SERVERS = {
    "gateway": "run-gateway-mcp",
    "vixxolink": "run-vixxolink-mcp",
    "business-objects": "run-business-objects-mcp",
    "powerbi-prod": "run-powerbi-mcp",
}


def check_wrapper(server: str, entry: dict) -> tuple[bool, str]:
    if entry.get("url"):
        return False, "uses native url (OAuth)"
    blob = json.dumps(entry).lower()
    needle = SERVERS[server]
    if needle not in blob:
        return False, f"missing {needle}.cmd wrapper"
    if "mcp-remote" in blob and needle not in blob:
        return False, "bare npx mcp-remote"
    cmd = BIN / f"{needle}.cmd"
    py = BIN / f"{needle}.py"
    if not cmd.is_file() or not py.is_file():
        return False, f"missing launcher files under .cursor/bin"
    return True, "bearer wrapper"


def main() -> int:
    results: list[dict] = []
    if not MCP_JSON.is_file():
        print(json.dumps({"status": "FAIL", "error": f"missing {MCP_JSON}"}, indent=2))
        return 1

    payload = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    servers = payload.get("mcpServers") or {}

    for name, needle in SERVERS.items():
        entry = servers.get(name) or {}
        ok, detail = check_wrapper(name, entry)
        results.append({"server": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    vixxo = Path.home() / ".vixxo"
    gateway_usable = bool(ensure_gateway_bearer_for_url(GATEWAY_URL))
    vixxolink_usable = bool(resolve_vixxolink_bearer_token())
    gateway_raw = load_token_file(vixxo / "gateway_api_token")
    gateway_expiry = gateway_token_expiry(gateway_raw)
    gateway_detail = {
        "gateway_api_token_file": (vixxo / "gateway_api_token").is_file(),
        "gateway_usable": gateway_usable,
        "gateway_expiry": (
            gateway_expiry.isoformat(sep=" ", timespec="seconds")
            if gateway_expiry is not None
            else None
        ),
        "vixxolink_api_token_file": (vixxo / "vixxolink_api_token").is_file(),
        "vixxolink_usable": vixxolink_usable,
    }
    if not gateway_usable:
        gateway_detail["gateway_fix"] = ".cursor/bin/refresh-gateway-bearer.cmd"
    results.append(
        {
            "server": "tokens",
            "status": "PASS" if gateway_usable and vixxolink_usable else "FAIL",
            "detail": gateway_detail,
        }
    )

    local_ok = True
    if SYNC_STATE.is_file():
        state = json.loads(SYNC_STATE.read_text(encoding="utf-8"))
        resolution = state.get("managed_entry_resolution") or {}
        missing_local = [k for k in SERVERS if resolution.get(k) != "local"]
        local_ok = not missing_local
        results.append(
            {
                "server": "mcp-sync-state",
                "status": "PASS" if local_ok else "WARN",
                "detail": (
                    "all local"
                    if local_ok
                    else f"set local resolution for: {', '.join(missing_local)}"
                ),
            }
        )

    user_mcp = Path.home() / ".cursor" / "mcp.json"
    if user_mcp.is_file():
        user_payload = json.loads(user_mcp.read_text(encoding="utf-8"))
        dupes = [
            k
            for k in SERVERS
            if k in (user_payload.get("mcpServers") or {})
        ]
        results.append(
            {
                "server": "user-mcp.json",
                "status": "WARN" if dupes else "PASS",
                "detail": (
                    f"duplicate keys: {', '.join(dupes)}"
                    if dupes
                    else "no duplicate Vixxo HTTP entries"
                ),
            }
        )

    failed = [r for r in results if r["status"] == "FAIL"]
    report = {
        "repo_root": str(ROOT),
        "mcp_config": str(MCP_JSON),
        "overall": "PASS" if not failed else "FAIL",
        "results": results,
    }
    print(json.dumps(report, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
