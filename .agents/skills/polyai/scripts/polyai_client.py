#!/usr/bin/env python3
"""PolyAI Conversations API client."""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import certifi
except ImportError:
    certifi = None

REGION_PLATFORM = {
    "us": "us-1",
    "uk": "uk-1",
    "euw": "euw-1",
    "eu": "euw-1",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_dotenv(root: Path | None = None) -> None:
    env_path = (root or repo_root()) / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def platform_base(region: str) -> str:
    platform_region = REGION_PLATFORM.get(region.lower())
    if not platform_region:
        raise SystemExit(f"Unsupported POLYAI_REGION: {region}")
    return f"https://api.{platform_region}.platform.polyai.app"


def ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def request_json(url: str, api_key: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"x-api-key": api_key, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_context()) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {url}\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Request failed: {exc}") from exc


def config_from_env(project_id: str | None = None) -> dict[str, str]:
    load_dotenv()
    if project_id is not None:
        from polyai_projects import config_for_project

        return config_for_project(project_id)

    required = ["POLYAI_API_KEY", "POLYAI_REGION", "POLYAI_ACCOUNT_ID", "POLYAI_PROJECT_ID"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        from polyai_projects import load_registry

        registry = load_registry()
        if os.environ.get("POLYAI_API_KEY") and registry.get("default_project"):
            return {
                "POLYAI_API_KEY": os.environ["POLYAI_API_KEY"],
                "POLYAI_REGION": registry["region"],
                "POLYAI_ACCOUNT_ID": registry["account_id"],
                "POLYAI_PROJECT_ID": registry["default_project"],
            }
        raise SystemExit(
            "Missing env vars: "
            + ", ".join(missing)
            + "\nCopy .env.example → .env and set PolyAI values."
        )
    return {name: os.environ[name] for name in required}


def conversations_url(cfg: dict[str, str], suffix: str = "") -> str:
    base = platform_base(cfg["POLYAI_REGION"])
    path = f"/v3/{cfg['POLYAI_ACCOUNT_ID']}/{cfg['POLYAI_PROJECT_ID']}/conversations{suffix}"
    return base + path


def cmd_health(cfg: dict[str, str]) -> int:
    url = conversations_url(cfg) + "?limit=1"
    data = request_json(url, cfg["POLYAI_API_KEY"])
    print(
        json.dumps(
            {
                "ok": True,
                "region": cfg["POLYAI_REGION"],
                "account_id": cfg["POLYAI_ACCOUNT_ID"],
                "project_id": cfg["POLYAI_PROJECT_ID"],
                "sample_keys": sorted(data.keys()) if isinstance(data, dict) else [],
            },
            indent=2,
        )
    )
    return 0


def cmd_list(cfg: dict[str, str], limit: int) -> int:
    url = conversations_url(cfg) + f"?limit={limit}"
    data = request_json(url, cfg["POLYAI_API_KEY"])
    print(json.dumps(data, indent=2))
    return 0


def cmd_get(cfg: dict[str, str], conversation_id: str) -> int:
    url = conversations_url(cfg, f"/{conversation_id}")
    data = request_json(url, cfg["POLYAI_API_KEY"])
    print(json.dumps(data, indent=2))
    return 0


def cmd_projects() -> int:
    from polyai_projects import enabled_projects, load_registry, project_label

    registry = load_registry()
    payload = {
        "account_id": registry["account_id"],
        "region": registry["region"],
        "default_project": registry["default_project"],
        "projects": [
            {
                "project_id": project_id,
                "label": project_label(project_id, registry),
                "enabled": (registry.get("projects") or {}).get(project_id, {}).get("enabled", True),
            }
            for project_id in enabled_projects(registry)
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_health_all() -> int:
    from polyai_projects import config_for_project, enabled_projects

    results = []
    for project_id in enabled_projects():
        cfg = config_for_project(project_id)
        try:
            url = conversations_url(cfg) + "?limit=1"
            data = request_json(url, cfg["POLYAI_API_KEY"])
            results.append(
                {
                    "project_id": project_id,
                    "ok": True,
                    "keys": sorted(data.keys()) if isinstance(data, dict) else [],
                }
            )
        except SystemExit as exc:
            results.append({"project_id": project_id, "ok": False, "error": str(exc)[:200]})
    print(json.dumps({"results": results}, indent=2))
    return 0


def cmd_parse_jupiter(url: str) -> int:
    from polyai_projects import parse_jupiter_url

    print(json.dumps(parse_jupiter_url(url), indent=2))
    return 0


def add_project_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project",
        help="PolyAI project_id (default: POLYAI_PROJECT_ID or projects.json default)",
    )


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="PolyAI Conversations API helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("projects", help="List configured USP projects").set_defaults(
        func=lambda _a: cmd_projects()
    )

    health_all = sub.add_parser("health-all", help="Health check every enabled project")
    health_all.set_defaults(func=lambda _a: cmd_health_all())

    parse = sub.add_parser("parse-jupiter", help="Parse Jupiter / Studio URL → project IDs")
    parse.add_argument("url")
    parse.set_defaults(func=lambda a: cmd_parse_jupiter(a.url))

    health = sub.add_parser("health", help="Verify credentials with a 1-row list call")
    add_project_arg(health)
    health.set_defaults(func=lambda a: cmd_health(config_from_env(a.project)))

    list_parser = sub.add_parser("list", help="List recent conversations")
    list_parser.add_argument("--limit", type=int, default=10)
    add_project_arg(list_parser)
    list_parser.set_defaults(func=lambda a: cmd_list(config_from_env(a.project), a.limit))

    get_parser = sub.add_parser("get", help="Get one conversation by ID (may 404 on v3)")
    get_parser.add_argument("--conversation-id", required=True)
    add_project_arg(get_parser)
    get_parser.set_defaults(
        func=lambda a: cmd_get(config_from_env(a.project), a.conversation_id)
    )

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
