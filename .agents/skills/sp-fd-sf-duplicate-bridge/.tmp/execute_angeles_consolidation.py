#!/usr/bin/env python3
"""Execute Angeles Plumbing COI consolidation onto SF Case #00005985."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TMP = SKILL / ".tmp" / "angeles-consolidate-5985-run"
TMP.mkdir(parents=True, exist_ok=True)

ORG = "vixxo"
SF = str(Path(__import__("os").environ.get("APPDATA", "")) / "npm" / "sf.cmd")
PRIMARY = "500TS00000nmtkLYAQ"
ACCOUNT = "001TS00000en7sdYAA"
CLOSE_SF = [
    ("500TS00000nZfYlYAK", "00005886"),
    ("500TS00000nWkRhYAK", "00005831"),
    ("500TS00000nnp8UYAQ", "00006016"),
]
EMAILS = [
    "02sTS00000lFFLVYA4",
    "02sTS00000lCFg9YAG",
    "02sTS00000lSDnJYAW",
]
DOCS = ["069TS00000f5Xq9YAE", "069TS00000fJbpAYAS"]
FD_SYNC = [48695, 49414]
FD_CLOSE = [48695, 49414, 49190, 58276, 58573]
FD_NOTES = {
    48695: "Consolidated to SF Case #00005985. Cert synced to SF. FD duplicate closed.",
    49414: "Consolidated to SF Case #00005985. Cert ER12480.pdf synced to SF. FD duplicate closed.",
    49190: "Duplicate merged to SF Case #00005985 (Angeles Plumbing consolidated COI).",
    58276: "Duplicate merged to SF Case #00005985 (Angeles Plumbing consolidated COI).",
    58573: "Duplicate merged to SF Case #00005985 (Angeles Plumbing consolidated COI).",
}

log: list[dict] = []


def run_sf(args: list[str]) -> dict:
    cmd = [SF, *args, "--target-org", ORG, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = proc.stdout.strip()
    err = proc.stderr.strip()
    try:
        data = json.loads(out) if out else {}
    except json.JSONDecodeError:
        data = {"raw": out, "stderr": err}
    ok = proc.returncode == 0 and data.get("status") == 0
    entry = {"cmd": args[:4], "ok": ok, "data": data, "stderr": err}
    log.append(entry)
    print(("OK" if ok else "FAIL"), " ".join(args[:3]), err[:120] if not ok else "")
    return entry


def sf_query(soql: str) -> list[dict]:
    r = run_sf(["data", "query", "--query", soql])
    if not r["ok"]:
        return []
    return ((r["data"].get("result") or {}).get("records") or [])


def link_doc_if_missing(doc_id: str) -> None:
    existing = sf_query(
        f"SELECT Id FROM ContentDocumentLink WHERE LinkedEntityId = '{PRIMARY}' "
        f"AND ContentDocumentId = '{doc_id}' LIMIT 1"
    )
    if existing:
        print(f"SKIP link {doc_id} already on case")
        return
    run_sf(
        [
            "data",
            "create",
            "record",
            "--sobject",
            "ContentDocumentLink",
            "--values",
            f"ContentDocumentId={doc_id} LinkedEntityId={PRIMARY} ShareType=V Visibility=AllUsers",
        ]
    )


def create_task(subject: str, description: str) -> None:
    desc = description.replace("'", "\\'")[:32000]
    subj = subject.replace("'", "\\'")[:255]
    run_sf(
        [
            "data",
            "create",
            "record",
            "--sobject",
            "Task",
            "--values",
            f"Subject='{subj}' Description='{desc}' WhatId={PRIMARY} Status=Completed Priority=Normal",
        ]
    )


def fd_request(method: str, path: str, body: dict | None = None) -> dict:
    import base64
    import os

    domain = os.environ.get("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com")
    api_key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    token = Path.home() / ".vixxo" / "freshdesk_token"
    if not api_key and token.is_file():
        api_key = token.read_text(encoding="utf-8").strip()
    auth = "Basic " + base64.b64encode(f"{api_key}:X".encode()).decode()
    url = f"https://{domain}/api/v2{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": auth,
            "Content-Type": "application/json",
            "User-Agent": "sp-fd-sf-duplicate-bridge/1.0",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode()
            return {"ok": True, "data": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": exc.read().decode()[:500]}


def fd_note_and_close(ticket_id: int, note: str) -> None:
    note_r = fd_request(
        "POST",
        f"/tickets/{ticket_id}/notes",
        {"body": note, "private": True},
    )
    print(f"FD #{ticket_id} note:", "OK" if note_r["ok"] else note_r.get("error", "")[:80])
    close_r = fd_request("PUT", f"/tickets/{ticket_id}", {"status": 5})
    print(f"FD #{ticket_id} close:", "OK" if close_r["ok"] else close_r.get("error", "")[:80])
    log.append({"fd": ticket_id, "note": note_r, "close": close_r})


def main() -> int:
    print("=== Step 1: Update primary Case #00005985 ===")
    run_sf(
        [
            "data",
            "update",
            "record",
            "--sobject",
            "Case",
            "--record-id",
            PRIMARY,
            "--values",
            f"AccountId={ACCOUNT} Status=Working Subject='Certificate Of Insurance - Angeles Plumbing, LLC 450-802-4 (Consolidated Federated COI)'",
        ]
    )

    print("=== Step 2: Reparent EmailMessages ===")
    for em in EMAILS:
        run_sf(
            [
                "data",
                "update",
                "record",
                "--sobject",
                "EmailMessage",
                "--record-id",
                em,
                "--values",
                f"ParentId={PRIMARY}",
            ]
        )

    print("=== Step 3: Link ContentDocuments to Case ===")
    for doc in DOCS:
        link_doc_if_missing(doc)

    print("=== Step 4: Sync FD attachments ===")
    sync_script = SKILL / "scripts" / "sync_attachments_to_sf.py"
    for fd_id in FD_SYNC:
        proc = subprocess.run(
            [
                sys.executable,
                str(sync_script),
                "--fd-ticket-id",
                str(fd_id),
                "--sf-case-id",
                PRIMARY,
                "--policy",
                "full",
                "--skip-existing",
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(SKILL),
        )
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr[:500])
        log.append({"sync_fd": fd_id, "code": proc.returncode, "out": proc.stdout[:500]})

    print("=== Step 5: FD thread Tasks on primary ===")
    fd_tasks = [
        (48695, "FD thread merge — #48695 Req 17"),
        (49414, "FD thread merge — #49414 Req 19"),
        (49190, "FD thread merge — #49190 Req 17 auto-reply"),
        (58276, "FD thread merge — #58276 Req 17 auto-reply"),
        (58573, "FD thread merge — #58573 Req 21 auto-reply"),
    ]
    import os
    import base64

    domain = os.environ.get("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com")
    api_key = os.environ.get("FRESHDESK_API_KEY", "").strip()
    token = Path.home() / ".vixxo" / "freshdesk_token"
    if not api_key and token.is_file():
        api_key = token.read_text(encoding="utf-8").strip()
    auth = "Basic " + base64.b64encode(f"{api_key}:X".encode()).decode()
    for fd_id, subj in fd_tasks:
        try:
            req = urllib.request.Request(
                f"https://{domain}/api/v2/tickets/{fd_id}",
                headers={"Authorization": auth, "User-Agent": "sp-fd-sf-duplicate-bridge/1.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                t = json.loads(resp.read().decode())
            desc = (
                f"Merged from Freshdesk #{fd_id} into primary SF Case #00005985.\n"
                f"Original subject: {t.get('subject', '')}\n"
                f"Status at merge: {t.get('status')}\n"
                f"Action: FD ticket closed as duplicate; SF is system of record."
            )
        except Exception as exc:
            desc = f"Merged from Freshdesk #{fd_id}. Error fetching ticket: {exc}"
        create_task(subj, desc)

    print("=== Step 6: Consolidation Task ===")
    create_task(
        "Angeles Plumbing COI consolidated — SF #00005985 primary",
        "Consolidated all Angeles Plumbing Federated COI (450-802-4) onto Case #00005985. "
        "Merged SF #00005886, #00005831, #00006016. Reparented EmailMessages and linked certs. "
        "Synced FD #48695, #49414 attachments. Closed FD duplicates #48695, #49414, #49190, #58276, #58573.",
    )

    print("=== Step 7: Close duplicate SF Cases ===")
    for case_id, num in CLOSE_SF:
        run_sf(
            [
                "data",
                "update",
                "record",
                "--sobject",
                "Case",
                "--record-id",
                case_id,
                "--values",
                "Status=Closed",
            ]
        )

    print("=== Step 8: FD notes + close ===")
    for fd_id in FD_CLOSE:
        fd_note_and_close(fd_id, FD_NOTES[fd_id])

    print("=== Verify files on primary ===")
    files = sf_query(
        f"SELECT ContentDocument.Title, ContentDocument.ContentSize FROM ContentDocumentLink "
        f"WHERE LinkedEntityId = '{PRIMARY}' ORDER BY ContentDocument.Title"
    )
    for f in files:
        doc = f.get("ContentDocument") or {}
        print(f"  - {doc.get('Title')} ({doc.get('ContentSize')} bytes)")

    emails = sf_query(
        f"SELECT Id, Subject, MessageDate FROM EmailMessage WHERE ParentId = '{PRIMARY}' ORDER BY MessageDate"
    )
    print(f"EmailMessages on primary: {len(emails)}")
    for e in emails:
        print(f"  - {e.get('MessageDate')}: {(e.get('Subject') or '')[:60]}")

    report = TMP / "execution-log.json"
    report.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"LOG: {report}")
    fails = sum(1 for x in log if isinstance(x, dict) and x.get("ok") is False)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
