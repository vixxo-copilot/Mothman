#!/usr/bin/env python3
"""Browser-based SC SOS registered agent and entity search via Playwright."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

BASE = "https://businessfilings.sc.gov"
OUT = Path(__file__).resolve().parent / "sc_sos_playwright_results.json"

AGENT_QUERIES = [
    "Edward Randall Ramsey",
    "Edward R Ramsey",
    "Ramsey, Edward",
    "Edward Ramsey",
]

ENTITY_QUERIES = [
    "Corley Lock and Safe",
    "Corley Lock & Safe",
    "Security Lock and Safe",
    "Elite Security & Maintenance",
    "Corley Security Systems",
]


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_results_table(page) -> list[dict]:
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
    fields: dict[str, str] = {}
    patterns = [
        (r"Entity Name\s*[:]\s*(.+?)(?:Entity Type|Entity ID|$)", "entity_name"),
        (r"Entity Type\s*[:]\s*(.+?)(?:Entity ID|Status|$)", "entity_type"),
        (r"Entity ID\s*[:]\s*(\S+)", "entity_id"),
        (r"Status\s*[:]\s*(.+?)(?:Domestic|Foreign|Effective|$)", "status"),
        (r"Effective Date\s*[:]\s*(\S+)", "effective_date"),
        (r"Registered Agent\s*[:]\s*(.+?)(?:Agent Address|Principal|$)", "registered_agent"),
        (r"Principal Office Address\s*[:]\s*(.+?)(?:Mailing|Officers|$)", "principal_office"),
    ]
    for pat, key in patterns:
        m = re.search(pat, text, re.I)
        if m:
            fields[key] = clean(m.group(1))
    officers: list[str] = []
    for line in text.split(" "):
        pass
    officer_block = re.search(r"Officers.*?Members.*?(?:Filing History|$)", text, re.I | re.S)
    if officer_block:
        chunk = officer_block.group(0)
        for row in re.findall(r"(President|Secretary|Manager|Member|Treasurer|Director)[^A-Z]{0,20}([A-Za-z ,.'-]+)", chunk):
            officers.append(f"{row[0]}: {clean(row[1])}")
    if officers:
        fields["officers"] = officers
    fields["raw_excerpt"] = text[:4000]
    fields["url"] = page.url
    return fields


def search_agent(page, name: str) -> dict:
    result: dict = {"query": name, "rows": [], "profiles": [], "errors": []}
    url = f"{BASE}/BusinessFiling/Entity/AgentSearch"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)
        inp = page.locator("input[type='text'], input[name*='Agent' i], input[id*='Agent' i]").first
        inp.fill(name)
        page.locator("button:has-text('Search'), input[type='submit'][value*='Search' i]").first.click()
        page.wait_for_timeout(3000)
        result["rows"] = parse_results_table(page)
        result["page_text"] = clean(page.locator("body").inner_text())[:2500]
        for row in result["rows"][:10]:
            link = row.get("link")
            if not link:
                continue
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)
                result["profiles"].append(parse_profile(page))
            except Exception as exc:
                result["errors"].append(f"profile {link}: {exc}")
    except Exception as exc:
        result["errors"].append(str(exc))
    return result


def search_entity(page, name: str) -> dict:
    result: dict = {"query": name, "rows": [], "profiles": [], "errors": []}
    url = f"{BASE}/BusinessFiling/Entity/Search"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)
        inp = page.locator("input[type='text'], input[name*='Business' i], input[id*='Business' i]").first
        inp.fill(name)
        page.locator("button:has-text('Search'), input[type='submit'][value*='Search' i]").first.click()
        page.wait_for_timeout(3000)
        result["rows"] = parse_results_table(page)
        result["page_text"] = clean(page.locator("body").inner_text())[:2500]
        for row in result["rows"][:8]:
            link = row.get("link")
            if not link:
                continue
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)
                result["profiles"].append(parse_profile(page))
            except Exception as exc:
                result["errors"].append(f"profile {link}: {exc}")
    except Exception as exc:
        result["errors"].append(str(exc))
    return result


def main() -> int:
    results = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent_searches": [],
        "entity_searches": [],
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
        for q in AGENT_QUERIES:
            results["agent_searches"].append(search_agent(page, q))
        for q in ENTITY_QUERIES:
            results["entity_searches"].append(search_entity(page, q))
        browser.close()
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "agent_hits": sum(len(x["rows"]) for x in results["agent_searches"])}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
