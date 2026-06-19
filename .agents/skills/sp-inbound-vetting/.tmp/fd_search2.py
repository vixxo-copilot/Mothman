import base64, json, sys, urllib.parse, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
token = Path.home().joinpath(".vixxo", "freshdesk_token").read_text(encoding="ascii").strip()
auth = base64.b64encode(f"{token}:X".encode()).decode()
h = {"Authorization": f"Basic {auth}", "Accept": "application/json"}
for q in ["KS101990", "Triad", "Pacific View"]:
    path = "/api/v2/search/tickets?query=" + urllib.parse.quote(f'"{q}"')
    r = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"https://vixxo-helpdesk.freshdesk.com{path}", headers=h),
            timeout=60,
        ).read().decode()
    )
    print(q, "total", r.get("total"))
    for t in (r.get("results") or [])[:5]:
        print(" ", t["id"], t["subject"][:70], "status", t["status"], "agent", t.get("responder_id"))
