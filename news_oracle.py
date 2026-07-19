import os
import re
import warnings

import brotli
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.constants import POLYGON

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

STEALTH_API_URL = "https://stealth-scraper-api.onrender.com/scrape"
STEALTH_API_KEY = "sk-stealth-pro-99"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

MARKET_ID = "0xdeadbeef"  # placeholder


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
    return __import__("json").loads(raw.decode("utf-8"))["html"]


def fetch_top_headlines():
    resp = requests.get(
        "https://cointelegraph.com/rss",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    all_titles = soup.select("title")
    headlines = []
    for tag in all_titles[1:]:
        text = tag.get_text(strip=True)
        if text:
            headlines.append(text)
        if len(headlines) >= 5:
            break
    return headlines


def ask_groq(prompt):
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")
    resp = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def execute_polymarket_trade(market_id, outcome, amount):
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("PRIVATE_KEY environment variable not set")
    chain_id = int(os.environ.get("CHAIN_ID", "137"))

    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=chain_id,
    )

    order_args = OrderArgs(
        price=1.0,
        size=amount,
        side="BUY",
        token_id=market_id,
    )

    signed_order = client.create_order(order_args)
    receipt = client.post_order(signed_order)
    print(f"Order placed: {receipt}")
    return receipt


def main():
    print("Fetching latest crypto headlines...")
    headlines = fetch_top_headlines()
    print(f"Top {len(headlines)} headlines:")
    for h in headlines:
        print(f"  - {h}")

    prompt = (
        f"Based on these headlines: {headlines}\n"
        "Will Bitcoin close above $65,000 tomorrow? "
        "Answer strictly with 'YES' or 'NO'."
    )
    print("\nSending to Groq LLM for analysis...")
    answer = ask_groq(prompt)
    print(f"LLM prediction: {answer}")

    match = re.search(r"\b(YES|NO)\b", answer.upper())
    if not match:
        print(f"Could not parse YES/NO from: {answer}")
        return

    outcome = match.group(1)
    execute_polymarket_trade(MARKET_ID, outcome, 10)


if __name__ == "__main__":
    main()
