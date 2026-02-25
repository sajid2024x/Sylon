from datetime import datetime, timedelta
import random

CRYPTO_PRICE_LEVELS = [88000, 90000, 92000, 95000]

def generate_btc_arena(current_price: float):
    target = random.choice(CRYPTO_PRICE_LEVELS)

    deadline = datetime.utcnow() + timedelta(days=3)

    question = (
        f"will btc hit {target} usd before "
        f"{deadline.strftime('%Y-%m-%d %H:%M')} utc?"
    )

    rules = (
        "resolution rule: arena resolves YES if btc last traded "
        "price on binance reaches or exceeds the target before deadline."
    )

    return {
        "asset": "BTC",
        "question": question,
        "target_price": target,
        "deadline": deadline.isoformat(),
        "rules": rules,
        "type": "price"
    }


import time

if __name__ == "__main__":
    while True:
        arena = generate_btc_arena(current_price=89000)
        print(arena)
        time.sleep(86400)  # wait 24 hours
