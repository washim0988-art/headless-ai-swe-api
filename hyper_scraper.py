import argparse
import csv
import json
import re

import brotli
import requests
from bs4 import BeautifulSoup

STEALTH_API_URL = "https://stealth-scraper-api.onrender.com/scrape"
STEALTH_API_KEY = "sk-stealth-pro-99"


def fetch_via_stealth(url):
    resp = requests.post(
        STEALTH_API_URL,
        headers={"X-API-Key": STEALTH_API_KEY},
        json={"url": url},
        timeout=60,
    )
    raw = resp.content
    if not raw.startswith(b"{"):
        encoding = resp.headers.get("content-encoding", "")
        if encoding == "br":
            raw = brotli.decompress(raw)
    data = json.loads(raw.decode("utf-8"))
    return data["html"]


def find_website_on_detail_page(detail_url):
    try:
        html = fetch_via_stealth(detail_url)
    except Exception:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    external = soup.select_one(
        'a[href^="http"]:not([href*="merchantcircle"]):not([href*="facebook"]):not([href*="twitter"]):not([href*="onetrust"]):not([href*="google"])'
    )
    if external:
        return external["href"]
    url_meta = soup.select_one('[itemprop="url"][href]')
    if url_meta:
        return url_meta["href"]
    return ""


def scrape_merchantcircle(city, niche):
    results = []
    page = 1
    while page <= 10:
        url = f"https://www.merchantcircle.com/search?q={niche}&l={city}&page={page}"
        try:
            html = fetch_via_stealth(url)
        except Exception:
            break
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("div.company-item")
        if not items:
            break
        for item in items:
            name_el = item.select_one(".company-item-title")
            phone_el = item.select_one(".company-item-phone")
            link_el = item.select_one(
                ".company-item-title a, h3.company-item-title a"
            )
            if name_el and phone_el:
                name = name_el.get_text(strip=True)
                phone = phone_el.get_text(strip=True)
                cleaned = "".join(c for c in phone if c.isdigit() or c in "()+-. ")
                if not name or not cleaned:
                    continue

                website = ""
                detail_url = link_el["href"] if link_el else ""
                if detail_url and detail_url.startswith("/"):
                    detail_url = "https://www.merchantcircle.com" + detail_url
                if detail_url and "merchantcircle.com" in detail_url:
                    website = find_website_on_detail_page(detail_url)

                results.append({
                    "name": name,
                    "phone": cleaned,
                    "website": website,
                    "detail_url": detail_url,
                })
        page += 1
    return results


def extract_emails_from_html(html):
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", html)
    junk_domains = {"example", "sentry", "donotreply"}
    valid = []
    for email in emails:
        local = email.split("@")[0].lower()
        if local not in junk_domains and not any(
            junk in email.lower() for junk in ["example", "sentry", "donotreply"]
        ):
            valid.append(email)
    return valid


def fetch_homepage_email(website_url, debug=False):
    urls_to_try = [website_url.rstrip("/")]
    parsed = website_url.rstrip("/")
    for suffix in ["/contact", "/contact-us"]:
        candidate = parsed + suffix
        if candidate not in urls_to_try:
            urls_to_try.append(candidate)

    for url in urls_to_try:
        try:
            html = fetch_via_stealth(url)
            if debug:
                with open("debug_business.html", "w", encoding="utf-8") as f:
                    f.write(html)
            emails = extract_emails_from_html(html)
            if emails:
                return emails[0]
        except Exception:
            continue
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    parser.add_argument("--niche", required=True)
    args = parser.parse_args()

    businesses = scrape_merchantcircle(args.city, args.niche)
    debug_saved = False

    output_file = f"{args.niche}_{args.city}_emails.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["business_name", "phone", "website", "email"])
        for biz in businesses:
            email = ""
            if biz["website"]:
                save_debug = not debug_saved
                email = fetch_homepage_email(biz["website"], debug=save_debug)
                if save_debug:
                    debug_saved = True
            writer.writerow([biz["name"], biz["phone"], biz["website"], email])

    print(f"Done. Saved {len(businesses)} records to {output_file}")


if __name__ == "__main__":
    main()
