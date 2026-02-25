import time
import random
import requests
import sqlite3
from datetime import datetime, timedelta, timezone

# =================================================
# CONFIG
# =================================================

DAILY_ARENA_LIMIT = 3
BTC_PRICE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
DB_PATH = "arenas.db"

HIT_LEVELS = [88000, 90000, 92000, 95000]
FLOOR_LEVELS = [82000, 85000, 88000]

# =================================================
# NARRATIVE DETECTION (V1)
# =================================================

NARRATIVE_TRIGGERS = [
    {
        "keywords": ["emergency"],
        "arena_type": "MACRO_FED_EMERGENCY"
    },
    {
        "keywords": ["shutdown"],
        "arena_type": "MACRO_US_SHUTDOWN"
    }
]

# =================================================
# DATABASE
# =================================================

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

# =================================================
# HELPERS
# =================================================

def get_btc_price():
    return float(requests.get(BTC_PRICE_URL, timeout=10).json()["price"])

def detect_narrative(text: str):
    text = text.lower()
    for trigger in NARRATIVE_TRIGGERS:
        if all(k in text for k in trigger["keywords"]):
            return trigger["arena_type"]
    return None

# =================================================
# ARENA GENERATORS
# =================================================

def generate_hit_target_arena(num):
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(days=3)
    target = random.choice(HIT_LEVELS)

    return {
        "arena_id": f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}",
        "type": "CRYPTO_HIT",
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
    deadline = now + timedelta(days=2)
    floor = random.choice(FLOOR_LEVELS)

    return {
        "arena_id": f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}",
        "type": "CRYPTO_FLOOR",
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

def generate_macro_arena_from_narrative(arena_type, num):
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(days=2)

    if arena_type == "MACRO_FED_EMERGENCY":
        question = f"Will the Federal Reserve announce an emergency policy action before {deadline.strftime('%Y-%m-%d %H:%M')} UTC?"
        rules = "YES if confirmed by official Federal Reserve announcement."
    elif arena_type == "MACRO_US_SHUTDOWN":
        question = f"Will the U.S. government announce a shutdown before {deadline.strftime('%Y-%m-%d %H:%M')} UTC?"
        rules = "YES if confirmed by official U.S. government sources."
    else:
        return None

    return {
        "arena_id": f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}",
        "type": "MACRO",
        "question": question,
        "target": None,
        "floor": None,
        "deadline": deadline,
        "rules": rules,
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

# =================================================
# DATABASE ACTIONS
# =================================================

def save_arena(arena):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO arenas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        arena["arena_id"], arena["type"], arena["question"],
        arena["target"], arena["floor"],
        arena["deadline"].isoformat(),
        arena["rules"], arena["status"], arena["outcome"],
        arena["resolved_price"],
        arena["created_at"].isoformat(),
        arena["resolved_at"].isoformat() if arena["resolved_at"] else None
    ))
    conn.commit()
    conn.close()

def save_prediction(arena_id, username, prediction):
    prediction = prediction.upper()
    if prediction not in ("YES", "NO"):
        print("Invalid prediction.")
        return

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO predictions (arena_id, username, prediction, created_at)
            VALUES (?, ?, ?, ?)
        """, (arena_id, username.lower(), prediction, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        print(f"Recorded: @{username} → {prediction}")
    except sqlite3.IntegrityError:
        print("Already predicted.")
    conn.close()

# =================================================
# FORMATTERS (X-READY)
# =================================================

def format_arena(arena):
    return (
        "🧠 SYLON PREDICTION ARENA\n\n"
        f"Arena ID: {arena['arena_id']}\n\n"
        f"{arena['question']}\n\n"
        f"Deadline: {arena['deadline'].strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        "Reply YES or NO 👇\n\n"
        f"{arena['rules']}"
    )

# =================================================
# CLI HANDLER
# =================================================

def handle_command(cmd):
    parts = cmd.split()
    if not parts:
        return

    if parts[0] == "predict" and len(parts) == 4:
        _, arena_id, username, prediction = parts
        save_prediction(arena_id, username, prediction)

    elif parts[0] == "narrative":
        text = cmd.replace("narrative", "", 1).strip()
        arena_type = detect_narrative(text)
        if not arena_type:
            print("No actionable narrative detected.")
            return

        conn = get_db()
        cur = conn.cursor()
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        cur.execute("SELECT COUNT(*) FROM arenas WHERE arena_id LIKE ?", (f"SYLON-{today}-%",))
        num = cur.fetchone()[0] + 1
        conn.close()

        arena = generate_macro_arena_from_narrative(arena_type, num)
        save_arena(arena)
        print("\n--- READY TO POST ---")
        print(format_arena(arena))
        print("--- END ---\n")

    else:
        print("Commands:")
        print("  predict <ARENA_ID> <username> YES/NO")
        print("  narrative <text>")

# =================================================
# MAIN LOOP
# =================================================

if __name__ == "__main__":
    init_db()
    print("\nSylon running (Full V1).\n")

    while True:
        try:
            cmd = input(">> ").strip()
            if cmd:
                handle_command(cmd)
        except EOFError:
            pass

        time.sleep(1)
