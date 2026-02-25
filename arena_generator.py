import time
import random
import requests
from datetime import datetime, timedelta, timezone

# -----------------------------
# CONFIG
# -----------------------------

DAILY_ARENA_LIMIT = 3
CRYPTO_PRICE_LEVELS = [88000, 90000, 92000, 95000]
BTC_PRICE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

# -----------------------------
# STATE (in-memory v1)
# -----------------------------

arenas_created_today = 0
current_day = datetime.now(timezone.utc).date()
active_arenas = []  # arenas waiting for resolution

# -----------------------------
# PRICE FETCHER
# -----------------------------

def get_btc_price():
    response = requests.get(BTC_PRICE_URL, timeout=10)
    data = response.json()
    return float(data["price"])

# -----------------------------
# ARENA GENERATOR
# -----------------------------

def generate_btc_arena(arena_number_today: int):
    now = datetime.now(timezone.utc)
    target = random.choice(CRYPTO_PRICE_LEVELS)
    deadline = now + timedelta(days=3)

    arena_id = f"SYLON-{now.strftime('%Y%m%d')}-{arena_number_today:03d}"

    question = (
        f"Will BTC hit {target} USD before "
        f"{deadline.strftime('%Y-%m-%d %H:%M')} UTC?"
    )

    rules = (
        "Resolution Rule: YES if BTC last traded price on Binance "
        "reaches or exceeds the target before the deadline."
    )

    return {
        "arena_id": arena_id,
        "question": question,
        "target": target,
        "deadline": deadline,
        "rules": rules,
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

# -----------------------------
# FORMATTERS (MANUAL MODE)
# -----------------------------

def format_arena_tweet(arena):
    return (
        "🧠 SYLON PREDICTION ARENA\n\n"
        f"Arena ID: {arena['arena_id']}\n\n"
        f"{arena['question']}\n\n"
        f"Deadline: {arena['deadline'].strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        "Reply YES or NO 👇\n\n"
        f"{arena['rules']}"
    )

def format_resolution(arena):
    return (
        "🧠 SYLON ARENA RESOLVED\n\n"
        f"Arena ID: {arena['arena_id']}\n\n"
        f"Outcome: {arena['outcome']}\n"
        f"BTC Price: {arena['resolved_price']} USD\n\n"
        f"{arena['question']}"
    )

# -----------------------------
# RESOLUTION ENGINE (REAL)
# -----------------------------

def resolve_arena(arena):
    btc_price = get_btc_price()

    if btc_price >= arena["target"]:
        outcome = "YES"
    else:
        outcome = "NO"

    arena["status"] = "RESOLVED"
    arena["outcome"] = outcome
    arena["resolved_price"] = btc_price
    arena["resolved_at"] = datetime.now(timezone.utc)

    return arena

# -----------------------------
# MAIN LOOP
# -----------------------------

if __name__ == "__main__":

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()

        # Reset daily counter at UTC midnight
        if today != current_day:
            arenas_created_today = 0
            current_day = today
            print(f"\nNew UTC Day Started: {current_day}\n")

        # Create new arena if under limit
        if arenas_created_today < DAILY_ARENA_LIMIT:
            arena = generate_btc_arena(arenas_created_today + 1)
            arenas_created_today += 1
            active_arenas.append(arena)

            print("\n--- READY TO POST ON X ---")
            print(format_arena_tweet(arena))
            print("--- END ---\n")

        # Resolve arenas past deadline
        for arena in list(active_arenas):
            if now >= arena["deadline"]:
                resolved = resolve_arena(arena)
                active_arenas.remove(arena)

                print("\n--- ARENA RESOLVED ---")
                print(format_resolution(resolved))
                print("--- END ---\n")

        # Check every hour
        time.sleep(3600)
