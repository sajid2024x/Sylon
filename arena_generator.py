import time
import random
from datetime import datetime, timedelta, timezone

# -----------------------------
# CONFIG
# -----------------------------

DAILY_ARENA_LIMIT = 3
CRYPTO_PRICE_LEVELS = [88000, 90000, 92000, 95000]

# -----------------------------
# STATE (in-memory v1)
# -----------------------------

arenas_created_today = 0
current_day = datetime.now(timezone.utc).date()

# -----------------------------
# ARENA GENERATOR
# -----------------------------

def generate_btc_arena():
    target = random.choice(CRYPTO_PRICE_LEVELS)
    deadline = datetime.now(timezone.utc) + timedelta(days=3)

    question = (
        f"will btc hit {target} usd before "
        f"{deadline.strftime('%Y-%m-%d %H:%M')} utc?"
    )

    rules = (
        "resolution rule: YES if btc last traded price on binance "
        "reaches or exceeds target before deadline."
    )

    return {
        "question": question,
        "deadline": deadline,
        "rules": rules,
        "type": "crypto_price",
        "created_at": datetime.now(timezone.utc)
    }

# -----------------------------
# TWEET FORMATTER (MANUAL MODE)
# -----------------------------

def format_arena_tweet(arena):
    tweet = (
        "🧠 SYLON PREDICTION ARENA\n\n"
        f"{arena['question']}\n\n"
        f"deadline: {arena['deadline'].strftime('%Y-%m-%d %H:%M')} utc\n\n"
        "reply YES or NO 👇\n\n"
        f"{arena['rules']}"
    )
    return tweet

# -----------------------------
# MAIN LOOP
# -----------------------------

if __name__ == "__main__":

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()

        # reset daily counter
        if today != current_day:
            arenas_created_today = 0
            current_day = today
            print(f"\nnew utc day started: {current_day}\n")

        if arenas_created_today < DAILY_ARENA_LIMIT:
            arena = generate_btc_arena()
            tweet_text = format_arena_tweet(arena)

            arenas_created_today += 1

            print("\n--- READY TO POST ON X ---")
            print(tweet_text)
            print("--- END ---\n")

        else:
            print("daily arena limit reached")

        # wait 24 hours
        time.sleep(86400)
