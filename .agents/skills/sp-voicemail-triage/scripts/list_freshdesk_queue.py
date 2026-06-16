#!/usr/bin/env python3
"""List open KSOnboarding voicemail tickets for sp-voicemail-triage batch runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch_process_freshdesk import load_credentials, search_voicemail_tickets  # noqa: E402


def main() -> int:
    api_key = load_credentials()
    voicemail, skipped = search_voicemail_tickets(api_key)
    print(
        json.dumps(
            {
                "voicemail_count": len(voicemail),
                "skipped_non_voicemail": len(skipped),
                "skipped_ids": [int(t["id"]) for t in skipped],
                "tickets": voicemail,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
