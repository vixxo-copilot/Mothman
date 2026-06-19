import json
from collections import Counter
from pathlib import Path

runs = [
    Path(".agents/skills/sp-inbound-vetting/.tmp/live-run/live-run-all-20260617T144215Z.json"),
    Path(".agents/skills/sp-inbound-vetting/.tmp/live-run/live-run-invoice-concerns-20260617T144604Z.json"),
]

for p in runs:
    data = json.loads(p.read_text(encoding="utf-8"))
    results = data["results"]
    print(f"\n=== {p.name} ===")
    print(f"total: {data['total']}, notes_posted: {data['notes_posted']}, errors: {len(data.get('errors', []))}")
    print("by_queue:", dict(Counter(r["queue"] for r in results)))
    print("by_posture:", dict(Counter(r["posture"] for r in results)))
    ic = [r for r in results if r["queue"] == "invoice-concerns"]
    if ic:
        print(f"invoice-concerns: {len(ic)}")
        print("  postures:", dict(Counter(r["posture"] for r in ic)))
        print("  sample IDs:", [r["ticket_id"] for r in ic[:6]])
        print("  known SP:", [r["ticket_id"] for r in ic if r["posture"].startswith("Known SP")])
        print("  sf lead:", [r["ticket_id"] for r in ic if "Lead" in r["posture"]])
    if data.get("errors"):
        for e in data["errors"]:
            print(f"  ERROR #{e['ticket_id']}: {e.get('error')} tags={e.get('tags')}")
