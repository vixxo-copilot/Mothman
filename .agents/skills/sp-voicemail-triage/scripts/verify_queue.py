#!/usr/bin/env python3
"""Verify ticket status for KSOnboarding queue."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch_process_freshdesk import http_json, load_credentials, search_tickets  # noqa: E402


def main() -> int:
    key = load_credentials()
    open_tickets = search_tickets(key)
    sample = open_tickets[:3]
    for t in sample:
        tid = int(t["id"])
        full = http_json("GET", f"/api/v2/tickets/{tid}", key)
        print(f"ticket={tid} search_status={t.get('status')} live_status={full.get('status')}")
    print(f"search_open_count={len(open_tickets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
