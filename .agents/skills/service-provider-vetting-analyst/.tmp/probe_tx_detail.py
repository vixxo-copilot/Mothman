#!/usr/bin/env python3
import json
import re
import urllib.parse
import urllib.request

SEARCH_PAGE = "https://comptroller.texas.gov/taxes/franchise/account-status/search"
html = urllib.request.urlopen(urllib.request.Request(SEARCH_PAGE, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", errors="replace")
for block in re.findall(r"<script[^>]*>(.*?)</script>", html, re.I | re.S):
    if "franchise-tax" in block:
        for pat in ["detail", "taxpayerId", "render", "href", "window.open", "location"]:
            if pat in block:
                pass
        if "detail" in block.lower() or "render:" in block:
            print(block[block.find("render"):block.find("render")+4000])

IDS = ["32067800196", "32105525532"]
candidates = [
    "https://comptroller.texas.gov/data-search/franchise-tax/{}",
    "https://comptroller.texas.gov/data-search/franchise-tax-detail?taxpayerId={}",
    "https://comptroller.texas.gov/data-search/franchise-tax-detail/{}",
    "https://comptroller.texas.gov/data-search/franchise-tax?id={}",
    "https://comptroller.texas.gov/data-search/franchise-tax?taxpayerId={}",
    "https://mycpa.cpa.state.tx.us/coa/coaDetailServlet?taxpayerId={}",
    "https://mycpa.cpa.state.tx.us/coa/coaDetailServlet?taxpayerID={}",
]

for tid in IDS:
    print("\n==== taxpayer", tid, "====")
    for tmpl in candidates:
        url = tmpl.format(tid)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/html",
                "Referer": SEARCH_PAGE,
            },
        )
        try:
            resp = urllib.request.urlopen(req, timeout=20)
            body = resp.read(2000).decode("utf-8", errors="replace")
            print(url, "->", resp.status, body[:300].replace("\n", " "))
        except Exception as exc:
            print(url, "->", exc)
