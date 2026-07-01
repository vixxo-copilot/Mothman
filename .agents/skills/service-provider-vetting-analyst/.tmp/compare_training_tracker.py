import json
from pathlib import Path

providers = {
    "16925": "KS - AC Professional Handymen LLC",
    "KS69136": "KS - DAT Repair LLC",
    "KS69673": "KS - Tim-s Handywork LLC",
    "KS69903": "KS - GS Flook Inc",
    "KS69060": "KS - Priority Cabling Services",
    "KS69845": "KS - Commercial Maintenance & Repair Inc",
    "KS101029": "KS - Allegiant LLC",
    "17786": "KS - Handyman Al",
    "KS68797": "Commercial Services LLC",
    "KS69073": "KS - SBE Handyman and Construction Services LLC",
    "KS69286": "KS - Upstate Maintenance & Improvements",
    "KS69771": "KS - Ace Handyman Services",
}


def norm(code: str) -> str:
    code = str(code).strip().upper()
    if code.startswith("KS"):
        return code[2:]
    return code


def main() -> None:
    p = Path(
        r"C:\Users\CGagner\.cursor\projects\c-Users-CGagner-source-assistant-CGagner\agent-tools\882d5389-60a2-4f12-b20c-328bf2129293.txt"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    values = data["values"]

    header = None
    header_idx = None
    for i, row in enumerate(values[:15]):
        row_str = [str(c).strip() if c is not None else "" for c in row]
        if any("SP#" in c or "SP #" in c for c in row_str) or ("Vendor Name" in row_str):
            header = row_str
            header_idx = i
            break

    print("Header row index:", header_idx)
    print("Header:", header)

    col_map: dict[str, int] = {}
    if header:
        for j, h in enumerate(header):
            hlow = h.lower()
            if "vendor" in hlow and "name" in hlow:
                col_map["name"] = j
            elif h.strip() in ("SP#", "SP #", "SP"):
                col_map["sp"] = j
            elif h.strip() in ("SU#", "SU #", "SU"):
                col_map["su"] = j
            elif "email" in hlow:
                col_map["email"] = j
            elif "training" in hlow and "status" in hlow:
                col_map["status"] = j
            elif "notes" in hlow:
                col_map["notes"] = j

    if "sp" not in col_map:
        col_map = {"name": 5, "su": 6, "sp": 7, "email": 8, "status": 9, "notes": 10}

    print("Column map:", col_map)

    tracker: dict[str, dict] = {}
    start = (header_idx + 1) if header_idx is not None else 0
    for row in values[start:]:
        if not row or all((c is None or str(c).strip() == "") for c in row):
            continue
        sp_idx = col_map["sp"]
        if sp_idx >= len(row):
            continue
        sp = row[sp_idx]
        sp = str(sp).strip() if sp is not None else ""
        if not sp:
            continue
        key = norm(sp)
        tracker[key] = {
            "sp_raw": sp,
            "name": str(row[col_map.get("name", 5)] or "").strip(),
            "su": str(row[col_map.get("su", 6)] or "").strip(),
            "email": str(row[col_map.get("email", 8)] or "").strip(),
            "status": str(row[col_map.get("status", 9)] or "").strip(),
            "notes": str(row[col_map.get("notes", 10)] or "").strip(),
        }

    print("Tracker rows with SP#:", len(tracker))
    print()
    print("=== COMPARISON ===")

    matched = []
    missing = []
    for code, list_name in providers.items():
        key = norm(code)
        if key in tracker:
            t = tracker[key]
            matched.append((code, list_name, t))
            print(f"MATCH | {code} | {list_name}")
            print(
                f"       Tracker: {t['name']} | SU: {t['su']} | Status: {t['status']} | Email: {t['email']}"
            )
            if t["notes"]:
                print(f"       Notes: {t['notes']}")
        else:
            missing.append((code, list_name))
            print(f"MISSING FROM TRACKER | {code} | {list_name}")

    print()
    print(f"Summary: {len(matched)} matched, {len(missing)} missing out of {len(providers)} providers")


if __name__ == "__main__":
    main()
