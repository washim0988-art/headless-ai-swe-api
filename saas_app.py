import os
import re

import brotli
import httpx
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Lead Gen SaaS")

SCRAPE_API = "https://stealth-scraper-api.onrender.com/scrape"
SCRAPE_KEY = os.getenv("SCRAPE_API_KEY", "sk-stealth-pro-99")


class GenerateRequest(BaseModel):
    city: str
    niche: str


def fetch_listings(city: str, niche: str) -> list[dict]:
    q = niche.replace(" ", "+")
    loc = city.replace(" ", "+")
    url = f"https://www.merchantcircle.com/search?q={q}&location={loc}"

    resp = requests.post(
        SCRAPE_API,
        headers={"X-API-Key": SCRAPE_KEY},
        json={"url": url},
        timeout=30,
    )
    raw = resp.content
    if not raw.startswith(b"{"):
        encoding = resp.headers.get("content-encoding", "")
        if encoding == "br":
            raw = brotli.decompress(raw)
    data = __import__("json").loads(raw.decode("utf-8"))
    html = data["html"]

    soup = BeautifulSoup(html, "html.parser")
    businesses = []

    for item in soup.select("div.company-item"):
        name_el = item.select_one(".company-item-title")
        phone_el = item.select_one(".company-item-phone")
        website_el = item.select_one('a[href^="http"]:not([href*="merchantcircle"])')
        if name_el and phone_el:
            name = name_el.get_text(strip=True)
            phone = phone_el.get_text(strip=True)
            website = website_el.get("href", "") if website_el else ""
            cleaned = "".join(c for c in phone if c.isdigit() or c in "()+-. ")
            if name and cleaned:
                businesses.append({"business_name": name, "phone": cleaned, "website": website})

    return businesses


async def extract_email(website_url: str) -> str:
    if not website_url:
        return "No email found"

    payload = {"key": SCRAPE_KEY, "url": website_url}

    async with httpx.AsyncClient() as client:
        resp = await client.post(SCRAPE_API, json=payload, timeout=60)
        if resp.status_code != 200:
            return "No email found"

        html = resp.text
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", html)
        junk_domains = {"example", "sentry", "donotreply"}
        for email in emails:
            local = email.split("@")[0].lower()
            if local not in junk_domains and not any(
                junk in email.lower() for junk in ["example", "sentry", "donotreply"]
            ):
                return email

    return "No email found"


@app.get("/")
async def serve_index():
    return FileResponse("index.html")


@app.post("/generate")
async def generate(req: GenerateRequest):
    businesses = fetch_listings(req.city, req.niche)

    if not businesses:
        return JSONResponse(
            content={"error": f"No {req.niche} listings found in {req.city}"},
            status_code=404,
        )

    for biz in businesses:
        biz["email"] = await extract_email(biz.get("website", ""))

    return businesses
