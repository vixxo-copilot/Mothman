#!/usr/bin/env python3
"""Quick Option B auth/close smoke test."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Reuse batch loader
sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch_process_freshdesk import http_json, load_credentials, search_tickets  # noqa: E402


def main() -> int:
    key = load_credentials()
    tickets = search_tickets(key)
    print(f"env_auth=ok open_tickets={len(tickets)}")
    if not tickets:
        return 0
    tid = int(tickets[-1]["id"])  # oldest in page
    try:
        http_json(
            "PUT",
            f"/api/v2/tickets/{tid}",
            key,
            {"status": 5, "type": "KSOnboarding", "custom_fields": {"cf_sp": "Unknown"}},
        )
        print(f"close_test=ok ticket={tid}")
    except Exception as exc:  # noqa: BLE001
        print(f"close_test=fail ticket={tid} error={exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
