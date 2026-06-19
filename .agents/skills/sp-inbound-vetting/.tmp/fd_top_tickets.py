import base64, json, urllib.request
from pathlib import Path

token = Path.home().joinpath(".vixxo", "freshdesk_token").read_text(encoding="ascii").strip()
auth = base64.b64encode(f"{token}:X".encode()).decode()
h = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

for tid in [56976, 56571, 53949]:
    req = urllib.request.Request(
        f"https://vixxo-helpdesk.freshdesk.com/api/v2/tickets/{tid}?include=conversations,requester",
        headers=h,
    )
    t = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    convs = [c for c in (t.get("conversations") or []) if not c.get("private")]
    latest = convs[-1] if convs else None
    print(
        json.dumps(
            {
                "id": tid,
                "subject": t.get("subject"),
                "status": t.get("status"),
                "type": t.get("type"),
                "tags": t.get("tags"),
                "sp": (t.get("custom_fields") or {}).get("cf_sp"),
                "requester": (t.get("requester") or {}).get("email"),
                "updated_at": t.get("updated_at"),
                "fr_due_by": t.get("fr_due_by"),
                "latest_public": {
                    "at": latest.get("created_at") if latest else None,
                    "from": latest.get("from_email") if latest else None,
                    "body": (latest.get("body_text") or "")[:450] if latest else None,
                },
            },
            indent=2,
        )
    )
    print("---")
