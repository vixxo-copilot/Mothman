#!/usr/bin/env python3
"""Apply pre-built QSIAP vet batch items."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/sp-inbound-vetting/scripts"))
sys.path.insert(0, str(ROOT / ".agents/skills/sp-voicemail-triage/scripts"))

from batch_process_freshdesk import load_credentials  # noqa: E402
from dry_run_batch import posture  # noqa: E402
from live_run_qsiap_voicemails import apply_qsiap_item  # noqa: E402

path = ROOT / ".agents/skills/sp-inbound-vetting/.tmp/qsiap-vet-batch-20260723.json"
data = json.loads(path.read_text(encoding="utf-8"))
api = load_credentials()
results = []

for item in data["items"]:
    acct = item.get("sf_account")
    if acct and acct.get("Service_Provider_Number__c"):
        spn = acct["Service_Provider_Number__c"]
        item["ks_number"] = spn
        item["gateway_sp"] = {
            "sp_number": spn,
            "name": acct.get("Name"),
            "source": "Salesforce Account",
        }
        post, cf = posture(
            item["gateway_sp"],
            {"lead": item.get("sf_lead"), "case": item.get("sf_case"), "account": acct},
            item,
        )
        item["posture"] = post
        item["cf_sp_target"] = cf
    result = apply_qsiap_item(api, item)
    results.append(result)
    print(
        f"#{item['ticket_id']} {item['posture']} "
        f"note={result.get('note')} cf_sp={result.get('cf_sp')}"
    )

out = ROOT / ".agents/skills/sp-inbound-vetting/.tmp" / (
    f"live-run-qsiap-voicemails-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
)
summary = {
    "mode": "live",
    "discovered": 8,
    "vetted": len(results),
    "known_sp": sum(1 for i in data["items"] if str(i["posture"]).startswith("Known SP")),
    "results": results,
}
out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(
    json.dumps(
        {
            "vetted": len(results),
            "notes_posted": sum(1 for r in results if r.get("note") == "posted"),
            "errors": [r for r in results if r.get("error")],
            "report": str(out),
        },
        indent=2,
    )
)
