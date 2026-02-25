import time
import random
import os
import tweepy
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
# X TEST TWEET
# -----------------------------

def send_test_tweet():
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )

    tweet = "sylon online. prediction arenas coming soon."

    client.create_tweet(text=tweet)
    print("test tweet sent (v2)")

# -----------------------------
# MAIN (TEMPORARY TEST MODE)
# -----------------------------

if __name__ == "__main__":
    send_test_tweet()
