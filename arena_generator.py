import time
import random
from datetime import datetime, timedelta, timezone

# -----------------------------
# CONFIG
# -----------------------------

DAILY_ARENA_LIMIT = 3
CRYPTO_PRICE_LEVELS = [88000, 90000, 92000, 95000]

# -----------------------------
# STATE (in-memory for v1)
# -----------------------------

arenas_created_today = 0
current_day = datetime.now(timezone.utc).date()

# -----------------------------
# ARENA GENERATOR
# -----------------------------

def generate_btc_arena(current_price: float):
    target = random.choice(CRYPTO_PRICE_LEVELS)

    deadline = datetime.now(timezone.utc) + timedelta(days=3)

    question = (
        f"will btc hit {target} usd before "
        f"{deadline.strftime('%Y-%m-%d %H:%M')} utc?"
    )

    rules = (
        "resolution rule: arena resolves YES if btc last traded "
        "price on binance reaches or exceeds the target before deadline."
    )

    arena = {
        "asset": "BTC",
        "question": question,
        "target_price": target,
        "deadline": deadline.isoformat(),
        "rules": rules,
        "type": "price",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    return arena

# -----------------------------
# DAILY LOOP (WORKER)
# -----------------------------

if __name__ == "__main__":

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()

        # reset counter at new UTC day
        if today != current_day:
            arenas_created_today = 0
            current_day = today
            print(f"new utc day started: {current_day}")

        # create arena if under daily limit
        if arenas_created_today < DAILY_ARENA_LIMIT:
            arena = generate_btc_arena(current_price=89000)
            arenas_created_today += 1

            print("new arena created:")
            print(arena)
        else:
            print("daily arena limit reached")

        # sleep 24 hours
        time.sleep(86400)
