import requests, json, brotli

urls = [
    "https://www.yellowpages.com/search?search_terms=plumbers&geo_location_terms=Austin%2C+TX",
    "https://www.manta.com/s?search=plumbers&location=Austin%2C+TX",
]

for target in urls:
    resp = requests.post(
        "https://stealth-scraper-api.onrender.com/scrape",
        headers={"X-API-Key": "sk-stealth-pro-99"},
        json={"url": target},
        timeout=30,
    )
    raw = resp.content
    if not raw.startswith(b"{"):
        encoding = resp.headers.get("content-encoding", "")
        if encoding == "br":
            raw = brotli.decompress(raw)
    data = json.loads(raw.decode("utf-8"))
    html = data["html"]
    print(f"\n=== TARGET: {target} ===")
    print(f"Status: {resp.status_code}, HTML length: {len(html)}")
    print(f"Contains 'plumber': {'plumber' in html.lower()[:5000]}")
    print(f"First 300 chars: {html[:300]}")
