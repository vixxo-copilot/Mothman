"""Minimal Salesforce CLI helpers for sp-fd-sf-duplicate-bridge merge automation."""

from __future__ import annotations

import json
import os
import subprocess
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
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = proc.stdout.strip()
    err = proc.stderr.strip()
    try:
        data = json.loads(out) if out else {}
    except json.JSONDecodeError:
        data = {"raw": out}
    ok = proc.returncode == 0 and data.get("status", proc.returncode) == 0
    return {"ok": ok, "data": data, "stderr": err, "cmd": args[:6]}


def sf_query(soql: str, org: str = "vixxo") -> list[dict]:
    r = run_sf(["data", "query", "--query", soql], org=org)
    if not r["ok"]:
        return []
    return ((r["data"].get("result") or {}).get("records") or [])


def link_document_to_case(content_document_id: str, case_id: str, org: str = "vixxo") -> dict:
    existing = sf_query(
        "SELECT Id FROM ContentDocumentLink "
        f"WHERE LinkedEntityId = '{case_id}' "
        f"AND ContentDocumentId = '{content_document_id}' LIMIT 1",
        org=org,
    )
    if existing:
        return {"ok": True, "skipped": True}
    return run_sf(
        [
            "data",
            "create",
            "record",
            "--sobject",
            "ContentDocumentLink",
            "--values",
            (
                f"ContentDocumentId={content_document_id} "
                f"LinkedEntityId={case_id} ShareType=V Visibility=AllUsers"
            ),
        ],
        org=org,
    )


def copy_case_files(source_case_id: str, target_case_id: str, org: str = "vixxo") -> list[dict]:
    links = sf_query(
        "SELECT ContentDocumentId, ContentDocument.Title "
        f"FROM ContentDocumentLink WHERE LinkedEntityId = '{source_case_id}'",
        org=org,
    )
    results = []
    for link in links:
        doc_id = link.get("ContentDocumentId")
        if not doc_id:
            continue
        results.append(link_document_to_case(doc_id, target_case_id, org=org))
    return results


def post_case_comment(case_id: str, body: str, org: str = "vixxo", published: bool = True) -> dict:
    text = body.replace("'", "\\'").replace("\r\n", "\n").replace("\n", " ")[:4000]
    pub = "true" if published else "false"
    return run_sf(
        [
            "data",
            "create",
            "record",
            "--sobject",
            "CaseComment",
            "--values",
            f"ParentId={case_id} CommentBody='{text}' IsPublished={pub}",
        ],
        org=org,
    )


def create_completed_task(case_id: str, subject: str, description: str, org: str = "vixxo") -> dict:
    subj = subject.replace("'", "\\'")[:255]
    desc = description.replace("'", "\\'")[:32000]
    return run_sf(
        [
            "data",
            "create",
            "record",
            "--sobject",
            "Task",
            "--values",
            (
                f"Subject='{subj}' Description='{desc}' WhatId={case_id} "
                "Status=Completed Priority=Normal"
            ),
        ],
        org=org,
    )


def close_case(
    case_id: str,
    org: str = "vixxo",
    closed_reason: str = "Duplicate",
) -> dict:
    reason = closed_reason.replace("'", "\\'")
    return run_sf(
        [
            "data",
            "update",
            "record",
            "--sobject",
            "Case",
            "--record-id",
            case_id,
            "--values",
            f"Status=Closed Not_Filled_Reason__c='{reason}'",
        ],
        org=org,
    )
