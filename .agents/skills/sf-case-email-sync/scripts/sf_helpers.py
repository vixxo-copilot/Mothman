"""Salesforce helpers for sf-case-email-sync."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def sf_path() -> str:
    env = os.environ.get("SF_CLI_PATH", "").strip()
    if env:
        return env
    npm_sf = Path(os.environ.get("APPDATA", "")) / "npm" / "sf.cmd"
    if npm_sf.is_file():
        return str(npm_sf)
    return "sf"


def run_sf(args: list[str], org: str = "vixxo") -> dict:
    cmd = [sf_path(), *args, "--target-org", org, "--json"]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    out = proc.stdout.strip()
    err = proc.stderr.strip()
    try:
        data = json.loads(out) if out else {}
    except json.JSONDecodeError:
        data = {"raw": out}
    ok = proc.returncode == 0 and data.get("status", proc.returncode) == 0
    return {"ok": ok, "data": data, "stderr": err}


def sf_query(soql: str, org: str = "vixxo") -> list[dict]:
    r = run_sf(["data", "query", "--query", soql], org=org)
    if not r["ok"]:
        raise RuntimeError(r.get("stderr") or r["data"])
    return ((r["data"].get("result") or {}).get("records") or [])


def sf_auth(org: str = "vixxo") -> tuple[str, str]:
    env = os.environ.copy()
    env["SF_TEMP_SHOW_SECRETS"] = "true"
    proc = subprocess.run(
        [sf_path(), "org", "display", "--target-org", org, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        env=env,
    )
    data = json.loads(proc.stdout)["result"]
    return data["accessToken"], data["instanceUrl"]


def sf_org_username(org: str = "vixxo") -> str:
    proc = subprocess.run(
        [sf_path(), "org", "display", "--target-org", org, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return json.loads(proc.stdout)["result"]["username"]


def resolve_user_id(org: str, owner_email: str | None = None) -> str:
    email = (owner_email or os.environ.get("SF_CASE_SYNC_OWNER_EMAIL") or "").strip()
    if not email:
        email = sf_org_username(org)
    safe = email.replace("'", "\\'")
    rows = sf_query(
        "SELECT Id, Email, Username FROM User "
        f"WHERE IsActive = true AND (Email = '{safe}' OR Username = '{safe}') LIMIT 1",
        org=org,
    )
    if not rows:
        raise RuntimeError(f"No active Salesforce User for {email}")
    return rows[0]["Id"]


def sf_post(token: str, instance_url: str, sobject: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{instance_url}/services/data/v67.0/sobjects/{sobject}/",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_file(case_id: str, file_path: Path, title: str, org: str = "vixxo") -> dict:
    r = run_sf(
        [
            "data",
            "create",
            "file",
            "--file",
            str(file_path),
            "--parent-id",
            case_id,
            "--title",
            title,
        ],
        org=org,
    )
    if not r["ok"]:
        raise RuntimeError(r.get("stderr") or r["data"])
    return r["data"]


def case_file_titles(case_id: str, org: str = "vixxo") -> set[str]:
    rows = sf_query(
        "SELECT ContentDocument.Title FROM ContentDocumentLink "
        f"WHERE LinkedEntityId = '{case_id}'",
        org=org,
    )
    return {
        rec["ContentDocument"]["Title"]
        for rec in rows
        if rec.get("ContentDocument", {}).get("Title")
    }


def case_message_identifiers(case_id: str, org: str = "vixxo") -> set[str]:
    rows = sf_query(
        "SELECT MessageIdentifier FROM EmailMessage "
        f"WHERE ParentId = '{case_id}' AND MessageIdentifier != null",
        org=org,
    )
    return {rec["MessageIdentifier"] for rec in rows if rec.get("MessageIdentifier")}


def title_exists(title: str, titles: set[str]) -> bool:
    base = title.removesuffix(".eml")
    return title in titles or base in titles or f"{base}.eml" in titles
