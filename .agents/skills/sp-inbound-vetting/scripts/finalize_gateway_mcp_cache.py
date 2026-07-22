#!/usr/bin/env python3
"""Build gateway MCP cache from lookup plan (empty defaults + optional MCP results merge)."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_gateway_mcp_cache import build_cache  # noqa: E402
from live_run_qsiap_voicemails_mcp import cache_key  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mcp-results", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    results: list[dict] = []
    if args.mcp_results and args.mcp_results.is_file():
        raw = json.loads(args.mcp_results.read_text(encoding="utf-8"))
        results = raw.get("results") or []

    existing = {(r.get("tool"), json.dumps(r.get("arguments") or {}, sort_keys=True)) for r in results}
    for lookup in plan.get("lookups") or []:
        key = (lookup.get("tool"), json.dumps(lookup.get("arguments") or {}, sort_keys=True))
        if key in existing:
            continue
        results.append(
            {
                "tool": lookup["tool"],
                "arguments": lookup["arguments"],
                "response": {"data": {"invoiceList": [], "success": True}},
            }
        )

    tmp = args.out.with_suffix(".mcp-results.json")
    tmp.write_text(
        json.dumps(
            {"built_at": datetime.now(timezone.utc).isoformat(), "results": results},
            indent=2,
        ),
        encoding="utf-8",
    )
    meta = build_cache(args.plan, tmp, args.out)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
