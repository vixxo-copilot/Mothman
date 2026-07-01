#!/usr/bin/env python3
"""Query SC SOS Business Entities Online for registered agent and entity names."""

from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from html import unescape

BASE = "https://businessfilings.sc.gov"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
CTX = ssl.create_default_context()


def fetch(url: str, data: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
    hdrs = {"User-Agent": UA, "Accept": "text/html,application/json,*/*"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST" if data else "GET")
    with urllib.request.urlopen(req, context=CTX, timeout=45) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def strip_tags(html: str) -> str:
    text = re.sub(r"(?s)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?s)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def parse_table_rows(html: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", html):
        cells = [
            re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", c))).strip()
            for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)
        ]
        if len(cells) >= 2 and any(cells):
            rows.append({"cells": cells, "raw": tr[:500]})
    return rows


def try_agent_search(name: str) -> dict:
    out: dict = {"query": name, "attempts": []}
    page_url = f"{BASE}/BusinessFiling/Entity/AgentSearch"
    try:
        status, html = fetch(page_url)
        out["page_status"] = status
        out["page_has_captcha"] = "captcha" in html.lower()
    except Exception as exc:
        out["page_error"] = str(exc)
        return out

    candidates = [
        (f"{BASE}/BusinessFiling/Entity/AgentSearch/Search", {"AgentName": name}),
        (f"{BASE}/BusinessFiling/Entity/AgentSearch/Search", {"agentName": name}),
        (f"{BASE}/BusinessFiling/Entity/AgentSearch", {"AgentName": name, "Search": "Search"}),
        (f"{BASE}/BusinessFiling/Entity/SearchEntity", {"SearchText": name, "SearchType": "AgentName"}),
    ]
    for url, payload in candidates:
        body = urllib.parse.urlencode(payload).encode()
        try:
            status, html = fetch(
                url,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": page_url},
            )
            attempt = {
                "url": url,
                "payload": payload,
                "status": status,
                "has_captcha": "captcha" in html.lower(),
                "text_sample": strip_tags(html)[:1200],
                "rows": parse_table_rows(html)[:20],
            }
            out["attempts"].append(attempt)
        except Exception as exc:
            out["attempts"].append({"url": url, "payload": payload, "error": str(exc)})
    return out


def try_entity_search(name: str) -> dict:
    out: dict = {"query": name, "attempts": []}
    page_url = f"{BASE}/BusinessFiling/Entity/Search"
    candidates = [
        (f"{BASE}/BusinessFiling/Entity/Search", {"SearchText": name, "SearchType": "Contains"}),
        (f"{BASE}/BusinessFiling/Entity/Search", {"BusinessName": name, "SearchType": "Contains"}),
        (f"{BASE}/BusinessFiling/Entity/SearchEntity", {"SearchText": name, "SearchType": "Contains"}),
    ]
    for url, payload in candidates:
        body = urllib.parse.urlencode(payload).encode()
        try:
            status, html = fetch(
                url,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": page_url},
            )
            out["attempts"].append(
                {
                    "url": url,
                    "payload": payload,
                    "status": status,
                    "has_captcha": "captcha" in html.lower(),
                    "text_sample": strip_tags(html)[:1200],
                    "rows": parse_table_rows(html)[:20],
                }
            )
        except Exception as exc:
            out["attempts"].append({"url": url, "payload": payload, "error": str(exc)})
    return out


def main() -> None:
    queries = {
        "agent_names": [
            "Edward Randall Ramsey",
            "Edward R Ramsey",
            "Ramsey, Edward",
            "Edward Ramsey",
        ],
        "entity_names": [
            "Corley Lock and Safe",
            "Corley Lock & Safe",
            "Security Lock and Safe",
            "Elite Security & Maintenance",
            "Corley Security Systems",
        ],
    }
    results = {"agent_searches": [], "entity_searches": []}
    for name in queries["agent_names"]:
        results["agent_searches"].append(try_agent_search(name))
    for name in queries["entity_names"]:
        results["entity_searches"].append(try_entity_search(name))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
