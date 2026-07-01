#!/usr/bin/env python3
import re
import urllib.request

url = "https://comptroller.texas.gov/taxes/franchise/account-status/search"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
print("len", len(html))
for pat in ["ajax", "Servlet", "franchise-tax", "dataTables", "searchValue", "api.comptroller", "entityName", "coa"]:
    print(pat, html.lower().count(pat.lower()))
for m in re.findall(r'(?:src|href|action|url\s*:\s*["\'])([^"\']+)', html, re.I):
    if any(x in m.lower() for x in ["coa", "servlet", "ajax", "search", "franchise", "api", "datatable"]):
        print("link:", m)
# dump script blocks mentioning search
for block in re.findall(r"<script[^>]*>(.*?)</script>", html, re.I | re.S):
    if any(x in block.lower() for x in ["search", "ajax", "datatable", "franchise"]):
        print("--- script ---")
        print(block[:2000])
