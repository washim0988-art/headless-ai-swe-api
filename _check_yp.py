import requests, json, brotli, re
from bs4 import BeautifulSoup

resp = requests.post(
    "https://stealth-scraper-api.onrender.com/scrape",
    headers={"X-API-Key": "sk-stealth-pro-99"},
    json={"url": "https://www.yellowpages.com/search?search_terms=plumbers&geo_location_terms=Austin%2C+TX"},
    timeout=30,
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
print(f"Body text length: {len(soup.get_text())}")
print(f"First 2000 body text: {soup.get_text()[:2000]}")

# Check all text for clues
text = soup.get_text()
keywords = ["plumber", "blocked", "captcha", "robot", "verify", "access", "denied", "phone", "business", "call"]
for kw in keywords:
    if kw in text.lower():
        print(f"  Contains '{kw}'")
