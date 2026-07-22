#!/usr/bin/env python3
"""Remove duplicate ContentDocuments on VR voicemail SF Cases (same title+size)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
RUN_JSON = SKILL_DIR / ".tmp" / "vr-voicemail-bridge-run-20260722T185136Z.json"
ORG = "vixxo"


def sf_cmd() -> str:
    npm_sf = Path(os.environ.get("APPDATA", "")) / "npm" / "sf.cmd"
    if npm_sf.is_file():
        return str(npm_sf)
    found = shutil.which("sf")
    if not found:
        raise SystemExit("sf CLI not found")
    return found


def sf_query(sf: str, soql: str) -> list[dict]:
    proc = subprocess.run(
        [sf, "data", "query", "--query", soql, "--target-org", ORG, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    data = json.loads(proc.stdout)
    return ((data.get("result") or {}).get("records") or [])


def sf_delete_doc(sf: str, doc_id: str) -> bool:
    proc = subprocess.run(
        [sf, "data", "delete", "record", "--sobject", "ContentDocument", "--record-id", doc_id, "--target-org", ORG, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"  DELETE FAIL {doc_id}: {(proc.stderr or proc.stdout)[:200]}")
        return False
    return True


def main() -> int:
    run = json.loads(RUN_JSON.read_text(encoding="utf-8"))
    case_ids = sorted({r["sf_case_id"] for r in run["results"] if r.get("sf_case_id")})
    sf = sf_cmd()

    deleted: list[dict] = []
    kept: list[dict] = []

    for case_id in case_ids:
        rows = sf_query(
            sf,
            "SELECT ContentDocumentId, ContentDocument.Title, ContentDocument.ContentSize, "
            f"ContentDocument.CreatedDate FROM ContentDocumentLink "
            f"WHERE LinkedEntityId = '{case_id}' ORDER BY ContentDocument.CreatedDate ASC",
        )
        groups: dict[tuple[str, int], list[dict]] = {}
        for row in rows:
            doc = row.get("ContentDocument") or {}
            title = str(doc.get("Title") or "")
            size = int(doc.get("ContentSize") or 0)
            doc_id = row.get("ContentDocumentId")
            if not doc_id:
                continue
            groups.setdefault((title, size), []).append(
                {"doc_id": doc_id, "title": title, "size": size, "created": doc.get("CreatedDate"), "case_id": case_id}
            )

        for key, docs in groups.items():
            if len(docs) <= 1:
                kept.append(docs[0])
                continue
            keep = docs[0]
            kept.append(keep)
            for dup in docs[1:]:
                ok = sf_delete_doc(sf, dup["doc_id"])
                deleted.append({**dup, "deleted": ok, "kept_doc_id": keep["doc_id"]})
                print(f"{'OK' if ok else 'FAIL'} delete {dup['doc_id']} dup of {dup['title']} on {case_id}")

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "cases_scanned": len(case_ids),
        "kept": len(kept),
        "deleted_count": sum(1 for d in deleted if d.get("deleted")),
        "delete_failed": sum(1 for d in deleted if not d.get("deleted")),
        "deleted": deleted,
    }
    out = SKILL_DIR / ".tmp" / f"vr-voicemail-dedupe-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("cases_scanned", "kept", "deleted_count", "delete_failed")}, indent=2))
    print(f"Wrote {out}")
    return 0 if summary["delete_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
