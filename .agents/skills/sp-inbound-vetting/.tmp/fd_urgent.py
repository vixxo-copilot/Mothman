#!/usr/bin/env python3
import base64, json, urllib.parse, urllib.request
from pathlib import Path
token = Path.home().joinpath(".vixxo", "freshdesk_token").read_text(encoding="ascii").strip()
auth = base64.b64encode(f"{token}:X".encode()).decode()
h = {"Authorization": f"Basic {auth}", "Accept": "application/json"}
agent = 159009179645
for label, q in [
    ("urgent", f"agent_id:{agent} AND status:2 AND priority:4"),
    ("high", f"agent_id:{agent} AND status:2 AND priority:3"),
]:
    path = "/api/v2/search/tickets?query=" + urllib.parse.quote(f'"{q}"')
    req = urllib.request.Request(f"https://vixxo-helpdesk.freshdesk.com{path}", headers=h)
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    print(label, "total", r.get("total", 0))
    for t in r.get("results") or []:
        print(" ", t["id"], t["subject"], "updated", t.get("updated_at"))
