#!/usr/bin/env python3
import json
from pathlib import Path

d = json.loads(
    Path(__file__).parent.joinpath("fd-sf-duplicate-scan-20260629.json").read_text(encoding="utf-8")
)
for label in ("true_same_thread", "likely_same_thread", "contact_collision"):
    rows = [p for p in d["pairs"] if p["dup_type"] == label]
    print(f"\n=== {label} ({len(rows)}) ===")
    for p in rows:
        fd = p["freshdesk"]
        sf = p["salesforce"]
        print(
            f"FD #{fd['id']} <-> SF {sf['case_number']} | {p['origin']} | "
            f"{(fd.get('subject') or '')[:55]}"
        )
