import requests, json, brotli
from bs4 import BeautifulSoup

targets = [
    "https://www.hotfrog.com/search/?q=plumbers&city=Austin&state=TX",
    "https://www.showmelocal.com/category.aspx?city=Austin&state=TX&cat=Plumbers",
    "https://www.merchantcircle.com/search?q=plumbers&location=Austin%2C+TX",
    "https://www.brownbook.net/search/plumbers/Austin-TX",
]

for target in targets:
    try:
        resp = requests.post(
            "https://stealth-scraper-api.onrender.com/scrape",
            headers={"X-API-Key": "sk-stealth-pro-99"},
            json={"url": target},
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
        text = soup.get_text().lower()
        has_plumber = "plumber" in text or "plumbing" in text
        has_phone = "(" in text and ")" in text
        print(f"{target[:60]}... | len={len(html):>6} | plumber={has_plumber} | phone={has_phone} | title={soup.title.string[:60] if soup.title else 'N/A'}")
    except Exception as e:
        print(f"{target[:60]}... | ERROR: {e}")
