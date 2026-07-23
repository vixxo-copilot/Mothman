#!/usr/bin/env python3
"""Shared credential loading for MCP launchers."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

GATEWAY_AUTH_ID = "6486a04241e2b8e809e7c6f312812185"
VIXXOLINK_AUTH_ID = "86f3d1e19c821fab2297f5f94aac2d68"
# Legacy/alternate mcp-remote client registrations seen in older workspaces.
VIXXOLINK_AUTH_IDS = (
    VIXXOLINK_AUTH_ID,
    "bd3af626f5128d032de269bd1f9de2be",
)
BO_UNIVERSE_URL = "https://vixxonow.com/mcp/bo-universe"
GATEWAY_URL = "https://vixxonow.com/mcp/gateway"
VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val and not os.environ.get(key):
            os.environ[key] = val


def load_vixxo_secrets() -> None:
    vixxo = Path.home() / ".vixxo"
    if not vixxo.is_dir():
        return
    for path in vixxo.iterdir():
        if not path.is_file():
            continue
        secret = path.read_text(encoding="utf-8").strip()
        if not secret:
            continue
        stem = path.stem.upper().replace("-", "_")
        if not os.environ.get(stem):
            os.environ[stem] = secret


def load_workspace_env(root: Path | None = None) -> None:
    if root is None:
        root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")
    load_vixxo_secrets()
    ensure_node_path()


def ensure_node_path() -> None:
    if os.name != "nt":
        return
    extras: list[str] = []
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    node_dir = Path(program_files) / "nodejs"
    if node_dir.is_dir():
        extras.append(str(node_dir))
    appdata = os.environ.get("APPDATA")
    if appdata:
        npm_dir = Path(appdata) / "npm"
        if npm_dir.is_dir():
            extras.append(str(npm_dir))
    if not extras:
        return
    current = os.environ.get("PATH", "")
    for entry in extras:
        if entry.lower() not in current.lower():
            current = f"{entry};{current}" if current else entry
    os.environ["PATH"] = current


def resolve_npx() -> str:
    found = shutil.which("npx")
    if found:
        return found
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        for candidate in (
            Path(program_files) / "nodejs" / "npx.cmd",
            Path(os.environ.get("APPDATA", "")) / "npm" / "npx.cmd",
        ):
            if candidate.is_file():
                return str(candidate)
    return "npx"


def first_env(*names: str) -> str | None:
    for name in names:
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return None


def load_token_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    val = path.read_text(encoding="utf-8").strip()
    return val or None


def load_oauth_access_token(auth_id: str) -> str | None:
    base = Path.home() / ".mcp-auth"
    if not base.is_dir():
        return None
    candidates = sorted(base.glob(f"mcp-remote-*/{auth_id}_tokens.json"), reverse=True)
    for token_path in candidates:
        try:
            payload = json.loads(token_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        access = payload.get("access_token")
        if isinstance(access, str) and access.strip():
            return access.strip()
    return None


def resolve_vixxo_bearer_token() -> str | None:
    load_workspace_env()
    token = first_env("GATEWAY_API_TOKEN", "VIXXONOW_API_TOKEN")
    if token:
        return token

    vixxo = Path.home() / ".vixxo"
    for name in ("gateway_api_token", "vixxonow_api_token"):
        token = load_token_file(vixxo / name)
        if token:
            return token

    return load_oauth_access_token(GATEWAY_AUTH_ID)


def resolve_vixxolink_bearer_token() -> str | None:
    load_workspace_env()
    token = first_env("VIXXOLINK_API_TOKEN")
    if token:
        return token

    token = load_token_file(Path.home() / ".vixxo" / "vixxolink_api_token")
    if token:
        return token

    for auth_id in VIXXOLINK_AUTH_IDS:
        token = load_oauth_access_token(auth_id)
        if token:
            return token

    return None


def resolve_bearer_token_for_url(url: str) -> str | None:
    if "/vixxolink" in url:
        return resolve_vixxolink_bearer_token()
    return resolve_vixxo_bearer_token()


def auth_header_value(token: str) -> str:
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"
