import base64, json, urllib.parse, urllib.request
from pathlib import Path

token = Path.home().joinpath(".vixxo", "freshdesk_token").read_text(encoding="ascii").strip()
auth = base64.b64encode(f"{token}:X".encode()).decode()
h = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

for q in [
    "requester_email:officepacificview@gmail.com",
    "agent_id:159009179645 AND status:2 AND updated_at:>'2026-06-16'",
]:
    path = "/api/v2/search/tickets?query=" + urllib.parse.quote(f'"{q}"')
    r = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"https://vixxo-helpdesk.freshdesk.com{path}", headers=h),
            timeout=60,
        ).read().decode()
    )
    print("QUERY", q, "total", r.get("total"))
    for t in r.get("results") or []:
        print(" ", t["id"], t["subject"][:60], "status", t["status"], "updated", t.get("updated_at"))
