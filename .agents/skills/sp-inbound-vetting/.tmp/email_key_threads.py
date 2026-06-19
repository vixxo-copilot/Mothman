import json, sys, urllib.parse, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
cache = Path(__file__).resolve().parents[4] / ".cursor" / "bin" / "ms365-mcp" / "node_modules" / "@softeria" / "ms-365-mcp-server" / ".token-cache.json"
data = json.loads(json.loads(cache.read_text(encoding="utf-8"))["data"])
rt = next(iter(data["RefreshToken"].values()))["secret"]
body = urllib.parse.urlencode(
    {
        "grant_type": "refresh_token",
        "refresh_token": rt,
        "client_id": "084a3e9f-a9f4-43f7-89f9-d229cf97853e",
        "scope": "https://graph.microsoft.com/.default offline_access",
    }
).encode()
tok = json.loads(
    urllib.request.urlopen(
        urllib.request.Request(
            "https://login.microsoftonline.com/6971e9a1-0270-4452-ac45-b5023dc57b1b/oauth2/v2.0/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        ),
        timeout=60,
    ).read().decode()
)["access_token"]

for subj in ["Triad Manufacturing", "Pacific View", "Need SP Agreement"]:
    path = "/me/mailFolders/inbox/messages?" + urllib.parse.urlencode(
        {
            "$filter": f"contains(subject,'{subj.split()[0]}')",
            "$select": "subject,from,receivedDateTime,bodyPreview,isRead",
            "$top": "5",
            "$orderby": "receivedDateTime desc",
        }
    )
    req = urllib.request.Request(
        f"https://graph.microsoft.com/v1.0{path}",
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"},
    )
    try:
        msgs = json.loads(urllib.request.urlopen(req, timeout=60).read().decode()).get("value", [])
    except Exception as e:
        print(subj, "ERR", e)
        continue
    print("===", subj, "===")
    for m in msgs:
        frm = (m.get("from") or {}).get("emailAddress") or {}
        print(m.get("receivedDateTime"), frm.get("address"), m.get("subject"))
        print((m.get("bodyPreview") or "")[:350])
        print()
