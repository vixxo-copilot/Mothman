#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scan_duplicates import (
    _search_fd_filter,
    extract_federated_coi_provider,
    load_credentials,
    parse_dt,
)

window_start = parse_dt("2026-06-29T00:00:00Z")
window_end = datetime.now(timezone.utc)
api_key = load_credentials()
providers = {
    "KAA Investments LLC": "00006048",
    "CECCO, Inc.": "00006053",
    "Superior Mechanical Services, Inc.": "00006015",
    "Angeles Plumbing, LLC": "00006016",
    "Storefronts and Entrances, Inc.": "00006077",
    "Tri Star Transport LLC": None,
}
# Search all groups by tag COI
try:
    all_coi = _search_fd_filter(
        api_key, window_start, window_end, "tag:'COI'"
    )
except Exception as exc:
    print("tag search failed:", exc)
    all_coi = []

print(f"All-group COI tag tickets: {len(all_coi)}")
for t in all_coi:
    subj = t.get("subject") or ""
    prov = extract_federated_coi_provider(subj)
    if prov or "Certificate Of Insurance" in subj:
        print(t["id"], prov or subj[:70], t.get("created_at"), t.get("group_id"))

print("\nProvider match check:")
for prov, case in providers.items():
    matches = [
        t
        for t in all_coi
        if prov.split(",")[0].split()[0].lower()
        in (extract_federated_coi_provider(t.get("subject") or "") or "").lower()
        or prov.lower() in (t.get("subject") or "").lower()
    ]
    print(prov, "->", [(m["id"], m.get("subject", "")[:60]) for m in matches])
