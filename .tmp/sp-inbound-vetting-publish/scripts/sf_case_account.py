#!/usr/bin/env python3
"""Update SF Case AccountId when inbound vetting resolves a Known SP."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

# Intake placeholders — replace when vetting resolves a Known SP Account.
PLACEHOLDER_ACCOUNT_IDS = frozenset(
    {
        "001TS00000CLPi9YAH",  # Vixxo Corporation
        "001TS00000mWdvSYAS",  # Service Provider Support Shell Account
    }
)


def sf_bin() -> str:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidate = Path(appdata) / "npm" / "sf.cmd"
            if candidate.is_file():
                return str(candidate)
    return "sf"


def posture_allows_account_update(posture: str) -> bool:
    return (posture or "").startswith("Known SP")


def should_update_case_account(
    posture: str,
    current_account_id: str | None,
    target_account_id: str | None,
) -> bool:
    if not posture_allows_account_update(posture):
        return False
    if not target_account_id:
        return False
    current = (current_account_id or "").strip()
    target = target_account_id.strip()
    if not current:
        return True
    if current == target:
        return False
    if current in PLACEHOLDER_ACCOUNT_IDS:
        return True
    return False


def account_label(account: dict | None) -> str:
    if not account:
        return "Unknown"
    sp = str(account.get("Service_Provider_Number__c") or "").strip()
    name = str(account.get("Name") or "").strip()
    if sp and name:
        return f"{sp} — {name}"
    return name or sp or str(account.get("Id") or "Unknown")


def update_case_account(
    case_id: str,
    account_id: str,
    *,
    case_number: str | None = None,
    posture: str = "Known SP",
    account: dict | None = None,
    org: str = "vixxo",
) -> str:
    """Set Case.AccountId and post a short audit Task. Returns status string."""
    label = account_label(account)
    cmd = [
        sf_bin(),
        "data",
        "update",
        "record",
        "--sobject",
        "Case",
        "--record-id",
        case_id,
        "--target-org",
        org,
        "--json",
        "--values",
        f"AccountId={account_id}",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        return "failed — sf CLI not found"
    if proc.returncode != 0:
        return f"failed — {(proc.stderr or proc.stdout or '')[:200].strip()}"

    case_ref = case_number or case_id
    desc = (
        f"SP Inbound Vetting set Case Account to {label}. "
        f"Posture: {posture}. Processed via sf_case_account.update_case_account."
    ).replace("'", "''")
    task_cmd = [
        sf_bin(),
        "data",
        "create",
        "record",
        "--sobject",
        "Task",
        "--target-org",
        org,
        "--json",
        "--values",
        f"Subject='SP Inbound Vetting - Case {case_ref} Account updated' "
        f"Description='{desc}' WhatId='{case_id}' Status='Completed' Priority='Normal'",
    ]
    subprocess.run(task_cmd, capture_output=True, text=True, timeout=120)
    return f"updated — AccountId={account_id} ({label})"
