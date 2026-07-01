#!/usr/bin/env python3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scan_duplicates import (
    search_fd_created_in_window,
    extract_federated_coi_provider,
    load_credentials,
    parse_dt,
)

window_start = parse_dt("2026-06-26T00:00:00Z")
window_end = datetime.now(timezone.utc)
api_key = load_credentials()
spm = search_fd_created_in_window(api_key, window_start, window_end)
fed = [
    t
    for t in spm
    if extract_federated_coi_provider(t.get("subject") or "")
    or "Certificate Of Insurance" in (t.get("subject") or "")
]
print(f"Federated COI FD tickets Jun26-now: {len(fed)}")
for t in fed:
    print(
        t["id"],
        extract_federated_coi_provider(t.get("subject") or "") or "?",
        t.get("created_at"),
        (t.get("subject") or "")[:75],
    )
