#!/usr/bin/env python3
import json
import urllib.request

SEARCH_PAGE = "https://comptroller.texas.gov/taxes/franchise/account-status/search"
IDS = {
    "EXECUTIVE DOORS LLC": "32067800196",
    "JC DOORS LLC": "32105525532",
}
results = {}
for name, tid in IDS.items():
    url = f"https://comptroller.texas.gov/data-search/franchise-tax/{tid}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": SEARCH_PAGE},
    )
    data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    results[name] = data
    print(json.dumps(data, indent=2))

out = r"c:\Users\CGagner\source\assistant-CGagner\.agents\skills\service-provider-vetting-analyst\.tmp\tx_comptroller_entity_details.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
