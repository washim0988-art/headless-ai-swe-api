import csv
import os
import sys
import httpx
from bs4 import BeautifulSoup

TARGET_URL = "https://www.merchantcircle.com/search?q=plumbers&location=Austin%2C+TX"
OUTPUT_CSV = "client_lead_list.csv"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_KEY = os.environ.get("GROQ_KEY", "")


def fetch_html() -> str:
    import requests, brotli, json

    resp = requests.post(
        "https://stealth-scraper-api.onrender.com/scrape",
        headers={"X-API-Key": "sk-stealth-pro-99"},
        json={"url": TARGET_URL},
        timeout=30,
    )
    raw = resp.content
    if not raw.startswith(b"{"):
        encoding = resp.headers.get("content-encoding", "")
        if encoding == "br":
            raw = brotli.decompress(raw)
    data = json.loads(raw.decode("utf-8"))
    return data["html"]


def parse_businesses(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    businesses = []

    for item in soup.select("div.company-item"):
        name_el = item.select_one(".company-item-title")
        phone_el = item.select_one(".company-item-phone")
        if name_el and phone_el:
            name = name_el.get_text(strip=True)
            phone = phone_el.get_text(strip=True)
            cleaned = "".join(c for c in phone if c.isdigit() or c in "()+-. ")
            if name and cleaned:
                businesses.append({"business_name": name, "phone": cleaned})

    return businesses


async def generate_email(business_name: str) -> str:
    if not GROQ_KEY:
        return "GROQ_KEY not configured"

    prompt = (
        f"Write a short, 2-sentence cold email offering SEO services "
        f"to a plumber named {business_name}. Do not include the subject line."
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return "GROQ API error"

        result = resp.json()
        return result["choices"][0]["message"]["content"].strip()


async def main():
    print("Fetching HTML via Stealth Scraper API...")
    html = fetch_html()
    print(f"Received {len(html)} bytes")

    businesses = parse_businesses(html)
    print(f"Found {len(businesses)} businesses")

    if not businesses:
        print("No businesses found. Saving debug.html.")
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        sys.exit(1)

    for i, biz in enumerate(businesses):
        print(f"  [{i+1}/{len(businesses)}] Generating email for {biz['business_name']}...")
        biz["ai_email"] = await generate_email(biz["business_name"])

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["business_name", "phone", "ai_email"])
        writer.writeheader()
        writer.writerows(businesses)

    print(f"\nSaved {len(businesses)} leads to {OUTPUT_CSV}")
    for biz in businesses[:3]:
        print(f"\n{biz['business_name']} | {biz['phone']}")
        print(f"  Email: {biz['ai_email'][:120]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
