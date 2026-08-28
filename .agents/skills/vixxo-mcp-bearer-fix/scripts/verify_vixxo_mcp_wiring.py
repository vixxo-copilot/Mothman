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
    gateway_token = (vixxo / "gateway_api_token").is_file()
    vixxolink_token = (vixxo / "vixxolink_api_token").is_file()
    results.append(
        {
            "server": "tokens",
            "status": "PASS" if gateway_token and vixxolink_token else "FAIL",
            "detail": {
                "gateway_api_token": gateway_token,
                "vixxolink_api_token": vixxolink_token,
            },
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
