#!/usr/bin/env python3
import json
import urllib.parse
import urllib.request

API = "https://comptroller.texas.gov/data-search/franchise-tax"
DETAIL = "https://comptroller.texas.gov/data-search/franchise-tax-detail"
QUERIES = [
    "Executive Doors",
    "Executive Doors LLC",
    "JC Doors",
    "JC Doors LLC",
    "Joey Casella",
    "Quality Doors More",
    "Quality Doors & More",
    "Casella Doors",
]

results = {"searches": [], "details": []}

for q in QUERIES:
    url = f"{API}?name={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    try:
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        data = json.loads(raw)
        entry = {"query": q, "response": data}
        results["searches"].append(entry)
        print(f"\n=== {q} === success={data.get('success')} count={data.get('count', len(data.get('data') or []))}")
        for row in (data.get("data") or [])[:10]:
            print(" ", row)
            tid = row.get("taxpayerId") or row.get("taxpayer_id")
            if tid:
                durl = f"{DETAIL}?taxpayerId={urllib.parse.quote(str(tid))}"
                dreq = urllib.request.Request(durl, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
                try:
                    detail_raw = urllib.request.urlopen(dreq, timeout=30).read().decode("utf-8")
                    detail = json.loads(detail_raw)
                    results["details"].append({"query": q, "taxpayerId": tid, "response": detail})
                    print("   DETAIL:", json.dumps(detail.get("data") or detail, indent=2)[:1500])
                except Exception as exc:
                    print("   DETAIL ERROR:", exc)
    except Exception as exc:
        print(f"\n=== {q} === ERROR: {exc}")
        results["searches"].append({"query": q, "error": str(exc)})

out = r"c:\Users\CGagner\source\assistant-CGagner\.agents\skills\service-provider-vetting-analyst\.tmp\tx_comptroller_search_results.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("\nWrote", out)
