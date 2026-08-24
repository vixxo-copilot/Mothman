#!/usr/bin/env python3
"""Diagnose MCP prerequisites for this workspace (read-only checks)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_JSON = ROOT / ".cursor" / "mcp.json"
VIXXO_DIR = Path.home() / ".vixxo"


def has_secret(*names: str) -> bool:
    for name in names:
        if os.environ.get(name, "").strip():
            return True
        p = VIXXO_DIR / name.lower()
        if p.is_file() and p.read_text(encoding="utf-8").strip():
            return True
    return False


def check_cmd(name: str) -> bool:
    if shutil.which(name):
        return True
    # Windows npm global CLIs (e.g. sf.cmd) may be outside default PATH in shells.
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            for ext in ("", ".cmd", ".exe"):
                candidate = Path(appdata) / "npm" / f"{name}{ext}"
                if candidate.is_file():
                    return True
    return False


def check_vixxolink_launcher() -> tuple[bool, str]:
    """VixxoLink must use bearer wrapper (not url-only / OAuth in Cursor)."""
    if not MCP_JSON.is_file():
        return False, f"missing {MCP_JSON}"
    try:
        payload = json.loads(MCP_JSON.read_text(encoding="utf-8"))
        vl = (payload.get("mcpServers") or {}).get("vixxolink") or {}
    except json.JSONDecodeError as exc:
        return False, f"invalid mcp.json: {exc}"
    if vl.get("url"):
        return False, "vixxolink must use run-vixxolink-mcp.cmd (not native url OAuth)"
    cmd = (vl.get("command") or "").lower()
    if "run-vixxolink-mcp" not in cmd and "run-vixxolink-mcp" not in " ".join(vl.get("args") or []):
        return False, "vixxolink command must point at run-vixxolink-mcp.cmd"
    token_ok = has_secret("VIXXOLINK_API_TOKEN") or (
        Path.home() / ".vixxo" / "vixxolink_api_token"
    ).is_file()
    if not token_ok:
        return False, "run: python .cursor/bin/sync_vixxolink_token.py (after Gateway OAuth)"
    return True, "bearer wrapper + token file"


def check_salesforce_launcher() -> tuple[bool, str]:
    entry = ROOT / ".cursor" / "bin" / "salesforce-mcp" / "node_modules" / "@salesforce" / "mcp" / "bin" / "run.js"
    sf_cmd = Path(os.environ.get("APPDATA", "")) / "npm" / "sf.cmd"
    if not entry.is_file():
        return False, f"vendored MCP missing at {entry} — run npm install in .cursor/bin/salesforce-mcp"
    if not sf_cmd.is_file():
        return False, f"sf CLI missing at {sf_cmd} — npm install -g @salesforce/cli && sf org login web"
    return True, "vendored @salesforce/mcp + sf.cmd present"


def main() -> int:
    results: list[dict] = []

    for label, fn in (
        ("vixxolink launcher", check_vixxolink_launcher),
        ("salesforce launcher", check_salesforce_launcher),
    ):
        ok, detail = fn()
        results.append({"check": label, "status": "PASS" if ok else "FAIL", "fix": detail})

    checks = [
        ("freshdesk", has_secret("FRESHDESK_API_KEY", "FRESHDESK_TOKEN"), "freshdesk_token in ~/.vixxo or FRESHDESK_API_KEY in .env"),
        ("freshservice", has_secret("FRESHSERVICE_API_KEY"), "freshservice_api_key in ~/.vixxo"),
        ("gateway/vixxolink/vixxonow", has_secret("VIXXOLINK_API_TOKEN", "GATEWAY_API_TOKEN", "VIXXONOW_API_TOKEN"), "vixxolink_api_token or vixxonow_api_token in ~/.vixxo"),
        ("salesforce CLI", check_cmd("sf"), "npm install -g @salesforce/cli && sf org login web"),
        ("github MCP binary", (ROOT / ".cursor" / "bin" / "github-mcp-server.exe").is_file(), "see .cursor/mcp.README.md § GitHub"),
        ("node/npx", check_cmd("npx"), "install Node.js"),
        ("gong", has_secret("GONG_ACCESS_KEY", "GONG_ACCESS_KEY_SECRET"), "GONG_ACCESS_KEY + GONG_ACCESS_KEY_SECRET in .env"),
        ("smartsheet", has_secret("SMARTSHEET_API_TOKEN"), "SMARTSHEET_API_TOKEN in .env"),
    ]

    for label, ok, fix in checks:
        results.append({"check": label, "status": "PASS" if ok else "FAIL", "fix": fix})

    if check_cmd("sf"):
        sf_bin = shutil.which("sf") or str(Path(os.environ.get("APPDATA", "")) / "npm" / "sf.cmd")
        proc = subprocess.run([sf_bin, "org", "list", "--json"], capture_output=True, text=True, timeout=60)
        sf_ok = False
        if proc.returncode == 0:
            try:
                payload = json.loads(proc.stdout)
                orgs = payload.get("result", {}).get("nonScratchOrgs") or []
                sf_ok = len(orgs) > 0
            except json.JSONDecodeError:
                pass
        results.append(
            {
                "check": "salesforce org login",
                "status": "PASS" if sf_ok else "FAIL",
                "fix": "sf org login web",
            }
        )

    print(json.dumps({"mcp_config": str(MCP_JSON), "results": results}, indent=2))
    failed = [r for r in results if r["status"] == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
