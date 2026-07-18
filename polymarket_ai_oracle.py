import os
import sys
import json
import time
import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = "meta-llama/llama-3.1-8b-instruct:free"

MARKET_SLUG = "btc-updown-5m"


def ask_oracle(question: str) -> tuple[str, str]:
    prompt = (
        f"{question} "
        f"Answer strictly with 'YES' or 'NO' and provide a 1-sentence reason."
    )

    resp = httpx.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"OpenRouter API error {resp.status_code}: {resp.text}")
        return "ERROR", "API call failed"

    content = resp.json()["choices"][0]["message"]["content"].strip()
    decision = "YES" if content.upper().startswith("YES") else "NO"
    return decision, content


def get_current_market_timestamp(duration: int = 300) -> int:
    return (int(time.time()) // duration) * duration


def resolve_market_id(market_ts: int) -> dict:
    slug = f"{MARKET_SLUG}-{market_ts}"
    resp = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={"slug": slug, "closed": "false", "active": "true"},
        timeout=10,
    )
    if resp.status_code != 200 or not resp.json():
        raise RuntimeError(f"Market {slug} not found on Polymarket")
    market = resp.json()[0]
    token_ids = json.loads(market["clobTokenIds"])
    return {
        "market_id": market["id"],
        "slug": slug,
        "question": market["question"],
        "up_token_id": token_ids[0],
        "down_token_id": token_ids[1],
    }


def execute_polymarket_trade(
    market_id: str,
    token_id: str,
    side: str,
    amount_usd: float = 10.0,
) -> dict:
    """
    Placeholder — plug in py-clob-client calls here once API keys are configured.

    Expected signature for the real implementation:
        from py_clob_client_v2.client import ClobClient
        from py_clob_client_v2.clob_types import OrderArgs, OrderType

        client = ClobClient(host="https://clob.polymarket.com", ...)
        order_args = OrderArgs(
            token_id=token_id,
            price=0.50,
            size=int(amount_usd / 0.50),
            side=side.upper(),
        )
        resp = client.create_and_post_order(order_args, order_type=OrderType.GTC)
        return resp
    """
    print(
        f"  [TRADE] market={market_id} token={token_id} side={side} "
        f"amount=${amount_usd:.2f}"
    )
    print("  [TRADE] Placeholder — no real order placed. Set up py-clob-client to execute.")
    return {"status": "simulated", "side": side, "amount_usd": amount_usd}


def main():
    if not OPENROUTER_KEY:
        print("Set OPENROUTER_API_KEY environment variable.")
        sys.exit(1)

    question = (
        "Based on current news, will Bitcoin close above $65,000 "
        "in the next 5-minute window? "
        "Answer strictly with 'YES' or 'NO' and provide a 1-sentence reason."
    )

    print("Asking LLM oracle...")
    decision, raw = ask_oracle(question)
    print(f"Oracle says: {decision}")
    print(f"Reason: {raw}")

    if decision == "ERROR":
        sys.exit(1)

    market_ts = get_current_market_timestamp()
    try:
        market = resolve_market_id(market_ts)
    except RuntimeError as e:
        print(f"Market lookup failed: {e}")
        sys.exit(1)

    print(f"Market: {market['question']}")
    print(f"Slug:   {market['slug']}")

    if decision == "YES":
        token_id = market["up_token_id"]
        side = "BUY"
    else:
        token_id = market["down_token_id"]
        side = "SELL"

    execute_polymarket_trade(
        market_id=market["market_id"],
        token_id=token_id,
        side=side,
        amount_usd=10.0,
    )


if __name__ == "__main__":
    main()
