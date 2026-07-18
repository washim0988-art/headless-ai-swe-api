import os
import re
import time

import brotli
import httpx
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="AI Lead Gen SaaS")

LLM_URL = "https://api.groq.com/openai/v1/chat/completions"
LLM_MODEL = "llama-3.1-8b-instant"
LLM_KEY = os.getenv("GROQ_API_KEY", "")

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
        if name_el and phone_el:
            name = name_el.get_text(strip=True)
            phone = phone_el.get_text(strip=True)
            cleaned = "".join(c for c in phone if c.isdigit() or c in "()+-. ")
            if name and cleaned:
                businesses.append({"business_name": name, "phone": cleaned})

    return businesses


async def generate_email(business_name: str, niche: str) -> str:
    if not LLM_KEY:
        return "GROQ_API_KEY not configured"

    prompt = (
        f"Write a short, 2-sentence cold email offering SEO services "
        f"to a {niche} named {business_name}. Do not include the subject line."
    )

    time.sleep(1)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            LLM_URL,
            headers={
                "Authorization": f"Bearer {LLM_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if resp.status_code == 200:
            result = resp.json()
            return result["choices"][0]["message"]["content"].strip()
        print(f"Groq LLM call failed ({resp.status_code}): {resp.text}")

    return "AI generation temporarily unavailable."


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
        biz["ai_email"] = await generate_email(biz["business_name"], req.niche)

    return businesses
