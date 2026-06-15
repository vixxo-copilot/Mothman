#!/usr/bin/env python3
"""PolyAI project registry — multi-USP config from JSON, env, and Jupiter URLs."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import polyai_client

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = SCRIPT_DIR.parent / "reference" / "projects.json"

JUPITER_URL_RE = re.compile(
    r"https?://jupiter\.polyai\.app/(?P<account>[^/]+)/(?P<project>[^/?#]+)",
    re.IGNORECASE,
)


def load_registry() -> dict:
    if REGISTRY_PATH.is_file():
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    else:
        data = {
            "account_id": os.environ.get("POLYAI_ACCOUNT_ID", "vixxo-us"),
            "region": os.environ.get("POLYAI_REGION", "us"),
            "default_project": os.environ.get("POLYAI_PROJECT_ID", "vixxo-outbound-usp"),
            "projects": {},
        }

    projects = dict(data.get("projects") or {})
    default_project = (
        os.environ.get("POLYAI_PROJECT_ID")
        or data.get("default_project")
        or "vixxo-outbound-usp"
    )
    if default_project and default_project not in projects:
        projects[default_project] = {"label": default_project, "enabled": True}

    extra = os.environ.get("POLYAI_EXTRA_PROJECT_IDS", "")
    for project_id in extra.split(","):
        project_id = project_id.strip()
        if project_id and project_id not in projects:
            projects[project_id] = {"label": project_id, "enabled": True}

    data["projects"] = projects
    data["default_project"] = default_project
    data["account_id"] = os.environ.get("POLYAI_ACCOUNT_ID") or data.get("account_id") or "vixxo-us"
    data["region"] = os.environ.get("POLYAI_REGION") or data.get("region") or "us"
    return data


def enabled_projects(registry: dict | None = None) -> list[str]:
    registry = registry or load_registry()
    projects = registry.get("projects") or {}
    enabled = [pid for pid, meta in projects.items() if meta.get("enabled", True)]
    if enabled:
        return sorted(enabled)
    default_project = registry.get("default_project")
    return [default_project] if default_project else []


def resolve_project_id(project: str | None = None, registry: dict | None = None) -> str:
    registry = registry or load_registry()
    if project:
        projects = registry.get("projects") or {}
        if project in projects:
            return project
        matches = [pid for pid in projects if pid.endswith(project) or pid == project]
        if len(matches) == 1:
            return matches[0]
        return project
    return registry.get("default_project") or polyai_client.config_from_env()["POLYAI_PROJECT_ID"]


def config_for_project(project_id: str | None = None) -> dict[str, str]:
    polyai_client.load_dotenv()
    registry = load_registry()
    resolved = resolve_project_id(project_id, registry)
    api_key = os.environ.get("POLYAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing POLYAI_API_KEY in .env")
    return {
        "POLYAI_API_KEY": api_key,
        "POLYAI_REGION": registry["region"],
        "POLYAI_ACCOUNT_ID": registry["account_id"],
        "POLYAI_PROJECT_ID": resolved,
    }


def parse_jupiter_url(url: str) -> dict[str, str]:
    match = JUPITER_URL_RE.search(url.strip())
    if not match:
        raise SystemExit(
            "Could not parse Jupiter URL. Expected:\n"
            "  https://jupiter.polyai.app/{account_id}/{project_id}/..."
        )
    account_id = match.group("account")
    project_id = match.group("project")
    region = "us"
    if account_id.endswith("-uk"):
        region = "uk"
    elif account_id.endswith("-eu") or account_id.endswith("-euw"):
        region = "euw"
    return {
        "POLYAI_ACCOUNT_ID": account_id,
        "POLYAI_PROJECT_ID": project_id,
        "POLYAI_REGION": region,
    }


def export_csv_path(project_id: str, output_dir: Path | None = None) -> Path:
    root = output_dir or (polyai_client.repo_root() / "exports" / "polyai")
    return root / f"{project_id}-conversations.csv"


def project_label(project_id: str, registry: dict | None = None) -> str:
    registry = registry or load_registry()
    meta = (registry.get("projects") or {}).get(project_id) or {}
    return meta.get("label") or project_id
