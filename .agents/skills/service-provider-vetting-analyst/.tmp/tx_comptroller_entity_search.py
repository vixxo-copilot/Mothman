#!/usr/bin/env python3
"""Search Texas Comptroller Franchise Tax Account Status by entity name."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SEARCH_URL = "https://comptroller.texas.gov/taxes/franchise/account-status/search"
OUT = Path(__file__).resolve().parent / "tx_comptroller_search_results.json"

QUERIES = [
    "Executive Doors",
    "Executive Doors LLC",
    "JC Doors",
    "JC Doors LLC",
    "Joey Casella",
    "Quality Doors More",
    "Quality Doors & More",
]


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_search_results(page) -> dict:
    body = clean(page.locator("body").inner_text())
    rows: list[dict] = []
    for tr in page.locator("table tbody tr, table tr").all():
        cells = [clean(c) for c in tr.locator("td").all_text_contents()]
        if len(cells) >= 2 and any(cells):
            link = ""
            a = tr.locator("a").first
            if a.count():
                href = a.get_attribute("href") or ""
                if href:
                    link = href if href.startswith("http") else f"https://comptroller.texas.gov{href}"
            rows.append({"cells": cells, "link": link})

    return {
        "rows": rows,
        "body_excerpt": body[:5000],
        "url": page.url,
    }


def parse_detail(page) -> dict:
    body = clean(page.locator("body").inner_text())
    fields: dict[str, str] = {}
    patterns = [
        (r"Taxpayer Number\s*(\d[\d\s-]+)", "taxpayer_number"),
        (r"Texas Taxpayer Number\s*(\d[\d\s-]+)", "taxpayer_number"),
        (r"Taxpayer Name\s*(.+?)(?:Taxpayer Number|Mailing Address|$)", "taxpayer_name"),
        (r"Mailing Address\s*(.+?)(?:Registered Office|Registered Agent|$)", "mailing_address"),
        (r"Registered Agent Name\s*(.+?)(?:Registered Office|$)", "registered_agent"),
        (r"Registered Office Address\s*(.+?)(?:State of Formation|$)", "registered_office"),
        (r"State of Formation\s*(\w+)", "state_of_formation"),
        (r"SOS Registration Status\s*(\w+)", "sos_status"),
        (r"Effective SOS Registration Date\s*([\d/]+)", "effective_sos_date"),
        (r"SOS File Number\s*(\d+)", "sos_file_number"),
        (r"Right to Transact Business in Texas\s*(\w+)", "right_to_transact"),
        (r"Report Year\s*(\d{4})", "report_year"),
    ]
    for pat, key in patterns:
        m = re.search(pat, body, re.I)
        if m:
            fields[key] = clean(m.group(1))

    officers: list[str] = []
    for m in re.finditer(
        r"(President|Manager|Member|Director|Vice President|Secretary|Treasurer|Owner)\s+([A-Za-z ,.'-]+?)(?=\s+(?:President|Manager|Member|Director|Vice President|Secretary|Treasurer|Owner|Report Year|Mailing Address|$))",
        body,
        re.I,
    ):
        officers.append(f"{m.group(1)}: {clean(m.group(2))}")
    if officers:
        fields["officers"] = officers

    fields["body_excerpt"] = body[:6000]
    fields["url"] = page.url
    return fields


def search_entity(page, name: str) -> dict:
    result: dict = {"query": name, "summary": {}, "profiles": [], "errors": []}
    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)

        name_input = page.locator("input[name='entityName'], input#entityName, input[placeholder*='Entity' i]").first
        if not name_input.count():
            name_input = page.locator("input[type='text']").nth(1)
        name_input.fill(name)

        submit = page.locator(
            "button:has-text('Submit'), input[type='submit'][value*='Submit' i], button[type='submit']"
        ).first
        submit.click()
        page.wait_for_timeout(4000)

        result["summary"] = parse_search_results(page)

        for row in result["summary"].get("rows", [])[:5]:
            link = row.get("link")
            if not link:
                continue
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                profile = parse_detail(page)
                profile["search_row"] = row
                result["profiles"].append(profile)
            except Exception as exc:
                result["errors"].append(f"profile {link}: {exc}")
    except Exception as exc:
        result["errors"].append(str(exc))
    return result


def main() -> int:
    results = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": SEARCH_URL,
        "searches": [],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        for q in QUERIES:
            results["searches"].append(search_entity(page, q))
        browser.close()

    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    hits = sum(len(s.get("summary", {}).get("rows", [])) for s in results["searches"])
    print(json.dumps({"output": str(OUT), "total_rows": hits}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
