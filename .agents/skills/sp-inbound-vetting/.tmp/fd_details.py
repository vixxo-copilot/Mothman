import base64, json, sys, urllib.parse, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
token = Path.home().joinpath(".vixxo", "freshdesk_token").read_text(encoding="ascii").strip()
auth = base64.b64encode(f"{token}:X".encode()).decode()
h = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

for tid in [56976, 56571]:
    t = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"https://vixxo-helpdesk.freshdesk.com/api/v2/tickets/{tid}?include=conversations,requester",
                headers=h,
            ),
            timeout=60,
        ).read().decode()
    )
    print("TICKET", tid, t.get("subject"))
    print("DESC", (t.get("description_text") or "")[:800])
    for c in (t.get("conversations") or [])[-4:]:
        print("CONV", c.get("created_at"), "private", c.get("private"), (c.get("body_text") or "")[:250].replace("\n", " "))
    print("---")
