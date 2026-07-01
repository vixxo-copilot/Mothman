#!/usr/bin/env python3
import json
import re
from pathlib import Path

src = Path(
    r"C:\Users\CGagner\.cursor\projects\c-Users-CGagner-source-assistant-CGagner"
    r"\agent-tools\d07166c7-42a1-41ee-b277-ae95b33ac91e.txt"
)
text = src.read_text(encoding="utf-8")
m = re.search(r'\{\s*"records"', text)
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

out = Path(__file__).resolve().parents[1] / ".tmp" / "sf-cases-window-20260629.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"saved {data.get('totalSize')} cases -> {out}")
