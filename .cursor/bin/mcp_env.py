#!/usr/bin/env python3
"""Shared credential loading for Windows MCP launchers."""

from __future__ import annotations

import os
from pathlib import Path
import shutil


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
        # Also expose FRESHDESK_TOKEN as FRESHDESK_API_KEY when needed.
        if stem == "FRESHDESK_TOKEN" and not os.environ.get("FRESHDESK_API_KEY"):
            os.environ["FRESHDESK_API_KEY"] = secret
        if stem == "FRESHSERVICE_API_KEY" and not os.environ.get("FRESHSERVICE_API_KEY"):
            os.environ["FRESHSERVICE_API_KEY"] = secret


def load_workspace_env(root: Path | None = None) -> None:
    if root is None:
        root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")
    load_vixxo_secrets()
    ensure_node_path()


def ensure_node_path() -> None:
    """Ensure Node/npm directories are on PATH for Cursor-spawned MCP processes."""
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
