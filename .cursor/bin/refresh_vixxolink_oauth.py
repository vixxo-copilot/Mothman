#!/usr/bin/env python3
"""One-time VixxoLink authorization-code login. Opens Chrome; no token values printed."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_env import (  # noqa: E402
    VIXXOLINK_AUTH_ID,
    VIXXOLINK_TOKEN_URL,
    mcp_tools_list_ok,
)

AUTHORIZE_URL = "https://vixxonow.com/mcp/vixxolink/oauth/authorize"
VIXXOLINK_URL = "https://vixxonow.com/mcp/vixxolink"
REDIRECT = "http://127.0.0.1:37882/oauth/callback"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CLIENT_INFO = Path.home() / ".mcp-auth" / "mcp-remote-v1" / f"{VIXXOLINK_AUTH_ID}_client_info.json"
TOKENS = Path.home() / ".mcp-auth" / "mcp-remote-v1" / f"{VIXXOLINK_AUTH_ID}_tokens.json"
SYNC = Path(__file__).resolve().parent / "sync_vixxolink_token.py"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _load_client_id() -> str:
    payload = json.loads(CLIENT_INFO.read_text(encoding="utf-8"))
    client_id = payload.get("client_id")
    if not isinstance(client_id, str) or not client_id.strip():
        raise SystemExit("status=FAIL reason=no_client_id")
    return client_id.strip()


class _Handler(BaseHTTPRequestHandler):
    result: dict[str, str] | None = None
    error: str | None = None

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/oauth/callback":
            self.send_error(404)
            return
        qs = urllib.parse.parse_qs(parsed.query)
        if qs.get("error"):
            _Handler.error = qs.get("error", ["denied"])[0]
            body = b"Sign-in failed. You can close this tab."
        else:
            code = (qs.get("code") or [""])[0]
            _Handler.result = {"code": code, "state": (qs.get("state") or [""])[0]}
            body = b"VixxoLink sign-in complete. You can close this tab."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def _exchange(code: str, verifier: str, client_id: str) -> dict:
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT,
        "code_verifier": verifier,
        "client_id": client_id,
    }
    req = urllib.request.Request(
        VIXXOLINK_TOKEN_URL,
        data=urllib.parse.urlencode(form).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "mcp-remote/0.1.38",
            "Origin": "https://vixxonow.com",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    client_id = _load_client_id()
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    state = secrets.token_urlsafe(24)
    auth = (
        f"{AUTHORIZE_URL}?response_type=code"
        f"&client_id={urllib.parse.quote(client_id)}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT, safe='')}"
        f"&code_challenge={urllib.parse.quote(challenge)}"
        f"&code_challenge_method=S256"
        f"&state={urllib.parse.quote(state)}"
        f"&scope=openid"
    )

    server = HTTPServer(("127.0.0.1", 37882), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print("callback=http://127.0.0.1:37882/oauth/callback")
    print("Opening Chrome for VixxoLink sign-in...")
    if CHROME.is_file():
        subprocess.Popen([str(CHROME), auth], close_fds=True)
    else:
        subprocess.Popen(["cmd", "/c", "start", "", auth], close_fds=True)

    thread.join(timeout=180)
    if _Handler.error:
        print(f"status=FAIL reason=oauth_{_Handler.error}")
        return 1
    if not _Handler.result or not _Handler.result.get("code"):
        print("status=FAIL reason=no_auth_code timeout=180s")
        return 1
    if _Handler.result.get("state") != state:
        print("status=FAIL reason=state_mismatch")
        return 1

    try:
        tokens = _exchange(_Handler.result["code"], verifier, client_id)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"status=FAIL reason=token_exchange type={type(exc).__name__}")
        return 1

    access = tokens.get("access_token")
    if not isinstance(access, str) or not access.strip():
        print("status=FAIL reason=no_access_token")
        return 1

    TOKENS.parent.mkdir(parents=True, exist_ok=True)
    TOKENS.write_text(json.dumps(tokens), encoding="utf-8")
    print(f"wrote={TOKENS}")
    print(f"tools_ok={mcp_tools_list_ok(VIXXOLINK_URL, access.strip())}")
    return subprocess.call([sys.executable, str(SYNC)])


if __name__ == "__main__":
    raise SystemExit(main())
