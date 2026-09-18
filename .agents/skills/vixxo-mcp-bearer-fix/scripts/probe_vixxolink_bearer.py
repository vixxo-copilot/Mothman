#!/usr/bin/env python3
"""Probe VixxoLink bearer health; optionally refresh or prompt OAuth sign-in."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BIN = ROOT / ".cursor" / "bin"
TMP_DIR = ROOT / ".tmp" / "vixxo-mcp-bearer"

sys.path.insert(0, str(BIN))
from mcp_env import (  # noqa: E402
    VIXXOLINK_AUTH_ID,
    VIXXOLINK_URL,
    access_token_expires_at_iso,
    access_token_exp_unix,
    ensure_vixxolink_bearer_for_url,
    load_oauth_payload,
    load_token_file,
    mcp_tools_list_ok,
    refresh_vixxolink_oauth_tokens,
    vixxolink_bearer_acceptable_for_launch,
)


def vixxolink_token_expiry_iso() -> str | None:
    token_path = Path.home() / ".vixxo" / "vixxolink_api_token"
    file_token = load_token_file(token_path)
    jwt_iso = access_token_expires_at_iso(file_token) if file_token else None
    if jwt_iso:
        return jwt_iso
    loaded = load_oauth_payload(VIXXOLINK_AUTH_ID)
    if not loaded:
        return None
    _, payload = loaded
    expires_at = payload.get("expires_at")
    if isinstance(expires_at, (int, float)):
        return datetime.fromtimestamp(expires_at / 1000).isoformat(sep=" ", timespec="seconds")
    return None


def needs_silent_refresh(report: dict) -> bool:
    if report["status"] != "ok":
        return True
    token_path = Path.home() / ".vixxo" / "vixxolink_api_token"
    file_token = load_token_file(token_path)
    exp = access_token_exp_unix(file_token) if file_token else None
    if exp is None:
        return False
    return exp - datetime.now().timestamp() < 15 * 60


def probe() -> dict:
    token_path = Path.home() / ".vixxo" / "vixxolink_api_token"
    file_token = load_token_file(token_path)
    launch_ok = bool(file_token) and vixxolink_bearer_acceptable_for_launch(
        VIXXOLINK_URL, file_token
    )
    usable = bool(ensure_vixxolink_bearer_for_url(VIXXOLINK_URL))
    return {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "endpoint": VIXXOLINK_URL,
        "vixxolink_api_token_file": token_path.is_file(),
        "vixxolink_launch_ok": launch_ok,
        "vixxolink_usable": usable,
        "vixxolink_tools_list": (
            mcp_tools_list_ok(VIXXOLINK_URL, file_token) if file_token else False
        ),
        "oauth_expires_at": vixxolink_token_expiry_iso(),
        "has_refresh_token": bool(
            (load_oauth_payload(VIXXOLINK_AUTH_ID) or (None, {}))[1].get("refresh_token")
        ),
        "status": "ok" if launch_ok else "needs_auth",
    }


def run_silent_refresh() -> tuple[bool, str]:
    refreshed = refresh_vixxolink_oauth_tokens()
    if refreshed and vixxolink_bearer_acceptable_for_launch(VIXXOLINK_URL, refreshed):
        sync = BIN / "sync_vixxolink_token.py"
        proc = subprocess.run(
            [sys.executable, str(sync)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            return True, "oauth_refresh_token"
        return False, f"sync_failed rc={proc.returncode}"
    return False, "no_silent_refresh"


def run_prompt_oauth() -> tuple[bool, str]:
    script = BIN / "refresh_vixxolink_oauth.py"
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    if proc.returncode != 0:
        return False, f"refresh_vixxolink_oauth rc={proc.returncode}"
    return True, "browser_oauth"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    parser.add_argument(
        "--silent-refresh",
        action="store_true",
        help="Try OAuth refresh_token grant + sync before probing",
    )
    parser.add_argument(
        "--prompt-oauth",
        action="store_true",
        help="Open Chrome sign-in when bearer still invalid (interactive)",
    )
    parser.add_argument(
        "--write-tmp",
        action="store_true",
        help="Write report to .tmp/vixxo-mcp-bearer/probe-vixxolink-latest.json",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Exit 1 when the bearer is not usable (morning cascade)",
    )
    args = parser.parse_args()

    report = probe()
    actions: list[dict[str, str]] = []

    if args.silent_refresh and needs_silent_refresh(report):
        ok, detail = run_silent_refresh()
        actions.append({"action": "silent_refresh", "ok": str(ok).lower(), "detail": detail})
        report = probe()

    if report["status"] != "ok" and args.prompt_oauth:
        ok, detail = run_prompt_oauth()
        actions.append({"action": "prompt_oauth", "ok": str(ok).lower(), "detail": detail})
        report = probe()

    report["actions"] = actions
    if report["status"] != "ok":
        report["fix"] = ".cursor/bin/refresh-vixxolink-bearer.cmd"

    if args.write_tmp:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        out = TMP_DIR / "probe-vixxolink-latest.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["artifact"] = str(out)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status={report['status']}")
        print(f"vixxolink_launch_ok={report['vixxolink_launch_ok']}")
        if report.get("oauth_expires_at"):
            print(f"oauth_expires_at={report['oauth_expires_at']}")
        for step in actions:
            print(f"action={step['action']} ok={step['ok']} detail={step['detail']}")
        if report["status"] != "ok":
            print(f"fix={report['fix']}")

    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
