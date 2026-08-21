#!/usr/bin/env python3
"""Follow-up SC SOS entity name searches in same browser session."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://businessfilings.sc.gov"
OUT = Path(__file__).resolve().parent / "sc_sos_entity_results.json"

ENTITY_QUERIES = [
    "Corley Lock",
    "Security Lock",
    "Elite Security",
    "Corley Security",
    "Keystone Consulting",
]


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_rows(page) -> list[dict]:
    rows: list[dict] = []
    for tr in page.locator("table tbody tr, table tr").all():
        cells = [clean(c) for c in tr.locator("td, th").all_text_contents()]
        if len(cells) >= 2 and any(cells):
            link = ""
            a = tr.locator("a").first
            if a.count():
                href = a.get_attribute("href") or ""
                if href:
                    link = href if href.startswith("http") else f"{BASE}{href}"
            rows.append({"cells": cells, "link": link})
    return rows


def parse_profile(page) -> dict:
    text = clean(page.locator("body").inner_text())
    return {
        "url": page.url,
        "raw_excerpt": text[:5000],
    }


def search_entity(page, name: str) -> dict:
    result: dict = {"query": name, "rows": [], "profiles": [], "errors": []}
    url = f"{BASE}/BusinessFiling/Entity/Search"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        if "captcha" in page.locator("body").inner_text().lower():
            result["captcha"] = True
        inp = page.locator("#SearchTextBox, input[name='SearchText'], input[type='text']").first
        inp.fill(name)
        contains = page.locator("input[type='radio'][value='Contains'], label:has-text('Contains')").first
        if contains.count():
            try:
                contains.click()
            except Exception:
                pass
        page.locator("button:has-text('Search'), input[type='submit'][value*='Search' i]").first.click()
        page.wait_for_timeout(4000)
        result["page_text"] = clean(page.locator("body").inner_text())[:3000]
        result["captcha_after"] = "captcha" in result["page_text"].lower()
        result["rows"] = parse_rows(page)
        for row in result["rows"][:10]:
            link = row.get("link")
            if not link:
                continue
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)
                result["profiles"].append(parse_profile(page))
            except Exception as exc:
                result["errors"].append(str(exc))
    except Exception as exc:
        result["errors"].append(str(exc))
    return result


def main() -> None:
    results = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "entity_searches": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{BASE}/BusinessFiling/Entity/AgentSearch", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.locator("#SearchTextBox").fill("Edward Randall Ramsey")
        page.locator("#AgentSearchButton").click()
        page.wait_for_timeout(3000)
        for q in ENTITY_QUERIES:
            results["entity_searches"].append(search_entity(page, q))
        browser.close()
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "hits": sum(len(x["rows"]) for x in results["entity_searches"])}, indent=2))


if __name__ == "__main__":
    main()
