#!/usr/bin/env python3
import re
import urllib.request

url = "https://comptroller.texas.gov/taxes/franchise/account-status/search"
html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", errors="replace")
for block in re.findall(r"<script[^>]*>(.*?)</script>", html, re.I | re.S):
    if "franchise-tax" in block:
        idx = block.find("apiUrl")
        print(block[idx:idx+5000])
