#!/usr/bin/env python3
"""Shared credential loading for MCP launchers."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

GATEWAY_AUTH_ID = "6486a04241e2b8e809e7c6f312812185"
VIXXOLINK_AUTH_ID = "86f3d1e19c821fab2297f5f94aac2d68"
# md5("https://vixxonow.com/mcp/vixxonow") — own OAuth registration, not VixxoLink.
VIXXONOW_AUTH_ID = "bd3af626f5128d032de269bd1f9de2be"
VIXXOLINK_AUTH_IDS = (VIXXOLINK_AUTH_ID,)
BO_UNIVERSE_URL = "https://vixxonow.com/mcp/bo-universe"
POWERBI_URL = "https://vixxonow.com/mcp/powerbi"
GATEWAY_URL = "https://vixxonow.com/mcp/gateway"
VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"
VIXXONOW_URL = "https://vixxonow.com/mcp/vixxonow"
VIXXOLINK_TOKEN_URL = "https://vixxonow.com/mcp/vixxolink/oauth/token"
VIXXONOW_TOKEN_URL = "https://vixxonow.com/mcp/vixxonow/oauth/token"


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
        if stem in ("GATEWAY_API_TOKEN", "VIXXONOW_API_TOKEN") and not is_gateway_token_usable(secret):
            continue
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


def oauth_token_paths(auth_id: str) -> list[Path]:
    base = Path.home() / ".mcp-auth"
    if not base.is_dir():
        return []
    return sorted(base.glob(f"mcp-remote-*/{auth_id}_tokens.json"), reverse=True)


def load_oauth_payload(auth_id: str) -> tuple[Path, dict[str, Any]] | None:
    for token_path in oauth_token_paths(auth_id):
        try:
            payload = json.loads(token_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, dict):
            return token_path, payload
    return None


def load_oauth_client_info(auth_id: str, token_path: Path | None = None) -> dict[str, Any] | None:
    candidates: list[Path] = []
    if token_path is not None:
        candidates.append(token_path.with_name(f"{auth_id}_client_info.json"))
    base = Path.home() / ".mcp-auth"
    if base.is_dir():
        candidates.extend(sorted(base.glob(f"mcp-remote-*/{auth_id}_client_info.json"), reverse=True))
    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, dict):
            return payload
    return None


def load_oauth_access_token(auth_id: str) -> str | None:
    loaded = load_oauth_payload(auth_id)
    if not loaded:
        return None
    _, payload = loaded
    access = payload.get("access_token")
    if isinstance(access, str) and access.strip():
        return access.strip()
    return None


def refresh_oauth_tokens(auth_id: str, token_url: str) -> str | None:
    """Refresh an mcp-remote OAuth access token via refresh_token grant.

    Updates ~/.mcp-auth tokens.json in place and returns the new access token.
    """
    loaded = load_oauth_payload(auth_id)
    if not loaded:
        return None
    token_path, payload = loaded
    refresh = payload.get("refresh_token")
    if not isinstance(refresh, str) or not refresh.strip():
        return None

    client = load_oauth_client_info(auth_id, token_path) or {}
    client_id = client.get("client_id")
    form: dict[str, str] = {
        "grant_type": "refresh_token",
        "refresh_token": refresh.strip(),
    }
    if isinstance(client_id, str) and client_id.strip():
        form["client_id"] = client_id.strip()

    data = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(
        token_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            # Cloudflare 403s bare urllib; mcp-remote's UA is accepted.
            "User-Agent": "mcp-remote/0.1.38",
            "Origin": urllib.parse.urlparse(token_url)._replace(path="", params="", query="", fragment="").geturl(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    access = body.get("access_token")
    if not isinstance(access, str) or not access.strip():
        return None

    updated = dict(payload)
    updated["access_token"] = access.strip()
    if isinstance(body.get("refresh_token"), str) and body["refresh_token"].strip():
        updated["refresh_token"] = body["refresh_token"].strip()
    if "expires_in" in body:
        updated["expires_in"] = body["expires_in"]
    if isinstance(body.get("token_type"), str) and body["token_type"].strip():
        updated["token_type"] = body["token_type"].strip()

    token_path.write_text(json.dumps(updated), encoding="utf-8")
    return access.strip()


def refresh_vixxolink_oauth_tokens(auth_id: str = VIXXOLINK_AUTH_ID) -> str | None:
    """Refresh VixxoLink access token via OAuth refresh_token grant."""
    return refresh_oauth_tokens(auth_id, VIXXOLINK_TOKEN_URL)


def refresh_vixxonow_oauth_tokens(auth_id: str = VIXXONOW_AUTH_ID) -> str | None:
    """Refresh VixxoNow access token via OAuth refresh_token grant."""
    return refresh_oauth_tokens(auth_id, VIXXONOW_TOKEN_URL)



def gateway_token_expiry(token: str) -> datetime | None:
    """Parse CGAGNER:YYYYMMDDHHMMSS:... stamp when present."""
    parts = token.strip().split(":")
    if len(parts) < 2:
        return None
    stamp = parts[1]
    if len(stamp) < 14 or not stamp[:14].isdigit():
        return None
    try:
        return datetime.strptime(stamp[:14], "%Y%m%d%H%M%S")
    except ValueError:
        return None


def is_gateway_token_usable(token: str | None) -> bool:
    if not token or not token.strip():
        return False
    expiry = gateway_token_expiry(token)
    if expiry is None:
        # Non-CGAGNER shapes (JWT/etc): keep and let the server reject if needed.
        return True
    return expiry > datetime.now()


def collect_gateway_bearer_candidates() -> list[str]:
    load_workspace_env()
    candidates: list[str] = []
    seen: set[str] = set()

    def add(token: str | None) -> None:
        if not token or not token.strip():
            return
        value = token.strip()
        if value in seen:
            return
        seen.add(value)
        candidates.append(value)

    add(first_env("GATEWAY_API_TOKEN", "VIXXONOW_API_TOKEN"))
    vixxo = Path.home() / ".vixxo"
    for name in ("gateway_api_token", "vixxonow_api_token"):
        add(load_token_file(vixxo / name))
    add(load_oauth_access_token(GATEWAY_AUTH_ID))
    return candidates


def ensure_gateway_bearer_for_url(url: str) -> str | None:
    """Return a bearer token that tools/list accepts for url (no browser OAuth)."""
    for token in collect_gateway_bearer_candidates():
        if mcp_tools_list_ok(url, token):
            return token
    return None


def gateway_bearer_failure_message(url: str | None = None) -> str:
    raw = load_token_file(Path.home() / ".vixxo" / "gateway_api_token")
    expiry = gateway_token_expiry(raw) if raw else None
    lines = [
        "Gateway bearer missing or rejected by the server (no browser OAuth fallback).",
        "Fix: .cursor/bin/refresh-gateway-bearer.cmd (one browser sign-in in terminal only).",
    ]
    if expiry is not None:
        lines.insert(
            1,
            f"Local gateway_api_token stamp: {expiry.isoformat(sep=' ', timespec='seconds')}.",
        )
    if url:
        lines.append(f"Endpoint: {url}")
    lines.append(
        "Then restart gateway, business-objects, powerbi-prod, vixxonow, chatfpt, and dynamics365 in Cursor MCP."
    )
    return "\n".join(lines)


def resolve_vixxo_bearer_token() -> str | None:
    load_workspace_env()
    token = first_env("GATEWAY_API_TOKEN", "VIXXONOW_API_TOKEN")
    if is_gateway_token_usable(token):
        return token

    vixxo = Path.home() / ".vixxo"
    for name in ("gateway_api_token", "vixxonow_api_token"):
        token = load_token_file(vixxo / name)
        if is_gateway_token_usable(token):
            return token

    token = load_oauth_access_token(GATEWAY_AUTH_ID)
    if is_gateway_token_usable(token):
        return token
    return None


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


def mcp_tools_list_ok(url: str, token: str) -> bool:
    """Return True if tools/list accepts this bearer. Does not print the token."""
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "mcp-remote/0.1.38",
            "Authorization": auth_header_value(token),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            if resp.status != 200:
                return False
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False
    return isinstance(body, dict) and "result" in body


def ensure_vixxolink_access_token() -> str | None:
    """Prefer a freshly refreshed OAuth access token, else fall back to cache/file."""
    refreshed = refresh_vixxolink_oauth_tokens()
    if refreshed:
        return refreshed
    return resolve_vixxolink_bearer_token()


def ensure_vixxolink_bearer_for_url(url: str = VIXXOLINK_URL) -> str | None:
    """Return a bearer for VixxoLink MCP. Prefer shared gateway_api_token when Gateway is up."""
    gateway_token = ensure_gateway_bearer_for_url(GATEWAY_URL)
    if gateway_token:
        if mcp_tools_list_ok(url, gateway_token):
            return gateway_token
        if "/vixxolink" in url:
            return gateway_token

    candidates: list[str] = []
    seen: set[str] = set()

    def add(token: str | None) -> None:
        if not token or not token.strip():
            return
        value = token.strip()
        if value in seen:
            return
        seen.add(value)
        candidates.append(value)

    add(refresh_vixxolink_oauth_tokens())
    load_workspace_env()
    add(first_env("VIXXOLINK_API_TOKEN"))
    add(load_token_file(Path.home() / ".vixxo" / "vixxolink_api_token"))
    for auth_id in VIXXOLINK_AUTH_IDS:
        add(load_oauth_access_token(auth_id))

    for token in candidates:
        if mcp_tools_list_ok(url, token):
            return token
    return None


def vixxolink_bearer_failure_message(url: str | None = None) -> str:
    lines = [
        "VixxoLink bearer missing or rejected (no browser OAuth in Cursor).",
        "Fix: python .cursor/bin/sync_gateway_token.py",
        "If gateway is still red: .cursor/bin/refresh-gateway-bearer.cmd",
        "Legacy VixxoLink-only login: python .cursor/bin/refresh_vixxolink_oauth.py",
    ]
    if url:
        lines.append(f"Endpoint: {url}")
    lines.append("Then restart vixxolink in Cursor Settings -> MCP.")
    return "\n".join(lines)


def resolve_bearer_token_for_url(url: str) -> str | None:
    if "/vixxolink" in url:
        return ensure_vixxolink_bearer_for_url(url)
    return ensure_gateway_bearer_for_url(url) or resolve_vixxo_bearer_token()


def auth_header_value(token: str) -> str:
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"


MCP_REMOTE_CONFIG_VERSION = 1


def mcp_remote_server_url_hash(server_url: str, headers: dict[str, str] | None = None) -> str:
    """Match mcp-remote getServerUrlHash (URL, then JSON.stringify(headers, sortedKeys))."""
    parts = [server_url]
    if headers:
        sorted_keys = sorted(headers)
        parts.append(json.dumps({k: headers[k] for k in sorted_keys}, separators=(",", ":")))
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def mcp_remote_config_dirs() -> list[Path]:
    base = Path.home() / ".mcp-auth"
    dirs = [base / f"mcp-remote-v{MCP_REMOTE_CONFIG_VERSION}"]
    if base.is_dir():
        dirs.extend(sorted(p for p in base.glob("mcp-remote-*") if p.is_dir() and p not in dirs))
    return dirs


def clear_vixxolink_oauth_in_progress() -> int:
    """Remove in-flight VixxoLink PKCE files so mcp-remote does not resume browser OAuth."""
    removed = 0
    prefix = f"{VIXXOLINK_AUTH_ID}_code_verifier"
    lock_suffix = f"{VIXXOLINK_AUTH_ID}_lock.json"
    for config_dir in mcp_remote_config_dirs():
        if not config_dir.is_dir():
            continue
        for path in config_dir.iterdir():
            name = path.name
            if name.startswith(prefix) or name == lock_suffix:
                path.unlink(missing_ok=True)
                removed += 1
    return removed


def mirror_gateway_bearer_to_vixxolink(token: str) -> Path:
    """Keep ~/.vixxo/vixxolink_api_token aligned with the shared Gateway bearer."""
    token_path = Path.home() / ".vixxo" / "vixxolink_api_token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(token.strip(), encoding="utf-8")
    return token_path


def clear_gateway_oauth_in_progress() -> int:
    """Remove in-flight Gateway PKCE files so mcp-remote does not resume browser OAuth."""
    removed = 0
    prefix = f"{GATEWAY_AUTH_ID}_code_verifier"
    lock_suffix = f"{GATEWAY_AUTH_ID}_lock.json"
    for config_dir in mcp_remote_config_dirs():
        if not config_dir.is_dir():
            continue
        for path in config_dir.iterdir():
            name = path.name
            if name.startswith(prefix) or name == lock_suffix:
                path.unlink(missing_ok=True)
                removed += 1
    return removed


def seed_mcp_remote_token_cache(server_url: str, token: str, headers: dict[str, str]) -> Path:
    """Write mcp-remote tokens.json so bearer launches skip browser OAuth."""
    raw = token.strip()
    if raw.lower().startswith("bearer "):
        raw = raw.split(None, 1)[1]

    # CGAGNER:YYYYMMDDHHMMSS is advisory. Using it as expires_at makes
    # mcp-remote treat the cache as expired and start OAuth for a refresh_token.
    now_ms = int(datetime.now().timestamp() * 1000)
    expires_ms = now_ms + 7 * 86400 * 1000
    payload = json.dumps(
        {"access_token": raw, "token_type": "Bearer", "expires_at": expires_ms},
        separators=(",", ":"),
    )
    hashes = {mcp_remote_server_url_hash(server_url, headers), mcp_remote_server_url_hash(server_url)}
    if server_url.rstrip("/").endswith("/gateway"):
        hashes.add(GATEWAY_AUTH_ID)
    if server_url.rstrip("/").endswith("/vixxolink"):
        hashes.add(VIXXOLINK_AUTH_ID)
    primary: Path | None = None
    for config_dir in mcp_remote_config_dirs():
        config_dir.mkdir(parents=True, exist_ok=True)
        for url_hash in hashes:
            path = config_dir / f"{url_hash}_tokens.json"
            path.write_text(payload, encoding="utf-8")
            if primary is None and config_dir.name == f"mcp-remote-v{MCP_REMOTE_CONFIG_VERSION}":
                primary = path
    if primary is None:
        raise RuntimeError("failed to seed mcp-remote token cache")
    return primary


def launch_mcp_remote_with_bearer(server_url: str, token: str) -> int:
    header = auth_header_value(token)
    headers = {"Authorization": header}
    if server_url.rstrip("/").endswith("/gateway"):
        clear_gateway_oauth_in_progress()
    if server_url.rstrip("/").endswith("/vixxolink"):
        clear_vixxolink_oauth_in_progress()
    seed_mcp_remote_token_cache(server_url, token, headers)
    npx = resolve_npx()
    return subprocess.call(
        [
            npx,
            "-y",
            "mcp-remote",
            server_url,
            "--header",
            f"Authorization:{header}",
        ]
    )
