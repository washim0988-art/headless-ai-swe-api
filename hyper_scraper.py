import argparse
import csv
import re
import requests
from urllib.parse import quote

STEALTH_API_URL = "https://stealth-scraper-api.onrender.com/scrape"
STEALTH_API_KEY = "sk-stealth-pro-99"


def scrape_merchantcircle(city, niche):
    results = []
    page = 1
    while True:
        url = f"https://www.merchantcircle.com/search?q={quote(niche)}&l={quote(city)}&page={page}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            break
        html = resp.text
        if "No results found" in html or page > 10:
            break
        biz_pattern = re.compile(
            r'<a\s+href="/[^"]+"[^>]*class="[^"]*business-name[^"]*"[^>]*>([^<]+)</a>.*?'
            r'(?:<a\s+href="tel:([^"]+)"[^>]*>.*?)?.*?'
            r'(?:<a\s+href="(https?://[^"]+)"[^>]*>.*?)?',
            re.DOTALL,
        )
        for match in biz_pattern.finditer(html):
            name = match.group(1).strip() if match.group(1) else ""
            phone = match.group(2).strip() if match.group(2) else ""
            website = match.group(3).strip() if match.group(3) else ""
            if name:
                results.append({"name": name, "phone": phone, "website": website})
        page += 1
    return results


def fetch_homepage_email(website_url):
    payload = {
        "key": STEALTH_API_KEY,
        "url": website_url,
    }
    try:
        resp = requests.post(STEALTH_API_URL, json=payload, timeout=60)
        if resp.status_code != 200:
            return ""
        html = resp.text
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", html)
        junk_domains = {"example", "sentry", "donotreply"}
        for email in emails:
            local = email.split("@")[0].lower()
            if local not in junk_domains and not any(
                junk in email.lower() for junk in ["example", "sentry", "donotreply"]
            ):
                return email
    except Exception:
        pass
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    parser.add_argument("--niche", required=True)
    args = parser.parse_args()

    businesses = scrape_merchantcircle(args.city, args.niche)

    output_file = f"{args.niche}_{args.city}_emails.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["business_name", "phone", "website", "email"])
        for biz in businesses:
            email = ""
            if biz["website"]:
                email = fetch_homepage_email(biz["website"])
            writer.writerow([biz["name"], biz["phone"], biz["website"], email])

    print(f"Done. Saved {len(businesses)} records to {output_file}")


if __name__ == "__main__":
    main()
