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

def save_prediction(arena_id, username, prediction):
    prediction = prediction.upper()
    if prediction not in ("YES", "NO"):
        print("Invalid prediction. Use YES or NO.")
        return

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO predictions (arena_id, username, prediction, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            arena_id,
            username.lower(),
            prediction,
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
        print(f"Prediction recorded: {username} → {prediction}")
    except sqlite3.IntegrityError:
        print("User already predicted on this arena.")

    conn.close()

def load_open_arenas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM arenas WHERE status='OPEN'")
    rows = cur.fetchall()
    conn.close()

    arenas = []
    for r in rows:
        arenas.append({
            "arena_id": r[0],
            "type": r[1],
            "question": r[2],
            "target": r[3],
            "floor": r[4],
            "deadline": datetime.fromisoformat(r[5]),
            "rules": r[6],
            "status": r[7],
            "outcome": r[8],
            "resolved_price": r[9],
            "created_at": datetime.fromisoformat(r[10]),
            "resolved_at": datetime.fromisoformat(r[11]) if r[11] else None
        })

    return arenas

# -----------------------------
# LEADERBOARD LOGIC
# -----------------------------

def update_user_stats(arena):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT username, prediction FROM predictions WHERE arena_id=?",
        (arena["arena_id"],)
    )

    for username, prediction in cur.fetchall():
        correct = prediction == arena["outcome"]

        cur.execute("SELECT * FROM user_stats WHERE username=?", (username,))
        row = cur.fetchone()

        if not row:
            total = 1
            wins = 1 if correct else 0
            losses = 0 if correct else 1
            streak = 1 if correct else 0
            max_streak = streak
        else:
            _, total, wins, losses, streak, max_streak = row
            total += 1
            if correct:
                wins += 1
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                losses += 1
                streak = 0

        cur.execute("""
            INSERT OR REPLACE INTO user_stats
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, total, wins, losses, streak, max_streak))

    conn.commit()
    conn.close()

# -----------------------------
# RESOLUTION ENGINE
# -----------------------------

def resolve_arena(arena):
    price = get_btc_price()

    if arena["type"] == "HIT_TARGET":
        outcome = "YES" if price >= arena["target"] else "NO"
    else:
        outcome = "YES" if price >= arena["floor"] else "NO"

    arena["status"] = "RESOLVED"
    arena["outcome"] = outcome
    arena["resolved_price"] = price
    arena["resolved_at"] = datetime.now(timezone.utc)

    save_arena(arena)
    update_user_stats(arena)
    return arena

# -----------------------------
# CLI COMMAND HANDLER
# -----------------------------

def handle_command(command: str):
    parts = command.strip().split()

    if len(parts) != 4 or parts[0].lower() != "predict":
        print("Use: predict <ARENA_ID> <username> YES/NO")
        return

    _, arena_id, username, prediction = parts
    save_prediction(arena_id, username, prediction)

# -----------------------------
# MAIN LOOP
# -----------------------------

if __name__ == "__main__":

    init_db()
    active_arenas = load_open_arenas()

    print("\nSylon running.")
    print("Enter predictions like:")
    print("predict SYLON-YYYYMMDD-001 alice YES\n")

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
            arena = generate_hit_target_arena(num) if num % 2 else generate_stay_above_arena(num)
            save_arena(arena)
            active_arenas.append(arena)
            print("NEW ARENA:", arena["arena_id"])

        for arena in list(active_arenas):
            if now >= arena["deadline"]:
                resolved = resolve_arena(arena)
                active_arenas.remove(arena)
                print("RESOLVED:", resolved["arena_id"], resolved["outcome"])

        try:
            user_input = input(">> ").strip()
            if user_input:
                handle_command(user_input)
        except EOFError:
            pass

        time.sleep(3600)
