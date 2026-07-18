from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, HttpUrl
from typing import Dict
import httpx
import os

app = FastAPI(title="Scrape API")

API_KEY = os.environ.get("SCRAPE_API_KEY", "sk-default-change-me")

class ScrapeRequest(BaseModel):
    url: HttpUrl

class ScrapeResponse(BaseModel):
    html: str
    status_code: int

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

async def verify_api_key(request: Request):
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")
    return True

@app.post("/scrape", response_model=ScrapeResponse, dependencies=[Depends(verify_api_key)])
async def scrape(req: ScrapeRequest):
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(str(req.url), headers=BROWSER_HEADERS)
            return ScrapeResponse(html=resp.text, status_code=resp.status_code)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {e}")

@app.get("/health")
async def health():
    return {"status": "ok"}
