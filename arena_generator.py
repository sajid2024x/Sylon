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
        "deadline": deadline,
        "rules": rules,
        "type": "crypto_price",
        "created_at": now
    }

# -----------------------------
# TWEET FORMATTER (MANUAL MODE)
# -----------------------------

def format_arena_tweet(arena):
    tweet = (
        "🧠 SYLON PREDICTION ARENA\n\n"
        f"Arena ID: {arena['arena_id']}\n\n"
        f"{arena['question']}\n\n"
        f"Deadline: {arena['deadline'].strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        "Reply YES or NO 👇\n\n"
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

        # Reset daily counter at UTC midnight
        if today != current_day:
            arenas_created_today = 0
            current_day = today
            print(f"\nNew UTC Day Started: {current_day}\n")

        if arenas_created_today < DAILY_ARENA_LIMIT:
            arena = generate_btc_arena(arenas_created_today + 1)
            tweet_text = format_arena_tweet(arena)

            arenas_created_today += 1

            print("\n--- READY TO POST ON X ---")
            print(tweet_text)
            print("--- END ---\n")
        else:
            print("Daily Arena Limit Reached.")

        # Wait 24 hours
        time.sleep(86400)
