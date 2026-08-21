#!/usr/bin/env python3
"""Extract JSON from MCP agent-tools SOQL output file."""
import json
import re
from pathlib import Path

src = Path(
    r"C:\Users\CGagner\.cursor\projects\c-Users-CGagner-source-assistant-CGagner"
    r"\agent-tools\f66ef4a2-00be-43d0-a009-5bf59b2c4942.txt"
)
text = src.read_text(encoding="utf-8")
m = re.search(r'\{\s*"records"', text)
if not m:
    raise SystemExit("No JSON found")
chunk = text[m.start() :]
depth = 0
for idx, ch in enumerate(chunk):
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            data = json.loads(chunk[: idx + 1])
            break
else:
    raise SystemExit("parse failed")

out = Path(__file__).resolve().parent / "sf-cases-window-20260701.json"
out.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"saved {data.get('totalSize', len(data.get('records', [])))} cases -> {out}")
