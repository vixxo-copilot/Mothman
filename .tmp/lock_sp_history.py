import json
import sys

sys.path.insert(0, r"C:\Users\CGagner\source\mothman\.agents\skills\sp-inbound-vetting\scripts")
from gateway_vetting import gateway_search_invoices

LOCK_SPS = {
    "KS101552": "KS - Ace Lock and Security (Earlysville/Charlottesville)",
    "12817": "Albermarie Safe & Lock Co. Inc. (Charlottesville)",
    "12378": "Action Lock, Safe & Security (Charlottesville)",
    "13088": "Hawkins Lock & Key Co. Inc. (Lynchburg)",
    "13147": "Norvac Lock Technology Inc (Winchester)",
    "12681": "Willhite's Lock Service (Winchester)",
    "6641": "East Coast Safe & Lock (Richmond)",
}

for sp, name in LOCK_SPS.items():
    rows = gateway_search_invoices(serviceProviderNumber=sp)
    lock_rows = [r for r in rows if (r.get("lineOfService") or "") in ("Locks", "Security - Safe") or "Lock" in (r.get("lineOfService") or "")]
    va_rows = [r for r in rows if ", VA " in (r.get("siteAddress") or "")]
    hburg = [r for r in rows if "Harrisonburg" in (r.get("siteAddress") or "")]
    cville = [r for r in rows if "Charlottesville" in (r.get("siteAddress") or "")]
    lynch = [r for r in rows if "Lynchburg" in (r.get("siteAddress") or "")]
    print(f"=== {sp} {name} ===")
    print(f"  total={len(rows)} lock/safe={len(lock_rows)} va={len(va_rows)} hburg={len(hburg)} cville={len(cville)} lynch={len(lynch)}")
    for r in (lock_rows or rows)[:3]:
        print(
            "   ",
            r.get("lineOfService"),
            r.get("customerName"),
            r.get("siteAddress"),
            r.get("status"),
        )
