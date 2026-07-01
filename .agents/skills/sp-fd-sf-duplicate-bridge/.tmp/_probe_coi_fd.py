#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scan_duplicates import (
    load_credentials,
    search_fd_coi_in_window,
    search_fd_created_in_window,
    extract_federated_coi_provider,
    parse_dt,
)
from datetime import datetime, timezone

window_start = parse_dt("2026-06-29T00:00:00Z")
window_end = datetime.now(timezone.utc)
api_key = load_credentials()
spm = search_fd_created_in_window(api_key, window_start, window_end)
coi = search_fd_coi_in_window(api_key, window_start, window_end)
print(f"SPM count: {len(spm)}")
print(f"COI tag count: {len(coi)}")
for t in coi:
    print(
        t["id"],
        (t.get("subject") or "")[:80],
        t.get("created_at"),
        t.get("tags"),
    )
