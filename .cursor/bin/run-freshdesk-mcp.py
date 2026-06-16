#!/usr/bin/env python3
"""Windows launcher for freshdesk-mcp — loads credentials then starts stdio server."""

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


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")

    home_vixxo = Path.home() / ".vixxo"
    load_secret_file(home_vixxo / "freshdesk_token", "FRESHDESK_API_KEY")
    load_secret_file(home_vixxo / "freshdesk_api_key", "FRESHDESK_API_KEY")

    if not os.environ.get("FRESHDESK_API_KEY") and os.environ.get("FRESHDESK_TOKEN"):
        os.environ["FRESHDESK_API_KEY"] = os.environ["FRESHDESK_TOKEN"]

    os.environ.setdefault("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com")
    os.environ.setdefault("NODE_ENV", "production")

    if not os.environ.get("FRESHDESK_API_KEY"):
        print(
            "Freshdesk MCP: FRESHDESK_API_KEY not set — server will start but API tools will fail until configured.",
            file=sys.stderr,
        )
        print(
            "Fix: set FRESHDESK_API_KEY in .env or save key to ~/.vixxo/freshdesk_token, then restart MCP.",
            file=sys.stderr,
        )

    npx = os.environ.get("NPX", "npx")
    return subprocess.call([npx, "-y", "freshdesk-mcp", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
