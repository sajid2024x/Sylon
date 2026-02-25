import time
import random
import requests
import sqlite3
from datetime import datetime, timedelta, timezone

# -----------------------------
# CONFIG
# -----------------------------

DAILY_ARENA_LIMIT = 3
BTC_PRICE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

HIT_LEVELS = [88000, 90000, 92000, 95000]
FLOOR_LEVELS = [82000, 85000, 88000]

MACRO_TEMPLATES = [
    {
        "question": "Will the Federal Reserve announce an emergency policy action before {deadline} UTC?",
        "resolver": "FED_ANNOUNCEMENT"
    },
    {
        "question": "Will the U.S. government announce a shutdown before {deadline} UTC?",
        "resolver": "US_SHUTDOWN"
    },
    {
        "question": "Will a new U.S. economic sanctions package be announced before {deadline} UTC?",
        "resolver": "SANCTIONS"
    }
]

DB_PATH = "arenas.db"

# -----------------------------
# DATABASE
# -----------------------------

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS arenas (
            arena_id TEXT PRIMARY KEY,
            type TEXT,
            question TEXT,
            target REAL,
            floor REAL,
            deadline TEXT,
            rules TEXT,
            status TEXT,
            outcome TEXT,
            resolved_price REAL,
            created_at TEXT,
            resolved_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arena_id TEXT,
            username TEXT,
            prediction TEXT,
            created_at TEXT,
            UNIQUE(arena_id, username)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            username TEXT PRIMARY KEY,
            total_predictions INTEGER,
            wins INTEGER,
            losses INTEGER,
            current_streak INTEGER,
            max_streak INTEGER
        )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# PRICE FETCHER
# -----------------------------

def get_btc_price():
    r = requests.get(BTC_PRICE_URL, timeout=10)
    return float(r.json()["price"])

# -----------------------------
# ARENA GENERATORS
# -----------------------------

def generate_hit_target_arena(num):
    now = datetime.now(timezone.utc)
    target = random.choice(HIT_LEVELS)
    deadline = now + timedelta(days=3)
    arena_id = f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}"

    return {
        "arena_id": arena_id,
        "type": "HIT_TARGET",
        "question": f"Will BTC hit {target} USD before {deadline.strftime('%Y-%m-%d %H:%M')} UTC?",
        "target": target,
        "floor": None,
        "deadline": deadline,
        "rules": "YES if BTC price on Binance reaches or exceeds target before deadline.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

def generate_stay_above_arena(num):
    now = datetime.now(timezone.utc)
    floor = random.choice(FLOOR_LEVELS)
    deadline = now + timedelta(days=2)
    arena_id = f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}"

    return {
        "arena_id": arena_id,
        "type": "STAY_ABOVE",
        "question": f"Will BTC stay above {floor} USD until {deadline.strftime('%Y-%m-%d %H:%M')} UTC?",
        "target": None,
        "floor": floor,
        "deadline": deadline,
        "rules": "YES if BTC price on Binance is still above floor at deadline.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

def generate_macro_arena(num):
    now = datetime.now(timezone.utc)
    template = random.choice(MACRO_TEMPLATES)
    deadline = now + timedelta(days=2)

    arena_id = f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}"

    return {
        "arena_id": arena_id,
        "type": "MACRO",
        "question": template["question"].format(
            deadline=deadline.strftime('%Y-%m-%d %H:%M')
        ),
        "target": None,
        "floor": None,
        "deadline": deadline,
        "rules": "YES if confirmed by official government or institutional announcement.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

# -----------------------------
# DATABASE HELPERS
# -----------------------------

def save_arena(arena):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO arenas
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        arena["arena_id"],
        arena["type"],
        arena["question"],
        arena["target"],
        arena["floor"],
        arena["deadline"].isoformat(),
        arena["rules"],
        arena["status"],
        arena["outcome"],
        arena["resolved_price"],
        arena["created_at"].isoformat(),
        arena["resolved_at"].isoformat() if arena["resolved_at"] else None
    ))
    conn.commit()
    conn.close()

# -----------------------------
# RESOLUTION ENGINE (MACRO = MANUAL)
# -----------------------------

def resolve_arena(arena):
    if arena["type"] in ("HIT_TARGET", "STAY_ABOVE"):
        price = get_btc_price()
        if arena["type"] == "HIT_TARGET":
            outcome = "YES" if price >= arena["target"] else "NO"
        else:
            outcome = "YES" if price >= arena["floor"] else "NO"
        arena["resolved_price"] = price
    else:
        # macro v1 = manual resolution
        outcome = "NO"

    arena["status"] = "RESOLVED"
    arena["outcome"] = outcome
    arena["resolved_at"] = datetime.now(timezone.utc)

    save_arena(arena)
    return arena

# -----------------------------
# MAIN LOOP (3 arenas/day)
# -----------------------------

if __name__ == "__main__":

    init_db()

    print("\nSylon running with Crypto + Macro arenas.\n")

    while True:
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y%m%d")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM arenas WHERE arena_id LIKE ?",
            (f"SYLON-{today}-%",)
        )
        count = cur.fetchone()[0]
        conn.close()

        if count < DAILY_ARENA_LIMIT:
            num = count + 1

            if num == 3:
                arena = generate_macro_arena(num)
            elif num % 2 == 1:
                arena = generate_hit_target_arena(num)
            else:
                arena = generate_stay_above_arena(num)

            save_arena(arena)

            print("\n--- READY TO POST ON X ---")
            print(arena["arena_id"])
            print(arena["question"])
            print("--- END ---\n")

        time.sleep(3600)
