#!/usr/bin/env python3
"""Merge qsiap MCP live-run JSON shards into one summary."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR.parent / ".tmp" / "live-run"


def main() -> int:
    runs = []
    for path in sorted(OUT_DIR.glob("live-run-qsiap-voicemails-MCP-20260722T17*.json")):
        if "171912" in path.name:
            continue
        runs.append(json.loads(path.read_text(encoding="utf-8")))

    by_id: dict[int, dict] = {}
    for run in runs:
        for row in run.get("results") or []:
            by_id[int(row["ticket_id"])] = row

    results = [by_id[k] for k in sorted(by_id, reverse=True)]
    failures = [
        r
        for r in results
        if r.get("error") or str(r.get("tags", "")).startswith("failed")
    ]
    forward = [r for r in results if r.get("forward_candidate")]

    summary = {
        "mode": "live-mcp",
        "discovered": 59,
        "processed": len(results),
        "skipped_ids": [74250],
        "known_sp": sum(
            1 for r in results if str(r.get("posture", "")).startswith("Known SP")
        ),
        "notes_posted": sum(1 for r in results if r.get("note") == "posted"),
        "gateway_health": {"ok": True, "source": "cursor_mcp_cache"},
        "gateway_cache": str(OUT_DIR / "gateway-mcp-cache.json"),
        "skip_sf": True,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "forward_candidates": forward,
        "failures": failures,
        "results": results,
    }
    final = OUT_DIR / f"live-run-qsiap-voicemails-MCP-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    final.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "processed": len(results),
                "notes_posted": summary["notes_posted"],
                "failures": len(failures),
                "forward_candidates": len(forward),
                "output_path": str(final),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
