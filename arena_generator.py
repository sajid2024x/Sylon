import time
import random
import requests
from datetime import datetime, timedelta, timezone

# -----------------------------
# CONFIG
# -----------------------------

DAILY_ARENA_LIMIT = 3
BTC_PRICE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

HIT_LEVELS = [88000, 90000, 92000, 95000]
FLOOR_LEVELS = [82000, 85000, 88000]

# -----------------------------
# STATE (in-memory v1)
# -----------------------------

arenas_created_today = 0
current_day = datetime.now(timezone.utc).date()
active_arenas = []

# -----------------------------
# PRICE FETCHER
# -----------------------------

def get_btc_price():
    response = requests.get(BTC_PRICE_URL, timeout=10)
    data = response.json()
    return float(data["price"])

# -----------------------------
# ARENA GENERATORS
# -----------------------------

def generate_hit_target_arena(arena_number_today: int):
    now = datetime.now(timezone.utc)
    target = random.choice(HIT_LEVELS)
    deadline = now + timedelta(days=3)

    arena_id = f"SYLON-{now.strftime('%Y%m%d')}-{arena_number_today:03d}"

    return {
        "arena_id": arena_id,
        "type": "HIT_TARGET",
        "question": f"Will BTC hit {target} USD before {deadline.strftime('%Y-%m-%d %H:%M')} UTC?",
        "target": target,
        "deadline": deadline,
        "rules": "YES if BTC price on Binance reaches or exceeds target before deadline.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

def generate_stay_above_arena(arena_number_today: int):
    now = datetime.now(timezone.utc)
    floor = random.choice(FLOOR_LEVELS)
    deadline = now + timedelta(days=2)

    arena_id = f"SYLON-{now.strftime('%Y%m%d')}-{arena_number_today:03d}"

    return {
        "arena_id": arena_id,
        "type": "STAY_ABOVE",
        "question": f"Will BTC stay above {floor} USD until {deadline.strftime('%Y-%m-%d %H:%M')} UTC?",
        "floor": floor,
        "deadline": deadline,
        "rules": "YES if BTC price on Binance is still above floor at deadline.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

# -----------------------------
# FORMATTERS
# -----------------------------

def format_arena(arena):
    return (
        "🧠 SYLON PREDICTION ARENA\n\n"
        f"Arena ID: {arena['arena_id']}\n\n"
        f"{arena['question']}\n\n"
        f"Deadline: {arena['deadline'].strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        "Reply YES or NO 👇\n\n"
        f"Resolution Rule: {arena['rules']}"
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
# RESOLUTION ENGINE
# -----------------------------

def resolve_arena(arena):
    price = get_btc_price()

    if arena["type"] == "HIT_TARGET":
        outcome = "YES" if price >= arena["target"] else "NO"

    elif arena["type"] == "STAY_ABOVE":
        outcome = "YES" if price >= arena["floor"] else "NO"

    arena["status"] = "RESOLVED"
    arena["outcome"] = outcome
    arena["resolved_price"] = price
    arena["resolved_at"] = datetime.now(timezone.utc)

    return arena

# -----------------------------
# MAIN LOOP
# -----------------------------

if __name__ == "__main__":

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()

        if today != current_day:
            arenas_created_today = 0
            current_day = today
            print(f"\nNew UTC Day Started: {current_day}\n")

        if arenas_created_today < DAILY_ARENA_LIMIT:
            arena_number = arenas_created_today + 1

            # Alternate arena types
            if arena_number % 2 == 1:
                arena = generate_hit_target_arena(arena_number)
            else:
                arena = generate_stay_above_arena(arena_number)

            arenas_created_today += 1
            active_arenas.append(arena)

            print("\n--- READY TO POST ON X ---")
            print(format_arena(arena))
            print("--- END ---\n")

        for arena in list(active_arenas):
            if now >= arena["deadline"]:
                resolved = resolve_arena(arena)
                active_arenas.remove(arena)

                print("\n--- ARENA RESOLVED ---")
                print(format_resolution(resolved))
                print("--- END ---\n")

        time.sleep(3600)
