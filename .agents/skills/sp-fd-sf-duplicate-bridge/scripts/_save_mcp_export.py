#!/usr/bin/env python3
"""Save Salesforce MCP run_soql_query output to .tmp cache JSON."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python _save_mcp_export.py <mcp-output.txt> <output.json>")
        return 2
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")
    if text.lstrip().startswith("SOQL query results:"):
        text = text.split("\n", 1)[1].strip()
    else:
        m = re.search(r'\{\s*"records"', text)
        if not m:
            raise SystemExit("Could not find records JSON in MCP output")
        text = text[m.start() :]
    data = json.loads(text)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"saved {data.get('totalSize', len(data.get('records', [])))} cases -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
