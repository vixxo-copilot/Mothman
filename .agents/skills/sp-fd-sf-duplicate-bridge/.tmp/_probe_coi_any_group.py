#!/usr/bin/env python3
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
# No group filter - all tickets in window
all_tickets = _search_fd_filter(api_key, window_start, window_end, "status:>1")
fed = [t for t in all_tickets if extract_federated_coi_provider(t.get("subject") or "")]
print(f"All FD tickets (any group) with federated COI subject: {len(fed)}")
for t in fed:
    print(t["id"], extract_federated_coi_provider(t.get("subject")), t.get("group_id"), t.get("created_at"))
