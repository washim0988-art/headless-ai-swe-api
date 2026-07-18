import requests, json, brotli
from bs4 import BeautifulSoup

resp = requests.post(
    "https://stealth-scraper-api.onrender.com/scrape",
    headers={"X-API-Key": "sk-stealth-pro-99"},
    json={"url": "https://www.merchantcircle.com/search?q=plumbers&location=Austin%2C+TX"},
    timeout=20,
)
raw = resp.content
if not raw.startswith(b"{"):
    encoding = resp.headers.get("content-encoding", "")
    if encoding == "br":
        raw = brotli.decompress(raw)
data = json.loads(raw.decode("utf-8"))
html = data["html"]

soup = BeautifulSoup(html, "html.parser")
print(f"Title: {soup.title.string if soup.title else 'N/A'}")
print(f"Total text length: {len(soup.get_text())}")

# Check for business-related content
for cls in ["business", "name", "title", "phone", "contact", "result", "card", "listing", "item", "merchant"]:
    els = soup.find_all(class_=lambda c: c and cls in c.lower())
    if els:
        print(f".{cls}: {len(els)} elements")
        if els:
            print(f"  First: {els[0].get_text(strip=True)[:100]}")

# Check for phone-like patterns
import re
phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', html)
print(f"Phone numbers found: {len(phones)}")
if phones:
    for p in phones[:5]:
        print(f"  {p}")

# Check for business name-like patterns
business_names = re.findall(r'[A-Z][a-z]+(?: [A-Z][a-z]+)+(?:\s+(?:LLC|Inc|Plumbing|Services|Company|Repair))?', html)
print(f"\nPotential business names: {len(business_names)}")
if business_names:
    for n in business_names[:10]:
        print(f"  {n}")

# Look at the structure 
print("\n--- 50 most common classes ---")
from collections import Counter
classes = Counter()
for el in soup.find_all(class_=True):
    for c in (el.get("class") or []):
        classes[c] += 1
for cls, cnt in classes.most_common(50):
    print(f"  .{cls}: {cnt}")
