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
ENV_PATH = ROOT / ".env"


def load_dotenv() -> None:
    if not ENV_PATH.is_file():
        return
    for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val and not os.environ.get(key):
            os.environ[key] = val


def has_secret(*names: str) -> bool:
    for name in names:
        if os.environ.get(name, "").strip():
            return True
        p = VIXXO_DIR / name.lower()
        if p.is_file() and p.read_text(encoding="utf-8").strip():
            return True
        p2 = VIXXO_DIR / f"{name.lower()}.txt"
        if p2.is_file() and p2.read_text(encoding="utf-8").strip():
            return True
    # Also scan ~/.vixxo filenames mapped to env-style keys.
    if VIXXO_DIR.is_dir():
        for path in VIXXO_DIR.iterdir():
            if not path.is_file():
                continue
            stem = path.stem.upper().replace("-", "_")
            if stem in names and path.read_text(encoding="utf-8").strip():
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


def check_gh_auth() -> bool:
    binary = ROOT / ".cursor" / "bin" / "github-mcp-server.exe"
    if not binary.is_file():
        return False
    if os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "").strip():
        return True
    if shutil.which("gh") is None:
        return False
    proc = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=30)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def main() -> int:
    load_dotenv()
    results: list[dict] = []

    checks = [
        ("freshdesk", has_secret("FRESHDESK_API_KEY", "FRESHDESK_TOKEN"), "freshdesk_token in ~/.vixxo or FRESHDESK_API_KEY in .env"),
        ("freshservice", has_secret("FRESHSERVICE_API_KEY"), "freshservice_api_key in ~/.vixxo"),
        ("gateway/vixxolink/vixxonow (OAuth)", True, "complete OAuth in Cursor Settings → MCP (no token file required)"),
        ("salesforce CLI", check_cmd("sf"), "npm install -g @salesforce/cli && sf org login web"),
        ("github gh auth", check_gh_auth(), "gh auth login or set GITHUB_PERSONAL_ACCESS_TOKEN in .env"),
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
