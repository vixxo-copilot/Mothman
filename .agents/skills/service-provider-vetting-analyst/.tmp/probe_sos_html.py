#!/usr/bin/env python3
import re
import ssl
import urllib.request

url = "https://businessfilings.sc.gov/BusinessFiling/Entity/AgentSearch"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=30).read().decode(
    "utf-8", "replace"
)
print("len", len(html))
for m in re.finditer(r"<form[^>]*>(.*?)</form>", html, re.I | re.S):
    print("FORM", m.group(0)[:1200])
for m in re.finditer(r'src="([^"]+)"', html):
    s = m.group(1)
    if ".js" in s.lower():
        print("JS", s)
for m in re.finditer(r'"(/BusinessFiling[^"]+)"', html):
    print("PATH", m.group(1))
if "captcha" in html.lower():
    print("HAS CAPTCHA IN PAGE")
