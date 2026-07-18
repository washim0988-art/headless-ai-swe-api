import csv
import sys
import brotli
import requests
from bs4 import BeautifulSoup


API_URL = "https://stealth-scraper-api.onrender.com/scrape"
API_KEY = "sk-stealth-pro-99"
TARGET_URL = "https://weworkremotely.com/"
OUTPUT_CSV = "remote_tech_leads.csv"


def fetch_html() -> str:
    resp = requests.post(
        API_URL,
        headers={"X-API-Key": API_KEY},
        json={"url": TARGET_URL},
        timeout=30,
    )
    resp.raise_for_status()

    raw = resp.content

    if not raw.startswith(b"{"):
        encoding = resp.headers.get("content-encoding", "")
        if encoding == "br":
            raw = brotli.decompress(raw)

    body = raw.decode("utf-8")
    data = __import__("json").loads(body)
    return data["html"]


def parse_jobs(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for li in soup.select("li.new-listing-container"):
        company_el = li.select_one(".new-listing__company-name")
        title_el = li.select_one(".new-listing__header__title__text")
        url_el = li.select_one("a.listing-link--unlocked")
        if company_el and title_el:
            company = company_el.get_text(strip=True)
            title = title_el.get_text(strip=True)
            url = ""
            if url_el:
                href = url_el.get("href", "")
                if href:
                    url = "https://weworkremotely.com" + href
            if company and title:
                jobs.append({"company": company, "title": title, "url": url})

    return jobs


def save_csv(jobs: list[dict]):
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "title", "url"])
        writer.writeheader()
        writer.writerows(jobs)
    print(f"Saved {len(jobs)} job listings to {OUTPUT_CSV}")


def main():
    try:
        print("Fetching HTML from Stealth Scraper API...")
        html = fetch_html()
        print(f"Received {len(html)} bytes of HTML")
    except Exception as e:
        print(f"Error fetching HTML: {e}", file=sys.stderr)
        sys.exit(1)

    jobs = parse_jobs(html)
    if not jobs:
        print("No job listings found. Saving debug.html for inspection.")
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(html)
    else:
        save_csv(jobs)


if __name__ == "__main__":
    main()
