#!/usr/bin/env python3
import json, sys, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/sp-voicemail-triage/scripts"))
from batch_process_freshdesk import auth_headers, http_json, load_credentials, is_voicemail_ticket

DOMAIN = "vixxo-helpdesk.freshdesk.com"
SPM = "159000485013"
QSIAP = "qsiap@vixxo.com"
api = load_credentials()

def blob(t):
    parts = [t.get("subject") or "", t.get("description_text") or ""]
    for f in ("to_emails", "cc_emails", "support_email"):
        v = t.get(f)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
        elif v:
            parts.append(str(v))
    return " ".join(parts).lower()

by_id = {}
for q in [
    f"group_id:{SPM} AND status:2 AND type:'Invoice Support'",
    f"group_id:{SPM} AND status:2 AND type:null",
]:
    for page in range(1, 15):
        url = f"https://{DOMAIN}/api/v2/search/tickets?" + urllib.parse.urlencode(
            {"query": f'"{q}"', "page": str(page)}
        )
        req = urllib.request.Request(url, headers=auth_headers(api))
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        rows = data.get("results") or []
        for row in rows:
            tid = int(row["id"])
            if tid in by_id:
                continue
            if not is_voicemail_ticket(row):
                continue
            ticket = http_json("GET", f"/api/v2/tickets/{tid}?include=requester", api)
            if QSIAP not in blob(ticket):
                continue
            by_id[tid] = {
                "id": tid,
                "subject": ticket.get("subject"),
                "tags": ticket.get("tags") or [],
                "cf_sp": (ticket.get("custom_fields") or {}).get("cf_sp"),
                "status": ticket.get("status"),
            }
        if len(rows) < 30:
            break

print(json.dumps({"count": len(by_id), "tickets": sorted(by_id.values(), key=lambda x: x["id"], reverse=True)}, indent=2))
