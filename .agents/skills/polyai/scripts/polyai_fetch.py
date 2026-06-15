#!/usr/bin/env python3
"""Shared PolyAI Conversations API pagination with retry."""
from __future__ import annotations

import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import polyai_client  # noqa: E402


def fetch_all_conversations(cfg: dict[str, str], page_size: int = 50, progress: bool = False) -> list[dict]:
    url = polyai_client.conversations_url(cfg) + f"?limit={page_size}"
    rows: list[dict] = []
    while url:
        for attempt in range(8):
            try:
                data = polyai_client.request_json(url, cfg["POLYAI_API_KEY"])
                break
            except SystemExit as exc:
                message = str(exc)
                retryable = any(
                    token in message
                    for token in ("429", "SSL", "Request failed", "HTTP 5")
                )
                if retryable and attempt < 7:
                    time.sleep(65 if "429" in message else 5 * (attempt + 1))
                    continue
                raise
        batch = data.get("conversations") or []
        rows.extend(batch)
        if progress and rows:
            print(f"Fetched {len(rows)} conversations...", file=sys.stderr)
        cursor = data.get("cursor")
        if not cursor or not batch:
            break
        url = polyai_client.conversations_url(cfg) + f"?limit={page_size}&cursor={cursor}"
    return rows
