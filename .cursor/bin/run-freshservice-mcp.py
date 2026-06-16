#!/usr/bin/env python3
"""Windows launcher for freshservice-mcp — mirrors bin/run-freshservice-mcp.sh."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val and not os.environ.get(key):
            os.environ[key] = val


def load_secret_file(path: Path, target: str) -> None:
    if os.environ.get(target) or not path.is_file():
        return
    secret = path.read_text(encoding="utf-8").strip()
    if secret:
        os.environ[target] = secret


def tool_python() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not set")
    candidate = Path(appdata) / "uv" / "tools" / "freshservice-mcp" / "Scripts" / "python.exe"
    if candidate.is_file():
        return candidate

    print("Freshservice MCP: installing freshservice-mcp via uv...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "uv", "tool", "install", "freshservice-mcp"])
    if not candidate.is_file():
        raise RuntimeError(f"freshservice-mcp venv missing at {candidate}")
    return candidate


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")
    load_secret_file(Path.home() / ".vixxo" / "freshservice_api_key", "FRESHSERVICE_API_KEY")
    load_secret_file(Path.home() / ".vixxo" / "freshservice_token", "FRESHSERVICE_API_KEY")

    os.environ.setdefault("FRESHSERVICE_DOMAIN", "vixxo.freshservice.com")

    if not os.environ.get("FRESHSERVICE_API_KEY") and os.environ.get("FRESHSERVICE_APIKEY"):
        os.environ["FRESHSERVICE_API_KEY"] = os.environ["FRESHSERVICE_APIKEY"]

    if not os.environ.get("FRESHSERVICE_API_KEY"):
        print(
            "Freshservice MCP: FRESHSERVICE_API_KEY not set — server will start but API tools will fail until configured.",
            file=sys.stderr,
        )
        print(
            "Fix: set FRESHSERVICE_API_KEY in .env or save key to ~/.vixxo/freshservice_api_key, then restart MCP.",
            file=sys.stderr,
        )

    python = tool_python()
    return subprocess.call([str(python), "-m", "freshservice_mcp.server", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
