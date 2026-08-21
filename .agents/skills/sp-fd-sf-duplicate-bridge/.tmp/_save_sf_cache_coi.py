#!/usr/bin/env python3
import json
import re
from pathlib import Path

src = Path(
    r"C:\Users\CGagner\.cursor\projects\c-Users-CGagner-source-assistant-CGagner"
    r"\agent-tools\2d5d6b3b-1a53-45f7-ab1d-5aa7f662852d.txt"
)
text = src.read_text(encoding="utf-8")
m = re.search(r'\{\s*"status"', text)
if not m:
    m = re.search(r'\{\s*"records"', text)
if not m:
    raise SystemExit("JSON not found in sf output")
data = json.loads(text[m.start() :])
records = data.get("result", data)
out = Path(__file__).resolve().parent / "sf-cases-window-coi-20260630.json"
out.write_text(json.dumps(records, indent=2), encoding="utf-8")
print(f"saved {records.get('totalSize', len(records.get('records', [])))} cases -> {out}")
