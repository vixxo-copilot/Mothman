#!/usr/bin/env python3
"""Apply MCP infrastructure fixes for this workspace (Windows-friendly)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_JSON = ROOT / ".cursor" / "mcp.json"
MS365_DIR = ROOT / ".cursor" / "bin" / "ms365-mcp"
VIXXO_DIR = Path.home() / ".vixxo"


def run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def ensure_vixxo_dir() -> None:
    VIXXO_DIR.mkdir(parents=True, exist_ok=True)


def ensure_ms365_deps() -> dict:
    if not MS365_DIR.is_dir():
        return {"step": "ms365 npm install", "status": "SKIP", "detail": "ms365-mcp dir missing"}
    local = MS365_DIR / "node_modules" / "@softeria" / "ms-365-mcp-server" / "dist" / "index.js"
    if local.is_file():
        return {"step": "ms365 npm install", "status": "PASS", "detail": "already installed"}
    code, out = run(["npm", "install"], cwd=MS365_DIR)
    return {
        "step": "ms365 npm install",
        "status": "PASS" if code == 0 and local.is_file() else "FAIL",
        "detail": out[-400:] if out else ("installed" if local.is_file() else "missing dist/index.js"),
    }


def validate_mcp_json() -> dict:
    try:
        payload = json.loads(MCP_JSON.read_text(encoding="utf-8"))
        servers = payload.get("mcpServers") or {}
        nested_cmd = [
            k
            for k, v in servers.items()
            if v.get("command", "").lower().endswith("cmd.exe") and "/c" in (v.get("args") or [])
        ]
        if nested_cmd:
            return {
                "step": "mcp.json validation",
                "status": "WARN",
                "detail": f"nested cmd.exe wrappers remain: {', '.join(nested_cmd)}",
            }
        return {"step": "mcp.json validation", "status": "PASS", "detail": f"{len(servers)} servers configured"}
    except Exception as exc:  # noqa: BLE001
        return {"step": "mcp.json validation", "status": "FAIL", "detail": str(exc)}


def check_gh_auth() -> dict:
    if shutil.which("gh") is None:
        return {"step": "github gh auth", "status": "FAIL", "detail": "gh CLI not on PATH"}
    code, out = run(["gh", "auth", "status"])
    if code != 0:
        return {"step": "github gh auth", "status": "FAIL", "detail": "run: gh auth login"}
    return {"step": "github gh auth", "status": "PASS", "detail": out.splitlines()[0] if out else "authenticated"}


def main() -> int:
    steps: list[dict] = []
    ensure_vixxo_dir()
    steps.append({"step": "ensure ~/.vixxo", "status": "PASS", "detail": str(VIXXO_DIR)})
    steps.append(validate_mcp_json())
    steps.append(ensure_ms365_deps())
    steps.append(check_gh_auth())

    diag = subprocess.run([sys.executable, str(ROOT / "bin" / "diagnose-mcp.py")], capture_output=True, text=True)
    steps.append(
        {
            "step": "diagnose-mcp.py",
            "status": "PASS" if diag.returncode == 0 else "FAIL",
            "detail": diag.stdout.strip() or diag.stderr.strip(),
        }
    )

    print(json.dumps({"root": str(ROOT), "steps": steps}, indent=2))
    failed = [s for s in steps if s["status"] == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
